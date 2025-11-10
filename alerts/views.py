from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Alert


@login_required
def alert_list(request):
    """
    Liste des alertes de l'utilisateur
    """
    alerts = Alert.objects.filter(user=request.user).order_by('-created_at')
    
    # Filtrage par type si spécifié
    alert_type = request.GET.get('type', None)
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)
    
    # Filtrage par statut lu/non lu
    status = request.GET.get('status', None)
    if status == 'unread':
        alerts = alerts.filter(is_read=False)
    elif status == 'read':
        alerts = alerts.filter(is_read=True)
    
    context = {
        'alerts': alerts,
        'total_alerts': alerts.count(),
        'unread_count': Alert.objects.filter(user=request.user, is_read=False).count(),
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
