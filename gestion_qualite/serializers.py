from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import NonConformite, ActionQualite, AuditInterne, IndicateurQualite


class ActionQualiteSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)

    class Meta:
        model = ActionQualite
        fields = ['id', 'non_conformite', 'type_action', 'titre', 'description', 'statut',
                  'responsable', 'responsable_detail', 'date_prevue', 'date_realisation',
                  'resultat', 'efficace', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']


class NonConformiteListSerializer(serializers.ModelSerializer):
    detecte_par_detail = UserMinimalSerializer(source='detecte_par', read_only=True)
    nb_actions = serializers.SerializerMethodField()

    class Meta:
        model = NonConformite
        fields = ['id', 'reference', 'titre', 'type_nc', 'gravite', 'statut',
                  'detecte_par', 'detecte_par_detail', 'responsable',
                  'date_detection', 'date_echeance', 'nb_actions', 'created_at']

    def get_nb_actions(self, obj):
        return obj.actions.count()


class NonConformiteDetailSerializer(serializers.ModelSerializer):
    detecte_par_detail = UserMinimalSerializer(source='detecte_par', read_only=True)
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    actions = ActionQualiteSerializer(many=True, read_only=True)

    class Meta:
        model = NonConformite
        fields = '__all__'
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']


class AuditInterneSerializer(serializers.ModelSerializer):
    auditeur_detail = UserMinimalSerializer(source='auditeur_principal', read_only=True)

    class Meta:
        model = AuditInterne
        fields = '__all__'
        read_only_fields = ['id', 'reference', 'created_at']


class IndicateurQualiteSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    taux_realisation = serializers.SerializerMethodField()

    class Meta:
        model = IndicateurQualite
        fields = ['id', 'code', 'intitule', 'description', 'unite',
                  'valeur_cible', 'valeur_actuelle', 'frequence_mesure',
                  'actif', 'responsable', 'responsable_detail',
                  'taux_realisation', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_taux_realisation(self, obj):
        if obj.valeur_cible and obj.valeur_actuelle and obj.valeur_cible > 0:
            return round(float(obj.valeur_actuelle) / float(obj.valeur_cible) * 100, 1)
        return None
