from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignupForm
from django.urls import reverse
from django.contrib.auth.models import Group

def inscription(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé. Connectez-vous.")
            return redirect('connexion')
    else:
        form = SignupForm()
    return render(request, 'inscription.html', {'form': form})

def connexion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(dashboard_redirect(user))
        messages.error(request, 'Nom d’utilisateur ou mot de passe invalide.')
    else:
        form = AuthenticationForm(request)
    return render(request, 'connexion.html', {'form': form})

def is_admin(user):
    return user.is_active and user.is_superuser

def is_client(user):
    return user.is_active and user.groups.filter(name="Client").exists() 


def dashboard_redirect(user):
    if is_admin(user):
        return reverse("admin_dashboard")
    if is_client(user):
        return reverse("client_dashboard")
    # fallback: si aucun groupe
    return reverse("connexion")

def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')
def client_dashboard(request):
    return render(request, 'client_dashboard.html')

def deconnexion(request):
    logout(request)
    return redirect('connexion')