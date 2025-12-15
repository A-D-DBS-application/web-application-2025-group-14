from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, abort, flash
from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from .models import db, Material, Zone, Item, Reservation, User, Company, MaterialEvent
from flask import session
from urllib.parse import urlparse

# ===========================================================================
# HELPER FUNCTIES
# Deze functies centraliseren herbruikte logica om duplicatie te vermijden
# en de routes zelf schoner en leesbaarder te maken.
# ===========================================================================

def _get_current_company_name() -> str:
    """
    Haalt de bedrijfsnaam van de ingelogde gebruiker op uit de sessie.
    Dit maakt de code in de routes duidelijker en centraliseert de sessie-toegang.
    """
    return session.get("company_name") or "Primetals"


def _record_material_event(username: str, material_id: int, event_type: str) -> None:
    """
    Houdt gebruikersinteracties met materialen bij (views en reservaties).
    Deze data wordt gebruikt voor de 'For You' pagina.

    - Zoekt een bestaand 'MaterialEvent' record voor de combinatie user/material/type.
    - Als het bestaat, wordt de teller (`total_events`) verhoogd en de datum bijgewerkt.
    - Als het niet bestaat, wordt een nieuw record aangemaakt.

    Dit zorgt voor een efficiënte tracking zonder voor elke view een nieuwe rij
    in de database aan te maken.
    """
    if not username or not material_id:
        return

    ev = MaterialEvent.query.filter_by(
        username=username,
        material_id=material_id,
        event_type=event_type,
    ).first()

    if ev:
        ev.total_events = (ev.total_events or 0) + 1
        ev.date = datetime.utcnow()
    else:
        ev = MaterialEvent(
            username=username,
            material_id=material_id,
            event_type=event_type,
            total_events=1,
            date=datetime.utcnow(),
        )
        db.session.add(ev)

    db.session.commit()


def _redirect_back(fallback_endpoint: str = "main.inventory"):
    """
    Stuur de gebruiker terug naar de vorige pagina (request.referrer).
    Dit is essentieel om de context (zoals actieve filters) te behouden na een actie.

    - Als er een 'referrer' is met query parameters (bv. filters), wordt de gebruiker
      teruggestuurd naar die exacte URL.
    - In alle andere gevallen (geen referrer, of een referrer zonder query string),
      wordt de gebruiker naar een veilige fallback-pagina gestuurd (standaard de inventory).
    """
    ref = request.referrer
    if not ref:
        return redirect(url_for(fallback_endpoint))

    parsed = urlparse(ref)
    if not parsed.query:
        return redirect(url_for(fallback_endpoint))

    return redirect(ref)


def _find_or_create_zone(company_name: str, zone_name: str) -> Zone:
    """
    Zoekt een zone op naam. Als die niet bestaat, wordt een nieuwe aangemaakt.
    Voorkomt duplicatie in 'add_item' en 'edit_item'.
    """
    zone = Zone.query.filter_by(company_name=company_name, zone_name=zone_name).first()
    if zone is None:
        zone = Zone(zone_name=zone_name, company_name=company_name)
        db.session.add(zone)
        db.session.flush()  # Zorgt ervoor dat de zone een ID krijgt vooraleer te committen
    return zone


def _handle_ajax_form_error(error_msg: str, partial_template: str, full_template: str, **context):
    """
    Centraliseert de foutafhandeling voor formulieren die zowel via AJAX (modals)
    als via een volledige pagina kunnen worden ingediend.

    - Als het een AJAX-request is, wordt de partial template gerenderd met een 400-statuscode.
    - Anders wordt de volledige pagina opnieuw gerenderd met de foutmelding.
    """
    flash(error_msg, "error")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template(partial_template, error=error_msg, **context), 400
    return render_template(full_template, error=error_msg, **context)


# ===========================================================================
# BLUEPRINT & AUTHENTICATIE
# ===========================================================================

main = Blueprint("main", __name__)

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")

        # gebruiker opzoeken
        # Niet-hoofdlettergevoelige zoekopdracht
        user = User.query.filter(func.lower(User.username) == func.lower(username)).first()

        if not user:
            return render_template("login.html", error="Invalid login")

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


# ===========================================================================
# INVENTORY & SEARCH LOGICA
# De 'inventory' route is opgesplitst in helpers voor leesbaarheid.
# ===========================================================================

def _process_filters():
    """
    Verwerkt alle zoek- en filterparameters uit de request en sessie.
    Geeft een dictionary met filterwaarden terug, en een eventueel redirect-object.
    """
    # --- Clear filters if requested ---
    if request.args.get("clear_filters") == "1":
        session.pop("filters", None)
        return None, redirect(url_for("main.inventory"))

    # --- Sidebar (manual) selection ---
    active_brand = request.args.get("brand")
    active_material_id = request.args.get("material_id", type=int)

    # --- Search & Filter (search flow) ---
    # Get filters from URL params first, fallback to session if not in URL
    url_filters = {
        "q_type": request.args.get("q_type"),
        "q_desc": request.args.get("q_desc"),
        "q_brand": request.args.get("q_brand"),
        "q_zone": request.args.get("q_zone"),
        "q_lifecycle": request.args.get("q_lifecycle"),
        "filter_purpose": request.args.get("filter_purpose"),
        "filter_packaging": request.args.get("filter_packaging"),
    }

    # If filters are provided in URL, save them to session
    if any(url_filters.values()):
        session["filters"] = {k: v or "" for k, v in url_filters.items()}
    # If no filters in URL but session has filters, use session filters
    elif "filters" in session and not any([active_brand, active_material_id]):
        saved_filters = session.get("filters", {})
        # Redirect with session filters in URL to make them visible and persistent
        redirect_url = url_for("main.inventory", **{k: v for k, v in saved_filters.items() if v})
        return None, redirect(redirect_url)

    # Use the filters from the session if they exist, otherwise from the URL
    current_filters = session.get("filters", url_filters)

    # Normalize all filter values to strings to avoid None.strip errors
    q_type = current_filters.get("q_type", "") or ""
    q_desc = current_filters.get("q_desc", "") or ""
    q_brand = current_filters.get("q_brand", "") or ""
    q_zone = current_filters.get("q_zone", "") or ""
    q_lifecycle = current_filters.get("q_lifecycle", "") or ""
    filter_purpose = current_filters.get("filter_purpose", "") or ""
    filter_packaging = current_filters.get("filter_packaging", "") or ""

    # determine whether this request is a "search" (right-panel) request:
    is_search = any([
        bool(q_type.strip()), bool(q_desc.strip()), bool(q_brand.strip()),
        bool(q_zone.strip()), bool(q_lifecycle.strip()),
        bool(filter_purpose), bool(filter_packaging),
    ])

    company_name = _get_current_company_name()

    # --- Make brand "active" if searching by it ---
    if q_brand and not active_brand:
        active_brand = q_brand

    filters = {
        "active_brand": active_brand,
        "active_material_id": active_material_id,
        "q_type": q_type, "q_desc": q_desc, "q_brand": q_brand,
        "q_zone": q_zone, "q_lifecycle": q_lifecycle,
        "filter_purpose": filter_purpose, "filter_packaging": filter_packaging,
        "is_search": is_search,
        "company_name": company_name,
    }
    return filters, None


def _get_sidebar_data(company_name, filters):
    """Haalt de data op voor de sidebar (merken en materialen) en filtert deze."""
    active_brand = filters["active_brand"]
    q_type, q_desc, q_brand, q_zone, q_lifecycle = filters["q_type"], filters["q_desc"], filters["q_brand"], filters["q_zone"], filters["q_lifecycle"]
    filter_purpose, filter_packaging = filters["filter_purpose"], filters["filter_packaging"]
    is_search = filters["is_search"]

    material_stats = (
        db.session.query(
            Material,
            func.coalesce(func.sum(Item.quantity), 0).label("total_quantity"), #coalesce om None te vermijden
        )
        .outerjoin(Item)
        .filter(Material.company_name == company_name)
        .group_by(Material.material_id)
        .order_by(Material.brand, Material.material_type)
        .all()
    )

    brands_dict = {}
    for material, total_quantity in material_stats:
        brand_name = material.brand
        is_brand_active = active_brand and brand_name.lower() == active_brand.lower()

        if brand_name not in brands_dict:
            brands_dict[brand_name] = {
                "name": brand_name,
                "material_count": 0,
                "materials": [],
                "active": is_brand_active,  # flag voor template
            }

        material_matches = True
        if not active_brand and q_brand and brand_name.lower() != q_brand.lower(): material_matches = False
        if q_type and q_type.strip() and q_type.lower() not in (material.material_type or "").lower(): material_matches = False
        if q_desc and q_desc.strip() and q_desc.lower() not in (material.description or "").lower(): material_matches = False
        if q_lifecycle and q_lifecycle.strip() and q_lifecycle.lower() not in (material.lifecycle or "").lower(): material_matches = False
        
        if q_zone and q_zone.strip() and not any(z.zone_name.lower().find(q_zone.lower()) != -1 for z in Zone.query.join(Item).filter(Item.material_id == material.material_id).all()): material_matches = False
        if filter_purpose and not any(i.purpose == filter_purpose for i in Item.query.filter_by(material_id=material.material_id).all()): material_matches = False
        if filter_packaging and not any(i.packaging == filter_packaging for i in Item.query.filter_by(material_id=material.material_id).all()): material_matches = False

        if material_matches:
            has_item_filters = filter_purpose or filter_packaging or (q_zone and q_zone.strip())
            if has_item_filters:
                filtered_quantity = db.session.query(func.coalesce(func.sum(Item.quantity), 0)).filter(Item.material_id == material.material_id)
                if filter_purpose: filtered_quantity = filtered_quantity.filter(Item.purpose == filter_purpose)
                if filter_packaging: filtered_quantity = filtered_quantity.filter(Item.packaging == filter_packaging)
                if q_zone and q_zone.strip(): filtered_quantity = filtered_quantity.join(Zone).filter(Zone.zone_name.ilike(f"%{q_zone}%"))
                filtered_count = filtered_quantity.scalar() or 0
                if filtered_count > 0:
                    brands_dict[brand_name]["material_count"] += filtered_count
                    brands_dict[brand_name]["materials"].append({"id": material.material_id, "type": material.material_type, "description": material.description, "item_count": filtered_count})
            else:
                brands_dict[brand_name]["material_count"] += total_quantity
                brands_dict[brand_name]["materials"].append({"id": material.material_id, "type": material.material_type, "description": material.description, "item_count": total_quantity})

    brands = list(brands_dict.values())
    if is_search:
        brands = [b for b in brands if b.get("materials")]
    if q_brand and q_brand.strip():
        brands = [b for b in brands if b.get("name", "").lower() == q_brand.lower()]

    return brands

def _get_inventory_items(company_name, filters):
    """Haalt de effectieve inventory items op basis van de actieve filters."""
    # Unpack filters for clarity
    active_material_id = filters["active_material_id"]
    active_brand = filters["active_brand"]
    q_brand, q_type, q_desc, q_lifecycle, q_zone, filter_purpose, filter_packaging = \
        filters["q_brand"], filters["q_type"], filters["q_desc"], filters["q_lifecycle"], filters["q_zone"], filters["filter_purpose"], filters["filter_packaging"]
    is_search = filters["is_search"]

    # Business rule: when to show items
    show_items = False
    if is_search:
        show_items = True
    elif active_material_id:
        show_items = True
    elif active_brand and is_search:
        show_items = True

    # Page title logic
    page_title = "Inventory"
    active_material = None
    if filters["active_material_id"]:
        active_material = Material.query.get(filters["active_material_id"])

    if is_search:
        if q_brand and (q_type or q_desc):
            page_title = f"{q_brand} — {q_type or q_desc}"
        elif q_brand:
            page_title = q_brand
        elif q_type or q_desc:
            page_title = q_type if q_type else q_desc
        # Anders blijft de titel "Inventory", wat correct is voor een zoekopdracht op bv. enkel zone.
    elif active_material:
        page_title = f"{active_material.brand} — {active_material.material_type}"
    elif active_brand:
        page_title = active_brand

    # Items query
    items_result = []
    if show_items:
        query = (Item.query.join(Material).join(Zone).filter(Material.company_name == company_name))

        if active_material_id:
            query = query.filter(Item.material_id == active_material_id)
        
        if active_brand and not active_material_id:
            query = query.filter(Material.brand.ilike(f"%{active_brand}%"))
        elif q_brand and q_brand.strip():
            query = query.filter(Material.brand.ilike(f"%{q_brand}%"))
        
        if q_type and q_type.strip(): query = query.filter(Material.material_type.ilike(f"%{q_type}%"))
        if q_desc and q_desc.strip(): query = query.filter(Material.description.ilike(f"%{q_desc}%"))
        if q_lifecycle and q_lifecycle.strip(): query = query.filter(Material.lifecycle.ilike(f"%{q_lifecycle}%"))
        if q_zone and q_zone.strip(): query = query.filter(Zone.zone_name.ilike(f"%{q_zone}%"))
        if filter_purpose: query = query.filter(Item.purpose == filter_purpose)
        if filter_packaging: query = query.filter(Item.packaging == filter_packaging)

        items_result = query.order_by(
            Material.brand, Material.material_type, Zone.zone_name,
            Item.purpose, Item.packaging, Item.item_id,
        ).all()
        
    return items_result, page_title, active_material, show_items

def _get_for_you_data(username_pk):
    """Haalt de 'For You' data op voor de ingelogde gebruiker."""
    if not username_pk:
        return []

    # --- EVENT LOGGING: only log when the user manually clicked a material (sidebar) ---
    personal_top_materials = []
    if username_pk:
        stats = (
            db.session.query(
                MaterialEvent.material_id,

                # totaal views per materiaal (voor deze user)
                func.sum(
                    case(
                        (MaterialEvent.event_type == "view", MaterialEvent.total_events),
                        else_=0
                    )
                ).label("views"),

                # totaal reservaties per materiaal
                func.sum(
                    case(
                        (MaterialEvent.event_type == "reserve", MaterialEvent.total_events),
                        else_=0
                    )
                ).label("reservations"),

                # laatste activiteit (view of reserve)
                func.max(MaterialEvent.date).label("last_date"),
            )
            .filter(MaterialEvent.username == username_pk)
            .group_by(MaterialEvent.material_id)
            # sortering: meest recent eerst
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
    return personal_top_materials


@main.route("/")
def inventory():
    if "username" not in session:
        return redirect(url_for("main.login"))

    # 1. Verwerk alle filters uit de request en sessie
    filters, redirect_response = _process_filters()
    if redirect_response:
        return redirect_response

    # 2. Haal data op voor de sidebar, gefilterd volgens de actieve filters
    brands = _get_sidebar_data(filters['company_name'], filters)

    # 3. Haal de inventaris-items op die getoond moeten worden
    items, page_title, active_material, show_items = _get_inventory_items(filters['company_name'], filters)
    item_count = len(items)

    # 4. Log een 'view' event als een specifiek materiaal is geselecteerd
    username_pk = session.get("username_pk") or session.get("username")
    if active_material and username_pk:
        _record_material_event(
            username=username_pk,
            material_id=active_material.material_id,
            event_type="view",
        )

    # --- Reserved totals per item ---
    reserved_totals = {
        item.item_id: sum(r.quantity for r in item.reservations)
        for item in items
    }

    # 5. Haal de lijst van alle reservaties op voor het 'winkelmandje' paneel
    reservations_raw = (
        db.session.query(Reservation, Item, Material, Zone)
        .join(Item, Reservation.item_id == Item.item_id)
        .join(Material, Item.material_id == Material.material_id)
        .join(Zone, Item.zone_id == Zone.zone_id)
        .filter(Material.company_name == filters['company_name'])
        .order_by(Reservation.date.desc())
        .all()
    )

    reservations_list = [
        {
            "reservation_id": reservation.reservation_id,
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

    # 6. Haal de 'For You' data op
    personal_top_materials = _get_for_you_data(username_pk)

    # 7. Bepaal de context voor de view
    # Wanneer moet de "For You" sectie getoond worden?
    is_manual_flow = (filters["active_brand"] or filters["active_material_id"]) and not filters["is_search"]
    show_for_you = False
    if is_manual_flow and filters["active_brand"] and not filters["active_material_id"]:
        show_for_you = True
    if not filters["active_brand"] and not filters["is_search"]:
        show_for_you = True

    # Vlaggen voor de template om de juiste layout te renderen
    manual_items_view = False
    if (not filters["is_search"] and filters["active_material_id"]) or active_material:
        manual_items_view = True
    
    search_brand = False
    if filters["is_search"] and filters["q_brand"]:
        search_brand = True
    
    # 8. Render de finale template met alle verzamelde data
    return render_template(
        "inventory.html",
        username=session["username"],
        company=filters['company_name'],
        brands=brands,
        items=items,
        active_brand=filters["active_brand"],
        active_material=active_material,
        active_material_id=filters["active_material_id"],
        item_count=item_count,
        reserved_totals=reserved_totals,
        reservations_list=reservations_list,
        zones=Zone.query.filter_by(company_name=filters['company_name']).order_by(Zone.zone_name).all(),
        q_type=filters["q_type"], q_desc=filters["q_desc"], q_brand=filters["q_brand"],
        q_zone=filters["q_zone"], q_lifecycle=filters["q_lifecycle"],
        filter_purpose=filters["filter_purpose"], filter_packaging=filters["filter_packaging"],
        personal_top_materials=personal_top_materials,
        show_items=show_items,
        show_for_you=show_for_you,
        is_search=filters["is_search"],
        manual_items_view=manual_items_view,
        search_brand=search_brand,
        page_title=page_title,
    )

# ===========================================================================
# API-LIKE ROUTES (voor AJAX-calls vanuit de frontend)
# ===========================================================================

@main.route("/brand_suggest")
def brand_suggest():
    q = (request.args.get("q") or "").strip()
    company_name = session.get("company_name")

    if not q:
        return {"suggestions": []}

    # Zoek alle merken die het typed stukje bevatten (case insensitive)
    results = (
        db.session.query(Material.brand)
        .filter(Material.company_name == company_name)
        .filter(Material.brand.ilike(f"%{q}%"))
        .distinct()
        .join(Item)
        .limit(5)
        .all()
    )

    return {"suggestions": [r[0] for r in results]}

@main.route("/material_details")
def material_details():
    brand = request.args.get("brand")
    m_type = request.args.get("type")
    exclude_id = request.args.get("exclude_id", type=int)
    company_name = session.get("company_name")

    if not brand or not m_type or not company_name:
        return jsonify({})

    query = Material.query.filter_by(
        company_name=company_name,
        brand=brand,
        material_type=m_type
    )

    if exclude_id:
        query = query.filter(Material.material_id != exclude_id)

    material = query.first()

    if material:
        return jsonify({
            "description": material.description,
            "lifecycle": material.lifecycle,
            "price": str(material.price) if material.price is not None else ""
        })
    return jsonify({})

@main.route("/item_details")
def item_details():
    """Fetch comment for an existing item configuration."""
    brand = request.args.get("brand")
    m_type = request.args.get("type")
    zone_name = request.args.get("zone")
    purpose = request.args.get("purpose")
    packaging = request.args.get("packaging")
    exclude_id = request.args.get("exclude_id", type=int)
    company_name = session.get("company_name")

    if not all([brand, m_type, zone_name, purpose, packaging, company_name]):
        return jsonify({})

    # Find material first
    material = Material.query.filter_by(
        company_name=company_name, brand=brand, material_type=m_type
    ).first()
    if not material:
        return jsonify({})

    # Find zone
    zone = Zone.query.filter_by(
        company_name=company_name, zone_name=zone_name
    ).first()
    if not zone:
        return jsonify({})

    # Find item
    query = Item.query.filter_by(
        material_id=material.material_id,
        zone_id=zone.zone_id,
        purpose=purpose,
        packaging=packaging
    )

    if exclude_id:
        query = query.filter(Item.item_id != exclude_id)

    item = query.first()
    
    if item and item.comment:
        # Return comment without the hidden marker for display
        return jsonify({"comment": item.display_comment})
    
    return jsonify({})

# ===========================================================================
# ITEM ROUTES
# ===========================================================================

@main.route("/add_item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        company_name = _get_current_company_name()

        # --- Material data ---
        brand = request.form["brand"].strip()
        material_type = request.form["material_type"].strip()
        description = request.form["description"].strip()

        # Beschrijving is altijd verplicht. De frontend validatie (HTML required attribuut)
        # zou dit al moeten afvangen, maar dit is een extra server-side garantie.
        if not description:
            flash("Description is a required field.", "error")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                # Render de partial opnieuw met de ingevulde data en een foutmelding.
                return render_template("add_item_partial.html", **request.form), 400
            return render_template("add_item.html", **request.form)

        lifecycle = request.form.get("lifecycle") or None
        
        try:
            price_raw = request.form.get("price")
            price = float(price_raw.replace(",", ".")) if price_raw else None
            quantity = int(request.form["quantity"])

            # Validate price is not negative
            if price is not None and price < 0:
                return _handle_ajax_form_error("Price must be greater than or equal to 0.",
                                               "add_item_partial.html", "add_item.html", **request.form)

            # Validate quantity is not negative
            if quantity < 0:
                return _handle_ajax_form_error("Quantity must be a non-negative number.",
                                               "add_item_partial.html", "add_item.html", **request.form)
                
        except (ValueError, TypeError):
            return _handle_ajax_form_error("Invalid number format for price or quantity.",
                                           "add_item_partial.html", "add_item.html", **request.form)

        # --- Material Logic: Find, Create, or Update ---
        material = Material.query.filter_by(
            company_name=company_name,
            brand=brand,
            material_type=material_type,
        ).first()

        if material is None:
            try:
                if not description:
                    flash("Description is required for a new material.", "error")
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return render_template("add_item_partial.html"), 400
                    return redirect(url_for("main.inventory"))
                material = Material(
                    company_name=company_name, brand=brand, material_type=material_type,
                    description=description, lifecycle=lifecycle, price=price,
                )
                db.session.add(material)
                db.session.flush()
            except ValueError as e:
                flash(f"Error creating material: {e}", "error")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return render_template("add_item_partial.html"), 400
                return redirect(url_for("main.inventory"))
        else:
            # Material exists. Update its properties from the form if the user changed them.
            try:
                material.description = description
                material.price = price
                material.lifecycle = lifecycle
            except ValueError as e:
                db.session.rollback()
                flash(f"Error updating material: {e}", "error")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return render_template("add_item_partial.html"), 400
                return redirect(url_for("main.inventory"))

        # If quantity is 0, we just created/updated the material. Commit and leave.
        # Als de hoeveelheid 0 is, hebben we enkel de materiaal-info opgeslagen/geüpdatet.
        # We voegen dan geen item toe en tonen een informatieve boodschap. Dit is de correcte werking
        # die de gebruiker in staat stelt om een materiaal aan te maken zonder direct een item toe te voegen.
        if quantity == 0:
            db.session.commit()
            flash("Material information saved. No item added as quantity was 0.", "info")
            return redirect(url_for("main.inventory", material_id=material.material_id))

        # --- Zone data ---
        zone = _find_or_create_zone(company_name, request.form["zone_name"].strip().upper())

        # --- Item data ---
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
            try:
                # ❗ Update quantity instead of creating duplicate
                existing_item.quantity += quantity
                existing_item.comment = comment # Altijd updaten, ook naar None
                flash("Item quantity updated successfully.", "success")
                db.session.commit()
            except ValueError as e:
                db.session.rollback()
                flash(f"Error updating item: {e}", "error")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return render_template("add_item_partial.html"), 400
                return redirect(url_for("main.inventory"))

            return redirect(url_for("main.inventory", material_id=material.material_id))

        # If not duplicate → create new item
        try:
            item = Item(
                material_id=material.material_id, zone_id=zone.zone_id, purpose=purpose,
                packaging=packaging, quantity=quantity, comment=comment,
            )
            db.session.add(item)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            flash(f"Error creating item: {e}", "error")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return render_template("add_item_partial.html"), 400
            return redirect(url_for("main.inventory"))

        flash("Item added successfully", "success")
        return redirect(url_for("main.inventory", material_id=material.material_id))

    # Check if this is an AJAX request (for modal)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("add_item_partial.html")
    
    return render_template("add_item.html")

@main.route("/item/<int:item_id>/use", methods=["GET", "POST"])
def use_item(item_id: int):
    """
    Verwerkt het reserveren (vroeger 'use') van een item.
    """
    item = Item.query.get_or_404(item_id)
    available = item.quantity

    if request.method == "POST":
        error_msg = None
        username = request.form["username"].strip()
        project = request.form.get("project") or None

        try:
            quantity = int(request.form["quantity"])
        except (ValueError, TypeError):
            error_msg = "Invalid quantity entered."

        user_exists = None
        if not error_msg:
            # --- User validation (case-insensitive) ---
            user_exists = User.query.filter(
                func.lower(User.username) == func.lower(username),
                User.company_name == item.material.company_name
            ).first()

            if not user_exists:
                error_msg = f"This user '{username}' does not exist in your organization."
            # --- Availability check ---
            elif quantity > available:
                error_msg = f"Not enough stock available. Available: {available}, requested: {quantity}."

        # If there was a validation error, render the form again with the error
        if error_msg:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return render_template("use_item_partial.html", item=item, available=available, error=error_msg), 400
            return render_template("use_item.html", item=item, available=available, error=error_msg)

        # --- All validation passed, proceed with reservation ---
        try:
            reservation = Reservation(
                item_id=item.item_id, username=user_exists.username, quantity=quantity, project=project
            )
            db.session.add(reservation)
            item.quantity -= quantity
            db.session.commit()
            flash(f"{quantity} item(s) reserved successfully.", "success")

            # 👉 reserve-event loggen
            _record_material_event(username=user_exists.username, material_id=item.material_id, event_type="reserve")
            return _redirect_back()
        except ValueError as e:
            db.session.rollback()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return render_template("use_item_partial.html", item=item, available=available, error=str(e)), 400
            return render_template("use_item.html", item=item, available=available, error=str(e), is_full_page=True)

    # GET request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("use_item_partial.html", item=item, available=available)
    
    return render_template("use_item.html", item=item, available=available, is_full_page=True)

@main.route("/item/<int:item_id>/quantity", methods=["POST"])
def update_quantity(item_id: int):
    """Update quantity from the inline form on the inventory page."""

    item = Item.query.get_or_404(item_id)
    new_quantity = max(int(request.form["quantity"]), 0)
    # Capture current filters to preserve navigation state
    brand = request.args.get("brand")
    material_id = request.args.get("material_id")

    # Compute reserved qty for safety
    reserved_qty = sum(r.quantity for r in item.reservations)

    if new_quantity <= 0 and reserved_qty <= 0:
        # safe to delete if nothing reserved and qty set to 0
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted as quantity was set to 0.", "info")
        return redirect(url_for("main.inventory", brand=brand, material_id=material_id))

    # otherwise update quantity (cannot go negative)
    item.quantity = new_quantity
    db.session.commit()
    flash("Quantity updated successfully.", "success")
    return redirect(url_for("main.inventory", brand=brand, material_id=material_id))


@main.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id: int):
    """Delete an item if it has no reservations."""
    
    item = Item.query.get_or_404(item_id)
    material_id = item.material_id
    material = Material.query.get(material_id)
    
    # Check if item has reservations
    reserved_qty = sum(r.quantity for r in item.reservations)
    if reserved_qty > 0:
        flash(f"Cannot delete item: {reserved_qty} items are reserved.", "error")
        return redirect(url_for("main.edit_material", material_id=material_id))
    
    db.session.delete(item)
    db.session.commit()
    flash("Item deleted successfully.", "success")
    return redirect(url_for("main.edit_material", material_id=material_id))


# ===========================================================================
# MATERIAL ROUTES
# ===========================================================================

@main.route("/material/<int:material_id>/edit", methods=["GET", "POST"])
def edit_material(material_id: int):
    """Edit brand / type / description / lifecycle / price of a material."""

    material = Material.query.get_or_404(material_id)

    # Check if the material has any associated items to control UI elements.
    has_items = Item.query.filter_by(material_id=material.material_id).first() is not None

    if request.method == "POST":
        new_brand = request.form["brand"]
        new_type = request.form["material_type"]
        
        existing_material = Material.query.filter(
            Material.material_id != material_id,
            Material.company_name == material.company_name,
            Material.brand == new_brand,
            Material.material_type == new_type
        ).first()

        if existing_material:
            # --- Merge this material into the existing one ---
            try:
                # Overwrite properties of the target material with data from the form
                existing_material.description = request.form["description"]
                existing_material.lifecycle = request.form.get("lifecycle") or None
                price_raw = request.form.get("price")
                price = float(price_raw.replace(",", ".")) if price_raw else None
                existing_material.price = price

                # Move items, merging where necessary
                for item_to_move in list(material.items):
                    conflicting_item = Item.query.filter_by(
                        material_id=existing_material.material_id,
                        zone_id=item_to_move.zone_id,
                        purpose=item_to_move.purpose,
                        packaging=item_to_move.packaging
                    ).first()

                    if conflicting_item:
                        # Merge items: sum quantity, move reservations
                        conflicting_item.quantity += item_to_move.quantity
                        for res in list(item_to_move.reservations):
                            res.item = conflicting_item # Re-parent reservation
                        db.session.flush() # Persist reservation moves before deleting item
                        db.session.delete(item_to_move)
                    else:
                        # Just move the item
                        item_to_move.material = existing_material # Re-parent item
                
                # Move material events, merging where necessary
                for event_to_move in list(material.material_events):
                    conflicting_event = MaterialEvent.query.filter_by(
                        username=event_to_move.username,
                        material_id=existing_material.material_id,
                        event_type=event_to_move.event_type
                    ).first()

                    if conflicting_event:
                        conflicting_event.total_events += event_to_move.total_events
                        if event_to_move.date > conflicting_event.date:
                            conflicting_event.date = event_to_move.date
                        db.session.delete(event_to_move)
                    else:
                        event_to_move.material = existing_material # Re-parent event
                
                # Flush changes to prevent NOT NULL violation before deleting the old material
                db.session.flush()

                # Delete the old, now empty, material
                db.session.delete(material)
                db.session.commit()
                flash("Material updated and merged with an existing material.", "success")
                return redirect(url_for("main.inventory", material_id=existing_material.material_id))
            except Exception as e:
                db.session.rollback()
                error_msg = f"Error merging materials: {e}"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return render_template("edit_material_partial.html", material=material, has_items=has_items, error=error_msg), 400
                flash(error_msg, "error")
                return render_template("edit_material.html", material=material, has_items=has_items)

        try:
            material.brand = new_brand
            material.material_type = new_type
            material.description = request.form["description"]
            material.lifecycle = request.form.get("lifecycle") or None
            price_raw = request.form.get("price")
            price = float(price_raw.replace(",", ".")) if price_raw else None
            material.price = price
            db.session.commit()
            flash("Material updated successfully.", "success")
        except ValueError as e:
            db.session.rollback()
            error_msg = str(e)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return render_template("edit_material_partial.html", material=material, has_items=has_items, error=error_msg), 400
            flash(error_msg, "error")
            return render_template("edit_material.html", material=material, has_items=has_items)

        return redirect(
            url_for(
                "main.inventory",
                brand=material.brand,
                material_id=material.material_id,
            )
        )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("edit_material_partial.html", material=material, has_items=has_items)

    return render_template("edit_material.html", material=material, has_items=has_items, is_full_page=True)


@main.route("/material/<int:material_id>/delete", methods=["POST"])
def delete_material(material_id: int):
    """Delete a material and all its items from the database."""
    material = Material.query.get_or_404(material_id)

    # Prevent deletion if the material still has items associated with it.
    if Item.query.filter_by(material_id=material_id).first():
        flash("Cannot delete material: it still has items in inventory. Please delete the items first.", "error")
        return redirect(url_for("main.edit_material", material_id=material_id))

    try:
        # If we are here, there are no items. We can safely delete related events and the material.
        # Delete material events for this material
        MaterialEvent.query.filter_by(material_id=material_id).delete()

        # Delete the material
        db.session.delete(material)
        db.session.commit()

        flash("Material deleted successfully.", "success")
        return redirect(url_for("main.inventory"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting material: {str(e)}", "error")
        return redirect(url_for("main.edit_material", material_id=material_id))


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
    
    company_name = item.material.company_name
    zones = Zone.query.filter_by(company_name=company_name).order_by(Zone.zone_name).all()

    if request.method == "POST":
        # Zone is free text: look it up or create it.
        zone_name = request.form["zone_name"].strip().upper()
        zone = _find_or_create_zone(company_name, zone_name)

        # Check for existing item with the new properties (UC3)
        existing_item = Item.query.filter(
            Item.item_id != item_id,
            Item.material_id == item.material_id,
            Item.zone_id == zone.zone_id,
            Item.purpose == request.form["purpose"],
            Item.packaging == request.form["packaging"]
        ).first()

        if existing_item:
            # Merge into existing item
            try:
                existing_item.quantity += item.quantity
                # Preserve changed marker if item was changed, otherwise use new comment
                new_comment = request.form.get("comment") or None
                was_changed = item.is_changed
                if was_changed and new_comment:
                    # Preserve marker in new comment
                    if Item._CHANGED_MARKER not in new_comment:
                        existing_item.comment = new_comment + Item._CHANGED_MARKER
                    else:
                        existing_item.comment = new_comment
                elif was_changed and not new_comment:
                    # Keep marker even if comment is empty
                    existing_item.comment = Item._CHANGED_MARKER
                else:
                    existing_item.comment = new_comment

                # Move reservations to the target item
                for r in list(item.reservations):
                    r.item = existing_item # Re-parenting is the idiomatic way

                # Flush the session to persist the re-parenting before deleting the old item
                db.session.flush()

                db.session.delete(item)
                db.session.commit()
                flash("Item updated and merged with an existing item.", "success")
                return redirect(url_for("main.inventory", material_id=item.material_id))
            except Exception as e:
                db.session.rollback()
                error_msg = f"Error merging items: {e}"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return render_template("edit_item_partial.html", item=item, zones=zones, error=error_msg), 400
                flash(error_msg, "error")
                return render_template("edit_item.html", item=item, zones=zones, error=error_msg)

        # If no duplicate, just update the item
        try:
            item.zone_id = zone.zone_id # zone_id is now set
            item.purpose = request.form["purpose"]
            item.packaging = request.form["packaging"]
            # Preserve changed marker if item was changed
            new_comment = request.form.get("comment") or None
            was_changed = item.is_changed
            if was_changed and new_comment:
                # Preserve marker in new comment
                if Item._CHANGED_MARKER not in new_comment:
                    item.comment = new_comment + Item._CHANGED_MARKER
                else:
                    item.comment = new_comment
            elif was_changed and not new_comment:
                # Keep marker even if comment is empty
                item.comment = Item._CHANGED_MARKER
            else:
                item.comment = new_comment
            db.session.commit()
            flash("Item updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error updating item: {e}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return render_template("edit_item_partial.html", item=item, zones=zones, error=error_msg), 400
            flash(error_msg, "error")
            return render_template("edit_item.html", item=item, zones=zones, error=error_msg)

        return redirect(
            url_for(
                "main.inventory",
                brand=item.material.brand,
                material_id=item.material_id,
            )
        )

    # GET request - return partial for modal (AJAX) or full page for direct access
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("edit_item_partial.html", item=item, zones=zones)
    
    # If accessed directly (not via AJAX), return full page
    return render_template("edit_item.html", item=item, zones=zones, is_full_page=True)


# ===========================================================================
# RESERVATION ROUTES
# ===========================================================================

@main.route("/reservation/<int:reservation_id>/return", methods=["GET", "POST"])
def return_item(reservation_id):
    """
    Toon een pagina om een gereserveerd item te verwerken. De gebruiker kan
    meerdere acties (terug naar stock, weggooien, markeren als gewijzigd)
    combineren voor verschillende hoeveelheden van dezelfde reservatie.
    """
    reservation = Reservation.query.get_or_404(reservation_id)
    item = Item.query.get_or_404(reservation.item_id)

    # --- POST: Verwerk de gekozen actie ---
    if request.method == "POST":
        error_msg = None
        # Haal hoeveelheden op voor elke mogelijke actie
        try:
            qty_stock = int(request.form.get("qty_return_to_stock") or 0)
            qty_discard = int(request.form.get("qty_discard") or 0)
            qty_changed = int(request.form.get("qty_mark_changed") or 0)
        except (ValueError, TypeError):
            error_msg = "Invalid quantity entered."
            qty_stock, qty_discard, qty_changed = 0, 0, 0

        # Validatie
        total_qty_processed = qty_stock + qty_discard + qty_changed
        if not error_msg:
            if total_qty_processed > reservation.quantity:
                error_msg = "Specified quantities are more than the reserved quantity."
            elif total_qty_processed <= 0:
                error_msg = "Specify a quantity for at least one action." 

            if qty_changed > 0:
                purpose = request.form.get("purpose")
                packaging = request.form.get("packaging")
                zone_name = request.form.get("zone_name", "").strip().upper()
                if not all([purpose, packaging, zone_name]):
                    error_msg = "Voor 'markeer als gewijzigd' zijn zone, doel en verpakking vereist."

        if error_msg:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                company_name = item.material.company_name
                zones = Zone.query.filter_by(company_name=company_name).order_by(Zone.zone_name).all()
                return render_template("return_item_partial.html", reservation=reservation, item=item, zones=zones, error=error_msg), 400
            flash(error_msg, "error") # flash() is called inside the helper
            return redirect(url_for(".return_item", reservation_id=reservation_id))

        # --- Verwerk actie: Terug naar stock ---
        if qty_stock > 0:
            item.quantity += qty_stock
            flash(f"{qty_stock} item(s) returned to stock.", "success")

        # --- Verwerk actie: Weggooien ---
        if qty_discard > 0:
            # Items worden niet teruggestort in de voorraad, maar gewoon afgeschreven.
            flash(f"{qty_discard} item(s) discarded.", "success")

        # --- Verwerk actie: Markeer als gewijzigd ---
        if qty_changed > 0:
            purpose = request.form.get("purpose")
            packaging = request.form.get("packaging")
            zone = _find_or_create_zone(item.material.company_name, request.form.get("zone_name", "").strip().upper())

            # Zoek of er al een item met exact dezelfde nieuwe eigenschappen bestaat
            existing_item = Item.query.filter_by(
                material_id=item.material_id,
                zone_id=zone.zone_id,
                purpose=purpose,
                packaging=packaging
            ).first()

            if existing_item:
                existing_item.quantity += qty_changed
                # Add marker to comment if not already present
                if existing_item.comment and Item._CHANGED_MARKER not in existing_item.comment:
                    existing_item.comment = existing_item.comment + Item._CHANGED_MARKER
                elif not existing_item.comment:
                    existing_item.comment = Item._CHANGED_MARKER
                target_item_id = existing_item.item_id
            else:
                # Preserve the original comment if it exists, otherwise leave it None
                original_comment = item.comment
                # Add marker to indicate this is a changed item
                if original_comment:
                    new_comment = original_comment + Item._CHANGED_MARKER
                else:
                    new_comment = Item._CHANGED_MARKER
                    
                new_item = Item(
                    material_id=item.material_id,
                    zone_id=zone.zone_id,
                    purpose=purpose,
                    packaging=packaging,
                    quantity=qty_changed,
                    comment=new_comment  # Keep original comment + hidden marker
                )
                db.session.add(new_item)
                db.session.flush()  # ensure item_id is available
                target_item_id = new_item.item_id

            flash(f"{qty_changed} item(s) marked as changed.", "success")

        # --- Werk de oorspronkelijke reservatie bij ---
        new_res_quantity = reservation.quantity - total_qty_processed
        if new_res_quantity <= 0:
            # Verwijder de reservatie als de hoeveelheid 0 of minder is
            db.session.delete(reservation)
        else:
            # Anders, update de hoeveelheid (dit voorkomt de ValueError van de validator)
            reservation.quantity = new_res_quantity

        # Als het item geen voorraad meer heeft en geen reservaties, verwijder het dan.
        # De 'item.reservations' collectie is bijgewerkt in de sessie na de delete/update hierboven.
        if item.quantity <= 0 and not item.reservations:
            db.session.delete(item)
            flash("Item has been removed as its quantity is zero and it has no pending reservations.", "info")

        # Commit alle wijzigingen in één transactie
        db.session.commit()

        return redirect(url_for("main.inventory"))

    # --- GET: Toon de return-pagina ---
    company_name = item.material.company_name
    zones = Zone.query.filter_by(company_name=company_name).order_by(Zone.zone_name).all()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("return_item_partial.html", reservation=reservation, item=item, zones=zones)

    return render_template("return_item.html", reservation=reservation, item=item, zones=zones, is_full_page=True)


@main.route("/reservation/delete", methods=["POST"])
def delete_reservation():
    """
    Verwijder een volledige reservatie en plaats de items terug in de voorraad.
    Dit is een snelle actie vanuit het winkelmandje.
    """
    # Gebruik de unieke reservation_id die vanuit de form wordt gepost
    reservation_id = request.form.get("reservation_id", type=int)
    if not reservation_id:
        abort(400, "Reservation ID is vereist.")

    reservation = Reservation.query.get_or_404(reservation_id)

    # Voeg de hoeveelheid terug toe aan de item stock
    item = Item.query.get(reservation.item_id)
    if item:
        item.quantity += reservation.quantity

    db.session.delete(reservation)
    db.session.commit()

    return _redirect_back()


# ===========================================================================
# 'FOR YOU' ROUTES
# ===========================================================================

@main.route("/for_you/clear", methods=["POST"])
def clear_for_you():
    """Alle persoonlijke aanbevelingen wissen voor de ingelogde gebruiker."""
    username = session.get("username_pk")
    if not username:
        return redirect(url_for("main.login"))

    MaterialEvent.query.filter_by(username=username).delete()
    db.session.commit()

    flash("Your 'For you' list has been cleared.", "success")
    return redirect(url_for("main.inventory"))


@main.route("/for_you/<int:material_id>/remove", methods=["POST"])
def remove_for_you_material(material_id):
    """Eén materiaal uit 'For you' verwijderen voor deze gebruiker."""
    username = session.get("username_pk")
    if not username:
        return redirect(url_for("main.login"))

    MaterialEvent.query.filter_by(username=username, material_id=material_id).delete()
    db.session.commit()

    flash("Material removed from your 'For you' list.", "success")
    return redirect(url_for("main.inventory"))
