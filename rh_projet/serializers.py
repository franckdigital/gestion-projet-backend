from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    EmployeProjet, AffectationRH, FeuilleTemps,
    LigneFeuilleTemps, EvaluationPerformance, BesoinFormation,
)


# ─── EmployeProjet ────────────────────────────────────────────────────────────

class EmployeProjetMinimalSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model = EmployeProjet
        fields = ['id', 'matricule', 'nom', 'prenom', 'nom_complet',
                  'type_personnel', 'statut', 'poste', 'specialite']


class EmployeProjetListSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model = EmployeProjet
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'nom_complet',
            'type_personnel', 'statut', 'email', 'telephone',
            'poste', 'specialite', 'niveau_expertise',
            'date_embauche', 'date_fin_contrat',
            'taux_journalier', 'devise', 'taux_occupation_max',
            'photo', 'created_at',
        ]


class EmployeProjetDetailSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)
    nb_affectations_actives = serializers.SerializerMethodField()

    class Meta:
        model = EmployeProjet
        fields = [
            'id', 'utilisateur', 'utilisateur_detail',
            'matricule', 'nom', 'prenom', 'nom_complet',
            'type_personnel', 'statut', 'email', 'telephone',
            'poste', 'specialite', 'niveau_expertise',
            'date_embauche', 'date_fin_contrat',
            'taux_journalier', 'devise', 'taux_occupation_max',
            'competences', 'cv', 'photo', 'notes',
            'nb_affectations_actives', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'matricule', 'created_at', 'updated_at']

    def get_nb_affectations_actives(self, obj):
        return obj.affectations.filter(statut='active').count()


# ─── AffectationRH ────────────────────────────────────────────────────────────

class AffectationRHListSerializer(serializers.ModelSerializer):
    employe_detail = EmployeProjetMinimalSerializer(source='employe', read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = AffectationRH
        fields = [
            'id', 'employe', 'employe_detail',
            'programme', 'projet', 'activite',
            'role', 'taux_affectation', 'date_debut', 'date_fin',
            'statut', 'cree_par', 'cree_par_detail', 'created_at',
        ]


class AffectationRHDetailSerializer(serializers.ModelSerializer):
    employe_detail = EmployeProjetMinimalSerializer(source='employe', read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = AffectationRH
        fields = [
            'id', 'employe', 'employe_detail',
            'programme', 'projet', 'activite',
            'role', 'taux_affectation', 'date_debut', 'date_fin',
            'statut', 'description',
            'cree_par', 'cree_par_detail', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ─── LigneFeuilleTemps ────────────────────────────────────────────────────────

class LigneFeuilleTempsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneFeuilleTemps
        fields = [
            'id', 'feuille', 'date', 'projet', 'activite',
            'heures', 'description', 'est_jour_ferie', 'est_conge',
        ]
        read_only_fields = ['id']


# ─── FeuilleTemps ─────────────────────────────────────────────────────────────

class FeuilleTempsListSerializer(serializers.ModelSerializer):
    employe_detail = EmployeProjetMinimalSerializer(source='employe', read_only=True)
    valideur_detail = UserMinimalSerializer(source='valideur', read_only=True)

    class Meta:
        model = FeuilleTemps
        fields = [
            'id', 'employe', 'employe_detail',
            'mois', 'annee', 'statut',
            'total_heures', 'total_jours', 'montant_total',
            'valideur', 'valideur_detail', 'date_validation',
            'created_at',
        ]


class FeuilleTempsDetailSerializer(serializers.ModelSerializer):
    employe_detail = EmployeProjetMinimalSerializer(source='employe', read_only=True)
    valideur_detail = UserMinimalSerializer(source='valideur', read_only=True)
    lignes = LigneFeuilleTempsSerializer(many=True, read_only=True)

    class Meta:
        model = FeuilleTemps
        fields = [
            'id', 'employe', 'employe_detail',
            'mois', 'annee', 'statut',
            'total_heures', 'total_jours', 'montant_total',
            'valideur', 'valideur_detail', 'date_validation',
            'motif_rejet', 'commentaire',
            'lignes', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'total_heures', 'total_jours', 'montant_total',
            'date_validation', 'created_at', 'updated_at',
        ]


# ─── EvaluationPerformance ────────────────────────────────────────────────────

class EvaluationPerformanceListSerializer(serializers.ModelSerializer):
    employe_detail = EmployeProjetMinimalSerializer(source='employe', read_only=True)
    evaluateur_detail = UserMinimalSerializer(source='evaluateur', read_only=True)

    class Meta:
        model = EvaluationPerformance
        fields = [
            'id', 'employe', 'employe_detail',
            'evaluateur', 'evaluateur_detail',
            'projet', 'periode', 'annee', 'trimestre',
            'statut', 'note_globale', 'date_evaluation', 'created_at',
        ]


class EvaluationPerformanceDetailSerializer(serializers.ModelSerializer):
    employe_detail = EmployeProjetMinimalSerializer(source='employe', read_only=True)
    evaluateur_detail = UserMinimalSerializer(source='evaluateur', read_only=True)

    class Meta:
        model = EvaluationPerformance
        fields = [
            'id', 'employe', 'employe_detail',
            'evaluateur', 'evaluateur_detail',
            'projet', 'periode', 'annee', 'trimestre',
            'statut', 'note_globale', 'criteres',
            'points_forts', 'axes_amelioration', 'objectifs_periode_suivante',
            'commentaire_employe', 'date_evaluation', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ─── BesoinFormation ─────────────────────────────────────────────────────────

class BesoinFormationListSerializer(serializers.ModelSerializer):
    employe_detail = EmployeProjetMinimalSerializer(source='employe', read_only=True)
    identifie_par_detail = UserMinimalSerializer(source='identifie_par', read_only=True)

    class Meta:
        model = BesoinFormation
        fields = [
            'id', 'employe', 'employe_detail',
            'projet', 'intitule', 'domaine',
            'priorite', 'statut', 'date_souhaitee',
            'cout_estime', 'duree_jours',
            'identifie_par', 'identifie_par_detail', 'created_at',
        ]


class BesoinFormationDetailSerializer(serializers.ModelSerializer):
    employe_detail = EmployeProjetMinimalSerializer(source='employe', read_only=True)
    identifie_par_detail = UserMinimalSerializer(source='identifie_par', read_only=True)

    class Meta:
        model = BesoinFormation
        fields = [
            'id', 'employe', 'employe_detail',
            'projet', 'intitule', 'description', 'domaine',
            'priorite', 'statut',
            'date_souhaitee', 'date_realisation',
            'cout_estime', 'cout_reel', 'duree_jours',
            'organisme_formation', 'lieu', 'attestation',
            'identifie_par', 'identifie_par_detail', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
