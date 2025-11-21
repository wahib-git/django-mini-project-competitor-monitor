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
                'num_predict': 2500,     # Limite de tokens générés
            }
        )
        
        # Extraction du contenu de la réponse
        raw_content = response['message']['content']
        print(f"Réponse LLM brute reçue: {raw_content[:4500]}")
        
        # Validation avec Pydantic
        try:
            validated_response = LLMResponse.model_validate_json(raw_content)
            print(f"✅ Extraction réussie: {len(validated_response.products)} produits trouvés")
            print(f"validated_response: {validated_response}")
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
    sample_text = """ 844 avis Très bien 4.76/5.00 Service client 7 jours sur 7 : Whatsapp Nous acceptons les cartes bancaires Tunisiaines et étrangères dt € $ Fleurs Tunisie Nous vous souhaitons la bienvenue sur notre service de livraison de fleurs en Tunisie. Previous Next Comment passer commande sur fleurs-tunisie.tn ? × Opportunité ! Bénéficier 5% de réduction pour votre première commande. Cliquez-ici POUR TOUTE OCCASION + de 40 bouquets disponibles MOT D'ACCOMPAGNEMENT personnalisable POUR TOUT BUDGET à partir de 115 dt LIVRAISON DANS LA JOURNÉE Si commande avant h Afficher tous nos bouquets de fleurs et compositions florales Nos bouquets Glamour 12 roses roses - sans vase à partir de  115DT Pureté 12 roses blanches à partir de  120DT Je t'aime 15 roses rouges - sans vase à partir de  139DT Tu es unique ! à partir de  234DT Rien que pour toi 30 roses à partir de  285DT Promesse 12 roses rouges à partir de  115DT Passion de roses 36 roses à partir de  355DT All you need is love ! 50 roses rouges + 1 rose blanche à partir de  595DT Jardin de Roses à partir de  709DT So Chic ! 15 roses à partir de  140DT L'Orient 40 roses à partir de  430DT Poésie 36 roses à partir de  355DT Bonheur à partir de  120DT Corinne 12 roses jaunes à partir de  120DT Tendresse 7 fleurs blanches - 12 roses à partir de  189DT Ame soeur 12 roses rouges à partir de  120DT Romance 30 roses à partir de  355DT Ma moitié 50 roses à partir de  595DT Close to you 15 roses, sans vase à partir de  139DT Amour 16 roses rouges à partir de  150DT Neige 25 roses blanches 270DT à partir de  230DT Paradis 25 roses rouges à partir de  270DT Élégance 15 roses blanches à partir de  190DT Meryem 36 roses à partir de  355DT Merveille 70 roses jaunes & roses - sans vase à partir de  710DT Roses jaunes 12 roses jaunes à partir de  120DT Sublime 50 roses - sans vase à partir de  520DT Magique 34 roses jaunes & roses - sans vase à partir de  355DT Afficher tous nos bouquets de Fleurs Nicolas - Co-fondateur de Fleurs-Tunisie Webmaster et Co-fondateur de Fleurs-Tunisie, je me ferai un plaisir de vous orienter et de vous conseiller dans la sélection de votre bouquet. MOHAMMED - Co-fondateur de Fleurs-Tunisie C'est un plaisir pour moi de vous recevoir sur notre site. MERYEM - Responsable du catalogue de Fleurs-Tunisie Je suis heureuse de vous recevoir dans notre magasin de fleurs en ligne. N'hésitez pas à me contacter pour toute demande de conseil. Previous Next INSCRIVEZ-NOUS À NOTRE NEWSLETTER ! Soyez informé en temps réel de toutes nos promotions et exclusivités en renseignant votre adresse ci-dessous. S'inscrire Livraison 7 jours sur 7 Choisissez la date et la tranche horaire pour la livraison de votre bouquet ! Une livraison le jour même est possible si vous passez commande avant h. Après cette heure, contactez-nous pour savoir si cela est encore possible. Paiements en ligne sécurisés Paiements en ligne sécurisés (CB,VISA,MASTERCARD) depuis la Tunisie et l'étranger. Nous proposons aussi les moyens de paiement Paypal, virement bancaire et transfert d'espèces. Support Clientèle Support clientèle avant et après commande 7 jours sur 7 par Whatsapp ,  mail sur contact@fleurs-tunisie.tn, Facebook et Chat en bas à gauche de chaque page du site. Personnalisez votre cadeau Personnalisez votre cadeau en accompagnant votre bouquet d'un mot personnel, d'un vase ou de délicieux chocolats.. Nous pouvons ajouter d'autres accessoires à votre bouquet sur-demande. Fleurs Tunisie Livraison Fleurs Tunisie : Votre Fleuriste en ligne 7 jours sur 7 Livraison de fleurs Tunis, Sousse, Monastir, Sahline, Mahdia, Kairouan, Msaken, La Marsa, Grand Tunis, Hammamet, Bizerte, Sfax, Djerba, Nabeul, Beja, El Kef, Kasserine, Gafsa, Tozeur, Gabes, Houm Souk, Medenine, Tataouine, Zarzis et bientôt dans tout la Tunisie incha'Allah Spécialiste de la composition florale originale, des fleurs et des plantes naturelles comme artificielles, nous proposons la livraison de fleurs en Tunisie sur plusieurs villes . afficher la liste des villes Une équipe de fournisseurs professionnels et de fleuristes engagés dans la transmission de ce beau métier par des compositions uniques, mettent leur talent à notre service pour vous offrir le meilleur de la fleur en Tunisie. Envoyer des fleurs en Tunisie est désormais possibles dans de nombreuses villes pour surprendre votre famille ou vos amis à leur domicile ou sur leur lieu de travail !
                                Parce que chaque instant de la vie mérite un arrêt sur image particulier :
                                nous multiplions les occasions de vous livrer, où que vous soyez, nos plus beaux bouquets de fleurs. 7 jours sur 7, notre seul objectif est de satisfaire tous les goûts et toutes les exigences. Celle d'une clientèle amoureuse, comme nous, des belles choses, avec notre catalogue de fleurs, plantes et compositions originales que nous mettons à jour régulièrement. Et cette clientèle à la recherche du meilleur service pour faire parler son cœur, c'est vous ! Notre équipe, à l'écoute de vos attentes, saura vous guider, si nécessaire, pour trouver la prestation adéquate qui vous satisfera pleinement. Et pour répondre à tous vos besoins de produits ou en termes de livraison, fréquence, et accessoires d'accompagnement, nous avons pris le soin de répartir tous nos produits selon plusieurs catégories. Différentes occasions de la vie sont propices à l'envoi de fleurs. A vous d'y être attentif(ve) ! Acheter un bouquet chez Fleurs-Tunisie pour surprendre et épater vos proches, c'est s'assurer d'être livré dans les plus brefs délais du meilleur bouquet, qu'il soit déjà proposé en ligne, ou sur-mesure selon vos attentes. Toute la beauté du monde végétal s'offre à vous en quelques clics pour séduire ou simplement faire plaisir. Enrichir vos relations sentimentales ou amicales n'aura jamais été aussi délicat et raffiné. Même les distances disparaissent le temps d'un présent aux senteurs subtiles pour rafraîchir la mémoire et les sentiments. Un bouquet et tout est rappelé ! Un site frais pour dire «je t'aime» de mille manières à tous ceux qui vous sont chers. Amitié, famille, amour, naissance et retrouvailles sont célébrées à chaque occasion, dans chaque ville pour le plaisir de tous. Envie de vous faire livrer à domicile sur les villes  ? afficher la liste des villes Que vous cherchiez un brin de coquetterie pour votre intérieur ou un cadeau pour une occasion spéciale, vous trouverez dans notre large gamme de produits mise en ligne le bouquet qui respirera votre personnalité. Vous vivez à l'étranger et souhaitez faire preuve de présence sincère auprès de vos proches, dans les moments de joie comme dans les difficultés ? Fleurs-Tunisie est votre intermédiaire de confiance et se charge de tout ! S'il est temps de féliciter les grandes victoires dans une carrière ou une scolarité, n'oubliez pas votre bouquet ! La célébration d'un anniversaire ou d'un heureux événement arrive à grands pas ? Vous pourrez compter sur nos sélections de fleurs et compositions florales haut de gamme pour refléter le message qui vous tient à cœur avec originalité et élégance. Et si l'expression de vos sentiments est à transmettre, avec justesse, pour une déclaration d'amour, la perte d'un être cher ou le rétablissement espéré de vos proches ou relations n'ayez aucune crainte."""
    
    print("🧪 Test d'extraction LLM...")
    print(f"📝 Longueur du texte: {sample_text}")
    
    result = extract_products_with_llm(
        text_batch=sample_text, 
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
