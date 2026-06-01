from django.contrib import admin
from .models import (
    ActiviteExecution, AffectationRessource, DependanceActivite, RapportActivite,
    Tache, ChecklistItem, DependanceTache, CommentaireTache, HistoriqueTache,
    Livrable, VersionLivrable, ValidationLivrable, CommentaireLivrable,
    Reunion, ParticipantReunion, PointOrdreJour, CompteRendu,
    DecisionReunion, ActionReunion,
    Mission, MembreMission, OrdreMission, RapportMission, RapportAvancement,
)


# ─── M13 : Activités ─────────────────────────────────────────────────────────

class AffectationRessourceInline(admin.TabularInline):
    model = AffectationRessource
    extra = 0
    fields = ['type_ressource', 'utilisateur', 'nom_ressource', 'taux_affectation', 'date_debut', 'date_fin']


@admin.register(ActiviteExecution)
class ActiviteExecutionAdmin(admin.ModelAdmin):
    list_display = ['code', 'intitule', 'projet', 'responsable', 'statut', 'priorite',
                    'date_debut_prevue', 'date_fin_prevue', 'taux_avancement']
    list_filter = ['statut', 'priorite', 'projet', 'programme']
    search_fields = ['code', 'intitule', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AffectationRessourceInline]
    fieldsets = (
        ('Identification', {'fields': ('code', 'intitule', 'description', 'priorite', 'statut', 'ordre')}),
        ('Rattachements', {'fields': ('projet', 'programme', 'parent', 'activite_pa', 'plan_travail_activite')}),
        ('Responsable', {'fields': ('responsable', 'co_responsables')}),
        ('Planification', {'fields': ('date_debut_prevue', 'date_fin_prevue', 'date_debut_reelle', 'date_fin_reelle')}),
        ('Budget & Avancement', {'fields': ('budget_prevu', 'budget_realise', 'taux_avancement')}),
        ('Workflow', {'fields': ('valide_par', 'date_validation', 'motif_suspension')}),
        ('Méta', {'fields': ('tags', 'notes', 'created_by', 'created_at', 'updated_at')}),
    )


@admin.register(AffectationRessource)
class AffectationRessourceAdmin(admin.ModelAdmin):
    list_display = ['activite', 'type_ressource', 'utilisateur', 'nom_ressource', 'taux_affectation']
    list_filter = ['type_ressource']
    search_fields = ['nom_ressource', 'activite__code']


@admin.register(DependanceActivite)
class DependanceActiviteAdmin(admin.ModelAdmin):
    list_display = ['activite_source', 'activite_cible', 'type_dependance', 'decalage_jours']
    list_filter = ['type_dependance']


@admin.register(RapportActivite)
class RapportActiviteAdmin(admin.ModelAdmin):
    list_display = ['activite', 'periode', 'date_rapport', 'taux_realisation', 'statut', 'redacteur']
    list_filter = ['periode', 'statut']
    search_fields = ['activite__code']


# ─── M14 : Tâches ─────────────────────────────────────────────────────────────

class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    fields = ['libelle', 'complete', 'ordre']


@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = ['titre', 'activite', 'assignee', 'statut', 'priorite', 'date_echeance', 'taux_avancement']
    list_filter = ['statut', 'priorite', 'activite__projet']
    search_fields = ['code', 'titre']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ChecklistItemInline]
    fieldsets = (
        ('Identification', {'fields': ('code', 'titre', 'description', 'priorite', 'statut', 'ordre')}),
        ('Rattachements', {'fields': ('activite', 'parent')}),
        ('Assignation', {'fields': ('assignee', 'co_assignees')}),
        ('Planification', {'fields': ('date_debut', 'date_echeance', 'date_completion')}),
        ('Charge', {'fields': ('estimation_heures', 'heures_realisees', 'taux_avancement')}),
        ('Méta', {'fields': ('tags', 'notes', 'created_by', 'created_at', 'updated_at')}),
    )


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'tache', 'complete', 'ordre', 'complete_par', 'date_completion']
    list_filter = ['complete']
    search_fields = ['libelle', 'tache__titre']


@admin.register(DependanceTache)
class DependanceTacheAdmin(admin.ModelAdmin):
    list_display = ['tache_source', 'tache_cible', 'type_dependance']


@admin.register(CommentaireTache)
class CommentaireTacheAdmin(admin.ModelAdmin):
    list_display = ['tache', 'auteur', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HistoriqueTache)
class HistoriqueTacheAdmin(admin.ModelAdmin):
    list_display = ['tache', 'user', 'action', 'ancien_statut', 'nouveau_statut', 'created_at']
    readonly_fields = ['created_at']


# ─── M15 : Livrables ──────────────────────────────────────────────────────────

class VersionLivrableInline(admin.TabularInline):
    model = VersionLivrable
    extra = 0
    fields = ['numero_version', 'fichier', 'url_externe', 'est_courante', 'uploaded_by']
    readonly_fields = ['date_upload']


class ValidationLivrableInline(admin.TabularInline):
    model = ValidationLivrable
    extra = 0
    fields = ['etape', 'validateur', 'statut', 'commentaire', 'date_validation', 'ordre']
    readonly_fields = ['date_validation']


@admin.register(Livrable)
class LivrableAdmin(admin.ModelAdmin):
    list_display = ['code', 'titre', 'type_livrable', 'projet', 'responsable',
                    'date_prevue', 'statut', 'version_courante']
    list_filter = ['statut', 'type_livrable', 'projet']
    search_fields = ['code', 'titre']
    readonly_fields = ['version_courante', 'created_at', 'updated_at']
    inlines = [VersionLivrableInline, ValidationLivrableInline]


@admin.register(VersionLivrable)
class VersionLivrableAdmin(admin.ModelAdmin):
    list_display = ['livrable', 'numero_version', 'est_courante', 'uploaded_by', 'date_upload']
    list_filter = ['est_courante']
    readonly_fields = ['date_upload']


@admin.register(ValidationLivrable)
class ValidationLivrableAdmin(admin.ModelAdmin):
    list_display = ['livrable', 'etape', 'validateur', 'statut', 'date_validation', 'ordre']
    list_filter = ['etape', 'statut']


@admin.register(CommentaireLivrable)
class CommentaireLivrableAdmin(admin.ModelAdmin):
    list_display = ['livrable', 'auteur', 'created_at']
    readonly_fields = ['created_at']


# ─── M16 : Réunions ───────────────────────────────────────────────────────────

class ParticipantReunionInline(admin.TabularInline):
    model = ParticipantReunion
    extra = 0
    fields = ['utilisateur', 'nom_externe', 'email_externe', 'type_participant', 'statut_presence']


class PointOrdreJourInline(admin.TabularInline):
    model = PointOrdreJour
    extra = 0
    fields = ['ordre', 'intitule', 'responsable', 'duree_prevue']


@admin.register(Reunion)
class ReunionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'objet', 'type_reunion', 'statut', 'date', 'heure_debut',
                    'lieu', 'plateforme', 'organisateur']
    list_filter = ['type_reunion', 'statut', 'plateforme', 'projet']
    search_fields = ['reference', 'objet', 'lieu']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [ParticipantReunionInline, PointOrdreJourInline]
    fieldsets = (
        ('Identification', {'fields': ('reference', 'type_reunion', 'objet', 'description', 'statut')}),
        ('Rattachements', {'fields': ('projet', 'programme', 'organisateur')}),
        ('Planification', {'fields': ('date', 'heure_debut', 'heure_fin', 'lieu')}),
        ('Visioconférence', {'fields': ('plateforme', 'lien_visio', 'id_reunion_virtuelle')}),
        ('Rappels', {'fields': ('rappel_envoye', 'rappel_24h')}),
        ('Méta', {'fields': ('notes', 'created_by', 'created_at', 'updated_at')}),
    )


@admin.register(ParticipantReunion)
class ParticipantReunionAdmin(admin.ModelAdmin):
    list_display = ['reunion', 'utilisateur', 'nom_externe', 'type_participant', 'statut_presence']
    list_filter = ['type_participant', 'statut_presence']


@admin.register(PointOrdreJour)
class PointOrdreJourAdmin(admin.ModelAdmin):
    list_display = ['reunion', 'ordre', 'intitule', 'responsable', 'duree_prevue']


class DecisionReunionInline(admin.TabularInline):
    model = DecisionReunion
    extra = 0
    fields = ['intitule', 'responsable', 'echeance', 'statut']


class ActionReunionInline(admin.TabularInline):
    model = ActionReunion
    extra = 0
    fields = ['libelle', 'responsable', 'echeance', 'statut', 'tache_generee']


@admin.register(CompteRendu)
class CompteRenduAdmin(admin.ModelAdmin):
    list_display = ['reunion', 'redacteur', 'statut', 'genere_par_ia', 'created_at']
    list_filter = ['statut', 'genere_par_ia']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DecisionReunionInline, ActionReunionInline]


@admin.register(DecisionReunion)
class DecisionReunionAdmin(admin.ModelAdmin):
    list_display = ['compte_rendu', 'intitule', 'responsable', 'echeance', 'statut']
    list_filter = ['statut']


@admin.register(ActionReunion)
class ActionReunionAdmin(admin.ModelAdmin):
    list_display = ['compte_rendu', 'libelle', 'responsable', 'echeance', 'statut', 'tache_generee']
    list_filter = ['statut']


# ─── M16 : Missions ───────────────────────────────────────────────────────────

class MembreMissionInline(admin.TabularInline):
    model = MembreMission
    extra = 0
    fields = ['user', 'role_mission', 'indemnite_journaliere', 'frais_transport',
              'frais_hebergement', 'autres_frais']


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'objet', 'type_mission', 'statut', 'destination',
                    'date_debut', 'date_fin', 'budget_prevu', 'demandeur']
    list_filter = ['type_mission', 'statut', 'projet']
    search_fields = ['reference', 'objet', 'destination']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [MembreMissionInline]
    fieldsets = (
        ('Identification', {'fields': ('reference', 'objet', 'type_mission', 'description', 'statut')}),
        ('Rattachements', {'fields': ('projet', 'programme', 'demandeur')}),
        ('Destination', {'fields': ('lieu_depart', 'destination', 'pays_destination')}),
        ('Période', {'fields': ('date_debut', 'date_fin')}),
        ('Budget', {'fields': ('budget_prevu', 'budget_realise')}),
        ('Approbation', {'fields': ('approuve_par', 'date_approbation')}),
        ('Objectifs', {'fields': ('objectifs', 'resultats_attendus')}),
        ('Méta', {'fields': ('notes', 'created_at', 'updated_at')}),
    )


@admin.register(MembreMission)
class MembreMissionAdmin(admin.ModelAdmin):
    list_display = ['mission', 'user', 'role_mission', 'indemnite_journaliere',
                    'frais_transport', 'frais_hebergement', 'autres_frais']
    list_filter = ['role_mission']


@admin.register(OrdreMission)
class OrdreMissionAdmin(admin.ModelAdmin):
    list_display = ['mission', 'numero', 'date_emission', 'signataire', 'statut']
    list_filter = ['statut']
    readonly_fields = ['numero', 'date_emission', 'created_at']


@admin.register(RapportMission)
class RapportMissionAdmin(admin.ModelAdmin):
    list_display = ['mission', 'redacteur', 'statut', 'date_soumission', 'valide_par']
    list_filter = ['statut']
    readonly_fields = ['created_at']


# ─── Rapport d'avancement ─────────────────────────────────────────────────────

@admin.register(RapportAvancement)
class RapportAvancementAdmin(admin.ModelAdmin):
    list_display = ['projet', 'activite', 'periode', 'date_rapport', 'taux_realisation',
                    'statut', 'redacteur']
    list_filter = ['periode', 'statut', 'projet']
    readonly_fields = ['created_at']
