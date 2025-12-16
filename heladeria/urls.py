from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('pos/', views.pos_home, name='pos_home'),
    path('pos/ajax/', views.pos_ajax, name='pos_ajax'),
    path('add_to_cart/<int:producto_id>/', views.add_to_cart, name='add_to_cart'),
    path('confirmar_venta/', views.confirmar_venta, name='confirmar_venta'),
    path('clientes/', include('clientes.urls')),
    path('ventas/', include('ventas.urls')),
    path('productos/', include('productos.urls')),
    path('categorias/', include('categorias.urls')),
    path("reportes/", include("reportes.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
