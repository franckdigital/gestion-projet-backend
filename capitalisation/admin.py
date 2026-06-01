from django.contrib import admin
from .models import (
    FicheCapitalisation, EntreeBibliotheque, CommentaireFiche, CentreConnaissance,
)


# ─── FicheCapitalisation ─────────────────────────────────────────────────────

class CommentaireFicheInline(admin.TabularInline):
    model = CommentaireFiche
    extra = 0
    fields = ['auteur', 'contenu', 'en_reponse_a', 'created_at']
    readonly_fields = ['created_at']


@admin.register(FicheCapitalisation)
class FicheCapitalisationAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'titre', 'type_fiche', 'domaine', 'statut',
        'programme', 'projet', 'auteur', 'genere_par_ia',
        'nb_consultations', 'nb_favoris', 'created_at',
    ]
    list_filter = ['type_fiche', 'domaine', 'statut', 'niveau_replicabilite', 'genere_par_ia']
    search_fields = ['reference', 'titre', 'mots_cles', 'lecon_principale']
    readonly_fields = ['reference', 'nb_consultations', 'nb_favoris', 'created_at', 'updated_at']
    filter_horizontal = ['contributeurs']
    list_select_related = ['auteur', 'programme', 'projet']
    inlines = [CommentaireFicheInline]
    fieldsets = (
        ('Identification', {
            'fields': ('reference', 'titre', 'type_fiche', 'domaine', 'statut'),
        }),
        ('Rattachements', {'fields': ('programme', 'projet')}),
        ('Contenu', {
            'fields': (
                'contexte', 'probleme_defi', 'solution_approche',
                'resultats_obtenus', 'lecon_principale', 'recommandation',
                'conditions_replicabilite', 'indicateurs_succes',
            ),
        }),
        ('Classification', {
            'fields': (
                'tags', 'mots_cles', 'niveau_replicabilite',
                'periode_reference', 'zone_geographique', 'public_cible',
            ),
        }),
        ('Auteurs & Validation', {
            'fields': ('auteur', 'contributeurs', 'valide_par', 'date_validation'),
        }),
        ('Fichiers', {'fields': ('fichier_principal', 'document_ged')}),
        ('Statistiques', {
            'fields': ('genere_par_ia', 'nb_consultations', 'nb_favoris'),
            'classes': ('collapse',),
        }),
        ('Méta', {'fields': ('created_at', 'updated_at')}),
    )


# ─── EntreeBibliotheque ───────────────────────────────────────────────────────

@admin.register(EntreeBibliotheque)
class EntreeBibliothequeAdmin(admin.ModelAdmin):
    list_display = [
        'titre', 'categorie', 'domaine', 'auteur', 'organisation',
        'annee_publication', 'langue', 'est_public', 'nb_telechargements', 'ajoute_par',
    ]
    list_filter = ['categorie', 'domaine', 'langue', 'est_public']
    search_fields = ['titre', 'description', 'auteur', 'organisation', 'mots_cles']
    readonly_fields = ['nb_telechargements', 'created_at', 'updated_at']
    list_select_related = ['ajoute_par', 'programme', 'projet']
    fieldsets = (
        ('Identification', {'fields': ('titre', 'categorie', 'sous_categorie', 'domaine')}),
        ('Auteur & Source', {'fields': ('auteur', 'organisation', 'annee_publication', 'langue')}),
        ('Contenu', {'fields': ('description', 'fichier', 'url_externe')}),
        ('Classification', {'fields': ('mots_cles', 'tags')}),
        ('Visibilité & Rattachements', {'fields': ('est_public', 'programme', 'projet')}),
        ('Statistiques', {'fields': ('nb_telechargements',), 'classes': ('collapse',)}),
        ('Méta', {'fields': ('ajoute_par', 'created_at', 'updated_at')}),
    )


# ─── CommentaireFiche ─────────────────────────────────────────────────────────

@admin.register(CommentaireFiche)
class CommentaireFicheAdmin(admin.ModelAdmin):
    list_display = ['fiche', 'auteur', 'en_reponse_a', 'contenu_court', 'created_at']
    list_filter = ['fiche']
    search_fields = ['contenu', 'fiche__titre', 'auteur__email']
    readonly_fields = ['created_at']
    list_select_related = ['fiche', 'auteur', 'en_reponse_a']

    def contenu_court(self, obj):
        return obj.contenu[:80] + ('...' if len(obj.contenu) > 80 else '')
    contenu_court.short_description = 'Contenu'


# ─── CentreConnaissance ───────────────────────────────────────────────────────

@admin.register(CentreConnaissance)
class CentreConnaissanceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'domaine', 'responsable', 'actif', 'nb_fiches_display',
                    'nb_entrees_display', 'couleur']
    list_filter = ['domaine', 'actif']
    search_fields = ['nom', 'description']
    readonly_fields = ['created_at']
    filter_horizontal = ['fiches', 'entrees_bibliotheque']
    list_select_related = ['responsable']
    fieldsets = (
        ('Identification', {'fields': ('nom', 'description', 'domaine', 'actif')}),
        ('Apparence', {'fields': ('icone', 'couleur')}),
        ('Responsable', {'fields': ('responsable',)}),
        ('Ressources', {
            'fields': ('fiches', 'entrees_bibliotheque'),
            'classes': ('collapse',),
        }),
        ('Méta', {'fields': ('created_at',)}),
    )

    def nb_fiches_display(self, obj):
        return obj.fiches.count()
    nb_fiches_display.short_description = 'Nb fiches'

    def nb_entrees_display(self, obj):
        return obj.entrees_bibliotheque.count()
    nb_entrees_display.short_description = 'Nb entrées biblio.'
