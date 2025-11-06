from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from heladeria.models import Venta, DetalleVenta
from django.db.models import Sum, F, FloatField
import json

@login_required
def lista_ventas(request):
    estado = request.GET.get('estado', '')
    sort = request.GET.get('sort', 'fecha')
    direction = request.GET.get('direction', 'desc')
    next_direction = 'asc' if direction == 'desc' else 'desc'

    ventas = Venta.objects.all()

    if estado:
        ventas = ventas.filter(estado=estado)

    ventas = ventas.annotate(
        total_calc=Sum(F('detalleventa__producto__precio') * F('detalleventa__cantidad'), output_field=FloatField())
    )

    sort_field = 'total_calc' if sort == 'total' else sort

    if direction == 'desc':
        ventas = ventas.order_by(f'-{sort_field}')
    else:
        ventas = ventas.order_by(sort_field)

    context = {
        'ventas': ventas,
        'estado': estado,
        'sort': sort,
        'direction': direction,
        'next_direction': next_direction,
    }
    return render(request, 'ventas/lista_ventas.html', context)

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
