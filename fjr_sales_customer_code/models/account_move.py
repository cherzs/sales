from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    customer_description = fields.Text(string='Customer Description')
    customer_uom = fields.Char(string='Customer UoM')



    def _get_label_without_product_code(self):
        current_name = self.name
        product_display_name = self.product_id.display_name
        if product_display_name in current_name:
            return current_name.replace(product_display_name, self.product_id._get_display_name_without_code())
        return current_name