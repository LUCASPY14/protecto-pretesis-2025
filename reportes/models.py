from django.db import models
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta

class ReporteBase(models.Model):
    """
    Modelo base para reportes generados
    """
    TIPO_REPORTE_CHOICES = [
        ('consumo_estudiante', 'Consumo por Estudiante'),
        ('productos_mas_vendidos', 'Productos Más Vendidos'),
        ('ingresos_metodo_pago', 'Ingresos por Método de Pago'),
        ('ventas_diarias', 'Ventas Diarias'),
        ('stock_productos', 'Estado de Stock'),
        ('comisiones_pagos', 'Comisiones de Pagos'),
    ]
    
    tipo_reporte = models.CharField(
        max_length=30,
        choices=TIPO_REPORTE_CHOICES
    )
    
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    
    # Período del reporte
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    # Usuario que generó el reporte
    generado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='reportes_%(class)s_generados'
    )
    
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    # Archivo generado
    archivo_excel = models.FileField(
        upload_to='reportes/', 
        blank=True, 
        null=True
    )
    
    archivo_pdf = models.FileField(
        upload_to='reportes/', 
        blank=True, 
        null=True
    )
    
    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.fecha_inicio} a {self.fecha_fin}"
    
    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        ordering = ['-fecha_generacion']
        abstract = True


class ReporteConsumoEstudiante(ReporteBase):
    """
    Reporte específico de consumo por estudiante
    """
    estudiante = models.ForeignKey(
        'usuarios.PerfilHijo',
        on_delete=models.CASCADE,
        related_name='reportes_consumo'
    )
    
    # Datos calculados
    total_compras = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    cantidad_transacciones = models.IntegerField(default=0)
    producto_mas_comprado = models.CharField(max_length=150, blank=True)
    promedio_gasto_diario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    class Meta:
        verbose_name = "Reporte de Consumo de Hijo"
        verbose_name_plural = "Reportes de Consumo de Hijos"


class ReporteProductosMasVendidos(ReporteBase):
    """
    Reporte de productos más vendidos
    """
    # Los datos se almacenarán en DetalleReporteProducto
    
    class Meta:
        verbose_name = "Reporte de Productos Más Vendidos"
        verbose_name_plural = "Reportes de Productos Más Vendidos"


class DetalleReporteProducto(models.Model):
    """
    Detalle de productos en reporte de más vendidos
    """
    reporte = models.ForeignKey(
        ReporteProductosMasVendidos,
        on_delete=models.CASCADE,
        related_name='detalles_productos'
    )
    
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.CASCADE
    )
    
    cantidad_vendida = models.IntegerField()
    monto_total_vendido = models.DecimalField(max_digits=10, decimal_places=2)
    numero_transacciones = models.IntegerField()
    
    class Meta:
        verbose_name = "Detalle de Reporte de Producto"
        verbose_name_plural = "Detalles de Reporte de Productos"
        ordering = ['-cantidad_vendida']


class ReporteIngresosPorMetodo(ReporteBase):
    """
    Reporte de ingresos por método de pago
    """
    # Los datos se almacenarán en DetalleReporteMetodoPago
    
    total_ingresos = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00
    )
    
    total_comisiones = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    class Meta:
        verbose_name = "Reporte de Ingresos por Método de Pago"
        verbose_name_plural = "Reportes de Ingresos por Método de Pago"


class DetalleReporteMetodoPago(models.Model):
    """
    Detalle de ingresos por método de pago
    """
    reporte = models.ForeignKey(
        ReporteIngresosPorMetodo,
        on_delete=models.CASCADE,
        related_name='detalles_metodos'
    )
    
    metodo_pago = models.ForeignKey(
        'ventas.MetodoPago',
        on_delete=models.CASCADE
    )
    
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_transacciones = models.IntegerField()
    comision_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Detalle de Reporte por Método de Pago"
        verbose_name_plural = "Detalles de Reporte por Método de Pago"
        ordering = ['-monto_total']


class AlertaStock(models.Model):
    """
    Alertas de stock bajo para productos
    """
    TIPO_ALERTA_CHOICES = [
        ('stock_bajo', 'Stock Bajo'),
        ('stock_agotado', 'Stock Agotado'),
        ('stock_excesivo', 'Stock Excesivo'),
    ]
    
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.CASCADE,
        related_name='alertas_stock'
    )
    
    tipo_alerta = models.CharField(
        max_length=15,
        choices=TIPO_ALERTA_CHOICES
    )
    
    stock_actual = models.IntegerField()
    stock_minimo = models.IntegerField()
    stock_maximo = models.IntegerField()
    
    mensaje = models.TextField()
    
    # Control de notificaciones
    notificada = models.BooleanField(default=False)
    fecha_notificacion = models.DateTimeField(null=True, blank=True)
    
    resuelto = models.BooleanField(default=False)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.get_tipo_alerta_display()}"
    
    class Meta:
        verbose_name = "Alerta de Stock"
        verbose_name_plural = "Alertas de Stock"
        ordering = ['-fecha_creacion']


class ConfiguracionReporte(models.Model):
    """
    Configuración para generación automática de reportes
    """
    FRECUENCIA_CHOICES = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
    ]
    
    tipo_reporte = models.CharField(
        max_length=30,
        choices=ReporteBase.TIPO_REPORTE_CHOICES
    )
    
    frecuencia = models.CharField(
        max_length=10,
        choices=FRECUENCIA_CHOICES
    )
    
    hora_generacion = models.TimeField(
        help_text="Hora del día para generar el reporte automático"
    )
    
    activo = models.BooleanField(default=True)
    
    # Destinatarios por email
    destinatarios = models.TextField(
        help_text="Emails separados por comas para enviar el reporte"
    )
    
    fecha_ultimo_reporte = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Reporte {self.get_tipo_reporte_display()} - {self.get_frecuencia_display()}"
    
    class Meta:
        verbose_name = "Configuración de Reporte"
        verbose_name_plural = "Configuraciones de Reportes"
