from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


class TipoDocumento(models.Model):
    """Tipos de documentos fiscales"""
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    requiere_rut = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"


class ConfiguracionFacturacion(models.Model):
    """Configuración general de facturación"""
    empresa_nombre = models.CharField(max_length=200, default="La Cantina de Tita")
    empresa_rut = models.CharField(max_length=20, default="76.123.456-7")
    empresa_direccion = models.TextField(default="Av. Principal 123, Santiago, Chile")
    empresa_telefono = models.CharField(max_length=20, default="+56 9 1234 5678")
    empresa_email = models.EmailField(default="info@cantinatita.cl")
    
    # Configuración de numeración
    proximo_numero_boleta = models.PositiveIntegerField(default=1)
    proximo_numero_factura = models.PositiveIntegerField(default=1)
    
    # Configuración de impuestos
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'))
    
    # Configuración de documentos
    emite_boletas = models.BooleanField(default=True)
    emite_facturas = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Configuración de {self.empresa_nombre}"
    
    class Meta:
        verbose_name = "Configuración de Facturación"
        verbose_name_plural = "Configuraciones de Facturación"


class HistorialFacturacion(models.Model):
    """Historial de cambios en las facturas"""
    
    ACCIONES = [
        ('creada', 'Creada'),
        ('emitida', 'Emitida'),
        ('anulada', 'Anulada'),
        ('modificada', 'Modificada'),
        ('impresa', 'Impresa'),
        ('enviada', 'Enviada por Email'),
    ]
    
    # Usamos el modelo Factura de ventas
    factura_numero = models.CharField(max_length=20)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    descripcion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Factura {self.factura_numero} - {self.get_accion_display()} - {self.fecha}"
    
    class Meta:
        verbose_name = "Historial de Facturación"
        verbose_name_plural = "Historiales de Facturación"
        ordering = ['-fecha']
