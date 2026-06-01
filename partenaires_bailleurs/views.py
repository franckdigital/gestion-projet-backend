from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import (
    Partenaire, ContactPartenaire, LiaisonProjetPartenaire,
    Convention, RenouvellementConvention,
    AccesPortailPartenaire, DepotDocumentPortail,
)
from .serializers import (
    PartenaireListSerializer, PartenaireDetailSerializer, PartenaireCartographieSerializer,
    ContactPartenaireSerializer,
    LiaisonProjetPartenaireSerializer,
    ConventionListSerializer, ConventionDetailSerializer, ConventionCreateSerializer,
    RenouvellementConventionSerializer, RenouvellementCreateSerializer,
    AccesPortailPartenaireSerializer,
    DepotDocumentPortailSerializer, DepotRejeterSerializer,
)
from .filters import (
    PartenaireFilter, ContactPartenaireFilter, LiaisonProjetPartenaireFilter,
    ConventionFilter, RenouvellementConventionFilter,
    AccesPortailPartenaireFilter, DepotDocumentPortailFilter,
)

# ─── Raccourcis permissions ───────────────────────────────────────────────────

CanReadPartenaires = HasModulePermission.for_module('partenaires_bailleurs', 'peut_lire')
CanEditPartenaires = HasModulePermission.for_module('partenaires_bailleurs', 'peut_modifier')
CanValidatePartenaires = HasModulePermission.for_module('partenaires_bailleurs', 'peut_valider')


# ─── M39 : Partenaires ────────────────────────────────────────────────────────

class PartenaireViewSet(viewsets.ModelViewSet):
    queryset = Partenaire.objects.select_related('cree_par').prefetch_related('contacts', 'conventions').order_by('nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PartenaireFilter
    search_fields = ['nom', 'sigle', 'email', 'pays', 'ville', 'contact_principal']
    ordering_fields = ['nom', 'type_partenaire', 'statut', 'pays', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'cartographie']:
            return [CanReadPartenaires()]
        return [CanEditPartenaires()]

    def get_serializer_class(self):
        if self.action == 'list':
            return PartenaireListSerializer
        if self.action == 'cartographie':
            return PartenaireCartographieSerializer
        return PartenaireDetailSerializer

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)

    @action(detail=False, methods=['get'])
    def cartographie(self, request):
        """Retourne la liste des partenaires avec coordonnées GPS pour affichage SIG."""
        qs = Partenaire.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        ).select_related('cree_par')

        # Filtres optionnels
        type_partenaire = request.query_params.get('type_partenaire')
        statut = request.query_params.get('statut')
        if type_partenaire:
            qs = qs.filter(type_partenaire=type_partenaire)
        if statut:
            qs = qs.filter(statut=statut)

        serializer = PartenaireCartographieSerializer(qs, many=True)
        return Response({
            'nb_partenaires': qs.count(),
            'partenaires': serializer.data,
        })

    @action(detail=True, methods=['get'])
    def conventions(self, request, pk=None):
        """Liste des conventions d'un partenaire."""
        partenaire = self.get_object()
        qs = partenaire.conventions.select_related('responsable').order_by('-date_signature')
        return Response(ConventionListSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'])
    def projets(self, request, pk=None):
        """Liste des projets liés au partenaire."""
        partenaire = self.get_object()
        qs = partenaire.liaisons_projet.select_related('projet').order_by('-date_debut')
        return Response(LiaisonProjetPartenaireSerializer(qs, many=True).data)


class ContactPartenaireViewSet(viewsets.ModelViewSet):
    queryset = ContactPartenaire.objects.select_related('partenaire').order_by('partenaire__nom', 'nom')
    serializer_class = ContactPartenaireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ContactPartenaireFilter
    search_fields = ['nom', 'prenom', 'email', 'telephone']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadPartenaires()]
        return [CanEditPartenaires()]

    def get_queryset(self):
        qs = super().get_queryset()
        partenaire_id = self.request.query_params.get('partenaire')
        if partenaire_id:
            qs = qs.filter(partenaire_id=partenaire_id)
        return qs


class LiaisonProjetPartenaireViewSet(viewsets.ModelViewSet):
    queryset = LiaisonProjetPartenaire.objects.select_related('partenaire', 'projet').order_by('-date_debut')
    serializer_class = LiaisonProjetPartenaireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LiaisonProjetPartenaireFilter
    search_fields = ['partenaire__nom', 'projet__titre', 'notes']
    ordering_fields = ['montant_finance', 'date_debut', 'date_fin']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadPartenaires()]
        return [CanEditPartenaires()]


# ─── M40 : Conventions ────────────────────────────────────────────────────────

class ConventionViewSet(viewsets.ModelViewSet):
    queryset = Convention.objects.select_related(
        'partenaire', 'programme', 'projet', 'signataire_interne', 'responsable', 'document_ged'
    ).prefetch_related('renouvellements').order_by('-date_signature', '-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ConventionFilter
    search_fields = ['reference', 'intitule', 'objet', 'partenaire__nom', 'signataire_externe']
    ordering_fields = ['date_signature', 'date_fin', 'montant', 'created_at', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'alertes']:
            return [CanReadPartenaires()]
        if self.action in ['signer', 'archiver', 'renouveler']:
            return [CanValidatePartenaires()]
        return [CanEditPartenaires()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ConventionListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ConventionCreateSerializer
        return ConventionDetailSerializer

    # ── Actions métier ────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def signer(self, request, pk=None):
        """Marque la convention comme signée."""
        convention = self.get_object()
        if convention.statut not in ('valide', 'en_validation'):
            return Response(
                {'detail': 'Seule une convention validée peut être signée.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        convention.statut = 'signe'
        convention.date_signature = request.data.get('date_signature') or timezone.now().date()
        convention.signataire_externe = request.data.get('signataire_externe', convention.signataire_externe)
        convention.save(update_fields=['statut', 'date_signature', 'signataire_externe'])
        return Response(ConventionDetailSerializer(convention).data)

    @action(detail=True, methods=['post'])
    def renouveler(self, request, pk=None):
        """Renouvelle la convention : crée un RenouvellementConvention et met à jour date_fin."""
        convention = self.get_object()
        serializer = RenouvellementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        renouvellement = RenouvellementConvention.objects.create(
            convention=convention,
            nouvelle_date_fin=data['nouvelle_date_fin'],
            nouveau_montant=data.get('nouveau_montant'),
            motif=data.get('motif', ''),
            date_signature=data.get('date_signature'),
            fichier=data.get('fichier'),
            effectue_par=request.user,
        )

        # Mise à jour de la convention
        convention.date_fin = data['nouvelle_date_fin']
        if data.get('nouveau_montant'):
            convention.montant = data['nouveau_montant']
        if convention.statut in ('expire', 'suspendu', 'signe'):
            convention.statut = 'actif'
        convention.save(update_fields=['date_fin', 'montant', 'statut'])

        return Response(
            {
                'convention': ConventionDetailSerializer(convention).data,
                'renouvellement': RenouvellementConventionSerializer(renouvellement).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        """Archive la convention."""
        convention = self.get_object()
        if convention.statut == 'archive':
            return Response({'detail': 'Convention déjà archivée.'}, status=status.HTTP_400_BAD_REQUEST)
        convention.statut = 'archive'
        convention.save(update_fields=['statut'])
        return Response(ConventionDetailSerializer(convention).data)

    @action(detail=False, methods=['get'])
    def alertes(self, request):
        """Liste des conventions expirant dans 30 ou 60 jours."""
        today = timezone.now().date()
        seuil_str = request.query_params.get('jours', '30')
        try:
            seuil = int(seuil_str)
        except ValueError:
            seuil = 30

        date_limite = today + timezone.timedelta(days=seuil)

        qs = Convention.objects.filter(
            date_fin__gte=today,
            date_fin__lte=date_limite,
            statut__in=['actif', 'signe'],
        ).select_related('partenaire', 'responsable').order_by('date_fin')

        return Response({
            'seuil_jours': seuil,
            'date_today': today,
            'date_limite': date_limite,
            'nb_alertes': qs.count(),
            'conventions': ConventionListSerializer(qs, many=True).data,
        })


class RenouvellementConventionViewSet(viewsets.ModelViewSet):
    queryset = RenouvellementConvention.objects.select_related('convention', 'effectue_par').order_by('-created_at')
    serializer_class = RenouvellementConventionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RenouvellementConventionFilter
    ordering_fields = ['created_at', 'nouvelle_date_fin']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadPartenaires()]
        return [CanValidatePartenaires()]

    def get_queryset(self):
        qs = super().get_queryset()
        convention_id = self.request.query_params.get('convention')
        if convention_id:
            qs = qs.filter(convention_id=convention_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(effectue_par=self.request.user)


# ─── M44 : Portail partenaire ────────────────────────────────────────────────

class AccesPortailPartenaireViewSet(viewsets.ModelViewSet):
    queryset = AccesPortailPartenaire.objects.select_related(
        'partenaire', 'utilisateur', 'accorde_par'
    ).prefetch_related('projets_accessibles', 'programmes_accessibles').order_by('-created_at')
    serializer_class = AccesPortailPartenaireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AccesPortailPartenaireFilter
    search_fields = ['partenaire__nom', 'utilisateur__email']
    ordering_fields = ['created_at', 'date_fin']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadPartenaires()]
        return [CanValidatePartenaires()]

    def perform_create(self, serializer):
        serializer.save(accorde_par=self.request.user)

    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        acces = self.get_object()
        acces.statut = 'suspendu'
        acces.save(update_fields=['statut'])
        return Response(AccesPortailPartenaireSerializer(acces).data)

    @action(detail=True, methods=['post'])
    def reactiver(self, request, pk=None):
        acces = self.get_object()
        acces.statut = 'actif'
        acces.save(update_fields=['statut'])
        return Response(AccesPortailPartenaireSerializer(acces).data)


class DepotDocumentPortailViewSet(viewsets.ModelViewSet):
    queryset = DepotDocumentPortail.objects.select_related(
        'partenaire', 'projet', 'depose_par', 'valide_par'
    ).order_by('-created_at')
    serializer_class = DepotDocumentPortailSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DepotDocumentPortailFilter
    search_fields = ['titre', 'description', 'type_document', 'partenaire__nom']
    ordering_fields = ['created_at', 'statut', 'type_document']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadPartenaires()]
        if self.action in ['valider', 'rejeter']:
            return [CanValidatePartenaires()]
        return [CanEditPartenaires()]

    def perform_create(self, serializer):
        serializer.save(depose_par=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide un dépôt de document portail."""
        depot = self.get_object()
        if depot.statut != 'en_attente':
            return Response(
                {'detail': 'Seul un dépôt en attente peut être validé.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        depot.statut = 'valide'
        depot.valide_par = request.user
        depot.date_validation = timezone.now()
        depot.motif_rejet = ''
        depot.save(update_fields=['statut', 'valide_par', 'date_validation', 'motif_rejet'])
        return Response(DepotDocumentPortailSerializer(depot).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        """Rejette un dépôt de document portail avec motif obligatoire."""
        depot = self.get_object()
        if depot.statut != 'en_attente':
            return Response(
                {'detail': 'Seul un dépôt en attente peut être rejeté.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = DepotRejeterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        depot.statut = 'rejete'
        depot.valide_par = request.user
        depot.date_validation = timezone.now()
        depot.motif_rejet = serializer.validated_data['motif_rejet']
        depot.save(update_fields=['statut', 'valide_par', 'date_validation', 'motif_rejet'])
        return Response(DepotDocumentPortailSerializer(depot).data)


# ─── Dashboard partenaires & bailleurs ───────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadPartenaires])
def dashboard_partenaires(request):
    today = timezone.now().date()
    seuil_alerte = today + timezone.timedelta(days=60)

    # Partenaires par type
    par_type = list(
        Partenaire.objects.values('type_partenaire').annotate(nb=Count('id')).order_by('-nb')
    )
    par_statut = list(
        Partenaire.objects.values('statut').annotate(nb=Count('id')).order_by('-nb')
    )

    # Conventions
    conventions_actives = Convention.objects.filter(statut__in=['actif', 'signe']).count()
    conventions_expirees = Convention.objects.filter(date_fin__lt=today).count()
    montant_total = Convention.objects.filter(
        statut__in=['actif', 'signe']
    ).aggregate(total=Sum('montant'))['total'] or 0

    alertes_expiration = Convention.objects.filter(
        date_fin__gte=today,
        date_fin__lte=seuil_alerte,
        statut__in=['actif', 'signe'],
    ).order_by('date_fin')

    # Dépôts portail
    depots_en_attente = DepotDocumentPortail.objects.filter(statut='en_attente').count()

    return Response({
        'partenaires': {
            'total': Partenaire.objects.count(),
            'actifs': Partenaire.objects.filter(statut='actif').count(),
            'par_type': par_type,
            'par_statut': par_statut,
            'avec_coordonnees': Partenaire.objects.filter(
                latitude__isnull=False, longitude__isnull=False
            ).count(),
        },
        'conventions': {
            'total': Convention.objects.count(),
            'actives': conventions_actives,
            'expirees': conventions_expirees,
            'montant_total': montant_total,
            'alertes_60j': alertes_expiration.count(),
            'alertes_30j': Convention.objects.filter(
                date_fin__gte=today,
                date_fin__lte=today + timezone.timedelta(days=30),
                statut__in=['actif', 'signe'],
            ).count(),
            'prochaines_expirations': ConventionListSerializer(
                alertes_expiration[:5], many=True
            ).data,
        },
        'portail': {
            'depots_en_attente': depots_en_attente,
            'acces_actifs': AccesPortailPartenaire.objects.filter(statut='actif').count(),
        },
    })
