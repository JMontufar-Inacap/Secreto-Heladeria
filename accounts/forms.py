from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.models import User
from .models import PerfilUsuario
import re

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Usuario o email"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Contraseña"}
        )


class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['telefono', 'avatar']
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 9 1234 5678'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        if telefono and not re.match(r'^[0-9\s]+$', telefono):
            raise forms.ValidationError("Solo se permiten números y espacios en el teléfono.")
        return telefono


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class CambiarPasswordForm(forms.Form):
    nueva_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Nueva contraseña"
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar contraseña"
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('nueva_password')
        p2 = cleaned_data.get('confirmar_password')

        if p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        if len(p1) < 8 or not re.search(r'[A-Z]', p1) or not re.search(r'[0-9]', p1):
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres, una mayúscula y un número.")
        return cleaned_data