from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.models import AuditLog
from accounts.permissions import IsAdminOrSuperAdmin
from .models import (
    Organisation, Direction, SousDirection, Service, Site,
    Partenaire, Bailleur, ComiteDirecteur
)
from .serializers import (
    OrganisationSerializer, DirectionSerializer, SousDirectionSerializer,
    ServiceSerializer, SiteSerializer, PartenaireSerializer, BailleurSerializer,
    ComiteDirecteurSerializer, OrganigrammeSerializer
)
from .filters import (
    OrganisationFilter, DirectionFilter, ServiceFilter,
    SiteFilter, PartenaireFilter, BailleurFilter
)


class OrganisationViewSet(viewsets.ModelViewSet):
    queryset = Organisation.objects.select_related('directeur_general').order_by('nom')
    serializer_class = OrganisationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OrganisationFilter
    search_fields = ['nom', 'sigle', 'email']
    ordering_fields = ['nom', 'date_creation']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'organigramme']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]

    def perform_create(self, serializer):
        org = serializer.save()
        AuditLog.log(self.request.user, 'create', module='gouvernance',
                     objet_type='Organisation', objet_id=org.id, objet_repr=str(org),
                     request=self.request)

    def perform_update(self, serializer):
        org = serializer.save()
        AuditLog.log(self.request.user, 'update', module='gouvernance',
                     objet_type='Organisation', objet_id=org.id, objet_repr=str(org),
                     request=self.request)

    def perform_destroy(self, instance):
        AuditLog.log(self.request.user, 'delete', module='gouvernance',
                     objet_type='Organisation', objet_id=instance.id, objet_repr=str(instance),
                     request=self.request)
        instance.delete()

    @action(detail=True, methods=['get'])
    def organigramme(self, request, pk=None):
        org = self.get_object()
        serializer = OrganigrammeSerializer(org)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        org = self.get_object()
        return Response({
            'utilisateurs_actifs': org.utilisateurs.filter(is_active=True).count(),
            'directions': org.directions.filter(actif=True).count(),
            'services': Service.objects.filter(
                Q(direction__organisation=org) | Q(sous_direction__direction__organisation=org)
            ).filter(actif=True).count(),
            'sites': org.sites.filter(actif=True).count(),
            'partenaires': org.partenaires.filter(statut='actif').count(),
            'bailleurs': org.bailleurs.filter(actif=True).count(),
        })


class DirectionViewSet(viewsets.ModelViewSet):
    queryset = Direction.objects.select_related(
        'organisation', 'responsable'
    ).prefetch_related('sous_directions', 'services').order_by('code')
    serializer_class = DirectionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DirectionFilter
    search_fields = ['nom', 'code', 'sigle']
    ordering_fields = ['code', 'nom']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]

    def perform_create(self, serializer):
        d = serializer.save()
        AuditLog.log(self.request.user, 'create', module='gouvernance',
                     objet_type='Direction', objet_id=d.id, objet_repr=str(d), request=self.request)

    def perform_update(self, serializer):
        d = serializer.save()
        AuditLog.log(self.request.user, 'update', module='gouvernance',
                     objet_type='Direction', objet_id=d.id, objet_repr=str(d), request=self.request)


class SousDirectionViewSet(viewsets.ModelViewSet):
    queryset = SousDirection.objects.select_related(
        'direction', 'responsable'
    ).prefetch_related('services').order_by('code')
    serializer_class = SousDirectionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['nom', 'code']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related(
        'direction', 'sous_direction', 'responsable'
    ).order_by('code')
    serializer_class = ServiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ['intitule', 'code']
    ordering_fields = ['code', 'intitule']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]

    def perform_create(self, serializer):
        s = serializer.save()
        AuditLog.log(self.request.user, 'create', module='gouvernance',
                     objet_type='Service', objet_id=s.id, objet_repr=str(s), request=self.request)


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.select_related('organisation', 'responsable').order_by('type_site', 'nom')
    serializer_class = SiteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SiteFilter
    search_fields = ['nom', 'code', 'ville', 'region']
    ordering_fields = ['nom', 'type_site']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]


class PartenaireViewSet(viewsets.ModelViewSet):
    queryset = Partenaire.objects.select_related('organisation').order_by('nom')
    serializer_class = PartenaireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PartenaireFilter
    search_fields = ['nom', 'sigle', 'email', 'pays', 'contact_nom']
    ordering_fields = ['nom', 'type_partenaire']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]

    def perform_create(self, serializer):
        p = serializer.save()
        AuditLog.log(self.request.user, 'create', module='gouvernance',
                     objet_type='Partenaire', objet_id=p.id, objet_repr=str(p), request=self.request)


class BailleurViewSet(viewsets.ModelViewSet):
    queryset = Bailleur.objects.select_related('organisation').order_by('nom')
    serializer_class = BailleurSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BailleurFilter
    search_fields = ['nom', 'sigle', 'email', 'pays_origine', 'contact_nom']
    ordering_fields = ['nom', 'type_bailleur']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]


class ComiteDirecteurViewSet(viewsets.ModelViewSet):
    queryset = ComiteDirecteur.objects.select_related(
        'organisation', 'president'
    ).prefetch_related('participants').order_by('-date_tenue')
    serializer_class = ComiteDirecteurSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['intitule', 'lieu']
    ordering_fields = ['date_tenue']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]


# ─── Dashboard Gouvernance ────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def dashboard_gouvernance(request):
    org_id = request.query_params.get('organisation')
    qs_filter = {}
    if org_id:
        qs_filter['id'] = org_id

    orgs = Organisation.objects.filter(statut='active', **qs_filter)
    total_utilisateurs = sum(o.utilisateurs.filter(is_active=True).count() for o in orgs)
    total_directions = Direction.objects.filter(organisation__in=orgs, actif=True).count()
    total_services = Service.objects.filter(
        Q(direction__organisation__in=orgs) | Q(sous_direction__direction__organisation__in=orgs),
        actif=True,
    ).count()
    total_sites = Site.objects.filter(organisation__in=orgs, actif=True).count()
    total_partenaires = Partenaire.objects.filter(organisation__in=orgs, statut='actif').count()
    total_bailleurs = Bailleur.objects.filter(organisation__in=orgs, actif=True).count()

    by_type = Organisation.objects.values('type_organisation').annotate(nb=Count('id'))

    return Response({
        'organisations_actives': orgs.count(),
        'utilisateurs_actifs': total_utilisateurs,
        'directions': total_directions,
        'services': total_services,
        'sites': total_sites,
        'partenaires': total_partenaires,
        'bailleurs': total_bailleurs,
        'par_type': list(by_type),
    })
