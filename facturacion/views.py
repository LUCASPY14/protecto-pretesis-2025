from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import json
import uuid

# Imports de reportlab para generar PDFs
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from io import BytesIO
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from ventas.models import Venta, Factura
from .models import TipoDocumento, ConfiguracionFacturacion, HistorialFacturacion


@login_required
def lista_facturas(request):
    """Lista todas las facturas y boletas"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver las facturas')
        return redirect('usuarios:dashboard')
    
    # Filtros
    tipo_doc = request.GET.get('tipo_doc', '')
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    cliente = request.GET.get('cliente', '')
    
    # Queryset base
    facturas = Factura.objects.select_related('venta', 'usuario_creacion').all()
    
    # Aplicar filtros
    if tipo_doc:
        facturas = facturas.filter(tipo_factura=tipo_doc)
    if estado:
        facturas = facturas.filter(estado=estado)
    if fecha_desde:
        facturas = facturas.filter(fecha_emision__date__gte=fecha_desde)
    if fecha_hasta:
        facturas = facturas.filter(fecha_emision__date__lte=fecha_hasta)
    if cliente:
        facturas = facturas.filter(cliente_nombre__icontains=cliente)
    
    # Paginación
    paginator = Paginator(facturas, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    stats = {
        'total_facturas': facturas.count(),
        'total_emitidas': facturas.filter(estado='emitida').count(),
        'total_anuladas': facturas.filter(estado='anulada').count(),
        'total_monto': sum(f.total_factura for f in facturas.filter(estado='emitida')),
    }
    
    context = {
        'title': 'Gestión de Facturas y Boletas',
        'page_obj': page_obj,
        'stats': stats,
        'filtros': {
            'tipo_doc': tipo_doc,
            'estado': estado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'cliente': cliente,
        },
        'tipos_documento': Factura.TIPO_FACTURA_CHOICES,
        'estados': Factura.ESTADOS_DOCUMENTO,
    }
    
    return render(request, 'facturacion/lista_facturas.html', context)


@login_required
def detalle_factura(request, factura_id):
    """Muestra el detalle de una factura"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver facturas')
        return redirect('usuarios:dashboard')
    
    factura = get_object_or_404(Factura, id=factura_id)
    
    # Historial de la factura
    historial = HistorialFacturacion.objects.filter(
        factura_numero=factura.numero_factura
    ).order_by('-fecha')
    
    context = {
        'title': f'Factura {factura.numero_factura}',
        'factura': factura,
        'historial': historial,
    }
    
    return render(request, 'facturacion/detalle_factura.html', context)


@login_required
def generar_factura(request, venta_id):
    """Genera una factura para una venta"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Verificar si ya tiene factura
    if hasattr(venta, 'factura_documento'):
        return JsonResponse({
            'success': False, 
            'error': 'Esta venta ya tiene factura generada'
        })
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Crear la factura
                factura = Factura(
                    venta=venta,
                    tipo_factura=data.get('tipo_factura', 'boleta'),
                    cliente_nombre=data.get('cliente_nombre', 'Cliente General'),
                    cliente_rut=data.get('cliente_rut', ''),
                    cliente_direccion=data.get('cliente_direccion', ''),
                    cliente_telefono=data.get('cliente_telefono', ''),
                    cliente_email=data.get('cliente_email', ''),
                    observaciones=data.get('observaciones', ''),
                    usuario_creacion=request.user,
                )
                factura.save()
                
                # Emitir automáticamente
                factura.emitir(request.user)
                
                # Registrar en historial
                HistorialFacturacion.objects.create(
                    factura_numero=factura.numero_factura,
                    accion='creada',
                    descripcion='Factura creada desde POS',
                    usuario=request.user
                )
            
            return JsonResponse({
                'success': True,
                'factura_id': str(factura.id),
                'numero_factura': factura.numero_factura,
                'message': 'Factura generada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # GET request - mostrar formulario
    context = {
        'venta': venta,
        'tipos_factura': Factura.TIPO_FACTURA_CHOICES,
    }
    
    return render(request, 'facturacion/generar_factura.html', context)


@login_required
def anular_factura(request, factura_id):
    """Anula una factura"""
    if request.user.tipo_usuario not in ['administrador']:
        return JsonResponse({'success': False, 'error': 'Sin permisos para anular'})
    
    factura = get_object_or_404(Factura, id=factura_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            motivo = data.get('motivo', 'Anulada por usuario')
            
            if factura.estado == 'anulada':
                return JsonResponse({
                    'success': False,
                    'error': 'La factura ya está anulada'
                })
            
            # Anular la factura
            factura.anular(request.user, motivo)
            
            return JsonResponse({
                'success': True,
                'message': 'Factura anulada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def generar_pdf_factura(request, factura_id):
    """Genera el PDF de una factura"""
    if not REPORTLAB_AVAILABLE:
        messages.error(request, 'La generación de PDF no está disponible')
        return redirect('facturacion:lista_facturas')
    
    factura = get_object_or_404(Factura, id=factura_id)
    
    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{factura.numero_factura}.pdf"'
    
    # Obtener configuración
    config = ConfiguracionFacturacion.objects.first()
    if not config:
        config = ConfiguracionFacturacion.objects.create()
    
    # Crear el documento PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.darkblue,
        alignment=1  # Centro
    )
    
    # Contenido del PDF
    story = []
    
    # Encabezado de la empresa
    story.append(Paragraph(config.empresa_nombre, title_style))
    story.append(Paragraph(f"RUT: {config.empresa_rut}", styles['Normal']))
    story.append(Paragraph(config.empresa_direccion, styles['Normal']))
    story.append(Paragraph(f"Teléfono: {config.empresa_telefono}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Tipo y número de documento
    doc_tipo = 'BOLETA' if factura.tipo_factura == 'boleta' else 'FACTURA'
    story.append(Paragraph(f"{doc_tipo} N° {factura.numero_factura}", title_style))
    story.append(Spacer(1, 20))
    
    # Datos del cliente
    story.append(Paragraph("DATOS DEL CLIENTE", styles['Heading2']))
    story.append(Paragraph(f"Nombre: {factura.cliente_nombre}", styles['Normal']))
    if factura.cliente_rut:
        story.append(Paragraph(f"RUT: {factura.cliente_rut}", styles['Normal']))
    if factura.cliente_direccion:
        story.append(Paragraph(f"Dirección: {factura.cliente_direccion}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Fecha de emisión
    story.append(Paragraph(f"Fecha: {factura.fecha_emision.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Detalle de productos
    story.append(Paragraph("DETALLE DE PRODUCTOS", styles['Heading2']))
    
    # Crear tabla de productos
    data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
    
    for detalle in factura.venta.detalles.all():
        data.append([
            detalle.producto.nombre,
            str(detalle.cantidad),
            f"${detalle.precio_unitario:,.0f}",
            f"${detalle.subtotal:,.0f}"
        ])
    
    # Totales
    data.append(['', '', 'SUBTOTAL:', f"${factura.subtotal_factura:,.0f}"])
    if factura.impuesto_factura > 0:
        data.append(['', '', 'IVA (19%):', f"${factura.impuesto_factura:,.0f}"])
    data.append(['', '', 'TOTAL:', f"${factura.total_factura:,.0f}"])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Alinear números a la derecha
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Observaciones
    if factura.observaciones:
        story.append(Paragraph("OBSERVACIONES", styles['Heading2']))
        story.append(Paragraph(factura.observaciones, styles['Normal']))
    
    # Construir el PDF
    doc.build(story)
    
    # Obtener el PDF del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Registrar en historial
    HistorialFacturacion.objects.create(
        factura_numero=factura.numero_factura,
        accion='impresa',
        descripcion='PDF generado',
        usuario=request.user
    )
    
    response.write(pdf)
    return response


@login_required
def configuracion_facturacion(request):
    """Configuración del sistema de facturación"""
    if request.user.tipo_usuario != 'administrador':
        messages.error(request, 'No tienes permisos para configurar facturación')
        return redirect('usuarios:dashboard')
    
    config = ConfiguracionFacturacion.objects.first()
    if not config:
        config = ConfiguracionFacturacion.objects.create()
    
    if request.method == 'POST':
        try:
            # Actualizar configuración
            config.empresa_nombre = request.POST.get('empresa_nombre', config.empresa_nombre)
            config.empresa_rut = request.POST.get('empresa_rut', config.empresa_rut)
            config.empresa_direccion = request.POST.get('empresa_direccion', config.empresa_direccion)
            config.empresa_telefono = request.POST.get('empresa_telefono', config.empresa_telefono)
            config.empresa_email = request.POST.get('empresa_email', config.empresa_email)
            
            config.iva_porcentaje = Decimal(request.POST.get('iva_porcentaje', config.iva_porcentaje))
            config.emite_boletas = 'emite_boletas' in request.POST
            config.emite_facturas = 'emite_facturas' in request.POST
            
            config.save()
            
            messages.success(request, 'Configuración actualizada exitosamente')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar configuración: {str(e)}')
    
    context = {
        'title': 'Configuración de Facturación',
        'config': config,
    }
    
    return render(request, 'facturacion/configuracion.html', context)


@login_required
def reporte_facturacion(request):
    """Reporte de facturación"""
    if request.user.tipo_usuario not in ['administrador', 'cajero']:
        messages.error(request, 'No tienes permisos para ver reportes')
        return redirect('usuarios:dashboard')
    
    # Estadísticas de facturación
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    stats = {
        'facturas_mes': Factura.objects.filter(
            fecha_emision__date__gte=hace_30_dias,
            estado='emitida'
        ).count(),
        
        'boletas_mes': Factura.objects.filter(
            fecha_emision__date__gte=hace_30_dias,
            tipo_factura='boleta',
            estado='emitida'
        ).count(),
        
        'ingresos_mes': Factura.objects.filter(
            fecha_emision__date__gte=hace_30_dias,
            estado='emitida'
        ).aggregate(total=Sum('total_factura'))['total'] or Decimal('0.00'),
        
        'documentos_anulados': Factura.objects.filter(
            fecha_emision__date__gte=hace_30_dias,
            estado='anulada'
        ).count(),
    }
    
    # Facturas por tipo
    facturas_por_tipo = {}
    for tipo_key, tipo_nombre in Factura.TIPO_FACTURA_CHOICES:
        count = Factura.objects.filter(
            tipo_factura=tipo_key,
            fecha_emision__date__gte=hace_30_dias,
            estado='emitida'
        ).count()
        facturas_por_tipo[tipo_nombre] = count
    
    context = {
        'title': 'Reporte de Facturación',
        'stats': stats,
        'facturas_por_tipo': facturas_por_tipo,
    }
    
    return render(request, 'facturacion/reporte.html', context)
