from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.lista_reportes, name='lista_reportes'),
    path('consumo-hijo/', views.reporte_consumo_hijo, name='reporte_consumo_hijo'),
    path('productos-vendidos/', views.reporte_productos_mas_vendidos, name='reporte_productos_mas_vendidos'),
    path('ingresos-metodo-pago/', views.reporte_ingresos_metodo_pago, name='reporte_ingresos_metodo_pago'),
    path('ventas-diarias/', views.reporte_ventas_diarias, name='reporte_ventas_diarias'),
    path('stock-productos/', views.reporte_stock_productos, name='reporte_stock_productos'),
    path('alertas-stock/', views.alertas_stock, name='alertas_stock'),
    path('configuracion/', views.configuracion_reportes, name='configuracion_reportes'),
]