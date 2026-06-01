from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.models import AuditLog
from accounts.permissions import HasModulePermission
from .models import (
    Budget, RevisionBudgetaire, LigneBudgetaire,
    Fournisseur, Depense, Avance, Engagement,
    Convention, TrancheFinancement, Cofinancement, RapportBailleur,
    PlanTresorerie, LigneTresorerie, RapportFinancier,
    CompteBancaire, MouvementBancaire, RapprochementBancaire,
)
from .serializers import (
    BudgetListSerializer, BudgetDetailSerializer,
    RevisionBudgetaireSerializer, LigneBudgetaireSerializer,
    FournisseurSerializer,
    DepenseListSerializer, DepenseDetailSerializer,
    AvanceSerializer, EngagementListSerializer, EngagementDetailSerializer,
    ConventionListSerializer, ConventionDetailSerializer,
    TrancheFinancementSerializer, CofinancementSerializer,
    RapportBailleurSerializer, PlanTresorerieSerializer,
    LigneTresorerieSerializer, RapportFinancierSerializer,
    CompteBancaireSerializer, MouvementBancaireSerializer, RapprochementBancaireSerializer,
)
from .filters import (
    BudgetFilter, LigneBudgetaireFilter, DepenseFilter, AvanceFilter,
    EngagementFilter, FournisseurFilter, ConventionFilter,
    RapportBailleurFilter, RapportFinancierFilter,
)

CanReadFin = HasModulePermission.for_module('gestion_financiere', 'peut_lire')
CanEditFin = HasModulePermission.for_module('gestion_financiere', 'peut_modifier')
CanValidateFin = HasModulePermission.for_module('gestion_financiere', 'peut_valider')


# ─── M21 : Budget ────────────────────────────────────────────────────────────

class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.select_related(
        'projet', 'programme', 'approuve_par', 'created_by'
    ).prefetch_related('lignes', 'revisions').order_by('-exercice', '-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BudgetFilter
    search_fields = ['reference', 'intitule']
    ordering_fields = ['exercice', 'montant_initial', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'execution', 'tableau_bord']:
            return [CanReadFin()]
        if self.action in ['approuver', 'valider_finance', 'valider_direction']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_serializer_class(self):
        return BudgetListSerializer if self.action == 'list' else BudgetDetailSerializer

    def perform_create(self, s):
        b = s.save(created_by=self.request.user)
        AuditLog.log(self.request.user, 'create', module='gestion_financiere',
                     objet_type='Budget', objet_id=b.id, request=self.request)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        b = self.get_object()
        if b.statut != 'preparation':
            return Response({'detail': 'Seul un budget en préparation peut être soumis.'}, status=400)
        b.soumettre(request.user)
        return Response(BudgetDetailSerializer(b).data)

    @action(detail=True, methods=['post'])
    def valider_finance(self, request, pk=None):
        b = self.get_object()
        if b.statut != 'soumis':
            return Response({'detail': 'Statut incompatible.'}, status=400)
        b.valider_finance(request.user)
        return Response(BudgetDetailSerializer(b).data)

    @action(detail=True, methods=['post'])
    def valider_direction(self, request, pk=None):
        b = self.get_object()
        b.statut = 'validation_direction'
        b.save(update_fields=['statut'])
        return Response(BudgetDetailSerializer(b).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        b = self.get_object()
        b.approuver(request.user)
        return Response(BudgetDetailSerializer(b).data)

    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        b = self.get_object()
        if b.statut not in ('approuve',):
            return Response({'detail': 'Le budget doit être approuvé.'}, status=400)
        b.activer()
        return Response(BudgetDetailSerializer(b).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        b = self.get_object()
        b.statut = 'preparation'
        b.motif_rejet = request.data.get('motif', '')
        b.save(update_fields=['statut', 'motif_rejet'])
        return Response(BudgetDetailSerializer(b).data)

    @action(detail=True, methods=['post'])
    def dupliquer(self, request, pk=None):
        b = self.get_object()
        exercice = request.data.get('exercice')
        if not exercice:
            return Response({'detail': 'exercice requis.'}, status=400)
        nouveau = b.dupliquer(int(exercice), request.user)
        return Response(BudgetDetailSerializer(nouveau).data, status=201)

    @action(detail=True, methods=['post'])
    def reviser(self, request, pk=None):
        b = self.get_object()
        nouveau_montant = request.data.get('montant')
        motif = request.data.get('motif', '')
        if not nouveau_montant:
            return Response({'detail': 'montant requis.'}, status=400)
        num = b.revisions.count() + 1
        RevisionBudgetaire.objects.create(
            budget=b, numero_revision=num, motif=motif,
            montant_avant=b.montant_revise or b.montant_initial,
            montant_apres=nouveau_montant, valide_par=request.user,
        )
        b.montant_revise = nouveau_montant
        b.statut = 'revise'
        b.save(update_fields=['montant_revise', 'statut'])
        return Response(BudgetDetailSerializer(b).data)

    @action(detail=True, methods=['get'])
    def execution(self, request, pk=None):
        b = self.get_object()
        lignes = b.lignes.all()
        return Response({
            'budget': {'reference': b.reference, 'montant_actuel': float(b.montant_actuel),
                       'taux_execution': b.taux_execution, 'taux_engagement': b.taux_engagement},
            'lignes': LigneBudgetaireSerializer(lignes, many=True).data,
            'alertes': [
                {'code': l.code, 'libelle': l.libelle, 'taux': l.taux_consommation}
                for l in lignes if l.est_depassee
            ],
        })

    @action(detail=False, methods=['get'])
    def tableau_bord(self, request):
        projet_id = request.query_params.get('projet')
        exercice = request.query_params.get('exercice', timezone.now().year)
        qs = Budget.objects.filter(exercice=exercice)
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        total_budget = qs.aggregate(s=Sum('montant_initial'))['s'] or 0
        total_depense = qs.aggregate(s=Sum('montant_depense'))['s'] or 0
        total_engage = qs.aggregate(s=Sum('montant_engage'))['s'] or 0
        return Response({
            'exercice': exercice,
            'total_budgets': qs.count(),
            'budget_total': float(total_budget),
            'depense_total': float(total_depense),
            'engage_total': float(total_engage),
            'taux_execution': round(float(total_depense) / float(total_budget) * 100, 1) if total_budget else 0,
            'par_statut': {s: qs.filter(statut=s).count() for s, _ in Budget.STATUT_CHOICES},
        })


class LigneBudgetaireViewSet(viewsets.ModelViewSet):
    queryset = LigneBudgetaire.objects.select_related('budget', 'activite').order_by('code')
    serializer_class = LigneBudgetaireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = LigneBudgetaireFilter
    search_fields = ['code', 'libelle']
    permission_classes = [CanEditFin]

    def get_queryset(self):
        qs = super().get_queryset()
        b = self.request.query_params.get('budget')
        return qs.filter(budget_id=b) if b else qs


class RevisionBudgetaireViewSet(viewsets.ModelViewSet):
    queryset = RevisionBudgetaire.objects.order_by('budget', 'numero_revision')
    serializer_class = RevisionBudgetaireSerializer
    permission_classes = [CanReadFin]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        b = self.request.query_params.get('budget')
        return qs.filter(budget_id=b) if b else qs

    def perform_create(self, s):
        s.save(valide_par=self.request.user)


# ─── M22 : Fournisseurs ───────────────────────────────────────────────────────

class FournisseurViewSet(viewsets.ModelViewSet):
    queryset = Fournisseur.objects.order_by('nom')
    serializer_class = FournisseurSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FournisseurFilter
    search_fields = ['code', 'nom', 'email', 'telephone']
    ordering_fields = ['nom', 'created_at']
    permission_classes = [CanReadFin]

    @action(detail=True, methods=['get'])
    def historique_depenses(self, request, pk=None):
        f = self.get_object()
        depenses = f.depenses.order_by('-date_depense')[:20]
        return Response({
            'fournisseur': f.nom,
            'total_depenses': float(f.depenses.filter(statut='paye').aggregate(
                s=Sum('montant'))['s'] or 0),
            'nb_depenses': f.depenses.count(),
            'depenses': DepenseListSerializer(depenses, many=True).data,
        })


# ─── M22 : Dépenses ───────────────────────────────────────────────────────────

class DepenseViewSet(viewsets.ModelViewSet):
    queryset = Depense.objects.select_related(
        'ligne_budgetaire', 'projet', 'activite', 'fournisseur', 'saisi_par', 'approuve_par'
    ).order_by('-date_depense')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DepenseFilter
    search_fields = ['reference', 'libelle', 'numero_piece']
    ordering_fields = ['date_depense', 'montant', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action in ['approuver', 'valider_responsable', 'valider_finance', 'rejeter']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_serializer_class(self):
        return DepenseListSerializer if self.action == 'list' else DepenseDetailSerializer

    def perform_create(self, s):
        dep = s.save(saisi_par=self.request.user)
        AuditLog.log(self.request.user, 'create', module='gestion_financiere',
                     objet_type='Depense', objet_id=dep.id, request=self.request)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        d = self.get_object()
        if d.statut != 'brouillon':
            return Response({'detail': 'Seul un brouillon peut être soumis.'}, status=400)
        d.soumettre()
        return Response(DepenseDetailSerializer(d).data)

    @action(detail=True, methods=['post'])
    def valider_responsable(self, request, pk=None):
        d = self.get_object()
        d.valider_responsable(request.user)
        return Response(DepenseDetailSerializer(d).data)

    @action(detail=True, methods=['post'])
    def valider_finance(self, request, pk=None):
        d = self.get_object()
        d.valider_finance(request.user)
        return Response(DepenseDetailSerializer(d).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        d = self.get_object()
        if d.ligne_budgetaire and d.montant > d.ligne_budgetaire.solde_disponible:
            autorisation = request.data.get('autorisation_depassement', False)
            if not autorisation:
                return Response({
                    'detail': 'Budget insuffisant. Fournissez autorisation_depassement=true pour forcer.',
                    'solde_disponible': float(d.ligne_budgetaire.solde_disponible),
                    'montant_depense': float(d.montant),
                }, status=400)
        d.approuver(request.user)
        return Response(DepenseDetailSerializer(d).data)

    @action(detail=True, methods=['post'])
    def marquer_paye(self, request, pk=None):
        d = self.get_object()
        if d.statut != 'approuve':
            return Response({'detail': 'La dépense doit être approuvée.'}, status=400)
        d.marquer_paye(
            date_paiement=request.data.get('date_paiement'),
            mode=request.data.get('mode_paiement'),
        )
        return Response(DepenseDetailSerializer(d).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        d = self.get_object()
        d.rejeter(request.user, request.data.get('motif', ''))
        return Response(DepenseDetailSerializer(d).data)

    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        projet_id = request.query_params.get('projet')
        qs = Depense.objects.filter(statut='paye')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        result = qs.values('type_depense').annotate(
            total=Sum('montant'), nb=Count('id')
        ).order_by('-total')
        return Response(list(result))

    @action(detail=False, methods=['get'])
    def evolution_mensuelle(self, request):
        projet_id = request.query_params.get('projet')
        annee = int(request.query_params.get('annee', timezone.now().year))
        qs = Depense.objects.filter(statut='paye', date_depense__year=annee)
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        from django.db.models.functions import TruncMonth
        result = qs.annotate(mois=TruncMonth('date_depense')).values('mois').annotate(
            total=Sum('montant'), nb=Count('id')
        ).order_by('mois')
        return Response([{
            'mois': r['mois'].strftime('%Y-%m'), 'total': float(r['total']), 'nb': r['nb']
        } for r in result])


# ─── Avances ─────────────────────────────────────────────────────────────────

class AvanceViewSet(viewsets.ModelViewSet):
    queryset = Avance.objects.select_related(
        'beneficiaire', 'fournisseur', 'projet', 'accorde_par'
    ).order_by('-date_accord')
    serializer_class = AvanceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = AvanceFilter
    search_fields = ['reference', 'motif']
    permission_classes = [CanReadFin]

    def perform_create(self, s):
        s.save(accorde_par=self.request.user)

    @action(detail=True, methods=['post'])
    def justifier(self, request, pk=None):
        a = self.get_object()
        montant = float(request.data.get('montant', 0))
        a.montant_justifie += montant
        if a.montant_justifie >= a.montant:
            a.statut = 'justifiee'
        else:
            a.statut = 'partiellement_justifiee'
        a.save(update_fields=['montant_justifie', 'statut'])
        return Response(AvanceSerializer(a).data)

    @action(detail=True, methods=['post'])
    def rembourser(self, request, pk=None):
        a = self.get_object()
        montant = float(request.data.get('montant', 0))
        a.montant_rembourse += montant
        if a.montant_justifie + a.montant_rembourse >= a.montant:
            a.statut = 'remboursee'
        a.save(update_fields=['montant_rembourse', 'statut'])
        return Response(AvanceSerializer(a).data)

    @action(detail=False, methods=['get'])
    def en_cours(self, request):
        qs = Avance.objects.filter(
            statut__in=['accordee', 'partiellement_justifiee', 'non_justifiee']
        ).order_by('date_limite_justification')
        return Response(AvanceSerializer(qs, many=True).data)


# ─── Engagements ─────────────────────────────────────────────────────────────

class EngagementViewSet(viewsets.ModelViewSet):
    queryset = Engagement.objects.select_related(
        'ligne_budgetaire', 'fournisseur', 'approuve_par', 'created_by'
    ).order_by('-date_engagement')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EngagementFilter
    search_fields = ['reference', 'libelle']
    ordering_fields = ['date_engagement', 'montant', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadFin()]
        if self.action in ['approuver']:
            return [CanValidateFin()]
        return [CanEditFin()]

    def get_serializer_class(self):
        return EngagementListSerializer if self.action == 'list' else EngagementDetailSerializer

    def perform_create(self, s):
        e = s.save(created_by=self.request.user)
        AuditLog.log(self.request.user, 'create', module='gestion_financiere',
                     objet_type='Engagement', objet_id=e.id, request=self.request)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        e = self.get_object()
        e.statut = 'soumis'
        e.save(update_fields=['statut'])
        return Response(EngagementDetailSerializer(e).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        e = self.get_object()
        e.statut = 'valide'
        e.valide_par = request.user
        e.save(update_fields=['statut', 'valide_par'])
        return Response(EngagementDetailSerializer(e).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        e = self.get_object()
        if e.statut not in ('soumis', 'valide'):
            return Response({'detail': 'Statut incompatible.'}, status=400)
        e.approuver(request.user)
        return Response(EngagementDetailSerializer(e).data)

    @action(detail=True, methods=['post'])
    def liquider(self, request, pk=None):
        """Liquidation : constatation du service fait et validation du montant."""
        e = self.get_object()
        if e.statut not in ('approuve', 'en_cours'):
            return Response({'detail': 'Statut incompatible pour la liquidation.'}, status=400)
        montant = float(request.data.get('montant', 0))
        if montant <= 0:
            return Response({'detail': 'Montant invalide.'}, status=400)
        e.liquider(montant)
        AuditLog.log(request.user, 'update', module='gestion_financiere',
                     objet_type='Engagement', objet_id=e.id, request=request)
        return Response(EngagementDetailSerializer(e).data)

    @action(detail=True, methods=['post'])
    def ordonner(self, request, pk=None):
        """Ordonnancement : émission de l'ordre de paiement à la comptabilité."""
        e = self.get_object()
        if e.statut != 'liquide':
            return Response({'detail': 'La liquidation doit être complète avant l\'ordonnancement.'}, status=400)
        e.ordonner(request.user)
        AuditLog.log(request.user, 'update', module='gestion_financiere',
                     objet_type='Engagement', objet_id=e.id, request=request)
        return Response(EngagementDetailSerializer(e).data)

    @action(detail=True, methods=['post'])
    def marquer_paye(self, request, pk=None):
        """Paiement : exécution effective du règlement."""
        e = self.get_object()
        if e.statut != 'ordonnance':
            return Response({'detail': 'L\'engagement doit être ordonné avant le paiement.'}, status=400)
        date_paiement = request.data.get('date_paiement')
        e.marquer_paye(request.user, date_paiement)
        AuditLog.log(request.user, 'update', module='gestion_financiere',
                     objet_type='Engagement', objet_id=e.id, request=request)
        return Response(EngagementDetailSerializer(e).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        e = self.get_object()
        e.statut = 'annule'
        e.motif_annulation = request.data.get('motif', '')
        e.save(update_fields=['statut', 'motif_annulation'])
        return Response(EngagementDetailSerializer(e).data)


# ─── M23 : Conventions ────────────────────────────────────────────────────────

class ConventionViewSet(viewsets.ModelViewSet):
    queryset = Convention.objects.select_related(
        'bailleur', 'programme', 'projet', 'responsable', 'created_by'
    ).prefetch_related('tranches', 'cofinancements').order_by('-date_signature')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ConventionFilter
    search_fields = ['reference', 'intitule']
    ordering_fields = ['date_signature', 'montant_total', 'taux_decaissement']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'suivi_decaissement']:
            return [CanReadFin()]
        return [CanEditFin()]

    def get_serializer_class(self):
        return ConventionListSerializer if self.action == 'list' else ConventionDetailSerializer

    def perform_create(self, s):
        c = s.save(created_by=self.request.user)
        AuditLog.log(self.request.user, 'create', module='gestion_financiere',
                     objet_type='Convention', objet_id=c.id, request=self.request)

    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        c = self.get_object()
        c.statut = 'active'
        c.save(update_fields=['statut'])
        return Response(ConventionDetailSerializer(c).data)

    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        c = self.get_object()
        c.statut = 'suspendue'
        c.save(update_fields=['statut'])
        return Response(ConventionDetailSerializer(c).data)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        c = self.get_object()
        c.statut = 'cloturee'
        c.save(update_fields=['statut'])
        return Response(ConventionDetailSerializer(c).data)

    @action(detail=True, methods=['get'])
    def suivi_decaissement(self, request, pk=None):
        c = self.get_object()
        tranches = c.tranches.order_by('numero')
        return Response({
            'convention': c.intitule,
            'montant_total': float(c.montant_total),
            'montant_recu': float(c.montant_recu),
            'montant_restant': float(c.montant_restant),
            'taux_decaissement': c.taux_decaissement,
            'tranches': TrancheFinancementSerializer(tranches, many=True).data,
            'cofinancements': CofinancementSerializer(c.cofinancements.all(), many=True).data,
        })


class TrancheFinancementViewSet(viewsets.ModelViewSet):
    queryset = TrancheFinancement.objects.order_by('convention', 'numero')
    serializer_class = TrancheFinancementSerializer
    permission_classes = [CanEditFin]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        c = self.request.query_params.get('convention')
        return qs.filter(convention_id=c) if c else qs

    @action(detail=True, methods=['post'])
    def marquer_recue(self, request, pk=None):
        t = self.get_object()
        montant = float(request.data.get('montant', t.montant_prevu))
        date = request.data.get('date')
        t.marquer_recue(montant, date)
        return Response(TrancheFinancementSerializer(t).data)


class CofinancementViewSet(viewsets.ModelViewSet):
    queryset = Cofinancement.objects.all()
    serializer_class = CofinancementSerializer
    permission_classes = [CanEditFin]

    def get_queryset(self):
        qs = super().get_queryset()
        c = self.request.query_params.get('convention')
        return qs.filter(convention_id=c) if c else qs


class RapportBailleurViewSet(viewsets.ModelViewSet):
    queryset = RapportBailleur.objects.select_related(
        'convention', 'redacteur', 'valide_par'
    ).order_by('-periode_fin')
    serializer_class = RapportBailleurSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RapportBailleurFilter
    search_fields = ['reference', 'titre']
    permission_classes = [CanReadFin]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(redacteur=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        r = self.get_object()
        r.statut = 'valide'
        r.valide_par = request.user
        r.date_validation = timezone.now()
        r.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(RapportBailleurSerializer(r).data)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        r = self.get_object()
        r.statut = 'soumis'
        r.date_soumission_reelle = timezone.now().date()
        r.save(update_fields=['statut', 'date_soumission_reelle'])
        return Response(RapportBailleurSerializer(r).data)


# ─── Trésorerie ───────────────────────────────────────────────────────────────

class PlanTresorerieViewSet(viewsets.ModelViewSet):
    queryset = PlanTresorerie.objects.select_related(
        'projet', 'programme', 'created_by'
    ).prefetch_related('lignes').order_by('-exercice')
    serializer_class = PlanTresorerieSerializer
    permission_classes = [CanReadFin]

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def flux(self, request, pk=None):
        plan = self.get_object()
        lignes = plan.lignes.all()
        entrants = lignes.filter(type_flux='entrant')
        sortants = lignes.filter(type_flux='sortant')
        total_entrees = float(entrants.aggregate(s=Sum('montant_prevu'))['s'] or 0)
        total_sorties = float(sortants.aggregate(s=Sum('montant_prevu'))['s'] or 0)
        return Response({
            'plan': str(plan),
            'total_entrees': total_entrees,
            'total_sorties': total_sorties,
            'solde_global': total_entrees - total_sorties,
            'lignes_entrant': LigneTresorerieSerializer(entrants, many=True).data,
            'lignes_sortant': LigneTresorerieSerializer(sortants, many=True).data,
        })

    @action(detail=False, methods=['get'])
    def prevision_annuelle(self, request):
        projet_id = request.query_params.get('projet')
        annee = int(request.query_params.get('annee', timezone.now().year))
        qs = PlanTresorerie.objects.filter(exercice=annee)
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        lignes = LigneTresorerie.objects.filter(plan__in=qs)
        tableau = []
        for mois in range(1, 13):
            l_mois = lignes.filter(mois=mois)
            entrees = float(l_mois.filter(type_flux='entrant').aggregate(s=Sum('montant_prevu'))['s'] or 0)
            sorties = float(l_mois.filter(type_flux='sortant').aggregate(s=Sum('montant_prevu'))['s'] or 0)
            tableau.append({'mois': mois, 'entrees': entrees, 'sorties': sorties,
                            'solde': entrees - sorties})
        return Response({'annee': annee, 'tableau': tableau})


class LigneTresorerieViewSet(viewsets.ModelViewSet):
    queryset = LigneTresorerie.objects.order_by('plan', 'annee', 'mois')
    serializer_class = LigneTresorerieSerializer
    permission_classes = [CanEditFin]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params.get('plan')
        return qs.filter(plan_id=p) if p else qs


# ─── Rapports financiers ─────────────────────────────────────────────────────

class RapportFinancierViewSet(viewsets.ModelViewSet):
    queryset = RapportFinancier.objects.select_related(
        'projet', 'programme', 'redacteur', 'valide_par'
    ).order_by('-date_rapport')
    serializer_class = RapportFinancierSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RapportFinancierFilter
    search_fields = ['reference', 'titre']
    permission_classes = [CanReadFin]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(redacteur=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        r = self.get_object()
        r.statut = 'valide'
        r.valide_par = request.user
        r.date_validation = timezone.now()
        r.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(RapportFinancierSerializer(r).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        r = self.get_object()
        r.statut = 'publie'
        r.save(update_fields=['statut'])
        return Response(RapportFinancierSerializer(r).data)

    @action(detail=False, methods=['post'])
    def generer_automatique(self, request):
        projet_id = request.data.get('projet')
        programme_id = request.data.get('programme')
        type_rapport = request.data.get('type_rapport', 'budgetaire')
        periode = request.data.get('periode', 'trimestriel')
        exercice = int(request.data.get('exercice', timezone.now().year))

        budgets = Budget.objects.filter(exercice=exercice, statut='en_execution')
        if projet_id:
            budgets = budgets.filter(projet_id=projet_id)
        if programme_id:
            budgets = budgets.filter(programme_id=programme_id)

        total_budget = float(budgets.aggregate(s=Sum('montant_initial'))['s'] or 0)
        total_depense = float(budgets.aggregate(s=Sum('montant_depense'))['s'] or 0)
        total_engage = float(budgets.aggregate(s=Sum('montant_engage'))['s'] or 0)
        taux = round(total_depense / total_budget * 100, 1) if total_budget else 0

        rapport = RapportFinancier.objects.create(
            titre=f"Rapport {periode} {type_rapport} — {exercice}",
            type_rapport=type_rapport,
            periode=periode,
            projet_id=projet_id,
            programme_id=programme_id,
            date_rapport=timezone.now().date(),
            montant_budget=total_budget,
            montant_depense=total_depense,
            montant_engage=total_engage,
            taux_execution=taux,
            contenu=f"Exercice {exercice}. Budget: {total_budget:,.0f}. Dépenses: {total_depense:,.0f}. Taux: {taux}%.",
            redacteur=request.user,
            genere_par_ia=True,
            donnees_json={
                'exercice': exercice, 'nb_budgets': budgets.count(),
                'total_budget': total_budget, 'total_depense': total_depense,
                'total_engage': total_engage, 'taux_execution': taux,
            },
        )
        return Response(RapportFinancierSerializer(rapport).data, status=201)


# ─── IA Financière ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([CanReadFin])
def analyse_ia_financiere(request):
    """
    Analyse financière avancée : régression linéaire pondérée, simulation de
    scénarios (optimiste/réaliste/pessimiste), alertes précoces hiérarchisées,
    analyse de variance par catégorie et recommandations priorisées.
    """
    from .services.ia_financiere import analyser

    projet_id = request.data.get('projet')
    programme_id = request.data.get('programme')
    exercice = int(request.data.get('exercice', timezone.now().year))

    budgets = Budget.objects.filter(exercice=exercice)
    depenses = Depense.objects.filter(statut='paye', date_depense__year=exercice)

    if projet_id:
        budgets = budgets.filter(projet_id=projet_id)
        depenses = depenses.filter(projet_id=projet_id)
    if programme_id:
        budgets = budgets.filter(programme_id=programme_id)

    # Inclure tous les budgets actifs (en_execution + approuve)
    budgets = budgets.filter(statut__in=['en_execution', 'approuve', 'revise'])

    return Response(analyser(budgets, depenses, exercice))


# ─── Trésorerie avancée — Comptes bancaires ───────────────────────────────────

class CompteBancaireViewSet(viewsets.ModelViewSet):
    queryset = CompteBancaire.objects.select_related(
        'programme', 'projet', 'responsable'
    ).order_by('banque', 'intitule')
    serializer_class = CompteBancaireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['code', 'intitule', 'banque', 'numero_compte']
    ordering_fields = ['banque', 'solde_actuel', 'created_at']
    permission_classes = [CanReadFin]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('actif'):
            qs = qs.filter(actif=True)
        if projet := self.request.query_params.get('projet'):
            qs = qs.filter(projet_id=projet)
        if programme := self.request.query_params.get('programme'):
            qs = qs.filter(programme_id=programme)
        return qs

    @action(detail=True, methods=['get'])
    def extrait(self, request, pk=None):
        """Extrait de compte : mouvements filtrés + résumé de la période."""
        compte = self.get_object()
        depuis = request.query_params.get('depuis')
        jusqu = request.query_params.get('jusqu')
        qs = compte.mouvements.order_by('date_operation')
        if depuis:
            qs = qs.filter(date_operation__gte=depuis)
        if jusqu:
            qs = qs.filter(date_operation__lte=jusqu)
        entrees = float(qs.filter(type_mouvement='credit').aggregate(s=Sum('montant'))['s'] or 0)
        sorties = float(qs.filter(type_mouvement='debit').aggregate(s=Sum('montant'))['s'] or 0)
        return Response({
            'compte': CompteBancaireSerializer(compte).data,
            'periode': {'depuis': depuis, 'jusqu': jusqu},
            'solde_actuel': float(compte.solde_actuel),
            'entrees_periode': entrees,
            'sorties_periode': sorties,
            'solde_periode': entrees - sorties,
            'nb_mouvements': qs.count(),
            'mouvements': MouvementBancaireSerializer(qs, many=True).data,
        })

    @action(detail=True, methods=['post'])
    def recalculer_solde(self, request, pk=None):
        compte = self.get_object()
        solde = compte.recalculer_solde()
        return Response({'solde_actuel': float(solde)})


class MouvementBancaireViewSet(viewsets.ModelViewSet):
    queryset = MouvementBancaire.objects.select_related(
        'compte', 'depense', 'convention', 'saisi_par'
    ).order_by('-date_operation')
    serializer_class = MouvementBancaireSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['libelle', 'reference_externe']
    ordering_fields = ['date_operation', 'montant']
    permission_classes = [CanEditFin]

    def get_queryset(self):
        qs = super().get_queryset()
        if c := self.request.query_params.get('compte'):
            qs = qs.filter(compte_id=c)
        if self.request.query_params.get('non_rapproches'):
            qs = qs.filter(rapproche=False)
        if t := self.request.query_params.get('type'):
            qs = qs.filter(type_mouvement=t)
        return qs

    def perform_create(self, s):
        mouvement = s.save(saisi_par=self.request.user)
        # Recalculer le solde du compte après chaque mouvement
        mouvement.compte.recalculer_solde()

    def perform_update(self, s):
        mouvement = s.save()
        mouvement.compte.recalculer_solde()

    def perform_destroy(self, instance):
        compte = instance.compte
        instance.delete()
        compte.recalculer_solde()

    @action(detail=True, methods=['post'])
    def rapprocher(self, request, pk=None):
        mouvement = self.get_object()
        mouvement.rapproche = True
        mouvement.save(update_fields=['rapproche'])
        return Response(MouvementBancaireSerializer(mouvement).data)

    @action(detail=True, methods=['post'])
    def derapprocher(self, request, pk=None):
        mouvement = self.get_object()
        mouvement.rapproche = False
        mouvement.save(update_fields=['rapproche'])
        return Response(MouvementBancaireSerializer(mouvement).data)


class RapprochementBancaireViewSet(viewsets.ModelViewSet):
    queryset = RapprochementBancaire.objects.select_related(
        'compte', 'effectue_par', 'valide_par'
    ).order_by('-periode_fin')
    serializer_class = RapprochementBancaireSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['periode_fin', 'ecart']
    permission_classes = [CanReadFin]

    def get_queryset(self):
        qs = super().get_queryset()
        if c := self.request.query_params.get('compte'):
            qs = qs.filter(compte_id=c)
        if s := self.request.query_params.get('statut'):
            qs = qs.filter(statut=s)
        return qs

    def perform_create(self, s):
        rap = s.save(effectue_par=self.request.user)
        # Calcul automatique : solde comptable = solde actuel du compte
        rap.solde_comptable = rap.compte.solde_actuel
        rap.calculer_ecart()
        # Rapprocher automatiquement les mouvements de la période
        qs_mvt = MouvementBancaire.objects.filter(
            compte=rap.compte,
            date_operation__range=[rap.periode_debut, rap.periode_fin],
        )
        nb_rapproches = qs_mvt.filter(rapproche=False).update(rapproche=True)
        rap.nb_mouvements_rapproches = qs_mvt.count()
        rap.nb_mouvements_non_rapproches = 0
        rap.save(update_fields=[
            'solde_comptable', 'ecart',
            'nb_mouvements_rapproches', 'nb_mouvements_non_rapproches',
        ])

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        rap = self.get_object()
        if rap.statut != 'en_cours':
            return Response({'detail': 'Seul un rapprochement en cours peut être validé.'}, status=400)
        rap.statut = 'valide'
        rap.valide_par = request.user
        rap.date_validation = timezone.now()
        rap.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(RapprochementBancaireSerializer(rap).data)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        rap = self.get_object()
        rap.statut = 'cloture'
        rap.save(update_fields=['statut'])
        return Response(RapprochementBancaireSerializer(rap).data)


# ─── Dashboards financiers ────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadFin])
def depassements_budgetaires(request):
    """Toutes les lignes budgétaires dont montant_engage > montant_prevu."""
    from django.db.models import F, ExpressionWrapper, DecimalField
    exercice = int(request.query_params.get('exercice', timezone.now().year))
    projet_id = request.query_params.get('projet')

    qs = LigneBudgetaire.objects.filter(
        montant_engage__gt=F('montant_prevu'),
        budget__exercice=exercice,
        budget__statut__in=['en_execution', 'approuve', 'revise'],
    ).select_related('budget', 'budget__projet', 'budget__programme').order_by(
        ExpressionWrapper(F('montant_engage') - F('montant_prevu'), output_field=DecimalField())
    ).reverse()[:100]

    if projet_id:
        qs = qs.filter(budget__projet_id=projet_id)

    lignes = []
    total_ecart = 0
    for l in qs:
        ecart = float(l.montant_engage - l.montant_prevu)
        total_ecart += ecart
        lignes.append({
            'id': l.id,
            'code': l.code,
            'libelle': l.libelle,
            'categorie': l.categorie,
            'budget_reference': l.budget.reference,
            'budget_intitule': l.budget.intitule or '',
            'projet': l.budget.projet.code if l.budget.projet else None,
            'montant_prevu': float(l.montant_prevu),
            'montant_engage': float(l.montant_engage),
            'montant_depense': float(l.montant_depense),
            'ecart': round(ecart, 2),
            'taux_engagement': round(float(l.montant_engage) / float(l.montant_prevu) * 100, 1) if l.montant_prevu else 0,
        })

    return Response({
        'exercice': exercice,
        'nb_depassements': len(lignes),
        'montant_total_ecart': round(total_ecart, 2),
        'lignes': lignes,
    })


@api_view(['GET'])
@permission_classes([CanReadFin])
def dashboard_financier(request):
    projet_id = request.query_params.get('projet')
    programme_id = request.query_params.get('programme')
    exercice = int(request.query_params.get('exercice', timezone.now().year))
    today = timezone.now().date()

    qs_budget = Budget.objects.filter(exercice=exercice)
    qs_depense = Depense.objects.filter(date_depense__year=exercice)
    qs_convention = Convention.objects.all()
    qs_avance = Avance.objects.all()
    qs_engagement = Engagement.objects.filter(date_engagement__year=exercice)

    if projet_id:
        qs_budget = qs_budget.filter(projet_id=projet_id)
        qs_depense = qs_depense.filter(projet_id=projet_id)
        qs_convention = qs_convention.filter(projet_id=projet_id)
        qs_avance = qs_avance.filter(projet_id=projet_id)

    if programme_id:
        qs_budget = qs_budget.filter(programme_id=programme_id)
        qs_convention = qs_convention.filter(programme_id=programme_id)

    total_budget = float(qs_budget.aggregate(s=Sum('montant_initial'))['s'] or 0)
    total_depense = float(qs_depense.filter(statut='paye').aggregate(s=Sum('montant'))['s'] or 0)
    total_engage = float(qs_engagement.filter(statut='approuve').aggregate(s=Sum('montant'))['s'] or 0)
    total_finance = float(qs_convention.aggregate(s=Sum('montant_recu'))['s'] or 0)

    return Response({
        'exercice': exercice,
        'budget': {
            'total': total_budget,
            'depense': total_depense,
            'engage': total_engage,
            'disponible': total_budget - total_engage,
            'taux_execution': round(total_depense / total_budget * 100, 1) if total_budget else 0,
            'taux_engagement': round(total_engage / total_budget * 100, 1) if total_budget else 0,
        },
        'financements': {
            'total_conventions': qs_convention.count(),
            'total_recu': total_finance,
            'conventions_actives': qs_convention.filter(statut='active').count(),
        },
        'depenses': {
            'ce_mois': float(qs_depense.filter(
                statut='paye', date_depense__month=today.month
            ).aggregate(s=Sum('montant'))['s'] or 0),
            'en_attente': qs_depense.filter(
                statut__in=['soumis', 'validation_responsable', 'validation_finance']
            ).count(),
        },
        'avances': {
            'en_cours': qs_avance.filter(
                statut__in=['accordee', 'partiellement_justifiee']
            ).count(),
            'montant_en_cours': float(qs_avance.filter(
                statut__in=['accordee', 'partiellement_justifiee']
            ).aggregate(s=Sum('montant'))['s'] or 0),
        },
    })


@api_view(['GET'])
@permission_classes([CanReadFin])
def dashboard_tresorerie(request):
    projet_id = request.query_params.get('projet')
    exercice = int(request.query_params.get('annee', timezone.now().year))
    mois_courant = timezone.now().month

    plans = PlanTresorerie.objects.filter(exercice=exercice)
    if projet_id:
        plans = plans.filter(projet_id=projet_id)

    lignes = LigneTresorerie.objects.filter(plan__in=plans)

    entrees_cumul = float(lignes.filter(
        type_flux='entrant', mois__lte=mois_courant
    ).aggregate(s=Sum('montant_prevu'))['s'] or 0)

    sorties_cumul = float(lignes.filter(
        type_flux='sortant', mois__lte=mois_courant
    ).aggregate(s=Sum('montant_prevu'))['s'] or 0)

    entrees_mois = float(lignes.filter(
        type_flux='entrant', mois=mois_courant
    ).aggregate(s=Sum('montant_prevu'))['s'] or 0)

    sorties_mois = float(lignes.filter(
        type_flux='sortant', mois=mois_courant
    ).aggregate(s=Sum('montant_prevu'))['s'] or 0)

    return Response({
        'exercice': exercice,
        'mois_courant': mois_courant,
        'cumul': {
            'entrees': entrees_cumul,
            'sorties': sorties_cumul,
            'solde': entrees_cumul - sorties_cumul,
        },
        'mois': {
            'entrees': entrees_mois,
            'sorties': sorties_mois,
            'solde': entrees_mois - sorties_mois,
        },
    })
