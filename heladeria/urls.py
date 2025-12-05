from django.urls import path, include
from . import views
from django.contrib import admin
from heladeria.views import dashboard
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.dashboard, name='dashboard'), 
    path('add_to_cart/<int:producto_id>/', views.add_to_cart, name='add_to_cart'),
    path('accounts/', include("accounts.urls")),
    path('confirmar_venta/', views.confirmar_venta, name='confirmar_venta'),
    path('reportes/', views.reportes_ventas, name='reportes_ventas'),
    path('clientes/', include('clientes.urls')),
    path('ventas/', include('ventas.urls')),
    path('productos/', include('productos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)