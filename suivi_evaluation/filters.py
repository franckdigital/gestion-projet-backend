import django_filters
from django.utils import timezone
from .models import (
    Indicateur, CollecteIndicateur,
    FormulaireDynamique, SoumissionFormulaire,
    Enquete, ReponseEnquete,
    Evaluation, LeconApprise, RapportSE, PointSIG,
    RegistreRisque,
)


class IndicateurFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    intitule = django_filters.CharFilter(lookup_expr='icontains')
    type_indicateur = django_filters.ChoiceFilter(choices=Indicateur.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Indicateur.STATUT_CHOICES)
    frequence_collecte = django_filters.ChoiceFilter(choices=Indicateur.FREQUENCE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    niveau_resultat = django_filters.NumberFilter(field_name='niveau_resultat__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    actif = django_filters.BooleanFilter()
    taux_min = django_filters.NumberFilter(method='filter_taux_min')
    taux_max = django_filters.NumberFilter(method='filter_taux_max')
    sans_collecte_recente = django_filters.BooleanFilter(method='filter_sans_collecte_recente')

    class Meta:
        model = Indicateur
        fields = ['type_indicateur', 'statut', 'frequence_collecte', 'projet', 'programme', 'actif']

    def filter_taux_min(self, queryset, name, value):
        ids = [i.id for i in queryset if i.taux_realisation >= float(value)]
        return queryset.filter(id__in=ids)

    def filter_taux_max(self, queryset, name, value):
        ids = [i.id for i in queryset if i.taux_realisation <= float(value)]
        return queryset.filter(id__in=ids)

    def filter_sans_collecte_recente(self, queryset, name, value):
        if value:
            from datetime import timedelta
            seuil = timezone.now().date() - timedelta(days=90)
            ids_avec_collecte = CollecteIndicateur.objects.filter(
                date_collecte__gte=seuil, statut='valide'
            ).values_list('indicateur_id', flat=True)
            return queryset.exclude(id__in=ids_avec_collecte)
        return queryset


class CollecteIndicateurFilter(django_filters.FilterSet):
    indicateur = django_filters.NumberFilter(field_name='indicateur__id')
    projet = django_filters.NumberFilter(field_name='indicateur__projet__id')
    statut = django_filters.ChoiceFilter(choices=CollecteIndicateur.STATUT_CHOICES)
    collecteur = django_filters.NumberFilter(field_name='collecteur__id')
    date_apres = django_filters.DateFilter(field_name='date_collecte', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_collecte', lookup_expr='lte')
    annee = django_filters.NumberFilter(field_name='date_collecte', lookup_expr='year')
    trimestre = django_filters.NumberFilter(field_name='periode__trimestre')

    class Meta:
        model = CollecteIndicateur
        fields = ['indicateur', 'statut', 'collecteur']


class FormulaireFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=FormulaireDynamique.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')

    class Meta:
        model = FormulaireDynamique
        fields = ['statut', 'projet', 'programme']


class SoumissionFilter(django_filters.FilterSet):
    formulaire = django_filters.NumberFilter(field_name='formulaire__id')
    statut = django_filters.ChoiceFilter(choices=SoumissionFormulaire.STATUT_CHOICES)
    soumetteur = django_filters.NumberFilter(field_name='soumetteur__id')
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    hors_ligne = django_filters.BooleanFilter(field_name='soumis_hors_ligne')

    class Meta:
        model = SoumissionFormulaire
        fields = ['formulaire', 'statut', 'soumetteur']


class EnqueteFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    type_enquete = django_filters.ChoiceFilter(choices=Enquete.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Enquete.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    date_debut_apres = django_filters.DateFilter(field_name='date_debut', lookup_expr='gte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin', lookup_expr='lte')

    class Meta:
        model = Enquete
        fields = ['type_enquete', 'statut', 'projet', 'programme', 'responsable']


class ReponseEnqueteFilter(django_filters.FilterSet):
    enquete = django_filters.NumberFilter(field_name='enquete__id')
    statut = django_filters.ChoiceFilter(choices=ReponseEnquete.STATUT_CHOICES)
    canal = django_filters.ChoiceFilter(choices=Enquete.CANAL_CHOICES)
    repondant = django_filters.NumberFilter(field_name='repondant__id')
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    hors_ligne = django_filters.BooleanFilter(field_name='soumis_hors_ligne')

    class Meta:
        model = ReponseEnquete
        fields = ['enquete', 'statut', 'canal', 'repondant']


class EvaluationFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    type_evaluation = django_filters.ChoiceFilter(choices=Evaluation.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Evaluation.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    date_apres = django_filters.DateFilter(field_name='date_debut', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_fin', lookup_expr='lte')

    class Meta:
        model = Evaluation
        fields = ['type_evaluation', 'statut', 'projet', 'programme', 'responsable']


class LeconApprisFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    type_lecon = django_filters.ChoiceFilter(choices=LeconApprise.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=LeconApprise.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    evaluation = django_filters.NumberFilter(field_name='evaluation__id')
    domaine = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = LeconApprise
        fields = ['type_lecon', 'statut', 'projet', 'programme', 'evaluation']


class RapportSEFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    type_rapport = django_filters.ChoiceFilter(choices=RapportSE.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=RapportSE.STATUT_CHOICES)
    periode = django_filters.ChoiceFilter(choices=RapportSE.PERIODE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    redacteur = django_filters.NumberFilter(field_name='redacteur__id')
    date_apres = django_filters.DateFilter(field_name='date_rapport', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_rapport', lookup_expr='lte')
    annee = django_filters.NumberFilter(field_name='date_rapport', lookup_expr='year')

    class Meta:
        model = RapportSE
        fields = ['type_rapport', 'statut', 'periode', 'projet', 'programme', 'redacteur']


class PointSIGFilter(django_filters.FilterSet):
    type_point = django_filters.ChoiceFilter(choices=PointSIG.TYPE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    indicateur = django_filters.NumberFilter(field_name='indicateur__id')
    actif = django_filters.BooleanFilter()
    lat_min = django_filters.NumberFilter(field_name='latitude', lookup_expr='gte')
    lat_max = django_filters.NumberFilter(field_name='latitude', lookup_expr='lte')
    lon_min = django_filters.NumberFilter(field_name='longitude', lookup_expr='gte')
    lon_max = django_filters.NumberFilter(field_name='longitude', lookup_expr='lte')

    class Meta:
        model = PointSIG
        fields = ['type_point', 'projet', 'programme', 'indicateur', 'actif']


class RegistreRisqueFilter(django_filters.FilterSet):
    intitule = django_filters.CharFilter(lookup_expr='icontains')
    categorie = django_filters.ChoiceFilter(choices=RegistreRisque.CATEGORIE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=RegistreRisque.STATUT_CHOICES)
    tendance = django_filters.ChoiceFilter(choices=RegistreRisque.TENDANCE_CHOICES)
    niveau_risque = django_filters.CharFilter()
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    score_min = django_filters.NumberFilter(field_name='score_risque', lookup_expr='gte')
    score_max = django_filters.NumberFilter(field_name='score_risque', lookup_expr='lte')
    critiques_seulement = django_filters.BooleanFilter(method='filter_critiques')

    class Meta:
        model = RegistreRisque
        fields = ['categorie', 'statut', 'tendance', 'projet', 'programme', 'responsable']

    def filter_critiques(self, queryset, name, value):
        if value:
            return queryset.filter(niveau_risque='critique')
        return queryset
