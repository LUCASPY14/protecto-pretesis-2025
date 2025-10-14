from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('nuevo/', views.crear_producto, name='crear_producto'),
    path('<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),
    path('stock/', views.control_stock, name='control_stock'),
    path('stock/<int:pk>/movimiento/', views.movimiento_stock, name='movimiento_stock'),
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/nuevo/', views.crear_proveedor, name='crear_proveedor'),
]