import uuid
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import Evenement, ParticipantEvenement, DepenseEvenement
from .serializers import (
    EvenementListSerializer, EvenementDetailSerializer,
    ParticipantSerializer, DepenseSerializer,
)

CanRead = HasModulePermission.for_module('evenements', 'peut_lire')
CanEdit = HasModulePermission.for_module('evenements', 'peut_modifier')


class EvenementViewSet(viewsets.ModelViewSet):
    queryset = Evenement.objects.select_related(
        'organisateur', 'programme', 'projet', 'created_by'
    ).prefetch_related('participants', 'depenses').order_by('-date_debut')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type_evenement', 'statut', 'programme', 'projet']
    search_fields = ['titre', 'lieu', 'description']
    ordering_fields = ['date_debut', 'statut', 'created_at']

    def get_permissions(self):
        return [CanRead()] if self.action in ['list', 'retrieve', 'dashboard'] else [CanEdit()]

    def get_serializer_class(self):
        return EvenementListSerializer if self.action == 'list' else EvenementDetailSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user, organisateur=self.request.user)

    @action(detail=True, methods=['post'])
    def confirmer(self, request, pk=None):
        e = self.get_object()
        e.statut = 'confirme'
        e.save(update_fields=['statut'])
        return Response({'statut': 'confirme'})

    @action(detail=True, methods=['post'])
    def demarrer(self, request, pk=None):
        e = self.get_object()
        e.statut = 'en_cours'
        e.save(update_fields=['statut'])
        return Response({'statut': 'en_cours'})

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        e = self.get_object()
        e.statut = 'termine'
        e.compte_rendu = request.data.get('compte_rendu', e.compte_rendu)
        e.save(update_fields=['statut', 'compte_rendu'])
        return Response({'statut': 'termine'})

    @action(detail=True, methods=['post'])
    def inscrire_participant(self, request, pk=None):
        e = self.get_object()
        data = {**request.data, 'evenement': e.id}
        data.setdefault('statut', 'invite')
        s = ParticipantSerializer(data=data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data, status=201)

    @action(detail=True, methods=['post'])
    def pointer_presence(self, request, pk=None):
        e = self.get_object()
        email = request.data.get('email')
        qr_code = request.data.get('qr_code')
        try:
            if qr_code:
                p = e.participants.get(qr_code=qr_code)
            else:
                p = e.participants.get(email=email)
            p.statut = 'present'
            p.date_presence = timezone.now()
            p.save(update_fields=['statut', 'date_presence'])
            return Response({'detail': f'{p.nom} {p.prenom} marqué présent.'})
        except ParticipantEvenement.DoesNotExist:
            return Response({'error': 'Participant non trouvé'}, status=404)

    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        e = self.get_object()
        parts = e.participants.all()
        depenses = e.depenses.all()
        from django.db.models import Sum
        return Response({
            'participants': {
                'total': parts.count(),
                'confirmes': parts.filter(statut='confirme').count(),
                'presents': parts.filter(statut='present').count(),
                'absents': parts.filter(statut='absent').count(),
                'taux_presence': round(
                    parts.filter(statut='present').count() / parts.count() * 100
                    if parts.count() > 0 else 0, 1
                ),
            },
            'budget': {
                'prevu': float(e.budget_prevu),
                'realise': float(depenses.aggregate(t=Sum('montant'))['t'] or 0),
                'par_categorie': list(
                    depenses.values('categorie').annotate(total=Sum('montant'))
                ),
            },
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        qs = Evenement.objects.all()
        today = timezone.now().date()
        return Response({
            'total': qs.count(),
            'par_statut': {s: qs.filter(statut=s).count() for s, _ in Evenement.STATUT_CHOICES},
            'par_type': {t: qs.filter(type_evenement=t).count() for t, _ in Evenement.TYPE_CHOICES},
            'a_venir': qs.filter(date_debut__gte=timezone.now(), statut__in=['planifie', 'confirme']).count(),
            'ce_mois': qs.filter(date_debut__month=today.month, date_debut__year=today.year).count(),
        })


class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = ParticipantEvenement.objects.select_related('evenement', 'utilisateur').order_by('nom')
    serializer_class = ParticipantSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['evenement', 'statut']
    search_fields = ['nom', 'prenom', 'email', 'organisation']

    def get_permissions(self):
        return [CanRead()] if self.action in ['list', 'retrieve'] else [CanEdit()]

    def perform_create(self, s):
        qr = str(uuid.uuid4())[:12].upper()
        s.save(qr_code=qr)


class DepenseEvenementViewSet(viewsets.ModelViewSet):
    queryset = DepenseEvenement.objects.select_related('evenement', 'saisi_par').order_by('-date_depense')
    serializer_class = DepenseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['evenement', 'categorie']

    def get_permissions(self):
        return [CanRead()] if self.action in ['list', 'retrieve'] else [CanEdit()]

    def perform_create(self, s):
        s.save(saisi_par=self.request.user)
