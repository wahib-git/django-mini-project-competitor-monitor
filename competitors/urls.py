from django.urls import path
from . import views

app_name = 'competitors'

urlpatterns = [
    # Liste des concurrents
    path('', views.competitor_list, name='competitor_list'),
    
    # Ajouter un concurrent
    path('add/', views.competitor_add, name='competitor_add'),
    
    # Modifier un concurrent
    path('edit/<uuid:competitor_id>/', views.competitor_edit, name='competitor_edit'),
    
    # Supprimer un concurrent
    path('delete/<uuid:competitor_id>/', views.competitor_delete, name='competitor_delete'),
    
    # 🔥 SCRAPING MANUEL
    path('scrape/<uuid:competitor_id>/', views.trigger_scraping, name='trigger_scraping'),
    
    # 🔥 ANALYSE DES PRIX
    path('analyze/<uuid:competitor_id>/', views.trigger_analysis, name='trigger_analysis'),
    
    # Liste des produits d'un concurrent
    path('<uuid:competitor_id>/products/', views.product_list, name='product_list'),
    
    # Détail d'un produit avec historique des prix
    path('product/<uuid:product_id>/', views.product_detail, name='product_detail'),
]
