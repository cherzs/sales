{
    "name": "Purchase Backdate and Postdate in Odoo",
    "version": "18.0.0.0",

    "summary": """Backdate or postdate Purchase Orders to match real business timelines.  
                  Easily adjust PO, receipt, and vendor bill dates for accurate reporting.  
                  Ensure compliance with mandatory notes and maintain transparent procurement.
                """,

    "description": """Backdate or postdate Purchase Orders to match real business timelines.  
                      Easily adjust PO, receipt, and vendor bill dates for accurate reporting.  
                      Ensure compliance with mandatory notes and maintain transparent procurement.
                   """,

    "author": "Reliution",
    "website": "https://www.reliution.com",
    "support": "support@reliution.com",
    "category": "Purchase",

    "images": ["static/description/banner.gif"],

    'license': 'AGPL-3',

    "depends": ["purchase", "stock", "purchase_stock"],

    "data": [
        'security/purchase_backdate_groups.xml',
        'security/ir.model.access.csv',
        'data/purchase_order_data.xml',
        'views/account_move_views.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_move_views.xml',
        'views/stock_picking_views.xml',
        'wizard/extends_support_wizard.xml',
        'wizard/purchase_backdate_wizard_views.xml',
    ],

    "price": 50,
    "currency": "USD",
    "auto_install": False,
    "installable": True,
    "application": True,
    'live_test_url': "https://www.reliution.com/odoo-app-store?app_name=rcs_purchase_backdate_and_postdate&app_version=18.0&odoo_type=Community"
}
