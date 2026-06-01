from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import SessionTerrain, CollecteTerrain, PointageTerrain, SynchronisationMobile, QRCodeScan
from .serializers import (
    SessionTerrainListSerializer, SessionTerrainDetailSerializer,
    CollecteTerrainSerializer, PointageTerrainSerializer,
    SynchronisationMobileSerializer, QRCodeScanSerializer,
)
from .filters import SessionTerrainFilter, CollecteTerrainFilter, PointageTerrainFilter

CanReadMobile = HasModulePermission.for_module('mobile_terrain', 'peut_lire')
CanEditMobile = HasModulePermission.for_module('mobile_terrain', 'peut_modifier')


class SessionTerrainViewSet(viewsets.ModelViewSet):
    queryset = SessionTerrain.objects.select_related(
        'agent', 'projet', 'activite'
    ).prefetch_related('collectes').order_by('-date_debut')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SessionTerrainFilter
    search_fields = ['notes', 'appareil']
    ordering_fields = ['date_debut', 'date_fin', 'statut']

    def get_permissions(self):
        return [CanReadMobile()] if self.action in ['list', 'retrieve'] else [CanEditMobile()]

    def get_serializer_class(self):
        return SessionTerrainListSerializer if self.action == 'list' else SessionTerrainDetailSerializer

    def perform_create(self, s):
        s.save(agent=self.request.user)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        session = self.get_object()
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        session.terminer(lat=lat, lon=lon)
        return Response(SessionTerrainDetailSerializer(session).data)

    @action(detail=True, methods=['post'])
    def synchroniser(self, request, pk=None):
        session = self.get_object()
        session.synchroniser()
        synchro = SynchronisationMobile.objects.create(
            agent=request.user,
            statut='succes',
            nb_elements_envoyes=session.collectes.count(),
            nb_elements_recus=0,
            version_app=request.data.get('version_app', ''),
        )
        session.collectes.filter(statut='en_attente_sync').update(statut='synchronise')
        return Response({
            'session_statut': session.statut,
            'synchro_id': synchro.id,
            'nb_synchronises': session.collectes.count(),
        })

    @action(detail=False, methods=['get'])
    def mes_sessions(self, request):
        qs = SessionTerrain.objects.filter(
            agent=request.user
        ).order_by('-date_debut')[:20]
        return Response(SessionTerrainListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        qs = SessionTerrain.objects.filter(
            agent=request.user, statut='en_cours'
        ).order_by('-date_debut')
        return Response(SessionTerrainDetailSerializer(qs, many=True).data)


class CollecteTerrainViewSet(viewsets.ModelViewSet):
    queryset = CollecteTerrain.objects.select_related(
        'session', 'session__agent', 'indicateur', 'formulaire', 'valide_par'
    ).order_by('-date_collecte_locale')
    serializer_class = CollecteTerrainSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CollecteTerrainFilter
    search_fields = ['titre', 'notes', 'adresse_geo']
    ordering_fields = ['date_collecte_locale', 'type_collecte', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [CanReadMobile()] if self.action in ['list', 'retrieve'] else [CanEditMobile()]

    def perform_create(self, s):
        collecte = s.save()
        collecte.session.nb_collectes = collecte.session.collectes.count()
        collecte.session.save(update_fields=['nb_collectes'])

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        collecte = self.get_object()
        collecte.statut = 'valide'
        collecte.valide_par = request.user
        collecte.save(update_fields=['statut', 'valide_par'])
        return Response(CollecteTerrainSerializer(collecte).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        collecte = self.get_object()
        collecte.statut = 'rejete'
        collecte.save(update_fields=['statut'])
        return Response(CollecteTerrainSerializer(collecte).data)

    @action(detail=False, methods=['post'])
    def sync_batch(self, request):
        """Synchronisation en lot de collectes hors-ligne."""
        collectes_data = request.data.get('collectes', [])
        session_id = request.data.get('session_id')
        created = []
        errors = []
        for item in collectes_data:
            try:
                item['session'] = session_id
                ser = CollecteTerrainSerializer(data=item)
                if ser.is_valid():
                    c = ser.save()
                    c.statut = 'synchronise'
                    c.save(update_fields=['statut'])
                    created.append(c.id)
                else:
                    errors.append({'data': item, 'errors': ser.errors})
            except Exception as e:
                errors.append({'data': item, 'errors': str(e)})
        return Response({
            'created': created,
            'nb_created': len(created),
            'nb_errors': len(errors),
            'errors': errors,
        }, status=201 if created else 400)


class PointageTerrainViewSet(viewsets.ModelViewSet):
    queryset = PointageTerrain.objects.select_related(
        'agent', 'projet', 'activite', 'valide_par'
    ).order_by('-date_heure')
    serializer_class = PointageTerrainSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PointageTerrainFilter
    search_fields = ['notes', 'adresse_geo']
    ordering_fields = ['date_heure', 'type_pointage']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [CanReadMobile()] if self.action in ['list', 'retrieve'] else [CanEditMobile()]

    def perform_create(self, s):
        s.save(agent=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        pointage = self.get_object()
        pointage.valide = True
        pointage.valide_par = request.user
        pointage.save(update_fields=['valide', 'valide_par'])
        return Response(PointageTerrainSerializer(pointage).data)

    @action(detail=False, methods=['get'])
    def mes_pointages(self, request):
        qs = PointageTerrain.objects.filter(
            agent=request.user
        ).order_by('-date_heure')[:50]
        return Response(PointageTerrainSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        qs = self.filter_queryset(self.get_queryset())
        features = []
        for p in qs:
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [float(p.longitude), float(p.latitude)]},
                'properties': {
                    'id': p.id,
                    'agent': str(p.agent),
                    'type_pointage': p.type_pointage,
                    'date_heure': p.date_heure.isoformat(),
                    'valide': p.valide,
                    'notes': p.notes,
                    'projet_id': p.projet_id,
                },
            })
        return Response({'type': 'FeatureCollection', 'features': features})


class SynchronisationMobileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SynchronisationMobile.objects.select_related('agent').order_by('-date_synchro')
    serializer_class = SynchronisationMobileSerializer
    permission_classes = [CanReadMobile]

    def get_queryset(self):
        return super().get_queryset().filter(agent=self.request.user)


class QRCodeScanViewSet(viewsets.ModelViewSet):
    queryset = QRCodeScan.objects.select_related('agent').order_by('-date_scan')
    serializer_class = QRCodeScanSerializer
    permission_classes = [CanEditMobile]

    def perform_create(self, s):
        s.save(agent=self.request.user)

    @action(detail=True, methods=['post'])
    def traiter(self, request, pk=None):
        scan = self.get_object()
        scan.traite = True
        scan.type_objet = request.data.get('type_objet', '')
        scan.objet_id = request.data.get('objet_id')
        scan.save(update_fields=['traite', 'type_objet', 'objet_id'])
        return Response(QRCodeScanSerializer(scan).data)


@api_view(['GET'])
@permission_classes([CanReadMobile])
def dashboard_mobile(request):
    today = timezone.now().date()
    agent = request.query_params.get('agent')
    qs_sessions = SessionTerrain.objects.all()
    qs_collectes = CollecteTerrain.objects.all()
    qs_pointages = PointageTerrain.objects.all()

    if agent:
        qs_sessions = qs_sessions.filter(agent_id=agent)
        qs_collectes = qs_collectes.filter(session__agent_id=agent)
        qs_pointages = qs_pointages.filter(agent_id=agent)

    return Response({
        'sessions': {
            'total': qs_sessions.count(),
            'en_cours': qs_sessions.filter(statut='en_cours').count(),
            'synchronisees': qs_sessions.filter(statut='synchronisee').count(),
            'aujourd_hui': qs_sessions.filter(date_debut__date=today).count(),
        },
        'collectes': {
            'total': qs_collectes.count(),
            'en_attente_sync': qs_collectes.filter(statut='en_attente_sync').count(),
            'validees': qs_collectes.filter(statut='valide').count(),
            'par_type': {t: qs_collectes.filter(type_collecte=t).count()
                        for t, _ in CollecteTerrain.TYPE_CHOICES},
        },
        'pointages': {
            'total': qs_pointages.count(),
            'valides': qs_pointages.filter(valide=True).count(),
            'aujourd_hui': qs_pointages.filter(date_heure__date=today).count(),
        },
        'synchronisations': {
            'total': SynchronisationMobile.objects.count(),
            'succes': SynchronisationMobile.objects.filter(statut='succes').count(),
            'echecs': SynchronisationMobile.objects.filter(statut='echec').count(),
        },
    })
