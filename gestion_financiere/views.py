from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import CSVDjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, Count, Q
import uuid

from accounts.permissions import HasModulePermission
from accounts.models import AuditLog

from .models import (
    Budget, RevisionBudgetaire, LigneBudgetaire,
    BudgetProjet, LigneBudgetaireLegacy, DepenseLegacy,
    Fournisseur, Depense, Avance, Engagement,
    Convention, TrancheFinancement, Cofinancement, RapportBailleur,
    PlanTresorerie, LigneTresorerie, RapportFinancier,
    CompteBancaire, MouvementBancaire, RapprochementBancaire,
)
from .serializers import (
    BudgetListSerializer, BudgetDetailSerializer,
    RevisionBudgetaireSerializer, LigneBudgetaireSerializer,
    BudgetProjetListSerializer, BudgetProjetDetailSerializer,
    LigneBudgetaireLegacySerializer, DepenseLegacySerializer,
    FournisseurSerializer,
    DepenseListSerializer, DepenseDetailSerializer,
    AvanceSerializer,
    EngagementListSerializer, EngagementDetailSerializer,
    ConventionListSerializer, ConventionDetailSerializer,
    TrancheFinancementSerializer, CofinancementSerializer,
    RapportBailleurSerializer,
    PlanTresorerieSerializer, LigneTresorerieSerializer,
    RapportFinancierSerializer,
    CompteBancaireSerializer, MouvementBancaireSerializer,
    RapprochementBancaireSerializer,
)


CanReadFin = HasModulePermission.for_module('gestion_financiere', 'peut_lire')
CanEditFin = HasModulePermission.for_module('gestion_financiere', 'peut_modifier')
CanValidateFin = HasModulePermission.for_module('gestion_financiere', 'peut_valider')


# ─── M21 : Budget ─────────────────────────────────────────────────────────────

class BudgetViewSet(viewsets.ModelViewSet):
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['reference', 'intitule', 'projet__titre', 'programme__intitule']
    ordering_fields = ['exercice', 'montant_initial', 'created_at']
    filterset_fields = ['statut', 'type_budget', 'exercice', 'devise']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action in ['valider', 'approuver']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return Budget.objects.select_related(
            'projet', 'programme', 'created_by', 'soumis_par', 'valide_finance_par', 'approuve_par'
        ).prefetch_related('lignes', 'revisions').order_by('-exercice', '-created_at')

    def get_serializer_class(self):
        return BudgetListSerializer if self.action == 'list' else BudgetDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        budget = self.get_object()
        if budget.statut != 'draft':
            return Response({'detail': 'Seul un brouillon peut etre soumis.'}, status=400)
        budget.statut = 'soumis'
        budget.save(update_fields=['statut'])
        AuditLog.log(request.user, 'soumettre', module='gestion_financiere', objet_type='Budget', objet_id=str(budget.pk), objet_repr=str(budget))
        return Response(BudgetDetailSerializer(budget).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        budget = self.get_object()
        if budget.statut != 'soumis':
            return Response({'detail': 'Seul un budget soumis peut etre valide.'}, status=400)
        budget.statut = 'valide'
        budget.valide_par = request.user
        budget.date_validation = timezone.now().date()
        budget.save(update_fields=['statut', 'valide_par', 'date_validation'])
        AuditLog.log(request.user, 'valider', module='gestion_financiere', objet_type='Budget', objet_id=str(budget.pk), objet_repr=str(budget))
        return Response(BudgetDetailSerializer(budget).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        budget = self.get_object()
        motif = request.data.get('motif', '')
        budget.statut = 'rejete'
        budget.notes = motif
        budget.save(update_fields=['statut', 'notes'])
        return Response(BudgetDetailSerializer(budget).data)

    @action(detail=True, methods=['get'])
    def execution(self, request, pk=None):
        budget = self.get_object()
        lignes = budget.lignes.all()
        data = {
            'budget_id': budget.id,
            'reference': budget.reference,
            'montant_initial': budget.montant_initial,
            'montant_engage': budget.montant_engage,
            'montant_depense': budget.montant_depense,
            'taux_execution': budget.taux_execution,
            'taux_engagement': budget.taux_engagement,
            'lignes_count': lignes.count(),
            'lignes_depassees': sum(1 for l in lignes if getattr(l, 'est_depassee', False)),
        }
        return Response(data)


class LigneBudgetaireViewSet(viewsets.ModelViewSet):
    serializer_class = LigneBudgetaireSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['code', 'libelle']
    ordering_fields = ['code', 'montant_prevu', 'ordre']
    filterset_fields = ['budget', 'categorie', 'activite']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return LigneBudgetaire.objects.select_related(
            'budget', 'activite'
        ).order_by('budget', 'ordre', 'code')


class RevisionBudgetaireViewSet(viewsets.ModelViewSet):
    serializer_class = RevisionBudgetaireSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['motif']
    ordering_fields = ['date_revision', 'numero_revision']
    filterset_fields = ['budget']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanValidateFin()]

    def get_queryset(self):
        return RevisionBudgetaire.objects.select_related(
            'budget', 'valide_par'
        ).order_by('-date_revision')

    def perform_create(self, serializer):
        serializer.save(valide_par=self.request.user)


# ─── BudgetProjet (legacy) ────────────────────────────────────────────────────

class BudgetProjetViewSet(viewsets.ModelViewSet):
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['projet__titre', 'projet__code']
    ordering_fields = ['exercice', 'montant_initial', 'created_at']
    filterset_fields = ['statut', 'exercice']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action in ['approuver']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return BudgetProjet.objects.select_related(
            'projet', 'approuve_par'
        ).prefetch_related('lignes').order_by('-exercice')

    def get_serializer_class(self):
        return BudgetProjetListSerializer if self.action == 'list' else BudgetProjetDetailSerializer

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        budget = self.get_object()
        if budget.statut != 'draft':
            return Response({'detail': 'Seul un brouillon peut etre soumis.'}, status=400)
        budget.statut = 'soumis'
        budget.save(update_fields=['statut'])
        return Response(BudgetProjetDetailSerializer(budget).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        budget = self.get_object()
        if budget.statut != 'soumis':
            return Response({'detail': 'Seul un budget soumis peut etre approuve.'}, status=400)
        budget.statut = 'approuve'
        budget.approuve_par = request.user
        budget.date_approbation = timezone.now().date()
        budget.save(update_fields=['statut', 'approuve_par', 'date_approbation'])
        return Response(BudgetProjetDetailSerializer(budget).data)


# ─── LigneBudgetaireLegacy ────────────────────────────────────────────────────

class LigneBudgetaireLegacyViewSet(viewsets.ModelViewSet):
    serializer_class = LigneBudgetaireLegacySerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['code', 'libelle']
    ordering_fields = ['code', 'montant_prevu']
    filterset_fields = ['budget']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return LigneBudgetaireLegacy.objects.select_related('budget').order_by('code')


# ─── DepenseLegacy ────────────────────────────────────────────────────────────

class DepenseLegacyViewSet(viewsets.ModelViewSet):
    serializer_class = DepenseLegacySerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['reference', 'libelle', 'fournisseur']
    ordering_fields = ['date_depense', 'montant']
    filterset_fields = ['statut', 'ligne']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action == 'approuver':
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return DepenseLegacy.objects.select_related(
            'ligne', 'saisi_par', 'approuve_par'
        ).order_by('-date_depense')

    def perform_create(self, serializer):
        ref = f"DEP-{timezone.now().year}-{str(uuid.uuid4())[:8].upper()}"
        serializer.save(saisi_par=self.request.user, reference=ref)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        dep = self.get_object()
        if dep.statut != 'soumis':
            return Response({'detail': 'Seule une depense soumise peut etre approuvee.'}, status=400)
        dep.statut = 'approuve'
        dep.approuve_par = request.user
        dep.date_approbation = timezone.now()
        dep.save(update_fields=['statut', 'approuve_par', 'date_approbation'])
        return Response(DepenseLegacySerializer(dep).data)


# ─── M22 : Depenses & Fournisseurs ────────────────────────────────────────────

class FournisseurViewSet(viewsets.ModelViewSet):
    serializer_class = FournisseurSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nom', 'code', 'numero_contribuable', 'email']
    ordering_fields = ['nom', 'created_at']
    filterset_fields = ['type_fournisseur', 'actif', 'pays']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return Fournisseur.objects.order_by('nom')


class DepenseViewSet(viewsets.ModelViewSet):
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['reference', 'libelle', 'fournisseur__nom']
    ordering_fields = ['date_depense', 'montant', 'created_at']
    filterset_fields = ['statut', 'type_depense', 'ligne_budgetaire', 'fournisseur']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action in ['valider', 'approuver']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return Depense.objects.select_related(
            'ligne_budgetaire', 'fournisseur', 'saisi_par', 'valide_responsable_par',
            'valide_finance_par', 'approuve_par'
        ).order_by('-date_depense')

    def get_serializer_class(self):
        return DepenseListSerializer if self.action == 'list' else DepenseDetailSerializer

    def perform_create(self, serializer):
        serializer.save(saisi_par=self.request.user)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        dep = self.get_object()
        if dep.statut != 'brouillon':
            return Response({'detail': 'Seul un brouillon peut etre soumis.'}, status=400)
        dep.statut = 'soumis'
        dep.save(update_fields=['statut'])
        return Response(DepenseDetailSerializer(dep).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        dep = self.get_object()
        if dep.statut != 'soumis':
            return Response({'detail': 'Seule une depense soumise peut etre validee.'}, status=400)
        dep.statut = 'valide'
        dep.valide_par = request.user
        dep.date_validation = timezone.now()
        dep.save(update_fields=['statut', 'valide_par', 'date_validation'])
        AuditLog.log(request.user, 'valider', module='gestion_financiere', objet_type='Depense', objet_id=str(dep.pk), objet_repr=str(dep))
        return Response(DepenseDetailSerializer(dep).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        dep = self.get_object()
        if dep.statut != 'valide':
            return Response({'detail': 'Seule une depense validee peut etre approuvee.'}, status=400)
        dep.statut = 'approuve'
        dep.approuve_par = request.user
        dep.date_approbation = timezone.now()
        dep.save(update_fields=['statut', 'approuve_par', 'date_approbation'])
        AuditLog.log(request.user, 'approuver', module='gestion_financiere', objet_type='Depense', objet_id=str(dep.pk), objet_repr=str(dep))
        return Response(DepenseDetailSerializer(dep).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        dep = self.get_object()
        motif = request.data.get('motif', '')
        dep.statut = 'rejete'
        dep.motif_rejet = motif
        dep.save(update_fields=['statut', 'motif_rejet'])
        return Response(DepenseDetailSerializer(dep).data)


class AvanceViewSet(viewsets.ModelViewSet):
    serializer_class = AvanceSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['reference', 'beneficiaire__last_name', 'beneficiaire__first_name']
    ordering_fields = ['date_accord', 'montant', 'created_at']
    filterset_fields = ['statut', 'beneficiaire']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action in ['approuver']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return Avance.objects.select_related('beneficiaire', 'fournisseur', 'accorde_par').order_by('-date_accord')

    def perform_create(self, serializer):
        serializer.save(accorde_par=self.request.user)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        avance = self.get_object()
        avance.statut = 'approuve'
        avance.approuve_par = request.user
        avance.save(update_fields=['statut', 'approuve_par'])
        return Response(AvanceSerializer(avance).data)

    @action(detail=True, methods=['post'])
    def rembourser(self, request, pk=None):
        avance = self.get_object()
        montant = request.data.get('montant_rembourse', 0)
        avance.montant_rembourse = float(avance.montant_rembourse or 0) + float(montant)
        if float(avance.montant_rembourse) >= float(avance.montant):
            avance.statut = 'rembourse'
        avance.save(update_fields=['montant_rembourse', 'statut'])
        return Response(AvanceSerializer(avance).data)


class EngagementViewSet(viewsets.ModelViewSet):
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['reference', 'libelle', 'fournisseur__nom']
    ordering_fields = ['date_engagement', 'montant', 'created_at']
    filterset_fields = ['statut', 'type_engagement', 'ligne_budgetaire', 'fournisseur']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action in ['valider']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return Engagement.objects.select_related(
            'ligne_budgetaire', 'fournisseur', 'created_by', 'valide_par'
        ).order_by('-date_engagement')

    def get_serializer_class(self):
        return EngagementListSerializer if self.action == 'list' else EngagementDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        eng = self.get_object()
        eng.statut = 'valide'
        eng.valide_par = request.user
        eng.date_validation = timezone.now()
        eng.save(update_fields=['statut', 'valide_par', 'date_validation'])
        AuditLog.log(request.user, 'valider', module='gestion_financiere', objet_type='Engagement', objet_id=str(eng.pk), objet_repr=str(eng))
        return Response(EngagementDetailSerializer(eng).data)

    @action(detail=True, methods=['post'])
    def liquider(self, request, pk=None):
        eng = self.get_object()
        montant = request.data.get('montant_liquide', 0)
        eng.montant_liquide = float(eng.montant_liquide or 0) + float(montant)
        if float(eng.montant_liquide) >= float(eng.montant_engage):
            eng.statut = 'liquide'
        eng.save(update_fields=['montant_liquide', 'statut'])
        return Response(EngagementDetailSerializer(eng).data)


# ─── M23 : Conventions & Financements ─────────────────────────────────────────

class ConventionViewSet(viewsets.ModelViewSet):
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['reference', 'intitule', 'bailleur__nom']
    ordering_fields = ['date_signature', 'montant_total', 'created_at']
    filterset_fields = ['statut', 'type_convention', 'devise']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action in ['valider', 'approuver']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return Convention.objects.select_related('bailleur', 'programme', 'projet', 'responsable', 'created_by').order_by('-date_signature')

    def get_serializer_class(self):
        return ConventionListSerializer if self.action == 'list' else ConventionDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        convention = self.get_object()
        convention.statut = 'active'
        convention.save(update_fields=['statut'])
        AuditLog.log(request.user, 'valider', module='gestion_financiere', objet_type='Convention', objet_id=str(convention.pk), objet_repr=str(convention))
        return Response(ConventionDetailSerializer(convention).data)


class TrancheFinancementViewSet(viewsets.ModelViewSet):
    serializer_class = TrancheFinancementSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['date_prevue', 'montant_prevu']
    filterset_fields = ['convention', 'statut']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return TrancheFinancement.objects.select_related('convention').order_by('date_prevue')

    @action(detail=True, methods=['post'])
    def recevoir(self, request, pk=None):
        tranche = self.get_object()
        tranche.statut = 'recue'
        tranche.date_reception = timezone.now().date()
        tranche.save(update_fields=['statut', 'date_reception'])
        return Response(TrancheFinancementSerializer(tranche).data)


class CofinancementViewSet(viewsets.ModelViewSet):
    serializer_class = CofinancementSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['montant', 'montant_recu']
    filterset_fields = ['convention', 'bailleur']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return Cofinancement.objects.select_related('convention', 'bailleur').order_by('convention')


class RapportBailleurViewSet(viewsets.ModelViewSet):
    serializer_class = RapportBailleurSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['titre', 'reference']
    ordering_fields = ['date_soumission_prevue', 'periode_debut']
    filterset_fields = ['convention', 'statut', 'type_rapport']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return RapportBailleur.objects.select_related('convention', 'redacteur').order_by('-date_soumission_prevue')

    def perform_create(self, serializer):
        serializer.save(redige_par=self.request.user)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        rapport = self.get_object()
        rapport.statut = 'soumis'
        rapport.date_soumission = timezone.now().date()
        rapport.save(update_fields=['statut', 'date_soumission'])
        return Response(RapportBailleurSerializer(rapport).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        rapport = self.get_object()
        rapport.statut = 'approuve'
        rapport.save(update_fields=['statut'])
        return Response(RapportBailleurSerializer(rapport).data)


# ─── Tresorerie ───────────────────────────────────────────────────────────────

class PlanTresorerieViewSet(viewsets.ModelViewSet):
    serializer_class = PlanTresorerieSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['notes']
    ordering_fields = ['exercice', 'created_at']
    filterset_fields = ['exercice', 'projet', 'programme']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return PlanTresorerie.objects.select_related('projet', 'programme', 'created_by').order_by('-exercice')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class LigneTresorerieViewSet(viewsets.ModelViewSet):
    serializer_class = LigneTresorerieSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['mois', 'montant_prevu']
    filterset_fields = ['plan', 'mois']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return LigneTresorerie.objects.select_related('plan').order_by('plan', 'mois')


# ─── Comptes bancaires ────────────────────────────────────────────────────────

class CompteBancaireViewSet(viewsets.ModelViewSet):
    serializer_class = CompteBancaireSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['numero_compte', 'banque', 'intitule']
    ordering_fields = ['banque', 'created_at']
    filterset_fields = ['actif', 'devise', 'type_compte']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return CompteBancaire.objects.select_related('projet', 'programme').order_by('banque', 'intitule')


class MouvementBancaireViewSet(viewsets.ModelViewSet):
    serializer_class = MouvementBancaireSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['reference_externe', 'libelle']
    ordering_fields = ['date_operation', 'montant']
    filterset_fields = ['compte', 'type_mouvement', 'rapproche']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanEditFin()]

    def get_queryset(self):
        return MouvementBancaire.objects.select_related('compte', 'saisi_par').order_by('-date_operation')

    def perform_create(self, serializer):
        serializer.save(saisi_par=self.request.user)


class RapprochementBancaireViewSet(viewsets.ModelViewSet):
    serializer_class = RapprochementBancaireSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['periode_fin', 'created_at']
    filterset_fields = ['compte', 'statut']

    def get_permissions(self):
        return [CanReadFin()] if self.action in ['list', 'retrieve'] else [CanValidateFin()]

    def get_queryset(self):
        return RapprochementBancaire.objects.select_related(
            'compte', 'effectue_par'
        ).order_by('-periode_fin')

    def perform_create(self, serializer):
        serializer.save(effectue_par=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        rappr = self.get_object()
        rappr.statut = 'valide'
        rappr.save(update_fields=['statut'])
        AuditLog.log(request.user, 'valider', module='gestion_financiere', objet_type='RapprochementBancaire', objet_id=str(rappr.pk), objet_repr=str(rappr))
        return Response(RapprochementBancaireSerializer(rappr).data)


# ─── Rapports financiers ──────────────────────────────────────────────────────

class RapportFinancierViewSet(viewsets.ModelViewSet):
    serializer_class = RapportFinancierSerializer
    filter_backends = [CSVDjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['titre', 'reference']
    ordering_fields = ['date_rapport', 'created_at']
    filterset_fields = ['type_rapport', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        return [CanEditFin()]

    def get_queryset(self):
        return RapportFinancier.objects.select_related(
            'projet', 'programme', 'redacteur'
        ).order_by('-date_rapport')

    def perform_create(self, serializer):
        serializer.save(redacteur=self.request.user)


# ─── Dashboards & fonctions specifiques ──────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_financier(request):
    """Indicateurs du tableau de bord DG. Filtre optionnel : ?programme=<id>&projet=<id>&exercice=<annee>."""
    budgets = Budget.objects.filter(statut__in=['approuve', 'en_execution'])
    conventions = Convention.objects.filter(statut='active')
    for param, champ in (('programme', 'programme_id'), ('projet', 'projet_id'), ('exercice', 'exercice')):
        valeur = request.query_params.get(param)
        if valeur and (param == 'exercice' or hasattr(Convention, champ.replace('_id', ''))):
            budgets = budgets.filter(**{champ: valeur})
            if param != 'exercice':
                conventions = conventions.filter(**{champ: valeur})

    total_initial = budgets.aggregate(t=Sum('montant_initial'))['t'] or 0
    total_depense = budgets.aggregate(t=Sum('montant_depense'))['t'] or 0
    total_engage = budgets.aggregate(t=Sum('montant_engage'))['t'] or 0
    taux = round(float(total_depense) / float(total_initial) * 100, 1) if total_initial else 0

    conv = conventions.aggregate(total=Sum('montant_total'), recu=Sum('montant_recu'))
    conv_total, conv_recu = conv['total'] or 0, conv['recu'] or 0
    taux_decaissement = round(float(conv_recu) / float(conv_total) * 100, 1) if conv_total else 0

    return Response({
        # clés lues par le tableau de bord
        'budget_total': total_initial,
        'engage_total': total_engage,
        'depense_total': total_depense,
        'budget': {'taux_execution': taux, 'total': total_initial, 'engage': total_engage, 'depense': total_depense},
        'financements': {
            'total_recu': conv_recu, 'total_convenu': conv_total,
            'taux_decaissement': taux_decaissement, 'conventions_actives': conventions.count(),
        },
        # clés historiques
        'budgets_valides': budgets.count(),
        'montant_total_initial': total_initial,
        'montant_total_depense': total_depense,
        'montant_total_engage': total_engage,
        'taux_execution_global': taux,
        'depenses_en_attente': Depense.objects.filter(statut='soumis').count(),
        'engagements_actifs': Engagement.objects.filter(statut__in=['approuve', 'en_cours']).count(),
        'conventions_actives': conventions.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_tresorerie(request):
    """Trésorerie : comptes, mouvements récents, flux prévus du mois courant et cumul de l'exercice."""
    today = timezone.now().date()
    comptes = CompteBancaire.objects.filter(actif=True)
    mouvements_recents = MouvementBancaire.objects.order_by('-date_operation')[:10]

    def flux(qs):
        entrees = qs.filter(type_flux='entrant').aggregate(t=Sum('montant_prevu'))['t'] or 0
        sorties = qs.filter(type_flux='sortant').aggregate(t=Sum('montant_prevu'))['t'] or 0
        return {'entrees': entrees, 'sorties': sorties, 'solde': entrees - sorties}

    lignes = LigneTresorerie.objects.filter(annee=today.year)
    return Response({
        'comptes_actifs': comptes.count(),
        'solde_total': comptes.aggregate(t=Sum('solde_actuel'))['t'] or 0,
        'mouvements_recents_count': mouvements_recents.count(),
        'mois': flux(lignes.filter(mois=today.month)),
        'cumul': flux(lignes.filter(mois__lte=today.month)),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analyse_ia_financiere(request):
    return Response({
        'message': 'Analyse IA financiere en cours de developpement.',
        'statut': 'beta',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def depassements_budgetaires(request):
    """Lignes budgétaires dont l'engagé dépasse le prévu. Filtres : ?exercice=&projet=&programme="""
    lignes = LigneBudgetaire.objects.filter(montant_engage__gt=0).select_related('budget', 'budget__projet')
    for param, champ in (('exercice', 'budget__exercice'), ('projet', 'budget__projet_id'), ('programme', 'budget__programme_id')):
        if request.query_params.get(param):
            lignes = lignes.filter(**{champ: request.query_params[param]})
    data = []
    for l in lignes:
        if l.est_depassee:
            data.append({
                'id': l.id,
                'code': l.code,
                'libelle': l.libelle,
                'budget': l.budget.reference if l.budget else None,
                'budget_reference': l.budget.reference if l.budget else None,
                'projet': getattr(l.budget.projet, 'code', None) if l.budget and l.budget.projet else None,
                'montant_prevu': l.montant_prevu,
                'montant_engage': l.montant_engage,
                'montant_depense': l.montant_depense,
                'ecart': l.montant_engage - l.montant_prevu,
            })
    return Response({
        'count': len(data),
        'nb_depassements': len(data),
        'montant_total_ecart': sum(d['ecart'] for d in data),
        'lignes': data,
        'results': data,
    })
