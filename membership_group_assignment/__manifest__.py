# -*- coding: utf-8 -*-
{
    'name': 'Membership Group Assignment',
    'version': '15.0.1.0.0',
    'category': 'Custom',
    'summary': 'Membership Group Assignment',
    'description': "Organize membership group assignment",
    'depends': ['membership'],
    'installable': True,
    'auto_install': True,
    'license': 'AGPL-3',
    "data": {
        'views/product_views.xml',
        'views/membership_views.xml',
        'data/membership_data.xml',
    }
}
