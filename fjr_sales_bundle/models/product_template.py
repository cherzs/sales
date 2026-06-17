from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_sale_bundle = fields.Boolean(string='Is Sale Bundle', default=False,
                                    help='Indicates if the product is a sale bundle.')
    

    sale_product_bundle_line_ids = fields.One2many(
        'sale.product.bundle.line', 'parent_product_id', string='Sale Bundle Lines',
        help='Lines defining the products included in this sale bundle.'
    )

class SaleProductBundleLine(models.Model):
    _name = 'sale.product.bundle.line'
    _description = 'Sale Product Bundle Line'

    parent_product_id = fields.Many2one(
        'product.template', string='Parent Product', required=True,
        help='The product template that represents the sale bundle.',
        ondelete='cascade'
    )
    quantity = fields.Float(string='Quantity', default=1.0,
                            help='Quantity of the component product in the bundle.')

    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        help='The component product included in the sale bundle.',
        ondelete='cascade'
    )
    
    uom_id = fields.Many2one(
        'uom.uom', string='Unit of Measure', 
        help='Unit of measure for the component product.',
        compute='_compute_uom_id',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="[('category_id', '=', product_uom_category_id)]"

    )

    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])

    @api.depends('product_id', 'quantity', 'uom_id')
    def _compute_display_name(self):
        for rec in self:
            code = rec.product_id.default_code or ''
            name = rec.product_id.name or ''
            qty = rec.quantity
            uom = rec.uom_id.name or ''
            if code:
                rec.display_name = '[%s] %s x%s %s' % (code, name, qty, uom)
            elif name:
                rec.display_name = '%s x%s %s' % (name, qty, uom)
            else:
                rec.display_name = '%s, %s' % (self._description, rec.id)

    @api.depends('product_id')
    def _compute_uom_id(self):
        for line in self:
            if not line.uom_id or (line.product_id.uom_id.id != line.uom_id.id):
                line.uom_id = line.product_id.uom_id