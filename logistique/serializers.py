from rest_framework import serializers
from accounts.serializers import UserMinimalSerializer
from .models import (
    Vehicule, MissionVehicule, EntretienVehicule,
    Equipement, Magasin, ArticleStock, LigneStock, MouvementStock,
)


# ─── M38 : Parc automobile ────────────────────────────────────────────────────

class VehiculeListSerializer(serializers.ModelSerializer):
    est_assurance_expiree = serializers.ReadOnlyField()
    projet_nom = serializers.CharField(source='projet.titre', read_only=True)
    programme_nom = serializers.CharField(source='programme.nom', read_only=True)

    class Meta:
        model = Vehicule
        fields = [
            'id', 'immatriculation', 'type_vehicule', 'marque', 'modele', 'annee',
            'couleur', 'statut', 'programme', 'programme_nom', 'projet', 'projet_nom',
            'kilometrage_actuel', 'date_expiration_assurance', 'date_expiration_vignette',
            'date_prochain_entretien', 'est_assurance_expiree', 'created_at',
        ]


class VehiculeDetailSerializer(serializers.ModelSerializer):
    est_assurance_expiree = serializers.ReadOnlyField()
    projet_nom = serializers.CharField(source='projet.titre', read_only=True)
    programme_nom = serializers.CharField(source='programme.nom', read_only=True)
    nb_missions = serializers.SerializerMethodField()

    class Meta:
        model = Vehicule
        fields = [
            'id', 'immatriculation', 'type_vehicule', 'marque', 'modele', 'annee',
            'couleur', 'statut', 'programme', 'programme_nom', 'projet', 'projet_nom',
            'kilometrage_actuel', 'date_acquisition', 'valeur_acquisition',
            'date_expiration_assurance', 'date_expiration_vignette',
            'date_prochain_entretien', 'km_prochain_entretien',
            'notes', 'est_assurance_expiree', 'nb_missions',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nb_missions(self, obj):
        return obj.missions.count()


class MissionVehiculeListSerializer(serializers.ModelSerializer):
    vehicule_immat = serializers.CharField(source='vehicule.immatriculation', read_only=True)
    conducteur_detail = UserMinimalSerializer(source='conducteur', read_only=True)
    distance = serializers.ReadOnlyField()

    class Meta:
        model = MissionVehicule
        fields = [
            'id', 'vehicule', 'vehicule_immat', 'conducteur', 'conducteur_detail',
            'projet', 'objet', 'lieu_depart', 'lieu_arrivee',
            'date_depart', 'date_retour_prevue', 'date_retour_reelle',
            'km_depart', 'km_retour', 'statut', 'distance',
            'carburant_litres', 'cout_carburant', 'created_at',
        ]


class MissionVehiculeDetailSerializer(serializers.ModelSerializer):
    conducteur_detail = UserMinimalSerializer(source='conducteur', read_only=True)
    autorise_par_detail = UserMinimalSerializer(source='autorise_par', read_only=True)
    vehicule_detail = VehiculeListSerializer(source='vehicule', read_only=True)
    distance = serializers.ReadOnlyField()

    class Meta:
        model = MissionVehicule
        fields = [
            'id', 'vehicule', 'vehicule_detail',
            'conducteur', 'conducteur_detail',
            'projet', 'activite', 'objet',
            'lieu_depart', 'lieu_arrivee',
            'date_depart', 'date_retour_prevue', 'date_retour_reelle',
            'km_depart', 'km_retour', 'statut', 'distance',
            'carburant_litres', 'cout_carburant',
            'observations', 'autorise_par', 'autorise_par_detail',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EntretienVehiculeSerializer(serializers.ModelSerializer):
    effectue_par_detail = UserMinimalSerializer(source='effectue_par', read_only=True)
    vehicule_immat = serializers.CharField(source='vehicule.immatriculation', read_only=True)

    class Meta:
        model = EntretienVehicule
        fields = [
            'id', 'vehicule', 'vehicule_immat',
            'type_entretien', 'description', 'date_entretien', 'km_entretien',
            'prestataire', 'cout', 'prochaine_echeance_date', 'prochaine_echeance_km',
            'facture', 'effectue_par', 'effectue_par_detail', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ─── M38 : Équipements ────────────────────────────────────────────────────────

class EquipementListSerializer(serializers.ModelSerializer):
    affecte_a_detail = UserMinimalSerializer(source='affecte_a', read_only=True)
    projet_nom = serializers.CharField(source='projet.titre', read_only=True)
    programme_nom = serializers.CharField(source='programme.nom', read_only=True)

    class Meta:
        model = Equipement
        fields = [
            'id', 'code_inventaire', 'nom', 'type_equipement', 'marque', 'modele',
            'statut', 'programme', 'programme_nom', 'projet', 'projet_nom',
            'affecte_a', 'affecte_a_detail', 'lieu',
            'date_acquisition', 'valeur_acquisition', 'date_fin_garantie',
            'created_at',
        ]


class EquipementDetailSerializer(serializers.ModelSerializer):
    affecte_a_detail = UserMinimalSerializer(source='affecte_a', read_only=True)
    projet_nom = serializers.CharField(source='projet.titre', read_only=True)
    programme_nom = serializers.CharField(source='programme.nom', read_only=True)

    class Meta:
        model = Equipement
        fields = [
            'id', 'code_inventaire', 'nom', 'type_equipement', 'marque', 'modele',
            'numero_serie', 'statut',
            'programme', 'programme_nom', 'projet', 'projet_nom',
            'affecte_a', 'affecte_a_detail', 'lieu',
            'date_acquisition', 'valeur_acquisition', 'date_fin_garantie',
            'description', 'photo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'code_inventaire', 'created_at', 'updated_at']


# ─── M38 : Magasins ───────────────────────────────────────────────────────────

class MagasinSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    projet_nom = serializers.CharField(source='projet.titre', read_only=True)
    programme_nom = serializers.CharField(source='programme.nom', read_only=True)
    nb_articles = serializers.SerializerMethodField()

    class Meta:
        model = Magasin
        fields = [
            'id', 'nom', 'code', 'description', 'adresse', 'actif',
            'responsable', 'responsable_detail',
            'programme', 'programme_nom', 'projet', 'projet_nom',
            'nb_articles', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_nb_articles(self, obj):
        return obj.lignes_stock.count()


# ─── M38 : Articles & Stock ───────────────────────────────────────────────────

class ArticleStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleStock
        fields = [
            'id', 'code', 'nom', 'description', 'unite', 'categorie',
            'stock_alerte', 'prix_unitaire', 'actif', 'created_at',
        ]
        read_only_fields = ['id', 'code', 'created_at']


class LigneStockSerializer(serializers.ModelSerializer):
    article_detail = ArticleStockSerializer(source='article', read_only=True)
    magasin_nom = serializers.CharField(source='magasin.nom', read_only=True)
    est_sous_alerte = serializers.ReadOnlyField()

    class Meta:
        model = LigneStock
        fields = [
            'id', 'magasin', 'magasin_nom', 'article', 'article_detail',
            'quantite', 'valeur_totale', 'est_sous_alerte', 'updated_at',
        ]
        read_only_fields = ['id', 'valeur_totale', 'updated_at']


class MouvementStockListSerializer(serializers.ModelSerializer):
    article_nom = serializers.CharField(source='article.nom', read_only=True)
    article_code = serializers.CharField(source='article.code', read_only=True)
    magasin_source_nom = serializers.CharField(source='magasin_source.nom', read_only=True)
    magasin_destination_nom = serializers.CharField(source='magasin_destination.nom', read_only=True)
    effectue_par_detail = UserMinimalSerializer(source='effectue_par', read_only=True)

    class Meta:
        model = MouvementStock
        fields = [
            'id', 'article', 'article_nom', 'article_code',
            'magasin_source', 'magasin_source_nom',
            'magasin_destination', 'magasin_destination_nom',
            'type_mouvement', 'quantite', 'prix_unitaire', 'valeur_totale',
            'reference_document', 'motif', 'projet',
            'effectue_par', 'effectue_par_detail',
            'date_mouvement', 'created_at',
        ]
        read_only_fields = ['id', 'valeur_totale', 'created_at']


class MouvementStockCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MouvementStock
        fields = [
            'article', 'magasin_source', 'magasin_destination',
            'type_mouvement', 'quantite', 'prix_unitaire',
            'reference_document', 'motif', 'projet', 'date_mouvement',
        ]

    def validate(self, data):
        t = data.get('type_mouvement')
        if t == 'entree' and not data.get('magasin_destination'):
            raise serializers.ValidationError({'magasin_destination': 'Obligatoire pour une entrée.'})
        if t in ('sortie', 'perte') and not data.get('magasin_source'):
            raise serializers.ValidationError({'magasin_source': 'Obligatoire pour une sortie/perte.'})
        if t == 'transfert':
            if not data.get('magasin_source'):
                raise serializers.ValidationError({'magasin_source': 'Obligatoire pour un transfert.'})
            if not data.get('magasin_destination'):
                raise serializers.ValidationError({'magasin_destination': 'Obligatoire pour un transfert.'})
        return data


class MouvementBatchItemSerializer(serializers.Serializer):
    """Ligne individuelle pour l'opération batch."""
    article = serializers.IntegerField()
    quantite = serializers.DecimalField(max_digits=12, decimal_places=2)
    prix_unitaire = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    motif = serializers.CharField(required=False, allow_blank=True)


class MouvementBatchSerializer(serializers.Serializer):
    """Sérializer pour l'entrée/sortie en lot (batch)."""
    type_mouvement = serializers.ChoiceField(choices=MouvementStock.TYPE_CHOICES)
    magasin_source = serializers.IntegerField(required=False, allow_null=True)
    magasin_destination = serializers.IntegerField(required=False, allow_null=True)
    reference_document = serializers.CharField(required=False, allow_blank=True)
    projet = serializers.IntegerField(required=False, allow_null=True)
    date_mouvement = serializers.DateField(required=False)
    lignes = MouvementBatchItemSerializer(many=True)

    def validate_lignes(self, value):
        if not value:
            raise serializers.ValidationError('Au moins une ligne est requise.')
        return value
