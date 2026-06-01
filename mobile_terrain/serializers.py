from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import SessionTerrain, CollecteTerrain, PointageTerrain, SynchronisationMobile, QRCodeScan


class CollecteTerrainSerializer(serializers.ModelSerializer):
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = CollecteTerrain
        fields = [
            'id', 'session', 'type_collecte', 'indicateur', 'formulaire',
            'titre', 'donnees', 'valeur_numerique', 'notes',
            'fichier_media', 'type_mime', 'taille_fichier',
            'latitude', 'longitude', 'altitude', 'precision_gps', 'adresse_geo',
            'statut', 'valide_par', 'valide_par_detail',
            'date_collecte_locale', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'taille_fichier']


class SessionTerrainListSerializer(serializers.ModelSerializer):
    agent_detail = UserMinimalSerializer(source='agent', read_only=True)
    nb_collectes = serializers.SerializerMethodField()

    class Meta:
        model = SessionTerrain
        fields = [
            'id', 'agent', 'agent_detail', 'projet', 'activite',
            'statut', 'mode_hors_ligne', 'date_debut', 'date_fin',
            'date_synchronisation', 'nb_collectes', 'appareil', 'version_app',
        ]

    def get_nb_collectes(self, obj):
        return obj.collectes.count()


class SessionTerrainDetailSerializer(serializers.ModelSerializer):
    agent_detail = UserMinimalSerializer(source='agent', read_only=True)
    collectes = CollecteTerrainSerializer(many=True, read_only=True)

    class Meta:
        model = SessionTerrain
        fields = [
            'id', 'agent', 'agent_detail', 'projet', 'activite',
            'appareil', 'version_app', 'mode_hors_ligne', 'statut',
            'latitude_debut', 'longitude_debut', 'latitude_fin', 'longitude_fin',
            'date_debut', 'date_fin', 'date_synchronisation',
            'nb_collectes', 'notes', 'collectes',
        ]
        read_only_fields = ['id', 'date_debut', 'nb_collectes']


class PointageTerrainSerializer(serializers.ModelSerializer):
    agent_detail = UserMinimalSerializer(source='agent', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = PointageTerrain
        fields = [
            'id', 'agent', 'agent_detail', 'type_pointage',
            'projet', 'activite',
            'date_heure', 'latitude', 'longitude', 'altitude', 'precision_gps',
            'adresse_geo', 'photo_preuve', 'notes',
            'valide', 'valide_par', 'valide_par_detail', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'valide', 'valide_par']


class SynchronisationMobileSerializer(serializers.ModelSerializer):
    agent_detail = UserMinimalSerializer(source='agent', read_only=True)

    class Meta:
        model = SynchronisationMobile
        fields = [
            'id', 'agent', 'agent_detail', 'date_synchro', 'statut',
            'nb_elements_envoyes', 'nb_elements_recus', 'nb_erreurs',
            'duree_secondes', 'version_app', 'details', 'message_erreur',
        ]
        read_only_fields = ['id', 'date_synchro']


class QRCodeScanSerializer(serializers.ModelSerializer):
    agent_detail = UserMinimalSerializer(source='agent', read_only=True)

    class Meta:
        model = QRCodeScan
        fields = [
            'id', 'agent', 'agent_detail', 'contenu_qr',
            'type_objet', 'objet_id',
            'latitude', 'longitude', 'date_scan', 'traite',
        ]
        read_only_fields = ['id', 'date_scan']
