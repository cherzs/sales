from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manual_delivery_address = fields.Html('Manual Delivery Address', sanitize=True, compute='_compute_manual_delivery_address', store=True, readonly=False)


    @api.depends('partner_shipping_id')
    def _compute_manual_delivery_address(self):
        for order in self:
            address = order.partner_shipping_id
            if address:
                lines = [
                    address.display_name or '',
                    address.street or '',
                    address.street2 or '',
                    f"{(address.city or '').strip()} {(address.state_id.name or '').strip()} {(address.zip or '').strip()}".strip(),
                    address.country_id.name or ''
                ]
                filtered = [l for l in (ln.strip() for ln in lines) if l]
                wrapped = [f'<div class="">{l}</div>' for l in filtered]
                order.manual_delivery_address = ''.join(wrapped)
            else:
                order.manual_delivery_address = ''

    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['manual_delivery_address'] = self.manual_delivery_address
        return invoice_vals
    

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        vals.update({
            'manual_delivery_address': self.order_id.manual_delivery_address,
        })
        return vals