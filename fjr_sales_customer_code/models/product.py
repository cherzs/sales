from odoo import models, fields, api,_

class ProductProduct(models.Model):
    _inherit = 'product.product'

    
    def _get_display_name_without_code(self):
        return self.with_context(display_default_code=False).display_name
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'


    def _get_display_name_without_code(self):
        return self.name
    