from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    CourrierEntrant, CourrierSortant,
    CircuitValidation, EtapeCircuit, Parapheur, VisaParapheur, Diligence,
    ModeleCourrierSortant,
)


class DiligenceSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)

    class Meta:
        model = Diligence
        fields = ['id', 'courrier', 'type_diligence', 'description', 'responsable',
                  'responsable_detail', 'echeance', 'statut', 'resultat',
                  'assigne_par', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModeleCourrierSortantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleCourrierSortant
        fields = ['id', 'nom', 'type_courrier', 'description', 'objet', 'corps',
                  'actif', 'cree_par', 'created_at', 'updated_at']
        read_only_fields = ['id', 'cree_par', 'created_at', 'updated_at']


class CourrierEntrantListSerializer(serializers.ModelSerializer):
    affecte_a_detail = UserMinimalSerializer(source='affecte_a', read_only=True)

    class Meta:
        model = CourrierEntrant
        fields = ['id', 'numero', 'date_reception', 'expediteur', 'organisation_expediteur',
                  'objet', 'urgence', 'canal', 'statut', 'projet', 'programme',
                  'affecte_a', 'affecte_a_detail', 'ocr_effectue', 'created_at']


class CourrierEntrantDetailSerializer(serializers.ModelSerializer):
    affecte_a_detail = UserMinimalSerializer(source='affecte_a', read_only=True)
    enregistre_par_detail = UserMinimalSerializer(source='enregistre_par', read_only=True)
    diligences = DiligenceSerializer(many=True, read_only=True)

    class Meta:
        model = CourrierEntrant
        fields = [
            'id', 'numero', 'date_reception', 'expediteur', 'organisation_expediteur',
            'email_expediteur', 'objet', 'description', 'urgence', 'canal', 'statut',
            'programme', 'projet',
            'fichier_scan', 'ocr_effectue', 'texte_ocr', 'document_ged',
            'affecte_a', 'affecte_a_detail', 'date_affectation', 'instruction_affectation',
            'date_traitement', 'reponse_donnee',
            'enregistre_par', 'enregistre_par_detail', 'notes', 'created_at', 'updated_at',
            'diligences',
        ]
        read_only_fields = ['id', 'numero', 'created_at', 'updated_at']


class CourrierSortantListSerializer(serializers.ModelSerializer):
    redacteur_detail = UserMinimalSerializer(source='redacteur', read_only=True)

    class Meta:
        model = CourrierSortant
        fields = ['id', 'reference', 'type_courrier', 'objet', 'destinataire',
                  'organisation_destinataire', 'date_courrier', 'date_expedition',
                  'statut', 'projet', 'programme', 'redacteur', 'redacteur_detail', 'created_at']


class CourrierSortantDetailSerializer(serializers.ModelSerializer):
    redacteur_detail = UserMinimalSerializer(source='redacteur', read_only=True)
    signataire_detail = UserMinimalSerializer(source='signataire', read_only=True)

    class Meta:
        model = CourrierSortant
        fields = [
            'id', 'reference', 'type_courrier', 'objet', 'corps', 'destinataire',
            'organisation_destinataire', 'email_destinataire', 'date_courrier', 'date_expedition',
            'statut', 'programme', 'projet', 'en_reponse_a',
            'fichier', 'document_ged', 'modele_utilise',
            'redacteur', 'redacteur_detail', 'signataire', 'signataire_detail',
            'date_signature', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']


class EtapeCircuitSerializer(serializers.ModelSerializer):
    validateur_detail = UserMinimalSerializer(source='validateur', read_only=True)

    class Meta:
        model = EtapeCircuit
        fields = ['id', 'circuit', 'ordre', 'nom_etape', 'validateur', 'validateur_detail',
                  'role', 'obligatoire', 'delai_jours']


class CircuitValidationSerializer(serializers.ModelSerializer):
    etapes = EtapeCircuitSerializer(many=True, read_only=True)

    class Meta:
        model = CircuitValidation
        fields = ['id', 'nom', 'description', 'est_actif', 'created_at', 'etapes']
        read_only_fields = ['id', 'created_at']


class VisaParapheurSerializer(serializers.ModelSerializer):
    validateur_detail = UserMinimalSerializer(source='validateur', read_only=True)
    etape_detail      = EtapeCircuitSerializer(source='etape', read_only=True)

    class Meta:
        model = VisaParapheur
        fields = ['id', 'parapheur', 'etape', 'etape_detail', 'ordre',
                  'validateur', 'validateur_detail',
                  'decision', 'commentaire', 'date_visa', 'delai_prevu']
        read_only_fields = ['id', 'date_visa']


class ParapheurListSerializer(serializers.ModelSerializer):
    soumis_par_detail = UserMinimalSerializer(source='soumis_par', read_only=True)
    nb_visas_en_attente = serializers.SerializerMethodField()

    class Meta:
        model = Parapheur
        fields = ['id', 'reference', 'intitule', 'statut', 'etape_courante',
                  'soumis_par', 'soumis_par_detail', 'date_soumission',
                  'nb_visas_en_attente', 'date_cloture']

    def get_nb_visas_en_attente(self, obj):
        return obj.visas.filter(decision='en_attente').count()


class ParapheurDetailSerializer(serializers.ModelSerializer):
    soumis_par_detail = UserMinimalSerializer(source='soumis_par', read_only=True)
    visas = VisaParapheurSerializer(many=True, read_only=True)

    class Meta:
        model = Parapheur
        fields = [
            'id', 'reference', 'intitule', 'circuit', 'statut', 'etape_courante',
            'courrier_sortant', 'document_ged',
            'soumis_par', 'soumis_par_detail', 'date_soumission',
            'date_cloture', 'notes', 'visas',
        ]
        read_only_fields = ['id', 'reference', 'date_soumission']
