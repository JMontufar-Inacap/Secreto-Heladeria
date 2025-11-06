from django import forms
from heladeria.models import Cliente

class SeleccionarClienteForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(estado="ACTIVE"),
        label="Selecciona un cliente",
        required=True
    )