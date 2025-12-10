from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .models import Competitor, Product, PriceHistory, ScrapeSession
from alerts.models import Alert
from utils.dom_cleaner import clean_html_content, split_into_batches
from utils.llm_processor import extract_products_with_llm

def scrape_competitor_website(competitor_id):
    """
    Fonction principale de scraping (appelée manuellement par le client)
    """
    try:
        competitor = Competitor.objects.get(id=competitor_id)
    except Competitor.DoesNotExist:
        return {"success": False, "error": "Concurrent introuvable"}
    
    # Créer une session de scraping
    session = ScrapeSession.objects.create(
        competitor=competitor,
        status='running'
    )
    
    session_id = session.id
    
    try:
        # 1. Configuration Selenium (headless mode)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        print("🚀 1.Selenium WebDriver configuré en mode headless")
        
        # 2. Naviguer vers le site
        print(f"🌐2.Naviguation vers le site: {competitor.base_url}")
        driver.get(competitor.base_url)
        
        # Attendre que la page se charge (ajuster le sélecteur selon le site)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        print("✅ Page chargée")

        
        # 3. Extraire le contenu du <body> UNIQUEMENT
        # Localiser l'élément body
        body_element = driver.find_element(By.TAG_NAME, 'body')
        
        # Récupérer l'attribut 'innerHTML' de l'élément body, qui est tout le contenu interne
        raw_html = body_element.get_attribute('innerHTML')
        print("📝 Contenu du <body> extrait")
        driver.quit()    
        
        # Sauvegarder le HTML brut pour debug
        session.raw_html = raw_html[:50000]  # Limiter à 50k caractères
        session.save()
        print("💾 HTML brut sauvegardé dans la session")


        # 4. Nettoyer le HTML
        print("🧹 4.Nettoyage du HTML...")
        cleaned_text = clean_html_content(raw_html)
        
    
        # 5. Diviser en batches
        batches = split_into_batches(cleaned_text, max_chars=7500)
        print("📦 5.Texte divisé en batches pour LLM")
        print(f"📦 {len(batches)} batches créés")
        

        # 6. Extraire les produits avec LLM (UNIQUEMENT BATCH 3)
        all_products = []
        all_promotions = []
        
        # 🔥 Traiter UNIQUEMENT le batch d'indice 2 (3ème batch)
        i = 2
        print(f"🤖 Traitement batch {i+1}/{len(batches)} avec LLM...")
        llm_response = extract_products_with_llm(
            text_batch=batches[i], 
            competitor_base_url=competitor.base_url,
            model='llama3.1'
        )
        all_products.extend(llm_response.products)
        all_promotions.extend(llm_response.promotions)
        
        print("🤖 6.Extraction LLM terminée")
        print(f"✅ {len(all_products)} produits extraits")
        print(f"✅ {len(all_promotions)} promotions extraites")
        print(f"✅ produits extraits exemple: {[p.name for p in all_products[:3]]}")
        print(f"✅ promotions extraites exemple: {all_promotions[:3]}")

        # 7. Sauvegarder les produits en base de données
        products_saved = save_products_to_database(
            all_products, 
            competitor, 
            session_id
        )
        print(f"💾 7.Sauvegarde terminée: {products_saved} produits enregistrés")

        # 8. Finaliser la session
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.products_found = products_saved
        session.save()
        print("✅ 8.Session finalisée")
        
        # 9. Mettre à jour le timestamp du competitor
        competitor.last_scraped_at = timezone.now()
        competitor.save()
        print("🕒 9.Timestamp du competitor mis à jour")
        return {
            "success": True,
            "products_found": products_saved,
            "promotions": all_promotions,
            "session_id": str(session_id)
        }
        
    except Exception as e:
        # En cas d'erreur
        session.status = 'failed'
        session.completed_at = timezone.now()
        session.errors = {"error": str(e)}
        session.save()
        
        return {
            "success": False,
            "error": str(e)
        }


def save_products_to_database(products_data, competitor, session_id):
    """
    Sauvegarde les produits extraits par le LLM
    """
    count = 0
    
    for product_data in products_data:
        try:
            # Créer ou récupérer le produit
            product, created = Product.objects.get_or_create(
                competitor=competitor,
                product_identifier=product_data.product_identifier,
                defaults={
                    'name': product_data.name,
                    'description': product_data.description,
                    'category': product_data.category,
                    'product_url': product_data.product_url or competitor.base_url,
                    'image_url': product_data.image_url,
                    'current_price': product_data.price,
                    'currency': product_data.currency,
                    'is_available': product_data.is_available
                }
            )
            
            if created:
                # Nouveau produit → créer une alerte
                Alert.objects.create(
                    user=competitor.user,
                    competitor=competitor,
                    product=product,
                    alert_type='new_product',
                    severity='medium',
                    title=f"Nouveau produit: {product.name}",
                    message=f"Un nouveau produit a été détecté chez {competitor.name}",
                    new_value={'price': float(product.current_price), 'name': product.name}
                )
                print(f"🆕 Nouveau produit: {product.name}")
            
            # Toujours enregistrer le prix dans l'historique
            PriceHistory.objects.create(
                product=product,
                price=product_data.price,
                scrape_session_id=session_id
            )
            
            count += 1
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde produit {product_data.name}: {e}")
            continue
    
    return count


def analyze_price_changes(competitor_id):
    """
    Compare les prix et génère des alertes
    Appelé manuellement par le bouton "Analyser"
    """
    try:
        competitor = Competitor.objects.get(id=competitor_id)
    except Competitor.DoesNotExist:
        return {"success": False, "error": "Concurrent introuvable"}
    
    alerts_created = 0
    
    for product in competitor.products.all():
        # Récupérer les 2 derniers prix
        recent_prices = product.price_history.all()[:2]
        
        if recent_prices.count() < 2:
            continue  # Pas assez de données
        
        current_price = float(recent_prices.price)
        previous_price = float(recent_prices.price)[4]
        
        # Calculer le changement en pourcentage
        price_change_pct = ((current_price - previous_price) / previous_price) * 100
        
        # Seuil: 5%
        if abs(price_change_pct) >= 5:
            alert_type = 'price_decrease' if price_change_pct < 0 else 'price_increase'
            severity = 'high' if abs(price_change_pct) >= 15 else 'medium'
            
            Alert.objects.create(
                user=competitor.user,
                competitor=competitor,
                product=product,
                alert_type=alert_type,
                severity=severity,
                title=f"{product.name} - Changement de prix",
                message=f"Le prix a changé de {price_change_pct:.1f}% ({previous_price}€ → {current_price}€)",
                old_value={'price': previous_price},
                new_value={'price': current_price}
            )
            
            # Mettre à jour le prix actuel du produit
            product.current_price = current_price
            product.save()
            
            alerts_created += 1
            print(f"🔔 Alerte créée: {product.name} ({price_change_pct:.1f}%)")
    
    return {
        "success": True,
        "alerts_created": alerts_created
    }
