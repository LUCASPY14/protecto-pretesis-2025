from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db import models
from usuarios.models import PerfilHijo
from .models import Venta, DetalleVenta, PuntoVenta, PagoVenta, MetodoPago
from productos.models import Producto
from decimal import Decimal
import json

@csrf_exempt
@login_required
def buscar_tarjeta_ajax(request):
    """Buscar tarjetas virtuales con resultados múltiples"""
    if request.method == 'POST':
        data = json.loads(request.body)
        busqueda = data.get('busqueda', '').strip()
        
        if len(busqueda) < 2:
            return JsonResponse({'success': True, 'tarjetas': []})
        
        try:
            # Buscar por número de tarjeta o nombre del hijo
            hijos = PerfilHijo.objects.select_related('padre').filter(
                models.Q(numero_tarjeta__icontains=busqueda) |
                models.Q(nombre_completo__icontains=busqueda),
                tarjeta_activa=True,
                numero_tarjeta__isnull=False
            )[:10]  # Limitar a 10 resultados
            
            tarjetas = []
            for hijo in hijos:
                tarjetas.append({
                    'id': hijo.id,
                    'numeroTarjeta': hijo.numero_tarjeta,
                    'nombreHijo': hijo.nombre_completo.upper(),
                    'nombrePadre': hijo.padre.get_full_name() or hijo.padre.username,
                    'saldoDisponible': float(hijo.saldo_virtual),
                    'activa': hijo.tarjeta_activa
                })
            
            return JsonResponse({
                'success': True,
                'tarjetas': tarjetas
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@login_required
def seleccionar_tarjeta_ajax(request):
    """Seleccionar una tarjeta específica por ID"""
    if request.method == 'POST':
        data = json.loads(request.body)
        hijo_id = data.get('hijo_id')
        
        if not hijo_id:
            return JsonResponse({'error': 'ID de hijo requerido'}, status=400)
        
        try:
            hijo = PerfilHijo.objects.select_related('padre').get(
                id=hijo_id,
                tarjeta_activa=True,
                numero_tarjeta__isnull=False
            )
            
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
            
        except PerfilHijo.DoesNotExist:
            return JsonResponse({'error': 'Tarjeta no encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@login_required
def buscar_producto_ajax(request):
    """Buscar productos por código o descripción"""
    if request.method == 'POST':
        data = json.loads(request.body)
        busqueda = data.get('busqueda', '').strip()
        
        if len(busqueda) < 2:
            return JsonResponse({'success': True, 'productos': []})
        
        try:
            # Buscar por código o nombre
            productos = Producto.objects.filter(
                models.Q(codigo__icontains=busqueda) |
                models.Q(nombre__icontains=busqueda),
                disponible=True
            )[:15]  # Limitar a 15 resultados
            
            productos_list = []
            for producto in productos:
                stock_info = ""
                if producto.requiere_stock:
                    if producto.stock_actual <= 0:
                        stock_info = " (SIN STOCK)"
                    elif producto.stock_actual <= producto.stock_minimo:
                        stock_info = f" (Stock: {producto.stock_actual} - BAJO)"
                    else:
                        stock_info = f" (Stock: {producto.stock_actual})"
                else:
                    stock_info = " (Ilimitado)"
                
                productos_list.append({
                    'id': producto.id,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'descripcion': f"{producto.codigo} - {producto.nombre}{stock_info}",
                    'precio': float(producto.precio_venta),
                    'stock': producto.stock_actual,
                    'requiere_stock': producto.requiere_stock,
                    'disponible': producto.stock_actual > 0 if producto.requiere_stock else True
                })
            
            return JsonResponse({
                'success': True,
                'productos': productos_list
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@login_required
def seleccionar_producto_ajax(request):
    """Obtener información completa de un producto específico"""
    if request.method == 'POST':
        data = json.loads(request.body)
        producto_id = data.get('producto_id')
        
        if not producto_id:
            return JsonResponse({'error': 'ID de producto requerido'}, status=400)
        
        try:
            producto = Producto.objects.get(id=producto_id, disponible=True)
            
            if producto.requiere_stock and producto.stock_actual <= 0:
                return JsonResponse({'error': 'Producto sin stock disponible'}, status=400)
            
            return JsonResponse({
                'success': True,
                'producto': {
                    'id': producto.id,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'precio': float(producto.precio_venta),
                    'stock': producto.stock_actual,
                    'requiere_stock': producto.requiere_stock
                }
            })
            
        except Producto.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
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
                    
                    if producto.requiere_stock and producto.stock_actual < cantidad:
                        return JsonResponse({
                            'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}'
                        }, status=400)
                    
                    subtotal = producto.precio_venta * cantidad
                    total_venta += subtotal
                    
                    items_validados.append({
                        'producto': producto,
                        'cantidad': cantidad,
                        'precio_unitario': producto.precio_venta,
                        'subtotal': subtotal
                    })
                
                # Validar saldo suficiente
                if hijo.saldo_virtual < total_venta:
                    return JsonResponse({
                        'error': f'Saldo insuficiente. Disponible: {hijo.saldo_virtual}, Requerido: {total_venta}'
                    }, status=400)
                
                # Obtener punto de venta
                punto_venta = PuntoVenta.objects.filter(activo=True).first()
                if not punto_venta:
                    return JsonResponse({'error': 'No hay puntos de venta activos'}, status=500)
                
                # Crear venta
                venta = Venta.objects.create(
                    punto_venta=punto_venta,
                    hijo=hijo,
                    total=total_venta,
                    cajero=request.user,
                    observaciones='Pago 100% saldo virtual - Sin factura adicional',
                    estado='pagada'
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
                    if item['producto'].requiere_stock:
                        item['producto'].stock_actual -= item['cantidad']
                        item['producto'].save()
                
                # Registrar pago con saldo virtual
                metodo_saldo = MetodoPago.objects.filter(codigo='saldo_virtual').first()
                if not metodo_saldo:
                    # Crear el método de pago saldo virtual si no existe
                    metodo_saldo = MetodoPago.objects.create(
                        codigo='saldo_virtual',
                        nombre='Saldo Virtual',
                        genera_factura=False,
                        activo=True
                    )
                
                PagoVenta.objects.create(
                    venta=venta,
                    metodo_pago=metodo_saldo,
                    monto=total_venta
                )
                
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
                    
                    if producto.requiere_stock and producto.stock_actual < cantidad:
                        return JsonResponse({
                            'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}'
                        }, status=400)
                    
                    subtotal = producto.precio_venta * cantidad
                    total_venta += subtotal
                    
                    items_validados.append({
                        'producto': producto,
                        'cantidad': cantidad,
                        'precio_unitario': producto.precio_venta,
                        'subtotal': subtotal
                    })
                
                # Validar montos
                monto_saldo_virtual = hijo.saldo_virtual
                vuelto = Decimal('0')
                
                # Si es pago en efectivo, manejar vuelto
                if forma_pago_adicional == 'efectivo':
                    monto_efectivo_recibido = Decimal(str(data.get('monto_efectivo_recibido', monto_adicional)))
                    if monto_efectivo_recibido < monto_adicional:
                        return JsonResponse({'error': 'Monto en efectivo insuficiente'}, status=400)
                    vuelto = monto_efectivo_recibido - monto_adicional
                elif monto_saldo_virtual + monto_adicional != total_venta:
                    return JsonResponse({'error': 'Los montos no coinciden con el total'}, status=400)
                
                # Obtener punto de venta
                punto_venta = PuntoVenta.objects.filter(activo=True).first()
                if not punto_venta:
                    return JsonResponse({'error': 'No hay puntos de venta activos'}, status=500)
                
                # Crear venta
                venta = Venta.objects.create(
                    punto_venta=punto_venta,
                    hijo=hijo,
                    total=total_venta,
                    cajero=request.user,
                    observaciones=f'Pago mixto: Saldo virtual Gs. {monto_saldo_virtual:,.0f} + {forma_pago_adicional} Gs. {monto_adicional:,.0f}',
                    estado='pagada'
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
                    if item['producto'].requiere_stock:
                        item['producto'].stock_actual -= item['cantidad']
                        item['producto'].save()
                
                # Registrar pago con saldo virtual
                metodo_saldo = MetodoPago.objects.filter(codigo='saldo_virtual').first()
                if not metodo_saldo:
                    # Crear el método de pago saldo virtual si no existe
                    metodo_saldo = MetodoPago.objects.create(
                        codigo='saldo_virtual',
                        nombre='Saldo Virtual',
                        genera_factura=False,
                        activo=True
                    )
                
                PagoVenta.objects.create(
                    venta=venta,
                    metodo_pago=metodo_saldo,
                    monto=monto_saldo_virtual
                )
                
                # Registrar pago adicional
                metodo_adicional = MetodoPago.objects.filter(codigo=forma_pago_adicional).first()
                if not metodo_adicional:
                    return JsonResponse({'error': f'Método de pago no válido: {forma_pago_adicional}'}, status=400)
                
                PagoVenta.objects.create(
                    venta=venta,
                    metodo_pago=metodo_adicional,
                    monto=monto_adicional
                )
                
                # Usar todo el saldo disponible
                hijo.saldo_virtual = Decimal('0')
                hijo.save()
                
                response_data = {
                    'success': True,
                    'venta_id': venta.id,
                    'mensaje': f'Venta mixta procesada. Se facturará: Gs. {monto_adicional:,.0f}',
                    'nuevo_saldo': float(hijo.saldo_virtual),
                    'facturar_monto': float(monto_adicional),
                    'forma_pago_facturada': forma_pago_adicional
                }
                
                # Agregar información del vuelto si aplica
                if vuelto > 0:
                    response_data['vuelto'] = float(vuelto)
                    response_data['mensaje'] += f' - Vuelto: Gs. {vuelto:,.0f}'
                
                return JsonResponse(response_data)
                
        except Exception as e:
            return JsonResponse({'error': f'Error procesando venta mixta: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@login_required
def procesar_venta_efectivo(request):
    """Procesar venta únicamente en efectivo con cálculo de vuelto"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            with transaction.atomic():
                hijo_id = data.get('hijo_id')
                items = data.get('items', [])
                monto_efectivo_recibido = Decimal(str(data.get('monto_efectivo_recibido', 0)))
                
                if not all([hijo_id, items, monto_efectivo_recibido]):
                    return JsonResponse({'error': 'Datos incompletos'}, status=400)
                
                # Obtener hijo
                hijo = get_object_or_404(PerfilHijo, id=hijo_id)
                
                # Calcular total y validar stock
                total_venta = Decimal('0')
                items_validados = []
                
                for item in items:
                    producto = get_object_or_404(Producto, id=item['producto_id'])
                    cantidad = int(item['cantidad'])
                    
                    if producto.requiere_stock and producto.stock_actual < cantidad:
                        return JsonResponse({
                            'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}'
                        }, status=400)
                    
                    subtotal = producto.precio_venta * cantidad
                    total_venta += subtotal
                    
                    items_validados.append({
                        'producto': producto,
                        'cantidad': cantidad,
                        'precio_unitario': producto.precio_venta,
                        'subtotal': subtotal
                    })
                
                # Validar monto efectivo
                if monto_efectivo_recibido < total_venta:
                    return JsonResponse({'error': 'Monto en efectivo insuficiente'}, status=400)
                
                vuelto = monto_efectivo_recibido - total_venta
                
                # Obtener punto de venta
                punto_venta = PuntoVenta.objects.filter(activo=True).first()
                if not punto_venta:
                    return JsonResponse({'error': 'No hay puntos de venta activos'}, status=500)
                
                # Crear venta
                observacion = f'Pago 100% efectivo - Recibido: Gs. {monto_efectivo_recibido:,.0f}'
                if vuelto > 0:
                    observacion += f' - Vuelto: Gs. {vuelto:,.0f}'
                
                venta = Venta.objects.create(
                    punto_venta=punto_venta,
                    hijo=hijo,
                    total=total_venta,
                    cajero=request.user,
                    observaciones=observacion,
                    estado='pagada'
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
                    if item['producto'].requiere_stock:
                        item['producto'].stock_actual -= item['cantidad']
                        item['producto'].save()
                
                # Registrar pago en efectivo
                metodo_efectivo = MetodoPago.objects.filter(codigo='efectivo').first()
                if not metodo_efectivo:
                    # Crear el método de pago efectivo si no existe
                    metodo_efectivo = MetodoPago.objects.create(
                        codigo='efectivo',
                        nombre='Efectivo',
                        genera_factura=True,
                        activo=True
                    )
                
                PagoVenta.objects.create(
                    venta=venta,
                    metodo_pago=metodo_efectivo,
                    monto=total_venta
                )
                
                response_data = {
                    'success': True,
                    'venta_id': venta.id,
                    'total_venta': float(total_venta),
                    'monto_recibido': float(monto_efectivo_recibido),
                    'vuelto': float(vuelto),
                    'mensaje': f'Venta procesada exitosamente. Total: Gs. {total_venta:,.0f}'
                }
                
                if vuelto > 0:
                    response_data['mensaje'] += f' - Vuelto: Gs. {vuelto:,.0f}'
                
                return JsonResponse(response_data)
                
        except Exception as e:
            return JsonResponse({'error': f'Error procesando venta: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)