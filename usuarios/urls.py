from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('perfil/', views.perfil, name='perfil'),
    path('hijos/', views.lista_hijos, name='lista_hijos'),
    path('hijos/nuevo/', views.crear_hijo, name='crear_hijo'),
    path('hijos/<int:pk>/', views.detalle_hijo, name='detalle_hijo'),
    path('hijos/<int:pk>/recarga/', views.recarga_saldo, name='recarga_saldo'),
    path('hijos/<int:pk>/asignar-tarjeta/', views.asignar_tarjeta, name='asignar_tarjeta'),
    path('hijos/<int:pk>/tarjeta-estado/', views.activar_desactivar_tarjeta, name='activar_desactivar_tarjeta'),
    path('hijos/<int:pk>/regenerar-tarjeta/', views.regenerar_tarjeta, name='regenerar_tarjeta'),
    path('hijos/<int:pk>/gestionar-tarjeta/', views.gestionar_tarjeta_manual, name='gestionar_tarjeta_manual'),
    path('hijos/<int:pk>/editar/', views.editar_hijo, name='editar_hijo'),
    path('hijos/<int:pk>/eliminar/', views.eliminar_hijo, name='eliminar_hijo'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/nuevo/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/', views.detalle_usuario, name='detalle_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    path('logout/', views.logout_view, name='logout'),
]