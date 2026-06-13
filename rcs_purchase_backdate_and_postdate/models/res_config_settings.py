# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class RcsResCompany(models.Model):
    _inherit = 'res.company'

    purchase_order_backdate = fields.Boolean(
        "Enable Custom Date for Purchase Orders")

    rcs_notes_for_purchase_order = fields.Boolean(
        "Enable Purchase Order Notes")

    rcs_notes_mandatory_for_purchase_order = fields.Boolean(
        "Require Notes for Purchase Orders")

    bill_backdate = fields.Boolean("Sync Bill Date with Purchase Order Date")

    stock_move_backdate = fields.Boolean("Sync Receipt Date with Purchase Order Date ")


class RcsResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_order_backdate = fields.Boolean(
        "Enable Custom Date for Purchase Orders",
        related="company_id.purchase_order_backdate",
        readonly=False
    )

    rcs_notes_for_purchase_order = fields.Boolean(
        "Enable Purchase Order Notes",
        related="company_id.rcs_notes_for_purchase_order",
        readonly=False
    )

    rcs_notes_mandatory_for_purchase_order = fields.Boolean(
        "Require Notes for Purchase Orders",
        related="company_id.rcs_notes_mandatory_for_purchase_order",
        readonly=False
    )

    bill_backdate = fields.Boolean(
        "Sync Bill Date with Purchase Order Date",
        related="company_id.bill_backdate",
        readonly=False
    )

    stock_move_backdate = fields.Boolean(
        "Sync Receipt Date with Purchase Order Date",
        related="company_id.stock_move_backdate",
        readonly=False
    )

    @api.onchange('purchase_order_backdate', 'rcs_notes_for_purchase_order', 'rcs_notes_mandatory_for_purchase_order', 'bill_backdate', 'stock_move_backdate')
    def manage_purchase_date_setting(self):
        if not self.purchase_order_backdate:
            self.rcs_notes_for_purchase_order = False
            self.rcs_notes_mandatory_for_purchase_order = False
            self.bill_backdate = False
            self.stock_move_backdate = False
        else:
            if not self.rcs_notes_for_purchase_order:
                self.rcs_notes_mandatory_for_purchase_order = False
