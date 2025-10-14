from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from usuarios.models import PerfilHijo
from .models import Venta, DetalleVenta
from productos.models import Producto
from decimal import Decimal
import json

@csrf_exempt
@login_required
def buscar_tarjeta_ajax(request):
    """Buscar tarjeta virtual por número o nombre"""
    if request.method == 'POST':
        data = json.loads(request.body)
        busqueda = data.get('busqueda', '').strip()
        
        if not busqueda:
            return JsonResponse({'error': 'Término de búsqueda requerido'}, status=400)
        
        try:
            # Buscar por número de tarjeta o nombre del hijo
            hijo = None
            
            # Primero intentar por número de tarjeta
            if busqueda.isdigit():
                hijo = PerfilHijo.objects.select_related('padre').filter(numero_tarjeta=busqueda).first()
            
            # Si no se encuentra, buscar por nombre
            if not hijo:
                hijo = PerfilHijo.objects.select_related('padre').filter(
                    nombre_completo__icontains=busqueda
                ).first()
            
            if not hijo:
                return JsonResponse({'error': 'Tarjeta no encontrada'}, status=404)
            
            # Verificar que tenga tarjeta asignada
            if not hijo.numero_tarjeta:
                return JsonResponse({'error': 'Este hijo no tiene tarjeta asignada'}, status=400)
            
            return JsonResponse({
                'success': True,
                'tarjeta': {
                    'id': hijo.id,
                    'numeroTarjeta': hijo.numero_tarjeta,
                    'nombreHijo': hijo.nombre_completo.upper(),
                    'nombrePadre': hijo.padre.get_full_name() or hijo.padre.username,
                    'saldoDisponible': float(hijo.saldo_virtual),
                    'activa': hijo.tarjeta_activa
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@login_required
def buscar_producto_ajax(request):
    """Buscar producto por código"""
    if request.method == 'POST':
        data = json.loads(request.body)
        codigo = data.get('codigo', '').strip()
        
        if not codigo:
            return JsonResponse({'error': 'Código de producto requerido'}, status=400)
        
        try:
            producto = Producto.objects.filter(codigo=codigo, disponible=True).first()
            
            if not producto:
                return JsonResponse({'error': 'Producto no encontrado'}, status=404)
            
            if producto.requiere_stock and producto.stock_actual <= 0:
                return JsonResponse({'error': 'Producto sin stock disponible'}, status=400)
            
            return JsonResponse({
                'success': True,
                'producto': {
                    'id': producto.id,
                    'codigo': producto.codigo,
                    'descripcion': producto.nombre,
                    'precio': float(producto.precio_venta),
                    'stock': producto.stock_actual
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@login_required
def procesar_venta_saldo_virtual(request):
    """Procesar venta únicamente con saldo virtual"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            with transaction.atomic():
                hijo_id = data.get('hijo_id')
                items = data.get('items', [])
                
                if not hijo_id or not items:
                    return JsonResponse({'error': 'Datos incompletos'}, status=400)
                
                # Obtener hijo y validar saldo
                hijo = get_object_or_404(PerfilHijo, id=hijo_id)
                
                # Calcular total y validar stock
                total_venta = Decimal('0')
                items_validados = []
                
                for item in items:
                    producto = get_object_or_404(Producto, id=item['producto_id'])
                    cantidad = int(item['cantidad'])
                    
                    if producto.stock < cantidad:
                        return JsonResponse({
                            'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}'
                        }, status=400)
                    
                    subtotal = producto.precio * cantidad
                    total_venta += subtotal
                    
                    items_validados.append({
                        'producto': producto,
                        'cantidad': cantidad,
                        'precio_unitario': producto.precio,
                        'subtotal': subtotal
                    })
                
                # Validar saldo suficiente
                if hijo.saldo_virtual < total_venta:
                    return JsonResponse({
                        'error': f'Saldo insuficiente. Disponible: {hijo.saldo_virtual}, Requerido: {total_venta}'
                    }, status=400)
                
                # Crear venta
                venta = Venta.objects.create(
                    hijo=hijo,
                    total=total_venta,
                    metodo_pago='saldo_virtual',
                    cajero=request.user,
                    observaciones='Pago 100% saldo virtual - Sin factura adicional'
                )
                
                # Crear detalles y actualizar stock
                for item in items_validados:
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=item['producto'],
                        cantidad=item['cantidad'],
                        precio_unitario=item['precio_unitario'],
                        subtotal=item['subtotal']
                    )
                    
                    # Actualizar stock
                    item['producto'].stock -= item['cantidad']
                    item['producto'].save()
                
                # Descontar saldo
                hijo.saldo_virtual -= total_venta
                hijo.save()
                
                return JsonResponse({
                    'success': True,
                    'venta_id': venta.id,
                    'mensaje': f'Venta procesada exitosamente. Total: Gs. {total_venta:,.0f}',
                    'nuevo_saldo': float(hijo.saldo_virtual)
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Error procesando venta: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@login_required
def procesar_venta_mixta(request):
    """Procesar venta con saldo virtual + otro método de pago"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            with transaction.atomic():
                hijo_id = data.get('hijo_id')
                items = data.get('items', [])
                forma_pago_adicional = data.get('forma_pago_adicional')
                monto_adicional = Decimal(str(data.get('monto_adicional', 0)))
                
                if not all([hijo_id, items, forma_pago_adicional, monto_adicional]):
                    return JsonResponse({'error': 'Datos incompletos'}, status=400)
                
                # Obtener hijo
                hijo = get_object_or_404(PerfilHijo, id=hijo_id)
                
                # Calcular total y validar stock
                total_venta = Decimal('0')
                items_validados = []
                
                for item in items:
                    producto = get_object_or_404(Producto, id=item['producto_id'])
                    cantidad = int(item['cantidad'])
                    
                    if producto.stock < cantidad:
                        return JsonResponse({
                            'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}'
                        }, status=400)
                    
                    subtotal = producto.precio * cantidad
                    total_venta += subtotal
                    
                    items_validados.append({
                        'producto': producto,
                        'cantidad': cantidad,
                        'precio_unitario': producto.precio,
                        'subtotal': subtotal
                    })
                
                # Validar montos
                monto_saldo_virtual = hijo.saldo_virtual
                if monto_saldo_virtual + monto_adicional != total_venta:
                    return JsonResponse({'error': 'Los montos no coinciden con el total'}, status=400)
                
                # Crear venta
                venta = Venta.objects.create(
                    hijo=hijo,
                    total=total_venta,
                    metodo_pago='mixto',
                    cajero=request.user,
                    observaciones=f'Pago mixto: Saldo virtual Gs. {monto_saldo_virtual:,.0f} + {forma_pago_adicional} Gs. {monto_adicional:,.0f}'
                )
                
                # Crear detalles y actualizar stock
                for item in items_validados:
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=item['producto'],
                        cantidad=item['cantidad'],
                        precio_unitario=item['precio_unitario'],
                        subtotal=item['subtotal']
                    )
                    
                    # Actualizar stock
                    item['producto'].stock -= item['cantidad']
                    item['producto'].save()
                
                # Usar todo el saldo disponible
                hijo.saldo_virtual = Decimal('0')
                hijo.save()
                
                return JsonResponse({
                    'success': True,
                    'venta_id': venta.id,
                    'mensaje': f'Venta mixta procesada. Se facturará: Gs. {monto_adicional:,.0f}',
                    'nuevo_saldo': float(hijo.saldo_virtual),
                    'facturar_monto': float(monto_adicional),
                    'forma_pago_facturada': forma_pago_adicional
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Error procesando venta mixta: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)