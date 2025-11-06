from django.contrib import admin
from django.urls import path, include
from heladeria.views import DashboardView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', DashboardView.as_view(), name='dashboard'),

    path('accounts/', include('accounts.urls')),

    path('heladeria/', include('heladeria.urls')),

    # Aquí registramos la app de ventas correctamente con namespace
    path('ventas/', include(('ventas.urls', 'ventas'), namespace='ventas')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)