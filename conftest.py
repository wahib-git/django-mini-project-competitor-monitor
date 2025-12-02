import pytest
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Configuration de la base de données de test avec migrations"""
    with django_db_blocker.unblock():
        # Appliquer toutes les migrations
        call_command('migrate', '--run-syncdb', verbosity=0)


@pytest.fixture
def create_user(db):
    """Fixture pour créer un utilisateur test"""
    def make_user(username='testuser', password='TestPass123!', email='test@example.com', **kwargs):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )
        return user
    return make_user


@pytest.fixture
def create_client_user(db):
    """Fixture pour créer un utilisateur client avec groupe"""
    def make_client(username='client', password='ClientPass123!', email='client@example.com'):
        client_group, _ = Group.objects.get_or_create(name='Client')
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.groups.add(client_group)
        return user
    return make_client


@pytest.fixture
def create_admin_user(db):
    """Fixture pour créer un utilisateur admin"""
    def make_admin(username='admin', password='AdminPass123!', email='admin@example.com'):
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True
        )
        user.groups.add(admin_group)
        return user
    return make_admin


@pytest.fixture
def authenticated_client(client, create_client_user):
    """Client Django authentifié"""
    user = create_client_user()
    client.force_login(user)
    return client, user


@pytest.fixture(scope='class')
def browser(request):
    """Fixture Selenium pour tests fonctionnels"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.implicitly_wait(10)
    
    # Attacher à la classe de test
    if request.cls is not None:
        request.cls.browser = driver
    
    yield driver
    
    driver.quit()


@pytest.fixture
def groups_setup(db):
    """Créer les groupes Client et Admin"""
    Group.objects.get_or_create(name='Client')
    Group.objects.get_or_create(name='Admin')