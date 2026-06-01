from django.contrib import admin
from .models import (
    ZoneSIG, CoucheCartographique, PointCartographie,
    InfrastructureSIG, CarteSIG,
)


# ─── ZoneSIG ─────────────────────────────────────────────────────────────────

@admin.register(ZoneSIG)
class ZoneSIGAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'type_zone', 'parent', 'pays', 'superficie_km2',
                    'population', 'actif', 'created_at']
    list_filter = ['type_zone', 'pays', 'actif']
    search_fields = ['nom', 'code', 'pays']
    readonly_fields = ['created_at']
    list_select_related = ['parent']
    fieldsets = (
        ('Identification', {'fields': ('nom', 'code', 'type_zone', 'parent', 'pays', 'actif')}),
        ('Données géographiques', {
            'fields': ('superficie_km2', 'population', 'latitude_centre', 'longitude_centre', 'geojson'),
        }),
        ('Méta', {'fields': ('created_at',)}),
    )


# ─── CoucheCartographique ─────────────────────────────────────────────────────

class PointCartographieInline(admin.TabularInline):
    model = PointCartographie
    extra = 0
    fields = ['titre', 'type_point', 'latitude', 'longitude', 'actif']
    readonly_fields = ['created_at']


@admin.register(CoucheCartographique)
class CoucheCartographiqueAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_couche', 'style_affichage', 'source_fond',
                    'couleur', 'opacite', 'est_visible', 'est_publique', 'ordre', 'cree_par']
    list_filter = ['type_couche', 'style_affichage', 'source_fond', 'est_visible', 'est_publique']
    search_fields = ['nom', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PointCartographieInline]
    fieldsets = (
        ('Identification', {'fields': ('nom', 'description', 'type_couche', 'ordre')}),
        ('Style', {'fields': ('style_affichage', 'source_fond', 'couleur', 'icone', 'opacite', 'configuration')}),
        ('Visibilité', {'fields': ('est_visible', 'est_publique')}),
        ('Filtres', {'fields': ('filtre_programme', 'filtre_projet')}),
        ('Méta', {'fields': ('cree_par', 'created_at', 'updated_at')}),
    )


# ─── PointCartographie ────────────────────────────────────────────────────────

@admin.register(PointCartographie)
class PointCartographieAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_point', 'couche', 'zone', 'latitude', 'longitude',
                    'actif', 'cree_par', 'created_at']
    list_filter = ['type_point', 'actif', 'couche']
    search_fields = ['titre', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['couche', 'zone', 'cree_par']
    fieldsets = (
        ('Identification', {'fields': ('titre', 'description', 'type_point', 'couche')}),
        ('Localisation', {'fields': ('latitude', 'longitude', 'altitude', 'rayon_metres', 'zone')}),
        ('Rattachements', {'fields': ('programme', 'projet')}),
        ('Attributs', {'fields': ('valeur', 'unite', 'couleur', 'icone', 'proprietes', 'image')}),
        ('GPS', {'fields': ('source_gps', 'precision_gps')}),
        ('Méta', {'fields': ('actif', 'cree_par', 'created_at', 'updated_at')}),
    )


# ─── InfrastructureSIG ───────────────────────────────────────────────────────

@admin.register(InfrastructureSIG)
class InfrastructureSIGAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_infrastructure', 'statut', 'zone', 'programme', 'projet',
                    'population_beneficiaire', 'date_mise_en_service', 'cree_par']
    list_filter = ['type_infrastructure', 'statut', 'zone']
    search_fields = ['nom', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['zone', 'programme', 'projet', 'cree_par']
    fieldsets = (
        ('Identification', {'fields': ('nom', 'description', 'type_infrastructure', 'statut')}),
        ('Localisation', {'fields': ('latitude', 'longitude', 'zone')}),
        ('Rattachements', {'fields': ('programme', 'projet')}),
        ('Données', {
            'fields': ('capacite', 'population_beneficiaire', 'date_mise_en_service',
                       'cout_realisation', 'photos', 'proprietes'),
        }),
        ('Méta', {'fields': ('cree_par', 'created_at', 'updated_at')}),
    )


# ─── CarteSIG ─────────────────────────────────────────────────────────────────

@admin.register(CarteSIG)
class CarteSIGAdmin(admin.ModelAdmin):
    list_display = ['nom', 'est_publique', 'est_defaut', 'programme', 'projet',
                    'zoom_defaut', 'cree_par', 'created_at']
    list_filter = ['est_publique', 'est_defaut']
    search_fields = ['nom', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['couches']
    list_select_related = ['programme', 'projet', 'cree_par']
    fieldsets = (
        ('Identification', {'fields': ('nom', 'description')}),
        ('Configuration carte', {
            'fields': ('couches', 'centre_lat', 'centre_lon', 'zoom_defaut'),
        }),
        ('Visibilité', {'fields': ('est_publique', 'est_defaut')}),
        ('Rattachements', {'fields': ('programme', 'projet')}),
        ('Méta', {'fields': ('cree_par', 'created_at', 'updated_at')}),
    )
