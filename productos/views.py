from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
import openpyxl
import json

from heladeria.models import Producto, DetalleVenta
from .forms import ProductoForm
from django.core.paginator import Paginator


@login_required
def lista_productos(request):

    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "nombre")
    direction = request.GET.get("direction", "asc")
    per_page = request.GET.get("per_page", "10")
    stock = request.GET.get("stock", "").strip()

    try:
        per_page = int(per_page)
    except:
        per_page = 10

    productos = Producto.objects.all()

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query)
        )
    if stock == "1":       # disponibles
        productos = productos.filter(stock__gt=0)
    elif stock == "0":     # sin stock
        productos = productos.filter(stock=0)

    if direction == "desc":
        productos = productos.order_by(f"-{sort}")
    else:
        productos = productos.order_by(sort)

    paginator = Paginator(productos, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    next_direction = "desc" if direction == "asc" else "asc"

    return render(request, "productos/lista_productos.html", {
        "page_obj": page_obj,
        "productos": page_obj.object_list,
        "query": query,
        "sort": sort,
        "direction": direction,
        "next_direction": next_direction,
        "per_page": per_page,
        "stock": stock,
        "total_productos": Producto.objects.count(),
        "productos_con_stock": Producto.objects.filter(stock__gt=0).count(),
        "productos_sin_stock": Producto.objects.filter(stock=0).count(),
    })


@login_required
def crear_producto(request):
    mensaje = None
    tipo_mensaje = None

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            mensaje = "Producto creado exitosamente."
            tipo_mensaje = "success"
        else:
            mensaje = "Corrige los errores del formulario."
            tipo_mensaje = "error"
    else:
        form = ProductoForm()

    return render(request, 'productos/form_productos.html', {
        'form': form,
        'accion': 'Crear',
        'mensaje': mensaje,
        'tipo_mensaje': tipo_mensaje
    })


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    mensaje = None
    tipo_mensaje = None

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            mensaje = "Producto actualizado correctamente."
            tipo_mensaje = "success"
        else:
            mensaje = "Corrige los errores del formulario."
            tipo_mensaje = "error"
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'productos/form_productos.html', {
        'form': form,
        'accion': 'Editar',
        'mensaje': mensaje,
        'tipo_mensaje': tipo_mensaje
    })


@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    return redirect('lista_productos')



@login_required
def eliminar_productos_multiples(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ids = data.get("ids", [])

            if not ids:
                return JsonResponse({"success": False, "error": "No se enviaron IDs"}, status=400)

            Producto.objects.filter(id__in=ids).delete()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)



@login_required
def exportar_productos_excel(request):
    productos = Producto.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Productos"

    ws.append(["Nombre", "Precio", "Stock"])

    for p in productos:
        ws.append([p.nombre, float(p.precio), p.stock])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="productos.xlsx"'
    wb.save(response)
    return response

@login_required
def detalle_productos(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    ventas = DetalleVenta.objects.filter(producto=producto).select_related("venta")

    total_vendido = sum(v.cantidad for v in ventas)
    total_ganado = sum(v.subtotal() for v in ventas)  # total de ingresos

    return render(request, "productos/detalle_productos.html", {
        "producto": producto,
        "ventas": ventas,
        "total_vendido": total_vendido,
        "total_ganado": total_ganado, 
    })



@login_required
def graficos_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    ventas = DetalleVenta.objects.filter(producto=producto).select_related("venta")

    # Agrupar por mes
    data_por_mes = {}

    for v in ventas:
        mes = v.venta.fecha.strftime("%Y-%m")
        data_por_mes.setdefault(mes, 0)
        data_por_mes[mes] += v.cantidad

    labels = list(data_por_mes.keys())
    data = list(data_por_mes.values())

    return render(request, "productos/graficos_producto.html", {
        "producto": producto,
        "labels": labels,
        "data": data,
    })
