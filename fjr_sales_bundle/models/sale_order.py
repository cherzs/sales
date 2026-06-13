from odoo import models, fields, api, _
from odoo.tools import float_compare

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_add_bundle_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Bundle Lines'),
            'res_model': 'sale.order.line.bundle.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            },
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    bundle_line_ids = fields.One2many(
        'sale.order.line.bundle', 'order_line_id', string='Bundle Lines',
        help='Lines defining the products included in this sale order line bundle.',
        copy=True
    )

    is_bundle_line = fields.Boolean(
        string='Is Bundle Line',
        compute='_compute_is_bundle_line',
        store=True,
    )

    @api.depends('product_id')
    def _compute_is_bundle_line(self):
        for line in self:
            line.is_bundle_line = line.product_id.is_sale_bundle


    @api.depends('is_bundle_line', 'bundle_line_ids.quantity', 'bundle_line_ids.qty_delivered')
    def _compute_qty_delivered(self):
        line_not_bundle = self.filtered(lambda line: not line.is_bundle_line)
        super(SaleOrderLine, line_not_bundle)._compute_qty_delivered()
        line_bundle = self.filtered(lambda line: line.is_bundle_line)
        for line in line_bundle:
            total_quantity = sum(bundle_line.quantity for bundle_line in line.bundle_line_ids)
            total_quantity_delivered = sum(bundle_line.qty_delivered for bundle_line in line.bundle_line_ids)
            qty = 0.0
            if total_quantity:
                qty = (total_quantity_delivered / total_quantity) * line.product_uom_qty
            line.qty_delivered = qty

    def action_add_bundle_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Bundle Lines'),
            'res_model': 'sale.order.line.bundle.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.env.context.get('order_id'),
            },
        }
    
    def action_open_sale_order_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order Line'),
            'res_model': 'sale.order.line',
            'view_mode': 'form',
            'views': [(self.env.ref('fjr_sales_bundle.sale_order_line_with_bundle_view_form').id, 'form')],
            'target': 'new',
            'res_id': self.id,
            
        }
        
    
    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        self_not_bundle = self.filtered(lambda line: not line.is_bundle_line)
        res = super(SaleOrderLine, self_not_bundle)._action_launch_stock_rule(previous_product_uom_qty)
        if self._context.get("skip_procurement"):
            return True and res
        bundle_lines = self.filtered(lambda line: line.is_bundle_line)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in bundle_lines:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or line.order_id.locked or not line.bundle_line_ids:
                continue
            
            group_id = line._get_procurement_group()
            origin = f'{line.order_id.name} - {line.order_id.client_order_ref}' if line.order_id.client_order_ref else line.order_id.name
            
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)
            
            for bundle_line in line.bundle_line_ids:

                qty = bundle_line._get_qty_procurement(previous_product_uom_qty)

                if float_compare(qty, bundle_line.quantity, precision_digits=precision) == 0:
                    continue


                values = bundle_line._prepare_procurement_values(group_id=group_id)
                product_qty = bundle_line.quantity - qty
                line_uom = bundle_line.uom_id
                quant_uom = bundle_line.product_id.uom_id
                product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
                procurements += bundle_line._create_procurements(product_qty, procurement_uom, origin, values)
                
        if procurements:
            self.env['procurement.group'].run(procurements)
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                pickings_to_confirm.action_confirm()
        return True



class SaleOrderLineBundle(models.Model):
    _name = 'sale.order.line.bundle'
    _description = 'Sale Order Line Bundle'

    order_line_id = fields.Many2one(
        'sale.order.line', string='Order Line', required=True,
        help='The sale order line that includes this bundle line.',
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

    move_ids = fields.One2many(
        'stock.move', 'sale_bundle_line_id', string='Stock Moves',
        help='Stock moves associated with this bundle line.'
    )

    qty_delivered = fields.Float(
        string='Delivered Quantity', compute='_compute_qty_delivered',
        help='Quantity of the component product that has been delivered.',
        store=True
    )

    



    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])


    @api.model_create_multi
    def create(self, vals_list):
        lines = super(SaleOrderLineBundle, self).create(vals_list)
        lines.filtered(lambda line: line.order_line_id.state == 'sale').order_line_id._action_launch_stock_rule()
        return lines
    
    def write(self, values):
        lines = self.env['sale.order.line.bundle']
        if 'quantity' in values:
            lines = self.filtered(lambda r: r.order_line_id.state == 'sale' and not r.order_line_id.is_expense)

        previous_product_uom_qty = {line.id: line.quantity for line in lines}
        res = super(SaleOrderLineBundle, self).write(values)
        if lines:
            lines.order_line_id._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)
        return res



    @api.depends('product_id')
    def _compute_uom_id(self):
        for line in self:
            if not line.uom_id or (line.product_id.uom_id.id != line.uom_id.id):
                line.uom_id = line.product_id.uom_id


    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.quantity', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        for line in self:
            qty = 0.0
            outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
            for move in outgoing_moves:
                if move.state != 'done':
                    continue
                qty += move.product_uom._compute_quantity(move.quantity, line.uom_id, rounding_method='HALF-UP')
            for move in incoming_moves:
                if move.state != 'done':
                    continue
                qty -= move.product_uom._compute_quantity(move.quantity, line.uom_id, rounding_method='HALF-UP')
            line.qty_delivered = qty

    def _prepare_procurement_values(self, group_id=False):
        values = self.order_line_id._prepare_procurement_values(group_id=group_id)
        values.update({
            'sale_bundle_line_id': self.id,
        })
        return values



    def _get_qty_procurement(self, previous_product_uom_qty=False):
        self.ensure_one()
        qty = 0.0
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves(strict=False)
        for move in outgoing_moves:
            qty_to_compute = move.quantity if move.state == 'done' else move.product_uom_qty
            qty += move.product_uom._compute_quantity(qty_to_compute, self.uom_id, rounding_method='HALF-UP')
        for move in incoming_moves:
            qty_to_compute = move.quantity if move.state == 'done' else move.product_uom_qty
            qty -= move.product_uom._compute_quantity(qty_to_compute, self.uom_id, rounding_method='HALF-UP')
        return qty
    
    def _create_procurements(self, product_qty, procurement_uom, origin, values):
        self.ensure_one()
        return [self.env['procurement.group'].Procurement(
            self.product_id, product_qty, procurement_uom, self.order_line_id._get_location_final(),
            self.product_id.display_name, origin, self.order_line_id.order_id.company_id, values)]
    
    def _get_outgoing_incoming_moves(self, strict=True):
        """ Return the outgoing and incoming moves of the sale order line.
            @param strict: If True, only consider the moves that are strictly delivered to the customer (old behavior).
                           If False, consider the moves that were created through the initial rule of the delivery route,
                           to support the new push mechanism.
        """
        outgoing_moves_ids = set()
        incoming_moves_ids = set()

        moves = self.move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id)
        if moves and not strict:
            # The first move created was the one created from the intial rule that started it all.
            sorted_moves = moves.sorted('id')
            triggering_rule_ids = []
            seen_wh_ids = set()
            for move in sorted_moves:
                if move.warehouse_id.id not in seen_wh_ids:
                    triggering_rule_ids.append(move.rule_id.id)
                    seen_wh_ids.add(move.warehouse_id.id)
        if self._context.get('accrual_entry_date'):
            moves = moves.filtered(lambda r: fields.Date.context_today(r, r.date) <= self._context['accrual_entry_date'])

        for move in moves:
            if (strict and move.location_dest_id._is_outgoing()) or \
               (not strict and move.rule_id.id in triggering_rule_ids and (move.location_final_id or move.location_dest_id)._is_outgoing()):
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    outgoing_moves_ids.add(move.id)
            elif move.location_id._is_outgoing() and move.to_refund:
                incoming_moves_ids.add(move.id)

        return self.env['stock.move'].browse(outgoing_moves_ids), self.env['stock.move'].browse(incoming_moves_ids)