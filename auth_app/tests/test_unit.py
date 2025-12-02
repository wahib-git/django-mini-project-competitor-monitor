import pytest
from django.contrib.auth.models import User, Group
from auth_app.forms import SignupForm


@pytest.mark.django_db
class TestSignupFormUnit:
    """
    Test unitaire: validation du formulaire d'inscription (logique isolée)
    """
    
    def test_valid_signup_form(self):
        """Formulaire valide avec toutes les données requises"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = SignupForm(data=form_data)
        assert form.is_valid(), f"Erreurs: {form.errors}"
    
    def test_invalid_email_duplicate(self):
        """Email déjà existant doit échouer"""
        # Créer un utilisateur existant
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='pass'
        )
        
        # Tenter de s'inscrire avec le même email
        form_data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'déjà utilisé' in str(form.errors['email']).lower()
    
    def test_password_mismatch(self):
        """Mots de passe différents doivent échouer"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass456!',
        }
        form = SignupForm(data=form_data)
        assert not form.is_valid()
        assert 'password2' in form.errors
    
    # def test_user_assigned_to_client_group_on_save(self):
    #     """L'utilisateur créé doit être ajouté au groupe Client"""
    #     # Créer le groupe Client
    #     Group.objects.get_or_create(name='Client')
        
    #     form_data = {
    #         'username': 'clientuser',
    #         'email': 'client@example.com',
    #         'password1': 'SecurePass123!',
    #         'password2': 'SecurePass123!',
    #     }
    #     form = SignupForm(data=form_data)
    #     assert form.is_valid()
        
    #     user = form.save()
    #     assert user.groups.filter(name='Client').exists()