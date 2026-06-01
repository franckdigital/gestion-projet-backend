from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    PlanPassationMarche, DemandeAchat, AppelOffre,
    SoumissionnaireOffre, ContratMarche, AvenantContrat,
)


# ─── Plan de passation des marchés ───────────────────────────────────────────

class PlanPassationMarcheListSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    nb_demandes = serializers.SerializerMethodField()
    nb_appels_offre = serializers.SerializerMethodField()

    class Meta:
        model = PlanPassationMarche
        fields = [
            'id', 'annee', 'titre', 'statut', 'programme', 'projet',
            'budget_total_prevu', 'date_validation',
            'cree_par', 'cree_par_detail',
            'valide_par', 'valide_par_detail',
            'nb_demandes', 'nb_appels_offre', 'created_at',
        ]

    def get_nb_demandes(self, obj):
        return obj.demandes.count()

    def get_nb_appels_offre(self, obj):
        return obj.appels_offre.count()


class PlanPassationMarcheDetailSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)
    nb_demandes = serializers.SerializerMethodField()
    nb_appels_offre = serializers.SerializerMethodField()

    class Meta:
        model = PlanPassationMarche
        fields = [
            'id', 'annee', 'titre', 'description', 'statut',
            'programme', 'projet',
            'budget_total_prevu',
            'cree_par', 'cree_par_detail',
            'valide_par', 'valide_par_detail',
            'date_validation',
            'nb_demandes', 'nb_appels_offre',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_demandes(self, obj):
        return obj.demandes.count()

    def get_nb_appels_offre(self, obj):
        return obj.appels_offre.count()


# ─── Demande d'achat ─────────────────────────────────────────────────────────

class DemandeAchatListSerializer(serializers.ModelSerializer):
    demandeur_detail = UserMinimalSerializer(source='demandeur', read_only=True)
    valideur_detail = UserMinimalSerializer(source='valideur', read_only=True)

    class Meta:
        model = DemandeAchat
        fields = [
            'id', 'reference', 'titre', 'type_marche', 'priorite', 'statut',
            'programme', 'projet', 'plan_passation',
            'budget_estime', 'date_besoin',
            'demandeur', 'demandeur_detail',
            'valideur', 'valideur_detail',
            'created_at',
        ]


class DemandeAchatDetailSerializer(serializers.ModelSerializer):
    demandeur_detail = UserMinimalSerializer(source='demandeur', read_only=True)
    valideur_detail = UserMinimalSerializer(source='valideur', read_only=True)
    appel_offre_reference = serializers.SerializerMethodField()

    class Meta:
        model = DemandeAchat
        fields = [
            'id', 'reference', 'titre', 'description',
            'type_marche', 'priorite', 'statut',
            'programme', 'projet', 'plan_passation',
            'budget_estime', 'date_besoin',
            'justification', 'specifications_techniques',
            'demandeur', 'demandeur_detail',
            'valideur', 'valideur_detail',
            'date_validation', 'motif_rejet',
            'appel_offre_reference',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_appel_offre_reference(self, obj):
        try:
            return obj.appel_offre.reference if obj.appel_offre else None
        except Exception:
            return None


# ─── Appel d'offres ──────────────────────────────────────────────────────────

class AppelOffreListSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    nb_soumissionnaires = serializers.SerializerMethodField()

    class Meta:
        model = AppelOffre
        fields = [
            'id', 'reference', 'titre', 'type_marche', 'statut',
            'programme', 'projet', 'plan_passation',
            'budget_estime', 'date_publication', 'date_limite_soumission',
            'responsable', 'responsable_detail',
            'nb_soumissionnaires', 'created_at',
        ]

    def get_nb_soumissionnaires(self, obj):
        return obj.soumissionnaires.count()


class AppelOffreDetailSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    nb_soumissionnaires = serializers.SerializerMethodField()
    soumissionnaire_selectionne = serializers.SerializerMethodField()

    class Meta:
        model = AppelOffre
        fields = [
            'id', 'reference', 'titre', 'description',
            'type_marche', 'statut',
            'demande_achat', 'plan_passation',
            'programme', 'projet',
            'budget_estime',
            'date_publication', 'date_limite_soumission', 'date_ouverture_plis',
            'lieu_depot', 'criteres_evaluation', 'documents_requis',
            'fichier_dao', 'nb_lots',
            'responsable', 'responsable_detail',
            'nb_soumissionnaires', 'soumissionnaire_selectionne',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_nb_soumissionnaires(self, obj):
        return obj.soumissionnaires.count()

    def get_soumissionnaire_selectionne(self, obj):
        s = obj.soumissionnaires.filter(statut='selectionne').first()
        if s:
            return {'id': s.id, 'nom_entreprise': s.nom_entreprise,
                    'montant_offre': float(s.montant_offre or 0),
                    'note_globale': float(s.note_globale or 0)}
        return None


# ─── Soumissionnaire ─────────────────────────────────────────────────────────

class SoumissionnaireOffreSerializer(serializers.ModelSerializer):
    note_globale = serializers.ReadOnlyField()

    class Meta:
        model = SoumissionnaireOffre
        fields = [
            'id', 'appel_offre',
            'nom_entreprise', 'pays', 'contact', 'email', 'telephone',
            'montant_offre', 'date_soumission', 'statut',
            'note_technique', 'note_financiere', 'note_globale',
            'poids_technique', 'poids_financier',
            'observations', 'fichier_offre', 'created_at',
        ]
        read_only_fields = ['id', 'note_globale', 'created_at']


class SoumissionnaireOffreListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoumissionnaireOffre
        fields = [
            'id', 'appel_offre', 'nom_entreprise', 'pays',
            'montant_offre', 'statut',
            'note_technique', 'note_financiere', 'note_globale',
            'date_soumission', 'created_at',
        ]


# ─── Contrat marché ──────────────────────────────────────────────────────────

class AvenantContratSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvenantContrat
        fields = [
            'id', 'contrat', 'numero_avenant', 'motif', 'description',
            'montant_supplementaire', 'nouveau_montant_ttc',
            'extension_jours', 'nouvelle_date_fin',
            'date_signature', 'statut', 'fichier', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ContratMarcheListSerializer(serializers.ModelSerializer):
    gestionnaire_detail = UserMinimalSerializer(source='gestionnaire', read_only=True)
    taux_execution = serializers.ReadOnlyField()
    est_en_retard = serializers.ReadOnlyField()
    nb_avenants = serializers.SerializerMethodField()

    class Meta:
        model = ContratMarche
        fields = [
            'id', 'reference', 'titre', 'type_contrat', 'statut',
            'programme', 'projet',
            'prestataire_nom', 'montant_ttc', 'devise',
            'montant_realise', 'taux_execution',
            'date_signature', 'date_debut', 'date_fin_prevue', 'date_fin_reelle',
            'gestionnaire', 'gestionnaire_detail',
            'est_en_retard', 'nb_avenants', 'created_at',
        ]

    def get_nb_avenants(self, obj):
        return obj.avenants.count()


class ContratMarcheDetailSerializer(serializers.ModelSerializer):
    gestionnaire_detail = UserMinimalSerializer(source='gestionnaire', read_only=True)
    taux_execution = serializers.ReadOnlyField()
    est_en_retard = serializers.ReadOnlyField()
    avenants = AvenantContratSerializer(many=True, read_only=True)
    appel_offre_reference = serializers.SerializerMethodField()

    class Meta:
        model = ContratMarche
        fields = [
            'id', 'reference', 'titre', 'type_contrat', 'statut',
            'appel_offre', 'appel_offre_reference',
            'soumissionnaire',
            'programme', 'projet',
            'prestataire_nom', 'prestataire_contact', 'prestataire_email',
            'montant_ttc', 'devise', 'montant_realise', 'taux_execution',
            'date_signature', 'date_debut', 'date_fin_prevue', 'date_fin_reelle',
            'objet', 'conditions_paiement', 'garanties', 'penalites',
            'fichier_contrat', 'notes',
            'gestionnaire', 'gestionnaire_detail',
            'est_en_retard', 'avenants',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_appel_offre_reference(self, obj):
        return obj.appel_offre.reference if obj.appel_offre else None
