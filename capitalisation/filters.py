import django_filters
from .models import FicheCapitalisation, EntreeBibliotheque, CommentaireFiche, CentreConnaissance


class FicheCapitalisationFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    reference = django_filters.CharFilter(lookup_expr='icontains')
    type_fiche = django_filters.ChoiceFilter(choices=FicheCapitalisation.TYPE_CHOICES)
    domaine = django_filters.ChoiceFilter(choices=FicheCapitalisation.DOMAINE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=FicheCapitalisation.STATUT_CHOICES)
    niveau_replicabilite = django_filters.ChoiceFilter(
        choices=[('faible', 'Faible'), ('moyen', 'Moyen'), ('eleve', 'Élevé')]
    )
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    auteur = django_filters.NumberFilter(field_name='auteur__id')
    valide_par = django_filters.NumberFilter(field_name='valide_par__id')
    genere_par_ia = django_filters.BooleanFilter()
    mots_cles = django_filters.CharFilter(lookup_expr='icontains')
    zone_geographique = django_filters.CharFilter(lookup_expr='icontains')
    date_creation_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_creation_avant = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    date_validation_apres = django_filters.DateFilter(field_name='date_validation', lookup_expr='date__gte')
    date_validation_avant = django_filters.DateFilter(field_name='date_validation', lookup_expr='date__lte')

    class Meta:
        model = FicheCapitalisation
        fields = ['type_fiche', 'domaine', 'statut', 'niveau_replicabilite',
                  'programme', 'projet', 'auteur', 'genere_par_ia']


class EntreeBibliothequeFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    categorie = django_filters.ChoiceFilter(choices=EntreeBibliotheque.CATEGORIE_CHOICES)
    domaine = django_filters.ChoiceFilter(choices=FicheCapitalisation.DOMAINE_CHOICES)
    sous_categorie = django_filters.CharFilter(lookup_expr='icontains')
    auteur = django_filters.CharFilter(field_name='auteur', lookup_expr='icontains')
    organisation = django_filters.CharFilter(lookup_expr='icontains')
    langue = django_filters.CharFilter(lookup_expr='iexact')
    est_public = django_filters.BooleanFilter()
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    ajoute_par = django_filters.NumberFilter(field_name='ajoute_par__id')
    annee_min = django_filters.NumberFilter(field_name='annee_publication', lookup_expr='gte')
    annee_max = django_filters.NumberFilter(field_name='annee_publication', lookup_expr='lte')
    mots_cles = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = EntreeBibliotheque
        fields = ['categorie', 'domaine', 'langue', 'est_public', 'programme', 'projet']


class CommentaireFicheFilter(django_filters.FilterSet):
    fiche = django_filters.NumberFilter(field_name='fiche__id')
    auteur = django_filters.NumberFilter(field_name='auteur__id')
    en_reponse_a = django_filters.NumberFilter(field_name='en_reponse_a__id')
    sans_reponse = django_filters.BooleanFilter(field_name='en_reponse_a', lookup_expr='isnull')

    class Meta:
        model = CommentaireFiche
        fields = ['fiche', 'auteur']


class CentreConnaissanceFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    domaine = django_filters.ChoiceFilter(choices=FicheCapitalisation.DOMAINE_CHOICES)
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    actif = django_filters.BooleanFilter()

    class Meta:
        model = CentreConnaissance
        fields = ['domaine', 'actif', 'responsable']
