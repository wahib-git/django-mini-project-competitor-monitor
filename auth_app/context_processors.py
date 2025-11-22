from alerts.models import Alert

def unread_alerts(request):
    """
    Context processor pour afficher le nombre d'alertes non lues dans la navbar
    """
    if request.user.is_authenticated:
        count = Alert.objects.filter(user=request.user, is_read=False).count()
        return {'unread_alerts_count': count}
    return {'unread_alerts_count': 0}
