from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import NonConformite, ActionQualite, AuditInterne, IndicateurQualite
from .serializers import (
    NonConformiteListSerializer, NonConformiteDetailSerializer,
    ActionQualiteSerializer, AuditInterneSerializer, IndicateurQualiteSerializer,
)

CanRead = HasModulePermission.for_module('gestion_qualite', 'peut_lire')
CanEdit = HasModulePermission.for_module('gestion_qualite', 'peut_modifier')


class NonConformiteViewSet(viewsets.ModelViewSet):
    queryset = NonConformite.objects.select_related(
        'detecte_par', 'responsable', 'programme', 'projet'
    ).prefetch_related('actions').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'gravite', 'type_nc', 'programme', 'projet']
    search_fields = ['reference', 'titre', 'description']
    ordering_fields = ['created_at', 'date_detection', 'gravite']

    def get_permissions(self):
        return [CanRead()] if self.action in ['list', 'retrieve', 'dashboard'] else [CanEdit()]

    def get_serializer_class(self):
        return NonConformiteListSerializer if self.action == 'list' else NonConformiteDetailSerializer

    def perform_create(self, s):
        s.save(detecte_par=self.request.user)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        nc = self.get_object()
        nc.statut = 'cloturee'
        nc.date_cloture = timezone.now().date()
        nc.save(update_fields=['statut', 'date_cloture'])
        return Response({'statut': 'cloturee'})

    @action(detail=True, methods=['post'])
    def verifier(self, request, pk=None):
        nc = self.get_object()
        nc.statut = 'verifiee'
        nc.save(update_fields=['statut'])
        return Response({'statut': 'verifiee'})

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        qs = NonConformite.objects.all()
        return Response({
            'total': qs.count(),
            'par_statut': {s: qs.filter(statut=s).count() for s, _ in NonConformite.STATUT_CHOICES},
            'par_gravite': {g: qs.filter(gravite=g).count() for g, _ in NonConformite.GRAVITE_CHOICES},
            'par_type': {t: qs.filter(type_nc=t).count() for t, _ in NonConformite.TYPE_CHOICES},
            'ouvertes': qs.filter(statut='ouverte').count(),
        })


class ActionQualiteViewSet(viewsets.ModelViewSet):
    queryset = ActionQualite.objects.select_related('responsable', 'non_conformite').order_by('-created_at')
    serializer_class = ActionQualiteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['type_action', 'statut', 'non_conformite']
    search_fields = ['titre', 'description']

    def get_permissions(self):
        return [CanRead()] if self.action in ['list', 'retrieve'] else [CanEdit()]

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def realiser(self, request, pk=None):
        a = self.get_object()
        a.statut = 'realisee'
        a.date_realisation = timezone.now().date()
        a.resultat = request.data.get('resultat', a.resultat)
        a.save(update_fields=['statut', 'date_realisation', 'resultat'])
        return Response({'statut': 'realisee'})

    @action(detail=True, methods=['post'])
    def verifier(self, request, pk=None):
        a = self.get_object()
        a.statut = 'verifiee'
        a.efficace = request.data.get('efficace', True)
        a.save(update_fields=['statut', 'efficace'])
        return Response({'statut': 'verifiee', 'efficace': a.efficace})


class AuditInterneViewSet(viewsets.ModelViewSet):
    queryset = AuditInterne.objects.select_related('auditeur_principal', 'programme', 'projet').order_by('-date_planifiee')
    serializer_class = AuditInterneSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['statut', 'type_audit', 'programme', 'projet']
    search_fields = ['reference', 'titre', 'perimetre']

    def get_permissions(self):
        return [CanRead()] if self.action in ['list', 'retrieve'] else [CanEdit()]

    @action(detail=True, methods=['post'])
    def demarrer(self, request, pk=None):
        a = self.get_object()
        a.statut = 'en_cours'
        a.date_realisation = timezone.now().date()
        a.save(update_fields=['statut', 'date_realisation'])
        return Response({'statut': 'en_cours'})

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        a = self.get_object()
        a.statut = 'cloture'
        a.conclusions = request.data.get('conclusions', a.conclusions)
        a.nb_nc_majeures = request.data.get('nb_nc_majeures', a.nb_nc_majeures)
        a.nb_nc_mineures = request.data.get('nb_nc_mineures', a.nb_nc_mineures)
        a.save(update_fields=['statut', 'conclusions', 'nb_nc_majeures', 'nb_nc_mineures'])
        return Response({'statut': 'cloture'})


class IndicateurQualiteViewSet(viewsets.ModelViewSet):
    queryset = IndicateurQualite.objects.select_related('responsable').order_by('code')
    serializer_class = IndicateurQualiteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['actif', 'frequence_mesure']
    search_fields = ['code', 'intitule']

    def get_permissions(self):
        return [CanRead()] if self.action in ['list', 'retrieve'] else [CanEdit()]

    @action(detail=True, methods=['post'])
    def mesurer(self, request, pk=None):
        ind = self.get_object()
        valeur = request.data.get('valeur')
        if valeur is None:
            return Response({'error': 'valeur requise'}, status=400)
        ind.valeur_actuelle = valeur
        ind.save(update_fields=['valeur_actuelle'])
        return Response(IndicateurQualiteSerializer(ind).data)


@api_view(['GET'])
@permission_classes([CanRead])
def dashboard_qualite(request):
    return Response({
        'non_conformites': {
            'total': NonConformite.objects.count(),
            'ouvertes': NonConformite.objects.filter(statut='ouverte').count(),
            'par_gravite': {
                g: NonConformite.objects.filter(gravite=g).count()
                for g, _ in NonConformite.GRAVITE_CHOICES
            },
        },
        'actions': {
            'total': ActionQualite.objects.count(),
            'par_type': {
                t: ActionQualite.objects.filter(type_action=t).count()
                for t, _ in ActionQualite.TYPE_CHOICES
            },
            'en_cours': ActionQualite.objects.filter(statut='en_cours').count(),
        },
        'audits': {
            'total': AuditInterne.objects.count(),
            'planifies': AuditInterne.objects.filter(statut='planifie').count(),
        },
        'indicateurs': {
            'total': IndicateurQualite.objects.filter(actif=True).count(),
        },
    })
