from django.contrib import admin
from .models import (
    EmployeProjet, AffectationRH, FeuilleTemps,
    LigneFeuilleTemps, EvaluationPerformance, BesoinFormation,
)


# ─── EmployeProjet ────────────────────────────────────────────────────────────

class AffectationRHInline(admin.TabularInline):
    model = AffectationRH
    extra = 0
    fields = ['projet', 'programme', 'activite', 'role', 'taux_affectation',
              'date_debut', 'date_fin', 'statut']
    readonly_fields = ['created_at']


@admin.register(EmployeProjet)
class EmployeProjetAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom', 'prenom', 'type_personnel', 'statut',
                    'poste', 'specialite', 'niveau_expertise', 'taux_journalier', 'devise']
    list_filter = ['type_personnel', 'statut', 'niveau_expertise', 'devise']
    search_fields = ['matricule', 'nom', 'prenom', 'email', 'poste', 'specialite']
    readonly_fields = ['matricule', 'created_at', 'updated_at']
    inlines = [AffectationRHInline]
    fieldsets = (
        ('Identification', {
            'fields': ('utilisateur', 'matricule', 'nom', 'prenom',
                       'type_personnel', 'statut', 'niveau_expertise')
        }),
        ('Coordonnées', {
            'fields': ('email', 'telephone')
        }),
        ('Poste', {
            'fields': ('poste', 'specialite', 'date_embauche', 'date_fin_contrat')
        }),
        ('Rémunération', {
            'fields': ('taux_journalier', 'devise', 'taux_occupation_max')
        }),
        ('Compétences & Documents', {
            'fields': ('competences', 'cv', 'photo', 'notes')
        }),
        ('Méta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ─── AffectationRH ────────────────────────────────────────────────────────────

@admin.register(AffectationRH)
class AffectationRHAdmin(admin.ModelAdmin):
    list_display = ['employe', 'projet', 'programme', 'activite', 'role',
                    'taux_affectation', 'date_debut', 'date_fin', 'statut']
    list_filter = ['statut']
    search_fields = ['employe__nom', 'employe__prenom', 'employe__matricule', 'role']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Employé', {'fields': ('employe',)}),
        ('Rattachement', {'fields': ('programme', 'projet', 'activite')}),
        ('Mission', {'fields': ('role', 'taux_affectation', 'date_debut', 'date_fin', 'statut')}),
        ('Détails', {'fields': ('description', 'cree_par', 'created_at')}),
    )


# ─── FeuilleTemps ─────────────────────────────────────────────────────────────

class LigneFeuilleTempsInline(admin.TabularInline):
    model = LigneFeuilleTemps
    extra = 0
    fields = ['date', 'projet', 'activite', 'heures', 'description', 'est_conge', 'est_jour_ferie']
    ordering = ['date']


@admin.register(FeuilleTemps)
class FeuilleTempsAdmin(admin.ModelAdmin):
    list_display = ['employe', 'mois', 'annee', 'statut',
                    'total_heures', 'total_jours', 'montant_total', 'valideur']
    list_filter = ['statut', 'annee', 'mois']
    search_fields = ['employe__nom', 'employe__prenom', 'employe__matricule']
    readonly_fields = ['total_heures', 'total_jours', 'montant_total',
                       'date_validation', 'created_at', 'updated_at']
    inlines = [LigneFeuilleTempsInline]
    fieldsets = (
        ('Employé & Période', {'fields': ('employe', 'mois', 'annee')}),
        ('Totaux', {'fields': ('total_heures', 'total_jours', 'montant_total')}),
        ('Workflow', {
            'fields': ('statut', 'valideur', 'date_validation',
                       'motif_rejet', 'commentaire')
        }),
        ('Méta', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(LigneFeuilleTemps)
class LigneFeuilleTempsAdmin(admin.ModelAdmin):
    list_display = ['feuille', 'date', 'projet', 'activite', 'heures', 'est_conge', 'est_jour_ferie']
    list_filter = ['est_conge', 'est_jour_ferie']
    search_fields = ['feuille__employe__nom', 'description']
    ordering = ['feuille', 'date']


# ─── EvaluationPerformance ────────────────────────────────────────────────────

@admin.register(EvaluationPerformance)
class EvaluationPerformanceAdmin(admin.ModelAdmin):
    list_display = ['employe', 'evaluateur', 'projet', 'periode', 'annee',
                    'trimestre', 'statut', 'note_globale', 'date_evaluation']
    list_filter = ['statut', 'periode', 'annee']
    search_fields = ['employe__nom', 'employe__prenom', 'employe__matricule']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Évaluation', {
            'fields': ('employe', 'evaluateur', 'projet',
                       'periode', 'annee', 'trimestre', 'statut', 'date_evaluation')
        }),
        ('Notes & Critères', {
            'fields': ('note_globale', 'criteres')
        }),
        ('Commentaires', {
            'fields': ('points_forts', 'axes_amelioration',
                       'objectifs_periode_suivante', 'commentaire_employe')
        }),
        ('Méta', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


# ─── BesoinFormation ─────────────────────────────────────────────────────────

@admin.register(BesoinFormation)
class BesoinFormationAdmin(admin.ModelAdmin):
    list_display = ['employe', 'intitule', 'domaine', 'priorite', 'statut',
                    'date_souhaitee', 'cout_estime', 'duree_jours', 'organisme_formation']
    list_filter = ['statut', 'priorite']
    search_fields = ['intitule', 'domaine', 'employe__nom', 'employe__prenom', 'organisme_formation']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Employé & Projet', {'fields': ('employe', 'projet')}),
        ('Formation', {
            'fields': ('intitule', 'description', 'domaine',
                       'priorite', 'statut', 'duree_jours')
        }),
        ('Planification', {
            'fields': ('date_souhaitee', 'date_realisation',
                       'organisme_formation', 'lieu', 'attestation')
        }),
        ('Coûts', {'fields': ('cout_estime', 'cout_reel')}),
        ('Méta', {'fields': ('identifie_par', 'created_at'), 'classes': ('collapse',)}),
    )
