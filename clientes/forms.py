from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from heladeria.models import Cliente
import re, json

# Cargar data de regiones/comunas
with open(settings.BASE_DIR / "clientes" / "data" / "chile_comunas.json", encoding="utf-8") as f:
    CHILE_DATA = json.load(f)

# Crear lista de regiones para ChoiceField
REGIONES_CHILE = [("", "Seleccione región")]
for item in CHILE_DATA["regiones"]:
    REGIONES_CHILE.append((item["region"], item["region"]))

class ClienteForm(forms.ModelForm):
    region = forms.ChoiceField(
        choices=REGIONES_CHILE,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'region_select'})
    )
    comuna = forms.CharField(
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'comuna_select'})
    )

    class Meta:
        model = Cliente
        fields = [
            'rut', 'nombre', 'apellido', 'tipo_cliente', 'direccion',
            'pais', 'region', 'comuna', 'telefono', 'email',
            'idioma_preferido', 'documento_preferido',
            'enviar_comprobante_email', 'recibe_promociones',
        ]
        widgets = {
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'^\d+-[\dKk]$', 
                'title': 'Formato RUT válido: 12345678-5'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$',
                'title': 'Solo letras y espacios'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$',
                'title': 'Solo letras y espacios'
            }),
            'tipo_cliente': forms.Select(attrs={'class': 'form-select'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.HiddenInput(),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'^[0-9\s]+$',
                'title': 'Solo números y espacios'
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'idioma_preferido': forms.Select(attrs={'class': 'form-select'}),
            'documento_preferido': forms.Select(attrs={'class': 'form-select'}),
            'enviar_comprobante_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recibe_promociones': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # Validaciones de Django
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        if not nombre:
            raise ValidationError("El nombre no puede estar vacío.")
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
            raise ValidationError("El nombre solo puede contener letras y espacios.")
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '')
        if not apellido:
            raise ValidationError("El apellido no puede estar vacío.")
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', apellido):
            raise ValidationError("El apellido solo puede contener letras y espacios.")
        return apellido

    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '')
        if not re.match(r'^[0-9]+-[0-9Kk]$', rut):
            raise ValidationError(
                "El RUT debe tener el formato: números-guion-dígito (0-9 o K). Ej: 12345678-5"
            )
        return rut.upper()

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        if not telefono:
            raise ValidationError("El teléfono no puede estar vacío.")
        if not re.match(r'^[0-9\s]+$', telefono):
            raise ValidationError("El teléfono solo puede contener números y espacios.")
        return telefono

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if not email:
            raise ValidationError("El correo electrónico no puede estar vacío.")
        if '@' not in email:
            raise ValidationError("El correo electrónico debe contener '@'.")
        return email
