from django.urls import path
from auth_app import views

urlpatterns = [
    path('', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),    
    path('deconnexion/', views.deconnexion, name='deconnexion'),
]