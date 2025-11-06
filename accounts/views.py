from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PerfilUsuarioForm, UserForm, CambiarPasswordForm
from django.contrib.auth import update_session_auth_hash

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def perfil_usuario(request):
    perfil = request.user.perfilusuario
    if request.method == 'POST':
        uform = UserForm(request.POST, instance=request.user)
        pform = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, "✅ Perfil actualizado correctamente.")
            return redirect('perfil_usuario')
        else:
            messages.error(request, "❌ Corrige los errores del formulario.")
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
            messages.success(request, "🔒 Contraseña cambiada correctamente.")
            return redirect('perfil_usuario')
        else:
            messages.error(request, "❌ Revisa las contraseñas ingresadas.")
    else:
        form = CambiarPasswordForm()

    return render(request, 'accounts/cambiar_password.html', {'form': form})
