import django_filters
from .models import (
    PlanPassationMarche, DemandeAchat, AppelOffre,
    SoumissionnaireOffre, ContratMarche, AvenantContrat,
)


class PlanPassationMarcheFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    annee = django_filters.NumberFilter()
    annee_min = django_filters.NumberFilter(field_name='annee', lookup_expr='gte')
    annee_max = django_filters.NumberFilter(field_name='annee', lookup_expr='lte')
    statut = django_filters.ChoiceFilter(choices=PlanPassationMarche.STATUT_CHOICES)
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    cree_par = django_filters.NumberFilter(field_name='cree_par__id')
    valide_par = django_filters.NumberFilter(field_name='valide_par__id')
    date_validation_apres = django_filters.DateFilter(field_name='date_validation', lookup_expr='gte')
    date_validation_avant = django_filters.DateFilter(field_name='date_validation', lookup_expr='lte')
    budget_min = django_filters.NumberFilter(field_name='budget_total_prevu', lookup_expr='gte')
    budget_max = django_filters.NumberFilter(field_name='budget_total_prevu', lookup_expr='lte')

    class Meta:
        model = PlanPassationMarche
        fields = ['annee', 'statut', 'programme', 'projet', 'cree_par']


class DemandeAchatFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    reference = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=DemandeAchat.STATUT_CHOICES)
    priorite = django_filters.ChoiceFilter(choices=DemandeAchat.PRIORITE_CHOICES)
    type_marche = django_filters.ChoiceFilter(choices=DemandeAchat.TYPE_MARCHE_CHOICES)
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    plan_passation = django_filters.NumberFilter(field_name='plan_passation__id')
    demandeur = django_filters.NumberFilter(field_name='demandeur__id')
    valideur = django_filters.NumberFilter(field_name='valideur__id')
    date_besoin_apres = django_filters.DateFilter(field_name='date_besoin', lookup_expr='gte')
    date_besoin_avant = django_filters.DateFilter(field_name='date_besoin', lookup_expr='lte')
    budget_min = django_filters.NumberFilter(field_name='budget_estime', lookup_expr='gte')
    budget_max = django_filters.NumberFilter(field_name='budget_estime', lookup_expr='lte')
    created_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_avant = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = DemandeAchat
        fields = ['statut', 'priorite', 'type_marche', 'programme', 'projet',
                  'plan_passation', 'demandeur']


class AppelOffreFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    reference = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=AppelOffre.STATUT_CHOICES)
    type_marche = django_filters.ChoiceFilter(choices=AppelOffre.TYPE_CHOICES)
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    plan_passation = django_filters.NumberFilter(field_name='plan_passation__id')
    responsable = django_filters.NumberFilter(field_name='responsable__id')
    date_publication_apres = django_filters.DateFilter(field_name='date_publication', lookup_expr='gte')
    date_publication_avant = django_filters.DateFilter(field_name='date_publication', lookup_expr='lte')
    date_limite_apres = django_filters.DateFilter(field_name='date_limite_soumission', lookup_expr='gte')
    date_limite_avant = django_filters.DateFilter(field_name='date_limite_soumission', lookup_expr='lte')
    budget_min = django_filters.NumberFilter(field_name='budget_estime', lookup_expr='gte')
    budget_max = django_filters.NumberFilter(field_name='budget_estime', lookup_expr='lte')

    class Meta:
        model = AppelOffre
        fields = ['statut', 'type_marche', 'programme', 'projet', 'plan_passation', 'responsable']


class SoumissionnaireOffreFilter(django_filters.FilterSet):
    nom_entreprise = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=SoumissionnaireOffre.STATUT_CHOICES)
    appel_offre = django_filters.NumberFilter(field_name='appel_offre__id')
    pays = django_filters.CharFilter(lookup_expr='icontains')
    montant_min = django_filters.NumberFilter(field_name='montant_offre', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant_offre', lookup_expr='lte')
    note_globale_min = django_filters.NumberFilter(field_name='note_globale', lookup_expr='gte')
    note_globale_max = django_filters.NumberFilter(field_name='note_globale', lookup_expr='lte')
    date_soumission_apres = django_filters.DateFilter(field_name='date_soumission', lookup_expr='date__gte')
    date_soumission_avant = django_filters.DateFilter(field_name='date_soumission', lookup_expr='date__lte')

    class Meta:
        model = SoumissionnaireOffre
        fields = ['statut', 'appel_offre', 'pays']


class ContratMarcheFilter(django_filters.FilterSet):
    titre = django_filters.CharFilter(lookup_expr='icontains')
    reference = django_filters.CharFilter(lookup_expr='icontains')
    statut = django_filters.ChoiceFilter(choices=ContratMarche.STATUT_CHOICES)
    type_contrat = django_filters.ChoiceFilter(choices=ContratMarche.TYPE_CHOICES)
    programme = django_filters.NumberFilter(field_name='programme__id')
    projet = django_filters.NumberFilter(field_name='projet__id')
    gestionnaire = django_filters.NumberFilter(field_name='gestionnaire__id')
    prestataire_nom = django_filters.CharFilter(lookup_expr='icontains')
    devise = django_filters.CharFilter(lookup_expr='iexact')
    montant_min = django_filters.NumberFilter(field_name='montant_ttc', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant_ttc', lookup_expr='lte')
    date_signature_apres = django_filters.DateFilter(field_name='date_signature', lookup_expr='gte')
    date_signature_avant = django_filters.DateFilter(field_name='date_signature', lookup_expr='lte')
    date_fin_apres = django_filters.DateFilter(field_name='date_fin_prevue', lookup_expr='gte')
    date_fin_avant = django_filters.DateFilter(field_name='date_fin_prevue', lookup_expr='lte')
    en_retard = django_filters.BooleanFilter(method='filter_en_retard')

    class Meta:
        model = ContratMarche
        fields = ['statut', 'type_contrat', 'programme', 'projet', 'gestionnaire', 'devise']

    def filter_en_retard(self, queryset, name, value):
        from django.utils import timezone
        today = timezone.now().date()
        if value:
            return queryset.filter(
                date_fin_prevue__lt=today,
                statut__in=['signe', 'en_cours']
            )
        return queryset.exclude(
            date_fin_prevue__lt=today,
            statut__in=['signe', 'en_cours']
        )


class AvenantContratFilter(django_filters.FilterSet):
    contrat = django_filters.NumberFilter(field_name='contrat__id')
    motif = django_filters.ChoiceFilter(choices=AvenantContrat.MOTIF_CHOICES)
    statut = django_filters.ChoiceFilter(choices=[
        ('en_preparation', 'En préparation'), ('signe', 'Signé')
    ])
    numero_avenant = django_filters.NumberFilter()
    date_signature_apres = django_filters.DateFilter(field_name='date_signature', lookup_expr='gte')
    date_signature_avant = django_filters.DateFilter(field_name='date_signature', lookup_expr='lte')

    class Meta:
        model = AvenantContrat
        fields = ['contrat', 'motif', 'statut']
