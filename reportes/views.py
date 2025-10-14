from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Avg, Q, F, Case, When
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ventas.models import Venta, DetalleVenta, MetodoPago, PagoVenta
from productos.models import Producto, Categoria
from usuarios.models import PerfilHijo, TransaccionTarjeta, RecargaSaldo

@login_required
def lista_reportes(request):
    """Dashboard de reportes con estadísticas generales"""
    # Verificar permisos
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver los reportes')
        return redirect('usuarios:dashboard')
    
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    
    # Estadísticas generales
    stats = {
        'ventas_hoy': Venta.objects.filter(fecha_venta__date=hoy, estado='pagada').count(),
        'ingresos_hoy': Venta.objects.filter(fecha_venta__date=hoy, estado='pagada').aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00'),
        
        'ventas_semana': Venta.objects.filter(fecha_venta__date__gte=hace_7_dias, estado='pagada').count(),
        'ingresos_semana': Venta.objects.filter(fecha_venta__date__gte=hace_7_dias, estado='pagada').aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00'),
        
        'ventas_mes': Venta.objects.filter(fecha_venta__date__gte=hace_30_dias, estado='pagada').count(),
        'ingresos_mes': Venta.objects.filter(fecha_venta__date__gte=hace_30_dias, estado='pagada').aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00'),
        
        'hijos_activos': PerfilHijo.objects.filter(activo=True, tarjeta_activa=True).count(),
        'productos_stock_bajo': Producto.objects.filter(stock_actual__lte=F('stock_minimo'), disponible=True).count(),
        'saldo_total_tarjetas': PerfilHijo.objects.filter(activo=True).aggregate(
            total=Sum('saldo_virtual')
        )['total'] or Decimal('0.00'),
    }
    
    # Productos más vendidos (últimos 30 días)
    productos_top = DetalleVenta.objects.filter(
        venta__fecha_venta__date__gte=hace_30_dias,
        venta__estado='pagada'
    ).values(
        'producto__nombre',
        'producto__categoria__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:5]
    
    # Métodos de pago más usados
    metodos_pago = PagoVenta.objects.filter(
        venta__fecha_venta__date__gte=hace_30_dias,
        venta__estado='pagada'
    ).values(
        'metodo_pago__nombre'
    ).annotate(
        total_transacciones=Count('id'),
        total_monto=Sum('monto')
    ).order_by('-total_transacciones')
    
    context = {
        'titulo': 'Dashboard de Reportes',
        'stats': stats,
        'productos_top': productos_top,
        'metodos_pago': metodos_pago,
    }
    
    return render(request, 'reportes/lista_reportes.html', context)

@login_required
def reporte_consumo_hijo(request):
    """Reporte detallado de consumo por hijo"""
    if request.user.tipo_usuario not in ['administrador', 'cajero', 'padre']:
        messages.error(request, 'No tienes permisos para ver este reporte')
        return redirect('usuarios:dashboard')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    hijo_id = request.GET.get('hijo_id')
    
    # Queryset base según tipo de usuario
    if request.user.tipo_usuario == 'padre':
        hijos = PerfilHijo.objects.filter(padre=request.user, activo=True)
    else:
        hijos = PerfilHijo.objects.filter(activo=True)
    
    # Aplicar filtros de fecha
    ventas_query = Venta.objects.filter(estado='pagada')
    if fecha_desde:
        ventas_query = ventas_query.filter(fecha_venta__date__gte=fecha_desde)
    if fecha_hasta:
        ventas_query = ventas_query.filter(fecha_venta__date__lte=fecha_hasta)
    if hijo_id:
        ventas_query = ventas_query.filter(hijo_id=hijo_id)
    
    # Datos de consumo
    consumo_data = []
    for hijo in hijos:
        ventas_hijo = ventas_query.filter(hijo=hijo)
        
        total_gastado = ventas_hijo.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        num_compras = ventas_hijo.count()
        
        # Productos favoritos
        productos_favoritos = DetalleVenta.objects.filter(
            venta__in=ventas_hijo
        ).values(
            'producto__nombre'
        ).annotate(
            cantidad_total=Sum('cantidad')
        ).order_by('-cantidad_total')[:3]
        
        # Transacciones de tarjeta
        transacciones = TransaccionTarjeta.objects.filter(
            hijo=hijo,
            tipo_transaccion='compra'
        )
        if fecha_desde:
            transacciones = transacciones.filter(fecha_transaccion__date__gte=fecha_desde)
        if fecha_hasta:
            transacciones = transacciones.filter(fecha_transaccion__date__lte=fecha_hasta)
        
        consumo_data.append({
            'hijo': hijo,
            'total_gastado': total_gastado,
            'num_compras': num_compras,
            'promedio_por_compra': total_gastado / num_compras if num_compras > 0 else Decimal('0.00'),
            'productos_favoritos': productos_favoritos,
            'saldo_actual': hijo.saldo_virtual,
            'transacciones_tarjeta': transacciones.count()
        })
    
    context = {
        'titulo': 'Reporte de Consumo por Hijo',
        'consumo_data': consumo_data,
        'hijos': hijos,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'hijo_id': int(hijo_id) if hijo_id else None,
    }
    
    return render(request, 'reportes/reporte_consumo_hijo.html', context)

@login_required
def reporte_productos_mas_vendidos(request):
    """Reporte de productos más vendidos con análisis detallado"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver este reporte')
        return redirect('usuarios:dashboard')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    categoria_id = request.GET.get('categoria_id')
    
    # Queryset base
    detalles_query = DetalleVenta.objects.filter(venta__estado='pagada')
    
    # Aplicar filtros
    if fecha_desde:
        detalles_query = detalles_query.filter(venta__fecha_venta__date__gte=fecha_desde)
    if fecha_hasta:
        detalles_query = detalles_query.filter(venta__fecha_venta__date__lte=fecha_hasta)
    if categoria_id:
        detalles_query = detalles_query.filter(producto__categoria_id=categoria_id)
    
    # Productos más vendidos
    productos_vendidos = detalles_query.values(
        'producto__id',
        'producto__nombre',
        'producto__categoria__nombre',
        'producto__precio_venta'
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario')),
        num_transacciones=Count('venta', distinct=True)
    ).order_by('-cantidad_vendida')
    
    # Análisis por categorías
    categorias_analysis = detalles_query.values(
        'producto__categoria__nombre'
    ).annotate(
        total_productos=Count('producto', distinct=True),
        cantidad_vendida=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_ingresos')
    
    # Tendencias de venta (últimos 7 días)
    hace_7_dias = timezone.now().date() - timedelta(days=7)
    tendencias = []
    for i in range(7):
        fecha = hace_7_dias + timedelta(days=i)
        ventas_dia = DetalleVenta.objects.filter(
            venta__fecha_venta__date=fecha,
            venta__estado='pagada'
        ).aggregate(
            total_items=Sum('cantidad'),
            total_ingresos=Sum(F('cantidad') * F('precio_unitario'))
        )
        
        tendencias.append({
            'fecha': fecha,
            'total_items': ventas_dia['total_items'] or 0,
            'total_ingresos': ventas_dia['total_ingresos'] or Decimal('0.00')
        })
    
    context = {
        'titulo': 'Reporte de Productos Más Vendidos',
        'productos_vendidos': productos_vendidos,
        'categorias_analysis': categorias_analysis,
        'tendencias': tendencias,
        'categorias': Categoria.objects.filter(activo=True),
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'categoria_id': int(categoria_id) if categoria_id else None,
    }
    
    return render(request, 'reportes/reporte_productos_mas_vendidos.html', context)

@login_required
def reporte_ingresos_metodo_pago(request):
    """Análisis detallado de ingresos por método de pago"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver este reporte')
        return redirect('usuarios:dashboard')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Queryset base
    pagos_query = PagoVenta.objects.filter(venta__estado='pagada')
    
    # Aplicar filtros
    if fecha_desde:
        pagos_query = pagos_query.filter(venta__fecha_venta__date__gte=fecha_desde)
    if fecha_hasta:
        pagos_query = pagos_query.filter(venta__fecha_venta__date__lte=fecha_hasta)
    
    # Análisis por método de pago
    metodos_analysis = pagos_query.values(
        'metodo_pago__nombre',
        'metodo_pago__codigo'
    ).annotate(
        total_transacciones=Count('id'),
        total_monto=Sum('monto'),
        promedio_transaccion=Avg('monto')
    ).order_by('-total_monto')
    
    # Análisis de uso de tarjetas exclusivas
    transacciones_tarjeta = TransaccionTarjeta.objects.filter(
        tipo_transaccion='compra',
        estado='exitosa'
    )
    if fecha_desde:
        transacciones_tarjeta = transacciones_tarjeta.filter(fecha_transaccion__date__gte=fecha_desde)
    if fecha_hasta:
        transacciones_tarjeta = transacciones_tarjeta.filter(fecha_transaccion__date__lte=fecha_hasta)
    
    tarjeta_stats = {
        'total_transacciones': transacciones_tarjeta.count(),
        'total_monto': transacciones_tarjeta.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00'),
        'hijos_activos': transacciones_tarjeta.values('hijo').distinct().count(),
        'promedio_por_hijo': 0
    }
    
    if tarjeta_stats['hijos_activos'] > 0:
        tarjeta_stats['promedio_por_hijo'] = abs(tarjeta_stats['total_monto']) / tarjeta_stats['hijos_activos']
    
    # Comparación semanal
    hace_14_dias = timezone.now().date() - timedelta(days=14)
    hace_7_dias = timezone.now().date() - timedelta(days=7)
    hoy = timezone.now().date()
    
    semana_pasada = PagoVenta.objects.filter(
        venta__fecha_venta__date__gte=hace_14_dias,
        venta__fecha_venta__date__lt=hace_7_dias,
        venta__estado='pagada'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    semana_actual = PagoVenta.objects.filter(
        venta__fecha_venta__date__gte=hace_7_dias,
        venta__fecha_venta__date__lte=hoy,
        venta__estado='pagada'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    crecimiento = 0
    if semana_pasada > 0:
        crecimiento = ((semana_actual - semana_pasada) / semana_pasada) * 100
    
    context = {
        'titulo': 'Reporte de Ingresos por Método de Pago',
        'metodos_analysis': metodos_analysis,
        'tarjeta_stats': tarjeta_stats,
        'semana_pasada': semana_pasada,
        'semana_actual': semana_actual,
        'crecimiento': crecimiento,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'reportes/reporte_ingresos_metodo_pago.html', context)

@login_required
def reporte_ventas_diarias(request):
    """Reporte de ventas diarias con tendencias"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver este reporte')
        return redirect('usuarios:dashboard')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Fechas por defecto (últimos 30 días)
    if not fecha_desde:
        fecha_desde = (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = timezone.now().date().strftime('%Y-%m-%d')
    
    # Ventas por día
    ventas_diarias = Venta.objects.filter(
        fecha_venta__date__gte=fecha_desde,
        fecha_venta__date__lte=fecha_hasta,
        estado='pagada'
    ).extra(
        select={'fecha': 'DATE(fecha_venta)'}
    ).values('fecha').annotate(
        num_ventas=Count('id'),
        total_ingresos=Sum('total'),
        num_items=Sum('detalleventa__cantidad')
    ).order_by('fecha')
    
    # Estadísticas del período
    total_ventas = sum(dia['num_ventas'] for dia in ventas_diarias)
    total_ingresos = sum(dia['total_ingresos'] for dia in ventas_diarias)
    total_items = sum(dia['num_items'] for dia in ventas_diarias)
    
    promedio_ventas_dia = total_ventas / len(ventas_diarias) if ventas_diarias else 0
    promedio_ingresos_dia = total_ingresos / len(ventas_diarias) if ventas_diarias else 0
    
    # Mejor y peor día
    mejor_dia = max(ventas_diarias, key=lambda x: x['total_ingresos']) if ventas_diarias else None
    peor_dia = min(ventas_diarias, key=lambda x: x['total_ingresos']) if ventas_diarias else None
    
    context = {
        'titulo': 'Reporte de Ventas Diarias',
        'ventas_diarias': list(ventas_diarias),
        'total_ventas': total_ventas,
        'total_ingresos': total_ingresos,
        'total_items': total_items,
        'promedio_ventas_dia': promedio_ventas_dia,
        'promedio_ingresos_dia': promedio_ingresos_dia,
        'mejor_dia': mejor_dia,
        'peor_dia': peor_dia,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'reportes/reporte_ventas_diarias.html', context)

@login_required
def reporte_stock_productos(request):
    """Reporte completo de inventario y stock"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver este reporte')
        return redirect('usuarios:dashboard')
    
    # Productos con stock bajo
    productos_stock_bajo = Producto.objects.filter(
        stock_actual__lte=F('stock_minimo'),
        disponible=True
    ).select_related('categoria')
    
    # Productos sin stock
    productos_sin_stock = Producto.objects.filter(
        stock_actual=0,
        disponible=True
    ).select_related('categoria')
    
    # Resumen por categoría
    categorias_stock = Categoria.objects.filter(
        activo=True
    ).annotate(
        total_productos=Count('productos', filter=Q(productos__disponible=True)),
        productos_stock_bajo=Count('productos', filter=Q(
            productos__disponible=True,
            productos__stock_actual__lte=F('productos__stock_minimo')
        )),
        productos_sin_stock=Count('productos', filter=Q(
            productos__disponible=True,
            productos__stock_actual=0
        )),
        valor_inventario=Sum(F('productos__stock_actual') * F('productos__precio_costo'), filter=Q(productos__disponible=True))
    )
    
    # Productos más críticos (ordenados por prioridad)
    productos_criticos = Producto.objects.filter(
        disponible=True
    ).annotate(
        porcentaje_stock=Case(
            When(stock_minimo=0, then=100),
            default=F('stock_actual') * 100 / F('stock_minimo')
        )
    ).filter(porcentaje_stock__lte=100).order_by('porcentaje_stock')[:10]
    
    # Valor total del inventario
    valor_total_inventario = Producto.objects.filter(
        disponible=True
    ).aggregate(
        total=Sum(F('stock_actual') * F('precio_costo'))
    )['total'] or Decimal('0.00')
    
    context = {
        'titulo': 'Reporte de Stock e Inventario',
        'productos_stock_bajo': productos_stock_bajo,
        'productos_sin_stock': productos_sin_stock,
        'categorias_stock': categorias_stock,
        'productos_criticos': productos_criticos,
        'valor_total_inventario': valor_total_inventario,
        'total_productos_activos': Producto.objects.filter(disponible=True).count(),
    }
    
    return render(request, 'reportes/reporte_stock_productos.html', context)

@login_required
def alertas_stock(request):
    """Vista de alertas de stock en tiempo real"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver las alertas')
        return redirect('usuarios:dashboard')
    
    # Alertas críticas (sin stock)
    alertas_criticas = Producto.objects.filter(
        stock_actual=0,
        disponible=True
    ).select_related('categoria')
    
    # Alertas importantes (stock bajo)
    alertas_importantes = Producto.objects.filter(
        stock_actual__gt=0,
        stock_actual__lte=F('stock_minimo'),
        disponible=True
    ).select_related('categoria')
    
    # Alertas de advertencia (stock cerca del mínimo - 20% por encima)
    alertas_advertencia = Producto.objects.filter(
        stock_actual__gt=F('stock_minimo'),
        stock_actual__lte=F('stock_minimo') * 1.2,
        disponible=True
    ).select_related('categoria')
    
    context = {
        'titulo': 'Alertas de Stock',
        'alertas_criticas': alertas_criticas,
        'alertas_importantes': alertas_importantes,
        'alertas_advertencia': alertas_advertencia,
    }
    
    return render(request, 'reportes/alertas_stock.html', context)

@login_required
def configuracion_reportes(request):
    """Configuración de reportes automáticos y preferencias"""
    if request.user.tipo_usuario != 'administrador':
        messages.error(request, 'No tienes permisos para configurar reportes')
        return redirect('usuarios:dashboard')
    
    # Aquí se implementaría la configuración de reportes automáticos
    # Por ahora, solo mostramos la interfaz
    
    context = {
        'titulo': 'Configuración de Reportes',
    }
    
    return render(request, 'reportes/configuracion_reportes.html', context)
