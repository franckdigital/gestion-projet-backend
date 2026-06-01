from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import Evenement, ParticipantEvenement, DepenseEvenement


class ParticipantSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = ParticipantEvenement
        fields = ['id', 'evenement', 'utilisateur', 'utilisateur_detail',
                  'nom', 'prenom', 'email', 'organisation', 'fonction', 'telephone',
                  'statut', 'date_confirmation', 'date_presence', 'qr_code',
                  'note_evaluation', 'commentaire_evaluation', 'created_at']
        read_only_fields = ['id', 'qr_code', 'created_at']


class DepenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepenseEvenement
        fields = ['id', 'evenement', 'categorie', 'description', 'montant',
                  'fournisseur', 'date_depense', 'facture_ref', 'saisi_par', 'created_at']
        read_only_fields = ['id', 'saisi_par', 'created_at']


class EvenementListSerializer(serializers.ModelSerializer):
    organisateur_detail = UserMinimalSerializer(source='organisateur', read_only=True)
    nb_participants = serializers.SerializerMethodField()
    taux_budget = serializers.SerializerMethodField()

    class Meta:
        model = Evenement
        fields = [
            'id', 'titre', 'type_evenement', 'statut',
            'date_debut', 'date_fin', 'lieu',
            'organisateur', 'organisateur_detail',
            'programme', 'projet',
            'budget_prevu', 'budget_realise',
            'nombre_participants_prevu', 'nb_participants',
            'taux_budget', 'avec_inscription',
            'created_at',
        ]

    def get_nb_participants(self, obj):
        return obj.participants.filter(statut__in=['confirme', 'present']).count()

    def get_taux_budget(self, obj):
        if obj.budget_prevu and obj.budget_prevu > 0:
            return round(float(obj.budget_realise) / float(obj.budget_prevu) * 100, 1)
        return 0


class EvenementDetailSerializer(serializers.ModelSerializer):
    organisateur_detail = UserMinimalSerializer(source='organisateur', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    participants = ParticipantSerializer(many=True, read_only=True)
    depenses = DepenseSerializer(many=True, read_only=True)
    nb_participants = serializers.SerializerMethodField()

    class Meta:
        model = Evenement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_participants(self, obj):
        return obj.participants.filter(statut__in=['confirme', 'present']).count()
