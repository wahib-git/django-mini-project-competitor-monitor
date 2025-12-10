"""
Module pour l'extraction de données structurées avec Ollama LLM
Utilise l'API structurée d'Ollama avec Pydantic pour une validation robuste
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError
from ollama import chat

class ProductExtraction(BaseModel):
    """
    Schéma Pydantic pour un produit extrait
    """
    product_identifier: str = Field(
        ..., 
        description="SKU, code produit ou identifiant unique",
        min_length=1,
        max_length=255
    )
    name: str = Field(
        ..., 
        description="Nom du produit",
        min_length=1,
        max_length=500
    )
    price: float = Field(
        ..., 
        description="Prix numérique du produit",
        ge=0.0    
    )
    currency: str = Field(
        default="DT", 
        description="Code devise ISO (DT,TND, EUR,USD,$, etc.)",
        max_length=3
    )
    category: Optional[str] = Field(
        None, 
        description="Catégorie du produit",
        max_length=255
    )
    description: Optional[str] = Field(
        None, 
        description="Description détaillée du produit"
    )
    product_url: Optional[str] = Field(
        None, 
        description="URL complète de la page produit"
    )
    image_url: Optional[str] = Field(
        None, 
        description="URL de l'image principale du produit"
    )
    is_available: bool = Field(
        default=True, 
        description="Disponibilité du produit (en stock ou non)"
    )
  
class LLMResponse(BaseModel):
    """
    Schéma Pydantic pour la réponse complète du LLM
    """
    products: List[ProductExtraction] = Field(
        default_factory=list,
        description="Liste des produits extraits"
    )
    promotions: List[str] = Field(
        default_factory=list,
        description="Liste des promotions détectées"
    )

def extract_products_with_llm(text_batch: str, competitor_base_url: str, model: str = 'llama3.1') -> LLMResponse:
    """
    Extrait les produits d'un texte en utilisant Ollama avec sortie structurée
    
    Args:
        text_batch: Texte nettoyé à analyser
        competitor_base_url: URL du site concurrent (pour contexte)
        model: Nom du modèle Ollama à utiliser (défaut: llama3.1)
    
    Returns:
        LLMResponse: Objet Pydantic contenant les produits et promotions extraits
    """
    
    # Prompt optimisé pour l'extraction structurée

    
    system_prompt = """You are an expert in data extraction for e-commerce.
Your mission is to analyze text from competitor websites and extract ALL product information in a structured and precise manner.

STRICT RULES:
1. Extract only information present in the text
2. NEVER generate fictional or invented data except for the product_identifier use the product name, without adding anything else.
3. If it's a bouquet of a certain type of flower (bouquet of something), ignore it.
4. If it's a category of products (Fleurs d'Amour, Fleurs de 200 à 300 dt ), ignore it.
5. If you determine this cannot be a product, ignore it
6. The product and image URLs must be concatenated with competitor_base_url if they are relative paths
7. If a field is uncertain, use null
8. If more than 1 fields are missing or null for a product, ignore it
9. Detect promotions and special offers separately

OUTPUT FORMAT:
The JSON must follow exactly this schema with these mandatory fields:
- products: list of objects with (product_identifier, name, price, currency, category?, description?, product_url?, image_url?, is_available)
- promotions: list of texts describing detected promotional offers"""


    user_prompt = f"""Analyze the following text from the website: {competitor_base_url}

TEXTE À ANALYSER:
{text_batch[:7500]} 

Extrait TOUS les produits avec leurs informations complètes."""

    try:
        # Appel à l'API Ollama avec schéma structuré (nouvelle API)
        response = chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            format=LLMResponse.model_json_schema(),  # Force le LLM à suivre le schéma Pydantic
            options={
                'temperature': 0.1,      # Très déterministe pour extraction de données
                'top_p': 0.9,
                'num_predict': 2500,     # Limite de tokens générés
            }
        )
        
        # Extraction du contenu de la réponse
        raw_content = response['message']['content']
        print(f"Réponse LLM brute reçue: {raw_content[:4500]}")
        # Validation avec gestion partielle des erreurs
        try:
            validated_response = LLMResponse.model_validate_json(raw_content)
            print(f"✅ Extraction réussie: {len(validated_response.products)} produits trouvés")
            return validated_response
            
        except ValidationError as e:
            print(f"⚠️ Erreur de validation Pydantic détectée, tentative de récupération partielle...")
            
            # Parser manuellement le JSON pour récupérer les produits valides
            import json
            try:
                raw_data = json.loads(raw_content)
                valid_products = []
                failed_count = 0
                
                # Valider chaque produit individuellement
                for idx, product_data in enumerate(raw_data.get('products', [])):
                    try:
                        valid_product = ProductExtraction(**product_data)
                        valid_products.append(valid_product)
                    except ValidationError as prod_error:
                        failed_count += 1
                        print(f"❌ Produit {idx} invalide ({product_data.get('name', 'N/A')}): {prod_error}")
                
                # Récupérer les promotions (généralement pas de validation stricte)
                promotions = raw_data.get('promotions', [])
                
                print(f"✅ Récupération partielle: {len(valid_products)} produits valides, {failed_count} ignorés")
                
                return LLMResponse(products=valid_products, promotions=promotions)
                
            except json.JSONDecodeError:
                print(f"❌ Impossible de parser le JSON: {raw_content[:500]}")
                return LLMResponse(products=[], promotions=[])        
        # Validation avec Pydantic
        # try:
        #     validated_response = LLMResponse.model_validate_json(raw_content)
        #     print(f"✅ Extraction réussie: {len(validated_response.products)} produits trouvés")
        #     print(f"validated_response: {validated_response}")
        #     return validated_response
            
        # except ValidationError as e:
        #     print(f"❌ Erreur de validation Pydantic: {e}")
        #     print(f"Contenu brut qui a échoué: {raw_content[:2500]}")
        #     # Retourner le Contenu vide plutôt que de crasher
        #     return LLMResponse(products=[], promotions=[])

           
        
                
    except Exception as e:
        print(f"❌ Erreur lors de l'appel Ollama: {type(e).__name__}: {e}")
        return LLMResponse(products=[], promotions=[])


def test_llm_extraction():
    """
    Fonction de test pour vérifier le bon fonctionnement du LLM
    À exécuter manuellement depuis le shell Django
    """

    sample_text1 = """
    iPhone 15 Pro Max 256GB - Prix: 1199.99 EUR
    Référence: IPHONE15PM256
    
    Description: Le dernier smartphone Apple avec puce A17 Pro
    Catégorie: Smartphones
    En stock
    
    Samsung Galaxy S24 Ultra - 999.00 EUR
    SKU: SAMS24ULTRA
    Disponible en noir et gris
    
    PROMOTION SPÉCIALE: -20% sur tous les accessoires ce week-end!
    """

    print("🧪 Test d'extraction LLM...")
    print(f"📝 Longueur du texte: {sample_text1}")
    
    result = extract_products_with_llm(
        text_batch=sample_text1, 
        competitor_base_url="https://www.fleurs-tunisie.tn/",
        model='llama3.1'
    )
    print(f"\n📊 Résultats:")
    for product in result.products:
        print(f"  - {product.name}: {product.price} {product.currency} (SKU: {product.product_identifier})")
    
    print(f"\n🎁 Promotions: {result.promotions}")

    return result



# Pour utiliser dans Django shell:
# python manage.py shell
# >>> from utils.llm_processor import test_llm_extraction
# >>> test_llm_extraction()
