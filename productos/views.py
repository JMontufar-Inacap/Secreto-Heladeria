from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from heladeria.models import Producto, DetalleVenta
from .forms import ProductoForm
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.timezone import make_naive
import openpyxl, json
import pandas as pd
from heladeria.decorators import grupo_requerido

@grupo_requerido('Admin')
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

@grupo_requerido('Admin')
@login_required
def lista_productos_ajax(request):

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

    if stock == "1":        # con stock
        productos = productos.filter(stock__gt=0)
    elif stock == "0":      # sin stock
        productos = productos.filter(stock=0)

    if direction == "desc":
        productos = productos.order_by(f"-{sort}")
    else:
        productos = productos.order_by(sort)

    paginator = Paginator(productos, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    html = render_to_string("productos/_tabla_productos.html", {
        "page_obj": page_obj,
        "productos": page_obj.object_list,
        "query": query,
        "sort": sort,
        "direction": direction,
        "next_direction": "desc" if direction == "asc" else "asc",
        "per_page": per_page,
        "stock": stock,
    }, request=request)

    return JsonResponse({"html": html})

@grupo_requerido('Admin')
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

@grupo_requerido('Admin')
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

@grupo_requerido('Admin')
@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    return redirect('lista_productos')

@grupo_requerido('Admin')
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

@grupo_requerido('Admin')
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

from django.db.models import F, ExpressionWrapper, DecimalField, Sum

def _get_filtered_queryset(producto, params):
    detalles = (
        DetalleVenta.objects
        .filter(
            producto=producto,
            venta__estado__in=["PENDING", "COMPLETED"]
        )
        .select_related("venta", "producto")
        .annotate(
            recaudacion=ExpressionWrapper(
                F("cantidad") * F("producto__precio"),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
    )

    ventas_validas = detalles.order_by("-venta__fecha")

    ventas_completadas = ventas_validas.filter(venta__estado="COMPLETED")

    total_vendido = ventas_completadas.aggregate(
        total=Sum("cantidad")
    )["total"] or 0

    total_ganado = ventas_completadas.aggregate(
        total=Sum("recaudacion")
    )["total"] or 0

    ventas_pendientes = ventas_validas.filter(venta__estado="PENDING")

    unidades_pendientes = ventas_pendientes.aggregate(
        total=Sum("cantidad")
    )["total"] or 0

    ingreso_pendiente = ventas_pendientes.aggregate(
        total=Sum("recaudacion")
    )["total"] or 0

    ingreso_potencial = total_ganado + ingreso_pendiente
    filtered = detalles

    estado = params.get("estado")
    if estado in ["PENDING", "COMPLETED"]:
        filtered = filtered.filter(venta__estado=estado)

    min_cantidad = params.get("min_cantidad")
    if min_cantidad:
        try:
            filtered = filtered.filter(cantidad__gte=int(min_cantidad))
        except ValueError:
            pass

    max_cantidad = params.get("max_cantidad")
    if max_cantidad:
        try:
            filtered = filtered.filter(cantidad__lte=int(max_cantidad))
        except ValueError:
            pass

    min_precio = params.get("min_precio")
    if min_precio:
        try:
            filtered = filtered.filter(recaudacion__gte=float(min_precio))
        except ValueError:
            pass

    max_precio = params.get("max_precio")
    if max_precio:
        try:
            filtered = filtered.filter(recaudacion__lte=float(max_precio))
        except ValueError:
            pass

    stats = {
        "total_vendido": total_vendido,
        "total_ganado": float(total_ganado),
        "unidades_pendientes": unidades_pendientes,
        "ingreso_pendiente": float(ingreso_pendiente),
        "ingreso_potencial": float(ingreso_potencial),
        "ventas_validas_qs": ventas_validas,
    }

    return filtered, stats

@grupo_requerido('Admin')
@login_required
def detalle_productos(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    filtered, stats = _get_filtered_queryset(producto, request.GET)

    if request.GET.get("export") == "excel":
        import pandas as pd
        from django.http import HttpResponse

        registros = []

        for item in filtered.select_related("venta", "producto"):
            registros.append({
                "ID Venta": item.venta.id,
                "Fecha": make_naive(item.venta.fecha),
                "Cantidad": item.cantidad,
                "Subtotal": item.producto.precio * item.cantidad,
                "Estado": item.venta.estado,
            })

        df = pd.DataFrame(registros)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename=\"detalle_producto_{producto.id}.xlsx\"'  # noqa

        df.to_excel(response, index=False)
        return response


    try:
        page_size = int(request.GET.get("page_size", 5))
    except:
        page_size = 5


    paginator = Paginator(filtered.order_by("-venta__fecha"), page_size)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    querydict = request.GET.copy()
    if "page" in querydict:
        del querydict["page"]
    querystring = querydict.urlencode()

    querydict_no_page = querydict.copy()
    if "page_size" in querydict_no_page:
        del querydict_no_page["page_size"]
    querystring_no_page = querydict_no_page.urlencode()

    return render(request, "productos/detalle_productos.html", {
        "producto": producto,
        "page_obj": page_obj,
        "page_size": page_size,
        "querystring": querystring,
        "querystring_no_page": querystring_no_page,

        "total_vendido": stats["total_vendido"],
        "total_ganado": stats["total_ganado"],
        "unidades_pendientes": stats["unidades_pendientes"],

        "ingreso_pendiente": stats["ingreso_pendiente"],
        "ingreso_potencial": stats["ingreso_potencial"],

        "ventas": stats["ventas_validas_qs"],
    })

@grupo_requerido('Admin')
@login_required
def detalle_productos_ajax(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    filtered, stats = _get_filtered_queryset(producto, request.GET)

    if request.GET.get("export") == "excel":
        rows = []
        for d in filtered.order_by("-venta__fecha"):
            rows.append({
                "Fecha": d.venta.fecha,
                "Estado": d.venta.estado,
                "Cantidad": d.cantidad,
                "Precio": float(d.producto.precio),
                "Subtotal": float(d.subtotal()),
            })
        df = pd.DataFrame(rows)
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="detalle_{producto.id}.xlsx"'
        df.to_excel(response, index=False)
        return response

    try:
        page_size = int(request.GET.get("page_size", 5))
    except:
        page_size = 5

    paginator = Paginator(filtered.order_by("-venta__fecha"), page_size)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    querydict = request.GET.copy()
    if "page" in querydict:
        del querydict["page"]
    querystring = querydict.urlencode()

    querydict_no_page = querydict.copy()
    if "page_size" in querydict_no_page:
        del querydict_no_page["page_size"]
    querystring_no_page = querydict_no_page.urlencode()

    html = render_to_string("productos/_tabla_detalle_productos.html", {
        "page_obj": page_obj,
        "paginator": paginator,
        "page_size": page_size,
        "querystring": querystring,
        "querystring_no_page": querystring_no_page,
    }, request=request)

    return JsonResponse({
        "html": html,
        "stats": {
            "total_vendido": stats["total_vendido"],
            "total_ganado": f"{int(stats['total_ganado']):,}".replace(",", "."),
            "ingreso_potencial": f"{int(stats['ingreso_potencial']):,}".replace(",", "."),
        }
    })

@grupo_requerido('Admin')
@login_required
def graficos_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    ventas = DetalleVenta.objects.filter(producto=producto).select_related("venta")

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
