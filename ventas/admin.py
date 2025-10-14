from django.contrib import admin
from .models import MetodoPago, PuntoVenta, Venta, DetalleVenta, PagoVenta, Factura

@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    """
    Administración para métodos de pago
    """
    list_display = ('nombre', 'codigo', 'tiene_comision', 'porcentaje_comision', 'genera_factura', 'activo', 'orden')
    list_filter = ('tiene_comision', 'genera_factura', 'activo')
    search_fields = ('nombre', 'codigo')
    ordering = ('orden', 'nombre')


@admin.register(PuntoVenta)
class PuntoVentaAdmin(admin.ModelAdmin):
    """
    Administración para puntos de venta
    """
    list_display = ('codigo', 'nombre', 'ubicacion', 'cajero_actual', 'activo')
    list_filter = ('activo', 'cajero_actual')
    search_fields = ('codigo', 'nombre', 'ubicacion')
    ordering = ('codigo',)


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('subtotal',)


class PagoVentaInline(admin.TabularInline):
    model = PagoVenta
    extra = 0
    readonly_fields = ('comision', 'fecha_pago')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    """
    Administración para ventas
    """
    list_display = ('numero_venta', 'nombre_cliente', 'cajero', 'punto_venta', 'total', 'estado', 'fecha_venta')
    list_filter = ('estado', 'punto_venta', 'cajero', 'fecha_venta')
    search_fields = ('numero_venta', 'cliente_nombre', 'estudiante__nombre_completo')
    ordering = ('-fecha_venta',)
    
    inlines = [DetalleVentaInline, PagoVentaInline]
    
    readonly_fields = ('numero_venta', 'fecha_venta', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información de Venta', {
            'fields': ('numero_venta', 'punto_venta', 'cajero', 'estado')
        }),
        ('Cliente', {
            'fields': ('estudiante', 'cliente_nombre')
        }),
        ('Totales', {
            'fields': ('subtotal', 'descuento', 'impuesto', 'total')
        }),
        ('Fechas', {
            'fields': ('fecha_venta', 'fecha_actualizacion')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        })
    )


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    """
    Administración para facturas
    """
    list_display = ('numero_factura', 'cliente_nombre', 'tipo_factura', 'total_factura', 'fecha_emision')
    list_filter = ('tipo_factura', 'fecha_emision')
    search_fields = ('numero_factura', 'cliente_nombre', 'cliente_ruc')
    ordering = ('-fecha_emision',)
    
    readonly_fields = ('fecha_emision',)
