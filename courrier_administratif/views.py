from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import (
    CourrierEntrant, CourrierSortant,
    CircuitValidation, EtapeCircuit, Parapheur, VisaParapheur, Diligence,
    ModeleCourrierSortant,
)
from .serializers import (
    CourrierEntrantListSerializer, CourrierEntrantDetailSerializer,
    CourrierSortantListSerializer, CourrierSortantDetailSerializer,
    CircuitValidationSerializer, EtapeCircuitSerializer,
    ParapheurListSerializer, ParapheurDetailSerializer,
    VisaParapheurSerializer, DiligenceSerializer, ModeleCourrierSortantSerializer,
)
from .filters import CourrierEntrantFilter, CourrierSortantFilter, ParapheurFilter

CanReadCA = HasModulePermission.for_module('courrier_administratif', 'peut_lire')
CanEditCA = HasModulePermission.for_module('courrier_administratif', 'peut_modifier')
CanValidateCA = HasModulePermission.for_module('courrier_administratif', 'peut_valider')


class CourrierEntrantViewSet(viewsets.ModelViewSet):
    queryset = CourrierEntrant.objects.select_related(
        'affecte_a', 'enregistre_par', 'projet', 'programme'
    ).prefetch_related('diligences').order_by('-date_reception')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourrierEntrantFilter
    search_fields = ['numero', 'expediteur', 'objet', 'texte_ocr']
    ordering_fields = ['date_reception', 'urgence', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadCA()]
        if self.action in ['affecter', 'valider']:
            return [CanValidateCA()]
        return [CanEditCA()]

    def get_serializer_class(self):
        return CourrierEntrantListSerializer if self.action == 'list' else CourrierEntrantDetailSerializer

    def perform_create(self, s):
        s.save(enregistre_par=self.request.user)

    @action(detail=True, methods=['post'])
    def affecter(self, request, pk=None):
        c = self.get_object()
        user_id = request.data.get('user_id')
        instruction = request.data.get('instruction', '')
        if not user_id:
            return Response({'detail': 'user_id requis.'}, status=400)
        from accounts.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable.'}, status=404)
        c.affecter(user, instruction)
        return Response(CourrierEntrantDetailSerializer(c).data)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        c = self.get_object()
        c.cloturer(request.data.get('reponse', ''))
        return Response(CourrierEntrantDetailSerializer(c).data)

    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        c = self.get_object()
        c.statut = 'archive'
        c.save(update_fields=['statut'])
        return Response(CourrierEntrantDetailSerializer(c).data)

    @action(detail=True, methods=['post'])
    def ocr(self, request, pk=None):
        c = self.get_object()
        c.texte_ocr = f"[OCR] Contenu extrait du courrier {c.numero}: {c.objet}"
        c.ocr_effectue = True
        c.save(update_fields=['texte_ocr', 'ocr_effectue'])
        return Response({'ocr_effectue': True, 'nb_caracteres': len(c.texte_ocr)})

    @action(detail=True, methods=['post'])
    def ajouter_diligence(self, request, pk=None):
        c = self.get_object()
        d = Diligence.objects.create(
            courrier=c,
            type_diligence=request.data.get('type_diligence', 'action'),
            description=request.data.get('description', ''),
            responsable_id=request.data.get('responsable'),
            echeance=request.data.get('echeance'),
            assigne_par=request.user,
        )
        c.statut = 'en_cours'
        c.save(update_fields=['statut'])
        return Response(DiligenceSerializer(d).data, status=201)


class CourrierSortantViewSet(viewsets.ModelViewSet):
    queryset = CourrierSortant.objects.select_related(
        'redacteur', 'signataire', 'projet', 'programme', 'en_reponse_a'
    ).order_by('-date_courrier')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourrierSortantFilter
    search_fields = ['reference', 'objet', 'destinataire', 'corps']
    ordering_fields = ['date_courrier', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadCA()]
        if self.action in ['signer']:
            return [CanValidateCA()]
        return [CanEditCA()]

    def get_serializer_class(self):
        return CourrierSortantListSerializer if self.action == 'list' else CourrierSortantDetailSerializer

    def perform_create(self, s):
        s.save(redacteur=self.request.user)

    @action(detail=True, methods=['post'])
    def soumettre_validation(self, request, pk=None):
        c = self.get_object()
        c.statut = 'en_validation'
        c.save(update_fields=['statut'])
        return Response(CourrierSortantDetailSerializer(c).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        c = self.get_object()
        c.statut = 'valide'
        c.save(update_fields=['statut'])
        return Response(CourrierSortantDetailSerializer(c).data)

    @action(detail=True, methods=['post'])
    def signer(self, request, pk=None):
        c = self.get_object()
        c.signer(request.user)
        return Response(CourrierSortantDetailSerializer(c).data)

    @action(detail=True, methods=['post'])
    def expedier(self, request, pk=None):
        c = self.get_object()
        if c.statut not in ('valide', 'signe'):
            return Response({'detail': 'Le courrier doit être validé ou signé.'}, status=400)
        c.expedier()
        return Response(CourrierSortantDetailSerializer(c).data)


class CircuitValidationViewSet(viewsets.ModelViewSet):
    queryset = CircuitValidation.objects.prefetch_related('etapes').filter(est_actif=True)
    serializer_class = CircuitValidationSerializer
    permission_classes = [CanReadCA]


class EtapeCircuitViewSet(viewsets.ModelViewSet):
    queryset = EtapeCircuit.objects.order_by('ordre')
    serializer_class = EtapeCircuitSerializer
    permission_classes = [CanEditCA]

    def get_queryset(self):
        qs = super().get_queryset()
        c = self.request.query_params.get('circuit')
        return qs.filter(circuit_id=c) if c else qs


class ParapheurViewSet(viewsets.ModelViewSet):
    queryset = Parapheur.objects.select_related(
        'circuit', 'soumis_par', 'courrier_sortant'
    ).prefetch_related('visas').order_by('-date_soumission')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ParapheurFilter
    search_fields = ['reference', 'intitule']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadCA()]
        if self.action in ['viser']:
            return [CanValidateCA()]
        return [CanEditCA()]

    def get_serializer_class(self):
        return ParapheurListSerializer if self.action == 'list' else ParapheurDetailSerializer

    def perform_create(self, s):
        par = s.save(soumis_par=self.request.user)
        if par.circuit:
            for etape in par.circuit.etapes.order_by('ordre'):
                VisaParapheur.objects.create(
                    parapheur=par, etape=etape, ordre=etape.ordre,
                    validateur=etape.validateur,
                )

    @action(detail=True, methods=['post'])
    def viser(self, request, pk=None):
        par = self.get_object()
        visa_id = request.data.get('visa_id')
        decision = request.data.get('decision', 'valide')
        commentaire = request.data.get('commentaire', '')
        try:
            visa = par.visas.get(id=visa_id)
        except VisaParapheur.DoesNotExist:
            return Response({'detail': 'Visa introuvable.'}, status=404)
        visa.viser(request.user, decision, commentaire)
        return Response(ParapheurDetailSerializer(par).data)


class VisaParapheurViewSet(viewsets.ModelViewSet):
    queryset = VisaParapheur.objects.order_by('ordre')
    serializer_class = VisaParapheurSerializer
    permission_classes = [CanReadCA]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params.get('parapheur')
        return qs.filter(parapheur_id=p) if p else qs


class DiligenceViewSet(viewsets.ModelViewSet):
    queryset = Diligence.objects.select_related('courrier', 'responsable').order_by('echeance')
    serializer_class = DiligenceSerializer
    permission_classes = [CanReadCA]

    def get_queryset(self):
        qs = super().get_queryset()
        c = self.request.query_params.get('courrier')
        resp = self.request.query_params.get('responsable')
        if c:
            qs = qs.filter(courrier_id=c)
        if resp:
            qs = qs.filter(responsable_id=resp)
        return qs

    @action(detail=True, methods=['post'])
    def realiser(self, request, pk=None):
        d = self.get_object()
        d.statut = 'realisee'
        d.resultat = request.data.get('resultat', '')
        d.save(update_fields=['statut', 'resultat'])
        return Response(DiligenceSerializer(d).data)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        d = self.get_object()
        d.statut = 'cloturee'
        d.save(update_fields=['statut'])
        return Response(DiligenceSerializer(d).data)

    @action(detail=False, methods=['get'])
    def mes_diligences(self, request):
        qs = Diligence.objects.filter(
            responsable=request.user
        ).exclude(statut__in=['cloturee', 'annulee']).order_by('echeance')
        return Response(DiligenceSerializer(qs, many=True).data)


class ModeleCourrierSortantViewSet(viewsets.ModelViewSet):
    serializer_class = ModeleCourrierSortantSerializer
    permission_classes = [CanReadCA]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['nom', 'objet', 'description']

    def get_queryset(self):
        qs = ModeleCourrierSortant.objects.all()
        t = self.request.query_params.get('type_courrier')
        if t:
            qs = qs.filter(type_courrier=t)
        return qs.filter(actif=True)

    def perform_create(self, s):
        s.save(cree_par=self.request.user)


@api_view(['GET'])
@permission_classes([CanReadCA])
def dashboard_courrier(request):
    today = timezone.now().date()
    ce = CourrierEntrant.objects.all()
    cs = CourrierSortant.objects.all()
    par = Parapheur.objects.all()
    return Response({
        'entrants': {
            'total': ce.count(),
            'par_statut': {s: ce.filter(statut=s).count() for s, _ in CourrierEntrant.STATUT_CHOICES},
            'urgents': ce.filter(urgence='tres_urgent').count(),
            'non_affectes': ce.filter(statut='recu').count(),
            'ce_mois': ce.filter(date_reception__month=today.month,
                                  date_reception__year=today.year).count(),
        },
        'sortants': {
            'total': cs.count(),
            'par_statut': {s: cs.filter(statut=s).count() for s, _ in CourrierSortant.STATUT_CHOICES},
        },
        'parapheurs': {
            'total': par.count(),
            'en_cours': par.filter(statut='en_cours').count(),
            'en_attente_visa': par.filter(visas__decision='en_attente').distinct().count(),
        },
        'diligences': {
            'ouvertes': Diligence.objects.filter(statut='ouverte').count(),
            'en_retard': Diligence.objects.filter(
                echeance__lt=today, statut__in=['ouverte', 'en_cours']
            ).count(),
        },
    })
