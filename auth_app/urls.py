from django.urls import path
from auth_app import views

urlpatterns = [
    path('', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('acceuil/', views.acceuil, name='acceuil'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
]