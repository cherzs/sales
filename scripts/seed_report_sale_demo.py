"""Seed data that resembles the provided real documents.

Usage from Odoo shell:
    ./odoo/odoo-bin shell -c odoo18sale.conf -d ReportSale
    >>> exec(open('/Users/mac/Documents/Dev/work/sales/scripts/seed_report_sale_demo.py').read())
    >>> seed_report_sale_demo(env, order_count=3)
"""

from datetime import timedelta

from odoo import fields

DEMO_PREFIX = "SEED-RPT"

CUSTOMERS = [
    {
        "name": "PT. Sawit Mas Sejahtera",
        "street": "Gedung Sinar Mas Land Plaza Menara 2 Lt.30",
        "street2": "Jl. MH Thamrin No.51, Gondangdia",
        "city": "Jakarta Pusat",
        "zip": "10350",
        "vat": "001220467309200000000",
    },
    {
        "name": "PT. Forestalestari Dwikarya",
        "street": "Gedung Sinar Mas Land Plaza",
        "street2": "Jl. MH Arsyad No.88, KM 3,5",
        "city": "Tanjung Pandan",
        "zip": "33411",
        "vat": "013592126092000",
    },
    {
        "name": "PT. Mitrakarya Agroindo",
        "street": "Gedung Sinar Mas Land Plaza",
        "street2": "Jl. MH. Thamrin No.51",
        "city": "Jakarta Pusat",
        "zip": "10350",
        "vat": "022754832073000",
    },
]

PRODUCTS = [
    ("KLS/CH3 HARVESTING CHISEL / DODOS 3\"", "KLS-CH3", "EA", 78200.0, 53000.0),
    ("ZY-001 SA-GRUNI HAND SPRAYER RB-15/SA-15, MALAYSIA", "ZY-001", "UN", 858000.0, 620000.0),
    ("Sepatu Boots PVC 8\"", "BOOT-8", "PR", 76700.0, 51000.0),
    ("Sepatu Boots PVC 10\"", "BOOT-10", "PR", 105000.0, 70000.0),
    ("Kereta Sorong (Angkong) Roda Satu", "ANGKONG-1", "PCS", 1040000.0, 790000.0),
]


def _upsert_partner(env, vals):
    partner = env["res.partner"].search(
        [("name", "=", vals["name"]), ("is_company", "=", True)], limit=1
    )
    if partner:
        partner.write(vals)
    else:
        vals["is_company"] = True
        vals["customer_rank"] = 1
        partner = env["res.partner"].create(vals)
    return partner


def _upsert_product(env, name, code, customer_uom, sale_price, cost):
    product = env["product.product"].search([("default_code", "=", code)], limit=1)
    unit = env.ref("uom.product_uom_unit")
    vals = {
        "name": name,
        "default_code": code,
        "is_storable": True,
        "uom_id": unit.id,
        "uom_po_id": unit.id,
        "list_price": sale_price,
        "standard_price": cost,
    }
    if product:
        product.write(vals)
    else:
        product = env["product.product"].create(vals)

    return product, customer_uom


def _ensure_stock(env, products, quantity=500.0):
    stock_location = env.ref("stock.stock_location_stock")
    for product in products:
        quant = env["stock.quant"].search(
            [("product_id", "=", product.id), ("location_id", "=", stock_location.id)],
            limit=1,
        )
        if not quant:
            quant = env["stock.quant"].create(
                {
                    "product_id": product.id,
                    "location_id": stock_location.id,
                    "inventory_quantity": quantity,
                }
            )
        else:
            quant.inventory_quantity = max(quant.quantity, quantity)
        quant.with_context(set_inventory_quantity_auto_apply=True).action_apply_inventory()


def _build_order_lines(sol_model, order, catalog, idx):
    line_specs = []
    if idx % 3 == 1:
        line_specs = [
            (catalog[0], 20.0, "EA"),
            (catalog[1], 10.0, "UN"),
        ]
    elif idx % 3 == 2:
        line_specs = [
            (catalog[2], 260.0, "PR"),
            (catalog[3], 159.0, "PR"),
            (catalog[3], 161.0, "PR"),
            (catalog[3], 194.0, "Units"),
        ]
    else:
        line_specs = [
            (catalog[4], 2.0, "PCS"),
        ]

    for product, qty, uom_txt in line_specs:
        vals = {
            "order_id": order.id,
            "product_id": product.id,
            "product_uom_qty": qty,
            "price_unit": product.list_price,
        }
        if "customer_description" in sol_model._fields:
            vals["customer_description"] = product.name
        if "customer_uom" in sol_model._fields:
            vals["customer_uom"] = uom_txt
        sol_model.create(vals)


def _set_extra_notes(order, invoice):
    shipping_note = (
        "Mohon ditandatangani dan cap perusahaan sebanyak 3 kali, "
        "Lembar 1: Penagihan, Lembar 2: Gudang, Lembar 3: Ekspedisi."
    )
    for picking in order.picking_ids:
        picking.note = shipping_note

    if invoice:
        invoice.narration = (
            "Untuk kebutuhan APD-SM 2026 kebun TKME.\n"
            "Ukuran sepatu:\n"
            "37: 25 PR\n"
            "38: 116 PR\n"
            "39: 119 PR"
        )


def _validate_pickings(pickings):
    """Validate pickings through standard flow and auto-resolve wizards."""
    if not pickings:
        return

    pickings.action_assign()
    for ml in pickings.move_line_ids:
        ml.quantity = ml.move_id.product_uom_qty or ml.quantity or 1.0

    result = pickings.button_validate()
    if isinstance(result, dict) and result.get("res_model") == "stock.immediate.transfer":
        wiz = pickings.env[result["res_model"]].browse(result.get("res_id"))
        wiz.process()
    elif isinstance(result, dict) and result.get("res_model") == "stock.backorder.confirmation":
        wiz = pickings.env[result["res_model"]].browse(result.get("res_id"))
        wiz.process()


def seed_report_sale_demo(env, order_count=3, commit=True):
    """Create SO/DO/Invoice demo documents similar to provided examples."""
    company = env.company
    warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
    pricelist = env["product.pricelist"].search(
        [("company_id", "in", [False, company.id])], limit=1
    )
    incoterm = env["account.incoterms"].search([], limit=1)

    so_model = env["sale.order"]
    sol_model = env["sale.order.line"]
    inv_model = env["account.move"]
    partners = [_upsert_partner(env, vals.copy()) for vals in CUSTOMERS]
    product_catalog = [_upsert_product(env, *vals)[0] for vals in PRODUCTS]

    _ensure_stock(env, product_catalog)

    created_orders = env["sale.order"]
    base_date = fields.Datetime.now()

    for idx in range(1, order_count + 1):
        partner = partners[(idx - 1) % len(partners)]
        so_vals = {
            "company_id": company.id,
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner.id,
            "date_order": base_date - timedelta(days=idx),
            "client_order_ref": f"4900{idx:06d}",
            "origin": f"{DEMO_PREFIX}-{idx:03d}",
        }
        if warehouse:
            so_vals["warehouse_id"] = warehouse.id
        if pricelist:
            so_vals["pricelist_id"] = pricelist.id
        if "franco" in so_model._fields:
            so_vals["franco"] = "Franco Palembang"
        if "incoterm" in so_model._fields and incoterm:
            so_vals["incoterm"] = incoterm.id
        if "incoterm_location" in so_model._fields:
            so_vals["incoterm_location"] = "Plant: Sungai Musi Estate"
        if "commitment_date" in so_model._fields:
            so_vals["commitment_date"] = base_date + timedelta(days=30)

        order = so_model.create(so_vals)
        _build_order_lines(sol_model, order, product_catalog, idx)
        order.action_confirm()

        pickings = order.picking_ids
        if pickings:
            _validate_pickings(pickings)

        invoices = order._create_invoices()
        draft_invoices = invoices.filtered(lambda m: m.state == "draft")
        if draft_invoices:
            draft_invoices.action_post()

        invoice = invoices[:1] if invoices else env["account.move"]
        if invoice:
            invoice.write({"ref": f"{so_vals['client_order_ref']}-{idx:02d}"})
            _set_extra_notes(order, invoice)

        created_orders |= order

    result = {
        "orders": created_orders.mapped("name"),
        "pickings": created_orders.mapped("picking_ids.name"),
        "invoices": inv_model.search(
            [("invoice_origin", "in", created_orders.mapped("name"))]
        ).mapped("name"),
    }
    if commit:
        env.cr.commit()
    print("Seed completed:", result)
    return result

