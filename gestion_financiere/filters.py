import django_filters
from django.utils import timezone
from .models import (
    Budget, LigneBudgetaire, Depense, Avance, Engagement,
    Fournisseur, Convention, TrancheFinancement, RapportBailleur,
    PlanTresorerie, RapportFinancier,
)


class BudgetFilter(django_filters.FilterSet):
    type_budget = django_filters.ChoiceFilter(choices=Budget.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Budget.STATUT_CHOICES)
    exercice = django_filters.NumberFilter()
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    montant_min = django_filters.NumberFilter(field_name='montant_initial', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant_initial', lookup_expr='lte')
    devise = django_filters.ChoiceFilter(choices=[
        ('XOF', 'XOF'), ('EUR', 'EUR'), ('USD', 'USD'), ('GBP', 'GBP'), ('CHF', 'CHF')
    ])

    class Meta:
        model = Budget
        fields = ['type_budget', 'statut', 'exercice', 'projet', 'programme', 'devise']


class LigneBudgetaireFilter(django_filters.FilterSet):
    budget = django_filters.NumberFilter(field_name='budget__id')
    categorie = django_filters.ChoiceFilter(choices=LigneBudgetaire.CATEGORIE_CHOICES)
    code = django_filters.CharFilter(lookup_expr='icontains')
    depassee = django_filters.BooleanFilter(method='filter_depassee')

    class Meta:
        model = LigneBudgetaire
        fields = ['budget', 'categorie']

    def filter_depassee(self, queryset, name, value):
        if value:
            return queryset.filter(montant_engage__gt=django_filters.utils.handle_timezone(None))
        return queryset


class DepenseFilter(django_filters.FilterSet):
    type_depense = django_filters.ChoiceFilter(choices=Depense.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Depense.STATUT_CHOICES)
    mode_paiement = django_filters.ChoiceFilter(choices=Depense.MODE_PAIEMENT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    activite = django_filters.NumberFilter(field_name='activite__id')
    fournisseur = django_filters.NumberFilter(field_name='fournisseur__id')
    ligne_budgetaire = django_filters.NumberFilter(field_name='ligne_budgetaire__id')
    date_apres = django_filters.DateFilter(field_name='date_depense', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_depense', lookup_expr='lte')
    montant_min = django_filters.NumberFilter(field_name='montant', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant', lookup_expr='lte')
    mois = django_filters.NumberFilter(field_name='date_depense', lookup_expr='month')
    annee = django_filters.NumberFilter(field_name='date_depense', lookup_expr='year')
    saisi_par = django_filters.NumberFilter(field_name='saisi_par__id')

    class Meta:
        model = Depense
        fields = ['type_depense', 'statut', 'mode_paiement', 'projet', 'fournisseur']


class AvanceFilter(django_filters.FilterSet):
    type_avance = django_filters.ChoiceFilter(choices=Avance.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Avance.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    beneficiaire = django_filters.NumberFilter(field_name='beneficiaire__id')
    date_apres = django_filters.DateFilter(field_name='date_accord', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_accord', lookup_expr='lte')
    non_justifiees = django_filters.BooleanFilter(method='filter_non_justifiees')

    class Meta:
        model = Avance
        fields = ['type_avance', 'statut', 'projet', 'beneficiaire']

    def filter_non_justifiees(self, queryset, name, value):
        if value:
            return queryset.filter(
                statut__in=['accordee', 'partiellement_justifiee', 'non_justifiee']
            )
        return queryset


class EngagementFilter(django_filters.FilterSet):
    type_engagement = django_filters.ChoiceFilter(choices=Engagement.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Engagement.STATUT_CHOICES)
    fournisseur = django_filters.NumberFilter(field_name='fournisseur__id')
    ligne_budgetaire = django_filters.NumberFilter(field_name='ligne_budgetaire__id')
    date_apres = django_filters.DateFilter(field_name='date_engagement', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='date_engagement', lookup_expr='lte')
    montant_min = django_filters.NumberFilter(field_name='montant', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant', lookup_expr='lte')

    class Meta:
        model = Engagement
        fields = ['type_engagement', 'statut', 'fournisseur']


class FournisseurFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    type_fournisseur = django_filters.ChoiceFilter(choices=Fournisseur.TYPE_CHOICES)
    pays = django_filters.CharFilter(lookup_expr='icontains')
    actif = django_filters.BooleanFilter()

    class Meta:
        model = Fournisseur
        fields = ['type_fournisseur', 'actif']


class ConventionFilter(django_filters.FilterSet):
    type_convention = django_filters.ChoiceFilter(choices=Convention.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Convention.STATUT_CHOICES)
    bailleur = django_filters.NumberFilter(field_name='bailleur__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    date_debut_apres = django_filters.DateFilter(field_name='date_debut', lookup_expr='gte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin', lookup_expr='lte')
    montant_min = django_filters.NumberFilter(field_name='montant_total', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant_total', lookup_expr='lte')

    class Meta:
        model = Convention
        fields = ['type_convention', 'statut', 'bailleur', 'projet', 'programme']


class RapportBailleurFilter(django_filters.FilterSet):
    type_rapport = django_filters.ChoiceFilter(choices=RapportBailleur.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=RapportBailleur.STATUT_CHOICES)
    convention = django_filters.NumberFilter(field_name='convention__id')
    date_apres = django_filters.DateFilter(field_name='periode_debut', lookup_expr='gte')
    date_avant = django_filters.DateFilter(field_name='periode_fin', lookup_expr='lte')

    class Meta:
        model = RapportBailleur
        fields = ['type_rapport', 'statut', 'convention']


class RapportFinancierFilter(django_filters.FilterSet):
    type_rapport = django_filters.ChoiceFilter(choices=RapportFinancier.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=RapportFinancier.STATUT_CHOICES)
    periode = django_filters.ChoiceFilter(choices=RapportFinancier.PERIODE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    annee = django_filters.NumberFilter(field_name='date_rapport', lookup_expr='year')

    class Meta:
        model = RapportFinancier
        fields = ['type_rapport', 'statut', 'periode', 'projet', 'programme']
