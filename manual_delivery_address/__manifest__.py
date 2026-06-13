# -*- coding: utf-8 -*-
{
    'name': "Manual Delivery Address",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Fajar - 0812 6888 8199",
    'website': "https://www.yourcompany.com",

   
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/account_move.xml',
    ],
    
}

