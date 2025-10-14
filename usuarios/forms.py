from django import forms
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from .models import PerfilHijo, RecargaSaldo


class RecargaSaldoForm(forms.ModelForm):
    """
    Formulario para recargar saldo a un hijo
    """
    monto = forms.DecimalField(
        max_digits=10, 
        decimal_places=0,
        validators=[MinValueValidator(1000)],  # Mínimo 1000 Gs
        widget=forms.NumberInput(attrs={
            'class': 'form-control text-right pr-12',
            'placeholder': '10000',
            'min': '1000',
            'step': '1000',
        }),
        help_text='Monto mínimo: 1.000 Gs.'
    )
    
    observaciones = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo de la recarga (opcional)'
        })
    )
    
    class Meta:
        model = RecargaSaldo
        fields = ['monto', 'observaciones']
        
    def __init__(self, *args, **kwargs):
        self.hijo = kwargs.pop('hijo', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True, realizada_por=None):
        """
        Guardar la recarga y actualizar el saldo del hijo
        """
        recarga = super().save(commit=False)
        recarga.hijo = self.hijo
        recarga.realizada_por = realizada_por
        
        if commit:
            recarga.save()
            # Actualizar saldo del hijo
            self.hijo.saldo_virtual += recarga.monto
            self.hijo.save()
            
        return recarga


class PerfilHijoForm(forms.ModelForm):
    """
    Formulario para crear/editar perfil de hijo
    """
    nombre_completo = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del hijo'
        })
    )
    
    grado = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1° Grado, 2° Grado, etc.'
        })
    )
    
    seccion = forms.CharField(
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'A, B, C, etc.'
        })
    )
    
    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    puede_saldo_negativo = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        help_text='Permitir que el hijo tenga saldo negativo'
    )
    
    limite_saldo_negativo = forms.DecimalField(
        max_digits=10,
        decimal_places=0,
        required=False,
        initial=10000,  # 10,000 Gs por defecto
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10000',
            'min': '0',
            'step': '1000',
        }),
        help_text='Límite máximo de saldo negativo permitido (en Gs.)'
    )
    
    activo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        help_text='Marcar como activo para permitir compras'
    )
    
    # Campos de tarjeta
    asignar_tarjeta = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        }),
        help_text='Asignar tarjeta exclusiva de La Cantina de Tita automáticamente'
    )
    
    numero_tarjeta_manual = forms.CharField(
        required=False,
        max_length=19,  # 16 dígitos + 3 guiones
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234-5678-9012-3456',
            'pattern': r'\d{4}-\d{4}-\d{4}-\d{4}',
        }),
        help_text='Número específico de tarjeta (opcional). Formato: XXXX-XXXX-XXXX-XXXX'
    )
    
    codigo_tarjeta_manual = forms.CharField(
        required=False,
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234',
            'pattern': r'\d{4}',
            'maxlength': '4'
        }),
        help_text='Código de seguridad específico (opcional). 4 dígitos'
    )
    
    class Meta:
        model = PerfilHijo
        fields = [
            'nombre_completo', 
            'grado', 
            'seccion', 
            'fecha_nacimiento',
            'puede_saldo_negativo', 
            'limite_saldo_negativo',
            'activo'
        ]
        
    def __init__(self, *args, **kwargs):
        self.padre = kwargs.pop('padre', None)
        super().__init__(*args, **kwargs)
        
        # Ocultar campo de límite si no puede tener saldo negativo
        if not self.instance.pk or not self.instance.puede_saldo_negativo:
            self.fields['limite_saldo_negativo'].widget.attrs['style'] = 'display: none;'
    
    def clean(self):
        cleaned_data = super().clean()
        puede_negativo = cleaned_data.get('puede_saldo_negativo', False)
        limite_negativo = cleaned_data.get('limite_saldo_negativo', 0)
        numero_manual = cleaned_data.get('numero_tarjeta_manual', '')
        codigo_manual = cleaned_data.get('codigo_tarjeta_manual', '')
        asignar_tarjeta = cleaned_data.get('asignar_tarjeta', False)
        
        # Si permite saldo negativo, debe tener un límite
        if puede_negativo and not limite_negativo:
            cleaned_data['limite_saldo_negativo'] = 10000  # Valor por defecto
            
        # Si no permite saldo negativo, el límite debe ser 0
        if not puede_negativo:
            cleaned_data['limite_saldo_negativo'] = 0
        
        # Validaciones de tarjeta manual
        if numero_manual and not asignar_tarjeta:
            raise forms.ValidationError("Debe marcar 'Asignar tarjeta' para usar un número manual")
        
        if numero_manual:
            # Limpiar formato del número
            numero_limpio = numero_manual.replace('-', '').replace(' ', '')
            if not numero_limpio.isdigit() or len(numero_limpio) != 16:
                raise forms.ValidationError("El número de tarjeta debe tener exactamente 16 dígitos")
            
            # Verificar que no esté en uso (excluyendo la instancia actual si existe)
            from .models import PerfilHijo
            query = PerfilHijo.objects.filter(numero_tarjeta=numero_limpio)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise forms.ValidationError("Este número de tarjeta ya está en uso")
            
            cleaned_data['numero_tarjeta_manual'] = numero_limpio
        
        if codigo_manual:
            if not codigo_manual.isdigit() or len(codigo_manual) != 4:
                raise forms.ValidationError("El código de seguridad debe tener exactamente 4 dígitos")
            
        return cleaned_data
        
    def save(self, commit=True):
        """
        Guardar el perfil del hijo y asignar tarjeta si es necesario
        """
        hijo = super().save(commit=False)
        if self.padre:
            hijo.padre = self.padre
            
        if commit:
            hijo.save()
            
            # Asignar tarjeta si se solicitó
            if self.cleaned_data.get('asignar_tarjeta', False):
                numero_manual = self.cleaned_data.get('numero_tarjeta_manual')
                codigo_manual = self.cleaned_data.get('codigo_tarjeta_manual')
                
                try:
                    hijo.asignar_tarjeta(
                        numero_manual=numero_manual,
                        codigo_manual=codigo_manual
                    )
                except Exception as e:
                    # Si hay error en la asignación, lo manejamos
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error asignando tarjeta: {e}")
            
        return hijo


class TarjetaManualForm(forms.Form):
    """
    Formulario para asignación manual de tarjetas
    """
    ACCION_CHOICES = [
        ('asignar_nueva', 'Asignar nueva tarjeta (automática)'),
        ('asignar_manual', 'Asignar número específico'),
        ('regenerar_codigo', 'Regenerar código de seguridad'),
        ('desactivar', 'Desactivar tarjeta'),
        ('activar', 'Activar tarjeta'),
    ]
    
    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio'
        }),
        help_text='Seleccione la acción a realizar'
    )
    
    numero_tarjeta = forms.CharField(
        required=False,
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234-5678-9012-3456',
            'pattern': r'\d{4}-\d{4}-\d{4}-\d{4}',
        }),
        help_text='Número específico de tarjeta. Formato: XXXX-XXXX-XXXX-XXXX'
    )
    
    codigo_seguridad = forms.CharField(
        required=False,
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234',
            'pattern': r'\d{4}',
            'maxlength': '4'
        }),
        help_text='Código de seguridad de 4 dígitos'
    )
    
    def __init__(self, *args, **kwargs):
        self.hijo = kwargs.pop('hijo', None)
        super().__init__(*args, **kwargs)
        
        if self.hijo and self.hijo.numero_tarjeta:
            # Si ya tiene tarjeta, mostrar información actual
            self.fields['numero_actual'] = forms.CharField(
                initial=self.hijo.numero_tarjeta_formateado,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'readonly': True
                }),
                label='Número actual'
            )
            self.fields['estado_actual'] = forms.CharField(
                initial='Activa' if self.hijo.tarjeta_activa else 'Inactiva',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'readonly': True
                }),
                label='Estado actual'
            )
    
    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get('accion')
        numero = cleaned_data.get('numero_tarjeta')
        codigo = cleaned_data.get('codigo_seguridad')
        
        # Validaciones según la acción
        if accion == 'asignar_manual':
            if not numero:
                raise ValidationError("Debe proporcionar un número de tarjeta")
            
            # Limpiar y validar número
            numero_limpio = numero.replace('-', '').replace(' ', '')
            if not numero_limpio.isdigit() or len(numero_limpio) != 16:
                raise ValidationError("El número de tarjeta debe tener exactamente 16 dígitos")
            
            # Verificar unicidad
            if PerfilHijo.objects.filter(numero_tarjeta=numero_limpio).exclude(id=self.hijo.id if self.hijo else None).exists():
                raise ValidationError("Este número de tarjeta ya está en uso")
            
            cleaned_data['numero_tarjeta'] = numero_limpio
        
        if codigo:
            if not codigo.isdigit() or len(codigo) != 4:
                raise ValidationError("El código de seguridad debe tener exactamente 4 dígitos")
        
        return cleaned_data
    
    def aplicar_accion(self):
        """
        Aplica la acción seleccionada al hijo
        """
        if not self.hijo:
            raise ValidationError("No hay hijo asociado")
        
        accion = self.cleaned_data.get('accion')
        numero = self.cleaned_data.get('numero_tarjeta')
        codigo = self.cleaned_data.get('codigo_seguridad')
        
        try:
            if accion == 'asignar_nueva':
                self.hijo.asignar_tarjeta()
                return f"Nueva tarjeta asignada: {self.hijo.numero_tarjeta_formateado}"
            
            elif accion == 'asignar_manual':
                self.hijo.asignar_tarjeta(numero_manual=numero, codigo_manual=codigo)
                return f"Tarjeta manual asignada: {self.hijo.numero_tarjeta_formateado}"
            
            elif accion == 'regenerar_codigo':
                codigo_nuevo = self.hijo.generar_codigo_tarjeta()
                self.hijo.codigo_tarjeta = codigo_nuevo
                self.hijo.save()
                return f"Código de seguridad regenerado"
            
            elif accion == 'desactivar':
                self.hijo.desactivar_tarjeta()
                return "Tarjeta desactivada exitosamente"
            
            elif accion == 'activar':
                self.hijo.tarjeta_activa = True
                self.hijo.save()
                return "Tarjeta activada exitosamente"
                
        except Exception as e:
            raise ValidationError(f"Error al aplicar acción: {str(e)}")