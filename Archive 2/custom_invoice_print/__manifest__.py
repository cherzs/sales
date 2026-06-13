# -*- coding: utf-8 -*-
{
    'name': "Custom - Invoice Print",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Fajar - 0812 6888 8199",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'fjr_sales_customer_code', 'manual_delivery_address'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',

        'report/account_move.xml',
       
    ],
}

