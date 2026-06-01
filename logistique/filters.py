import django_filters
from django.utils import timezone
from .models import (
    Vehicule, MissionVehicule, EntretienVehicule,
    Equipement, Magasin, ArticleStock, LigneStock, MouvementStock,
)


class VehiculeFilter(django_filters.FilterSet):
    immatriculation = django_filters.CharFilter(lookup_expr='icontains')
    marque = django_filters.CharFilter(lookup_expr='icontains')
    modele = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=Vehicule.STATUT_CHOICES)
    type_vehicule = django_filters.ChoiceFilter(choices=Vehicule.TYPE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    annee_min = django_filters.NumberFilter(field_name='annee', lookup_expr='gte')
    annee_max = django_filters.NumberFilter(field_name='annee', lookup_expr='lte')
    assurance_expire_avant = django_filters.DateFilter(
        field_name='date_expiration_assurance', lookup_expr='lte'
    )
    vignette_expire_avant = django_filters.DateFilter(
        field_name='date_expiration_vignette', lookup_expr='lte'
    )
    entretien_avant = django_filters.DateFilter(
        field_name='date_prochain_entretien', lookup_expr='lte'
    )

    class Meta:
        model = Vehicule
        fields = ['statut', 'type_vehicule', 'projet', 'programme']


class MissionVehiculeFilter(django_filters.FilterSet):
    statut = django_filters.ChoiceFilter(choices=MissionVehicule.STATUT_CHOICES)
    vehicule = django_filters.NumberFilter(field_name='vehicule__id')
    conducteur = django_filters.NumberFilter(field_name='conducteur__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    objet = django_filters.CharFilter(lookup_expr='icontains')
    lieu_depart = django_filters.CharFilter(lookup_expr='icontains')
    lieu_arrivee = django_filters.CharFilter(lookup_expr='icontains')
    date_depart_apres = django_filters.DateTimeFilter(
        field_name='date_depart', lookup_expr='gte'
    )
    date_depart_avant = django_filters.DateTimeFilter(
        field_name='date_depart', lookup_expr='lte'
    )
    date_retour_apres = django_filters.DateTimeFilter(
        field_name='date_retour_reelle', lookup_expr='gte'
    )
    date_retour_avant = django_filters.DateTimeFilter(
        field_name='date_retour_reelle', lookup_expr='lte'
    )

    class Meta:
        model = MissionVehicule
        fields = ['statut', 'vehicule', 'conducteur', 'projet']


class EntretienVehiculeFilter(django_filters.FilterSet):
    type_entretien = django_filters.ChoiceFilter(choices=EntretienVehicule.TYPE_CHOICES)
    vehicule = django_filters.NumberFilter(field_name='vehicule__id')
    prestataire = django_filters.CharFilter(lookup_expr='icontains')
    date_apres = django_filters.DateFilter(field_name='date_entretien', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_entretien', lookup_expr='lte')
    cout_min = django_filters.NumberFilter(field_name='cout', lookup_expr='gte')
    cout_max = django_filters.NumberFilter(field_name='cout', lookup_expr='lte')
    effectue_par = django_filters.NumberFilter(field_name='effectue_par__id')

    class Meta:
        model = EntretienVehicule
        fields = ['type_entretien', 'vehicule', 'effectue_par']


class EquipementFilter(django_filters.FilterSet):
    code_inventaire = django_filters.CharFilter(lookup_expr='icontains')
    nom = django_filters.CharFilter(lookup_expr='icontains')
    type_equipement = django_filters.ChoiceFilter(choices=Equipement.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Equipement.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    affecte_a = django_filters.NumberFilter(field_name='affecte_a__id')
    lieu = django_filters.CharFilter(lookup_expr='icontains')
    marque = django_filters.CharFilter(lookup_expr='icontains')
    date_acquisition_apres = django_filters.DateFilter(
        field_name='date_acquisition', lookup_expr='gte'
    )
    date_acquisition_avant = django_filters.DateFilter(
        field_name='date_acquisition', lookup_expr='lte'
    )
    garantie_expire_avant = django_filters.DateFilter(
        field_name='date_fin_garantie', lookup_expr='lte'
    )

    class Meta:
        model = Equipement
        fields = ['type_equipement', 'statut', 'projet', 'programme', 'affecte_a']


class MagasinFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    actif = django_filters.BooleanFilter()

    class Meta:
        model = Magasin
        fields = ['projet', 'programme', 'responsable', 'actif']


class ArticleStockFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    nom = django_filters.CharFilter(lookup_expr='icontains')
    categorie = django_filters.CharFilter(lookup_expr='icontains')
    unite = django_filters.ChoiceFilter(choices=ArticleStock.UNITE_CHOICES)
    actif = django_filters.BooleanFilter()
    prix_min = django_filters.NumberFilter(field_name='prix_unitaire', lookup_expr='gte')
    prix_max = django_filters.NumberFilter(field_name='prix_unitaire', lookup_expr='lte')

    class Meta:
        model = ArticleStock
        fields = ['unite', 'categorie', 'actif']


class LigneStockFilter(django_filters.FilterSet):
    magasin = django_filters.NumberFilter(field_name='magasin__id')
    article = django_filters.NumberFilter(field_name='article__id')
    categorie = django_filters.CharFilter(field_name='article__categorie', lookup_expr='icontains')
    quantite_min = django_filters.NumberFilter(field_name='quantite', lookup_expr='gte')
    quantite_max = django_filters.NumberFilter(field_name='quantite', lookup_expr='lte')
    sous_alerte = django_filters.BooleanFilter(method='filter_sous_alerte')

    class Meta:
        model = LigneStock
        fields = ['magasin', 'article']

    def filter_sous_alerte(self, queryset, name, value):
        from django.db.models import F
        if value:
            return queryset.filter(quantite__lte=F('article__stock_alerte'))
        return queryset.filter(quantite__gt=F('article__stock_alerte'))


class MouvementStockFilter(django_filters.FilterSet):
    type_mouvement = django_filters.ChoiceFilter(choices=MouvementStock.TYPE_CHOICES)
    article = django_filters.NumberFilter(field_name='article__id')
    magasin_source = django_filters.NumberFilter(field_name='magasin_source__id')
    magasin_destination = django_filters.NumberFilter(field_name='magasin_destination__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    effectue_par = django_filters.NumberFilter(field_name='effectue_par__id')
    reference_document = django_filters.CharFilter(lookup_expr='icontains')
    date_apres = django_filters.DateFilter(field_name='date_mouvement', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_mouvement', lookup_expr='lte')
    mois = django_filters.NumberFilter(field_name='date_mouvement', lookup_expr='month')
    annee = django_filters.NumberFilter(field_name='date_mouvement', lookup_expr='year')
    valeur_min = django_filters.NumberFilter(field_name='valeur_totale', lookup_expr='gte')
    valeur_max = django_filters.NumberFilter(field_name='valeur_totale', lookup_expr='lte')

    class Meta:
        model = MouvementStock
        fields = ['type_mouvement', 'article', 'magasin_source', 'magasin_destination',
                  'projet', 'effectue_par']
