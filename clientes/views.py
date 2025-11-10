from django.shortcuts import render, get_object_or_404, redirect
from heladeria.models import Cliente
from django import forms
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.decorators import login_required
import openpyxl
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'direccion', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        if not nombre:
            raise ValidationError("El nombre no puede estar vacío.")
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
            raise ValidationError("El nombre solo puede contener letras y espacios.")
        return nombre

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


@login_required
def lista_clientes(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "nombre")
    direction = request.GET.get("direction", "asc")
    per_page = request.GET.get("per_page", "10")

    # Convertir a int con fallback
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    clientes = Cliente.objects.all()

    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query) |
            Q(direccion__icontains=query) |
            Q(telefono__icontains=query) |
            Q(email__icontains=query)
        )

    if direction == "desc":
        clientes = clientes.order_by(f"-{sort}")
    else:
        clientes = clientes.order_by(sort)

    paginator = Paginator(clientes, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    next_direction = "desc" if direction == "asc" else "asc"

    return render(request, "clientes/lista_clientes.html", {
        "page_obj": page_obj,
        "clientes": page_obj.object_list,
        "query": query,
        "sort": sort,
        "direction": direction,
        "next_direction": next_direction,
        "per_page": per_page,
        "total_clientes": paginator.count,
    })


@login_required
def crear_cliente(request):
    mensaje = None
    tipo_mensaje = None

    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            mensaje = "Cliente creado exitosamente."
            tipo_mensaje = "success"
        else:
            mensaje = "Por favor corrige los errores del formulario."
            tipo_mensaje = "error"
    else:
        form = ClienteForm()

    return render(request, 'clientes/form_cliente.html', {
        'form': form,
        'accion': 'Crear',
        'mensaje': mensaje,
        'tipo_mensaje': tipo_mensaje
    })

@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    mensaje = None
    tipo_mensaje = None

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            mensaje = "Cliente actualizado correctamente."
            tipo_mensaje = "success"
        else:
            mensaje = "Por favor corrige los errores del formulario."
            tipo_mensaje = "error"
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'clientes/form_cliente.html', {
        'form': form,
        'accion': 'Editar',
        'mensaje': mensaje,
        'tipo_mensaje': tipo_mensaje
    })

@login_required
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'clientes/eliminar_cliente.html', {'cliente': cliente})

@login_required
def exportar_clientes_excel(request):
    clientes = Cliente.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Clientes"

    ws.append(["Nombre", "Dirección", "Teléfono", "Email", "Fecha de registro"])

    for c in clientes:
        ws.append([c.nombre, c.direccion, c.telefono, c.email, c.fecha_registro.strftime("%Y-%m-%d %H:%M")])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="clientes.xlsx"'

    wb.save(response)
    return response