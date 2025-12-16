from django.shortcuts import render, get_object_or_404, redirect
from heladeria.models import Cliente, Venta
from django import forms
from django.core.exceptions import ValidationError
import re, json, openpyxl 
from django.utils.timezone import localtime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper
from collections import defaultdict
from decimal import Decimal
import pandas as pd
from django.utils.timezone import make_naive
from clientes.forms import ClienteForm
from heladeria.decorators import grupo_requerido

@login_required
def lista_clientes(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "nombre")
    direction = request.GET.get("direction", "asc")

    try:
        per_page = int(request.GET.get("per_page", "10"))
    except ValueError:
        per_page = 10

    clientes = Cliente.objects.all()

    if query:
        clientes = clientes.filter(
            Q(rut__icontains=query) |
            Q(nombre__icontains=query) |
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
def lista_clientes_ajax(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "nombre")
    direction = request.GET.get("direction", "asc")

    try:
        per_page = int(request.GET.get("per_page", "10"))
    except ValueError:
        per_page = 10

    clientes = Cliente.objects.all()

    if query:
        clientes = clientes.filter(
            Q(rut__icontains=query) |
            Q(nombre__icontains=query) |
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

    html = render(
        request,
        "clientes/_tabla_clientes.html",
        {
            "page_obj": page_obj,
            "query": query,
            "sort": sort,
            "direction": direction,
            "next_direction": "desc" if direction == "asc" else "asc",
            "per_page": per_page,
            "total_clientes": paginator.count,
        }
    ).content.decode("utf-8")

    return JsonResponse({"html": html})

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

    # Pasar JSON de regiones/comunas al template
    from clientes.forms import CHILE_DATA
    regiones_comunas_json = json.dumps(CHILE_DATA["regiones"])

    return render(request, 'clientes/form_cliente.html', {
        'form': form,
        'accion': 'Crear',
        'mensaje': mensaje,
        'tipo_mensaje': tipo_mensaje,
        'regiones_comunas_json': regiones_comunas_json,  # <- nombre consistente con JS
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

    # Pasar JSON de regiones/comunas al template
    from clientes.forms import CHILE_DATA
    regiones_comunas_json = json.dumps(CHILE_DATA["regiones"])

    return render(request, 'clientes/form_cliente.html', {
        'form': form,
        'accion': 'Editar',
        'mensaje': mensaje,
        'tipo_mensaje': tipo_mensaje,
        'regiones_comunas_json': regiones_comunas_json,  # <- nombre consistente con JS
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

def _get_filtered_queryset_cliente(cliente, params):
    ventas = (
        Venta.objects
        .filter(
            cliente=cliente,
            estado__in=["COMPLETED", "PENDING", "CANCELLED"]
        )
        .annotate(
            total_calculado=Sum(
                ExpressionWrapper(
                    F("detalleventa__cantidad") * F("detalleventa__producto__precio"),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )
        .order_by("-fecha")
        .prefetch_related("detalleventa_set__producto")
    )

    estado = params.get("estado")
    if estado:
        ventas = ventas.filter(estado=estado)

    min_precio = params.get("min_precio")
    if min_precio:
        try:
            ventas = ventas.filter(total_calculado__gte=float(min_precio))
        except ValueError:
            pass

    max_precio = params.get("max_precio")
    if max_precio:
        try:
            ventas = ventas.filter(total_calculado__lte=float(max_precio))
        except ValueError:
            pass

    total_pedidos = ventas.count()
    total_compras = ventas.aggregate(
        total=Sum("total_calculado")
    )["total"] or 0

    avg_order_value = (
        round(total_compras / total_pedidos, 2)
        if total_pedidos else 0
    )

    stats = {
        "total_pedidos": total_pedidos,
        "total_compras": float(total_compras),
        "avg_order_value": avg_order_value,
    }

    return ventas, stats

@login_required
def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    ventas, stats = _get_filtered_queryset_cliente(cliente, request.GET)

    if request.GET.get("export") == "excel":
        rows = [
            {
                "ID Venta": v.id,
                "Fecha": make_naive(v.fecha),
                "Estado": v.estado,
                "Total": float(v.total_calculado or 0),
            }
            for v in ventas
        ]

        df = pd.DataFrame(rows)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="detalle_cliente_{cliente.id}.xlsx"'
        )
        df.to_excel(response, index=False)
        return response

    gastos_por_mes = defaultdict(Decimal)
    total_por_mes = defaultdict(Decimal)

    for v in ventas:
        key = localtime(v.fecha).strftime("%Y-%m")
        gastos_por_mes[key] += Decimal(str(v.total_calculado or 0))
        total_por_mes[key] += Decimal(str(v.total_calculado or 0))

    monthly_labels = list(gastos_por_mes.keys())
    monthly_avg_spend = [
        float(round(
            gastos_por_mes[m] /
            (ventas.filter(
                fecha__year=m.split("-")[0],
                fecha__month=m.split("-")[1]
            ).count() or 1),
            2
        ))
        for m in monthly_labels
    ]
    monthly_total_spend = [float(round(total_por_mes[m], 2)) for m in monthly_labels]

    productos = defaultdict(int)
    total_items = 0

    for v in ventas:
        for d in v.detalleventa_set.all():
            productos[d.producto.nombre] += d.cantidad
            total_items += d.cantidad

    product_labels, product_counts, otros = [], [], 0

    for nombre, cantidad in productos.items():
        porcentaje = (cantidad / total_items) * 100 if total_items else 0
        if porcentaje < 5:
            otros += cantidad
        else:
            product_labels.append(nombre)
            product_counts.append(cantidad)

    if otros:
        product_labels.append("Otros")
        product_counts.append(otros)

    return render(request, "clientes/detalle_cliente.html", {
        "cliente": cliente,
        "ventas": ventas,

        "total_pedidos": stats["total_pedidos"],
        "total_compras": stats["total_compras"],
        "avg_order_value": stats["avg_order_value"],

        "monthly_labels": json.dumps(monthly_labels),
        "monthly_avg_spend": json.dumps(monthly_avg_spend),
        "monthly_total_spend": json.dumps(monthly_total_spend),

        "product_labels": json.dumps(product_labels),
        "product_counts": json.dumps(product_counts),
    })

@login_required
def detalle_cliente_ajax(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    ventas, _ = _get_filtered_queryset_cliente(cliente, request.GET)

    try:
        page_size = int(request.GET.get("page_size", 5))
    except ValueError:
        page_size = 5

    paginator = Paginator(ventas, page_size)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    html = render(
        request,
        "clientes/_tabla_detalle_cliente.html",
        {
            "page_obj": page_obj,
            "page_size": page_size,
            "request": request,
        }
    ).content.decode("utf-8")

    return JsonResponse({"html": html})
