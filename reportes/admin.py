from django.contrib import admin
from .models import (
    ReporteConsumoEstudiante, ReporteProductosMasVendidos, ReporteIngresosPorMetodo,
    DetalleReporteProducto, DetalleReporteMetodoPago, AlertaStock, ConfiguracionReporte
)

@admin.register(ReporteConsumoEstudiante)
class ReporteConsumoEstudianteAdmin(admin.ModelAdmin):
    """
    Administración para reportes de consumo de hijos
    """
    list_display = ('estudiante', 'total_compras', 'cantidad_transacciones', 'fecha_inicio', 'fecha_fin', 'fecha_generacion')
    list_filter = ('fecha_generacion', 'fecha_inicio', 'fecha_fin')
    search_fields = ('estudiante__nombre_completo', 'estudiante__padre__username')
    ordering = ('-fecha_generacion',)
    
    readonly_fields = ('fecha_generacion',)


@admin.register(ReporteProductosMasVendidos)
class ReporteProductosMasVendidosAdmin(admin.ModelAdmin):
    """
    Administración para reportes de productos más vendidos
    """
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'generado_por', 'fecha_generacion')
    list_filter = ('fecha_generacion', 'generado_por')
    search_fields = ('nombre', 'descripcion')
    ordering = ('-fecha_generacion',)


@admin.register(ReporteIngresosPorMetodo)
class ReporteIngresosPorMetodoAdmin(admin.ModelAdmin):
    """
    Administración para reportes de ingresos por método de pago
    """
    list_display = ('nombre', 'total_ingresos', 'total_comisiones', 'fecha_inicio', 'fecha_fin', 'fecha_generacion')
    list_filter = ('fecha_generacion',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('-fecha_generacion',)


@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    """
    Administración para alertas de stock
    """
    list_display = ('producto', 'tipo_alerta', 'stock_actual', 'stock_minimo', 'notificada', 'resuelto', 'fecha_creacion')
    list_filter = ('tipo_alerta', 'notificada', 'resuelto', 'fecha_creacion')
    search_fields = ('producto__nombre', 'producto__codigo')
    ordering = ('-fecha_creacion',)
    
    readonly_fields = ('fecha_creacion', 'fecha_notificacion', 'fecha_resolucion')


@admin.register(ConfiguracionReporte)
class ConfiguracionReporteAdmin(admin.ModelAdmin):
    """
    Administración para configuración de reportes automáticos
    """
    list_display = ('tipo_reporte', 'frecuencia', 'hora_generacion', 'activo', 'fecha_ultimo_reporte')
    list_filter = ('tipo_reporte', 'frecuencia', 'activo')
    ordering = ('tipo_reporte', 'frecuencia')
