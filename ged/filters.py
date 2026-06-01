import django_filters
from .models import (
    Document, Categorie, BoiteArchive, AuditDocument,
    ModeleDocument, EntreesBibliotheque, DemandeDestruction,
)


class DocumentFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    reference = django_filters.CharFilter(lookup_expr='icontains')
    type_document = django_filters.ChoiceFilter(choices=Document.TYPE_DOC_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Document.STATUT_CHOICES)
    confidentialite = django_filters.ChoiceFilter(choices=Document.CONFIDENTIALITE_CHOICES)
    langue = django_filters.ChoiceFilter(choices=Document.LANGUE_CHOICES)
    categorie = django_filters.NumberFilter(field_name='categorie__id')
    domaine = django_filters.CharFilter(field_name='categorie__domaine')
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    auteur = django_filters.NumberFilter(field_name='auteur__id')
    mots_cles = django_filters.CharFilter(lookup_expr='icontains')
    ocr_effectue = django_filters.BooleanFilter()
    est_version_courante = django_filters.BooleanFilter()
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    expire_avant = django_filters.DateFilter(field_name='date_expiration', lookup_expr='lte')
    type_fichier = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Document
        fields = ['type_document', 'statut', 'confidentialite', 'langue',
                  'categorie', 'projet', 'programme', 'auteur', 'ocr_effectue']


class BoiteArchiveFilter(django_filters.FilterSet):
    intitule = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=BoiteArchive.STATUT_CHOICES)
    categorie = django_filters.NumberFilter(field_name='categorie__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    service_producteur = django_filters.CharFilter(lookup_expr='icontains')
    annee_debut = django_filters.NumberFilter()
    annee_fin = django_filters.NumberFilter()
    chiffree = django_filters.BooleanFilter()

    class Meta:
        model = BoiteArchive
        fields = ['statut', 'categorie', 'projet', 'programme', 'chiffree']


class AuditFilter(django_filters.FilterSet):
    action = django_filters.ChoiceFilter(choices=AuditDocument.ACTION_CHOICES)
    document = django_filters.NumberFilter(field_name='document__id')
    utilisateur = django_filters.NumberFilter(field_name='utilisateur__id')
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = AuditDocument
        fields = ['action', 'document', 'utilisateur']


class ModeleFilter(django_filters.FilterSet):
    type_modele = django_filters.ChoiceFilter(choices=ModeleDocument.TYPE_CHOICES)
    langue = django_filters.ChoiceFilter(choices=Document.LANGUE_CHOICES)
    actif = django_filters.BooleanFilter()
    titre = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ModeleDocument
        fields = ['type_modele', 'langue', 'actif']


class BibliothequeFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    categorie = django_filters.ChoiceFilter(choices=EntreesBibliotheque.CATEGORIE_CHOICES)
    langue = django_filters.ChoiceFilter(choices=Document.LANGUE_CHOICES)
    est_public = django_filters.BooleanFilter()
    mots_cles = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = EntreesBibliotheque
        fields = ['categorie', 'langue', 'est_public']
