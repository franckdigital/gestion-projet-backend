from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import Diligence, SuiviDiligence, RelanceDiligence


class SuiviDiligenceSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)

    class Meta:
        model = SuiviDiligence
        fields = ['id', 'diligence', 'auteur', 'auteur_detail', 'date_suivi',
                  'avancement', 'observations', 'actions_realisees', 'prochaines_etapes', 'created_at']
        read_only_fields = ['id', 'created_at']


class RelanceDiligenceSerializer(serializers.ModelSerializer):
    emetteur_detail = UserMinimalSerializer(source='emetteur', read_only=True)

    class Meta:
        model = RelanceDiligence
        fields = ['id', 'diligence', 'emetteur', 'emetteur_detail', 'message', 'date_relance']
        read_only_fields = ['id', 'date_relance']


class DiligenceListSerializer(serializers.ModelSerializer):
    emetteur_detail = UserMinimalSerializer(source='emetteur', read_only=True)
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    nb_suivis = serializers.SerializerMethodField()
    est_en_retard = serializers.SerializerMethodField()

    class Meta:
        model = Diligence
        fields = [
            'id', 'reference', 'titre', 'type_source', 'priorite', 'statut',
            'emetteur', 'emetteur_detail', 'responsable', 'responsable_detail',
            'programme', 'projet', 'date_echeance', 'taux_avancement',
            'nb_suivis', 'est_en_retard', 'created_at',
        ]

    def get_nb_suivis(self, obj):
        return obj.suivis.count()

    def get_est_en_retard(self, obj):
        if obj.date_echeance and obj.statut not in ('cloturee', 'annulee'):
            from django.utils import timezone
            return obj.date_echeance < timezone.now().date()
        return False


class DiligenceDetailSerializer(serializers.ModelSerializer):
    emetteur_detail = UserMinimalSerializer(source='emetteur', read_only=True)
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    suivis = SuiviDiligenceSerializer(many=True, read_only=True)
    relances = RelanceDiligenceSerializer(many=True, read_only=True)

    class Meta:
        model = Diligence
        fields = '__all__'
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']
