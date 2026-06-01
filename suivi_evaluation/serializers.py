from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
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

class ValeurCiblePeriodeSerializer(serializers.ModelSerializer):
    taux_realisation = serializers.ReadOnlyField()

    class Meta:
        model = ValeurCiblePeriode
        fields = ['id', 'indicateur', 'annee', 'trimestre',
                  'valeur_cible', 'valeur_realisee', 'taux_realisation', 'notes']


class CollecteIndicateurSerializer(serializers.ModelSerializer):
    collecteur_detail = UserMinimalSerializer(source='collecteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = CollecteIndicateur
        fields = ['id', 'indicateur', 'periode', 'date_collecte', 'valeur_reelle',
                  'valeur_disaggregee', 'collecteur', 'collecteur_detail',
                  'commentaire', 'source_donnee', 'fichier_justificatif',
                  'latitude', 'longitude', 'altitude',
                  'statut', 'valide_par', 'valide_par_detail', 'date_validation',
                  'motif_rejet', 'created_at']
        read_only_fields = ['id', 'created_at', 'date_validation']


class AlerteIndicateurSerializer(serializers.ModelSerializer):
    destinataire_detail = UserMinimalSerializer(source='destinataire', read_only=True)

    class Meta:
        model = AlerteIndicateur
        fields = ['id', 'indicateur', 'type_alerte', 'niveau', 'message',
                  'destinataire', 'destinataire_detail', 'lue', 'date_alerte', 'date_lecture']
        read_only_fields = ['id', 'date_alerte']


class IndicateurListSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source='responsable.nom_complet', read_only=True)
    taux_realisation = serializers.ReadOnlyField()
    derniere_collecte = serializers.SerializerMethodField()

    class Meta:
        model = Indicateur
        fields = ['id', 'code', 'intitule', 'type_indicateur', 'unite_mesure', 'unite_personnalisee',
                  'statut', 'actif',
                  'projet', 'programme',
                  'valeur_baseline', 'valeur_cible_globale', 'valeur_realisee',
                  'taux_realisation', 'frequence_collecte', 'responsable', 'responsable_nom',
                  'derniere_collecte', 'actif', 'ordre', 'created_at']

    def get_derniere_collecte(self, obj):
        c = obj.derniere_collecte
        if c:
            return {'date': c.date_collecte, 'valeur': float(c.valeur_reelle)}
        return None


class IndicateurDetailSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    responsable_collecte_detail = UserMinimalSerializer(source='responsable_collecte', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    cibles_periodes = ValeurCiblePeriodeSerializer(many=True, read_only=True)
    alertes = AlerteIndicateurSerializer(many=True, read_only=True)
    taux_realisation = serializers.ReadOnlyField()
    derniere_collecte = serializers.SerializerMethodField()
    historique_collectes = serializers.SerializerMethodField()

    class Meta:
        model = Indicateur
        fields = [
            'id', 'code', 'intitule', 'description', 'type_indicateur',
            'unite_mesure', 'unite_personnalisee',
            'projet', 'programme', 'niveau_resultat',
            'valeur_baseline', 'date_baseline', 'valeur_cible_globale', 'valeur_realisee',
            'frequence_collecte', 'mode_calcul', 'formule',
            'source_verification', 'methode_collecte',
            'responsable', 'responsable_detail',
            'responsable_collecte', 'responsable_collecte_detail',
            'hypotheses', 'risques',
            'statut', 'actif', 'est_disaggregue', 'dimensions_disaggregation',
            'ordre', 'tags', 'notes',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'taux_realisation', 'derniere_collecte', 'historique_collectes',
            'cibles_periodes', 'alertes',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_derniere_collecte(self, obj):
        c = obj.derniere_collecte
        if c:
            return {'date': c.date_collecte, 'valeur': float(c.valeur_reelle), 'id': c.id}
        return None

    def get_historique_collectes(self, obj):
        qs = obj.collectes.filter(statut='valide').order_by('date_collecte')[:12]
        return [{'date': str(c.date_collecte), 'valeur': float(c.valeur_reelle)} for c in qs]


# ─── M18 : Formulaires dynamiques ────────────────────────────────────────────

class ChampFormulaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChampFormulaire
        fields = ['id', 'formulaire', 'type_champ', 'libelle', 'description',
                  'obligatoire', 'ordre', 'options', 'formule_calcul',
                  'condition_affichage', 'valeur_defaut',
                  'validation_min', 'validation_max', 'indicateur_lie']


class ReponseChampSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReponseChamp
        fields = ['id', 'soumission', 'champ', 'valeur_texte', 'valeur_nombre',
                  'valeur_date', 'valeur_json', 'fichier', 'latitude', 'longitude']


class SoumissionFormulaireSerializer(serializers.ModelSerializer):
    soumetteur_detail = UserMinimalSerializer(source='soumetteur', read_only=True)
    reponses = ReponseChampSerializer(many=True, read_only=True)

    class Meta:
        model = SoumissionFormulaire
        fields = ['id', 'formulaire', 'soumetteur', 'soumetteur_detail',
                  'statut', 'valide_par', 'date_validation', 'motif_rejet',
                  'latitude', 'longitude', 'altitude', 'precision_gps',
                  'appareil', 'soumis_hors_ligne', 'date_soumission_locale',
                  'created_at', 'reponses']
        read_only_fields = ['id', 'created_at', 'date_validation']


class FormulaireDynamiqueListSerializer(serializers.ModelSerializer):
    nb_soumissions = serializers.SerializerMethodField()
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)

    class Meta:
        model = FormulaireDynamique
        fields = ['id', 'code', 'titre', 'statut', 'projet', 'programme',
                  'date_ouverture', 'date_fermeture', 'allow_offline',
                  'require_gps', 'require_photo', 'nb_soumissions',
                  'created_by', 'created_by_detail', 'created_at']

    def get_nb_soumissions(self, obj):
        return obj.soumissions.filter(statut__in=['soumis', 'valide']).count()


class FormulaireDynamiqueDetailSerializer(serializers.ModelSerializer):
    champs = ChampFormulaireSerializer(many=True, read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    nb_soumissions = serializers.SerializerMethodField()

    class Meta:
        model = FormulaireDynamique
        fields = [
            'id', 'code', 'titre', 'description', 'statut',
            'projet', 'programme', 'indicateur',
            'date_ouverture', 'date_fermeture',
            'allow_offline', 'require_gps', 'require_photo', 'require_signature',
            'max_soumissions',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'champs', 'nb_soumissions',
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']

    def get_nb_soumissions(self, obj):
        return obj.soumissions.count()


# ─── M19 : Enquêtes ───────────────────────────────────────────────────────────

class QuestionEnqueteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionEnquete
        fields = ['id', 'section', 'enquete', 'type_question', 'libelle', 'description',
                  'obligatoire', 'ordre', 'options', 'config_likert',
                  'indicateur_lie', 'condition_affichage', 'allow_other']


class SectionEnqueteSerializer(serializers.ModelSerializer):
    questions = QuestionEnqueteSerializer(many=True, read_only=True)

    class Meta:
        model = SectionEnquete
        fields = ['id', 'enquete', 'titre', 'description', 'ordre',
                  'condition_affichage', 'questions']


class ReponseQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReponseQuestion
        fields = ['id', 'reponse_enquete', 'question', 'valeur_texte', 'valeur_nombre',
                  'valeur_choix', 'valeur_date', 'valeur_fichier', 'latitude', 'longitude']


class ReponseEnqueteSerializer(serializers.ModelSerializer):
    repondant_detail = UserMinimalSerializer(source='repondant', read_only=True)
    reponses_questions = ReponseQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = ReponseEnquete
        fields = ['id', 'enquete', 'repondant', 'repondant_detail',
                  'identifiant_anonyme', 'statut', 'langue',
                  'duree_completion', 'latitude', 'longitude',
                  'canal', 'appareil', 'soumis_hors_ligne',
                  'created_at', 'soumis_le', 'reponses_questions']
        read_only_fields = ['id', 'created_at']


class EnqueteListSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    nb_reponses = serializers.ReadOnlyField()
    taux_completion = serializers.ReadOnlyField()

    class Meta:
        model = Enquete
        fields = ['id', 'code', 'titre', 'type_enquete', 'statut',
                  'projet', 'programme', 'responsable', 'responsable_detail',
                  'date_debut', 'date_fin', 'canaux',
                  'taille_echantillon', 'nb_reponses', 'taux_completion',
                  'created_at']


class EnqueteDetailSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    sections = SectionEnqueteSerializer(many=True, read_only=True)
    nb_reponses = serializers.ReadOnlyField()
    taux_completion = serializers.ReadOnlyField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Enquete
        fields = [
            'id', 'code', 'titre', 'description', 'type_enquete', 'statut', 'canaux',
            'projet', 'programme',
            'date_debut', 'date_fin', 'population_cible',
            'taille_echantillon', 'objectifs', 'methodologie',
            'responsable', 'responsable_detail',
            'allow_anonymous', 'nb_reponses_attendues',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'sections', 'nb_reponses', 'taux_completion', 'stats',
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']

    def get_stats(self, obj):
        reponses = obj.reponses.all()
        return {
            'total': reponses.count(),
            'soumises': reponses.filter(statut__in=['soumis', 'complete']).count(),
            'en_cours': reponses.filter(statut='en_cours').count(),
        }


# ─── M20 : Cadre de résultats ─────────────────────────────────────────────────

class NiveauResultatSerializer(serializers.ModelSerializer):
    enfants = serializers.SerializerMethodField()
    indicateurs_count = serializers.SerializerMethodField()

    class Meta:
        model = NiveauResultat
        fields = ['id', 'cadre', 'parent', 'niveau', 'code', 'intitule',
                  'description', 'ordre', 'taux_avancement', 'notes',
                  'enfants', 'indicateurs_count']

    def get_enfants(self, obj):
        return NiveauResultatSerializer(
            obj.enfants.all().order_by('ordre'), many=True
        ).data

    def get_indicateurs_count(self, obj):
        return obj.indicateurs.count()


class CadreResultatsSerializer(serializers.ModelSerializer):
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    niveaux = serializers.SerializerMethodField()

    class Meta:
        model = CadreResultats
        fields = ['id', 'projet', 'programme', 'titre', 'description',
                  'version', 'date_validation', 'valide_par', 'valide_par_detail',
                  'created_by', 'created_by_detail', 'created_at', 'updated_at',
                  'niveaux']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_niveaux(self, obj):
        racines = obj.niveaux.filter(parent__isnull=True).order_by('niveau', 'ordre')
        return NiveauResultatSerializer(racines, many=True).data


class TheorieChangementSerializer(serializers.ModelSerializer):
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)

    class Meta:
        model = TheorieChangement
        fields = ['id', 'projet', 'programme', 'titre',
                  'contexte', 'probleme_central', 'vision_changement',
                  'hypotheses_changement', 'facteurs_risque', 'diagramme_json',
                  'version', 'created_by', 'created_by_detail', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CritereEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CritereEvaluation
        fields = ['id', 'evaluation', 'critere', 'note', 'observation',
                  'points_forts', 'points_faibles', 'recommandations']


class EvaluationListSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)

    class Meta:
        model = Evaluation
        fields = ['id', 'reference', 'titre', 'type_evaluation', 'statut',
                  'projet', 'programme', 'responsable', 'responsable_detail',
                  'date_debut', 'date_fin', 'note_globale', 'created_at']


class EvaluationDetailSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    criteres = CritereEvaluationSerializer(many=True, read_only=True)
    lecons = serializers.SerializerMethodField()

    class Meta:
        model = Evaluation
        fields = [
            'id', 'reference', 'titre', 'type_evaluation', 'statut', 'description',
            'projet', 'programme',
            'date_debut', 'date_fin', 'date_rapport',
            'responsable', 'responsable_detail',
            'evaluateurs_externes', 'budget',
            'note_globale', 'conclusions', 'recommandations', 'rapport_final',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'criteres', 'lecons',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_lecons(self, obj):
        return [{'id': l.id, 'type': l.type_lecon, 'titre': l.titre} for l in obj.lecons.all()]


class LeconApprisSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = LeconApprise
        fields = ['id', 'projet', 'programme', 'evaluation',
                  'type_lecon', 'titre', 'contexte', 'description',
                  'recommandation', 'domaine', 'tags', 'statut',
                  'auteur', 'auteur_detail', 'valide_par', 'valide_par_detail',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─── Rapports S&E ─────────────────────────────────────────────────────────────

class RapportSESerializer(serializers.ModelSerializer):
    redacteur_detail = UserMinimalSerializer(source='redacteur', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = RapportSE
        fields = ['id', 'reference', 'titre', 'type_rapport', 'periode',
                  'date_debut_periode', 'date_fin_periode', 'date_rapport',
                  'projet', 'programme',
                  'contenu', 'synthese', 'principales_realisations',
                  'defis', 'recommandations', 'perspectives',
                  'indicateurs_inclus', 'donnees_json',
                  'redacteur', 'redacteur_detail', 'statut',
                  'valide_par', 'valide_par_detail', 'date_validation',
                  'fichier', 'genere_par_ia', 'created_at', 'updated_at']
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']


# ─── Analyse prédictive ───────────────────────────────────────────────────────

class AnalysePredictiveSerializer(serializers.ModelSerializer):
    demande_par_detail    = UserMinimalSerializer(source='demande_par', read_only=True)
    indicateur_code       = serializers.CharField(source='indicateur.code',     read_only=True, default=None)
    indicateur_intitule   = serializers.CharField(source='indicateur.intitule', read_only=True, default=None)
    projet_code           = serializers.CharField(source='projet.code',          read_only=True, default=None)

    class Meta:
        model = AnalysePredictive
        fields = [
            'id', 'indicateur', 'indicateur_code', 'indicateur_intitule',
            'projet', 'projet_code', 'type_analyse', 'statut',
            'parametres', 'resultats', 'previsions',
            'risques_detectes', 'suggestions', 'confiance_score',
            'demande_par', 'demande_par_detail', 'created_at', 'completed_at',
        ]
        read_only_fields = ['id', 'created_at', 'completed_at', 'statut',
                            'resultats', 'previsions', 'risques_detectes',
                            'indicateur_code', 'indicateur_intitule', 'projet_code']


# ─── SIG ──────────────────────────────────────────────────────────────────────

class PointSIGSerializer(serializers.ModelSerializer):
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)

    class Meta:
        model = PointSIG
        fields = ['id', 'type_point', 'titre', 'description',
                  'latitude', 'longitude', 'altitude', 'rayon',
                  'projet', 'programme', 'indicateur', 'valeur',
                  'couleur', 'icone', 'donnees_extra', 'actif',
                  'created_by', 'created_by_detail', 'created_at']
        read_only_fields = ['id', 'created_at']


# ─── M29 : Gestion des Risques ───────────────────────────────────────────────

class PlanMitigationSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    score_residuel = serializers.ReadOnlyField()

    class Meta:
        model = PlanMitigation
        fields = ['id', 'risque', 'type_mitigation', 'description', 'objectif',
                  'statut', 'responsable', 'responsable_detail',
                  'date_debut', 'date_fin', 'cout_estime',
                  'probabilite_residuelle', 'impact_residuel', 'score_residuel',
                  'resultat', 'created_at']
        read_only_fields = ['id', 'created_at']


class SuiviRisqueSerializer(serializers.ModelSerializer):
    suivi_par_detail = UserMinimalSerializer(source='suivi_par', read_only=True)

    class Meta:
        model = SuiviRisque
        fields = ['id', 'risque', 'date_suivi', 'probabilite', 'impact',
                  'statut', 'tendance', 'observations', 'actions_prises',
                  'suivi_par', 'suivi_par_detail', 'created_at']
        read_only_fields = ['id', 'created_at']


class AlerteRisqueSerializer(serializers.ModelSerializer):
    destinataire_detail = UserMinimalSerializer(source='destinataire', read_only=True)

    class Meta:
        model = AlerteRisque
        fields = ['id', 'risque', 'niveau', 'message', 'destinataire',
                  'destinataire_detail', 'lue', 'date_alerte', 'date_lecture']
        read_only_fields = ['id', 'date_alerte']


class RegistreRisqueListSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    nb_plans = serializers.SerializerMethodField()

    class Meta:
        model = RegistreRisque
        fields = ['id', 'reference', 'intitule', 'categorie',
                  'probabilite', 'impact', 'score_risque', 'niveau_risque',
                  'tendance', 'statut', 'est_critique',
                  'projet', 'programme', 'responsable', 'responsable_detail',
                  'date_identification', 'date_revue', 'nb_plans', 'created_at']

    def get_nb_plans(self, obj):
        return obj.plans_mitigation.count()


class RegistreRisqueDetailSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    plans_mitigation = PlanMitigationSerializer(many=True, read_only=True)
    suivis = SuiviRisqueSerializer(many=True, read_only=True)
    alertes_risque = AlerteRisqueSerializer(many=True, read_only=True)
    est_critique = serializers.ReadOnlyField()

    class Meta:
        model = RegistreRisque
        fields = [
            'id', 'reference', 'intitule', 'description', 'categorie',
            'programme', 'projet', 'activite',
            'probabilite', 'impact', 'score_risque', 'niveau_risque',
            'tendance', 'statut', 'est_critique',
            'responsable', 'responsable_detail',
            'date_identification', 'date_revue', 'date_resolution',
            'causes', 'consequences', 'indicateurs_declenchement',
            'hypotheses', 'notes', 'tags',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'plans_mitigation', 'suivis', 'alertes_risque',
        ]
        read_only_fields = ['id', 'reference', 'score_risque', 'niveau_risque',
                            'created_at', 'updated_at']
