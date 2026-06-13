from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

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
                wrapped = [f'<span class="w-100 o_force_ltr d-block">{l}</span>' for l in filtered]
                order.manual_delivery_address = ''.join(wrapped)
            else:
                order.manual_delivery_address = ''