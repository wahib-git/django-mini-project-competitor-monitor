import re
def clean_html_content(raw_html):
    """
    Supprime les espaces multiples du HTML brut
    """
    # Remplacer tous les espaces multiples par un seul
    cleaned = re.sub(r'\s+', ' ', raw_html)
    
    # Supprimer espaces entre tags (optionnel)
    cleaned = re.sub(r'>\s+<', '><', cleaned)
    text = cleaned.strip()
    print(f"HTML nettoyé: {text[:50000]}")
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

