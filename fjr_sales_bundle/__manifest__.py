# -*- coding: utf-8 -*-
{
    'name': "Sales Bundle Management",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Fajar - 0812 6888 8199",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/sale_order.xml',

        'wizard/sale_order_line_bundle_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

