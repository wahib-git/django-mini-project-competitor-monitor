from django import forms
from .models import Competitor


class CompetitorForm(forms.ModelForm):
    class Meta:
        model = Competitor
        fields = ['name', 'base_url', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Amazon, eBay, etc.'
            }),
            'base_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.exemple.com'
            }),

            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nom du concurrent',
            'base_url': 'URL du site web',
            'scrape_frequency_hours': 'Fréquence de scraping recommandée',
            'is_active': 'Actif',
        }
