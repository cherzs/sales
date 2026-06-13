"""Seed demo data matching client case: Sepatu Boots Bundle.

Usage from Odoo shell:
    source /Users/mac/Documents/Dev/work/venv/bin/activate
    cd /Users/mac/Documents/Dev/work
    python3 odoo/odoo-bin shell -c odoo18sale.conf -d Salereport --no-http
    >>> exec(open('/Users/mac/Documents/Dev/work/sales/scripts/seed_boots_bundle_demo.py').read())
    >>> seed_boots_bundle_demo(env)
"""

def seed_boots_bundle_demo(env):
    print("=== CREATE BOOTS BUNDLE DEMO DATA ===")
    print()

    uom_unit = env.ref('uom.product_uom_unit')

    # ── A. Category ──
    categ = env['product.category'].search([('name', '=', 'All / STOCK / BOOTS TEST')], limit=1)
    if not categ:
        # Try find 'All' parent
        all_categ = env['product.category'].search([('name', '=', 'All')], limit=1)
        parent_id = all_categ.id if all_categ else False
        categ = env['product.category'].create({
            'name': 'All / STOCK / BOOTS TEST',
            'parent_id': parent_id,
        })
    print("  Category:", categ.display_name, "id=%d" % categ.id)

    # ── B. Component Products ──
    def _make_product(code, name, price, cost):
        p = env['product.product'].search([('default_code', '=', code)], limit=1)
        if not p:
            p = env['product.product'].create({
                'name': name,
                'default_code': code,
                'type': 'consu',
                'categ_id': categ.id,
                'list_price': price,
                'standard_price': cost,
            })
        print("  Product:", p.default_code, p.name, "id=%d" % p.id)
        return p

    boot8 = _make_product('BOOT-8', 'TEST BOOTS PVC 8', 76700, 50000)
    boot10 = _make_product('BOOT-10', 'TEST BOOTS PVC 10', 105000, 70000)
    sprayer = _make_product('ZY-001', 'TEST HAND SPRAYER', 858000, 500000)

    # ── C. Bundle Parent Product ──
    bundle_parent = env['product.product'].search([('default_code', '=', 'ACC-BOOT-BUNDLE')], limit=1)
    if not bundle_parent:
        bundle_parent = env['product.product'].create({
            'name': 'TEST SEPATU BOOTS BUNDLE',
            'default_code': 'ACC-BOOT-BUNDLE',
            'type': 'consu',
            'categ_id': categ.id,
            'list_price': 500000,
            'standard_price': 300000,
        })
    print("  Bundle Parent:", bundle_parent.default_code, bundle_parent.name, "id=%d" % bundle_parent.id)

    # Set is_sale_bundle on template
    tmpl = bundle_parent.product_tmpl_id
    if not tmpl.is_sale_bundle:
        tmpl.is_sale_bundle = True
    print("  is_sale_bundle:", tmpl.is_sale_bundle)

    # ── D. Bundle Definition Lines ──
    existing_bl = env['sale.product.bundle.line'].search([('parent_product_id', '=', tmpl.id)])
    if not existing_bl:
        for prod in [boot8, boot10, sprayer]:
            env['sale.product.bundle.line'].create({
                'parent_product_id': tmpl.id,
                'product_id': prod.id,
                'quantity': 1,
            })
    existing_bl = env['sale.product.bundle.line'].search([('parent_product_id', '=', tmpl.id)])
    for bl in existing_bl:
        print("  Bundle def:", bl.product_id.default_code, "qty=%s" % bl.quantity)

    # ── E. Customer ──
    partner = env['res.partner'].search([('name', '=', 'TEST CUSTOMER BOOTS BUNDLE')], limit=1)
    if not partner:
        partner = env['res.partner'].create({
            'name': 'TEST CUSTOMER BOOTS BUNDLE',
            'ref': '4900171',
        })
    print("  Customer:", partner.name, "ref=%s id=%d" % (partner.ref, partner.id))

    # ── F. Sales Order with Bundle ──
    so = env['sale.order'].search([('client_order_ref', '=', 'TEST_SO_BOOTS_BUNDLE_DISPLAY')], limit=1)
    if not so:
        so = env['sale.order'].create({
            'partner_id': partner.id,
            'client_order_ref': 'TEST_SO_BOOTS_BUNDLE_DISPLAY',
            'date_order': '2026-06-12 10:00:00',
            'x_studio_date': '2026-05-25',
        })
        # Create bundle sale.order.line (matching wizard action_add_bundle_lines)
        bundle_line_vals = [(0, 0, {
            'product_id': bl.product_id.id,
            'quantity': bl.quantity,
            'uom_id': bl.product_id.uom_id.id,
        }) for bl in existing_bl]
        sol = env['sale.order.line'].create({
            'order_id': so.id,
            'product_id': bundle_parent.id,
            'product_uom_qty': 1,
            'bundle_line_ids': bundle_line_vals,
        })
        so.action_confirm()
        print("  SOL:", sol.id, "product:", sol.product_id.default_code)
        print("  bundle_line_ids count:", len(sol.bundle_line_ids))
    else:
        sol = so.order_line.filtered(lambda l: l.is_bundle_line)
        sol = sol[0] if sol else so.order_line[0]
    print("  SO:", so.name, "state=%s x_studio_date=%s" % (so.state, so.x_studio_date))

    # ── G. Delivery ──
    for picking in so.picking_ids.filtered(lambda p: p.state != 'cancel' and p.state != 'done'):
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()
        print("  Picking:", picking.name, "state=%s" % picking.state)

    # ── H. Item Kit Reference Product ──
    kit_parent = env['product.product'].search([('default_code', '=', 'KIT-BOOTS-REF')], limit=1)
    if not kit_parent:
        kit_parent = env['product.product'].create({
            'name': 'TEST ITEM KIT BOOTS REF',
            'default_code': 'KIT-BOOTS-REF',
            'type': 'consu',
            'categ_id': categ.id,
            'list_price': 200000,
            'standard_price': 120000,
        })
    print("  Kit Parent:", kit_parent.default_code, "id=%d" % kit_parent.id)

    # Create BoM for kit
    mrp_bom = env['mrp.bom']
    bom = mrp_bom.search([('product_tmpl_id', '=', kit_parent.product_tmpl_id.id)], limit=1)
    if not bom:
        bom = mrp_bom.create({
            'product_tmpl_id': kit_parent.product_tmpl_id.id,
            'product_id': kit_parent.id,
            'product_qty': 1,
            'product_uom_id': uom_unit.id,
            'type': 'phantom',
        })
        for prod, qty in [(boot8, 1), (boot10, 1)]:
            env['mrp.bom.line'].create({
                'bom_id': bom.id,
                'product_id': prod.id,
                'product_qty': qty,
                'product_uom_id': prod.uom_id.id,
            })
        print("  BoM created:", bom.id, "type=%s lines=%d" % (bom.type, len(bom.bom_line_ids)))

    # Create SO with kit product in same SO
    kit_line = so.order_line.filtered(lambda l: l.product_id == kit_parent)
    if not kit_line:
        kit_line = env['sale.order.line'].create({
            'order_id': so.id,
            'product_id': kit_parent.id,
            'product_uom_qty': 2,
        })
        print("  Kit SOL:", kit_line.id, "product:", kit_line.product_id.default_code)

    env.cr.commit()

    # ── I. Print Summary ──
    print()
    print("=" * 60)
    print("VALIDATION")
    print("=" * 60)
    print()
    print("SO:", so.name, "state:", so.state)
    print("  x_studio_date:", so.x_studio_date)
    print("  date_order:", so.date_order)
    print()

    for line in so.order_line:
        print("--- SOL id=%d ---" % line.id)
        print("  product:", line.product_id.default_code, line.product_id.display_name)
        print("  is_bundle_line:", getattr(line, 'is_bundle_line', False))
        print("  qty:", line.product_uom_qty)
        print("  price_unit:", line.price_unit)
        print("  subtotal:", line.price_subtotal)
        print("  x_studio_date:", line.x_studio_date)
        print("  x_studio_delivery_status:", line.x_studio_delivery_status)
        print("  x_studio_relation_product_sale_bundle_line:", repr(line.x_studio_relation_product_sale_bundle_line))
        print("  x_studio_related_field_46u_1jh8asq3t (Item Kit):", repr(line.x_studio_related_field_46u_1jh8asq3t))
        print("  bundle_display:", repr(line.bundle_display))

        if hasattr(line, 'bundle_line_ids') and line.bundle_line_ids:
            print("  bundle_line_ids:")
            for bl in line.bundle_line_ids:
                print("    %s | qty=%s | delivered=%s" % (bl.product_id.default_code, bl.quantity, bl.qty_delivered))

    print()
    print("=== DONE ===")
