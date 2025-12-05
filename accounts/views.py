from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PerfilUsuarioForm, UserForm, CambiarPasswordForm
from django.contrib.auth import update_session_auth_hash
from .forms import LoginForm

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            grupo, creado = Group.objects.get_or_create(name="Editor")
            user.groups.add(grupo)

            messages.success(request, "Cuenta creada correctamente. ¡Ahora inicia sesión!")
            return redirect("login")
    else:
        form = UserCreationForm()

    # Estilos IGUALES a la página de login
    form.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Nombre de usuario"})
    form.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Contraseña"})
    form.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Repetir contraseña"})

    return render(request, "accounts/register.html", {"form": form})

@login_required
def perfil_usuario(request):
    perfil = request.user.perfilusuario
    if request.method == 'POST':
        uform = UserForm(request.POST, instance=request.user)
        pform = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('perfil_usuario')
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        uform = UserForm(instance=request.user)
        pform = PerfilUsuarioForm(instance=perfil)

    return render(request, 'accounts/perfil.html', {'uform': uform, 'pform': pform})


@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = CambiarPasswordForm(request.POST)
        if form.is_valid():
            nueva = form.cleaned_data['nueva_password']
            user = request.user
            user.set_password(nueva)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Contraseña cambiada correctamente.")
            return redirect('perfil_usuario')
        else:
            messages.error(request, "Revisa las contraseñas ingresadas.")
    else:
        form = CambiarPasswordForm()

    return render(request, 'accounts/cambiar_password.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/heladeria/"