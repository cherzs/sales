"""Seed demo data for Stock Card Report — multiple warehouses with stock movements.

Usage from Odoo shell:
    ./odoo/odoo-bin shell -c odoo.conf -d your_db
    >>> exec(open('/Users/mac/Documents/Dev/work/sales/scripts/seed_stock_card_demo.py').read())
    >>> seed_stock_card_demo(env)
"""

from datetime import datetime, timedelta

WAREHOUSES = [
    ("Jakarta",          "JKT"),
    ("Pekanbaru",        "PKU"),
    ("Samarinda",        "SMP"),
    ("Palembang",        "PLM"),
    ("Riau",             "RPR"),
    ("Kalimantan Sel.",  "KSY"),
    ("Citraland",        "CTR"),
    ("Jakarta Selatan",  "JKT-S"),
    ("Jakarta Barat",    "JKT-B"),
    ("Jakarta Timur",    "JKT-T"),
    ("Sulawesi",         "SLH"),
]

PRODUCTS = [
    ("BOSCH Battery N70ZL \"DC\"",          "75D31L"),
    ("BOSCH Battery N70Z \"DC\"",           "75D31R-DC"),
    ("Battery 80D26L - 0092S37057 HKL",    "80D26L"),
    ("HOSE NUT P/N 291",                    "291-EA"),
    ("SEPATU BOOTS PVC 10\"",               "ACC 005/37"),
    ("Kereta Sorong Roda Satu",             "ANGKONG-1"),
    ("Helm Safety Proyek",                  "HS-001"),
    ("Sarung Tangan Kulit",                 "SGT-KLT"),
]

VENDORS = [
    "PT. Meganusa Intisawit",
    "PT. Bhakti Manunggal Karya",
    "CV. Indo Teknik Mandiri",
    "PT. Global Supply Indonesia",
]

CUSTOMERS = [
    "PT. Sawit Mas Sejahtera",
    "PT. Forestalestari Dwikarya",
    "AYENT",
]


def _get_or_create_partner(env, name, is_vendor=False, is_customer=False):
    partner = env["res.partner"].search([("name", "=", name)], limit=1)
    if not partner:
        partner = env["res.partner"].create({
            "name": name,
            "is_company": True,
            "supplier_rank": 1 if is_vendor else 0,
            "customer_rank": 1 if is_customer else 0,
        })
    return partner


def _get_or_create_product(env, name, code, company_id):
    product = env["product.product"].search([("default_code", "=", code)], limit=1)
    if not product:
        unit = env.ref("uom.product_uom_unit")
        product = env["product.product"].create({
            "name": name,
            "default_code": code,
            "is_storable": True,
            "type": "consu",
            "uom_id": unit.id,
            "uom_po_id": unit.id,
            "company_id": company_id,
        })
    return product


def _get_or_create_warehouse(env, name, code, company_id):
    wh = env["stock.warehouse"].search([("code", "=", code), ("company_id", "=", company_id)], limit=1)
    if not wh:
        wh = env["stock.warehouse"].create({
            "name": name,
            "code": code,
            "company_id": company_id,
        })
    return wh


def _validate_picking(picking):
    picking.action_assign()
    for ml in picking.move_line_ids:
        ml.quantity = ml.move_id.product_uom_qty or ml.quantity or 1.0
    result = picking.button_validate()
    if isinstance(result, dict):
        res_model = result.get("res_model", "")
        res_id = result.get("res_id")
        if res_model and res_id:
            wiz = picking.env[res_model].browse(res_id)
            if hasattr(wiz, "process"):
                wiz.process()


def _create_receipt(env, warehouse, product, qty, vendor, date_offset_days=0):
    """Create a validated purchase receipt (vendor → warehouse stock)."""
    picking_type = warehouse.in_type_id
    src_location = env.ref("stock.stock_location_suppliers")
    dest_location = warehouse.lot_stock_id

    picking = env["stock.picking"].create({
        "picking_type_id": picking_type.id,
        "location_id": src_location.id,
        "location_dest_id": dest_location.id,
        "partner_id": vendor.id,
        "scheduled_date": datetime.now() - timedelta(days=date_offset_days),
    })
    env["stock.move"].create({
        "name": product.name,
        "product_id": product.id,
        "product_uom_qty": qty,
        "product_uom": product.uom_id.id,
        "picking_id": picking.id,
        "location_id": src_location.id,
        "location_dest_id": dest_location.id,
    })
    _validate_picking(picking)
    return picking


def _create_delivery(env, warehouse, product, qty, customer, date_offset_days=0):
    """Create a validated delivery order (warehouse stock → customer)."""
    picking_type = warehouse.out_type_id
    src_location = warehouse.lot_stock_id
    dest_location = env.ref("stock.stock_location_customers")

    picking = env["stock.picking"].create({
        "picking_type_id": picking_type.id,
        "location_id": src_location.id,
        "location_dest_id": dest_location.id,
        "partner_id": customer.id,
        "scheduled_date": datetime.now() - timedelta(days=date_offset_days),
    })
    env["stock.move"].create({
        "name": product.name,
        "product_id": product.id,
        "product_uom_qty": qty,
        "product_uom": product.uom_id.id,
        "picking_id": picking.id,
        "location_id": src_location.id,
        "location_dest_id": dest_location.id,
    })
    _validate_picking(picking)
    return picking


def _create_internal_transfer(env, wh_src, wh_dest, product, qty, date_offset_days=0):
    """Create a validated internal transfer between two warehouses."""
    company = wh_src.company_id
    picking_type = env["stock.picking.type"].search([
        ("code", "=", "internal"),
        ("warehouse_id", "=", wh_src.id),
    ], limit=1)
    if not picking_type:
        picking_type = env["stock.picking.type"].search([
            ("code", "=", "internal"),
            ("company_id", "=", company.id),
        ], limit=1)

    src_location = wh_src.lot_stock_id
    dest_location = wh_dest.lot_stock_id

    partner = env["res.partner"].search([("supplier_rank", ">", 0)], limit=1)

    picking = env["stock.picking"].create({
        "picking_type_id": picking_type.id,
        "location_id": src_location.id,
        "location_dest_id": dest_location.id,
        "scheduled_date": datetime.now() - timedelta(days=date_offset_days),
        "partner_id": partner.id if partner else False,
    })
    env["stock.move"].create({
        "name": product.name,
        "product_id": product.id,
        "product_uom_qty": qty,
        "product_uom": product.uom_id.id,
        "picking_id": picking.id,
        "location_id": src_location.id,
        "location_dest_id": dest_location.id,
    })
    _validate_picking(picking)
    return picking


def seed_stock_card_demo(env, commit=True):
    """
    Create warehouses, products, and stock movements for Stock Card Report demo.
    Run without location filter → will produce one sheet per warehouse.
    """
    company = env.company
    company_id = company.id

    print("Creating vendors & customers...")
    vendors = [_get_or_create_partner(env, n, is_vendor=True) for n in VENDORS]
    customers = [_get_or_create_partner(env, n, is_customer=True) for n in CUSTOMERS]

    print("Creating products...")
    products = [_get_or_create_product(env, name, code, company_id) for name, code in PRODUCTS]

    print("Creating warehouses...")
    warehouses = [_get_or_create_warehouse(env, name, code, company_id) for name, code in WAREHOUSES]

    print("Creating stock movements...")

    # Give each warehouse an initial stock via receipts, then some deliveries & internal transfers
    for i, wh in enumerate(warehouses):
        vendor = vendors[i % len(vendors)]
        customer = customers[i % len(customers)]

        for j, product in enumerate(products):
            # Receipt: initial stock (older date)
            try:
                _create_receipt(env, wh, product, qty=10 + j * 2, vendor=vendor, date_offset_days=30 + j)
                print(f"  Receipt: {wh.code} - {product.default_code} qty {10 + j * 2}")
            except Exception as e:
                print(f"  [SKIP receipt] {wh.code} - {product.default_code}: {e}")

            # Delivery: some outgoing stock
            if j % 2 == 0:
                try:
                    _create_delivery(env, wh, product, qty=2 + j, customer=customer, date_offset_days=15 + j)
                    print(f"  Delivery: {wh.code} - {product.default_code} qty {2 + j}")
                except Exception as e:
                    print(f"  [SKIP delivery] {wh.code} - {product.default_code}: {e}")

        # Internal transfer to next warehouse (circular)
        next_wh = warehouses[(i + 1) % len(warehouses)]
        product = products[i % len(products)]
        try:
            _create_internal_transfer(env, wh, next_wh, product, qty=3, date_offset_days=7)
            print(f"  IT: {wh.code} → {next_wh.code} - {product.default_code} qty 3")
        except Exception as e:
            print(f"  [SKIP IT] {wh.code} → {next_wh.code}: {e}")

    if commit:
        env.cr.commit()

    print("\n=== Seed completed ===")
    print(f"Warehouses: {[w.code for w in warehouses]}")
    print(f"Products  : {[p.default_code for p in products]}")
    print("\nRun Stock Card Report without location filter to see all warehouse tabs.")
