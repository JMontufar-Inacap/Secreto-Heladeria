from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from heladeria.models import Venta, DetalleVenta
from django.db.models import Sum, F, Q, FloatField
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from openpyxl import Workbook
from django.http import HttpResponse

@login_required
def lista_ventas(request):
    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    sort = request.GET.get('sort', 'fecha')
    direction = request.GET.get('direction', 'desc')
    
    try:
        per_page = int(request.GET.get('per_page', '10'))
    except ValueError:
        per_page = 10

    ventas = Venta.objects.all()

    if estado:
        ventas = ventas.filter(estado=estado)

    if query:
        ventas = ventas.filter(
            Q(cliente__nombre__icontains=query) |
            Q(usuario__username__icontains=query)
        )

    ventas = ventas.annotate(
        total_calc=Sum(
            F('detalleventa__producto__precio') * F('detalleventa__cantidad'),
            output_field=FloatField()
        )
    )

    sort_field = 'total_calc' if sort == 'total' else sort
    ventas = ventas.order_by(f"-{sort_field}" if direction == "desc" else sort_field)

    paginator = Paginator(ventas, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    next_direction = "desc" if direction == "asc" else "asc"
    rangos_pagina = [5, 10, 20, 50]

    return render(request, 'ventas/lista_ventas.html', {
        'page_obj': page_obj,
        'ventas': page_obj.object_list,
        'query': query,
        'estado': estado,
        'sort': sort,
        'direction': direction,
        'next_direction': next_direction,
        'per_page': per_page,
        'rangos_pagina': rangos_pagina,
        'total_ventas': paginator.count,
    })


@login_required
def detalle_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = DetalleVenta.objects.filter(venta=venta)
    return render(request, 'ventas/detalle_venta.html', {
        'venta': venta,
        'detalles': detalles
    })

@csrf_exempt
@login_required
def cambiar_estado_venta(request, venta_id):
    if request.method == 'POST':
        venta = get_object_or_404(Venta, id=venta_id)
        nuevo_estado = "COMPLETED" if venta.estado == "PENDING" else "PENDING"
        venta.estado = nuevo_estado
        venta.save()
        return JsonResponse({
            'success': True,
            'nuevo_estado': venta.estado,
            'estado_legible': venta.get_estado_display()
        })
    return JsonResponse({'success': False})

@csrf_exempt
@login_required
def eliminar_venta(request, venta_id):
    if request.method == 'POST':
        venta = get_object_or_404(Venta, id=venta_id)
        venta.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@csrf_exempt
@login_required
def eliminar_multiples(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ids = data.get('ids', [])
        Venta.objects.filter(id__in=ids).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@csrf_exempt
@login_required
def cambiar_estado_multiples(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ids = data.get('ids', [])
        nuevo_estado = data.get('nuevo_estado')
        if nuevo_estado not in ['PENDING', 'COMPLETED']:
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
        Venta.objects.filter(id__in=ids).update(estado=nuevo_estado)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def exportar_ventas_excel(request):

    ventas = Venta.objects.annotate(
        total_calc=Sum(F('detalleventa__producto__precio') * F('detalleventa__cantidad'), output_field=FloatField())
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"

    ws.append(["ID", "Usuario", "Cliente", "Fecha", "Estado", "Total"])

    for v in ventas:
        ws.append([
            v.id,
            v.usuario.username,
            v.cliente.nombre if v.cliente else "-",
            v.fecha.strftime("%Y-%m-%d %H:%M"),
            v.get_estado_display(),
            float(v.total_calc or 0)
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="ventas.xlsx"'
    wb.save(response)
    return response