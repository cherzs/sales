"""Seed SO backdate scenarios using sale.order.document_date.

Usage from Odoo shell:
    ./odoo/odoo-bin shell -c odoo18sale.conf -d <db_name>
    >>> exec(open('/Users/mac/Documents/Dev/work/sales/scripts/seed_so_document_date_backdate.py').read())
    >>> seed_so_document_date_backdate(env, order_count=4, commit=True)
"""

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError


DEMO_PREFIX = "SEED-BACKDATE"

CUSTOMERS = [
    {
        "name": "PT. Backdate Sawit Nusantara",
        "street": "Jl. Jenderal Sudirman Kav. 58",
        "city": "Jakarta Selatan",
        "zip": "12190",
    },
    {
        "name": "PT. Backdate Agro Lestari",
        "street": "Jl. Gatot Subroto No. 10",
        "city": "Palembang",
        "zip": "30137",
    },
]

PRODUCTS = [
    ("Backdate Safety Boots PVC 10", "BD-BOOT-10", 125000.0, 90000.0),
    ("Backdate Sprayer RB-15", "BD-SPRAYER-15", 925000.0, 710000.0),
    ("Backdate Harvesting Chisel", "BD-CHISEL-3", 86000.0, 60000.0),
]


def _upsert_partner(env, values):
    partner = env["res.partner"].search(
        [("name", "=", values["name"]), ("is_company", "=", True)],
        limit=1,
    )
    if partner:
        partner.write(values)
    else:
        create_vals = dict(values, is_company=True, customer_rank=1)
        partner = env["res.partner"].create(create_vals)
    return partner


def _upsert_product(env, name, code, list_price, cost):
    unit = env.ref("uom.product_uom_unit")
    product = env["product.product"].search([("default_code", "=", code)], limit=1)
    vals = {
        "name": name,
        "default_code": code,
        "is_storable": True,
        "uom_id": unit.id,
        "uom_po_id": unit.id,
        "list_price": list_price,
        "standard_price": cost,
    }
    if product:
        product.write(vals)
    else:
        product = env["product.product"].create(vals)
    return product


def _ensure_stock(env, products, quantity=300.0):
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


def _validate_pickings(pickings):
    if not pickings:
        return
    pickings.action_assign()
    for move_line in pickings.move_line_ids:
        move_line.quantity = move_line.move_id.product_uom_qty or move_line.quantity or 1.0
    result = pickings.button_validate()
    if isinstance(result, dict) and result.get("res_model") == "stock.immediate.transfer":
        pickings.env[result["res_model"]].browse(result["res_id"]).process()
    elif isinstance(result, dict) and result.get("res_model") == "stock.backorder.confirmation":
        pickings.env[result["res_model"]].browse(result["res_id"]).process()


def seed_so_document_date_backdate(env, order_count=4, commit=True):
    """Create confirmed SO/DO/Invoice with document_date backdate cases."""
    if "document_date" not in env["sale.order"]._fields:
        raise UserError("Field sale.order.document_date tidak ditemukan. Upgrade sale_recap_report dulu.")

    company = env.company
    so_model = env["sale.order"]
    sol_model = env["sale.order.line"]
    warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
    pricelist = env["product.pricelist"].search([("company_id", "in", [False, company.id])], limit=1)
    incoterm = env["account.incoterms"].search([], limit=1)

    partners = [_upsert_partner(env, vals.copy()) for vals in CUSTOMERS]
    products = [_upsert_product(env, *vals) for vals in PRODUCTS]
    _ensure_stock(env, products)

    now_dt = fields.Datetime.now()
    created_orders = env["sale.order"]

    for idx in range(1, order_count + 1):
        partner = partners[(idx - 1) % len(partners)]
        date_order = now_dt - timedelta(days=idx - 1)
        document_date = (date_order - timedelta(days=10 + idx)).date()

        so_vals = {
            "company_id": company.id,
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner.id,
            "date_order": date_order,
            "document_date": document_date,
            "client_order_ref": f"BDOC-{idx:05d}",
            "origin": f"{DEMO_PREFIX}-{idx:03d}",
        }
        if warehouse:
            so_vals["warehouse_id"] = warehouse.id
        if pricelist:
            so_vals["pricelist_id"] = pricelist.id
        if "commitment_date" in so_model._fields:
            so_vals["commitment_date"] = now_dt + timedelta(days=14 + idx)
        if "franco" in so_model._fields:
            so_vals["franco"] = "Franco Project Site"
        if "incoterm" in so_model._fields and incoterm:
            so_vals["incoterm"] = incoterm.id
        if "incoterm_location" in so_model._fields:
            so_vals["incoterm_location"] = "Warehouse Palembang"

        order = so_model.create(so_vals)

        for line_idx, product in enumerate(products, start=1):
            sol_vals = {
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": 3.0 * line_idx,
                "price_unit": product.list_price,
            }
            if "customer_description" in sol_model._fields:
                sol_vals["customer_description"] = f"{product.name} - Backdate seed"
            if "customer_uom" in sol_model._fields:
                sol_vals["customer_uom"] = "Units"
            sol_model.create(sol_vals)

        order.action_confirm()
        _validate_pickings(order.picking_ids)

        invoices = order._create_invoices()
        draft_invoices = invoices.filtered(lambda inv: inv.state == "draft")
        if draft_invoices:
            draft_invoices.action_post()

        created_orders |= order

    result = {
        "orders": created_orders.mapped("name"),
        "date_order": created_orders.mapped("date_order"),
        "document_date": created_orders.mapped("document_date"),
        "pickings": created_orders.mapped("picking_ids.name"),
        "invoices": env["account.move"].search(
            [("invoice_origin", "in", created_orders.mapped("name"))]
        ).mapped("name"),
    }
    if commit:
        env.cr.commit()
    print("Seed backdate completed:", result)
    return result

