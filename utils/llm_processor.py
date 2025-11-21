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
        description="Prix du produit (nombre décimal positif)",
        gt=0.0
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
    system_prompt = """Tu es un expert en extraction de données pour l'e-commerce.
Ta mission est d'analyser du texte provenant de sites web concurrents et d'extraire TOUTES les informations produits de manière structurée et précise.

RÈGLES STRICTES:
1. Extrais uniquement les informations présentes dans le texte
2. Ne génère JAMAIS de données fictives ou inventées
3. Si un champ est incertain, utilise null
4. Pour les prix, extrais uniquement la valeur numérique (retire symboles et espaces)
5. Identifie le code produit (SKU, référence, modèle) comme product_identifier
6. Détecte les promotions et offres spéciales séparément

FORMAT DE SORTIE:
Le JSON doit suivre exactement ce schéma avec ces champs obligatoires:
- products: liste d'objets avec (product_identifier, name, price, currency, category?, description?, product_url?, image_url?, is_available)
- promotions: liste de textes décrivant les offres promotionnelles détectées"""

    user_prompt = f"""Analyse le texte suivant provenant du site: {competitor_base_url}

TEXTE À ANALYSER:
{text_batch[:5000]} 

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
                'num_predict': 800,     # Limite de tokens générés
            }
        )
        
        # Extraction du contenu de la réponse
        raw_content = response['message']['content']
        print(f"Réponse LLM brute reçue: {raw_content[:2500]}")
        
        # Validation avec Pydantic
        try:
            validated_response = LLMResponse.model_validate_json(raw_content)
            print(f"✅ Extraction réussie: {len(validated_response.products)} produits trouvés")
            print(f"produits trouvés: {validated_response}")
            return validated_response
            
        except ValidationError as e:
            print(f"❌ Erreur de validation Pydantic: {e}")
            print(f"Contenu brut qui a échoué: {raw_content[:2500]}")
            # Retourner une réponse vide plutôt que de crasher
            return LLMResponse(products=[], promotions=[])

    except Exception as e:
        print(f"❌ Erreur lors de l'appel Ollama: {type(e).__name__}: {e}")
        return LLMResponse(products=[], promotions=[])


def test_llm_extraction():
    """
    Fonction de test pour vérifier le bon fonctionnement du LLM
    À exécuter manuellement depuis le shell Django
    """
    sample_text = """
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
    result = extract_products_with_llm(sample_text, "https://example.com")
    
    print(f"\n📊 Résultats:")
    print(f"🛒 Produits extraits: {result.products}")
    print(f"\n🎁 Promotions: {result.promotions}")
    
    return result


# Pour utiliser dans Django shell:
# python manage.py shell
# >>> from utils.llm_processor import test_llm_extraction
# >>> test_llm_extraction()
