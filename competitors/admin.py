from django.contrib import admin
from .models import Competitor, Product, PriceHistory, ScrapeSession


@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url', 'user', 'is_active', 'last_scraped_at', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'base_url', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_scraped_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'competitor', 'current_price', 'currency', 'is_available', 'category', 'last_updated_at')
    list_filter = ('competitor', 'category', 'is_available', 'currency')
    search_fields = ('name', 'product_identifier', 'description')
    readonly_fields = ('id', 'first_detected_at', 'last_updated_at')


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'price', 'recorded_at', 'scrape_session_id')
    list_filter = ('recorded_at',)
    search_fields = ('product__name',)
    readonly_fields = ('id', 'recorded_at')
    date_hierarchy = 'recorded_at'


@admin.register(ScrapeSession)
class ScrapeSessionAdmin(admin.ModelAdmin):
    list_display = ('competitor', 'status', 'started_at', 'completed_at', 'products_found')
    list_filter = ('status', 'started_at')
    search_fields = ('competitor__name',)
    readonly_fields = ('id', 'started_at', 'completed_at')
