#!/usr/bin/env python
"""
Script para crear datos iniciales del POS: métodos de pago, productos, etc.
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cantina_tita.settings")
    django.setup()

from ventas.models import MetodoPago, PuntoVenta
from productos.models import Categoria, Producto

def crear_metodos_pago():
    """Crear métodos de pago básicos"""
    metodos = [
        {
            'nombre': 'Tarjeta Exclusiva',
            'codigo': 'TARJETA',
            'descripcion': 'Pago con tarjeta exclusiva de La Cantina de Tita (saldo virtual)',
            'tiene_comision': False,
            'genera_factura': True,
            'orden': 1
        },
        {
            'nombre': 'Efectivo',
            'codigo': 'EFECTIVO',
            'descripcion': 'Pago en efectivo',
            'tiene_comision': False,
            'genera_factura': True,
            'orden': 2
        },
        {
            'nombre': 'Pago Móvil',
            'codigo': 'PAGO_MOVIL',
            'descripcion': 'Pago móvil interbancario',
            'tiene_comision': False,
            'genera_factura': True,
            'orden': 3
        },
        {
            'nombre': 'Zelle',
            'codigo': 'ZELLE',
            'descripcion': 'Pago en dólares por Zelle',
            'tiene_comision': True,
            'porcentaje_comision': Decimal('3.00'),
            'genera_factura': True,
            'orden': 4
        }
    ]
    
    for metodo_data in metodos:
        metodo, created = MetodoPago.objects.get_or_create(
            codigo=metodo_data['codigo'],
            defaults=metodo_data
        )
        if created:
            print(f"✅ Método de pago creado: {metodo.nombre}")
        else:
            print(f"📋 Método de pago ya existe: {metodo.nombre}")

def crear_puntos_venta():
    """Crear puntos de venta básicos"""
    puntos = [
        {
            'nombre': 'Caja Principal',
            'codigo': 'CAJA01',
            'ubicacion': 'Entrada principal de la cantina'
        },
        {
            'nombre': 'Caja Secundaria',
            'codigo': 'CAJA02',
            'ubicacion': 'Área de comidas rápidas'
        }
    ]
    
    for punto_data in puntos:
        punto, created = PuntoVenta.objects.get_or_create(
            codigo=punto_data['codigo'],
            defaults=punto_data
        )
        if created:
            print(f"✅ Punto de venta creado: {punto.nombre}")
        else:
            print(f"📋 Punto de venta ya existe: {punto.nombre}")

def crear_categorias_productos():
    """Crear categorías de productos"""
    categorias = [
        {
            'nombre': 'Bebidas',
            'descripcion': 'Refrescos, jugos, agua y bebidas calientes'
        },
        {
            'nombre': 'Snacks',
            'descripcion': 'Chucherías, galletas y aperitivos'
        },
        {
            'nombre': 'Comidas',
            'descripcion': 'Empanadas, sandwiches y comidas rápidas'
        },
        {
            'nombre': 'Dulces',
            'descripcion': 'Chocolates, caramelos y postres'
        },
        {
            'nombre': 'Útiles Escolares',
            'descripcion': 'Lápices, borradores y artículos escolares'
        }
    ]
    
    categorias_creadas = []
    for cat_data in categorias:
        categoria, created = Categoria.objects.get_or_create(
            nombre=cat_data['nombre'],
            defaults=cat_data
        )
        categorias_creadas.append(categoria)
        if created:
            print(f"✅ Categoría creada: {categoria.nombre}")
        else:
            print(f"📋 Categoría ya existe: {categoria.nombre}")
    
    return categorias_creadas

def crear_productos(categorias):
    """Crear productos de ejemplo"""
    # Obtener categorías por nombre
    cat_bebidas = next((c for c in categorias if c.nombre == 'Bebidas'), None)
    cat_snacks = next((c for c in categorias if c.nombre == 'Snacks'), None)
    cat_comidas = next((c for c in categorias if c.nombre == 'Comidas'), None)
    cat_dulces = next((c for c in categorias if c.nombre == 'Dulces'), None)
    cat_utiles = next((c for c in categorias if c.nombre == 'Útiles Escolares'), None)
    
    productos = [
        # Bebidas
        {
            'categoria': cat_bebidas,
            'codigo': 'BEB001',
            'nombre': 'Coca Cola 500ml',
            'precio_costo': Decimal('2500'),
            'precio_venta': Decimal('4000'),
            'stock_actual': 50,
            'stock_minimo': 10
        },
        {
            'categoria': cat_bebidas,
            'codigo': 'BEB002',
            'nombre': 'Agua Mineral 500ml',
            'precio_costo': Decimal('1000'),
            'precio_venta': Decimal('2000'),
            'stock_actual': 30,
            'stock_minimo': 5
        },
        {
            'categoria': cat_bebidas,
            'codigo': 'BEB003',
            'nombre': 'Jugo de Naranja',
            'precio_costo': Decimal('1500'),
            'precio_venta': Decimal('3000'),
            'stock_actual': 25,
            'stock_minimo': 8
        },
        
        # Snacks
        {
            'categoria': cat_snacks,
            'codigo': 'SNK001',
            'nombre': 'Doritos Nacho',
            'precio_costo': Decimal('2000'),
            'precio_venta': Decimal('3500'),
            'stock_actual': 40,
            'stock_minimo': 10
        },
        {
            'categoria': cat_snacks,
            'codigo': 'SNK002',
            'nombre': 'Cheetos Inflados',
            'precio_costo': Decimal('1800'),
            'precio_venta': Decimal('3000'),
            'stock_actual': 35,
            'stock_minimo': 8
        },
        
        # Comidas
        {
            'categoria': cat_comidas,
            'codigo': 'COM001',
            'nombre': 'Empanada de Carne',
            'precio_costo': Decimal('3000'),
            'precio_venta': Decimal('5000'),
            'stock_actual': 20,
            'stock_minimo': 5
        },
        {
            'categoria': cat_comidas,
            'codigo': 'COM002',
            'nombre': 'Sandwich de Jamón y Queso',
            'precio_costo': Decimal('4000'),
            'precio_venta': Decimal('7000'),
            'stock_actual': 15,
            'stock_minimo': 3
        },
        
        # Dulces
        {
            'categoria': cat_dulces,
            'codigo': 'DUL001',
            'nombre': 'Chocolate Jet',
            'precio_costo': Decimal('800'),
            'precio_venta': Decimal('1500'),
            'stock_actual': 60,
            'stock_minimo': 15
        },
        {
            'categoria': cat_dulces,
            'codigo': 'DUL002',
            'nombre': 'Gomitas de Frutas',
            'precio_costo': Decimal('1200'),
            'precio_venta': Decimal('2000'),
            'stock_actual': 45,
            'stock_minimo': 12
        },
        
        # Útiles Escolares
        {
            'categoria': cat_utiles,
            'codigo': 'UTI001',
            'nombre': 'Lápiz #2',
            'precio_costo': Decimal('500'),
            'precio_venta': Decimal('1000'),
            'stock_actual': 100,
            'stock_minimo': 20
        },
        {
            'categoria': cat_utiles,
            'codigo': 'UTI002',
            'nombre': 'Borrador Blanco',
            'precio_costo': Decimal('300'),
            'precio_venta': Decimal('800'),
            'stock_actual': 80,
            'stock_minimo': 15
        }
    ]
    
    for prod_data in productos:
        if prod_data['categoria']:  # Solo crear si la categoría existe
            producto, created = Producto.objects.get_or_create(
                codigo=prod_data['codigo'],
                defaults=prod_data
            )
            if created:
                print(f"✅ Producto creado: {producto.nombre} - Bs. {producto.precio_venta}")
            else:
                print(f"📋 Producto ya existe: {producto.nombre}")

def main():
    """Función principal"""
    print("🚀 Creando datos iniciales del POS...\n")
    
    print("📝 Creando métodos de pago...")
    crear_metodos_pago()
    
    print("\n🏪 Creando puntos de venta...")
    crear_puntos_venta()
    
    print("\n📦 Creando categorías de productos...")
    categorias = crear_categorias_productos()
    
    print("\n🍫 Creando productos de ejemplo...")
    crear_productos(categorias)
    
    print("\n🎉 ¡Datos iniciales del POS creados exitosamente!")
    print("\n📋 Resumen:")
    print(f"   💳 Métodos de pago: {MetodoPago.objects.count()}")
    print(f"   🏪 Puntos de venta: {PuntoVenta.objects.count()}")
    print(f"   📦 Categorías: {Categoria.objects.count()}")
    print(f"   🍫 Productos: {Producto.objects.count()}")
    
    print("\n🌐 Acceso al POS:")
    print("   🖥️  Panel POS: http://localhost:8001/ventas/pos/")
    print("   👤 Usuarios permitidos: cajeros y administradores")

if __name__ == "__main__":
    main()