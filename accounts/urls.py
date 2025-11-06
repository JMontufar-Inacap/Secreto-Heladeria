from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from .forms import LoginForm

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
            authentication_form=LoginForm,
        ),
        name="login",
    ),
    path("register/", views.register, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('cambiar_password/', views.cambiar_password, name='cambiar_password'),
]