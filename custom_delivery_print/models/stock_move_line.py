from odoo import models, fields, api, _

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'


    def _get_aggregated_properties(self, move_line=False, move=False):
        aggregated_properties = super()._get_aggregated_properties(move_line, move)
        sale_bundle_line_id = aggregated_properties['move'].sale_bundle_line_id
        sale_order_line_id = sale_bundle_line_id.order_line_id.id
        aggregated_properties['sale_from_bundle_id'] = sale_order_line_id or False
        aggregated_properties['line_key'] = f"sale_from_bundle_{sale_order_line_id}" if sale_order_line_id else aggregated_properties['line_key']
        return aggregated_properties



    def _get_aggregated_product_quantities(self, **kwargs):
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        for aggregated_move_line in aggregated_move_lines:
            sale_from_bundle_id  = aggregated_move_lines[aggregated_move_line]['sale_from_bundle_id']
            if sale_from_bundle_id:
                sale_order_line_id = self.env['sale.order.line'].sudo().browse(sale_from_bundle_id)
                bundle_factor = sale_order_line_id.product_uom_qty / (sum(sale_order_line_id.bundle_line_ids.mapped('quantity')) or 1)
                
                
                aggregated_move_lines[aggregated_move_line]['quantity'] = aggregated_move_lines[aggregated_move_line]['quantity'] * bundle_factor
                aggregated_move_lines[aggregated_move_line]['qty_ordered'] = aggregated_move_lines[aggregated_move_line]['qty_ordered'] * bundle_factor
                aggregated_move_lines[aggregated_move_line]['product'] = sale_order_line_id.product_id

        return aggregated_move_lines