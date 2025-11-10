from django.urls import path
from . import views


urlpatterns = [
    path('', views.lista_ventas, name='lista_ventas'),
    path('<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('<int:venta_id>/cambiar_estado_venta/', views.cambiar_estado_venta, name='cambiar_estado_venta'),
    path('<int:venta_id>/eliminar/', views.eliminar_venta, name='eliminar_venta'),
    path('eliminar-multiples/', views.eliminar_multiples, name='eliminar_multiples'),
    path('cambiar-estado-multiples/', views.cambiar_estado_multiples, name='cambiar_estado_multiples'),
    path('exportar/', views.exportar_ventas_excel, name='exportar_ventas_excel'),
]