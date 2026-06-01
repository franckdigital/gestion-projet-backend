from django.contrib import admin
from .models import (
    PlanPassationMarche, DemandeAchat, AppelOffre,
    SoumissionnaireOffre, ContratMarche, AvenantContrat,
)


# ─── Plan de passation des marchés ───────────────────────────────────────────

class DemandeAchatInline(admin.TabularInline):
    model = DemandeAchat
    extra = 0
    fields = ['reference', 'titre', 'type_marche', 'priorite', 'statut', 'budget_estime']
    readonly_fields = ['reference']
    show_change_link = True


class AppelOffreInline(admin.TabularInline):
    model = AppelOffre
    extra = 0
    fields = ['reference', 'titre', 'type_marche', 'statut', 'budget_estime', 'date_limite_soumission']
    readonly_fields = ['reference']
    show_change_link = True


@admin.register(PlanPassationMarche)
class PlanPassationMarcheAdmin(admin.ModelAdmin):
    list_display = [
        'annee', 'titre', 'statut', 'programme', 'projet',
        'budget_total_prevu', 'cree_par', 'valide_par', 'date_validation',
    ]
    list_filter = ['statut', 'annee', 'programme', 'projet']
    search_fields = ['titre', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DemandeAchatInline, AppelOffreInline]
    fieldsets = (
        ('Identification', {
            'fields': ('annee', 'titre', 'description', 'statut')
        }),
        ('Rattachements', {
            'fields': ('programme', 'projet')
        }),
        ('Budget', {
            'fields': ('budget_total_prevu',)
        }),
        ('Validation', {
            'fields': ('cree_par', 'valide_par', 'date_validation')
        }),
        ('Méta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ─── Demande d'achat ─────────────────────────────────────────────────────────

@admin.register(DemandeAchat)
class DemandeAchatAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'titre', 'type_marche', 'priorite', 'statut',
        'budget_estime', 'demandeur', 'valideur', 'date_besoin', 'created_at',
    ]
    list_filter = ['statut', 'priorite', 'type_marche', 'programme', 'projet']
    search_fields = ['reference', 'titre', 'description']
    readonly_fields = ['reference', 'created_at', 'updated_at', 'date_validation']
    fieldsets = (
        ('Identification', {
            'fields': ('reference', 'titre', 'description', 'type_marche', 'priorite', 'statut')
        }),
        ('Rattachements', {
            'fields': ('programme', 'projet', 'plan_passation')
        }),
        ('Détails', {
            'fields': ('budget_estime', 'date_besoin', 'justification', 'specifications_techniques')
        }),
        ('Acteurs', {
            'fields': ('demandeur', 'valideur', 'date_validation', 'motif_rejet')
        }),
        ('Méta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ─── Appel d'offres ──────────────────────────────────────────────────────────

class SoumissionnaireOffreInline(admin.TabularInline):
    model = SoumissionnaireOffre
    extra = 0
    fields = [
        'nom_entreprise', 'pays', 'montant_offre', 'statut',
        'note_technique', 'note_financiere', 'note_globale',
    ]
    readonly_fields = ['note_globale']
    show_change_link = True


@admin.register(AppelOffre)
class AppelOffreAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'titre', 'type_marche', 'statut',
        'budget_estime', 'date_publication', 'date_limite_soumission',
        'responsable', 'nb_lots',
    ]
    list_filter = ['statut', 'type_marche', 'programme', 'projet']
    search_fields = ['reference', 'titre', 'description']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [SoumissionnaireOffreInline]
    fieldsets = (
        ('Identification', {
            'fields': ('reference', 'titre', 'description', 'type_marche', 'statut')
        }),
        ('Rattachements', {
            'fields': ('demande_achat', 'plan_passation', 'programme', 'projet')
        }),
        ('Budget et lots', {
            'fields': ('budget_estime', 'nb_lots')
        }),
        ('Calendrier', {
            'fields': ('date_publication', 'date_limite_soumission', 'date_ouverture_plis', 'lieu_depot')
        }),
        ('Documents et critères', {
            'fields': ('criteres_evaluation', 'documents_requis', 'fichier_dao')
        }),
        ('Responsable', {
            'fields': ('responsable',)
        }),
        ('Méta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ─── Soumissionnaire ─────────────────────────────────────────────────────────

@admin.register(SoumissionnaireOffre)
class SoumissionnaireOffreAdmin(admin.ModelAdmin):
    list_display = [
        'nom_entreprise', 'appel_offre', 'pays', 'montant_offre', 'statut',
        'note_technique', 'note_financiere', 'note_globale', 'date_soumission',
    ]
    list_filter = ['statut', 'pays', 'appel_offre']
    search_fields = ['nom_entreprise', 'email', 'contact']
    readonly_fields = ['note_globale', 'created_at']
    fieldsets = (
        ('Entreprise', {
            'fields': ('nom_entreprise', 'pays', 'contact', 'email', 'telephone')
        }),
        ('Offre', {
            'fields': ('appel_offre', 'montant_offre', 'date_soumission', 'fichier_offre', 'statut')
        }),
        ('Évaluation', {
            'fields': (
                'note_technique', 'note_financiere', 'note_globale',
                'poids_technique', 'poids_financier', 'observations'
            )
        }),
        ('Méta', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


# ─── Contrat marché ──────────────────────────────────────────────────────────

class AvenantContratInline(admin.TabularInline):
    model = AvenantContrat
    extra = 0
    fields = [
        'numero_avenant', 'motif', 'montant_supplementaire',
        'nouveau_montant_ttc', 'extension_jours', 'nouvelle_date_fin',
        'date_signature', 'statut',
    ]
    readonly_fields = ['created_at']
    show_change_link = True


@admin.register(ContratMarche)
class ContratMarcheAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'titre', 'type_contrat', 'statut',
        'prestataire_nom', 'montant_ttc', 'devise',
        'date_signature', 'date_fin_prevue', 'gestionnaire',
    ]
    list_filter = ['statut', 'type_contrat', 'devise', 'programme', 'projet']
    search_fields = ['reference', 'titre', 'prestataire_nom', 'objet']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [AvenantContratInline]
    fieldsets = (
        ('Identification', {
            'fields': ('reference', 'titre', 'type_contrat', 'statut')
        }),
        ('Sources', {
            'fields': ('appel_offre', 'soumissionnaire', 'programme', 'projet')
        }),
        ('Prestataire', {
            'fields': ('prestataire_nom', 'prestataire_contact', 'prestataire_email')
        }),
        ('Financier', {
            'fields': ('montant_ttc', 'devise', 'montant_realise', 'conditions_paiement')
        }),
        ('Calendrier', {
            'fields': ('date_signature', 'date_debut', 'date_fin_prevue', 'date_fin_reelle')
        }),
        ('Contenu', {
            'fields': ('objet', 'garanties', 'penalites', 'fichier_contrat', 'notes')
        }),
        ('Gestionnaire', {
            'fields': ('gestionnaire',)
        }),
        ('Méta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ─── Avenant contrat ─────────────────────────────────────────────────────────

@admin.register(AvenantContrat)
class AvenantContratAdmin(admin.ModelAdmin):
    list_display = [
        'contrat', 'numero_avenant', 'motif', 'statut',
        'montant_supplementaire', 'extension_jours',
        'nouvelle_date_fin', 'date_signature',
    ]
    list_filter = ['statut', 'motif', 'contrat']
    search_fields = ['contrat__reference', 'contrat__titre', 'description']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Contrat', {
            'fields': ('contrat', 'numero_avenant', 'motif', 'description', 'statut')
        }),
        ('Modifications financières', {
            'fields': ('montant_supplementaire', 'nouveau_montant_ttc')
        }),
        ('Modifications calendrier', {
            'fields': ('extension_jours', 'nouvelle_date_fin', 'date_signature')
        }),
        ('Document', {
            'fields': ('fichier',)
        }),
        ('Méta', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
