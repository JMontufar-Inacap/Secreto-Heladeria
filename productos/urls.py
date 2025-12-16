from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('crear/', views.crear_producto, name='crear_producto'),
    path('<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('<int:pk>/', views.detalle_productos, name='detalle_productos'),
    path("<int:pk>/ajax/", views.detalle_productos_ajax, name="detalle_productos_ajax"),
    path('<int:pk>/graficos/', views.graficos_producto, name='graficos_producto'),
    path('exportar/', views.exportar_productos_excel, name='exportar_productos_excel'),
    path('eliminar-multiples/', views.eliminar_productos_multiples, name='eliminar_productos_multiples'),
    path('ajax/', views.lista_productos_ajax, name='lista_productos_ajax'),
]
