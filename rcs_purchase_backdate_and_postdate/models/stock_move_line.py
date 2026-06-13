# -*- coding: utf-8 -*-
from odoo import fields, models


class RcsStockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    rcs_notes_for_purchase = fields.Text(
        string="Notes for Purchase",
        related="move_id.rcs_notes_for_purchase"
    )

    is_rcs_notes_for_purchase = fields.Boolean(
        related="company_id.rcs_notes_for_purchase_order",
        string="Is Notes for Purchase"
    )

    def write(self, vals):
        for rec in self:
            if rec.company_id.stock_move_backdate:
                if rec.picking_id:
                    vals['date'] = rec.picking_id.scheduled_date
        return super().write(vals)