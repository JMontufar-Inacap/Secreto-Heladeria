from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_clientes, name='lista_clientes'),
    path('nuevo/', views.crear_cliente, name='crear_cliente'),
    path('editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    path('exportar/', views.exportar_clientes_excel, name='exportar_clientes_excel'),
    path("eliminar-multiples/", views.eliminar_clientes_multiples, name="eliminar_clientes_multiples"),
    path('<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
]
