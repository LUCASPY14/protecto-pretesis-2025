from django.urls import path
from . import views
from . import pos_api_new as pos_api

app_name = 'ventas'

urlpatterns = [
    path('', views.lista_ventas, name='lista_ventas'),
    path('pos/', views.pos_dashboard, name='pos_dashboard'),
    path('pos/simple/', views.pos_dashboard_simple, name='pos_dashboard_simple'),
    path('pos/test/', views.pos_dashboard_test, name='pos_dashboard_test'),
    path('pos/debug/', views.pos_dashboard_debug, name='pos_dashboard_debug'),
    path('pos/buscar-producto/', views.buscar_producto, name='buscar_producto'),
    path('pos/buscar-tarjeta/', views.buscar_tarjeta, name='buscar_tarjeta'),
    path('pos/procesar-venta/', views.procesar_venta, name='procesar_venta'),
    # APIs para tarjetas virtuales
    path('api/buscar-tarjeta/', pos_api.buscar_tarjeta_ajax, name='api_buscar_tarjeta'),
    path('api/seleccionar-tarjeta/', pos_api.seleccionar_tarjeta_ajax, name='api_seleccionar_tarjeta'),
    path('api/buscar-producto/', pos_api.buscar_producto_ajax, name='api_buscar_producto'),
    path('api/seleccionar-producto/', pos_api.seleccionar_producto_ajax, name='api_seleccionar_producto'),
    path('api/procesar-venta-saldo/', pos_api.procesar_venta_saldo_virtual, name='api_procesar_venta_saldo'),
    path('api/procesar-venta-mixta/', pos_api.procesar_venta_mixta, name='api_procesar_venta_mixta'),
    path('api/procesar-venta-efectivo/', pos_api.procesar_venta_efectivo, name='api_procesar_venta_efectivo'),
    path('nueva/', views.nueva_venta, name='nueva_venta'),
    path('<int:pk>/', views.detalle_venta, name='detalle_venta'),
    path('<int:pk>/factura/', views.generar_factura, name='generar_factura'),
    path('metodos-pago/', views.lista_metodos_pago, name='lista_metodos_pago'),
    path('puntos-venta/', views.lista_puntos_venta, name='lista_puntos_venta'),
    path('facturas/', views.lista_facturas, name='lista_facturas'),
    path('facturas/<int:pk>/', views.ver_factura, name='ver_factura'),
]