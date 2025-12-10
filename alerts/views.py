from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Alert
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def alert_list(request):
    # Récupérer toutes les alertes de l'utilisateur
    alerts = Alert.objects.filter(user=request.user).select_related('competitor', 'product')
    
    # Filtres
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    
    if status_filter == 'unread':
        alerts = alerts.filter(is_read=False)
    elif status_filter == 'read':
        alerts = alerts.filter(is_read=True)
    
    if type_filter:
        alerts = alerts.filter(alert_type=type_filter)
    
    # Tri par date décroissante
    alerts = alerts.order_by('created_at')
    
    # Compteurs
    total_alerts = Alert.objects.filter(user=request.user).count()
    unread_count = Alert.objects.filter(user=request.user, is_read=False).count()
    
    # Pagination (10 alertes par page)
    paginator = Paginator(alerts, 5)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    context = {
        'alerts': page_obj,
        'page_obj': page_obj,
        'total_alerts': total_alerts,
        'unread_count': unread_count,
    }
    
    return render(request, 'alerts/alert_list.html', context)

@login_required
def mark_as_read(request, alert_id):
    """
    Marquer une alerte comme lue
    """
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    alert.is_read = True
    alert.save()
    messages.success(request, "✅ Alerte marquée comme lue.")
    return redirect('alerts:alert_list')


@login_required
def mark_all_as_read(request):
    """
    Marquer toutes les alertes comme lues
    """
    if request.method == 'POST':
        Alert.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, "✅ Toutes les alertes ont été marquées comme lues.")
    return redirect('alerts:alert_list')


@login_required
def delete_alert(request, alert_id):
    """
    Supprimer une alerte
    """
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    alert.delete()
    messages.success(request, "🗑️ Alerte supprimée.")
    return redirect('alerts:alert_list')
