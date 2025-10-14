from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Categoria(models.Model):
    """
    Categorías de productos para la cantina
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']


class Producto(models.Model):
    """
    Productos disponibles en la cantina
    """
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.CASCADE,
        related_name='productos'
    )
    
    codigo = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Código interno del producto"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    
    # Precios
    precio_costo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Precio de costo del producto"
    )
    precio_venta = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Precio de venta al público"
    )
    
    # Inventario
    stock_actual = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cantidad actual en stock"
    )
    stock_minimo = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        help_text="Stock mínimo antes de alertar"
    )
    stock_maximo = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0)],
        help_text="Stock máximo recomendado"
    )
    
    # Información adicional
    imagen = models.ImageField(
        upload_to='productos/', 
        blank=True, 
        null=True,
        help_text="Imagen del producto"
    )
    
    # Control de disponibilidad
    disponible = models.BooleanField(
        default=True,
        help_text="Producto disponible para la venta"
    )
    requiere_stock = models.BooleanField(
        default=True,
        help_text="Si requiere control de stock o es ilimitado"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo
    
    @property
    def puede_venderse(self):
        """Verifica si el producto puede venderse"""
        if not self.disponible:
            return False
        if self.requiere_stock and self.stock_actual <= 0:
            return False
        return True
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia"""
        if self.precio_costo > 0:
            return ((self.precio_venta - self.precio_costo) / self.precio_costo) * 100
        return 0
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['categoria__nombre', 'nombre']


class MovimientoStock(models.Model):
    """
    Historial de movimientos de stock
    """
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste de Inventario'),
        ('venta', 'Venta'),
        ('devolucion', 'Devolución'),
    ]
    
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE,
        related_name='movimientos_stock'
    )
    
    tipo_movimiento = models.CharField(
        max_length=15,
        choices=TIPO_MOVIMIENTO_CHOICES
    )
    
    cantidad = models.IntegerField(
        help_text="Cantidad del movimiento (positivo para entradas, negativo para salidas)"
    )
    
    stock_anterior = models.IntegerField(
        help_text="Stock antes del movimiento"
    )
    
    stock_nuevo = models.IntegerField(
        help_text="Stock después del movimiento"
    )
    
    motivo = models.CharField(
        max_length=200,
        blank=True,
        help_text="Motivo del movimiento"
    )
    
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='movimientos_stock_realizados'
    )
    
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.get_tipo_movimiento_display()}: {self.cantidad}"
    
    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ['-fecha_movimiento']


class Proveedor(models.Model):
    """
    Proveedores de productos
    """
    nombre = models.CharField(max_length=150)
    ruc = models.CharField(max_length=20, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    contacto_nombre = models.CharField(max_length=150, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']
