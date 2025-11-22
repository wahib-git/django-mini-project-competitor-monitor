from django.urls import path
from auth_app import views

urlpatterns = [
    # Page d'accueil publique
    path('', views.home, name='home'),
    
    # Authentification
    path('connexion/', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    
    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
    
]
