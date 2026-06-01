from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import Diligence, SuiviDiligence, RelanceDiligence
from .serializers import (
    DiligenceListSerializer, DiligenceDetailSerializer,
    SuiviDiligenceSerializer, RelanceDiligenceSerializer,
)

CanRead = HasModulePermission.for_module('diligences', 'peut_lire')
CanEdit = HasModulePermission.for_module('diligences', 'peut_modifier')


class DiligenceViewSet(viewsets.ModelViewSet):
    queryset = Diligence.objects.select_related(
        'emetteur', 'responsable', 'programme', 'projet', 'created_by'
    ).prefetch_related('suivis', 'relances').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'priorite', 'type_source', 'responsable', 'programme', 'projet']
    search_fields = ['reference', 'titre', 'description', 'source_reference']
    ordering_fields = ['created_at', 'date_echeance', 'priorite', 'statut']

    def get_permissions(self):
        return [CanRead()] if self.action in ['list', 'retrieve', 'dashboard'] else [CanEdit()]

    def get_serializer_class(self):
        return DiligenceListSerializer if self.action == 'list' else DiligenceDetailSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user, emetteur=self.request.user)

    @action(detail=True, methods=['post'])
    def affecter(self, request, pk=None):
        d = self.get_object()
        responsable_id = request.data.get('responsable_id')
        if not responsable_id:
            return Response({'error': 'responsable_id requis'}, status=400)
        d.responsable_id = responsable_id
        d.statut = 'affectee'
        d.save(update_fields=['responsable_id', 'statut'])
        return Response(DiligenceDetailSerializer(d).data)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        d = self.get_object()
        d.statut = 'cloturee'
        d.date_cloture = timezone.now().date()
        d.taux_avancement = 100
        d.resultat = request.data.get('resultat', d.resultat)
        d.save(update_fields=['statut', 'date_cloture', 'taux_avancement', 'resultat'])
        return Response({'statut': 'cloturee'})

    @action(detail=True, methods=['post'])
    def ajouter_suivi(self, request, pk=None):
        d = self.get_object()
        data = {**request.data, 'diligence': d.id}
        s = SuiviDiligenceSerializer(data=data)
        s.is_valid(raise_exception=True)
        suivi = s.save(auteur=request.user)
        d.taux_avancement = suivi.avancement
        if suivi.avancement >= 100:
            d.statut = 'en_attente_controle'
        elif d.statut == 'affectee':
            d.statut = 'en_cours'
        d.save(update_fields=['taux_avancement', 'statut'])
        return Response(s.data, status=201)

    @action(detail=True, methods=['post'])
    def relancer(self, request, pk=None):
        d = self.get_object()
        relance = RelanceDiligence.objects.create(
            diligence=d,
            emetteur=request.user,
            message=request.data.get('message', 'Relance')
        )
        return Response(RelanceDiligenceSerializer(relance).data, status=201)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        qs = Diligence.objects.all()
        today = timezone.now().date()
        return Response({
            'total': qs.count(),
            'par_statut': {s: qs.filter(statut=s).count() for s, _ in Diligence.STATUT_CHOICES},
            'en_retard': qs.filter(date_echeance__lt=today).exclude(statut__in=['cloturee', 'annulee']).count(),
            'urgentes': qs.filter(priorite='urgente').exclude(statut__in=['cloturee', 'annulee']).count(),
            'par_type': {t: qs.filter(type_source=t).count() for t, _ in Diligence.TYPE_CHOICES},
        })


class SuiviDiligenceViewSet(viewsets.ModelViewSet):
    queryset = SuiviDiligence.objects.select_related('auteur', 'diligence').order_by('-date_suivi')
    serializer_class = SuiviDiligenceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['diligence']

    def get_permissions(self):
        return [CanRead()] if self.action == 'list' else [CanEdit()]

    def perform_create(self, s):
        s.save(auteur=self.request.user)


class RelanceDiligenceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RelanceDiligence.objects.select_related('emetteur', 'diligence').order_by('-date_relance')
    serializer_class = RelanceDiligenceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['diligence']
    permission_classes = [CanRead]
