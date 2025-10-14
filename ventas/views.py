from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json

from .models import Venta, DetalleVenta, MetodoPago, PuntoVenta, Factura, PagoVenta
from productos.models import Producto
from usuarios.models import PerfilHijo, TransaccionTarjeta

@login_required
def pos_dashboard(request):
    """Vista para el dashboard del punto de venta con tarjetas virtuales"""
    context = {
        'titulo': 'Punto de Venta - La Cantina de Tita',
    }
    
    return render(request, 'ventas/pos_tarjetas_virtuales_ultracompact.html', context)

@login_required
def pos_dashboard_simple(request):
    """Vista simple del POS para depuración"""
    context = {
        'titulo': 'POS Simple - Test',
        'productos': Producto.objects.filter(disponible=True).select_related('categoria'),
    }
    
    return render(request, 'ventas/pos_simple.html', context)

@login_required
def pos_dashboard_test(request):
    """Vista de prueba intermedia del POS"""
    context = {
        'titulo': 'POS Test - Intermedio',
        'productos': Producto.objects.filter(disponible=True).select_related('categoria')[:10],
    }
    
    return render(request, 'ventas/pos_dashboard_test.html', context)

@login_required
def pos_dashboard_debug(request):
    """Vista de debug del POS"""
    context = {
        'titulo': 'POS Debug',
        'productos': Producto.objects.filter(disponible=True).select_related('categoria'),
        'metodos_pago': MetodoPago.objects.filter(activo=True),
        'user': request.user,
    }
    
    return render(request, 'ventas/pos_dashboard_debug.html', context)

@csrf_exempt
@login_required
def buscar_producto(request):
    """Buscar productos por código o nombre"""
    if request.method == 'POST':
        data = json.loads(request.body)
        termino = data.get('termino', '').strip()
        
        if not termino:
            return JsonResponse({'error': 'Debe proporcionar un término de búsqueda'})
        
        # Buscar por código exacto primero
        producto = Producto.objects.filter(codigo=termino, disponible=True).first()
        
        if not producto:
            # Buscar por nombre parcial
            productos = Producto.objects.filter(
                nombre__icontains=termino,
                disponible=True
            )[:10]  # Limitar a 10 resultados
            
            if productos.count() == 1:
                producto = productos.first()
            elif productos.count() > 1:
                return JsonResponse({
                    'multiple': True,
                    'productos': [{
                        'id': p.id,
                        'codigo': p.codigo,
                        'nombre': p.nombre,
                        'precio': str(p.precio_venta),
                        'stock': p.stock_actual
                    } for p in productos]
                })
            else:
                return JsonResponse({'error': 'Producto no encontrado'})
        
        if producto:
            return JsonResponse({
                'success': True,
                'producto': {
                    'id': producto.id,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'precio': str(producto.precio_venta),
                    'stock': producto.stock_actual,
                    'categoria': producto.categoria.nombre
                }
            })
    
    return JsonResponse({'error': 'Método no permitido'})

@csrf_exempt
@login_required
def buscar_tarjeta(request):
    """Buscar hijo por número de tarjeta"""
    if request.method == 'POST':
        data = json.loads(request.body)
        numero_tarjeta = data.get('numero_tarjeta', '').strip().replace('-', '').replace(' ', '')
        
        if not numero_tarjeta:
            return JsonResponse({'error': 'Debe proporcionar un número de tarjeta'})
        
        try:
            hijo = PerfilHijo.objects.get(
                numero_tarjeta=numero_tarjeta,
                tarjeta_activa=True,
                activo=True
            )
            
            return JsonResponse({
                'success': True,
                'hijo': {
                    'id': hijo.id,
                    'nombre': hijo.nombre_completo,
                    'grado': hijo.grado,
                    'seccion': hijo.seccion or '',
                    'saldo': str(hijo.saldo_virtual),
                    'saldo_disponible': str(hijo.saldo_disponible),
                    'tarjeta': hijo.numero_tarjeta_formateado,
                    'padre': hijo.padre.get_full_name()
                }
            })
            
        except PerfilHijo.DoesNotExist:
            return JsonResponse({'error': 'Tarjeta no encontrada o inactiva'})
    
    return JsonResponse({'error': 'Método no permitido'})

@csrf_exempt
@login_required
def procesar_venta(request):
    """Procesar una venta completa"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar datos requeridos
            items = data.get('items', [])
            metodos_pago = data.get('metodos_pago', [])
            hijo_id = data.get('hijo_id')
            cliente_nombre = data.get('cliente_nombre', '')
            
            if not items:
                return JsonResponse({'error': 'No hay productos en la venta'})
            
            if not metodos_pago:
                return JsonResponse({'error': 'Debe especificar un método de pago'})
            
            # Obtener punto de venta
            punto_venta = PuntoVenta.objects.filter(cajero_actual=request.user).first()
            if not punto_venta:
                return JsonResponse({'error': 'No hay punto de venta asignado'})
            
            with transaction.atomic():
                # Crear la venta
                venta = Venta.objects.create(
                    punto_venta=punto_venta,
                    cajero=request.user,
                    hijo_id=hijo_id if hijo_id else None,
                    cliente_nombre=cliente_nombre,
                    fecha_venta=timezone.now(),
                    estado='pendiente'
                )
                
                # Generar número de venta
                venta.numero_venta = f"V{venta.id:06d}"
                
                subtotal = Decimal('0.00')
                
                # Procesar items
                for item in items:
                    producto = get_object_or_404(Producto, id=item['producto_id'])
                    cantidad = Decimal(str(item['cantidad']))
                    precio = Decimal(str(item['precio']))
                    
                    # Verificar stock
                    if producto.stock_actual < cantidad:
                        return JsonResponse({'error': f'Stock insuficiente para {producto.nombre}'})
                    
                    # Crear detalle de venta
                    detalle = DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=cantidad * precio
                    )
                    
                    subtotal += detalle.subtotal
                    
                    # Actualizar stock
                    producto.stock_actual -= cantidad
                    producto.save()
                
                # Calcular totales
                venta.subtotal = subtotal
                venta.total = subtotal  # Sin impuestos por ahora
                
                # Procesar pagos
                total_pagado = Decimal('0.00')
                
                for pago_data in metodos_pago:
                    metodo = get_object_or_404(MetodoPago, id=pago_data['metodo_id'])
                    monto = Decimal(str(pago_data['monto']))
                    
                    # Validar pago con tarjeta (saldo virtual)
                    if metodo.codigo == 'TARJETA' and hijo_id:
                        hijo = get_object_or_404(PerfilHijo, id=hijo_id)
                        puede_comprar, mensaje = hijo.puede_realizar_compra(monto)
                        
                        if not puede_comprar:
                            return JsonResponse({'error': mensaje})
                        
                        # Descontar saldo
                        saldo_anterior = hijo.saldo_virtual
                        hijo.saldo_virtual -= monto
                        hijo.save()
                        
                        # Registrar transacción
                        TransaccionTarjeta.objects.create(
                            hijo=hijo,
                            numero_tarjeta_utilizada=hijo.numero_tarjeta,
                            tipo_transaccion='compra',
                            monto=-monto,
                            saldo_anterior=saldo_anterior,
                            saldo_posterior=hijo.saldo_virtual,
                            estado='exitosa',
                            realizada_por=request.user,
                            punto_venta=punto_venta.codigo,
                            observaciones=f'Compra en POS - Venta #{venta.numero_venta}'
                        )
                    
                    # Crear registro de pago
                    PagoVenta.objects.create(
                        venta=venta,
                        metodo_pago=metodo,
                        monto=monto,
                        referencia=pago_data.get('referencia', '')
                    )
                    
                    total_pagado += monto
                
                # Validar que el total pagado coincida
                if total_pagado != venta.total:
                    return JsonResponse({'error': 'El monto pagado no coincide con el total'})
                
                # Marcar venta como pagada
                venta.estado = 'pagada'
                venta.save()
                
                # Verificar si se debe generar factura
                generar_factura_flag = data.get('generar_factura', False)
                factura_id = None
                numero_factura = None
                
                if generar_factura_flag:
                    try:
                        # Crear factura automáticamente
                        from facturacion.models import ConfiguracionFacturacion
                        
                        config = ConfiguracionFacturacion.objects.first()
                        if not config:
                            # Crear configuración básica si no existe
                            config = ConfiguracionFacturacion.objects.create(
                                empresa_nombre="La Cantina de Cantina",
                                empresa_direccion="Dirección de la empresa",
                                empresa_telefono="123-456-7890",
                                empresa_email="info@lacantina.com"
                            )
                        
                        # Crear la factura
                        factura = Factura.objects.create(
                            venta=venta,
                            cliente_nombre=cliente_nombre or 'Cliente General',
                            subtotal_factura=venta.subtotal,
                            impuesto_factura=venta.subtotal * Decimal('0.21'),  # IVA 21%
                            total_factura=venta.total,
                            estado='emitida',
                            usuario_creacion=request.user
                        )
                        
                        factura_id = factura.id
                        numero_factura = factura.numero
                        
                    except Exception as e:
                        # Si hay error en facturación, no fallar la venta
                        pass
                
                return JsonResponse({
                    'success': True,
                    'venta_id': venta.id,
                    'numero_venta': venta.numero_venta,
                    'total': str(venta.total),
                    'factura_id': factura_id,
                    'numero_factura': numero_factura
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Error procesando venta: {str(e)}'})
    
    return JsonResponse({'error': 'Método no permitido'})

# Vistas básicas de compatibilidad
@login_required
def lista_ventas(request):
    """Lista de ventas realizadas"""
    ventas = Venta.objects.select_related('punto_venta', 'cajero', 'hijo').order_by('-fecha_venta')[:50]
    context = {
        'titulo': 'Lista de Ventas',
        'ventas': ventas
    }
    return render(request, 'ventas/lista_ventas.html', context)

@login_required
def nueva_venta(request):
    """Redireccionar al POS"""
    return redirect('ventas:pos_dashboard')

@login_required
def detalle_venta(request, pk):
    """Detalle de una venta específica"""
    venta = get_object_or_404(Venta, pk=pk)
    context = {
        'titulo': f'Venta #{venta.numero_venta}',
        'venta': venta
    }
    return render(request, 'ventas/detalle_venta.html', context)

@login_required
def generar_factura(request, pk):
    """Generar factura de una venta"""
    venta = get_object_or_404(Venta, pk=pk)
    
    try:
        # Verificar si ya tiene factura
        if hasattr(venta, 'factura'):
            messages.warning(request, f'Esta venta ya tiene factura: {venta.factura.numero}')
            return redirect('facturacion:detalle_factura', pk=venta.factura.id)
        
        # Crear factura
        from facturacion.models import ConfiguracionFacturacion
        
        config = ConfiguracionFacturacion.objects.first()
        if not config:
            # Crear configuración básica si no existe
            config = ConfiguracionFacturacion.objects.create(
                empresa_nombre="La Cantina de Cantina",
                empresa_direccion="Dirección de la empresa",
                empresa_telefono="123-456-7890",
                empresa_email="info@lacantina.com"
            )
        
        # Crear la factura
        factura = Factura.objects.create(
            venta=venta,
            cliente_nombre=venta.cliente_nombre or 'Cliente General',
            subtotal_factura=venta.subtotal,
            impuesto_factura=venta.subtotal * Decimal('0.21'),  # IVA 21%
            total_factura=venta.total,
            estado='emitida',
            usuario_creacion=request.user
        )
        
        messages.success(request, f'Factura {factura.numero} generada correctamente')
        return redirect('facturacion:detalle_factura', pk=factura.id)
        
    except Exception as e:
        messages.error(request, f'Error al generar factura: {str(e)}')
        return redirect('ventas:detalle_venta', pk=pk)

@login_required
def lista_metodos_pago(request):
    """Lista de métodos de pago"""
    metodos = MetodoPago.objects.all().order_by('orden')
    context = {
        'titulo': 'Métodos de Pago',
        'metodos': metodos
    }
    return render(request, 'ventas/lista_metodos_pago.html', context)

@login_required
def lista_puntos_venta(request):
    """Lista de puntos de venta"""
    puntos = PuntoVenta.objects.all().order_by('codigo')
    context = {
        'titulo': 'Puntos de Venta',
        'puntos': puntos
    }
    return render(request, 'ventas/lista_puntos_venta.html', context)

@login_required
def lista_facturas(request):
    """Lista de facturas (funcionalidad en desarrollo)"""
    context = {
        'titulo': 'Lista de Facturas',
        'facturas': []
    }
    return render(request, 'ventas/lista_facturas.html', context)

@login_required
def ver_factura(request, pk):
    """Ver factura (funcionalidad en desarrollo)"""
    messages.info(request, 'Funcionalidad de facturación en desarrollo')
    return redirect('ventas:lista_facturas')
