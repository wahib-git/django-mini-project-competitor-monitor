from django.urls import path
from clients import views
urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('list/', views.client_list, name='client_list'),
    path('delete/<int:user_id>/', views.client_delete, name='client_delete'),
    path('stats/<int:user_id>/', views.client_stats, name='client_stats'),
    path('toggle_status/<int:user_id>/', views.client_toggle_status, name='client_toggle_status'),
    
]