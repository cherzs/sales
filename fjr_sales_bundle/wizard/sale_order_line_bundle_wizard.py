from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrderLineBundleWizard(models.TransientModel):
    _name = 'sale.order.line.bundle.wizard'
    _description = 'Wizard to add bundle lines to sale order line'

    order_id = fields.Many2one(
        'sale.order', string='Order', required=True,
        help='The sale order to which bundle lines will be added.'
    )

    product_id = fields.Many2one(
        'product.product', string='Bundle Product', required=True,
        help='The bundle product to add lines from.',
        domain="[('is_sale_bundle', '=', True)]"
    )

    line_ids = fields.One2many(
        'sale.order.line.bundle.wizard.line', 'wizard_id', string='Bundle Lines',
        help='Lines defining the products to be added to the sale order line bundle.',
        compute='_compute_line_ids',
        store=True,
        readonly=False,
    )

    @api.depends('product_id')
    def _compute_line_ids(self):
        for wizard in self:
            lines = []
            wizard.line_ids = []
            if wizard.product_id:
                bundle_lines = wizard.product_id.sale_product_bundle_line_ids
                for line in bundle_lines:
                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'uom_id': line.uom_id.id,
                    }))
            wizard.line_ids = lines


    def action_add_bundle_lines(self):
        self.ensure_one()
        sale_order = self.order_id
        line_with_quantity = self.line_ids.filtered(lambda l: l.quantity > 0)
        if not line_with_quantity:
            raise UserError(_("Please specify at least one product with quantity greater than zero."))
        
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product_id.id,
            'product_uom_qty': 1,
            'bundle_line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'uom_id': line.uom_id.id,
            }) for line in line_with_quantity],
        })
        

class SaleOrderLineBundleWizardLine(models.TransientModel):
    _name = 'sale.order.line.bundle.wizard.line'
    _description = 'Wizard Line for Sale Order Line Bundle'

    wizard_id = fields.Many2one(
        'sale.order.line.bundle.wizard', string='Wizard', required=True,
        help='The wizard this line belongs to.',
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        help='The product included in the bundle.'
    )
    quantity = fields.Float(
        string='Quantity', default=1.0,
        help='Quantity of the product in the bundle.'
    )
    uom_id = fields.Many2one(
        'uom.uom', string='Unit of Measure', 
        help='Unit of measure for the product.',
        domain="[('category_id', '=', product_uom_category_id)]"
    )
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])