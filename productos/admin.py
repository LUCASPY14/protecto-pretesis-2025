from django.contrib import admin
from .models import Categoria, Producto, MovimientoStock, Proveedor

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    Administración para categorías de productos
    """
    list_display = ('nombre', 'descripcion', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """
    Administración para productos
    """
    list_display = ('codigo', 'nombre', 'categoria', 'precio_venta', 'stock_actual', 'stock_bajo', 'disponible')
    list_filter = ('categoria', 'disponible', 'requiere_stock', 'fecha_creacion')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('categoria', 'nombre')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria', 'imagen')
        }),
        ('Precios', {
            'fields': ('precio_costo', 'precio_venta')
        }),
        ('Inventario', {
            'fields': ('stock_actual', 'stock_minimo', 'stock_maximo', 'requiere_stock')
        }),
        ('Disponibilidad', {
            'fields': ('disponible',)
        })
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    def stock_bajo(self, obj):
        return obj.stock_bajo
    stock_bajo.boolean = True
    stock_bajo.short_description = 'Stock Bajo'


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    """
    Administración para movimientos de stock
    """
    list_display = ('producto', 'tipo_movimiento', 'cantidad', 'stock_anterior', 'stock_nuevo', 'fecha_movimiento', 'usuario')
    list_filter = ('tipo_movimiento', 'fecha_movimiento', 'usuario')
    search_fields = ('producto__nombre', 'producto__codigo', 'motivo')
    ordering = ('-fecha_movimiento',)
    
    readonly_fields = ('fecha_movimiento',)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    """
    Administración para proveedores
    """
    list_display = ('nombre', 'ruc', 'telefono', 'email', 'contacto_nombre', 'activo')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'ruc', 'email', 'contacto_nombre')
    ordering = ('nombre',)
