from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_studio_no_do = fields.Char(string='No DO')
