from django.shortcuts import render, get_object_or_404, redirect
from heladeria.models import Cliente, Venta
from django import forms
from django.core.exceptions import ValidationError
import re, json
from django.utils.timezone import localtime
from django.contrib.auth.decorators import login_required
import openpyxl
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, F
from collections import defaultdict
import json
from decimal import Decimal

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut', 'nombre', 'direccion', 'telefono', 'email']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
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

    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '')

        if not re.match(r'^[0-9]+-[0-9Kk]$', rut):
            raise ValidationError("El RUT debe tener el formato: números-guion-dígito (0-9 o K). Ej: 12345678-5")

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


@login_required
def lista_clientes(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "nombre")
    direction = request.GET.get("direction", "asc")

    # PER PAGE
    try:
        per_page = int(request.GET.get("per_page", "10"))
    except ValueError:
        per_page = 10

    # Query base
    clientes = Cliente.objects.all()

    # BUSCADOR
    if query:
        clientes = clientes.filter(
            Q(rut__icontains=query) |
            Q(nombre__icontains=query) |
            Q(direccion__icontains=query) |
            Q(telefono__icontains=query) |
            Q(email__icontains=query)
        )

    # ORDEN
    if direction == "desc":
        clientes = clientes.order_by(f"-{sort}")
    else:
        clientes = clientes.order_by(sort)

    paginator = Paginator(clientes, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    next_direction = "desc" if direction == "asc" else "asc"
    rangos_pagina = [5, 10, 20, 50]

    return render(request, "clientes/lista_clientes.html", {
        "page_obj": page_obj,
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
def eliminar_cliente(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            if not email:
                return JsonResponse({'success': False, 'error': 'Email no proporcionado'}, status=400)

            cliente = Cliente.objects.filter(email=email).first()
            if not cliente:
                return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)

            cliente.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def exportar_clientes_excel(request):
    clientes = Cliente.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Clientes"

    ws.append(["RUT", "Nombre", "Dirección", "Teléfono", "Email", "Fecha de registro"])

    for c in clientes:
        ws.append([c.rut, c.nombre, c.direccion, c.telefono, c.email, c.fecha_registro.strftime("%Y-%m-%d %H:%M")])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="clientes.xlsx"'

    wb.save(response)
    return response

@login_required
def eliminar_clientes_multiples(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            emails = data.get("emails", [])

            if not emails:
                return JsonResponse({"success": False, "error": "No se enviaron emails"}, status=400)

            Cliente.objects.filter(email__in=emails).delete()
            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    ventas = (
        Venta.objects.filter(cliente=cliente, estado__in=["COMPLETED", "PENDING"])
        .order_by('-fecha')
        .prefetch_related('detalleventa_set__producto')
    )

    # -----------------------------
    # ESTADÍSTICAS BÁSICAS
    # -----------------------------
    total_pedidos = ventas.count()
    total_compras = sum(v.total() for v in ventas)
    avg_order_value = round(total_compras / total_pedidos, 2) if total_pedidos > 0 else 0

    # -----------------------------
    # AGRUPAR POR MES (AAAA-MM)
    # -----------------------------
    gastos_por_mes = defaultdict(lambda: Decimal("0"))
    total_por_mes = defaultdict(lambda: Decimal("0"))


    for v in ventas:
        fecha_local = localtime(v.fecha)
        clave_mes = fecha_local.strftime("%Y-%m")  # Ej: "2025-11"

        gastos_por_mes[clave_mes] += Decimal(str(v.total()))
        total_por_mes[clave_mes] += Decimal(str(v.total()))


    monthly_labels = list(gastos_por_mes.keys())
    monthly_avg_spend = [
        float(round(gastos_por_mes[m] / (
            ventas.filter(
                fecha__year=m.split("-")[0],
                fecha__month=m.split("-")[1]
            ).count() or 1
        ), 2))
        for m in monthly_labels
    ]

    monthly_total_spend = [float(round(total_por_mes[m], 2)) for m in monthly_labels]


    # -----------------------------
    # PRODUCTOS MÁS COMPRADOS
    # -----------------------------
    productos = defaultdict(int)
    total_items = 0

    for v in ventas:
        for d in v.detalleventa_set.all():
            productos[d.producto.nombre] += d.cantidad
            total_items += d.cantidad

    product_labels = []
    product_counts = []

    otros_count = 0

    for nombre, cantidad in productos.items():
        porcentaje = (cantidad / total_items) * 100 if total_items > 0 else 0
        if porcentaje < 5:
            otros_count += cantidad
        else:
            product_labels.append(nombre)
            product_counts.append(cantidad)

    if otros_count > 0:
        product_labels.append("Otros")
        product_counts.append(otros_count)

    # Convertir a JSON-safe
    monthly_labels = json.dumps(monthly_labels)
    monthly_avg_spend = json.dumps(monthly_avg_spend)
    monthly_total_spend = json.dumps(monthly_total_spend)
    product_labels = json.dumps(product_labels)
    product_counts = json.dumps(product_counts)

    return render(request, "clientes/detalle_cliente.html", {
        "cliente": cliente,
        "ventas": ventas,
        "total_pedidos": total_pedidos,
        "total_compras": total_compras,
        "avg_order_value": avg_order_value,

        # Datos para los gráficos
        "monthly_labels": monthly_labels,
        "monthly_avg_spend": monthly_avg_spend,
        "monthly_total_spend": monthly_total_spend,

        "product_labels": product_labels,
        "product_counts": product_counts,
    })

