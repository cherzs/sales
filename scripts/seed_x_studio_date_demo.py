"""Seed demo data to validate x_studio_date in Gross Profit & Rekap SO reports.

Usage from Odoo shell:
    source /Users/mac/Documents/Dev/work/venv/bin/activate
    cd /Users/mac/Documents/Dev/work
    python3 odoo/odoo-bin shell -c odoo18sale.conf -d Salereport --no-http
    >>> exec(open('/Users/mac/Documents/Dev/work/sales/scripts/seed_x_studio_date_demo.py').read())
    >>> seed_x_studio_date_demo(env)
"""

def seed_x_studio_date_demo(env):
    print("=== UPGRADE MODULE ===")
    module = env['ir.module.module'].search([('name', '=', 'sale_recap_report')])
    if module.state == 'installed':
        module.button_immediate_upgrade()
        env.cr.commit()
        print("  Module sale_recap_report upgraded.")
    else:
        print("  Module not installed, state:", module.state)

    print()
    print("=== CREATE DEMO DATA ===")

    # 1. Category
    categ = env['product.category'].search([('name', '=', 'TEST GP REKAP DATE CATEGORY')], limit=1)
    if not categ:
        categ = env['product.category'].create({
            'name': 'TEST GP REKAP DATE CATEGORY',
        })
    print("  Category:", categ.name, "(id=%d)" % categ.id)

    # 2. Customer
    partner = env['res.partner'].search([('name', '=', 'TEST CUSTOMER X_STUDIO_DATE')], limit=1)
    if not partner:
        partner = env['res.partner'].create({
            'name': 'TEST CUSTOMER X_STUDIO_DATE',
        })
    print("  Customer:", partner.name, "(id=%d)" % partner.id)

    # 3. Products
    # Product A - for GP
    prod_a = env['product.product'].search([('default_code', '=', 'TEST-GP-MAY')], limit=1)
    if not prod_a:
        prod_a = env['product.product'].create({
            'name': 'TEST GP DATE PRODUCT MAY',
            'default_code': 'TEST-GP-MAY',
            'type': 'consu',
            'categ_id': categ.id,
            'list_price': 100000,
            'standard_price': 60000,
        })
    print("  Product A:", prod_a.default_code, prod_a.name, "(id=%d)" % prod_a.id)

    # Product B - for Rekap SO
    prod_b = env['product.product'].search([('default_code', '=', 'TEST-REKAP-MAY')], limit=1)
    if not prod_b:
        prod_b = env['product.product'].create({
            'name': 'TEST REKAP DATE PRODUCT MAY',
            'default_code': 'TEST-REKAP-MAY',
            'type': 'consu',
            'categ_id': categ.id,
            'list_price': 200000,
            'standard_price': 120000,
        })
    print("  Product B:", prod_b.default_code, prod_b.name, "(id=%d)" % prod_b.id)

    # 4. SO A - Gross Profit (May via x_studio_date)
    so_gp = env['sale.order'].search([('client_order_ref', '=', 'TEST_X_STUDIO_DATE_GP_MAY')], limit=1)
    if not so_gp:
        so_gp = env['sale.order'].create({
            'partner_id': partner.id,
            'client_order_ref': 'TEST_X_STUDIO_DATE_GP_MAY',
            'date_order': '2026-06-10 10:00:00',
            'x_studio_date': '2026-05-15',
        })
        env['sale.order.line'].create({
            'order_id': so_gp.id,
            'product_id': prod_a.id,
            'product_uom_qty': 2,
            'price_unit': 100000,
        })
        so_gp.action_confirm()
    print("  SO GP:", so_gp.name, "state=%s date_order=%s x_studio_date=%s" % (
        so_gp.state, so_gp.date_order, so_gp.x_studio_date))

    # 5. SO B - Rekap SO (May via x_studio_date) - needs delivery
    so_rekap = env['sale.order'].search([('client_order_ref', '=', 'TEST_X_STUDIO_DATE_REKAP_MAY')], limit=1)
    if not so_rekap:
        so_rekap = env['sale.order'].create({
            'partner_id': partner.id,
            'client_order_ref': 'TEST_X_STUDIO_DATE_REKAP_MAY',
            'date_order': '2026-06-12 10:00:00',
            'x_studio_date': '2026-05-20',
        })
        env['sale.order.line'].create({
            'order_id': so_rekap.id,
            'product_id': prod_b.id,
            'product_uom_qty': 3,
            'price_unit': 200000,
        })
        so_rekap.action_confirm()

        # Create delivery for Rekap SO (required by INNER JOIN delivery_data)
        picking = so_rekap.picking_ids
        if picking:
            picking = picking[0]
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
            picking.button_validate()
            # Set picking to done
            picking.state = 'done'
            picking.date_done = '2026-05-20 12:00:00'
    print("  SO Rekap:", so_rekap.name, "state=%s date_order=%s x_studio_date=%s" % (
        so_rekap.state, so_rekap.date_order, so_rekap.x_studio_date))

    # 6. SO C - June control
    so_june = env['sale.order'].search([('client_order_ref', '=', 'TEST_X_STUDIO_DATE_JUNE_CONTROL')], limit=1)
    if not so_june:
        so_june = env['sale.order'].create({
            'partner_id': partner.id,
            'client_order_ref': 'TEST_X_STUDIO_DATE_JUNE_CONTROL',
            'date_order': '2026-06-15 10:00:00',
            'x_studio_date': '2026-06-15',
        })
        env['sale.order.line'].create({
            'order_id': so_june.id,
            'product_id': prod_b.id,
            'product_uom_qty': 1,
            'price_unit': 200000,
        })
        so_june.action_confirm()
        # Delivery for Rekap SO
        picking = so_june.picking_ids
        if picking:
            picking = picking[0]
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
            picking.button_validate()
            picking.state = 'done'
            picking.date_done = '2026-06-15 12:00:00'
    print("  SO June:", so_june.name, "state=%s date_order=%s x_studio_date=%s" % (
        so_june.state, so_june.date_order, so_june.x_studio_date))

    # 7. SO D - Draft (should be excluded)
    so_draft = env['sale.order'].search([('client_order_ref', '=', 'TEST_X_STUDIO_DATE_EXCLUDED_STATE')], limit=1)
    if not so_draft:
        so_draft = env['sale.order'].create({
            'partner_id': partner.id,
            'client_order_ref': 'TEST_X_STUDIO_DATE_EXCLUDED_STATE',
            'date_order': '2026-06-10 10:00:00',
            'x_studio_date': '2026-05-01',
        })
        env['sale.order.line'].create({
            'order_id': so_draft.id,
            'product_id': prod_a.id,
            'product_uom_qty': 5,
            'price_unit': 100000,
        })
        # Leave as draft
    print("  SO Draft:", so_draft.name, "state=%s date_order=%s x_studio_date=%s" % (
        so_draft.state, so_draft.date_order, so_draft.x_studio_date))

    env.cr.commit()
    print()
    print("=== DEMO DATA CREATED ===")

    # Print summary
    print()
    print("=== SUMMARY ===")
    for so in env['sale.order'].search([('client_order_ref', 'ilike', 'TEST_X_STUDIO_DATE%')], order='name'):
        print("  %-12s | state=%-6s | date_order=%s | x_studio_date=%s" % (
            so.name, so.state, so.date_order, so.x_studio_date))
