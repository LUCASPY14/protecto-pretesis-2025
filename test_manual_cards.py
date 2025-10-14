#!/usr/bin/env python
"""
Script para probar la funcionalidad de asignación manual de tarjetas
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

def probar_asignacion_manual():
    """Probar la asignación manual de tarjetas"""
    
    # Obtener padre existente
    padre = Usuario.objects.filter(username='juan_perez').first()
    if not padre:
        print("❌ No se encontró el usuario juan_perez. Ejecute create_test_data.py primero")
        return
    
    # Crear un nuevo hijo para probar asignación manual
    hijo_nuevo = PerfilHijo.objects.create(
        padre=padre,
        nombre_completo='Pedro Pérez',
        fecha_nacimiento=date(2016, 5, 10),
        grado='1ro',
        seccion='A',
        saldo_virtual=Decimal('50.00'),
        activo=True
    )
    
    print(f"✅ Hijo creado: {hijo_nuevo.nombre_completo}")
    print(f"   🆔 ID: {hijo_nuevo.pk}")
    print(f"   📱 Tarjeta inicial: {hijo_nuevo.numero_tarjeta or 'Sin tarjeta'}")
    
    # Probar asignación automática
    print("\n🔄 Probando asignación automática...")
    hijo_nuevo.asignar_tarjeta()
    print(f"   📱 Tarjeta asignada: {hijo_nuevo.numero_tarjeta_formateado}")
    print(f"   🔐 Código: {hijo_nuevo.codigo_tarjeta}")
    print(f"   ✅ Estado: {'Activa' if hijo_nuevo.tarjeta_activa else 'Inactiva'}")
    
    # Probar asignación manual
    print("\n🔄 Probando asignación manual...")
    numero_manual = "1234567890123456"
    codigo_manual = "9999"
    
    try:
        hijo_nuevo.asignar_tarjeta(
            numero_manual=numero_manual,
            codigo_manual=codigo_manual
        )
        print(f"   📱 Tarjeta manual asignada: {hijo_nuevo.numero_tarjeta_formateado}")
        print(f"   🔐 Código manual: {hijo_nuevo.codigo_tarjeta}")
        print(f"   ✅ Asignación manual exitosa")
        
    except Exception as e:
        print(f"   ❌ Error en asignación manual: {e}")
    
    # Probar validaciones
    print("\n🔄 Probando validaciones...")
    
    # Número duplicado
    hijo_duplicado = PerfilHijo.objects.create(
        padre=padre,
        nombre_completo='Luisa Pérez',
        fecha_nacimiento=date(2015, 2, 20),
        grado='2do',
        seccion='B',
        saldo_virtual=Decimal('25.00'),
        activo=True
    )
    
    try:
        hijo_duplicado.asignar_tarjeta(numero_manual=numero_manual)
        print("   ❌ ERROR: Debería haber fallado por número duplicado")
    except Exception as e:
        print(f"   ✅ Validación correcta - número duplicado: {e}")
    
    # Número con formato incorrecto
    try:
        hijo_duplicado.asignar_tarjeta(numero_manual="123456")  # Muy corto
        print("   ❌ ERROR: Debería haber fallado por formato incorrecto")
    except Exception as e:
        print(f"   ✅ Validación correcta - formato incorrecto: {e}")
    
    # Asignar tarjeta válida al segundo hijo
    hijo_duplicado.asignar_tarjeta()
    print(f"   📱 Tarjeta automática para {hijo_duplicado.nombre_completo}: {hijo_duplicado.numero_tarjeta_formateado}")
    
    print("\n🎉 Pruebas completadas exitosamente!")
    print("\n📋 Resumen de hijos con tarjetas:")
    
    hijos = PerfilHijo.objects.filter(padre=padre).order_by('nombre_completo')
    for hijo in hijos:
        print(f"   👶 {hijo.nombre_completo}:")
        print(f"      📱 Tarjeta: {hijo.numero_tarjeta_formateado or 'Sin tarjeta'}")
        print(f"      💰 Saldo: Bs. {hijo.saldo_virtual}")
        print(f"      ✅ Estado: {'Activa' if hijo.tarjeta_activa else 'Inactiva'}")
        print()

if __name__ == "__main__":
    probar_asignacion_manual()