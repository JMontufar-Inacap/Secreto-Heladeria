from django.contrib import admin
from django.urls import path, include
from heladeria.views import DashboardView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', DashboardView.as_view(), name='dashboard'),  # home general
    path('accounts/', include('accounts.urls')),          # login, logout, etc.
    path('heladeria/', include('heladeria.urls')),        # todo lo de heladería / POS
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
