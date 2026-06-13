from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    customer_description = fields.Text(string='Customer Description')
    customer_uom = fields.Char(string='Customer UoM')


    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        vals = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        vals.update({
            'customer_description': self.customer_description,
            'customer_uom': self.customer_uom,
        })
        return vals


    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        vals.update({
            'customer_description': self.customer_description,
            'customer_uom': self.customer_uom,
        })
        return vals