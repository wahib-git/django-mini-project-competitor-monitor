from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Competitor, Product, PriceHistory, ScrapeSession
from .forms import CompetitorForm
from .scraper import scrape_competitor_website, analyze_price_changes
from alerts.models import Alert


@login_required
def competitor_list(request):
    """
    Liste de tous les concurrents de l'utilisateur connecté
    """
    competitors = Competitor.objects.filter(user=request.user).annotate(
        product_count=Count('products'),
    ).order_by('-last_scraped_at')
    # Compter les alertes non lues
    unread_alerts_count = Alert.objects.filter(user=request.user, is_read=False).count()
    context = {
        'competitors': competitors,
        'total_competitors': competitors.count(),
        'active_competitors': competitors.filter(is_active=True).count(),
        'unread_alerts_count': unread_alerts_count,  # ✅ AJOUTÉ
    }
    return render(request, 'competitors/competitor_list.html', context)


@login_required
def competitor_add(request):
    """
    Ajouter un nouveau concurrent
    """
    if request.method == 'POST':
        form = CompetitorForm(request.POST)
        if form.is_valid():
            competitor = form.save(commit=False)
            competitor.user = request.user
            competitor.save()
            messages.success(request, f"✅ Concurrent '{competitor.name}' ajouté avec succès !")
            return redirect('competitors:competitor_list')
    else:
        form = CompetitorForm()
    
    return render(request, 'competitors/competitor_form.html', {
        'form': form,
        'title': 'Ajouter un concurrent',
        'button_text': 'Ajouter'
    })


@login_required
def competitor_edit(request, competitor_id):
    """
    Modifier un concurrent existant
    """
    competitor = get_object_or_404(Competitor, id=competitor_id, user=request.user)
    
    if request.method == 'POST':
        form = CompetitorForm(request.POST, instance=competitor)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Concurrent '{competitor.name}' modifié avec succès !")
            return redirect('competitors:competitor_list')
    else:
        form = CompetitorForm(instance=competitor)
    
    return render(request, 'competitors/competitor_form.html', {
        'form': form,
        'title': f'Modifier {competitor.name}',
        'button_text': 'Enregistrer'
    })


@login_required
def competitor_delete(request, competitor_id):
    """
    Supprimer un concurrent
    """
    competitor = get_object_or_404(Competitor, id=competitor_id, user=request.user)
    
    if request.method == 'POST':
        name = competitor.name
        competitor.delete()
        messages.success(request, f"🗑️ Concurrent '{name}' supprimé avec succès !")
        return redirect('competitors:competitor_list')
    
    return render(request, 'competitors/competitor_delete_confirm.html', {
        'competitor': competitor
    })


@login_required
def trigger_scraping(request, competitor_id):
    """
    🔥 Déclencher le scraping manuellement
    """
    competitor = get_object_or_404(Competitor, id=competitor_id, user=request.user)
    
    if request.method == 'POST':
        messages.info(request, f"⏳ Scraping de '{competitor.name}' en cours... Veuillez patienter.")
        
        # Lancer le scraping (synchrone)
        result = scrape_competitor_website(competitor_id)
        
        if result['success']:
            messages.success(
                request, 
                f"✅ Scraping terminé ! {result['products_found']} produits trouvés."
            )
        else:
            messages.error(
                request, 
                f"❌ Erreur de scraping : {result.get('error', 'Erreur inconnue')}"
            )
    
    return redirect('competitors:competitor_list')


@login_required
def trigger_analysis(request, competitor_id):
    """
    🔥 Analyser les changements de prix manuellement
    """
    competitor = get_object_or_404(Competitor, id=competitor_id, user=request.user)
    
    if request.method == 'POST':
        messages.info(request, f"⏳ Analyse des prix de '{competitor.name}' en cours...")
        
        # Lancer l'analyse
        result = analyze_price_changes(competitor_id)
        
        if result['success']:
            if result['alerts_created'] > 0:
                messages.success(
                    request, 
                    f"✅ Analyse terminée ! {result['alerts_created']} nouvelle(s) alerte(s) créée(s)."
                )
            else:
                messages.info(request, "ℹ️ Analyse terminée. Aucun changement significatif détecté.")
        else:
            messages.error(
                request, 
                f"❌ Erreur d'analyse : {result.get('error', 'Erreur inconnue')}"
            )
    
    return redirect('competitors:competitor_list')


@login_required
def product_list(request, competitor_id):
    """
    Liste des produits d'un concurrent spécifique
    """
    competitor = get_object_or_404(Competitor, id=competitor_id, user=request.user)
    products = competitor.products.all().order_by('-last_updated_at')
    
    context = {
        'competitor': competitor,
        'products': products,
        'total_products': products.count(),
    }
    return render(request, 'competitors/product_list.html', context)


@login_required
def product_detail(request, product_id):
    """
    Détail d'un produit avec historique des prix
    """
    product = get_object_or_404(Product, id=product_id)
    
    # Vérifier que l'utilisateur a accès à ce produit
    if product.competitor.user != request.user:
        messages.error(request, "❌ Vous n'avez pas accès à ce produit.")
        return redirect('competitors:competitor_list')
    
    # Récupérer l'historique des prix
    price_history = product.price_history.all()[:30]  # 30 derniers enregistrements
    
    # Préparer les données pour le graphique
    chart_data = {
        'labels': [ph.recorded_at.strftime('%d/%m %H:%M') for ph in reversed(price_history)],
        'prices': [float(ph.price) for ph in reversed(price_history)],
    }
    
    context = {
        'product': product,
        'price_history': price_history,
        'chart_data': chart_data,
    }
    return render(request, 'competitors/product_detail.html', context)
