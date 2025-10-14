from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import uuid

class MetodoPago(models.Model):
    """
    Métodos de pago disponibles en la cantina
    """
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True)
    
    # Configuración de comisiones
    tiene_comision = models.BooleanField(
        default=False,
        help_text="Si este método de pago tiene comisión"
    )
    porcentaje_comision = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de comisión aplicado"
    )
    
    # Control de facturación
    genera_factura = models.BooleanField(
        default=True,
        help_text="Si este método de pago genera factura legal"
    )
    
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de aparición en las listas"
    )
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['orden', 'nombre']


class PuntoVenta(models.Model):
    """
    Puntos de venta de la cantina
    """
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    ubicacion = models.CharField(max_length=200, blank=True)
    
    # Usuario asignado actualmente
    cajero_actual = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'tipo_usuario__in': ['cajero', 'administrador']},
        related_name='punto_venta_asignado'
    )
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    class Meta:
        verbose_name = "Punto de Venta"
        verbose_name_plural = "Puntos de Venta"
        ordering = ['codigo']


class Venta(models.Model):
    """
    Registro de ventas realizadas
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
        ('devuelta', 'Devuelta'),
    ]
    
    # Identificación única
    numero_venta = models.CharField(
        max_length=20, 
        unique=True,
        editable=False
    )
    
    # Información de la venta
    punto_venta = models.ForeignKey(
        PuntoVenta,
        on_delete=models.CASCADE,
        related_name='ventas'
    )
    
    cajero = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='ventas_realizadas',
        limit_choices_to={'tipo_usuario__in': ['cajero', 'administrador']}
    )
    
    # Cliente (puede ser hijo/estudiante o venta general)
    hijo = models.ForeignKey(
        'usuarios.PerfilHijo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compras'
    )
    
    cliente_nombre = models.CharField(
        max_length=150,
        blank=True,
        help_text="Nombre del cliente si no es estudiante"
    )
    
    # Totales
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    descuento = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    impuesto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    # Estado y fechas
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    
    fecha_venta = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.numero_venta:
            # Generar número de venta único
            fecha_str = timezone.now().strftime('%Y%m%d')
            ultimo_numero = Venta.objects.filter(
                numero_venta__startswith=f'V{fecha_str}'
            ).count() + 1
            self.numero_venta = f'V{fecha_str}{ultimo_numero:04d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        cliente = self.estudiante.nombre_completo if self.estudiante else self.cliente_nombre
        return f"{self.numero_venta} - {cliente} - {self.total}"
    
    @property
    def nombre_cliente(self):
        """Retorna el nombre del cliente"""
        if self.estudiante:
            return self.estudiante.nombre_completo
        return self.cliente_nombre or "Cliente General"
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha_venta']


class DetalleVenta(models.Model):
    """
    Detalles de productos vendidos en cada venta
    """
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.CASCADE,
        related_name='ventas_detalle'
    )
    
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio al momento de la venta"
    )
    
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Cantidad × Precio unitario"
    )
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.venta.numero_venta} - {self.producto.nombre} × {self.cantidad}"
    
    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"


class PagoVenta(models.Model):
    """
    Pagos realizados para una venta (permite pagos mixtos)
    """
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    
    monto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    
    # Información adicional según método de pago
    referencia = models.CharField(
        max_length=100,
        blank=True,
        help_text="Número de referencia, autorización, etc."
    )
    
    # Comisión calculada
    comision = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    fecha_pago = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Calcular comisión
        if self.metodo_pago.tiene_comision:
            self.comision = self.monto * (self.metodo_pago.porcentaje_comision / 100)
        else:
            self.comision = 0.00
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.venta.numero_venta} - {self.metodo_pago.nombre}: {self.monto}"
    
    class Meta:
        verbose_name = "Pago de Venta"
        verbose_name_plural = "Pagos de Venta"


class Factura(models.Model):
    """
    Facturas y boletas legales generadas
    """
    TIPO_FACTURA_CHOICES = [
        ('boleta', 'Boleta'),
        ('factura', 'Factura Exenta'),
        ('factura_afecta', 'Factura Afecta'),
    ]
    
    ESTADOS_DOCUMENTO = [
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida'),
        ('anulada', 'Anulada'),
        ('vencida', 'Vencida'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_factura = models.CharField(max_length=20, unique=True)
    
    venta = models.OneToOneField(
        Venta,
        on_delete=models.CASCADE,
        related_name='factura_documento'
    )
    
    tipo_factura = models.CharField(
        max_length=15,
        choices=TIPO_FACTURA_CHOICES,
        default='boleta'
    )
    
    # Datos del cliente para facturación
    cliente_nombre = models.CharField(max_length=200)
    cliente_rut = models.CharField(max_length=20, blank=True, null=True)
    cliente_direccion = models.TextField(blank=True, null=True)
    cliente_telefono = models.CharField(max_length=20, blank=True, null=True)
    cliente_email = models.EmailField(blank=True, null=True)
    
    # Totales de facturación
    subtotal_factura = models.DecimalField(max_digits=10, decimal_places=2)
    impuesto_factura = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_factura = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Estados y fechas
    estado = models.CharField(max_length=20, choices=ESTADOS_DOCUMENTO, default='borrador')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    fecha_anulacion = models.DateTimeField(blank=True, null=True)
    
    # Observaciones y notas
    observaciones = models.TextField(blank=True, null=True)
    notas_internas = models.TextField(blank=True, null=True)
    
    # Archivos generados
    archivo_pdf = models.FileField(
        upload_to='facturas/pdf/', 
        blank=True, 
        null=True
    )
    
    # Metadatos
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='facturas_creadas',
        null=True,  # Permitir null para compatibilidad
        blank=True
    )
    
    def save(self, *args, **kwargs):
        """Override para generar número y calcular montos"""
        if not self.numero_factura:
            # Importar aquí para evitar import circular
            from facturacion.models import ConfiguracionFacturacion
            
            configuracion = ConfiguracionFacturacion.objects.first()
            if not configuracion:
                configuracion = ConfiguracionFacturacion.objects.create()
            
            if self.tipo_factura == 'boleta':
                numero = configuracion.proximo_numero_boleta
                self.numero_factura = f"BOL-{numero:06d}"
                configuracion.proximo_numero_boleta += 1
            else:
                numero = configuracion.proximo_numero_factura  
                self.numero_factura = f"FAC-{numero:06d}"
                configuracion.proximo_numero_factura += 1
            
            configuracion.save()
        
        # Calcular montos
        if self.tipo_factura == 'factura_afecta':
            # Factura con IVA
            from facturacion.models import ConfiguracionFacturacion
            configuracion = ConfiguracionFacturacion.objects.first()
            if configuracion:
                iva_decimal = configuracion.iva_porcentaje / 100
                self.subtotal_factura = self.venta.total / (1 + iva_decimal)
                self.impuesto_factura = self.venta.total - self.subtotal_factura
            else:
                self.subtotal_factura = self.venta.total
                self.impuesto_factura = Decimal('0.00')
        else:
            # Boleta o factura exenta
            self.subtotal_factura = self.venta.total
            self.impuesto_factura = Decimal('0.00')
        
        self.total_factura = self.venta.total
        
        super().save(*args, **kwargs)
    
    # Propiedades de compatibilidad para los templates
    @property
    def numero(self):
        """Alias para numero_factura"""
        return self.numero_factura
    
    @property 
    def subtotal(self):
        """Alias para subtotal_factura"""
        return self.subtotal_factura
        
    @property
    def iva_monto(self):
        """Alias para impuesto_factura"""
        return self.impuesto_factura
        
    @property
    def iva_porcentaje(self):
        """Calcula el porcentaje de IVA"""
        if self.subtotal_factura > 0:
            return (self.impuesto_factura / self.subtotal_factura) * 100
        return Decimal('0.00')
        
    @property
    def total(self):
        """Alias para total_factura"""
        return self.total_factura
    
    def get_numero_formateado(self):
        """Retorna el número formateado para mostrar"""
        return self.numero_factura
    
    def anular(self, usuario, motivo=None):
        """Anula el documento"""
        self.estado = 'anulada'
        self.fecha_anulacion = timezone.now()
        if motivo:
            self.observaciones = f"Anulada: {motivo}"
        self.save()
        
        # Registrar en historial
        from facturacion.models import HistorialFacturacion
        HistorialFacturacion.objects.create(
            factura_numero=self.numero_factura,
            accion='anulada',
            descripcion=motivo,
            usuario=usuario
        )
    
    def emitir(self, usuario):
        """Emite el documento"""
        self.estado = 'emitida'
        self.save()
        
        # Registrar en historial
        from facturacion.models import HistorialFacturacion
        HistorialFacturacion.objects.create(
            factura_numero=self.numero_factura,
            accion='emitida',
            usuario=usuario
        )
    
    def __str__(self):
        return f"{self.numero_factura} - {self.cliente_nombre}"
    
    class Meta:
        verbose_name = "Factura/Boleta"
        verbose_name_plural = "Facturas/Boletas"
        ordering = ['-fecha_emision']
