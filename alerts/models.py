import uuid
from django.db import models
from django.contrib.auth.models import User
from competitors.models import Competitor, Product


class Alert(models.Model):
    """
    Alerte générée lors de changements détectés
    """
    ALERT_TYPE_CHOICES = [
        ('price_increase', 'Augmentation de prix'),
        ('price_decrease', 'Diminution de prix'),
        ('new_product', 'Nouveau produit'),
        ('product_unavailable', 'Produit indisponible'),
        ('promotion_detected', 'Promotion détectée'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts', verbose_name='Utilisateur')
    competitor = models.ForeignKey(Competitor, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Concurrent')
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Produit')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES, verbose_name='Type d\'alerte')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium', verbose_name='Sévérité')
    title = models.CharField(max_length=255, verbose_name='Titre')
    message = models.TextField(verbose_name='Message')
    old_value = models.JSONField(null=True, blank=True, verbose_name='Ancienne valeur')
    new_value = models.JSONField(verbose_name='Nouvelle valeur')
    is_read = models.BooleanField(default=False, verbose_name='Lu')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    
    class Meta:
        db_table = 'alerts'
        verbose_name = 'Alerte'
        verbose_name_plural = 'Alertes'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['alert_type']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_severity_display()}"
