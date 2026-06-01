from django.contrib import admin
from .models import (
    Vehicule, MissionVehicule, EntretienVehicule,
    Equipement, Magasin, ArticleStock, LigneStock, MouvementStock,
)


# ─── M38 : Parc automobile ────────────────────────────────────────────────────

class MissionVehiculeInline(admin.TabularInline):
    model = MissionVehicule
    extra = 0
    fields = ['objet', 'conducteur', 'date_depart', 'date_retour_reelle',
              'km_depart', 'km_retour', 'statut']
    readonly_fields = ['created_at']
    show_change_link = True


class EntretienVehiculeInline(admin.TabularInline):
    model = EntretienVehicule
    extra = 0
    fields = ['type_entretien', 'date_entretien', 'km_entretien', 'cout',
              'prestataire', 'prochaine_echeance_date']
    readonly_fields = ['created_at']
    show_change_link = True


@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = [
        'immatriculation', 'type_vehicule', 'marque', 'modele', 'annee',
        'statut', 'kilometrage_actuel',
        'date_expiration_assurance', 'date_expiration_vignette',
        'projet', 'programme',
    ]
    list_filter = ['statut', 'type_vehicule', 'marque', 'programme', 'projet']
    search_fields = ['immatriculation', 'marque', 'modele', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MissionVehiculeInline, EntretienVehiculeInline]
    fieldsets = (
        ('Identification', {
            'fields': ('immatriculation', 'type_vehicule', 'marque', 'modele', 'annee', 'couleur'),
        }),
        ('Rattachements', {
            'fields': ('programme', 'projet', 'statut'),
        }),
        ('Kilométrage & Acquisition', {
            'fields': ('kilometrage_actuel', 'date_acquisition', 'valeur_acquisition'),
        }),
        ('Échéances', {
            'fields': (
                'date_expiration_assurance', 'date_expiration_vignette',
                'date_prochain_entretien', 'km_prochain_entretien',
            ),
        }),
        ('Notes', {'fields': ('notes',)}),
        ('Méta', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(MissionVehicule)
class MissionVehiculeAdmin(admin.ModelAdmin):
    list_display = [
        'vehicule', 'conducteur', 'objet', 'statut',
        'lieu_depart', 'lieu_arrivee',
        'date_depart', 'date_retour_reelle',
        'km_depart', 'km_retour', 'cout_carburant',
    ]
    list_filter = ['statut', 'vehicule', 'conducteur', 'projet']
    search_fields = ['objet', 'lieu_depart', 'lieu_arrivee', 'vehicule__immatriculation']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Mission', {
            'fields': ('vehicule', 'conducteur', 'autorise_par', 'objet', 'statut'),
        }),
        ('Itinéraire', {
            'fields': ('lieu_depart', 'lieu_arrivee', 'date_depart', 'date_retour_prevue', 'date_retour_reelle'),
        }),
        ('Kilométrage', {
            'fields': ('km_depart', 'km_retour'),
        }),
        ('Carburant', {
            'fields': ('carburant_litres', 'cout_carburant'),
        }),
        ('Rattachements', {
            'fields': ('projet', 'activite'),
        }),
        ('Observations', {'fields': ('observations',)}),
        ('Méta', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


@admin.register(EntretienVehicule)
class EntretienVehiculeAdmin(admin.ModelAdmin):
    list_display = [
        'vehicule', 'type_entretien', 'date_entretien', 'km_entretien',
        'prestataire', 'cout', 'prochaine_echeance_date', 'effectue_par',
    ]
    list_filter = ['type_entretien', 'vehicule']
    search_fields = ['vehicule__immatriculation', 'description', 'prestataire']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Entretien', {
            'fields': ('vehicule', 'type_entretien', 'description', 'effectue_par'),
        }),
        ('Date & Kilométrage', {
            'fields': ('date_entretien', 'km_entretien'),
        }),
        ('Prestataire & Coût', {
            'fields': ('prestataire', 'cout', 'facture'),
        }),
        ('Prochaine échéance', {
            'fields': ('prochaine_echeance_date', 'prochaine_echeance_km'),
        }),
        ('Méta', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


# ─── M38 : Équipements ────────────────────────────────────────────────────────

@admin.register(Equipement)
class EquipementAdmin(admin.ModelAdmin):
    list_display = [
        'code_inventaire', 'nom', 'type_equipement', 'marque', 'modele',
        'statut', 'affecte_a', 'lieu', 'date_acquisition', 'date_fin_garantie',
        'programme', 'projet',
    ]
    list_filter = ['type_equipement', 'statut', 'programme', 'projet']
    search_fields = ['code_inventaire', 'nom', 'marque', 'modele', 'numero_serie', 'lieu']
    readonly_fields = ['code_inventaire', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('code_inventaire', 'nom', 'type_equipement', 'marque', 'modele', 'numero_serie'),
        }),
        ('Statut & Affectation', {
            'fields': ('statut', 'affecte_a', 'lieu'),
        }),
        ('Rattachements', {
            'fields': ('programme', 'projet'),
        }),
        ('Acquisition & Garantie', {
            'fields': ('date_acquisition', 'valeur_acquisition', 'date_fin_garantie'),
        }),
        ('Description & Photo', {
            'fields': ('description', 'photo'),
        }),
        ('Méta', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


# ─── M38 : Gestion des stocks ─────────────────────────────────────────────────

class LigneStockInline(admin.TabularInline):
    model = LigneStock
    extra = 0
    fields = ['article', 'quantite', 'valeur_totale', 'updated_at']
    readonly_fields = ['valeur_totale', 'updated_at']
    show_change_link = True


@admin.register(Magasin)
class MagasinAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'responsable', 'adresse', 'programme', 'projet', 'actif']
    list_filter = ['actif', 'programme', 'projet']
    search_fields = ['nom', 'code', 'adresse']
    readonly_fields = ['created_at']
    inlines = [LigneStockInline]
    fieldsets = (
        ('Identification', {'fields': ('nom', 'code', 'description', 'actif')}),
        ('Localisation & Responsable', {'fields': ('adresse', 'responsable')}),
        ('Rattachements', {'fields': ('programme', 'projet')}),
        ('Méta', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


@admin.register(ArticleStock)
class ArticleStockAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'unite', 'categorie', 'stock_alerte', 'prix_unitaire', 'actif']
    list_filter = ['unite', 'categorie', 'actif']
    search_fields = ['code', 'nom', 'description', 'categorie']
    readonly_fields = ['code', 'created_at']
    fieldsets = (
        ('Identification', {'fields': ('code', 'nom', 'description', 'categorie')}),
        ('Caractéristiques', {'fields': ('unite', 'prix_unitaire', 'stock_alerte', 'actif')}),
        ('Méta', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


@admin.register(LigneStock)
class LigneStockAdmin(admin.ModelAdmin):
    list_display = ['magasin', 'article', 'quantite', 'valeur_totale', 'updated_at']
    list_filter = ['magasin', 'article__categorie']
    search_fields = ['article__nom', 'article__code', 'magasin__nom']
    readonly_fields = ['valeur_totale', 'updated_at']


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = [
        'article', 'type_mouvement', 'quantite', 'prix_unitaire', 'valeur_totale',
        'magasin_source', 'magasin_destination',
        'date_mouvement', 'effectue_par', 'projet',
    ]
    list_filter = ['type_mouvement', 'article', 'magasin_source', 'magasin_destination', 'projet']
    search_fields = ['article__nom', 'article__code', 'reference_document', 'motif']
    readonly_fields = ['valeur_totale', 'created_at']
    fieldsets = (
        ('Mouvement', {
            'fields': ('article', 'type_mouvement', 'quantite', 'prix_unitaire', 'valeur_totale'),
        }),
        ('Magasins', {
            'fields': ('magasin_source', 'magasin_destination'),
        }),
        ('Référence & Motif', {
            'fields': ('reference_document', 'motif', 'date_mouvement'),
        }),
        ('Rattachements', {
            'fields': ('projet', 'effectue_par'),
        }),
        ('Méta', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
