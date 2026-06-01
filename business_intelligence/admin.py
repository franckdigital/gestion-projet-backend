from django.contrib import admin
from .models import (
    TableauBord, WidgetTableauBord, PartageTableauBord,
    DataWarehouseSnapshot, RapportBI,
    DatamartFinance, DatamartSE,
    ConnecteurBI, KPIPersonnalise,
)


class WidgetTableauBordInline(admin.TabularInline):
    model = WidgetTableauBord
    extra = 0
    fields = ['titre', 'type_widget', 'source_donnees', 'colonne', 'ligne',
              'largeur', 'hauteur', 'actif']


class PartageTableauBordInline(admin.TabularInline):
    model = PartageTableauBord
    extra = 0
    fields = ['utilisateur', 'niveau']


@admin.register(TableauBord)
class TableauBordAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_dashboard', 'proprietaire', 'est_public',
                    'est_defaut', 'actif', 'created_at']
    list_filter = ['type_dashboard', 'est_public', 'est_defaut', 'actif']
    search_fields = ['nom', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WidgetTableauBordInline, PartageTableauBordInline]


@admin.register(WidgetTableauBord)
class WidgetTableauBordAdmin(admin.ModelAdmin):
    list_display = ['titre', 'tableau_bord', 'type_widget', 'source_donnees',
                    'colonne', 'ligne', 'actif']
    list_filter = ['type_widget', 'source_donnees', 'actif']
    search_fields = ['titre', 'tableau_bord__nom']
    readonly_fields = ['created_at']


@admin.register(DataWarehouseSnapshot)
class DataWarehouseSnapshotAdmin(admin.ModelAdmin):
    list_display = ['type_snapshot', 'periode_debut', 'periode_fin',
                    'nb_enregistrements', 'taille_ko', 'valide', 'created_at']
    list_filter = ['type_snapshot', 'valide']
    readonly_fields = ['created_at', 'taille_ko', 'nb_enregistrements']


@admin.register(RapportBI)
class RapportBIAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_rapport', 'periode', 'statut', 'format_export',
                    'genere_par', 'genere_par_ia', 'created_at']
    list_filter = ['type_rapport', 'statut', 'periode', 'format_export', 'genere_par_ia']
    search_fields = ['titre']
    readonly_fields = ['donnees_calculees', 'statut', 'created_at', 'updated_at']


@admin.register(DatamartFinance)
class DatamartFinanceAdmin(admin.ModelAdmin):
    list_display = ['programme', 'projet', 'annee', 'mois', 'trimestre',
                    'budget_prevu', 'budget_realise', 'taux_execution']
    list_filter = ['annee', 'trimestre', 'programme']
    readonly_fields = ['calculated_at']


@admin.register(DatamartSE)
class DatamartSEAdmin(admin.ModelAdmin):
    list_display = ['programme', 'projet', 'annee', 'trimestre',
                    'nb_indicateurs', 'nb_atteints', 'taux_realisation_moyen']
    list_filter = ['annee', 'trimestre', 'programme']
    readonly_fields = ['calculated_at']


@admin.register(ConnecteurBI)
class ConnecteurBIAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_outil', 'statut', 'derniere_synchro', 'created_at']
    list_filter = ['type_outil', 'statut']
    readonly_fields = ['derniere_synchro', 'created_at']


@admin.register(KPIPersonnalise)
class KPIPersonnaliseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'source_donnees', 'unite', 'valeur_actuelle',
                    'statut_calcul', 'actif', 'derniere_maj']
    list_filter = ['source_donnees', 'statut_calcul', 'actif', 'unite']
    search_fields = ['nom', 'description']
    readonly_fields = ['valeur_actuelle', 'statut_calcul', 'derniere_maj', 'created_at']
