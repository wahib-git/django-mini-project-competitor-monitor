from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    # Liste des alertes
    path('', views.alert_list, name='alert_list'),
    
    # Marquer une alerte comme lue
    path('mark-read/<uuid:alert_id>/', views.mark_as_read, name='mark_as_read'),
    
    # Supprimer une alerte
    path('delete/<uuid:alert_id>/', views.delete_alert, name='delete_alert'),
    
    # Marquer toutes les alertes comme lues
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
]
