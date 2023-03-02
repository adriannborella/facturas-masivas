# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp

class asw_comprobante(models.Model):
    _inherit = "asw.comprobante"

    facturador_id = fields.Many2one(string='Facturador', comodel_name='facturamasiva.facturador', ondelete='restrict')
    

class facturador(models.Model):
    _name = 'facturamasiva.facturador'

    talonario_id = fields.Many2one(
        string='Talonario',
        comodel_name='asw.talonario',
        ondelete='restrict',  
        required=True   ,      
        domain=[('tal_menu','in',['fac', 'rve']),('tal_tipo','=','e'),('tal_tpc_id','!=', False)]        
    )

    cliente_id = fields.Many2one(
        string='Cliente',
        comodel_name='asw.cliente',
        ondelete='restrict',
        required=True             
    )

    producto_id = fields.Many2one(string='Producto', comodel_name='asw.producto', ondelete='restrict', required=True)

    moneda = fields.Many2one(
        string=u'Moneda',
        comodel_name='res.currency',
        ondelete='set null',
        default=lambda self: self.env.user.company_id.currency_id.id,
    )

    monto_maximo = fields.Monetary(
        digits=2,
        string=u'Monto maximo',
        currency_field='moneda',
        required=True
    )

    monto_facturar = fields.Monetary(
        digits=2,
        string=u'Monto a Facturar',
        currency_field='moneda',
        required=True
    )
    
    state = fields.Selection(
        string='state',
        selection=[('borrador', 'Borrador'), 
                   ('confirmado', 'Confirmado'), 
                   ('procesado', 'Procesado'),
                   ('cancelado', 'Cancelado')],
        default='borrador'
    )  

    lineas_ids = fields.One2many(string='Facturas',comodel_name='asw.comprobante',inverse_name='facturador_id' )

    @api.model
    def default_get(self, fields):
        result = super(facturador, self).default_get(fields)
        result.update({
            "talonario_id": self.env.user.company_id.talonario_defecto.id,
            "cliente_id": self.env.user.company_id.res_cliente_defecto.id,
            "monto_maximo": self.env.user.company_id.monto_facturar,
            "producto_id": self.env.user.company_id.producto_default.id
        })        
        return result
    
    def desconfirmar(self):
        self.lineas_ids.unlink()
        self.state = "borrador"

    @api.multi
    def confirmar(self):
        if self.monto_facturar <= 0:
            raise ValidationError('El monto a facturar debe ser mayor a 0') 
        resto = self.monto_facturar
        while resto > 0:
            a_facturar = round(min(resto, self.monto_maximo), 2)            
            resto = round(resto - a_facturar,2)
            
            comprobante = self.lineas_ids.generar_comprobante(
                self.talonario_id,
                self.cliente_id,
                a_facturar,
                'Comprobante generado masivamente'
            )
            comprobante.facturador_id = self.id

            comprobante.agregar_producto(self.producto_id, a_facturar)
        
        self.state = "confirmado"
    
    @api.multi
    def cancelar(self):
        tal = self.env['asw.talonario'].search([
            ('tal_tipo','=', self.talonario_id.tal_tipo ), 
            ('tal_menu','=', 'rve'), 
            ('tal_letra','=', self.talonario_id.tal_letra)], limit=1)
        for comprobante in self.lineas_ids:
            print(comprobante.id)
            comprobante.cancelar_pago()
            context = {
                'default_rc_talonario_original': comprobante.comp_talonario.id,
                'active_id' : comprobante.id
            }
            objeto = self.env['asw.reintegro_comprobante_wizzard'].with_context(context).create({ })
            objeto._asignar_talonario()
            objeto.rc_talonario = tal.id
    
            result = objeto.realizar_contracomprobante()            
            self.relacionar_comprobante(result)
        
        self.state = "cancelado"

    @api.multi
    def procesar(self):
        # TODO:  Ver como hacer para que un solo pago se relacione con todos los comprobantes creados
        # cntx = {
        #     'default_pcw_cliente': self.cliente_id.id,
        #     'default_pcw_referencia' : "Pago Automatico Procesar Facturas Masivas",
        #     "params":{
        #         "action": self.env.ref('asw_tpv.asw_tpv_ventas_ventas_registrar_cobro').id            
        #     }
        # }
        
        # wizzard = self.env['asw.pago_cliente_wizzard'].with_context(cntx).create({})
        # wizzard.pcw_transferencias_recibidas = [(0, 0, {
        #     'val_monto': self.monto_facturar
        # })]
        # result = wizzard.generar_recibo()
        # self.relacionar_comprobante(result)

        for comp in self.lineas_ids:
            if comp.comp_estado == "b":
                comp.validar()
                comp.pagar_transferencia()
        
        self.state = "procesado"

        # Actualiza valores por defecto
        company = self.env.user.company_id
        company.talonario_defecto = self.talonario_id.id
        company.res_cliente_defecto = self.cliente_id.id
        company.monto_facturar = self.monto_maximo
        company.producto_default = self.producto_id.id
    
    def relacionar_comprobante(self, result):
        rcomprobante = self.env['asw.comprobante'].search([('id','=',result.get("res_id"))])
        rcomprobante.facturador_id = self.id
            
    @api.multi
    def unlink(self):
        for record in self:
            if record.state != "borrador":
                raise ValidationError("Solo pueden eliminarse los registros que se encuentren en estado borrador")
        
        return super(facturador, self).unlink()
