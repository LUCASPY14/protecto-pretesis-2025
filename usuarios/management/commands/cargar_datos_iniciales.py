"""
Datos iniciales para La Cantina de Tita
Desarrollado por LGservice - +595985350656
"""
from django.core.management.base import BaseCommand
from ventas.models import MetodoPago, PuntoVenta
from productos.models import Categoria

class Command(BaseCommand):
    help = 'Carga datos iniciales del sistema'
    
    def handle(self, *args, **options):
        # Crear métodos de pago según requerimientos
        metodos_pago = [
            {
                'nombre': 'Efectivo',
                'codigo': 'EFECTIVO',
                'descripcion': 'Pago en efectivo',
                'tiene_comision': False,
                'porcentaje_comision': 0.00,
                'genera_factura': True,
                'orden': 1
            },
            {
                'nombre': 'Transferencia',
                'codigo': 'TRANSFERENCIA',
                'descripcion': 'Transferencia bancaria',
                'tiene_comision': False,
                'porcentaje_comision': 0.00,
                'genera_factura': True,
                'orden': 2
            },
            {
                'nombre': 'Giros Tigo',
                'codigo': 'GIROS_TIGO',
                'descripcion': 'Giros Tigo Money',
                'tiene_comision': False,
                'porcentaje_comision': 0.00,
                'genera_factura': True,
                'orden': 3
            },
            {
                'nombre': 'Tarjeta Débito/QR',
                'codigo': 'TARJETA_DEBITO',
                'descripcion': 'Tarjeta de débito o QR con 4% de recarga',
                'tiene_comision': True,
                'porcentaje_comision': 4.00,
                'genera_factura': True,
                'orden': 4
            },
            {
                'nombre': 'Tarjeta Crédito/QR',
                'codigo': 'TARJETA_CREDITO',
                'descripcion': 'Tarjeta de crédito o QR con 6% de recarga',
                'tiene_comision': True,
                'porcentaje_comision': 6.00,
                'genera_factura': True,
                'orden': 5
            },
            {
                'nombre': 'Tarjeta Exclusiva Cantina',
                'codigo': 'SALDO_VIRTUAL',
                'descripcion': 'Saldo virtual de la tarjeta exclusiva de la cantina',
                'tiene_comision': False,
                'porcentaje_comision': 0.00,
                'genera_factura': False,  # No genera factura para evitar doble facturación
                'orden': 6
            },
        ]
        
        for metodo_data in metodos_pago:
            metodo, created = MetodoPago.objects.get_or_create(
                codigo=metodo_data['codigo'],
                defaults=metodo_data
            )
            if created:
                self.stdout.write(f'Método de pago creado: {metodo.nombre}')
            else:
                self.stdout.write(f'Método de pago ya existe: {metodo.nombre}')
        
        # Crear puntos de venta
        puntos_venta = [
            {
                'nombre': 'Caja Principal',
                'codigo': 'CAJA01',
                'ubicacion': 'Planta Baja - Cantina Principal',
                'activo': True
            },
            {
                'nombre': 'Caja Secundaria',
                'codigo': 'CAJA02',
                'ubicacion': 'Primer Piso - Cantina Secundaria',
                'activo': True
            },
            {
                'nombre': 'Caja Móvil',
                'codigo': 'MOVIL01',
                'ubicacion': 'Punto móvil para eventos',
                'activo': True
            }
        ]
        
        for punto_data in puntos_venta:
            punto, created = PuntoVenta.objects.get_or_create(
                codigo=punto_data['codigo'],
                defaults=punto_data
            )
            if created:
                self.stdout.write(f'Punto de venta creado: {punto.nombre}')
            else:
                self.stdout.write(f'Punto de venta ya existe: {punto.nombre}')
        
        # Crear categorías básicas de productos
        categorias = [
            {
                'nombre': 'Bebidas',
                'descripcion': 'Gaseosas, jugos, agua, etc.',
                'activo': True
            },
            {
                'nombre': 'Snacks',
                'descripcion': 'Papas fritas, galletas, chocolates, etc.',
                'activo': True
            },
            {
                'nombre': 'Comidas',
                'descripcion': 'Hamburguesas, empanadas, sándwiches, etc.',
                'activo': True
            },
            {
                'nombre': 'Dulces y Golosinas',
                'descripcion': 'Caramelos, chicles, etc.',
                'activo': True
            },
            {
                'nombre': 'Productos Escolares',
                'descripcion': 'Útiles escolares básicos',
                'activo': True
            }
        ]
        
        for categoria_data in categorias:
            categoria, created = Categoria.objects.get_or_create(
                nombre=categoria_data['nombre'],
                defaults=categoria_data
            )
            if created:
                self.stdout.write(f'Categoría creada: {categoria.nombre}')
            else:
                self.stdout.write(f'Categoría ya existe: {categoria.nombre}')
        
        self.stdout.write(
            self.style.SUCCESS('Datos iniciales cargados correctamente')
        )