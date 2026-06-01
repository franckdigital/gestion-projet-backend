import django_filters
from .models import ConversationIA, GenerationDocument, AnalyseIAPredictive, AlerteIA, JournalIA


class ConversationIAFilter(django_filters.FilterSet):
    contexte = django_filters.ChoiceFilter(choices=ConversationIA.CONTEXTE_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    archivee = django_filters.BooleanFilter()

    class Meta:
        model = ConversationIA
        fields = ['contexte', 'projet', 'programme', 'archivee']


class GenerationDocumentFilter(django_filters.FilterSet):
    type_document = django_filters.ChoiceFilter(choices=GenerationDocument.TYPE_CHOICES)
    mode = django_filters.ChoiceFilter(choices=GenerationDocument.MODE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=GenerationDocument.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    demande_par = django_filters.NumberFilter(field_name='demande_par__id')
    langue = django_filters.CharFilter()
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')

    class Meta:
        model = GenerationDocument
        fields = ['type_document', 'mode', 'statut', 'projet', 'programme', 'langue']


class AnalyseIAPredictiveFilter(django_filters.FilterSet):
    type_analyse = django_filters.ChoiceFilter(choices=AnalyseIAPredictive.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=AnalyseIAPredictive.STATUT_CHOICES)
    projet = django_filters.NumberFilter(field_name='projet__id')
    programme = django_filters.NumberFilter(field_name='programme__id')
    demande_par = django_filters.NumberFilter(field_name='demande_par__id')

    class Meta:
        model = AnalyseIAPredictive
        fields = ['type_analyse', 'statut', 'projet', 'programme', 'demande_par']


class AlerteIAFilter(django_filters.FilterSet):
    niveau = django_filters.ChoiceFilter(choices=AlerteIA.NIVEAU_CHOICES)
    type_alerte = django_filters.ChoiceFilter(choices=AlerteIA.TYPE_CHOICES)
    lue = django_filters.BooleanFilter()
    traitee = django_filters.BooleanFilter()
    destinataire = django_filters.NumberFilter(field_name='destinataire__id')

    class Meta:
        model = AlerteIA
        fields = ['niveau', 'type_alerte', 'lue', 'traitee', 'destinataire']


class JournalIAFilter(django_filters.FilterSet):
    type_action = django_filters.ChoiceFilter(choices=JournalIA.TYPE_CHOICES)
    utilisateur = django_filters.NumberFilter(field_name='utilisateur__id')
    succes = django_filters.BooleanFilter()
    objet_type = django_filters.CharFilter()
    date_apres = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_avant = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = JournalIA
        fields = ['type_action', 'utilisateur', 'succes', 'objet_type']
