# -*- coding: utf-8 -*-
# from odoo import http


# class FjrSalesBundle(http.Controller):
#     @http.route('/fjr_sales_bundle/fjr_sales_bundle', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fjr_sales_bundle/fjr_sales_bundle/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fjr_sales_bundle.listing', {
#             'root': '/fjr_sales_bundle/fjr_sales_bundle',
#             'objects': http.request.env['fjr_sales_bundle.fjr_sales_bundle'].search([]),
#         })

#     @http.route('/fjr_sales_bundle/fjr_sales_bundle/objects/<model("fjr_sales_bundle.fjr_sales_bundle"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fjr_sales_bundle.object', {
#             'object': obj
#         })

