import pytest
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            cls.selenium = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        except Exception:
            # Fallback si webdriver-manager ne fonctionne pas
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
        try:
            # Étape 1: Accéder à la landing page
            self.selenium.get(f'{self.live_server_url}/')
            
            # Attendre le chargement complet
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Vérifier le titre
            assert "Competitor Monitor" in self.selenium.title or "Accueil" in self.selenium.title
            
            # Étape 2: Cliquer sur inscription (chercher par plusieurs méthodes)
            try:
                # Essayer le texte exact
                signup_btn = WebDriverWait(self.selenium, 10).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Commencer"))
                )
            except TimeoutException:
                # Alternative: chercher par href
                signup_btn = self.selenium.find_element(By.CSS_SELECTOR, "a[href*='inscription']")
            
            signup_btn.click()
            
            # Attendre la redirection
            WebDriverWait(self.selenium, 10).until(
                EC.url_contains('/inscription/')
            )
            
            # Vérifier qu'on est sur la page d'inscription
            assert "inscription" in self.selenium.current_url.lower()
            
            # Étape 3: Remplir le formulaire d'inscription
            # Attendre que le formulaire soit chargé
            username_input = WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, "id_username"))
            )
            
            email_input = self.selenium.find_element(By.ID, "id_email")
            password1_input = self.selenium.find_element(By.ID, "id_password1")
            password2_input = self.selenium.find_element(By.ID, "id_password2")
            
            # Remplir les champs
            username_input.clear()
            username_input.send_keys("functionaluser")
            
            email_input.clear()
            email_input.send_keys("functional@example.com")
            
            password1_input.clear()
            password1_input.send_keys("FunctionalPass123!")
            
            password2_input.clear()
            password2_input.send_keys("FunctionalPass123!")
            
            # Soumettre le formulaire
            submit_btn = self.selenium.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            
            # Vérifier redirection vers connexion
            WebDriverWait(self.selenium, 10).until(
                EC.url_contains('/connexion/')
            )
            
            assert "connexion" in self.selenium.current_url.lower()
            
            # Vérifier que l'utilisateur est créé en DB
            user = User.objects.get(username='functionaluser')
            assert user.email == 'functional@example.com'
            assert user.groups.filter(name='Client').exists()
            
            # Étape 4: Se connecter
            username_login = WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, "id_username"))
            )
            password_login = self.selenium.find_element(By.ID, "id_password")
            
            username_login.clear()
            username_login.send_keys("functionaluser")
            
            password_login.clear()
            password_login.send_keys("FunctionalPass123!")
            
            login_btn = self.selenium.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            
            # Étape 5: Vérifier accès au dashboard client
            WebDriverWait(self.selenium, 10).until(
                EC.url_contains('/dashboard/client/')
            )
            
            # Vérifier qu'on est bien sur le dashboard
            assert "/dashboard/client/" in self.selenium.current_url
            
            # Vérifier présence du nom d'utilisateur dans la page
            page_source = self.selenium.page_source.lower()
            assert "functionaluser" in page_source or "bienvenue" in page_source
            
        except Exception as e:
            # Sauvegarder une capture d'écran en cas d'erreur
            screenshot_path = "test_error_screenshot.png"
            self.selenium.save_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            print(f"Current URL: {self.selenium.current_url}")
            print(f"Page source: {self.selenium.page_source[:500]}")
            raise
    
    def test_invalid_login_shows_error(self):
        """Test: message d'erreur pour identifiants invalides"""
        try:
            self.selenium.get(f'{self.live_server_url}/connexion/')
            
            # Attendre le formulaire
            username_input = WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, "id_username"))
            )
            password_input = self.selenium.find_element(By.ID, "id_password")
            
            username_input.clear()
            username_input.send_keys("wronguser")
            
            password_input.clear()
            password_input.send_keys("wrongpass")
            
            submit_btn = self.selenium.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()
            
            # Attendre le message d'erreur (chercher par plusieurs sélecteurs)
            try:
                error_msg = WebDriverWait(self.selenium, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".error, .alert-danger, .messages .error"))
                )
                assert "invalide" in error_msg.text.lower() or "incorrect" in error_msg.text.lower()
            except TimeoutException:
                # Vérifier dans tout le contenu de la page
                page_source = self.selenium.page_source.lower()
                assert "invalide" in page_source or "incorrect" in page_source
                
        except Exception as e:
            screenshot_path = "test_login_error_screenshot.png"
            self.selenium.save_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            print(f"Current URL: {self.selenium.current_url}")
            raise