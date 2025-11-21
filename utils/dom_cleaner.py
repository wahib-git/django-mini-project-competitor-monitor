from bs4 import BeautifulSoup



def clean_html_content(raw_html):
    """
    Nettoie le HTML pour garder seulement le contenu pertinent
    """
    soup = BeautifulSoup(raw_html, 'lxml')

    # Supprimer les tags inutiles
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
        tag.decompose()

    # Extraire le texte
    text = soup.get_text(separator=' ', strip=True)
    print(f"Texte extrait du HTML: {text[:50000]}")  # Log first 50000 chars
    return text


def split_into_batches(text, max_chars=7500):
    """
    Divise le texte en batches pour l'envoi au LLM
    """

    if len(text) <= max_chars:
        return [text]
    
    sentences = text.split('. ')
    batches = []
    current_batch = ""
    
    for sentence in sentences:
        if len(current_batch) + len(sentence) + 2 <= max_chars:
            current_batch += sentence + '. '
        else:
            if current_batch:
                batches.append(current_batch.strip())
            current_batch = sentence + '. '
    
    if current_batch:
        batches.append(current_batch.strip())
    
    return batches

