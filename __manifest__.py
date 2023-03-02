# -*- coding: utf-8 -*-
{
    'name': "factura-masiva",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Adrian Borella",
    'website': "https://www.linkedin.com/in/adriannborella/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'asw_tpv', 'asw_afipws_fe'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/facturas.xml', 
        'views/company.xml',  
        'views/menu.xml',          
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}