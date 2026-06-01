from django.contrib import admin
from .models import (
    Indicateur, ValeurCiblePeriode, CollecteIndicateur, AlerteIndicateur,
    FormulaireDynamique, ChampFormulaire, SoumissionFormulaire, ReponseChamp,
    Enquete, SectionEnquete, QuestionEnquete, ReponseEnquete, ReponseQuestion,
    CadreResultats, NiveauResultat, TheorieChangement,
    Evaluation, CritereEvaluation, LeconApprise,
    RapportSE, AnalysePredictive, PointSIG,
    RegistreRisque, PlanMitigation, SuiviRisque, AlerteRisque,
)


# ─── M17 : Indicateurs ───────────────────────────────────────────────────────

class ValeurCiblePeriodeInline(admin.TabularInline):
    model = ValeurCiblePeriode
    extra = 0
    fields = ['annee', 'trimestre', 'valeur_cible', 'valeur_realisee']


class AlerteIndicateurInline(admin.TabularInline):
    model = AlerteIndicateur
    extra = 0
    fields = ['type_alerte', 'niveau', 'message', 'lue']
    readonly_fields = ['date_alerte']


@admin.register(Indicateur)
class IndicateurAdmin(admin.ModelAdmin):
    list_display = ['code', 'intitule', 'type_indicateur', 'statut', 'frequence_collecte',
                    'valeur_cible_globale', 'valeur_realisee', 'responsable', 'actif']
    list_filter = ['type_indicateur', 'statut', 'frequence_collecte', 'actif', 'projet', 'programme']
    search_fields = ['code', 'intitule', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ValeurCiblePeriodeInline, AlerteIndicateurInline]
    fieldsets = (
        ('Identification', {'fields': ('code', 'intitule', 'description', 'type_indicateur', 'actif')}),
        ('Rattachements', {'fields': ('projet', 'programme', 'niveau_resultat')}),
        ('Valeurs', {'fields': ('valeur_baseline', 'date_baseline', 'valeur_cible_globale',
                                'valeur_realisee', 'unite_mesure', 'unite_personnalisee')}),
        ('Collecte', {'fields': ('frequence_collecte', 'mode_calcul', 'formule',
                                 'source_verification', 'methode_collecte')}),
        ('Responsables', {'fields': ('responsable', 'responsable_collecte')}),
        ('Analyse', {'fields': ('hypotheses', 'risques', 'est_disaggregue',
                                'dimensions_disaggregation')}),
        ('Statut', {'fields': ('statut', 'ordre', 'tags', 'notes')}),
        ('Méta', {'fields': ('created_by', 'created_at', 'updated_at')}),
    )


@admin.register(ValeurCiblePeriode)
class ValeurCiblePeriodeAdmin(admin.ModelAdmin):
    list_display = ['indicateur', 'annee', 'trimestre', 'valeur_cible', 'valeur_realisee']
    list_filter = ['annee', 'trimestre']


@admin.register(CollecteIndicateur)
class CollecteIndicateurAdmin(admin.ModelAdmin):
    list_display = ['indicateur', 'date_collecte', 'valeur_reelle', 'collecteur', 'statut']
    list_filter = ['statut', 'date_collecte']
    readonly_fields = ['created_at', 'date_validation']
    fieldsets = (
        ('Données', {'fields': ('indicateur', 'periode', 'date_collecte', 'valeur_reelle',
                                'valeur_disaggregee', 'source_donnee', 'commentaire')}),
        ('Géolocalisation', {'fields': ('latitude', 'longitude', 'altitude')}),
        ('Validation', {'fields': ('statut', 'collecteur', 'valide_par', 'date_validation',
                                   'motif_rejet', 'fichier_justificatif')}),
        ('Méta', {'fields': ('created_at',)}),
    )


@admin.register(AlerteIndicateur)
class AlerteIndicateurAdmin(admin.ModelAdmin):
    list_display = ['indicateur', 'type_alerte', 'niveau', 'lue', 'destinataire', 'date_alerte']
    list_filter = ['type_alerte', 'niveau', 'lue']
    readonly_fields = ['date_alerte', 'date_lecture']


# ─── M18 : Formulaires ───────────────────────────────────────────────────────

class ChampFormulaireInline(admin.TabularInline):
    model = ChampFormulaire
    extra = 0
    fields = ['type_champ', 'libelle', 'obligatoire', 'ordre']


@admin.register(FormulaireDynamique)
class FormulaireDynamiqueAdmin(admin.ModelAdmin):
    list_display = ['code', 'titre', 'statut', 'projet', 'date_ouverture', 'date_fermeture']
    list_filter = ['statut', 'projet', 'allow_offline']
    search_fields = ['code', 'titre']
    readonly_fields = ['code', 'created_at', 'updated_at']
    inlines = [ChampFormulaireInline]


@admin.register(ChampFormulaire)
class ChampFormulaireAdmin(admin.ModelAdmin):
    list_display = ['formulaire', 'type_champ', 'libelle', 'obligatoire', 'ordre']
    list_filter = ['type_champ', 'obligatoire']


@admin.register(SoumissionFormulaire)
class SoumissionFormulaireAdmin(admin.ModelAdmin):
    list_display = ['formulaire', 'soumetteur', 'statut', 'soumis_hors_ligne', 'created_at']
    list_filter = ['statut', 'soumis_hors_ligne']
    readonly_fields = ['created_at', 'date_validation']


# ─── M19 : Enquêtes ───────────────────────────────────────────────────────────

class SectionEnqueteInline(admin.TabularInline):
    model = SectionEnquete
    extra = 0
    fields = ['ordre', 'titre']


@admin.register(Enquete)
class EnqueteAdmin(admin.ModelAdmin):
    list_display = ['code', 'titre', 'type_enquete', 'statut', 'projet',
                    'date_debut', 'date_fin', 'responsable']
    list_filter = ['type_enquete', 'statut', 'projet']
    search_fields = ['code', 'titre']
    readonly_fields = ['code', 'created_at', 'updated_at']
    inlines = [SectionEnqueteInline]


@admin.register(SectionEnquete)
class SectionEnqueteAdmin(admin.ModelAdmin):
    list_display = ['enquete', 'ordre', 'titre']


@admin.register(QuestionEnquete)
class QuestionEnqueteAdmin(admin.ModelAdmin):
    list_display = ['enquete', 'section', 'type_question', 'libelle', 'obligatoire', 'ordre']
    list_filter = ['type_question', 'obligatoire']
    search_fields = ['libelle']


@admin.register(ReponseEnquete)
class ReponseEnqueteAdmin(admin.ModelAdmin):
    list_display = ['enquete', 'repondant', 'statut', 'canal', 'soumis_hors_ligne', 'created_at']
    list_filter = ['statut', 'canal', 'soumis_hors_ligne']
    readonly_fields = ['created_at', 'soumis_le']


# ─── M20 : Cadre de résultats & Évaluations ──────────────────────────────────

class NiveauResultatInline(admin.TabularInline):
    model = NiveauResultat
    extra = 0
    fields = ['niveau', 'code', 'intitule', 'ordre', 'taux_avancement']
    fk_name = 'cadre'


@admin.register(CadreResultats)
class CadreResultatsAdmin(admin.ModelAdmin):
    list_display = ['titre', 'projet', 'programme', 'version', 'date_validation']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [NiveauResultatInline]


@admin.register(NiveauResultat)
class NiveauResultatAdmin(admin.ModelAdmin):
    list_display = ['cadre', 'niveau', 'code', 'intitule', 'ordre', 'taux_avancement']
    list_filter = ['niveau']
    search_fields = ['intitule', 'code']


@admin.register(TheorieChangement)
class TheorieChangementAdmin(admin.ModelAdmin):
    list_display = ['titre', 'projet', 'programme', 'version', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


class CritereEvaluationInline(admin.TabularInline):
    model = CritereEvaluation
    extra = 0
    fields = ['critere', 'note', 'observation']


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['reference', 'titre', 'type_evaluation', 'statut', 'projet',
                    'date_debut', 'date_fin', 'note_globale', 'responsable']
    list_filter = ['type_evaluation', 'statut', 'projet']
    search_fields = ['reference', 'titre']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [CritereEvaluationInline]


@admin.register(CritereEvaluation)
class CritereEvaluationAdmin(admin.ModelAdmin):
    list_display = ['evaluation', 'critere', 'note']
    list_filter = ['critere']


@admin.register(LeconApprise)
class LeconApprisAdmin(admin.ModelAdmin):
    list_display = ['type_lecon', 'titre', 'projet', 'statut', 'auteur', 'created_at']
    list_filter = ['type_lecon', 'statut', 'projet']
    search_fields = ['titre', 'description']
    readonly_fields = ['created_at', 'updated_at']


# ─── Rapports & IA ────────────────────────────────────────────────────────────

@admin.register(RapportSE)
class RapportSEAdmin(admin.ModelAdmin):
    list_display = ['reference', 'titre', 'type_rapport', 'periode', 'date_rapport',
                    'statut', 'redacteur', 'genere_par_ia']
    list_filter = ['type_rapport', 'statut', 'periode', 'genere_par_ia']
    search_fields = ['reference', 'titre']
    readonly_fields = ['reference', 'created_at', 'updated_at']


@admin.register(AnalysePredictive)
class AnalysePredictiveAdmin(admin.ModelAdmin):
    list_display = ['type_analyse', 'indicateur', 'projet', 'statut',
                    'confiance_score', 'demande_par', 'created_at']
    list_filter = ['type_analyse', 'statut']
    readonly_fields = ['created_at', 'completed_at']


# ─── SIG ──────────────────────────────────────────────────────────────────────

@admin.register(PointSIG)
class PointSIGAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_point', 'latitude', 'longitude', 'projet', 'actif', 'created_at']
    list_filter = ['type_point', 'actif', 'projet']
    search_fields = ['titre', 'description']
    readonly_fields = ['created_at']


# ─── M29 : Risques ───────────────────────────────────────────────────────────

class PlanMitigationInline(admin.TabularInline):
    model = PlanMitigation
    extra = 0
    fields = ['type_mitigation', 'description', 'responsable', 'date_fin', 'statut']


class SuiviRisqueInline(admin.TabularInline):
    model = SuiviRisque
    extra = 0
    fields = ['date_suivi', 'probabilite', 'impact', 'statut', 'tendance', 'suivi_par']
    readonly_fields = ['date_suivi']


@admin.register(RegistreRisque)
class RegistreRisqueAdmin(admin.ModelAdmin):
    list_display = ['reference', 'intitule', 'categorie', 'probabilite', 'impact',
                    'score_risque', 'niveau_risque', 'tendance', 'statut',
                    'responsable', 'date_identification']
    list_filter = ['categorie', 'statut', 'niveau_risque', 'tendance', 'projet', 'programme']
    search_fields = ['reference', 'intitule', 'description']
    readonly_fields = ['reference', 'score_risque', 'niveau_risque', 'date_identification',
                       'created_at', 'updated_at']
    inlines = [PlanMitigationInline, SuiviRisqueInline]


@admin.register(PlanMitigation)
class PlanMitigationAdmin(admin.ModelAdmin):
    list_display = ['risque', 'type_mitigation', 'responsable', 'date_fin', 'statut']
    list_filter = ['type_mitigation', 'statut']
    readonly_fields = ['created_at']


@admin.register(AlerteRisque)
class AlerteRisqueAdmin(admin.ModelAdmin):
    list_display = ['risque', 'niveau', 'message', 'destinataire', 'lue', 'date_alerte']
    list_filter = ['niveau', 'lue']
    readonly_fields = ['date_alerte']
