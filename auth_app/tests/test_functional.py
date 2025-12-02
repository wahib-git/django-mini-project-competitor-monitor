import pytest
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.auth.models import User, Group
from django.urls import reverse


@pytest.mark.selenium
class TestUserJourneyFunctional(LiveServerTestCase):
    """
    Test fonctionnel (E2E): simulation d'un utilisateur réel avec Selenium
    Parcours: Landing → Inscription → Connexion → Dashboard
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Utiliser Chrome headless pour CI/CD
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.selenium = webdriver.Chrome(options=options)
        cls.selenium.implicitly_wait(10)
    
    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Créer les groupes avant chaque test"""
        Group.objects.get_or_create(name='Client')
        Group.objects.get_or_create(name='Admin')
    
    def test_complete_user_journey(self):
        """
        Parcours complet d'un nouvel utilisateur:
        1. Visite la landing page
        2. Clique sur "S'inscrire"
        3. Remplit le formulaire d'inscription
        4. Se connecte
        5. Accède au dashboard client
        """
        # Étape 1: Accéder à la landing page
        self.selenium.get(f'{self.live_server_url}/')
        assert "Competitor Monitor" in self.selenium.title
        
        # Vérifier présence du bouton "Commencer gratuitement"
        signup_btn = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Commencer gratuitement"))
        )
        
        # Étape 2: Cliquer sur inscription
        signup_btn.click()
        
        # Vérifier qu'on est sur la page d'inscription
        assert "Inscription" in self.selenium.title
        
        # Étape 3: Remplir le formulaire
        username_input = self.selenium.find_element(By.ID, "id_username")
        email_input = self.selenium.find_element(By.ID, "id_email")
        password1_input = self.selenium.find_element(By.ID, "id_password1")
        password2_input = self.selenium.find_element(By.ID, "id_password2")
        
        username_input.send_keys("functionaluser")
        email_input.send_keys("functional@example.com")
        password1_input.send_keys("FunctionalPass123!")
        password2_input.send_keys("FunctionalPass123!")
        
        # Soumettre le formulaire
        submit_btn = self.selenium.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        
        # Vérifier redirection vers connexion
        WebDriverWait(self.selenium, 10).until(
            EC.url_contains('/connexion/')
        )
        
        # Vérifier message de succès (optionnel selon ton implémentation)
        # success_msg = self.selenium.find_element(By.CSS_SELECTOR, ".alert-success")
        # assert "Compte créé" in success_msg.text
        
        # Étape 4: Se connecter
        username_login = self.selenium.find_element(By.ID, "id_username")
        password_login = self.selenium.find_element(By.ID, "id_password")
        
        username_login.send_keys("functionaluser")
        password_login.send_keys("FunctionalPass123!")
        
        login_btn = self.selenium.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_btn.click()
        
        # Étape 5: Vérifier accès au dashboard client
        WebDriverWait(self.selenium, 10).until(
            EC.url_contains('/dashboard/client/')
        )
        
        # Vérifier présence du nom d'utilisateur
        assert "functionaluser" in self.selenium.page_source
        assert "Dashboard Client" in self.selenium.title
    
    def test_invalid_login_shows_error(self):
        """Test: message d'erreur pour identifiants invalides"""
        self.selenium.get(f'{self.live_server_url}/connexion/')
        
        username_input = self.selenium.find_element(By.ID, "id_username")
        password_input = self.selenium.find_element(By.ID, "id_password")
        
        username_input.send_keys("wronguser")
        password_input.send_keys("wrongpass")
        
        submit_btn = self.selenium.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        
        # Attendre le message d'erreur
        error_msg = WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".error, .alert-danger"))
        )
        
        assert "invalide" in error_msg.text.lower()