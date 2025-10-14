from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado para La Cantina de Tita
    Desarrollado por LGservice - +595985350656
    """
    TIPO_USUARIO_CHOICES = [
        ('padre', 'Padre/Tutor'),
        ('cajero', 'Cajero'),
        ('administrador', 'Administrador'),
    ]
    
    tipo_usuario = models.CharField(
        max_length=15,
        choices=TIPO_USUARIO_CHOICES,
        default='padre'
    )
    
    telefono_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos."
    )
    telefono = models.CharField(validators=[telefono_regex], max_length=17, blank=True)
    
    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_tipo_usuario_display()})"
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"


class PerfilHijo(models.Model):
    """
    Perfil de hijo vinculado a un padre/tutor
    """
    padre = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='hijos',
        limit_choices_to={'tipo_usuario': 'padre'}
    )
    nombre_completo = models.CharField(max_length=150)
    grado = models.CharField(max_length=50, blank=True)
    seccion = models.CharField(max_length=10, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    
    # Tarjeta exclusiva de La Cantina de Tita
    numero_tarjeta = models.CharField(
        max_length=16, 
        unique=True,
        null=True,
        blank=True,
        help_text="Número único de la tarjeta exclusiva de La Cantina de Tita"
    )
    codigo_tarjeta = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        help_text="Código de seguridad de la tarjeta (para verificación en POS)"
    )
    tarjeta_activa = models.BooleanField(
        default=False,
        help_text="Indica si la tarjeta está activa para uso en puntos de venta"
    )
    fecha_asignacion_tarjeta = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se asignó la tarjeta al hijo"
    )
    
    # Saldo virtual de la tarjeta exclusiva
    saldo_virtual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Saldo disponible en la tarjeta exclusiva de la cantina"
    )
    
    # Control de saldo negativo
    puede_saldo_negativo = models.BooleanField(
        default=False,
        help_text="Permite que el hijo tenga saldo negativo con autorización"
    )
    limite_saldo_negativo = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        help_text="Límite máximo de saldo negativo permitido"
    )
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre_completo} (Hijo de {self.padre.get_full_name()})"
    
    @property
    def saldo_disponible(self):
        """Calcula el saldo disponible incluyendo el límite negativo"""
        if self.puede_saldo_negativo:
            return self.saldo_virtual + self.limite_saldo_negativo
        return max(self.saldo_virtual, 0)
    
    def generar_numero_tarjeta(self):
        """Genera un número único de tarjeta de 16 dígitos"""
        import random
        while True:
            # Formato: TITA-XXXX-XXXX-XXXX (16 dígitos)
            numero = f"5555{random.randint(100000000000, 999999999999)}"
            if not PerfilHijo.objects.filter(numero_tarjeta=numero).exists():
                return numero
    
    def generar_codigo_tarjeta(self):
        """Genera un código de seguridad de 4 dígitos"""
        import random
        return f"{random.randint(1000, 9999)}"
    
    def asignar_tarjeta(self, numero_manual=None, codigo_manual=None, save=True):
        """
        Asigna una nueva tarjeta al hijo
        Args:
            numero_manual: Número de tarjeta específico a asignar (opcional)
            codigo_manual: Código de seguridad específico (opcional)
            save: Si debe guardar automáticamente los cambios
        """
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        
        # Asignar número de tarjeta
        if numero_manual:
            # Validar formato del número manual
            if not self.validar_numero_tarjeta(numero_manual):
                raise ValidationError("El número de tarjeta debe tener 16 dígitos")
            
            # Verificar que no esté en uso
            if PerfilHijo.objects.filter(numero_tarjeta=numero_manual).exclude(id=self.id).exists():
                raise ValidationError("Este número de tarjeta ya está en uso")
            
            self.numero_tarjeta = numero_manual
        elif not self.numero_tarjeta:
            self.numero_tarjeta = self.generar_numero_tarjeta()
        
        # Asignar código de seguridad
        if codigo_manual:
            if not self.validar_codigo_tarjeta(codigo_manual):
                raise ValidationError("El código de seguridad debe tener 4 dígitos")
            self.codigo_tarjeta = codigo_manual
        elif not self.codigo_tarjeta:
            self.codigo_tarjeta = self.generar_codigo_tarjeta()
        
        self.tarjeta_activa = True
        self.fecha_asignacion_tarjeta = timezone.now()
        
        if save:
            self.save()
    
    def validar_numero_tarjeta(self, numero):
        """Valida que el número de tarjeta tenga el formato correcto"""
        import re
        # Remover espacios y guiones
        numero = re.sub(r'[\s-]', '', numero)
        # Verificar que tenga 16 dígitos
        return len(numero) == 16 and numero.isdigit()
    
    def validar_codigo_tarjeta(self, codigo):
        """Valida que el código de seguridad tenga el formato correcto"""
        return len(codigo) == 4 and codigo.isdigit()
    
    def desactivar_tarjeta(self, save=True):
        """Desactiva la tarjeta del hijo"""
        self.tarjeta_activa = False
        if save:
            self.save()
    
    @property
    def numero_tarjeta_formateado(self):
        """Retorna el número de tarjeta formateado para mostrar"""
        if self.numero_tarjeta:
            num = self.numero_tarjeta
            return f"{num[:4]}-{num[4:8]}-{num[8:12]}-{num[12:16]}"
        return None
    
    @property
    def numero_tarjeta_oculto(self):
        """Retorna el número de tarjeta parcialmente oculto por seguridad"""
        if self.numero_tarjeta:
            num = self.numero_tarjeta
            return f"{num[:4]}-****-****-{num[12:16]}"
        return None
    
    def puede_realizar_compra(self, monto):
        """Verifica si el hijo puede realizar una compra con el monto dado"""
        if not self.activo or not self.tarjeta_activa:
            return False, "Tarjeta inactiva"
        
        if monto <= 0:
            return False, "Monto inválido"
        
        saldo_disponible = self.saldo_disponible
        if monto > saldo_disponible:
            return False, f"Saldo insuficiente. Disponible: {saldo_disponible}"
        
        return True, "OK"
    
    class Meta:
        verbose_name = "Perfil de Hijo"
        verbose_name_plural = "Perfiles de Hijos"
        ordering = ['nombre_completo']


class RecargaSaldo(models.Model):
    """
    Historial de recargas de saldo virtual
    """
    hijo = models.ForeignKey(
        PerfilHijo, 
        on_delete=models.CASCADE, 
        related_name='recargas'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_recarga = models.DateTimeField(auto_now_add=True)
    realizada_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='recargas_realizadas'
    )
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"Recarga {self.monto} - {self.hijo.nombre_completo}"
    
    class Meta:
        verbose_name = "Recarga de Saldo"
        verbose_name_plural = "Recargas de Saldo"
        ordering = ['-fecha_recarga']


class TransaccionTarjeta(models.Model):
    """
    Historial de transacciones realizadas con las tarjetas de los hijos
    """
    TIPO_TRANSACCION_CHOICES = [
        ('compra', 'Compra en POS'),
        ('recarga', 'Recarga de saldo'),
        ('ajuste', 'Ajuste manual'),
        ('devolucion', 'Devolución'),
    ]
    
    ESTADO_CHOICES = [
        ('exitosa', 'Exitosa'),
        ('fallida', 'Fallida'),
        ('pendiente', 'Pendiente'),
        ('cancelada', 'Cancelada'),
    ]
    
    hijo = models.ForeignKey(
        PerfilHijo,
        on_delete=models.CASCADE,
        related_name='transacciones_tarjeta'
    )
    numero_tarjeta_utilizada = models.CharField(
        max_length=16,
        help_text="Número de tarjeta utilizado en la transacción"
    )
    tipo_transaccion = models.CharField(
        max_length=20,
        choices=TIPO_TRANSACCION_CHOICES,
        default='compra'
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto de la transacción (positivo para créditos, negativo para débitos)"
    )
    saldo_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Saldo antes de la transacción"
    )
    saldo_posterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Saldo después de la transacción"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='exitosa'
    )
    fecha_transaccion = models.DateTimeField(auto_now_add=True)
    realizada_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones_realizadas'
    )
    punto_venta = models.CharField(
        max_length=50,
        blank=True,
        help_text="Identificación del punto de venta donde se realizó"
    )
    observaciones = models.TextField(blank=True)
    
    # Referencia a venta si es una compra
    venta_relacionada = models.ForeignKey(
        'ventas.Venta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones_tarjeta'
    )
    
    def __str__(self):
        return f"{self.get_tipo_transaccion_display()} - {self.hijo.nombre_completo} - {self.monto}"
    
    class Meta:
        verbose_name = "Transacción de Tarjeta"
        verbose_name_plural = "Transacciones de Tarjetas"
        ordering = ['-fecha_transaccion']
