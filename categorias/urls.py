from django.urls import path
from .views import (
    lista_categorias,
    crear_categoria_ajax,
    editar_categoria_ajax,
    desactivar_categoria, reactivar_categoria,
)

urlpatterns = [
    path("", lista_categorias, name="lista_categorias"),
path("crear/ajax/", crear_categoria_ajax, name="crear_categoria_ajax"),
path("editar/<int:categoria_id>/ajax/", editar_categoria_ajax, name="editar_categoria_ajax"),
path("desactivar/<int:categoria_id>/", desactivar_categoria, name="desactivar_categoria"),
path("reactivar/<int:categoria_id>/", reactivar_categoria, name="reactivar_categoria"),

]
