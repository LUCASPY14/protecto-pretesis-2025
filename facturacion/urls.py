from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    # Lista y gestión de facturas
    path('', views.lista_facturas, name='lista_facturas'),
    path('factura/<uuid:factura_id>/', views.detalle_factura, name='detalle_factura'),
    
    # Generación de facturas
    path('generar/<uuid:venta_id>/', views.generar_factura, name='generar_factura'),
    path('anular/<uuid:factura_id>/', views.anular_factura, name='anular_factura'),
    
    # PDF y exportación
    path('pdf/<uuid:factura_id>/', views.generar_pdf_factura, name='generar_pdf'),
    
    # Configuración y reportes
    path('configuracion/', views.configuracion_facturacion, name='configuracion'),
    path('reporte/', views.reporte_facturacion, name='reporte'),
]