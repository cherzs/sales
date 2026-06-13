"""Seed bundle demo data to validate bundle_display, GP, and Rekap SO.

Usage from Odoo shell:
    source /Users/mac/Documents/Dev/work/venv/bin/activate
    cd /Users/mac/Documents/Dev/work
    python3 odoo/odoo-bin shell -c odoo18sale.conf -d Salereport --no-http
    >>> exec(open('/Users/mac/Documents/Dev/work/sales/scripts/seed_bundle_demo.py').read())
    >>> seed_bundle_demo(env)
"""

def seed_bundle_demo(env):
    print("=== CREATE BUNDLE DEMO DATA ===")
    print()

    categ = env['product.category'].search([('name', '=', 'TEST GP REKAP DATE CATEGORY')], limit=1)
    partner = env['res.partner'].search([('name', '=', 'TEST CUSTOMER X_STUDIO_DATE')], limit=1)
    uom_unit = env.ref('uom.product_uom_unit')

    # ── 1. Component Product A ──
    comp_a = env['product.product'].search([('default_code', '=', 'TEST-BOOT-A')], limit=1)
    if not comp_a:
        comp_a = env['product.product'].create({
            'name': 'TEST BOOTS COMPONENT A',
            'default_code': 'TEST-BOOT-A',
            'type': 'consu',
            'categ_id': categ.id,
            'list_price': 100000,
            'standard_price': 60000,
        })
    print("  Component A:", comp_a.default_code, comp_a.name, "id=%d" % comp_a.id)

    # ── 2. Component Product B ──
    comp_b = env['product.product'].search([('default_code', '=', 'TEST-BOOT-B')], limit=1)
    if not comp_b:
        comp_b = env['product.product'].create({
            'name': 'TEST BOOTS COMPONENT B',
            'default_code': 'TEST-BOOT-B',
            'type': 'consu',
            'categ_id': categ.id,
            'list_price': 150000,
            'standard_price': 90000,
        })
    print("  Component B:", comp_b.default_code, comp_b.name, "id=%d" % comp_b.id)

    # ── 3. Parent Bundle Product ──
    bundle_parent = env['product.product'].search([('default_code', '=', 'TEST-BUNDLE-BOOTS')], limit=1)
    if not bundle_parent:
        bundle_parent = env['product.product'].create({
            'name': 'TEST BUNDLE BOOTS PARENT',
            'default_code': 'TEST-BUNDLE-BOOTS',
            'type': 'consu',
            'categ_id': categ.id,
            'list_price': 500000,
            'standard_price': 300000,
        })
    print("  Bundle Parent:", bundle_parent.default_code, bundle_parent.name, "id=%d" % bundle_parent.id)

    # ── 4. Set is_sale_bundle on the product template ──
    tmpl = bundle_parent.product_tmpl_id
    if not tmpl.is_sale_bundle:
        tmpl.is_sale_bundle = True
    print("  is_sale_bundle:", tmpl.is_sale_bundle, "on template id=%d" % tmpl.id)

    # ── 5. Bundle Definition Lines on product template ──
    existing_bl = env['sale.product.bundle.line'].search([
        ('parent_product_id', '=', tmpl.id)
    ])
    if not existing_bl:
        env['sale.product.bundle.line'].create({
            'parent_product_id': tmpl.id,
            'product_id': comp_a.id,
            'quantity': 1,
        })
        env['sale.product.bundle.line'].create({
            'parent_product_id': tmpl.id,
            'product_id': comp_b.id,
            'quantity': 2,
        })
    existing_bl = env['sale.product.bundle.line'].search([('parent_product_id', '=', tmpl.id)])
    for bl in existing_bl:
        print("  Bundle def:", bl.product_id.default_code, "qty=%s" % bl.quantity)

    # ── 6. Create Sales Order ──
    so = env['sale.order'].search([('client_order_ref', '=', 'TEST_X_STUDIO_DATE_BUNDLE_MAY')], limit=1)
    if not so:
        so = env['sale.order'].create({
            'partner_id': partner.id,
            'client_order_ref': 'TEST_X_STUDIO_DATE_BUNDLE_MAY',
            'date_order': '2026-06-13 10:00:00',
            'x_studio_date': '2026-05-25',
        })
        # Create bundle sale.order.line (matching wizard's action_add_bundle_lines)
        bundle_line_vals = []
        for bl in existing_bl:
            bundle_line_vals.append((0, 0, {
                'product_id': bl.product_id.id,
                'quantity': bl.quantity,
                'uom_id': bl.product_id.uom_id.id,
            }))
        sol = env['sale.order.line'].create({
            'order_id': so.id,
            'product_id': bundle_parent.id,
            'product_uom_qty': 1,
            'bundle_line_ids': bundle_line_vals,
        })
        # Confirm SO → triggers procurement for bundle components
        so.with_context(skip_procurement=False).action_confirm()
        print("  Bundle SOL created: id=%d, product=%s, bundle_line_ids count=%d" % (
            sol.id, sol.product_id.default_code, len(sol.bundle_line_ids)))
    else:
        sol = so.order_line.filtered(lambda l: l.product_id == bundle_parent)
        sol = sol[0] if sol else so.order_line[0]

    print("  SO:", so.name, "state=%s date_order=%s x_studio_date=%s" % (
        so.state, so.date_order, so.x_studio_date))

    # ── 7. Validate pickings and delivery ──
    pickings = so.picking_ids.filtered(lambda p: p.state != 'cancel')
    print("  Pickings:", len(pickings))
    for p in pickings:
        print("    %s state=%s type=%s" % (p.name, p.state, p.picking_type_id.code))
        # Validate and set done
        if p.state != 'done':
            for move in p.move_ids:
                move.quantity = move.product_uom_qty
            p.button_validate()

    env.cr.commit()

    # ── 8. Print summary ──
    print()
    print("=== SUMMARY ===")
    print("  SO:", so.name, so.state, "x_studio_date:", so.x_studio_date)
    for line in so.order_line:
        print("  SOL id=%d product=%s qty=%s price=%s subtotal=%s" % (
            line.id, line.product_id.default_code,
            line.product_uom_qty, line.price_unit, line.price_subtotal))
        print("    is_bundle_line:", line.is_bundle_line)
        bundle_lines = line.bundle_line_ids
        if bundle_lines:
            print("    bundle_line_ids (%d):" % len(bundle_lines))
            for bl in bundle_lines:
                print("      id=%d product=%s qty=%s qty_delivered=%s" % (
                    bl.id, bl.product_id.default_code, bl.quantity, bl.qty_delivered))
                moves = bl.move_ids
                if moves:
                    for m in moves:
                        print("        move id=%d state=%s qty=%s picking=%s" % (
                            m.id, m.state, m.product_uom_qty, m.picking_id.name))
        # Check bundle_display
        print("    bundle_display:", repr(line.bundle_display))

    print()
    print("=== DONE ===")
