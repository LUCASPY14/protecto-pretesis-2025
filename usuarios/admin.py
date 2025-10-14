from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, PerfilHijo, RecargaSaldo, TransaccionTarjeta

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Administración personalizada para el modelo Usuario
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'activo', 'date_joined')
    list_filter = ('tipo_usuario', 'activo', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'cedula')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('tipo_usuario', 'telefono', 'cedula', 'direccion', 'activo')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('email', 'first_name', 'last_name', 'tipo_usuario', 'telefono', 'cedula')
        }),
    )


@admin.register(PerfilHijo)
class PerfilHijoAdmin(admin.ModelAdmin):
    """
    Administración para perfiles de hijos
    """
    list_display = ('nombre_completo', 'padre', 'grado', 'numero_tarjeta_oculto', 'saldo_virtual', 'tarjeta_activa', 'activo')
    list_filter = ('activo', 'tarjeta_activa', 'puede_saldo_negativo', 'grado', 'padre__tipo_usuario')
    search_fields = ('nombre_completo', 'numero_tarjeta', 'padre__username', 'padre__first_name', 'padre__last_name')
    ordering = ('nombre_completo',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('padre', 'nombre_completo', 'fecha_nacimiento')
        }),
        ('Información Académica', {
            'fields': ('grado', 'seccion')
        }),
        ('Tarjeta Exclusiva', {
            'fields': ('numero_tarjeta', 'codigo_tarjeta', 'tarjeta_activa', 'fecha_asignacion_tarjeta'),
            'description': 'Información de la tarjeta exclusiva de La Cantina de Tita'
        }),
        ('Saldo Virtual', {
            'fields': ('saldo_virtual', 'puede_saldo_negativo', 'limite_saldo_negativo')
        }),
        ('Estado', {
            'fields': ('activo',)
        })
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')


@admin.register(RecargaSaldo)
class RecargaSaldoAdmin(admin.ModelAdmin):
    """
    Administración para recargas de saldo
    """
    list_display = ('hijo', 'monto', 'fecha_recarga', 'realizada_por')
    list_filter = ('fecha_recarga', 'realizada_por')
    search_fields = ('hijo__nombre_completo', 'realizada_por__username')
    ordering = ('-fecha_recarga',)
    
    fieldsets = (
        ('Información de Recarga', {
            'fields': ('hijo', 'monto', 'realizada_por')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        })
    )
    
    readonly_fields = ('fecha_recarga',)


@admin.register(TransaccionTarjeta)
class TransaccionTarjetaAdmin(admin.ModelAdmin):
    """
    Administración para transacciones de tarjeta
    """
    list_display = ('hijo', 'numero_tarjeta_enmascarada', 'tipo_transaccion', 'monto', 'estado', 'fecha_transaccion')
    list_filter = ('tipo_transaccion', 'estado', 'fecha_transaccion')
    search_fields = ('hijo__nombre_completo', 'numero_tarjeta_utilizada', 'observaciones', 'punto_venta')
    ordering = ('-fecha_transaccion',)
    readonly_fields = ('fecha_transaccion',)
    
    def numero_tarjeta_enmascarada(self, obj):
        """Muestra el número de tarjeta enmascarado para privacidad"""
        if obj.numero_tarjeta_utilizada and len(obj.numero_tarjeta_utilizada) >= 4:
            return f"****-****-****-{obj.numero_tarjeta_utilizada[-4:]}"
        return "N/A"
    numero_tarjeta_enmascarada.short_description = "Tarjeta"
    
    fieldsets = (
        ('Información de Transacción', {
            'fields': ('hijo', 'numero_tarjeta_utilizada', 'tipo_transaccion', 'monto', 'estado')
        }),
        ('Saldos', {
            'fields': ('saldo_anterior', 'saldo_posterior')
        }),
        ('Detalles Adicionales', {
            'fields': ('realizada_por', 'punto_venta', 'observaciones', 'fecha_transaccion')
        }),
    )
