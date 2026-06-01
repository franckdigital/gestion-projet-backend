from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    ZoneSIG, CoucheCartographique, PointCartographie,
    InfrastructureSIG, CarteSIG,
)


# ─── ZoneSIG ─────────────────────────────────────────────────────────────────

class ZoneSIGMinimalSerializer(serializers.ModelSerializer):
    type_zone_display = serializers.CharField(source='get_type_zone_display', read_only=True)

    class Meta:
        model = ZoneSIG
        fields = ['id', 'nom', 'code', 'type_zone', 'type_zone_display', 'pays']


class ZoneSIGListSerializer(serializers.ModelSerializer):
    type_zone_display = serializers.CharField(source='get_type_zone_display', read_only=True)
    parent_nom = serializers.CharField(source='parent.nom', read_only=True)
    nb_sous_zones = serializers.SerializerMethodField()

    class Meta:
        model = ZoneSIG
        fields = [
            'id', 'nom', 'code', 'type_zone', 'type_zone_display',
            'parent', 'parent_nom', 'pays', 'superficie_km2', 'population',
            'latitude_centre', 'longitude_centre', 'actif',
            'nb_sous_zones', 'created_at',
        ]

    def get_nb_sous_zones(self, obj):
        return obj.sous_zones.count()


class ZoneSIGDetailSerializer(serializers.ModelSerializer):
    type_zone_display = serializers.CharField(source='get_type_zone_display', read_only=True)
    parent_detail = ZoneSIGMinimalSerializer(source='parent', read_only=True)
    sous_zones = ZoneSIGMinimalSerializer(many=True, read_only=True)
    nb_points = serializers.SerializerMethodField()
    nb_infrastructures = serializers.SerializerMethodField()

    class Meta:
        model = ZoneSIG
        fields = [
            'id', 'nom', 'code', 'type_zone', 'type_zone_display',
            'parent', 'parent_detail', 'sous_zones',
            'pays', 'superficie_km2', 'population',
            'latitude_centre', 'longitude_centre', 'geojson', 'actif',
            'nb_points', 'nb_infrastructures', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_nb_points(self, obj):
        return obj.points.count()

    def get_nb_infrastructures(self, obj):
        return obj.infrastructures.count()


# ─── CoucheCartographique ─────────────────────────────────────────────────────

class CoucheCartographiqueListSerializer(serializers.ModelSerializer):
    type_couche_display = serializers.CharField(source='get_type_couche_display', read_only=True)
    style_affichage_display = serializers.CharField(source='get_style_affichage_display', read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    nb_points = serializers.SerializerMethodField()

    class Meta:
        model = CoucheCartographique
        fields = [
            'id', 'nom', 'type_couche', 'type_couche_display',
            'style_affichage', 'style_affichage_display',
            'source_fond', 'couleur', 'icone', 'opacite',
            'est_visible', 'est_publique', 'ordre',
            'filtre_programme', 'filtre_projet',
            'cree_par', 'cree_par_detail', 'nb_points', 'created_at',
        ]

    def get_nb_points(self, obj):
        return obj.points.count()


class CoucheCartographiqueDetailSerializer(serializers.ModelSerializer):
    type_couche_display = serializers.CharField(source='get_type_couche_display', read_only=True)
    style_affichage_display = serializers.CharField(source='get_style_affichage_display', read_only=True)
    source_fond_display = serializers.CharField(source='get_source_fond_display', read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    nb_points = serializers.SerializerMethodField()

    class Meta:
        model = CoucheCartographique
        fields = [
            'id', 'nom', 'type_couche', 'type_couche_display',
            'style_affichage', 'style_affichage_display',
            'source_fond', 'source_fond_display',
            'description', 'couleur', 'icone', 'opacite',
            'est_visible', 'est_publique', 'ordre', 'configuration',
            'filtre_programme', 'filtre_projet',
            'cree_par', 'cree_par_detail', 'nb_points',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_points(self, obj):
        return obj.points.count()


# ─── PointCartographie ────────────────────────────────────────────────────────

class PointCartographieListSerializer(serializers.ModelSerializer):
    type_point_display = serializers.CharField(source='get_type_point_display', read_only=True)
    zone_nom = serializers.CharField(source='zone.nom', read_only=True)
    couche_nom = serializers.CharField(source='couche.nom', read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = PointCartographie
        fields = [
            'id', 'couche', 'couche_nom', 'type_point', 'type_point_display',
            'titre', 'latitude', 'longitude', 'altitude',
            'zone', 'zone_nom', 'programme', 'projet',
            'couleur', 'icone', 'actif',
            'cree_par', 'cree_par_detail', 'created_at',
        ]


class PointCartographieDetailSerializer(serializers.ModelSerializer):
    type_point_display = serializers.CharField(source='get_type_point_display', read_only=True)
    zone_detail = ZoneSIGMinimalSerializer(source='zone', read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = PointCartographie
        fields = [
            'id', 'couche', 'type_point', 'type_point_display',
            'titre', 'description', 'latitude', 'longitude', 'altitude', 'rayon_metres',
            'programme', 'projet', 'zone', 'zone_detail',
            'valeur', 'unite', 'couleur', 'icone', 'proprietes', 'image',
            'source_gps', 'precision_gps', 'actif',
            'cree_par', 'cree_par_detail', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─── InfrastructureSIG ───────────────────────────────────────────────────────

class InfrastructureSIGListSerializer(serializers.ModelSerializer):
    type_infrastructure_display = serializers.CharField(
        source='get_type_infrastructure_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    zone_nom = serializers.CharField(source='zone.nom', read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = InfrastructureSIG
        fields = [
            'id', 'nom', 'type_infrastructure', 'type_infrastructure_display',
            'statut', 'statut_display', 'latitude', 'longitude',
            'zone', 'zone_nom', 'programme', 'projet',
            'capacite', 'population_beneficiaire', 'date_mise_en_service',
            'cree_par', 'cree_par_detail', 'created_at',
        ]


class InfrastructureSIGDetailSerializer(serializers.ModelSerializer):
    type_infrastructure_display = serializers.CharField(
        source='get_type_infrastructure_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    zone_detail = ZoneSIGMinimalSerializer(source='zone', read_only=True)
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = InfrastructureSIG
        fields = [
            'id', 'nom', 'type_infrastructure', 'type_infrastructure_display',
            'statut', 'statut_display', 'description',
            'latitude', 'longitude', 'zone', 'zone_detail',
            'programme', 'projet',
            'capacite', 'population_beneficiaire', 'date_mise_en_service',
            'cout_realisation', 'photos', 'proprietes',
            'cree_par', 'cree_par_detail', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─── CarteSIG ─────────────────────────────────────────────────────────────────

class CarteSIGListSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    nb_couches = serializers.SerializerMethodField()

    class Meta:
        model = CarteSIG
        fields = [
            'id', 'nom', 'description', 'centre_lat', 'centre_lon', 'zoom_defaut',
            'est_publique', 'est_defaut', 'programme', 'projet',
            'cree_par', 'cree_par_detail', 'nb_couches', 'created_at',
        ]

    def get_nb_couches(self, obj):
        return obj.couches.count()


class CarteSIGDetailSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)
    couches_detail = CoucheCartographiqueListSerializer(source='couches', many=True, read_only=True)

    class Meta:
        model = CarteSIG
        fields = [
            'id', 'nom', 'description',
            'couches', 'couches_detail',
            'centre_lat', 'centre_lon', 'zoom_defaut',
            'est_publique', 'est_defaut',
            'programme', 'projet',
            'cree_par', 'cree_par_detail',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
