from django.urls import path
from .views import CustomLoginView
from django.contrib.auth.views import LogoutView
from . import views
from .views import register

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),

    path("register/", views.register, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("perfil/", views.perfil_usuario, name="perfil_usuario"),
    path("cambiar_password/", views.cambiar_password, name="cambiar_password"),
    path("register/", register, name="register"),
]
