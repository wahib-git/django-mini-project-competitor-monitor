from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from django.contrib.auth.models import Group
from .forms import SignupForm

def home(request):
    """
    Page d'accueil publique (landing page)
    Redirige vers le dashboard si l'utilisateur est déjà connecté
    """
    if request.user.is_authenticated:
        return redirect(dashboard_redirect(request.user))
    return render(request, 'home.html')

def inscription(request):
    if request.user.is_authenticated:
        return redirect(dashboard_redirect(request.user))
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès ! Connectez-vous.")
            return redirect('connexion')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = SignupForm()
    return render(request, 'inscription.html', {'form': form})

def connexion(request):
    if request.user.is_authenticated:
        return redirect(dashboard_redirect(request.user))
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenue, {user.username} !")
            return redirect(dashboard_redirect(user))
        messages.error(request, 'Nom d’utilisateur ou mot de passe invalide.')
    else:
        form = AuthenticationForm(request)
    return render(request, 'connexion.html', {'form': form})

def is_admin(user):
    return user.is_active and (user.is_superuser or user.groups.filter(name="Admin").exists())

def is_client(user):
    return user.is_active and user.groups.filter(name="Client").exists() and not is_admin(user)

def dashboard_redirect(user):
    if is_admin(user):
        return reverse("admin_dashboard")
    if is_client(user):
        return reverse("client_dashboard")
    return reverse("connexion")

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

@login_required
@user_passes_test(is_client)
def client_dashboard(request):
    return render(request, 'client_dashboard.html')

def deconnexion(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')


