#!/usr/bin/env python
"""
Script para crear datos de prueba para el sistema de tarjetas de La Cantina de Tita
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date

# Configurar Django
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cantina_tita.settings")
    django.setup()

from usuarios.models import Usuario, PerfilHijo

def crear_datos_prueba():
    """Crear datos de prueba para demostrar el sistema de tarjetas"""
    
    # Crear padre de ejemplo
    padre, created = Usuario.objects.get_or_create(
        username='juan_perez',
        defaults={
            'email': 'juan.perez@gmail.com',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'tipo_usuario': 'padre',
            'telefono': '04241234567',
            'cedula': '12345678',
            'direccion': 'Av. Principal #123, Caracas',
            'is_active': True,
        }
    )
    
    if created:
        padre.set_password('password123')
        padre.save()
        print(f"✅ Padre creado: {padre.get_full_name()}")
    else:
        print(f"📋 Padre ya existe: {padre.get_full_name()}")
    
    # Crear cajero de ejemplo
    cajero, created = Usuario.objects.get_or_create(
        username='maria_cajera',
        defaults={
            'email': 'maria.cajera@cantina.com',
            'first_name': 'María',
            'last_name': 'González',
            'tipo_usuario': 'cajero',
            'telefono': '04261234567',
            'cedula': '87654321',
            'direccion': 'Calle Segunda #456, Caracas',
            'is_active': True,
        }
    )
    
    if created:
        cajero.set_password('cajero123')
        cajero.save()
        print(f"✅ Cajero creado: {cajero.get_full_name()}")
    else:
        print(f"📋 Cajero ya existe: {cajero.get_full_name()}")
    
    # Crear hijos de ejemplo
    hijos_data = [
        {
            'nombre_completo': 'María Pérez',
            'fecha_nacimiento': date(2010, 3, 15),
            'grado': '7mo',
            'seccion': 'A',
            'saldo_virtual': Decimal('150.00'),
        },
        {
            'nombre_completo': 'Carlos Pérez',
            'fecha_nacimiento': date(2012, 8, 22),
            'grado': '5to',
            'seccion': 'B',
            'saldo_virtual': Decimal('100.00'),
        },
        {
            'nombre_completo': 'Ana Pérez',
            'fecha_nacimiento': date(2014, 11, 5),
            'grado': '3ro',
            'seccion': 'A',
            'saldo_virtual': Decimal('75.00'),
        }
    ]
    
    for hijo_data in hijos_data:
        hijo, created = PerfilHijo.objects.get_or_create(
            padre=padre,
            nombre_completo=hijo_data['nombre_completo'],
            defaults=hijo_data
        )
        
        if created:
            # Asignar tarjeta automáticamente
            hijo.asignar_tarjeta()
            print(f"✅ Hijo creado: {hijo.nombre_completo}")
            print(f"   📱 Tarjeta asignada: {hijo.numero_tarjeta_formateado}")
            print(f"   💰 Saldo inicial: Bs. {hijo.saldo_virtual}")
        else:
            # Verificar si tiene tarjeta, si no asignar una
            if not hijo.numero_tarjeta:
                hijo.asignar_tarjeta()
                print(f"📋 Hijo ya existe: {hijo.nombre_completo}")
                print(f"   📱 Nueva tarjeta asignada: {hijo.numero_tarjeta_formateado}")
            else:
                print(f"📋 Hijo ya existe: {hijo.nombre_completo}")
                print(f"   📱 Tarjeta existente: {hijo.numero_tarjeta_formateado}")
    
    print("\n🎉 Datos de prueba creados exitosamente!")
    print("\n📋 Credenciales de acceso:")
    print(f"   👤 Usuario: {padre.username}")
    print(f"   🔑 Contraseña: password123")
    print("\n🌐 Puedes acceder a:")
    print("   🏠 Sistema principal: http://localhost:8001/")
    print("   ⚙️  Panel de admin: http://localhost:8001/admin/")
    print(f"   👨‍👩‍👧‍👦 Gestión de hijos: http://localhost:8001/usuarios/mis_hijos/")
    print("   🏪 Punto de Venta (POS): http://localhost:8001/ventas/pos/")
    print("\n👥 Usuarios adicionales:")
    print("   👩‍💼 Cajero: maria_cajera / password: cajero123")

if __name__ == "__main__":
    crear_datos_prueba()