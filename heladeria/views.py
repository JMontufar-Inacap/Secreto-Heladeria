from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timezone import now, timedelta
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.db.models import Sum, F, Q
from django.contrib import messages
from datetime import timedelta, datetime
from .models import Producto, Venta, DetalleVenta, Cliente
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "heladeria/pos_home.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        productos = Producto.objects.filter(state="ACTIVE")
        ventas = Venta.objects.filter(usuario=self.request.user)

        total_ventas = ventas.count()
        total_productos = productos.count()
        total_stock = sum([p.stock for p in productos])
        total_ganancias = sum([v.total() for v in ventas])

        context.update({
            'total_ventas': total_ventas,
            'total_productos': total_productos,
            'total_stock': total_stock,
            'total_ganancias': total_ganancias,
        })

        return context


@login_required
def pos_home(request):
    q = (request.GET.get("q") or "").strip()
    productos_qs = Producto.objects.filter(state="ACTIVE").order_by("nombre")

    if q:
        productos_qs = productos_qs.filter(Q(nombre__icontains=q))

    per_page = request.GET.get("per_page", 8)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 8

    paginator = Paginator(productos_qs, per_page)
    page_number = request.GET.get("page")

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    venta, created = Venta.objects.get_or_create(usuario=request.user, estado='CART')
    detalles_venta = DetalleVenta.objects.filter(venta=venta)

    total_ventas = Venta.objects.filter(usuario=request.user).count()
    total_productos = productos_qs.count()
    clientes = Cliente.objects.all()
    total_stock = sum([p.stock for p in productos_qs])
    total_ganancias = sum([v.total() for v in Venta.objects.filter(usuario=request.user)])

    total_carrito = 0
    total_carrito = sum(d.subtotal() for d in detalles_venta)


    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

    context = {
        'clientes': clientes,
        'productos': page_obj.object_list,
        'page_obj': page_obj,
        'detalles_venta': detalles_venta,
        'total_ventas': total_ventas,
        'total_productos': total_productos,
        'total_stock': total_stock,
        'total_ganancias': total_ganancias,
        'total_carrito': total_carrito,
        'query': q,
        'querystring': querystring,
        'per_page': per_page, 
    }

    if request.method == "POST" and 'confirmar_venta' in request.POST:
        venta.estado = 'COMPLETED'
        venta.fecha_venta = timezone.now()
        venta.save()
        messages.success(request, "La venta ha sido confirmada.")
        return redirect('pos_home')

    return render(request, "heladeria/pos_home.html", context)

@login_required
def pos_ajax(request):
    q = (request.GET.get("q") or "").strip()
    per_page = request.GET.get("per_page", 8)
    page = request.GET.get("page", 1)

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 8

    productos_qs = Producto.objects.filter(state="ACTIVE").order_by("nombre")
    if q:
        productos_qs = productos_qs.filter(nombre__icontains=q)

    paginator = Paginator(productos_qs, per_page)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        "productos": page_obj.object_list,
        "page_obj": page_obj,
        "query": q,
        "per_page": per_page,
    }

    html = render_to_string("heladeria/_pos_parcial.html", context, request=request)
    return HttpResponse(html)

@login_required
def confirmar_venta(request):
    if request.method == "POST":
        try:
            carrito_json = request.POST.get("carrito_json", "{}")
            carrito = json.loads(carrito_json)

            if not carrito:
                messages.warning(request, "El carrito está vacío.")
                return redirect("pos_home")

            cliente_id = request.POST.get("cliente")
            cliente = None
            if cliente_id:
                cliente = Cliente.objects.filter(id=cliente_id).first()

            venta = Venta.objects.create(
                usuario=request.user,
                cliente=cliente, 
                estado="PENDING"
            )

            for producto_id, item in carrito.items():
                try:
                    producto = Producto.objects.get(pk=producto_id, state="ACTIVE")
                    cantidad = int(item.get("cantidad", 1))
                    cantidad = max(cantidad, 1)

                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio,
                        precio_compra=producto.precio_compra
                    )


                    producto.stock = max(producto.stock - cantidad, 0)
                    producto.save()

                except Producto.DoesNotExist:
                    continue  

            
            return redirect("pos_home")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar la venta: {e}")
            return redirect("pos_home")

    return redirect("pos_home")

@login_required
def products_list(request):
    productos = Producto.objects.filter(state="ACTIVE")
    return render(request, "heladeria/products_list.html", {'productos': productos})

@login_required
def ventas_list(request):
    ventas = Venta.objects.filter(usuario=request.user)
    return render(request, "ventas/lista_ventas.html", {'ventas': ventas})

@login_required
def venta_detail(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id, usuario=request.user)
    detalles = DetalleVenta.objects.filter(venta=venta)
    return render(request, "heladeria/venta_detail.html", {'venta': venta, 'detalles': detalles})

@login_required
def add_to_cart(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    venta, created = Venta.objects.get_or_create(usuario=request.user, estado='CART')
    detalle, created = DetalleVenta.objects.get_or_create(venta=venta, producto=producto)
    if not created:
        detalle.cantidad += 1
    else:
        detalle.cantidad = 1
    
    detalle.save()

    if request.method == "POST" and 'confirmar_venta' in request.POST:
        venta.estado = 'COMPLETED'
        venta.fecha_venta = timezone.now()
        venta.save()

        messages.success(request, f"La venta de {producto.nombre} ha sido confirmada.")
        return redirect('pos_home')

    messages.success(request, f"{producto.nombre} ha sido agregado al carrito.")
    return redirect('pos_home')

def get_venta_actual(user):
    venta, created = Venta.objects.get_or_create(usuario=user, estado='PENDING')
    detalles = DetalleVenta.objects.filter(venta=venta)
    total = sum(d.subtotal() for d in detalles)
    return venta, detalles, total


@login_required
def listar_productos(request):
    q = (request.GET.get("q") or "").strip()
    productos_qs = Producto.objects.filter(state="ACTIVE").order_by("nombre")

    if q:
        productos_qs = productos_qs.filter(Q(nombre__icontains=q))

    paginator = Paginator(productos_qs, 8)
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    venta, detalles_venta, total_carrito = get_venta_actual(request.user)

    context = {
        "page_obj": page_obj,
        "productos": page_obj.object_list,
        "query": q,
        "total": productos_qs.count(),
        "detalles_venta": detalles_venta,
        "total_carrito": total_carrito,
    }
    return render(request, "heladeria/listar_productos.html", context)

@login_required
def reportes_ventas(request):
    productos = Producto.objects.filter(state="ACTIVE")

    producto_id = request.GET.get("producto")
    periodo = request.GET.get("periodo", "dia")
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    ventas = Venta.objects.filter(estado="COMPLETED")

    hoy = now()
    if periodo == "dia":
        ventas = ventas.filter(fecha__date=hoy.date())
    elif periodo == "semana":
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        ventas = ventas.filter(fecha__date__gte=inicio_semana.date())
    elif periodo == "mes":
        ventas = ventas.filter(fecha__month=hoy.month, fecha__year=hoy.year)
    elif periodo == "año":
        ventas = ventas.filter(fecha__year=hoy.year)
    elif periodo == "personalizado" and fecha_inicio and fecha_fin:
        try:
            f1 = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            f2 = datetime.strptime(fecha_fin, "%Y-%m-%d")
            ventas = ventas.filter(fecha__date__range=[f1, f2])
        except:
            pass

    if producto_id and producto_id != "todos":
        ventas = ventas.filter(detalleventa__producto_id=producto_id)

    detalles = DetalleVenta.objects.filter(venta__in=ventas)

    if producto_id and producto_id != "todos":
        detalles = detalles.filter(producto_id=producto_id)

    resumen = detalles.values("producto__nombre").annotate(
        total_vendido=Sum(F("cantidad") * F("producto__precio")),
        unidades_vendidas=Sum("cantidad")
    )

    total_general = sum([r["total_vendido"] or 0 for r in resumen])

    context = {
        "productos": productos,
        "resumen": resumen,
        "total_general": total_general,
        "producto_seleccionado": producto_id,
        "periodo": periodo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }

    return render(request, "heladeria/reportes_ventas.html", context)