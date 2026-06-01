from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    Canal, MembreCanal, Message, LectureMessage,
    Notification, PreferenceNotification, ActiviteRecente, GroupeTravail,
    Evenement, ParticipantEvenement, DepenseEvenement,
)


class MembreCanalSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = MembreCanal
        fields = ['id', 'canal', 'utilisateur', 'utilisateur_detail',
                  'role', 'rejoint_le', 'dernier_lu', 'notifications_actives']
        read_only_fields = ['id', 'rejoint_le']


class CanalListSerializer(serializers.ModelSerializer):
    nb_membres = serializers.SerializerMethodField()
    dernier_message = serializers.SerializerMethodField()

    class Meta:
        model = Canal
        fields = ['id', 'nom', 'type_canal', 'description', 'projet', 'programme',
                  'est_prive', 'archive', 'nb_membres', 'dernier_message', 'created_at']

    def get_nb_membres(self, obj):
        return obj.memberships.count()

    def get_dernier_message(self, obj):
        last = obj.messages.filter(supprime=False).order_by('-created_at').first()
        if last:
            return {'contenu': last.contenu[:80], 'date': last.created_at}
        return None


class CanalDetailSerializer(serializers.ModelSerializer):
    membres = MembreCanalSerializer(source='memberships', many=True, read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = Canal
        fields = ['id', 'nom', 'type_canal', 'description', 'projet', 'programme',
                  'est_prive', 'archive', 'cree_par', 'cree_par_detail', 'created_at',
                  'membres']
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)
    nb_reactions = serializers.SerializerMethodField()
    lu_par_moi = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'canal', 'auteur', 'auteur_detail', 'type_message',
                  'contenu', 'fichier', 'en_reponse_a', 'reactions', 'nb_reactions',
                  'modifie', 'supprime', 'created_at', 'updated_at', 'lu_par_moi']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_reactions(self, obj):
        return sum(len(v) if isinstance(v, list) else 1
                   for v in obj.reactions.values()) if obj.reactions else 0

    def get_lu_par_moi(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.lectures.filter(utilisateur=request.user).exists()
        return False


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type_notification', 'titre', 'message', 'priorite',
                  'canal', 'lue', 'date_lecture', 'lien', 'objet_type', 'objet_id',
                  'envoyee', 'date_envoi', 'created_at']
        read_only_fields = ['id', 'created_at', 'date_lecture', 'envoyee', 'date_envoi']


class PreferenceNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferenceNotification
        fields = ['id', 'email_active', 'sms_active', 'push_active', 'whatsapp_active',
                  'types_actives', 'heure_debut_silence', 'heure_fin_silence', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class ActiviteRecenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiviteRecente
        fields = ['id', 'type_activite', 'titre', 'description', 'lien',
                  'objet_type', 'objet_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class GroupeTravailSerializer(serializers.ModelSerializer):
    membres_detail = UserMinimalSerializer(source='membres', many=True, read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = GroupeTravail
        fields = ['id', 'nom', 'type_groupe', 'description', 'membres', 'membres_detail',
                  'programme', 'projet', 'actif', 'cree_par', 'cree_par_detail', 'created_at']
        read_only_fields = ['id', 'created_at']


# ─── M43 : Événements ─────────────────────────────────────────────────────────

class ParticipantEvenementSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = ParticipantEvenement
        fields = ['id', 'evenement', 'utilisateur', 'utilisateur_detail',
                  'nom_externe', 'organisation', 'email', 'telephone',
                  'statut', 'heure_arrivee', 'heure_depart',
                  'code_badge', 'qr_code_scan', 'note_evaluation', 'commentaire', 'created_at']
        read_only_fields = ['id', 'created_at']


class DepenseEvenementSerializer(serializers.ModelSerializer):
    saisi_par_detail = UserMinimalSerializer(source='saisi_par', read_only=True)

    class Meta:
        model = DepenseEvenement
        fields = ['id', 'evenement', 'categorie', 'libelle', 'montant',
                  'fournisseur', 'facture', 'saisi_par', 'saisi_par_detail', 'created_at']
        read_only_fields = ['id', 'created_at']


class EvenementListSerializer(serializers.ModelSerializer):
    organisateur_detail = UserMinimalSerializer(source='organisateur', read_only=True)
    nb_participants = serializers.SerializerMethodField()
    taux_budget = serializers.ReadOnlyField()

    class Meta:
        model = Evenement
        fields = ['id', 'titre', 'type_evenement', 'statut', 'description',
                  'projet', 'programme',
                  'date_debut', 'date_fin', 'lieu',
                  'nb_participants_attendus', 'budget_prevu', 'budget_realise',
                  'taux_budget', 'nb_participants',
                  'organisateur', 'organisateur_detail',
                  'inscription_requise', 'date_limite_inscription',
                  'created_at']

    def get_nb_participants(self, obj):
        return obj.participants.exclude(statut='annule').count()


class EvenementDetailSerializer(serializers.ModelSerializer):
    organisateur_detail = UserMinimalSerializer(source='organisateur', read_only=True)
    participants = ParticipantEvenementSerializer(many=True, read_only=True)
    depenses = DepenseEvenementSerializer(many=True, read_only=True)
    nb_participants = serializers.SerializerMethodField()
    taux_budget = serializers.ReadOnlyField()

    class Meta:
        model = Evenement
        fields = ['id', 'titre', 'type_evenement', 'statut', 'description', 'objectifs',
                  'projet', 'programme',
                  'date_debut', 'date_fin', 'lieu', 'adresse', 'latitude', 'longitude',
                  'nb_participants_attendus', 'budget_prevu', 'budget_realise', 'taux_budget',
                  'ordre_du_jour', 'compte_rendu',
                  'fichier_programme', 'fichier_compte_rendu',
                  'organisateur', 'organisateur_detail',
                  'est_public', 'inscription_requise', 'date_limite_inscription', 'lien_visio',
                  'nb_participants', 'participants', 'depenses',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_participants(self, obj):
        return obj.participants.exclude(statut='annule').count()
