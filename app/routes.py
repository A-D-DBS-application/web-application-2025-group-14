from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import func, case
from sqlalchemy.orm import joinedload

from .models import db, Material, Zone, Item, Reservation, User, Company, MaterialEvent
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

def record_material_event(username: str, material_id: int, event_type: str, total_events: int) -> None:
    """
    Slaat een view / reserve event op voor de For-you logica.
    """
    if not username or not material_id:
        return

    ev = MaterialEvent(
        username=username,
        material_id=material_id,
        event_type=event_type,
        total_events=total_events,
    )
    db.session.add(ev)
    db.session.commit()



main = Blueprint("main", __name__)
#----------------------------------------------------------------------------

@main.route("/login", methods=["GET", "POST"])
def login():
    """Login met Users uit de database, per company."""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # gebruiker opzoeken
        user = User.query.filter_by(username=username).first()

        # user bestaat niet of wachtwoord fout (plain text vergelijking)
        if not user or user.password != password:
            return render_template("login.html", error="Ongeldige login")

        # alles ok → sessie vullen
        session.permanent = True
        session["username"] = user.username          # NIET user.full_name
        session["company_name"] = user.company_name  # komt uit Supabase
        session["username_pk"] = user.username

        return redirect(url_for("main.inventory"))

    return render_template("login.html")




@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))



# ---------------------------------------------------------------------------
# INVENTORY OVERVIEW
# ---------------------------------------------------------------------------
@main.route("/")
def inventory():
    if "username" not in session:
        return redirect(url_for("main.login"))

    # --- Sidebar (manual) selection ---
    active_brand = request.args.get("brand")
    active_material_id = request.args.get("material_id", type=int)

    # --- Search & Filter (search flow) ---
    q_type = request.args.get("q_type") or ""
    q_desc = request.args.get("q_desc") or ""
    q_brand = request.args.get("q_brand") or ""
    q_zone = request.args.get("q_zone") or ""
    q_lifecycle = request.args.get("q_lifecycle") or ""
    filter_purpose = request.args.get("filter_purpose") or ""
    filter_packaging = request.args.get("filter_packaging") or ""

    # --- Make brand "active" if searching by it ---
    if q_brand and not active_brand:
        active_brand = q_brand

    # determine whether this request is a "search" (right-panel) request:
    is_search = any([
        bool(q_type.strip()),
        bool(q_desc.strip()),
        bool(q_brand.strip()),
        bool(q_zone.strip()),
        bool(q_lifecycle.strip()),
        bool(filter_purpose),
        bool(filter_packaging),
    ])

    company_name = session.get("company_name") or "Primetals"

    # --- 1) Sidebar brands + materials (unchanged) ---
    material_stats = (
        db.session.query(
            Material,
            func.count(Item.item_id).label("item_count"),
        )
        .outerjoin(Item)
        .filter(Material.company_name == company_name)
        .group_by(Material.material_id)
        .order_by(Material.brand, Material.material_type)
        .all()
    )

    brands_dict = {}
    for material, item_count in material_stats:
        brand_name = material.brand

        # Case-insensitive active_brand bepalen
        is_brand_active = False
        if active_brand and brand_name.lower() == active_brand.lower():
            is_brand_active = True

        # Maak de brand entry aan als die nog niet bestaat
        if brand_name not in brands_dict:
            brands_dict[brand_name] = {
                "name": brand_name,
                "material_count": 0,
                "materials": [],
                "active": is_brand_active,  # flag voor template
            }

        # ----- Controleer of dit materiaal bij alle actieve filters past -----
        material_matches = True

        # Brand filter
        if q_brand and brand_name.lower() != q_brand.lower():
            material_matches = False

        # Type filter
        if q_type and q_type.lower() not in material.material_type.lower():
            material_matches = False

        # Description filter
        if q_desc and q_desc.lower() not in material.description.lower():
            material_matches = False

        # Lifecycle filter
        if q_lifecycle and q_lifecycle.lower() not in (material.lifecycle or "").lower():
            material_matches = False

        # Zone filter: check of er minstens één item in deze zone hoort
        if q_zone:
            has_matching_zone = any(
                z.zone_name.lower().find(q_zone.lower()) != -1
                for z in Zone.query.join(Item).filter(Item.material_id == material.material_id).all()
            )
            if not has_matching_zone:
                material_matches = False

        # Purpose filter: check of er minstens één item met dit purpose bestaat
        if filter_purpose:
            has_matching_purpose = any(
                i.purpose == filter_purpose for i in Item.query.filter_by(material_id=material.material_id).all()
            )
            if not has_matching_purpose:
                material_matches = False

        # Packaging filter: check of er minstens één item met dit packaging bestaat
        if filter_packaging:
            has_matching_packaging = any(
                i.packaging == filter_packaging for i in Item.query.filter_by(material_id=material.material_id).all()
            )
            if not has_matching_packaging:
                material_matches = False

        # Voeg enkel materials toe die matchen
        if material_matches:
            brands_dict[brand_name]["material_count"] += item_count
            brands_dict[brand_name]["materials"].append({
                "id": material.material_id,
                "type": material.material_type,
                "description": material.description,
                "item_count": item_count,
            })



            brands = list(brands_dict.values())



    # --- Business rule: when to show items & For You ---
    # Manual flow = user clicked sidebar brand/material (active_brand / active_material_id) and no search filters
    is_manual_flow = (active_brand or active_material_id) and not is_search

    # For You: show only when manual brand selected AND no material_id (so brand clicked, not type)
    show_for_you = False
    if is_manual_flow and active_brand and not active_material_id:
        # Only show "For You" in this exact case (manual brand click + no type chosen)
        show_for_you = True
    if not active_brand and not is_search:
        show_for_you = True

    # Show items:
    # - if search flow: always show items (search may be single-field, e.g. only q_brand)
    # - or if manual flow and a specific material_id was clicked
    show_items = False
    if is_search:
        show_items = True
    elif is_manual_flow and active_material_id:
        show_items = True
    else:
        show_items = False

    # --- Page title logic ---
    # Priority:
    # 1) if manual material selected -> "Brand — Type"
    # 2) if search and q_brand+q_type/q_desc -> "Brand — Type"
    # 3) if search and q_brand only -> "Brand"
    # 4) if search and q_type/q_desc only -> "Type"
    # 5) if search with only zone/lifecycle/purpose/packaging -> "Inventory"
    # 6) fallback -> "Inventory"
    page_title = "Inventory"
    active_material = None

    if active_material_id:
        active_material = Material.query.get(active_material_id)
        if active_material:
            page_title = f"{active_material.brand} — {active_material.material_type}"
    elif is_search:
        # q_brand + q_type/desc
        if q_brand and (q_type or q_desc):
            # show brand-type (use q_type if provided, else q_desc)
            typ = q_type if q_type else q_desc
            page_title = f"{q_brand} — {typ}"
        elif q_brand:
            page_title = q_brand
        elif q_type or q_desc:
            page_title = q_type if q_type else q_desc
        else:
            # only zone/lifecycle/purpose/packaging -> keep Inventory
            page_title = "Inventory"
    elif active_brand:
        # manual brand clicked (no search)
        page_title = active_brand

    # --- 2) Items query: build only if show_items True,
    # and in search flow allow all filters combined (case-insensitive partial matches)
    items = []
    if show_items:
        query = (
            Item.query
            .join(Material)
            .join(Zone)
            .filter(Material.company_name == company_name)
        )

        # Manual material selected -> restrict to that material
        if active_material_id and not is_search:
            query = query.filter(Item.material_id == active_material_id)
        else:
            # SEARCH flow: apply any provided filters (partial, case-insensitive)
            if q_brand:
                query = query.filter(Material.brand.ilike(f"%{q_brand}%"))
            if q_type:
                query = query.filter(Material.material_type.ilike(f"%{q_type}%"))
            if q_desc:
                query = query.filter(Material.description.ilike(f"%{q_desc}%"))
            if q_zone:
                query = query.filter(Zone.zone_name.ilike(f"%{q_zone}%"))
            if q_lifecycle:
                query = query.filter(Material.lifecycle.ilike(f"%{q_lifecycle}%"))
            if filter_purpose:
                query = query.filter(Item.purpose == filter_purpose)
            if filter_packaging:
                query = query.filter(Item.packaging == filter_packaging)

        items = query.order_by(Material.brand, Material.material_type).all()

    item_count = len(items)

    # --- EVENT LOGGING: only log when the user manually clicked a material (sidebar) ---
    username_pk = session.get("username_pk") or session.get("username")
    if active_material and username_pk:
        record_material_event(
            username=username_pk,
            material_id=active_material.material_id,
            event_type="view",
            total_events=0
        )

    # --- Reserved totals per item ---
    reserved_totals = {
        item.item_id: sum(r.quantity for r in item.reservations)
        for item in items
    }

    # --- Reservations (cart) list (unchanged) ---
    reservations_raw = (
        db.session.query(Reservation, Item, Material, Zone)
        .join(Item, Reservation.item_id == Item.item_id)
        .join(Material, Item.material_id == Material.material_id)
        .join(Zone, Item.zone_id == Zone.zone_id)
        .filter(Material.company_name == company_name)
        .order_by(Reservation.date.desc())
        .all()
    )

    reservations_list = [
        {
            "item_id": item.item_id,
            "brand": mat.brand,
            "type": mat.material_type,
            "description": mat.description,
            "zone": zone.zone_name,
            "username": reservation.username,
            "project": reservation.project,
            "date": reservation.date,
            "quantity": reservation.quantity,
        }
        for reservation, item, mat, zone in reservations_raw
    ]

    zones = Zone.query.filter_by(company_name=company_name).order_by(Zone.zone_name).all()

    # --- FOR YOU retrieval (unchanged) ---
    personal_top_materials = []
    if username_pk:
        stats = (
            db.session.query(
                MaterialEvent.material_id,
                func.count(
                    case((MaterialEvent.event_type == "view", 1))
                ).label("views"),
                func.count(
                    case((MaterialEvent.event_type == "reserve", 1))
                ).label("reservations"),
                func.max(MaterialEvent.date).label("last_date"),
            )
            .filter(MaterialEvent.username == username_pk)
            .group_by(MaterialEvent.material_id)
            .order_by(func.max(MaterialEvent.date).desc())
            .limit(5)
            .all()
        )

        material_ids = [row.material_id for row in stats]
        if material_ids:
            materials = Material.query.filter(
                Material.material_id.in_(material_ids)
            ).all()
            mat_by_id = {m.material_id: m for m in materials}

            for row in stats:
                m = mat_by_id.get(row.material_id)
                if not m:
                    continue
                personal_top_materials.append(
                    {
                        "material": m,
                        "views": row.views or 0,
                        "reservations": row.reservations or 0,
                        "last_date": row.last_date,
                    }
                )

    # --- Flags for template to render the correct item-cards layout ---
    # manual_items_view: items are shown from a manual material selection (sidebar material click),
    # or when searching with q_brand+q_type/q_desc or when active_material set -> show the compact/limited fields.
    manual_items_view = False
    if (not is_search and active_material_id) or active_material:
        manual_items_view = True
    
    search_brand_type = False
    if is_search and q_brand and (q_type or q_desc):
        search_brand_type = True

    # search variants for item-card decisions
    search_brand_only = is_search and q_brand and not (q_type or q_desc)
    search_type_only = is_search and (q_type or q_desc) and not q_brand
    search_misc_filters_only = is_search and not (q_brand or q_type or q_desc) and any([q_zone, q_lifecycle, filter_purpose, filter_packaging])

    

    return render_template(
        "inventory.html",
        username=session["username"],
        company=company_name,
        brands=brands,
        items=items,
        active_brand=active_brand,
        active_material=active_material,
        active_material_id=active_material_id,
        item_count=item_count,
        reserved_totals=reserved_totals,
        reservations_list=reservations_list,
        zones=zones,
        q_type=q_type,
        q_desc=q_desc,
        q_brand=q_brand,
        q_zone=q_zone,
        q_lifecycle=q_lifecycle,
        filter_purpose=filter_purpose,
        filter_packaging=filter_packaging,
        personal_top_materials=personal_top_materials,
        show_items=show_items,
        show_for_you=show_for_you,
        is_search=is_search,
        manual_items_view=manual_items_view,
        search_brand_type =search_brand_type,
        search_brand_only=search_brand_only,
        search_type_only=search_type_only,
        search_misc_filters_only=search_misc_filters_only,
        page_title=page_title,
    )

# ---------------------------------------------------------------------------
# ADD INVENTORY ITEM (material + zone + item)
# ---------------------------------------------------------------------------
@main.route("/add_item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        company_name = session.get("company_name")

        # --- Material data ---
        brand = request.form["brand"].strip()
        material_type = request.form["material_type"].strip()
        description = request.form["description"].strip()
        lifecycle = request.form.get("lifecycle") or None

        price_raw = request.form.get("price")
        price = float(price_raw.replace(",", ".")) if price_raw else None

        # Material check
        material = Material.query.filter_by(
            company_name=company_name,
            material_type=material_type,
            description=description,
        ).first()

        if material is None:
            material = Material(
                company_name=company_name,
                brand=brand,
                material_type=material_type,
                description=description,
                lifecycle=lifecycle,
                price=price,
            )
            db.session.add(material)
            db.session.flush()

        # --- Zone data ---
        zone_name = request.form["zone_name"].strip().upper()
        zone = Zone.query.filter_by(
            company_name=company_name,
            zone_name=zone_name,
        ).first()

        if zone is None:
            zone = Zone(zone_name=zone_name, company_name=company_name)
            db.session.add(zone)
            db.session.flush()

        # --- Item data ---
        quantity = int(request.form["quantity"])
        purpose = request.form["purpose"]
        packaging = request.form["packaging"]
        comment = request.form.get("comment") or None

        # Check for existing duplicate item (UC3)
        existing_item = Item.query.filter_by(
            material_id=material.material_id,
            zone_id=zone.zone_id,
            purpose=purpose,
            packaging=packaging
        ).first()

        if existing_item:
            # ❗ Update quantity instead of creating duplicate
            existing_item.quantity += quantity
            if comment:
                existing_item.comment = comment
            
            db.session.commit()

            return redirect(url_for("main.inventory", material_id=material.material_id))

        # If not duplicate → create new item
        item = Item(
            material_id=material.material_id,
            zone_id=zone.zone_id,
            purpose=purpose,
            packaging=packaging,
            quantity=quantity,
            comment=comment,
        )

        db.session.add(item)
        db.session.commit()

        return redirect(url_for("main.inventory", material_id=material.material_id))

    return render_template("add_item.html")

# USE / RESERVE ITEM
# ---------------------------------------------------------------------------
@main.route("/item/<int:item_id>/use", methods=["GET", "POST"])
def use_item(item_id: int):
    item = Item.query.get_or_404(item_id)

    # Calculate reserved and available
    already_reserved = sum(r.quantity for r in item.reservations)
    available = item.quantity - already_reserved

    if request.method == "POST":
        username = request.form["username"].strip()
        project = request.form.get("project") or None
        quantity = int(request.form["quantity"])

        # --- User validation ---
        user_exists = User.query.filter_by(
            username=username,
            company_name=item.material.company_name
        ).first()

        if not user_exists:
            error_msg = f"This user '{username}' does not exist in your organization."
            return render_template(
                "use_item.html",
                item=item,
                available=available,
                error=error_msg
            )

        # --- Availability check ---
        if quantity > available:
            error_msg = (
                f"Not enough stock available. Available: {available}, "
                f"requested: {quantity}."
            )
            return render_template("use_item.html", item=item, available=available, error=error_msg)

        # --- Create reservation ---
        reservation = Reservation(
            item_id=item.item_id,
            username=username,
            quantity=quantity,
            project=project,
        )
        db.session.add(reservation)

        # --- Reduce real stock directly ---
        item.quantity -= quantity
        db.session.commit()

        # 👉 reserve-event loggen
        username_pk = session.get("username_pk") or username
        record_material_event(
            username=username_pk,
            material_id=item.material_id,
            event_type="reserve",
            total_events=0 #!
        )

        return redirect(
            url_for(
                "main.inventory",
                brand=request.args.get("brand"),
                material_id=request.args.get("material_id"),
            )
        )

    return render_template("use_item.html", item=item, available=available)





# ---------------------------------------------------------------------------
# INLINE QUANTITY UPDATE
# ---------------------------------------------------------------------------
@main.route("/item/<int:item_id>/quantity", methods=["POST"])
def update_quantity(item_id: int):
    """Update quantity from the inline form on the inventory page."""

    item = Item.query.get_or_404(item_id)
    new_quantity = max(int(request.form["quantity"]), 0)
    item.quantity = new_quantity
    db.session.commit()

    brand = request.args.get("brand")
    material_id = request.args.get("material_id")

    return redirect(url_for("main.inventory", brand=brand, material_id=material_id))


# ---------------------------------------------------------------------------
# EDIT MATERIAL
# ---------------------------------------------------------------------------
@main.route("/material/<int:material_id>/edit", methods=["GET", "POST"])
def edit_material(material_id: int):
    """Edit brand / type / description / lifecycle / price of a material."""

    material = Material.query.get_or_404(material_id)

    if request.method == "POST":
        material.brand = request.form["brand"]
        material.material_type = request.form["material_type"]
        material.description = request.form["description"]
        material.lifecycle = request.form.get("lifecycle") or None

        price_raw = request.form.get("price")
        material.price = float(price_raw) if price_raw else None

        db.session.commit()
        return redirect(
            url_for(
                "main.inventory",
                brand=material.brand,
                material_id=material.material_id,
            )
        )

    return render_template("edit_material.html", material=material)


# ---------------------------------------------------------------------------
# EDIT ITEM
# ---------------------------------------------------------------------------
@main.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id: int):
    """Edit zone, purpose, packaging and comment of an item."""

    item = (
        Item.query.options(
            joinedload(Item.material),
            joinedload(Item.zone),
        )
        .get_or_404(item_id)
    )

    if request.method == "POST":
        # Zone is free text: look it up or create it.
        zone_name = request.form["zone_name"].strip().upper()
        company_name = item.material.company_name

        zone = Zone.query.filter_by(
            company_name=company_name,
            zone_name=zone_name,
        ).first()

        if zone is None:
            zone = Zone(zone_name=zone_name, company_name=company_name)
            db.session.add(zone)
            db.session.flush()

        item.zone_id = zone.zone_id
        item.purpose = request.form["purpose"]
        item.packaging = request.form["packaging"]
        item.comment = request.form.get("comment") or None

        db.session.commit()

        return redirect(
            url_for(
                "main.inventory",
                brand=item.material.brand,
                material_id=item.material_id,
            )
        )

    return render_template("edit_item.html", item=item)


# ---------------------------------------------------------------------------
# DELETE RESERVATION (cart panel)
# ---------------------------------------------------------------------------
@main.route("/reservation/delete", methods=["POST"])
def delete_reservation():
    """Delete a single reservation and keep the same brand/material context."""

    item_id = int(request.form["item_id"])
    username = request.form["username"]
    date_str = request.form["date"]  # ISO string from the template
    date = datetime.fromisoformat(date_str)

    reservation = Reservation.query.filter_by(
        item_id=item_id,
        username=username,
        date=date,
    ).first_or_404()

    db.session.delete(reservation)
    db.session.commit()

    brand = request.form.get("brand")
    material_id = request.form.get("material_id")

    return redirect(url_for("main.inventory", brand=brand, material_id=material_id))


# ---------------------------------------------------------------------------
# SEARCH INVENTORY
# ---------------------------------------------------------------------------
@main.route("/search", methods=["POST"])
def search():
    """
    Search inventory based on optional criteria:
    type, description, brand, zone, purpose, lifecycle, packaging.
    Only uses criteria that are filled in.
    Filters by company_name from session as per business rules.
    """
    # Get company_name from session (required per Pasop.md)
    company_name = session.get("company_name")
    if not company_name:
        # Fallback if session not set (shouldn't happen in production)
        company_name = "Primetals"
    
    # Get search criteria from form (only use if provided)
    search_params = {}
    
    # Material fields
    search_type = request.form.get("search_type", "").strip()
    if search_type:
        search_params["q_type"] = search_type
    
    search_description = request.form.get("search_description", "").strip()
    if search_description:
        search_params["q_desc"] = search_description
    
    search_brand = request.form.get("search_brand", "").strip()
    if search_brand:
        search_params["q_brand"] = search_brand
    
    search_lifecycle = request.form.get("search_lifecycle", "").strip()
    if search_lifecycle:
        search_params["q_lifecycle"] = search_lifecycle
    
    # Item fields
    search_zone = request.form.get("search_zone", "").strip()
    if search_zone:
        search_params["q_zone"] = search_zone
    
    search_purpose = request.form.get("search_purpose", "").strip()
    if search_purpose:
        search_params["filter_purpose"] = search_purpose
    
    search_packaging = request.form.get("search_packaging", "").strip()
    if search_packaging:
        search_params["filter_packaging"] = search_packaging
    
    # Redirect to inventory with search parameters
    # The inventory() function will handle the actual filtering
    return redirect(url_for("main.inventory", **search_params))


# ---------------------------------------------------------------------------
# RESET SEARCH FILTERS
# ---------------------------------------------------------------------------
#@main.route("/reset", methods=["GET", "POST"])
#def reset_search():
    """
    Reset all search filters and return to default inventory view.
    Clears all query parameters and shows all items for the company.
    """
    # Simply redirect to inventory without any query parameters
    return redirect(url_for("main.inventory"))


# --------------------------------------------------------------------------- 



@main.route("/for_you/clear", methods=["POST"])
def clear_for_you():
    """Alle persoonlijke aanbevelingen wissen voor de ingelogde gebruiker."""
    username = session.get("username_pk")
    if not username:
        return redirect(url_for("main.login"))

    MaterialEvent.query.filter_by(username=username).delete()
    db.session.commit()

    return redirect(url_for("main.inventory"))


@main.route("/for_you/<int:material_id>/remove", methods=["POST"])
def remove_for_you_material(material_id):
    """Eén materiaal uit 'For you' verwijderen voor deze gebruiker."""
    username = session.get("username_pk")
    if not username:
        return redirect(url_for("main.login"))

    MaterialEvent.query.filter_by(
        username=username,
        material_id=material_id
    ).delete()
    db.session.commit()

    return redirect(url_for("main.inventory"))