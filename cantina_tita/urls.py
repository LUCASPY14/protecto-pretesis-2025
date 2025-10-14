"""
URL configuration para La Cantina de Tita
Sistema de Gestión de Cantina
Desarrollado por LGservice - +595985350656
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Personalizar el admin
admin.site.site_header = "La Cantina de Tita - Administración"
admin.site.site_title = "Cantina de Tita Admin"
admin.site.index_title = "Panel de Administración"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('productos/', include('productos.urls')),
    path('ventas/', include('ventas.urls')),
    path('reportes/', include('reportes.urls')),
    path('facturacion/', include('facturacion.urls')),
    
    # URLs de autenticación
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
