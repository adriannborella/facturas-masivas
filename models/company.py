from odoo import models, fields, api

class res_company(models.Model):
    _inherit = [
        'res.company',
        # 'asw.correccion_ctas_ctes'
    ]

    monto_facturar = fields.Float(string='Monto a Facturar')
    talonario_defecto = fields.Many2one(
        string='Talonario',
        comodel_name='asw.talonario',
        ondelete='restrict',  
        required=True   ,      
        domain=[('tal_menu','in',['fac', 'rve']),('tal_tipo','=','e'),('tal_tpc_id','!=', False)]        
    )
    producto_default = fields.Many2one(string='Producto', comodel_name='asw.producto', ondelete='restrict', required=True)
