from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.models import AuditLog
from accounts.permissions import HasModulePermission
from .models import (
    ZoneSIG, CoucheCartographique, PointCartographie,
    InfrastructureSIG, CarteSIG,
)
from .serializers import (
    ZoneSIGListSerializer, ZoneSIGDetailSerializer,
    CoucheCartographiqueListSerializer, CoucheCartographiqueDetailSerializer,
    PointCartographieListSerializer, PointCartographieDetailSerializer,
    InfrastructureSIGListSerializer, InfrastructureSIGDetailSerializer,
    CarteSIGListSerializer, CarteSIGDetailSerializer,
)
from .filters import (
    ZoneSIGFilter, CoucheCartographiqueFilter, PointCartographieFilter,
    InfrastructureSIGFilter, CarteSIGFilter,
)

CanReadSIG = HasModulePermission.for_module('sig', 'peut_lire')
CanEditSIG = HasModulePermission.for_module('sig', 'peut_modifier')
CanValidateSIG = HasModulePermission.for_module('sig', 'peut_valider')


# ─── ZoneSIG ─────────────────────────────────────────────────────────────────

class ZoneSIGViewSet(viewsets.ModelViewSet):
    queryset = ZoneSIG.objects.select_related('parent').prefetch_related('sous_zones').order_by(
        'type_zone', 'nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ZoneSIGFilter
    search_fields = ['nom', 'code', 'pays']
    ordering_fields = ['nom', 'type_zone', 'superficie_km2', 'population', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'arborescence']:
            return [CanReadSIG()]
        return [CanEditSIG()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ZoneSIGListSerializer
        return ZoneSIGDetailSerializer

    def perform_create(self, serializer):
        zone = serializer.save()
        AuditLog.log(self.request.user, 'create', module='sig',
                     objet_type='ZoneSIG', objet_id=zone.id, request=self.request)

    @action(detail=False, methods=['get'])
    def arborescence(self, request):
        """Retourne l'arborescence hiérarchique des zones (racines avec sous-zones imbriquées)."""
        racines = ZoneSIG.objects.filter(parent__isnull=True, actif=True).prefetch_related(
            'sous_zones__sous_zones')

        def build_node(zone):
            return {
                'id': zone.id,
                'nom': zone.nom,
                'code': zone.code,
                'type_zone': zone.type_zone,
                'type_zone_display': zone.get_type_zone_display(),
                'pays': zone.pays,
                'sous_zones': [build_node(s) for s in zone.sous_zones.filter(actif=True)],
            }

        data = [build_node(z) for z in racines]
        return Response(data)


# ─── CoucheCartographique ─────────────────────────────────────────────────────

class CoucheCartographiqueViewSet(viewsets.ModelViewSet):
    queryset = CoucheCartographique.objects.select_related(
        'cree_par', 'filtre_programme', 'filtre_projet'
    ).order_by('ordre', 'nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CoucheCartographiqueFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'ordre', 'type_couche', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadSIG()]
        return [CanEditSIG()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CoucheCartographiqueListSerializer
        return CoucheCartographiqueDetailSerializer

    def perform_create(self, serializer):
        couche = serializer.save(cree_par=self.request.user)
        AuditLog.log(self.request.user, 'create', module='sig',
                     objet_type='CoucheCartographique', objet_id=couche.id, request=self.request)


# ─── PointCartographie ────────────────────────────────────────────────────────

class PointCartographieViewSet(viewsets.ModelViewSet):
    queryset = PointCartographie.objects.select_related(
        'couche', 'zone', 'programme', 'projet', 'cree_par'
    ).order_by('type_point', 'titre')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PointCartographieFilter
    search_fields = ['titre', 'description']
    ordering_fields = ['titre', 'type_point', 'created_at', 'latitude', 'longitude']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'geojson']:
            return [CanReadSIG()]
        return [CanEditSIG()]

    def get_serializer_class(self):
        if self.action == 'list':
            return PointCartographieListSerializer
        return PointCartographieDetailSerializer

    def perform_create(self, serializer):
        point = serializer.save(cree_par=self.request.user)
        AuditLog.log(self.request.user, 'create', module='sig',
                     objet_type='PointCartographie', objet_id=point.id, request=self.request)

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Retourne une FeatureCollection GeoJSON de tous les points filtrés."""
        qs = self.filter_queryset(self.get_queryset())
        features = []
        for point in qs:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(point.longitude), float(point.latitude)],
                },
                'properties': {
                    'id': point.id,
                    'type_point': point.type_point,
                    'type_point_display': point.get_type_point_display(),
                    'titre': point.titre,
                    'description': point.description,
                    'couche_id': point.couche_id,
                    'zone_id': point.zone_id,
                    'programme_id': point.programme_id,
                    'projet_id': point.projet_id,
                    'valeur': float(point.valeur) if point.valeur is not None else None,
                    'unite': point.unite,
                    'couleur': point.couleur,
                    'icone': point.icone,
                    'altitude': float(point.altitude) if point.altitude is not None else None,
                    'rayon_metres': float(point.rayon_metres) if point.rayon_metres is not None else None,
                    'source_gps': point.source_gps,
                    'precision_gps': float(point.precision_gps) if point.precision_gps is not None else None,
                    'actif': point.actif,
                    **point.proprietes,
                },
            }
            features.append(feature)
        return Response({
            'type': 'FeatureCollection',
            'count': len(features),
            'features': features,
        })


# ─── InfrastructureSIG ───────────────────────────────────────────────────────

class InfrastructureSIGViewSet(viewsets.ModelViewSet):
    queryset = InfrastructureSIG.objects.select_related(
        'zone', 'programme', 'projet', 'cree_par'
    ).order_by('type_infrastructure', 'nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = InfrastructureSIGFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'type_infrastructure', 'statut', 'date_mise_en_service', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'geojson']:
            return [CanReadSIG()]
        return [CanEditSIG()]

    def get_serializer_class(self):
        if self.action == 'list':
            return InfrastructureSIGListSerializer
        return InfrastructureSIGDetailSerializer

    def perform_create(self, serializer):
        infra = serializer.save(cree_par=self.request.user)
        AuditLog.log(self.request.user, 'create', module='sig',
                     objet_type='InfrastructureSIG', objet_id=infra.id, request=self.request)

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Retourne une FeatureCollection GeoJSON de toutes les infrastructures filtrées."""
        qs = self.filter_queryset(self.get_queryset())
        features = []
        for infra in qs:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(infra.longitude), float(infra.latitude)],
                },
                'properties': {
                    'id': infra.id,
                    'nom': infra.nom,
                    'type_infrastructure': infra.type_infrastructure,
                    'type_infrastructure_display': infra.get_type_infrastructure_display(),
                    'statut': infra.statut,
                    'statut_display': infra.get_statut_display(),
                    'zone_id': infra.zone_id,
                    'programme_id': infra.programme_id,
                    'projet_id': infra.projet_id,
                    'capacite': infra.capacite,
                    'population_beneficiaire': infra.population_beneficiaire,
                    'date_mise_en_service': str(infra.date_mise_en_service) if infra.date_mise_en_service else None,
                    'cout_realisation': float(infra.cout_realisation) if infra.cout_realisation is not None else None,
                    **infra.proprietes,
                },
            }
            features.append(feature)
        return Response({
            'type': 'FeatureCollection',
            'count': len(features),
            'features': features,
        })


# ─── CarteSIG ─────────────────────────────────────────────────────────────────

class CarteSIGViewSet(viewsets.ModelViewSet):
    queryset = CarteSIG.objects.select_related(
        'cree_par', 'programme', 'projet'
    ).prefetch_related('couches').order_by('-est_defaut', 'nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CarteSIGFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'est_defaut', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadSIG()]
        if self.action == 'activer':
            return [CanValidateSIG()]
        return [CanEditSIG()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CarteSIGListSerializer
        return CarteSIGDetailSerializer

    def perform_create(self, serializer):
        carte = serializer.save(cree_par=self.request.user)
        AuditLog.log(self.request.user, 'create', module='sig',
                     objet_type='CarteSIG', objet_id=carte.id, request=self.request)

    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        """Marque cette carte comme carte par défaut (désactive les autres)."""
        carte = self.get_object()
        CarteSIG.objects.filter(est_defaut=True).update(est_defaut=False)
        carte.est_defaut = True
        carte.save(update_fields=['est_defaut'])
        AuditLog.log(request.user, 'update', module='sig',
                     objet_type='CarteSIG', objet_id=carte.id, request=request,
                     details={'detail': 'Carte définie comme carte par défaut'})
        return Response(CarteSIGDetailSerializer(carte).data)


# ─── Dashboard SIG ────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([HasModulePermission.for_module('sig', 'peut_lire')])
def dashboard_sig(request):
    """Dashboard SIG : statistiques et résumé GeoJSON."""
    # Zones
    nb_zones = ZoneSIG.objects.filter(actif=True).count()
    zones_par_type = list(
        ZoneSIG.objects.filter(actif=True)
        .values('type_zone')
        .annotate(nb=Count('id'))
        .order_by('type_zone')
    )

    # Points
    nb_points_total = PointCartographie.objects.filter(actif=True).count()
    points_par_type = list(
        PointCartographie.objects.filter(actif=True)
        .values('type_point')
        .annotate(nb=Count('id'))
        .order_by('type_point')
    )

    # Infrastructures
    nb_infrastructures_total = InfrastructureSIG.objects.count()
    infras_par_type = list(
        InfrastructureSIG.objects.values('type_infrastructure')
        .annotate(nb=Count('id'))
        .order_by('type_infrastructure')
    )
    infras_par_statut = list(
        InfrastructureSIG.objects.values('statut')
        .annotate(nb=Count('id'))
        .order_by('statut')
    )

    # Couches & cartes
    nb_couches = CoucheCartographique.objects.count()
    nb_cartes = CarteSIG.objects.count()

    # GeoJSON résumé (points actifs + infrastructures)
    points_qs = PointCartographie.objects.filter(actif=True).select_related('zone')
    infras_qs = InfrastructureSIG.objects.all()

    features = []
    for point in points_qs:
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [float(point.longitude), float(point.latitude)]},
            'properties': {
                'id': point.id, 'layer': 'point', 'type': point.type_point,
                'titre': point.titre, 'couleur': point.couleur,
            },
        })
    for infra in infras_qs:
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [float(infra.longitude), float(infra.latitude)]},
            'properties': {
                'id': infra.id, 'layer': 'infrastructure', 'type': infra.type_infrastructure,
                'titre': infra.nom, 'statut': infra.statut,
            },
        })

    nb_regions = ZoneSIG.objects.filter(actif=True, type_zone__in=['region', 'departement']).count()
    nb_points_valides = PointCartographie.objects.filter(actif=True).count()
    nb_infras_actives = InfrastructureSIG.objects.filter(statut='operationnel').count()
    nb_cartes_publiees = CarteSIG.objects.filter(est_publique=True).count()

    return Response({
        # Format structuré pour le frontend
        'zones': {
            'total': nb_zones,
            'regions': nb_regions,
            'par_type': zones_par_type,
        },
        'points': {
            'total': nb_points_total,
            'valides': nb_points_valides,
            'par_type': points_par_type,
        },
        'infrastructures': {
            'total': nb_infrastructures_total,
            'actives': nb_infras_actives,
            'par_type': infras_par_type,
            'par_statut': infras_par_statut,
        },
        'couches': {
            'total': nb_couches,
        },
        'cartes': {
            'total': nb_cartes,
            'actives': nb_cartes,
            'publiees': nb_cartes_publiees,
        },
        'geojson_resume': {
            'type': 'FeatureCollection',
            'count': len(features),
            'features': features,
        },
        # Rétrocompatibilité
        'nb_zones': nb_zones,
        'nb_points': nb_points_total,
        'nb_infrastructures': nb_infrastructures_total,
        'nb_couches': nb_couches,
        'nb_cartes': nb_cartes,
    })
