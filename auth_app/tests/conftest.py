import pytest
from auth_app.forms import SignupForm


@pytest.fixture
def valid_signup_data():
    """Données valides pour inscription"""
    return {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password1': 'SecurePass123!',
        'password2': 'SecurePass123!',
    }


@pytest.fixture
def signup_form(valid_signup_data):
    """Formulaire d'inscription pré-rempli"""
    return SignupForm(data=valid_signup_data)