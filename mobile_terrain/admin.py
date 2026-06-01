from django.contrib import admin
from .models import SessionTerrain, CollecteTerrain, PointageTerrain, SynchronisationMobile, QRCodeScan


class CollecteTerrainInline(admin.TabularInline):
    model = CollecteTerrain
    extra = 0
    fields = ['type_collecte', 'titre', 'statut', 'date_collecte_locale', 'latitude', 'longitude']
    readonly_fields = ['date_collecte_locale']


@admin.register(SessionTerrain)
class SessionTerrainAdmin(admin.ModelAdmin):
    list_display = ['agent', 'projet', 'statut', 'mode_hors_ligne',
                    'date_debut', 'date_fin', 'date_synchronisation', 'nb_collectes']
    list_filter = ['statut', 'mode_hors_ligne', 'projet']
    search_fields = ['agent__email', 'notes', 'appareil']
    readonly_fields = ['date_debut', 'date_synchronisation']
    inlines = [CollecteTerrainInline]


@admin.register(CollecteTerrain)
class CollecteTerrainAdmin(admin.ModelAdmin):
    list_display = ['session', 'type_collecte', 'titre', 'statut',
                    'latitude', 'longitude', 'date_collecte_locale']
    list_filter = ['type_collecte', 'statut']
    search_fields = ['titre', 'notes', 'adresse_geo']
    readonly_fields = ['created_at']


@admin.register(PointageTerrain)
class PointageTerrainAdmin(admin.ModelAdmin):
    list_display = ['agent', 'type_pointage', 'projet', 'date_heure',
                    'latitude', 'longitude', 'valide']
    list_filter = ['type_pointage', 'valide', 'projet']
    search_fields = ['agent__email', 'notes', 'adresse_geo']
    readonly_fields = ['created_at']


@admin.register(SynchronisationMobile)
class SynchronisationMobileAdmin(admin.ModelAdmin):
    list_display = ['agent', 'date_synchro', 'statut', 'nb_elements_envoyes',
                    'nb_elements_recus', 'nb_erreurs', 'duree_secondes']
    list_filter = ['statut']
    readonly_fields = ['date_synchro']


@admin.register(QRCodeScan)
class QRCodeScanAdmin(admin.ModelAdmin):
    list_display = ['agent', 'contenu_qr', 'type_objet', 'objet_id',
                    'latitude', 'longitude', 'date_scan', 'traite']
    list_filter = ['traite', 'type_objet']
    readonly_fields = ['date_scan']
