import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.test import Client


@pytest.mark.django_db
class TestAuthenticationIntegration:
    """
    Test d'intégration: flux complet inscription → connexion → redirection
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Créer les groupes nécessaires avant chaque test"""
        Group.objects.get_or_create(name='Client')
        Group.objects.get_or_create(name='Admin')
        self.client = Client()
    
    def test_signup_login_redirect_flow(self):
        """
        Scénario complet:
        1. Inscription d'un utilisateur
        2. Connexion avec les mêmes identifiants
        3. Vérification de la redirection vers le dashboard client
        """
        # Étape 1: Inscription
        signup_url = reverse('inscription')
        signup_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        response = self.client.post(signup_url, signup_data)
        
        # Vérifier la redirection vers connexion
        assert response.status_code == 302
        assert response.url == reverse('connexion')
        
        # Vérifier que l'utilisateur est créé
        user = User.objects.get(username='integrationuser')
        assert user.email == 'integration@example.com'
        assert user.groups.filter(name='Client').exists()
        
        # Étape 2: Connexion
        login_url = reverse('connexion')
        login_data = {
            'username': 'integrationuser',
            'password': 'SecurePass123!',
        }
        response = self.client.post(login_url, login_data)
        
        # Vérifier la redirection vers le dashboard client
        assert response.status_code == 302
        assert response.url == reverse('client_dashboard')
        
        # Vérifier que l'utilisateur est authentifié
        assert '_auth_user_id' in self.client.session
    
    def test_admin_user_redirected_to_admin_dashboard(self):
        """Admin doit être redirigé vers le dashboard admin"""
        # Créer un admin
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(admin_group)
        
        # Connexion
        login_url = reverse('connexion')
        response = self.client.post(login_url, {
            'username': 'admin',
            'password': 'AdminPass123!',
        })
        
        # Vérifier redirection vers admin dashboard
        assert response.status_code == 302
        assert response.url == reverse('admin_dashboard')
    
    def test_authenticated_user_cannot_access_login_page(self):
        """Utilisateur connecté ne peut pas accéder à /connexion/"""
        # Créer et connecter un utilisateur
        user = User.objects.create_user(
            username='loggeduser',
            password='Pass123!',
            email='logged@example.com'
        )
        client_group, _ = Group.objects.get_or_create(name='Client')
        user.groups.add(client_group)
        
        self.client.login(username='loggeduser', password='Pass123!')
        
        # Tenter d'accéder à la page de connexion
        response = self.client.get(reverse('connexion'))
        
        # Doit être redirigé vers le dashboard
        assert response.status_code == 302
        assert response.url == reverse('client_dashboard')