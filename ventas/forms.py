from django import forms
from heladeria.models import Venta

class VentaEstadoForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['estado']
        labels = {'estado': 'Estado de la venta'}
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }
