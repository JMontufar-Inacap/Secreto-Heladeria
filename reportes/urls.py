from django.urls import path
from .views import reporte_dashboard

urlpatterns = [
    path("", reporte_dashboard, name="reporte_dashboard"),
]
