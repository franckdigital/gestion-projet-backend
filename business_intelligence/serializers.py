from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    TableauBord, WidgetTableauBord, PartageTableauBord,
    DataWarehouseSnapshot, RapportBI,
    DatamartFinance, DatamartSE,
    DatamartRH, DatamartCourrier, DatamartGED, DatamartRisque,
    ConnecteurBI, KPIPersonnalise,
)


class WidgetTableauBordSerializer(serializers.ModelSerializer):
    valeur_calculee = serializers.SerializerMethodField()

    class Meta:
        model = WidgetTableauBord
        fields = [
            'id', 'tableau_bord', 'titre', 'type_widget', 'source_donnees',
            'colonne', 'ligne', 'largeur', 'hauteur',
            'configuration', 'filtre_projet', 'filtre_programme',
            'actualisation_minutes', 'actif', 'ordre',
            'valeur_calculee', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_valeur_calculee(self, obj):
        return obj.calculer_valeur()


class PartageTableauBordSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = PartageTableauBord
        fields = ['id', 'tableau_bord', 'utilisateur', 'utilisateur_detail', 'niveau', 'created_at']
        read_only_fields = ['id', 'created_at']


class TableauBordListSerializer(serializers.ModelSerializer):
    proprietaire_detail = UserMinimalSerializer(source='proprietaire', read_only=True)
    nb_widgets = serializers.SerializerMethodField()

    class Meta:
        model = TableauBord
        fields = [
            'id', 'nom', 'type_dashboard', 'description',
            'est_public', 'est_defaut', 'actif',
            'proprietaire', 'proprietaire_detail',
            'programme', 'projet',
            'nb_widgets', 'created_at', 'updated_at',
        ]

    def get_nb_widgets(self, obj):
        return obj.widgets.filter(actif=True).count()


class TableauBordDetailSerializer(serializers.ModelSerializer):
    proprietaire_detail = UserMinimalSerializer(source='proprietaire', read_only=True)
    widgets = WidgetTableauBordSerializer(many=True, read_only=True)
    partages = PartageTableauBordSerializer(many=True, read_only=True)

    class Meta:
        model = TableauBord
        fields = [
            'id', 'nom', 'type_dashboard', 'description',
            'est_public', 'est_defaut', 'actif',
            'proprietaire', 'proprietaire_detail',
            'programme', 'projet',
            'configuration',
            'widgets', 'partages',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DataWarehouseSnapshotSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = DataWarehouseSnapshot
        fields = [
            'id', 'type_snapshot', 'periode_debut', 'periode_fin',
            'donnees', 'taille_ko', 'nb_enregistrements',
            'cree_par', 'cree_par_detail', 'created_at', 'valide',
        ]
        read_only_fields = ['id', 'created_at', 'taille_ko', 'nb_enregistrements']


class RapportBIListSerializer(serializers.ModelSerializer):
    genere_par_detail = UserMinimalSerializer(source='genere_par', read_only=True)

    class Meta:
        model = RapportBI
        fields = [
            'id', 'titre', 'type_rapport', 'periode', 'format_export', 'statut',
            'date_debut_periode', 'date_fin_periode',
            'programme', 'projet',
            'genere_par', 'genere_par_detail',
            'genere_par_ia', 'created_at', 'updated_at',
        ]


class RapportBIDetailSerializer(serializers.ModelSerializer):
    genere_par_detail = UserMinimalSerializer(source='genere_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = RapportBI
        fields = [
            'id', 'titre', 'type_rapport', 'periode', 'format_export', 'statut',
            'date_debut_periode', 'date_fin_periode',
            'programme', 'projet',
            'parametres', 'donnees_calculees', 'fichier',
            'genere_par', 'genere_par_detail',
            'valide_par', 'valide_par_detail', 'date_validation',
            'genere_par_ia', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'donnees_calculees', 'statut', 'created_at', 'updated_at']


class DatamartFinanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatamartFinance
        fields = [
            'id', 'programme', 'projet', 'annee', 'mois', 'trimestre',
            'budget_prevu', 'budget_engage', 'budget_realise', 'taux_execution',
            'nb_transactions', 'categorie_principale', 'bailleur', 'zone_geographique',
            'calculated_at',
        ]
        read_only_fields = ['id', 'calculated_at']


class DatamartSESerializer(serializers.ModelSerializer):
    class Meta:
        model = DatamartSE
        fields = [
            'id', 'programme', 'projet', 'annee', 'trimestre',
            'nb_indicateurs', 'nb_atteints', 'nb_non_atteints', 'taux_realisation_moyen',
            'nb_beneficiaires_hommes', 'nb_beneficiaires_femmes', 'nb_beneficiaires_total',
            'zone_geographique', 'calculated_at',
        ]
        read_only_fields = ['id', 'calculated_at']


class ConnecteurBISerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = ConnecteurBI
        fields = [
            'id', 'nom', 'type_outil', 'url_endpoint', 'configuration',
            'statut', 'derniere_synchro',
            'cree_par', 'cree_par_detail', 'created_at',
        ]
        read_only_fields = ['id', 'derniere_synchro', 'created_at']
        extra_kwargs = {'configuration': {'write_only': True}}


class KPIPersonnaliseSerializer(serializers.ModelSerializer):
    cree_par_detail = UserMinimalSerializer(source='cree_par', read_only=True)

    class Meta:
        model = KPIPersonnalise
        fields = [
            'id', 'nom', 'description', 'formule', 'source_donnees',
            'unite', 'valeur_actuelle', 'statut_calcul',
            'seuil_alerte_bas', 'seuil_alerte_haut',
            'icone', 'couleur', 'programme', 'projet',
            'cree_par', 'cree_par_detail',
            'derniere_maj', 'actif', 'created_at',
        ]
        read_only_fields = ['id', 'valeur_actuelle', 'statut_calcul', 'derniere_maj', 'created_at']


class DatamartRHSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatamartRH
        fields = '__all__'
        read_only_fields = ['id', 'calculated_at']


class DatamartCourrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatamartCourrier
        fields = '__all__'
        read_only_fields = ['id', 'calculated_at']


class DatamartGEDSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatamartGED
        fields = '__all__'
        read_only_fields = ['id', 'calculated_at']


class DatamartRisqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatamartRisque
        fields = '__all__'
        read_only_fields = ['id', 'calculated_at']
