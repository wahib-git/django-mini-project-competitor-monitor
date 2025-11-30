from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse

from competitors.models import Competitor, Product
from alerts.models import Alert


# Décorateur pour vérifier si l'utilisateur est un admin (staff)
def admin_required(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):
    """
    Dashboard principal de l'administrateur avec statistiques globales
    """
    # Statistiques globales
    total_clients = User.objects.filter(is_staff=False).count()
    active_clients = User.objects.filter(is_staff=False, is_active=True).count()
    total_competitors = Competitor.objects.count()
    total_products = Product.objects.count()
    total_alerts = Alert.objects.count()
    unread_alerts = Alert.objects.filter(is_read=False).count()
    
    # Derniers clients inscrits
    recent_clients = User.objects.filter(is_staff=False).order_by('-date_joined')[:5]
    
    # Clients les plus actifs (avec le plus de concurrents)
    top_clients = User.objects.filter(is_staff=False).annotate(
        competitor_count=Count('competitors')
    ).order_by('-competitor_count')[:5]
    
    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'total_competitors': total_competitors,
        'total_products': total_products,
        'total_alerts': total_alerts,
        'unread_alerts': unread_alerts,
        'recent_clients': recent_clients,
        'top_clients': top_clients,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(admin_required)
def client_list(request):
    """
    Liste de tous les clients avec statistiques
    """
    # Récupérer tous les clients (non-staff)
    clients = User.objects.filter(is_staff=False).annotate(
        competitor_count=Count('competitors'),
        product_count=Count('competitors__products'),
        alert_count=Count('alerts')
    ).order_by('-date_joined')
    
    # Filtrage par statut
    status_filter = request.GET.get('status', None)
    if status_filter == 'active':
        clients = clients.filter(is_active=True)
    elif status_filter == 'inactive':
        clients = clients.filter(is_active=False)
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        clients = clients.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    context = {
        'clients': clients,
        'total_clients': clients.count(),
        'search_query': search_query,
    }
    return render(request, 'client_list.html', context)


@login_required
@user_passes_test(admin_required)
def client_delete(request, user_id):
    """
    Supprimer un client
    """
    client = get_object_or_404(User, id=user_id, is_staff=False)
    
    if request.method == 'POST':
        username = client.username
        client.delete()
        messages.success(request, f"🗑️ Client '{username}' supprimé avec succès !")
        return redirect('client_list')
    
    # Récupérer les statistiques avant suppression
    stats = {
        'competitors': client.competitors.count(),
        'products': Product.objects.filter(competitor__user=client).count(),
        'alerts': client.alerts.count(),
    }
    
    return render(request, 'client_delete_confirm.html', {
        'client': client,
        'stats': stats
    })


@login_required
@user_passes_test(admin_required)
def client_toggle_status(request, user_id):
    """
    Activer/Désactiver un client
    """
    client = get_object_or_404(User, id=user_id, is_staff=False)
    
    if request.method == 'POST':
        client.is_active = not client.is_active
        client.save()
        
        status = "activé" if client.is_active else "désactivé"
        messages.success(request, f"✅ Client '{client.username}' {status} avec succès !")
    
    return redirect('client_list')


@login_required
@user_passes_test(admin_required)
def client_stats(request, user_id):
    """
    Statistiques détaillées d'un client
    """
    client = get_object_or_404(User, id=user_id, is_staff=False)
    
    # Récupérer toutes les statistiques
    competitors = client.competitors.all()
    total_products = Product.objects.filter(competitor__user=client).count()
    alerts = client.alerts.all()
    
    # Statistiques par concurrent
    competitor_stats = []
    for competitor in competitors:
        competitor_stats.append({
            'competitor': competitor,
            'product_count': competitor.products.count(),
            'alert_count': Alert.objects.filter(competitor=competitor).count(),
        })
    
    context = {
        'client': client,
        'total_competitors': competitors.count(),
        'total_products': total_products,
        'total_alerts': alerts.count(),
        'unread_alerts': alerts.filter(is_read=False).count(),
        'competitor_stats': competitor_stats,
    }
    return render(request, 'client_stats.html', context)
