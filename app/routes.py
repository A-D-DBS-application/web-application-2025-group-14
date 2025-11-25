from flask import Blueprint, request, redirect, url_for, render_template, session
from .models import db, Material, Zone, Item, Reservation

from sqlalchemy import func


main = Blueprint('main', __name__)

#Bovenstaande code niet aanpassen!!!

@main.route('/')
def inventory():
    active_brand = request.args.get('brand')
    active_type = request.args.get('type')

    # 1) Merken + aantallen voor de sidebar
    type_stats = (
        db.session.query(
            Material.brand,
            Material.material_type,
            func.count(Item.item_id)
        )
        .join(Item)
        .group_by(Material.brand, Material.material_type)
        .all()
    )

    brand_groups = {}
    for brand, mat_type, count in type_stats:
        if brand not in brand_groups:
            brand_groups[brand] = {"total": 0, "types": []}
        brand_groups[brand]["total"] += count
        brand_groups[brand]["types"].append({
            "material_type": mat_type,
            "count": count,
        })

<<<<<<< HEAD
<<<<<<< HEAD
    # 2) Items voor de hoofd-lijst
    query = Item.query.join(Material).join(Zone)

    if active_brand:
        query = query.filter(Material.brand == active_brand)
    if active_type:
        query = query.filter(Material.material_type == active_type)

    items = query.all()

    # Aantal gevonden items (voor de subtitel)
    item_count = len(items)

    return render_template(
        'inventory.html',
        brand_groups=brand_groups,
        items=items,
        active_brand=active_brand,
        active_type=active_type,
        item_count=item_count,
    )


@main.route('/item/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        material_id = request.form['material_id']
        zone_name = request.form['zone_name']
        purpose = request.form['purpose']
        packaging = request.form['packaging']
        quantity = int(request.form['quantity'])
        comment = request.form.get('comment')

        item = Item(
            material_id=material_id,
            zone_name=zone_name,
            purpose=purpose,
            packaging=packaging,
            quantity=quantity,
            comment=comment
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('main.inventory'))

    return render_template('add_item.html')

@main.route('/item/<int:item_id>/use', methods=['GET', 'POST'])
def use_item(item_id):
    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        username = request.form['username']
        project = request.form.get('project')
        quantity = int(request.form['quantity'])

        reservation = Reservation(
            item_id=item.item_id,
            username=username,
            quantity=quantity,
            project=project
        )
        db.session.add(reservation)
        # eventueel: item.quantity -= quantity
        db.session.commit()
        return redirect(url_for('main.inventory'))

    return render_template('use_item.html', item=item)
=======
#Tot hier ben k geraakt nu ben ik er niet zeker van hoe het verder moet. Dit heb ik zo goed mogelijk proberen doen adhv UI prototype.