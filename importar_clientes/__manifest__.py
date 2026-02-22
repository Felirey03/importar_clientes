{

    'name': 'Importar Clientes CSV',
    'version': '1.0',
    'category': 'sales',
    'summary': 'Importa contactos desde archivos CSV',
    'description': """
        Modulo para importar clientes desde archivos CSV.
        Permite subir un archivo y crear/actualizar contactos desde Odoo.
    """,
    'author': 'Felipe Reynoso',
    'depends': ['base','contacts'],
    'data':[
        'security/ir.model.access.csv',
        
        'wizards/importador_wizard_view.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application':True,

}