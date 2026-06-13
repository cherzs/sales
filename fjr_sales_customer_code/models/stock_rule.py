from odoo import models, fields, api, _

class StockRule(models.Model):
    _inherit = 'stock.rule'


    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['customer_description', 'customer_uom']
        return fields