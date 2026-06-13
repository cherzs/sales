from odoo import models, fields, api, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    customer_description = fields.Text(string='Customer Description')
    customer_uom = fields.Char(string='Customer UoM')

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'


    def _get_aggregated_product_quantities(self, **kwargs):
        res = super(StockMoveLine, self)._get_aggregated_product_quantities(**kwargs)
        for key, value in res.items():
            move = value.get('move')
            value['customer_uom'] = move.customer_uom
            value['customer_description'] = move.customer_description
        return res
    


    def _get_kit_done_qty(self):
        filters = {'incoming_moves': lambda m: True, 'outgoing_moves': lambda m: False}
        
        bom = self.move_id.bom_line_id.bom_id
        kit_qty_done = self.move_id._compute_kit_quantities(bom.product_id or bom.product_tmpl_id.product_variant_id, 1, bom, filters)
        return kit_qty_done