from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    CadreLogique, ElementCadreLogique,
    AnalyseSWOT, ElementSWOT, StrategieSWOT,
    TDR, PlanAction, ActionPlanItem,
    ProgrammeActivites, ActivitePA,
    PlanTravail, Activite, Jalon,
)


# ─── Cadre Logique ────────────────────────────────────────────────────────────

class ElementCadreLogiqueSerializer(serializers.ModelSerializer):
    sous_elements = serializers.SerializerMethodField()
    niveau_label = serializers.CharField(source='get_niveau_display', read_only=True)

    class Meta:
        model = ElementCadreLogique
        fields = ['id', 'cadre', 'parent', 'niveau', 'niveau_label', 'code', 'description',
                  'indicateurs_objectifs', 'sources_verification', 'hypotheses',
                  'ordre', 'actif', 'sous_elements']

    def get_sous_elements(self, obj):
        children = obj.sous_elements.filter(actif=True).order_by('ordre')
        return ElementCadreLogiqueSerializer(children, many=True).data


class CadreLogiqueSerializer(serializers.ModelSerializer):
    elements_racines = serializers.SerializerMethodField()
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)

    class Meta:
        model = CadreLogique
        fields = ['id', 'projet', 'programme', 'titre', 'version', 'description', 'statut',
                  'valide_par', 'valide_par_detail', 'date_validation',
                  'created_by', 'created_by_detail', 'created_at', 'updated_at',
                  'elements_racines']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_elements_racines(self, obj):
        roots = obj.elements.filter(parent__isnull=True, actif=True).order_by('ordre')
        return ElementCadreLogiqueSerializer(roots, many=True).data


# ─── SWOT ─────────────────────────────────────────────────────────────────────

class ElementSWOTSerializer(serializers.ModelSerializer):
    categorie_label = serializers.CharField(source='get_categorie_display', read_only=True)

    class Meta:
        model = ElementSWOT
        fields = ['id', 'analyse', 'categorie', 'categorie_label', 'description',
                  'ponderation', 'classement', 'notes']


class StrategieSWOTSerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source='get_type_strategie_display', read_only=True)

    class Meta:
        model = StrategieSWOT
        fields = ['id', 'analyse', 'type_strategie', 'type_label', 'titre', 'description',
                  'priorite', 'elements_lies', 'notes', 'generee_par_ia']


class AnalyseSWOTSerializer(serializers.ModelSerializer):
    elements = ElementSWOTSerializer(many=True, read_only=True)
    strategies = StrategieSWOTSerializer(many=True, read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    matrice = serializers.SerializerMethodField()

    class Meta:
        model = AnalyseSWOT
        fields = ['id', 'projet', 'programme', 'titre', 'description', 'contexte',
                  'date_analyse', 'statut', 'created_by', 'created_by_detail',
                  'created_at', 'updated_at', 'elements', 'strategies', 'matrice']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_matrice(self, obj):
        elements = obj.elements.all()
        return {
            'forces': ElementSWOTSerializer(
                elements.filter(categorie='force').order_by('-ponderation'), many=True
            ).data,
            'faiblesses': ElementSWOTSerializer(
                elements.filter(categorie='faiblesse').order_by('-ponderation'), many=True
            ).data,
            'opportunites': ElementSWOTSerializer(
                elements.filter(categorie='opportunite').order_by('-ponderation'), many=True
            ).data,
            'menaces': ElementSWOTSerializer(
                elements.filter(categorie='menace').order_by('-ponderation'), many=True
            ).data,
        }


# ─── TDR ─────────────────────────────────────────────────────────────────────

class TDRListSerializer(serializers.ModelSerializer):
    redige_par_nom = serializers.CharField(source='redige_par.nom_complet', read_only=True)

    class Meta:
        model = TDR
        fields = ['id', 'reference', 'titre', 'type_tdr', 'statut', 'projet', 'programme',
                  'redige_par', 'redige_par_nom', 'date_redaction',
                  'budget_previsionnel', 'genere_par_ia', 'created_at']


class TDRDetailSerializer(serializers.ModelSerializer):
    redige_par_detail = UserMinimalSerializer(source='redige_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    publie_par_detail = UserMinimalSerializer(source='publie_par', read_only=True)

    class Meta:
        model = TDR
        fields = [
            'id', 'reference', 'titre', 'type_tdr', 'statut',
            'projet', 'programme',
            'contexte', 'justification', 'objectifs', 'resultats_attendus',
            'methodologie', 'livrables', 'calendrier', 'budget_previsionnel',
            'profil_consultant', 'criteres_selection', 'modalites_paiement',
            'redige_par', 'redige_par_detail', 'date_redaction',
            'valide_par', 'valide_par_detail', 'date_validation',
            'publie_par', 'publie_par_detail', 'date_publication',
            'genere_par_ia', 'prompt_ia', 'fichier_final',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']


# ─── Plan d'Action ────────────────────────────────────────────────────────────

class ActionPlanItemSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    est_en_retard = serializers.ReadOnlyField()
    sous_actions = serializers.SerializerMethodField()

    class Meta:
        model = ActionPlanItem
        fields = ['id', 'plan', 'parent', 'code', 'libelle', 'description',
                  'responsable', 'responsable_detail',
                  'date_debut', 'date_fin', 'date_fin_reelle',
                  'budget_prevu', 'budget_realise',
                  'indicateur_realisation', 'livrable_attendu',
                  'statut', 'taux_avancement', 'commentaires', 'ordre',
                  'est_en_retard', 'sous_actions',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sous_actions(self, obj):
        return ActionPlanItemSerializer(
            obj.sous_actions.all().order_by('ordre'), many=True
        ).data


class PlanActionSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    taux_realisation = serializers.ReadOnlyField()

    class Meta:
        model = PlanAction
        fields = ['id', 'projet', 'programme', 'titre', 'periode', 'annee', 'trimestre', 'mois',
                  'statut', 'budget_total', 'valide_par', 'valide_par_detail', 'date_validation',
                  'notes', 'created_by', 'created_at', 'updated_at',
                  'items', 'taux_realisation']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_items(self, obj):
        roots = obj.items.filter(parent__isnull=True).order_by('ordre')
        return ActionPlanItemSerializer(roots, many=True).data


# ─── Programme d'Activités ────────────────────────────────────────────────────

class ActivitePASerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    est_en_retard = serializers.ReadOnlyField()
    sous_activites = serializers.SerializerMethodField()

    class Meta:
        model = ActivitePA
        fields = ['id', 'programme_activites', 'element_cadre', 'parent',
                  'code', 'libelle', 'description',
                  'responsable', 'responsable_detail',
                  'date_debut_prevue', 'date_fin_prevue',
                  'date_debut_reelle', 'date_fin_reelle',
                  'budget_prevu', 'budget_realise',
                  'indicateur', 'cible', 'unite_mesure', 'valeur_realisee',
                  'statut', 'taux_avancement', 'ordre', 'notes',
                  'est_en_retard', 'sous_activites',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sous_activites(self, obj):
        return ActivitePASerializer(
            obj.sous_activites.all().order_by('ordre'), many=True
        ).data


class ProgrammeActivitesSerializer(serializers.ModelSerializer):
    activites_racines = serializers.SerializerMethodField()
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    taux_realisation = serializers.ReadOnlyField()

    class Meta:
        model = ProgrammeActivites
        fields = ['id', 'projet', 'programme', 'reference', 'titre',
                  'periode', 'annee', 'semestre', 'trimestre', 'mois',
                  'budget_total', 'statut',
                  'valide_par', 'valide_par_detail', 'date_validation',
                  'notes', 'created_by', 'created_at', 'updated_at',
                  'activites_racines', 'taux_realisation']
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_activites_racines(self, obj):
        roots = obj.activites.filter(parent__isnull=True).order_by('ordre')
        return ActivitePASerializer(roots, many=True).data


class ProgrammeActivitesListSerializer(serializers.ModelSerializer):
    taux_realisation = serializers.ReadOnlyField()

    class Meta:
        model = ProgrammeActivites
        fields = ['id', 'projet', 'programme', 'reference', 'titre',
                  'periode', 'annee', 'statut', 'budget_total', 'taux_realisation', 'created_at']


# ─── Plan de Travail ──────────────────────────────────────────────────────────

class ActiviteSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    sous_activites = serializers.SerializerMethodField()

    class Meta:
        model = Activite
        fields = ['id', 'plan', 'parent', 'code', 'libelle', 'description', 'statut',
                  'date_debut_prevue', 'date_fin_prevue', 'date_debut_reelle', 'date_fin_reelle',
                  'responsable', 'responsable_detail', 'budget_prevu', 'taux_avancement',
                  'ordre', 'sous_activites', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_sous_activites(self, obj):
        return ActiviteSerializer(
            obj.sous_activites.all().order_by('ordre'), many=True
        ).data


class PlanTravailSerializer(serializers.ModelSerializer):
    activites = serializers.SerializerMethodField()
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = PlanTravail
        fields = ['id', 'projet', 'nom', 'annee', 'trimestre', 'statut',
                  'valide_par', 'valide_par_detail', 'date_validation',
                  'notes', 'created_at', 'activites']
        read_only_fields = ['id', 'created_at']

    def get_activites(self, obj):
        roots = obj.activites.filter(parent__isnull=True).order_by('ordre')
        return ActiviteSerializer(roots, many=True).data


class JalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jalon
        fields = ['id', 'projet', 'libelle', 'description',
                  'date_prevue', 'date_reelle', 'statut', 'notes']
