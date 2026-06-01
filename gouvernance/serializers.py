from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    Organisation, Direction, SousDirection, Service, Site,
    Partenaire, Bailleur, ComiteDirecteur
)


class OrganisationSerializer(serializers.ModelSerializer):
    directeur_general_detail = UserMinimalSerializer(source='directeur_general', read_only=True)
    nb_utilisateurs = serializers.SerializerMethodField()
    nb_directions = serializers.SerializerMethodField()
    nb_projets = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = [
            'id', 'nom', 'sigle', 'type_organisation', 'statut', 'description',
            'logo', 'adresse', 'ville', 'pays', 'telephone', 'email', 'site_web',
            'date_creation', 'numero_agrement', 'directeur_general', 'directeur_general_detail',
            'nb_utilisateurs', 'nb_directions', 'nb_projets',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_utilisateurs(self, obj):
        return obj.utilisateurs.filter(is_active=True).count()

    def get_nb_directions(self, obj):
        return obj.directions.filter(actif=True).count()

    def get_nb_projets(self, obj):
        try:
            return obj.programmes.aggregate(
                total=__import__('django.db.models', fromlist=['Count']).Count('projets')
            )['total'] or 0
        except Exception:
            return 0


class ServiceMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'code', 'intitule', 'responsable']


class SousDirectionSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    services = ServiceMinimalSerializer(many=True, read_only=True)
    nb_agents = serializers.SerializerMethodField()

    class Meta:
        model = SousDirection
        fields = ['id', 'direction', 'code', 'nom', 'description',
                  'responsable', 'responsable_detail', 'services', 'nb_agents', 'actif', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_nb_agents(self, obj):
        return obj.services.aggregate(
            total=__import__('django.db.models', fromlist=['Count']).Count('utilisateurs', distinct=True)
        ).get('total', 0)


class ServiceSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    direction_nom = serializers.CharField(source='direction.nom', read_only=True)
    sous_direction_nom = serializers.CharField(source='sous_direction.nom', read_only=True)
    nb_agents = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ['id', 'direction', 'direction_nom', 'sous_direction', 'sous_direction_nom',
                  'code', 'intitule', 'description',
                  'responsable', 'responsable_detail', 'nb_agents', 'actif', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_nb_agents(self, obj):
        return obj.utilisateurs.filter(is_active=True).count()


class DirectionSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    sous_directions = SousDirectionSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    nb_agents = serializers.SerializerMethodField()

    class Meta:
        model = Direction
        fields = ['id', 'organisation', 'code', 'nom', 'sigle', 'description',
                  'responsable', 'responsable_detail', 'sous_directions', 'services',
                  'nb_agents', 'actif', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_nb_agents(self, obj):
        return obj.utilisateurs.filter(is_active=True).count()


class SiteSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    nb_agents = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = ['id', 'organisation', 'code', 'nom', 'type_site',
                  'adresse', 'ville', 'region', 'pays', 'telephone', 'email',
                  'responsable', 'responsable_detail', 'latitude', 'longitude',
                  'nb_agents', 'actif', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_nb_agents(self, obj):
        return obj.utilisateurs.filter(is_active=True).count()


class PartenaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partenaire
        fields = [
            'id', 'organisation', 'nom', 'sigle', 'type_partenaire', 'statut',
            'pays', 'adresse', 'telephone', 'email', 'site_web', 'logo',
            'contact_nom', 'contact_fonction', 'contact_telephone', 'contact_email',
            'date_debut_partenariat', 'date_fin_partenariat',
            'domaines_intervention', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BailleurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bailleur
        fields = [
            'id', 'organisation', 'nom', 'sigle', 'type_bailleur', 'pays_origine',
            'adresse', 'telephone', 'email', 'site_web', 'logo',
            'contact_nom', 'contact_fonction', 'contact_telephone', 'contact_email',
            'exigences_reporting', 'conditions_financement', 'notes',
            'actif', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComiteDirecteurSerializer(serializers.ModelSerializer):
    president_detail = UserMinimalSerializer(source='president', read_only=True)
    participants_detail = UserMinimalSerializer(source='participants', many=True, read_only=True)

    class Meta:
        model = ComiteDirecteur
        fields = [
            'id', 'organisation', 'intitule', 'date_tenue', 'lieu', 'statut',
            'ordre_du_jour', 'compte_rendu',
            'president', 'president_detail', 'participants', 'participants_detail',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ─── Organigramme ─────────────────────────────────────────────────────────────

class OrganigrammeServiceSerializer(serializers.ModelSerializer):
    agents = UserMinimalSerializer(source='utilisateurs', many=True, read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'code', 'intitule', 'responsable', 'agents']


class OrganigrammeSousDirectionSerializer(serializers.ModelSerializer):
    services = OrganigrammeServiceSerializer(many=True, read_only=True)

    class Meta:
        model = SousDirection
        fields = ['id', 'code', 'nom', 'responsable', 'services']


class OrganigrammeDirectionSerializer(serializers.ModelSerializer):
    sous_directions = OrganigrammeSousDirectionSerializer(many=True, read_only=True)
    services = OrganigrammeServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Direction
        fields = ['id', 'code', 'nom', 'sigle', 'responsable', 'sous_directions', 'services']


class OrganigrammeSerializer(serializers.ModelSerializer):
    directions = OrganigrammeDirectionSerializer(many=True, read_only=True)
    sites = SiteSerializer(many=True, read_only=True)

    class Meta:
        model = Organisation
        fields = ['id', 'nom', 'sigle', 'type_organisation', 'logo',
                  'directeur_general', 'directions', 'sites']
