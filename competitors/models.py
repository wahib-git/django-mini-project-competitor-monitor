import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Competitor(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competitors', verbose_name='Utilisateur')
    name = models.CharField(max_length=255, verbose_name='Nom du concurrent')
    base_url = models.URLField(verbose_name='URL du site')
   
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    last_scraped_at = models.DateTimeField(null=True, blank=True, verbose_name='Dernier scraping')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Dernière modification')
    
    class Meta:
        db_table = 'competitors'
        verbose_name = 'Concurrent'
        verbose_name_plural = 'Concurrents'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_scraped_at']),
        ]
        unique_together = [['user', 'base_url']]  # Un utilisateur ne peut pas ajouter le même site 2 fois
    
    def __str__(self):
        return f"{self.name} ({self.base_url})"


class Product(models.Model):
    """
    Représente un produit détecté chez un concurrent
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, related_name='products', verbose_name='Concurrent')
    product_identifier = models.CharField(max_length=255, verbose_name='Identifiant produit (SKU)', help_text='SKU ou code produit unique')
    name = models.CharField(max_length=500, verbose_name='Nom du produit')
    description = models.TextField(null=True, blank=True, verbose_name='Description')
    category = models.CharField(max_length=255, null=True, blank=True, verbose_name='Catégorie')
    image_url = models.URLField(null=True, blank=True, verbose_name='URL de l\'image')
    product_url = models.URLField(verbose_name='URL du produit')
    current_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Prix actuel'
    )
    currency = models.CharField(max_length=3, default='EUR', verbose_name='Devise')
    is_available = models.BooleanField(default=True, verbose_name='Disponible')
    first_detected_at = models.DateTimeField(auto_now_add=True, verbose_name='Première détection')
    last_updated_at = models.DateTimeField(auto_now=True, verbose_name='Dernière mise à jour')
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        indexes = [
            models.Index(fields=['competitor', 'product_identifier']),
            models.Index(fields=['category']),
            models.Index(fields=['current_price']),
            models.Index(fields=['last_updated_at']),
        ]
        unique_together = [['competitor', 'product_identifier']]  # Un produit unique par concurrent
    
    def __str__(self):
        return f"{self.name} - {self.current_price} {self.currency}"


class PriceHistory(models.Model):
    """
    Historique des prix pour chaque produit
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history', verbose_name='Produit')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Prix'
    )
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'enregistrement')
    scrape_session_id = models.UUIDField(null=True, blank=True, verbose_name='ID de session de scraping')
    
    class Meta:
        db_table = 'price_history'
        verbose_name = 'Historique de prix'
        verbose_name_plural = 'Historiques de prix'
        indexes = [
            models.Index(fields=['product', 'recorded_at']),
        ]
        ordering = ['-recorded_at']  # Plus récent en premier
    
    def __str__(self):
        return f"{self.product.name} - {self.price} ({self.recorded_at.strftime('%Y-%m-%d %H:%M')})"


class ScrapeSession(models.Model):
    """
    Trace de chaque session de scraping (pour audit et debugging)
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, related_name='scrape_sessions', verbose_name='Concurrent')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Statut')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Début')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Fin')
    products_found = models.IntegerField(default=0, verbose_name='Produits trouvés')
    errors = models.JSONField(null=True, blank=True, verbose_name='Erreurs')
    llm_tokens_used = models.IntegerField(default=0, verbose_name='Tokens LLM utilisés')
    raw_html = models.TextField(null=True, blank=True, verbose_name='HTML brut (debug)')
    
    class Meta:
        db_table = 'scrape_sessions'
        verbose_name = 'Session de scraping'
        verbose_name_plural = 'Sessions de scraping'
        indexes = [
            models.Index(fields=['competitor', 'started_at']),
            models.Index(fields=['status']),
        ]
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Scrape {self.competitor.name} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
