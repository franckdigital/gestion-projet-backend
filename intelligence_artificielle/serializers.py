from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    ConversationIA, MessageIA,
    GenerationDocument,
    ModeleIA, AnalyseIAPredictive, AlerteIA, RecommandationIA,
    JournalIA,
)


# ─── M31 : Assistant IA ───────────────────────────────────────────────────────

class MessageIASerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageIA
        fields = [
            'id', 'conversation', 'role', 'contenu',
            'requete_metier', 'donnees_contexte',
            'tokens_utilises', 'duree_traitement_ms', 'confiance',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'tokens_utilises',
                            'duree_traitement_ms', 'requete_metier']


class ConversationIAListSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)
    nb_messages = serializers.SerializerMethodField()
    dernier_message = serializers.SerializerMethodField()

    class Meta:
        model = ConversationIA
        fields = [
            'id', 'titre', 'contexte', 'projet', 'programme',
            'utilisateur', 'utilisateur_detail',
            'archivee', 'nb_messages', 'dernier_message',
            'created_at', 'updated_at',
        ]

    def get_nb_messages(self, obj):
        return obj.messages.count()

    def get_dernier_message(self, obj):
        m = obj.messages.order_by('-created_at').first()
        return {'role': m.role, 'extrait': m.contenu[:100]} if m else None


class ConversationIADetailSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)
    messages = MessageIASerializer(many=True, read_only=True)

    class Meta:
        model = ConversationIA
        fields = [
            'id', 'titre', 'contexte', 'projet', 'programme',
            'utilisateur', 'utilisateur_detail',
            'archivee', 'messages', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─── M32 : Génération documentaire IA ────────────────────────────────────────

class GenerationDocumentListSerializer(serializers.ModelSerializer):
    demande_par_detail = UserMinimalSerializer(source='demande_par', read_only=True)

    class Meta:
        model = GenerationDocument
        fields = [
            'id', 'titre', 'type_document', 'mode', 'langue',
            'projet', 'programme',
            'statut', 'score_qualite', 'tokens_utilises',
            'demande_par', 'demande_par_detail',
            'created_at', 'completed_at',
        ]


class GenerationDocumentDetailSerializer(serializers.ModelSerializer):
    demande_par_detail = UserMinimalSerializer(source='demande_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = GenerationDocument
        fields = [
            'id', 'titre', 'type_document', 'mode', 'langue',
            'projet', 'programme',
            'instructions', 'texte_source', 'parametres',
            'contenu_genere', 'statut', 'score_qualite', 'tokens_utilises',
            'document_ged',
            'demande_par', 'demande_par_detail',
            'valide_par', 'valide_par_detail', 'date_validation',
            'created_at', 'completed_at',
        ]
        read_only_fields = ['id', 'contenu_genere', 'statut', 'score_qualite',
                            'tokens_utilises', 'created_at', 'completed_at']


# ─── M33 : IA Prédictive ──────────────────────────────────────────────────────

class ModeleIASerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleIA
        fields = [
            'id', 'nom', 'type_modele', 'description', 'statut',
            'version', 'precision', 'parametres',
            'derniere_execution', 'nb_executions', 'created_at',
        ]
        read_only_fields = ['id', 'nb_executions', 'derniere_execution', 'created_at']


class AlerteIASerializer(serializers.ModelSerializer):
    destinataire_detail = UserMinimalSerializer(source='destinataire', read_only=True)

    class Meta:
        model = AlerteIA
        fields = [
            'id', 'analyse', 'type_alerte', 'niveau', 'titre', 'message',
            'details', 'destinataire', 'destinataire_detail',
            'lue', 'traitee', 'date_alerte', 'date_traitement',
        ]
        read_only_fields = ['id', 'date_alerte']


class RecommandationIASerializer(serializers.ModelSerializer):
    acceptee_par_detail = UserMinimalSerializer(source='acceptee_par', read_only=True)

    class Meta:
        model = RecommandationIA
        fields = [
            'id', 'analyse', 'type_recommandation', 'titre', 'description',
            'justification', 'impact_estime', 'priorite', 'statut',
            'score_pertinence', 'projet', 'programme',
            'acceptee_par', 'acceptee_par_detail',
            'date_decision', 'motif_rejet', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AnalyseIAPredictiveListSerializer(serializers.ModelSerializer):
    demande_par_detail = UserMinimalSerializer(source='demande_par', read_only=True)
    nb_alertes = serializers.SerializerMethodField()
    nb_recommandations = serializers.SerializerMethodField()

    class Meta:
        model = AnalyseIAPredictive
        fields = [
            'id', 'type_analyse', 'projet', 'programme',
            'statut', 'score_confiance',
            'demande_par', 'demande_par_detail',
            'nb_alertes', 'nb_recommandations',
            'created_at', 'completed_at',
        ]

    def get_nb_alertes(self, obj):
        return obj.alertes.count()

    def get_nb_recommandations(self, obj):
        return obj.recommandations.count()


class AnalyseIAPredictiveDetailSerializer(serializers.ModelSerializer):
    demande_par_detail = UserMinimalSerializer(source='demande_par', read_only=True)
    alertes = AlerteIASerializer(many=True, read_only=True)
    recommandations = RecommandationIASerializer(many=True, read_only=True)

    class Meta:
        model = AnalyseIAPredictive
        fields = [
            'id', 'modele', 'type_analyse', 'projet', 'programme',
            'parametres', 'statut',
            'resultats', 'previsions', 'anomalies', 'suggestions_ia',
            'score_confiance',
            'demande_par', 'demande_par_detail',
            'created_at', 'completed_at',
            'alertes', 'recommandations',
        ]
        read_only_fields = ['id', 'resultats', 'previsions', 'anomalies',
                            'statut', 'created_at', 'completed_at']


# ─── Journal IA ───────────────────────────────────────────────────────────────

class JournalIASerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = JournalIA
        fields = [
            'id', 'type_action', 'utilisateur', 'utilisateur_detail',
            'objet_type', 'objet_id', 'description',
            'parametres_entree', 'resultats_sortie',
            'tokens_utilises', 'duree_ms', 'succes', 'message_erreur',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
