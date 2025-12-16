from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, permission_required
from heladeria.models import Categoria
from heladeria.decorators import grupo_requerido

@grupo_requerido('Admin')
@login_required
def lista_categorias(request):
    query = request.GET.get("q", "")

    categorias = (
        Categoria.objects
        .annotate(total_productos=Count("productos"))
        .filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )
        .order_by("nombre")
    )

    context = {
        "categorias": categorias,
        "query": query,
    }
    return render(request, "categorias/lista_categorias.html", context)

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from heladeria.models import Categoria

@require_POST
@grupo_requerido('Admin')
def crear_categoria_ajax(request):
    nombre = request.POST.get("nombre", "").strip()
    descripcion = request.POST.get("descripcion", "").strip()

    if not nombre:
        return JsonResponse({"success": False, "error": "El nombre es obligatorio"})

    Categoria.objects.create(
        nombre=nombre,
        descripcion=descripcion
    )
    return JsonResponse({"success": True})

@require_POST
@grupo_requerido('Admin')
def editar_categoria_ajax(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    nombre = request.POST.get("nombre", "").strip()
    descripcion = request.POST.get("descripcion", "").strip()

    if not nombre:
        return JsonResponse({"success": False, "error": "El nombre es obligatorio"})

    categoria.nombre = nombre
    categoria.descripcion = descripcion
    categoria.save()

    return JsonResponse({"success": True})


@require_POST
@grupo_requerido('Admin')
def desactivar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    categoria.activa = False
    categoria.save()
    return JsonResponse({"success": True})


@require_POST
@grupo_requerido('Admin')
def reactivar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    categoria.activa = True
    categoria.save()
    return JsonResponse({"success": True})

