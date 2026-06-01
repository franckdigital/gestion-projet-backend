import django_filters
from .models import (
    EmployeProjet, AffectationRH, FeuilleTemps,
    LigneFeuilleTemps, EvaluationPerformance, BesoinFormation,
)


class EmployeProjetFilter(django_filters.FilterSet):
    type_personnel = django_filters.ChoiceFilter(choices=EmployeProjet.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=EmployeProjet.STATUT_CHOICES)
    niveau_expertise = django_filters.ChoiceFilter(choices=EmployeProjet.NIVEAU_CHOICES)
    nom = django_filters.CharFilter(lookup_expr='icontains')
    prenom = django_filters.CharFilter(lookup_expr='icontains')
    specialite = django_filters.CharFilter(lookup_expr='icontains')
    poste = django_filters.CharFilter(lookup_expr='icontains')
    devise = django_filters.CharFilter()
    date_embauche_apres = django_filters.DateFilter(field_name='date_embauche', lookup_expr='gte')
    date_embauche_avant = django_filters.DateFilter(field_name='date_embauche', lookup_expr='lte')
    date_fin_contrat_avant = django_filters.DateFilter(field_name='date_fin_contrat', lookup_expr='lte')
    taux_journalier_min = django_filters.NumberFilter(field_name='taux_journalier', lookup_expr='gte')
    taux_journalier_max = django_filters.NumberFilter(field_name='taux_journalier', lookup_expr='lte')

    class Meta:
        model = EmployeProjet
        fields = ['type_personnel', 'statut', 'niveau_expertise', 'devise']


class AffectationRHFilter(django_filters.FilterSet):
    statut = django_filters.ChoiceFilter(choices=AffectationRH.STATUT_CHOICES)
    employe = django_filters.NumberFilter(field_name='employe__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    activite = django_filters.NumberFilter(field_name='activite__id')
    date_debut_apres = django_filters.DateFilter(field_name='date_debut', lookup_expr='gte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin', lookup_expr='lte')
    taux_min = django_filters.NumberFilter(field_name='taux_affectation', lookup_expr='gte')
    taux_max = django_filters.NumberFilter(field_name='taux_affectation', lookup_expr='lte')
    actives = django_filters.BooleanFilter(method='filter_actives')

    class Meta:
        model = AffectationRH
        fields = ['statut', 'employe', 'projet', 'programme', 'activite']

    def filter_actives(self, queryset, name, value):
        if value:
            return queryset.filter(statut='active')
        return queryset


class FeuilleTempsFilter(django_filters.FilterSet):
    statut = django_filters.ChoiceFilter(choices=FeuilleTemps.STATUT_CHOICES)
    employe = django_filters.NumberFilter(field_name='employe__id')
    mois = django_filters.NumberFilter()
    annee = django_filters.NumberFilter()
    valideur = django_filters.NumberFilter(field_name='valideur__id')
    en_attente = django_filters.BooleanFilter(method='filter_en_attente')

    class Meta:
        model = FeuilleTemps
        fields = ['statut', 'employe', 'mois', 'annee']

    def filter_en_attente(self, queryset, name, value):
        if value:
            return queryset.filter(statut='soumise')
        return queryset


class LigneFeuilleTempsFilter(django_filters.FilterSet):
    feuille = django_filters.NumberFilter(field_name='feuille__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    activite = django_filters.NumberFilter(field_name='activite__id')
    date_apres = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    est_conge = django_filters.BooleanFilter()
    est_jour_ferie = django_filters.BooleanFilter()

    class Meta:
        model = LigneFeuilleTemps
        fields = ['feuille', 'projet', 'activite', 'est_conge', 'est_jour_ferie']


class EvaluationPerformanceFilter(django_filters.FilterSet):
    statut = django_filters.ChoiceFilter(choices=EvaluationPerformance.STATUT_CHOICES)
    periode = django_filters.ChoiceFilter(choices=EvaluationPerformance.PERIODE_CHOICES)
    employe = django_filters.NumberFilter(field_name='employe__id')
    evaluateur = django_filters.NumberFilter(field_name='evaluateur__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    annee = django_filters.NumberFilter()
    trimestre = django_filters.NumberFilter()
    note_min = django_filters.NumberFilter(field_name='note_globale', lookup_expr='gte')
    note_max = django_filters.NumberFilter(field_name='note_globale', lookup_expr='lte')

    class Meta:
        model = EvaluationPerformance
        fields = ['statut', 'periode', 'employe', 'evaluateur', 'projet', 'annee']


class BesoinFormationFilter(django_filters.FilterSet):
    statut = django_filters.ChoiceFilter(choices=BesoinFormation.STATUT_CHOICES)
    priorite = django_filters.ChoiceFilter(choices=BesoinFormation.PRIORITE_CHOICES)
    employe = django_filters.NumberFilter(field_name='employe__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    domaine = django_filters.CharFilter(lookup_expr='icontains')
    intitule = django_filters.CharFilter(lookup_expr='icontains')
    date_souhaitee_apres = django_filters.DateFilter(field_name='date_souhaitee', lookup_expr='gte')
    date_souhaitee_avant = django_filters.DateFilter(field_name='date_souhaitee', lookup_expr='lte')
    cout_min = django_filters.NumberFilter(field_name='cout_estime', lookup_expr='gte')
    cout_max = django_filters.NumberFilter(field_name='cout_estime', lookup_expr='lte')
    prioritaires = django_filters.BooleanFilter(method='filter_prioritaires')

    class Meta:
        model = BesoinFormation
        fields = ['statut', 'priorite', 'employe', 'projet']

    def filter_prioritaires(self, queryset, name, value):
        if value:
            return queryset.filter(priorite__in=['haute', 'critique'])
        return queryset
