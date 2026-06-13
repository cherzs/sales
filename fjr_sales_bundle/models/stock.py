from odoo import models, fields, api, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_bundle_line_id = fields.Many2one(
        'sale.order.line.bundle', string='Bundle Line',
        help='The bundle line associated with this stock move, if any.'
    )


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['sale_bundle_line_id']
        return fields
