from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.models import AuditLog
from accounts.permissions import HasModulePermission
from .models import (
    CadreLogique, ElementCadreLogique,
    AnalyseSWOT, ElementSWOT, StrategieSWOT,
    TDR, PlanAction, ActionPlanItem,
    ProgrammeActivites, ActivitePA,
    PlanTravail, Activite, Jalon,
)
from .serializers import (
    CadreLogiqueSerializer, ElementCadreLogiqueSerializer,
    AnalyseSWOTSerializer, ElementSWOTSerializer, StrategieSWOTSerializer,
    TDRListSerializer, TDRDetailSerializer,
    PlanActionSerializer, ActionPlanItemSerializer,
    ProgrammeActivitesSerializer, ProgrammeActivitesListSerializer, ActivitePASerializer,
    PlanTravailSerializer, ActiviteSerializer, JalonSerializer,
)

CanReadPlan = HasModulePermission.for_module('planification', 'peut_lire')
CanCreatePlan = HasModulePermission.for_module('planification', 'peut_creer')
CanEditPlan = HasModulePermission.for_module('planification', 'peut_modifier')
CanValidatePlan = HasModulePermission.for_module('planification', 'peut_valider')


# ─── M08 : Cadre Logique ─────────────────────────────────────────────────────

class CadreLogiqueViewSet(viewsets.ModelViewSet):
    queryset = CadreLogique.objects.select_related(
        'projet', 'programme', 'created_by', 'valide_par'
    ).prefetch_related('elements').order_by('-created_at')
    serializer_class = CadreLogiqueSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['titre', 'description']
    permission_classes = [CanReadPlan]

    def get_queryset(self):
        qs = super().get_queryset()
        projet_id = self.request.query_params.get('projet')
        programme_id = self.request.query_params.get('programme')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        return qs

    def perform_create(self, serializer):
        cadre = serializer.save(created_by=self.request.user)
        AuditLog.log(self.request.user, 'create', module='planification',
                     objet_type='CadreLogique', objet_id=cadre.id, request=self.request)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        cadre = self.get_object()
        if cadre.statut == 'valide':
            return Response({'detail': 'Déjà validé.'}, status=400)
        cadre.statut = 'valide'
        cadre.valide_par = request.user
        cadre.date_validation = timezone.now()
        cadre.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(CadreLogiqueSerializer(cadre).data)

    @action(detail=True, methods=['get'])
    def matrice(self, request, pk=None):
        cadre = self.get_object()
        elements = cadre.elements.filter(actif=True).order_by('ordre')
        by_niveau = {}
        for el in elements:
            by_niveau.setdefault(el.niveau, []).append(
                ElementCadreLogiqueSerializer(el).data
            )
        return Response({
            'cadre': {'id': cadre.id, 'titre': cadre.titre, 'version': cadre.version},
            'niveaux': by_niveau,
        })


class ElementCadreLogiqueViewSet(viewsets.ModelViewSet):
    queryset = ElementCadreLogique.objects.filter(actif=True).order_by('ordre')
    serializer_class = ElementCadreLogiqueSerializer
    permission_classes = [CanReadPlan]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['code', 'description']

    def get_queryset(self):
        qs = super().get_queryset()
        cadre_id = self.request.query_params.get('cadre')
        niveau = self.request.query_params.get('niveau')
        if cadre_id:
            qs = qs.filter(cadre_id=cadre_id)
        if niveau:
            qs = qs.filter(niveau=niveau)
        return qs


# ─── M09 : SWOT ──────────────────────────────────────────────────────────────

class AnalyseSWOTViewSet(viewsets.ModelViewSet):
    queryset = AnalyseSWOT.objects.select_related(
        'projet', 'programme', 'created_by'
    ).prefetch_related('elements', 'strategies').order_by('-date_analyse')
    serializer_class = AnalyseSWOTSerializer
    permission_classes = [CanReadPlan]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['titre', 'description']

    def get_queryset(self):
        qs = super().get_queryset()
        projet_id = self.request.query_params.get('projet')
        programme_id = self.request.query_params.get('programme')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def generer_strategies_ia(self, request, pk=None):
        analyse = self.get_object()
        elements = analyse.elements.all()
        forces = list(elements.filter(categorie='force').values_list('description', flat=True))
        faiblesses = list(elements.filter(categorie='faiblesse').values_list('description', flat=True))
        opportunites = list(elements.filter(categorie='opportunite').values_list('description', flat=True))
        menaces = list(elements.filter(categorie='menace').values_list('description', flat=True))

        suggestions = [
            {'type_strategie': 'FO', 'titre': 'Stratégie offensive',
             'description': f"Exploiter les forces ({', '.join(forces[:2])}) pour saisir les opportunités ({', '.join(opportunites[:2])})",
             'priorite': 'haute'},
            {'type_strategie': 'FM', 'titre': 'Stratégie défensive',
             'description': f"Utiliser les forces pour contrer les menaces ({', '.join(menaces[:2])})",
             'priorite': 'haute'},
            {'type_strategie': 'FaO', 'titre': 'Stratégie de rattrapage',
             'description': f"Corriger les faiblesses ({', '.join(faiblesses[:2])}) en profitant des opportunités",
             'priorite': 'moyenne'},
            {'type_strategie': 'FaM', 'titre': 'Stratégie de survie',
             'description': "Minimiser les faiblesses pour éviter les menaces",
             'priorite': 'faible'},
        ]

        created = []
        for s in suggestions:
            strat = StrategieSWOT.objects.create(
                analyse=analyse, generee_par_ia=True, **s
            )
            created.append(StrategieSWOTSerializer(strat).data)

        return Response({'strategies_generees': created, 'message': 'Stratégies générées par IA (simulation).'})


class ElementSWOTViewSet(viewsets.ModelViewSet):
    queryset = ElementSWOT.objects.all().order_by('categorie', '-ponderation')
    serializer_class = ElementSWOTSerializer
    permission_classes = [CanReadPlan]

    def get_queryset(self):
        qs = super().get_queryset()
        analyse_id = self.request.query_params.get('analyse')
        categorie = self.request.query_params.get('categorie')
        if analyse_id:
            qs = qs.filter(analyse_id=analyse_id)
        if categorie:
            qs = qs.filter(categorie=categorie)
        return qs


class StrategieSWOTViewSet(viewsets.ModelViewSet):
    queryset = StrategieSWOT.objects.all().order_by('type_strategie', 'priorite')
    serializer_class = StrategieSWOTSerializer
    permission_classes = [CanReadPlan]

    def get_queryset(self):
        qs = super().get_queryset()
        analyse_id = self.request.query_params.get('analyse')
        if analyse_id:
            qs = qs.filter(analyse_id=analyse_id)
        return qs


# ─── M10 : TDR ───────────────────────────────────────────────────────────────

class TDRViewSet(viewsets.ModelViewSet):
    queryset = TDR.objects.select_related(
        'projet', 'programme', 'redige_par', 'valide_par', 'publie_par'
    ).order_by('-created_at')
    permission_classes = [CanReadPlan]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['reference', 'titre', 'objectifs']
    ordering_fields = ['created_at', 'date_redaction', 'budget_previsionnel']
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'list':
            return TDRListSerializer
        return TDRDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        for key in ('projet', 'programme', 'statut', 'type_tdr'):
            val = self.request.query_params.get(key)
            if val:
                qs = qs.filter(**{key: val})
        return qs

    def perform_create(self, serializer):
        serializer.save(redige_par=self.request.user)

    @action(detail=True, methods=['post'])
    def mettre_en_revision(self, request, pk=None):
        tdr = self.get_object()
        if tdr.statut != 'brouillon':
            return Response({'detail': 'Seul un TDR en brouillon peut être mis en révision.'}, status=400)
        tdr.statut = 'en_revision'
        tdr.save(update_fields=['statut'])
        return Response(TDRDetailSerializer(tdr).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        tdr = self.get_object()
        if tdr.statut not in ('brouillon', 'en_revision'):
            return Response({'detail': 'Statut incompatible.'}, status=400)
        tdr.valider(request.user)
        return Response(TDRDetailSerializer(tdr).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        tdr = self.get_object()
        if tdr.statut != 'valide':
            return Response({'detail': 'Le TDR doit être validé avant publication.'}, status=400)
        tdr.publier(request.user)
        return Response(TDRDetailSerializer(tdr).data)

    @action(detail=True, methods=['post'])
    def generer_ia(self, request, pk=None):
        tdr = self.get_object()
        contexte = request.data.get('contexte', tdr.contexte or 'Contexte du projet')
        type_tdr = tdr.type_tdr

        suggestions = {
            'contexte': f"[Suggestion IA] Dans le cadre de {contexte}, ce TDR de type {type_tdr} vise à...",
            'objectifs': "[Suggestion IA] Objectif général : ...\nObjectifs spécifiques :\n1. ...\n2. ...",
            'resultats_attendus': "[Suggestion IA] À l'issue de la mission :\n- Livrable 1 : ...\n- Livrable 2 : ...",
            'methodologie': "[Suggestion IA] La méthodologie comprend : phase 1 (démarrage), phase 2 (exécution), phase 3 (restitution).",
        }

        for field, val in suggestions.items():
            if not getattr(tdr, field):
                setattr(tdr, field, val)
        tdr.genere_par_ia = True
        tdr.save()

        return Response({'tdr': TDRDetailSerializer(tdr).data, 'message': 'Sections générées par IA (simulation).'})


# ─── M11 : Plans d'Actions ────────────────────────────────────────────────────

class PlanActionViewSet(viewsets.ModelViewSet):
    queryset = PlanAction.objects.select_related(
        'projet', 'programme', 'created_by', 'valide_par'
    ).prefetch_related('items').order_by('-annee', 'trimestre')
    serializer_class = PlanActionSerializer
    permission_classes = [CanReadPlan]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['titre']

    def get_queryset(self):
        qs = super().get_queryset()
        for key in ('projet', 'programme', 'statut', 'annee', 'periode'):
            val = self.request.query_params.get(key)
            if val:
                qs = qs.filter(**{key: val})
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        plan = self.get_object()
        plan.statut = 'valide'
        plan.valide_par = request.user
        plan.date_validation = timezone.now()
        plan.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(PlanActionSerializer(plan).data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        plan = self.get_object()
        items = plan.items.all()
        today = timezone.now().date()
        return Response({
            'total_actions': items.count(),
            'terminees': items.filter(statut='termine').count(),
            'en_cours': items.filter(statut='en_cours').count(),
            'en_retard': items.filter(date_fin__lt=today).exclude(statut__in=['termine', 'annule']).count(),
            'budget_prevu': items.aggregate(t=Sum('budget_prevu'))['t'] or 0,
            'budget_realise': items.aggregate(t=Sum('budget_realise'))['t'] or 0,
            'taux_realisation': plan.taux_realisation,
        })


class ActionPlanItemViewSet(viewsets.ModelViewSet):
    queryset = ActionPlanItem.objects.select_related('plan', 'responsable').order_by('ordre', 'date_debut')
    serializer_class = ActionPlanItemSerializer
    permission_classes = [CanReadPlan]

    def get_queryset(self):
        qs = super().get_queryset()
        plan_id = self.request.query_params.get('plan')
        statut = self.request.query_params.get('statut')
        responsable_id = self.request.query_params.get('responsable')
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        if statut:
            qs = qs.filter(statut=statut)
        if responsable_id:
            qs = qs.filter(responsable_id=responsable_id)
        return qs


# ─── M12 : Programmes d'Activités ────────────────────────────────────────────

class ProgrammeActivitesViewSet(viewsets.ModelViewSet):
    queryset = ProgrammeActivites.objects.select_related(
        'projet', 'programme', 'created_by', 'valide_par'
    ).prefetch_related('activites').order_by('-annee', 'trimestre')
    permission_classes = [CanReadPlan]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['titre', 'reference']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProgrammeActivitesListSerializer
        return ProgrammeActivitesSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        for key in ('projet', 'programme', 'statut', 'annee', 'periode'):
            val = self.request.query_params.get(key)
            if val:
                qs = qs.filter(**{key: val})
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        pa = self.get_object()
        pa.statut = 'soumis'
        pa.save(update_fields=['statut'])
        return Response(ProgrammeActivitesSerializer(pa).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        pa = self.get_object()
        if pa.statut not in ('soumis', 'brouillon'):
            return Response({'detail': 'Statut incompatible.'}, status=400)
        pa.statut = 'valide'
        pa.valide_par = request.user
        pa.date_validation = timezone.now()
        pa.save(update_fields=['statut', 'valide_par', 'date_validation'])
        AuditLog.log(request.user, 'update', module='planification',
                     objet_type='ProgrammeActivites', objet_id=pa.id, request=request)
        return Response(ProgrammeActivitesSerializer(pa).data)

    @action(detail=True, methods=['get'])
    def calendrier(self, request, pk=None):
        pa = self.get_object()
        activites = pa.activites.all().select_related('responsable').order_by('date_debut_prevue')
        events = []
        for a in activites:
            events.append({
                'id': a.id,
                'title': f"[{a.code}] {a.libelle}",
                'start': a.date_debut_prevue,
                'end': a.date_fin_prevue,
                'statut': a.statut,
                'taux_avancement': float(a.taux_avancement),
                'responsable': a.responsable_id,
                'type': 'activite',
            })
        return Response({'pa': {'id': pa.id, 'titre': pa.titre, 'annee': pa.annee}, 'events': events})

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        pa = self.get_object()
        activites = pa.activites.all()
        today = timezone.now().date()
        return Response({
            'total_activites': activites.count(),
            'terminees': activites.filter(statut='terminee').count(),
            'en_cours': activites.filter(statut='en_cours').count(),
            'en_retard': sum(1 for a in activites if a.est_en_retard),
            'budget_prevu': float(activites.aggregate(t=Sum('budget_prevu'))['t'] or 0),
            'budget_realise': float(activites.aggregate(t=Sum('budget_realise'))['t'] or 0),
            'taux_realisation': pa.taux_realisation,
        })


class ActivitePAViewSet(viewsets.ModelViewSet):
    queryset = ActivitePA.objects.select_related(
        'programme_activites', 'responsable', 'element_cadre'
    ).order_by('ordre', 'date_debut_prevue')
    serializer_class = ActivitePASerializer
    permission_classes = [CanReadPlan]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['code', 'libelle', 'description']

    def get_queryset(self):
        qs = super().get_queryset()
        pa_id = self.request.query_params.get('programme_activites')
        statut = self.request.query_params.get('statut')
        responsable_id = self.request.query_params.get('responsable')
        if pa_id:
            qs = qs.filter(programme_activites_id=pa_id)
        if statut:
            qs = qs.filter(statut=statut)
        if responsable_id:
            qs = qs.filter(responsable_id=responsable_id)
        return qs


# ─── Plan de Travail ─────────────────────────────────────────────────────────

class PlanTravailViewSet(viewsets.ModelViewSet):
    queryset = PlanTravail.objects.select_related('projet').order_by('-annee', 'trimestre')
    serializer_class = PlanTravailSerializer
    permission_classes = [CanReadPlan]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['nom']

    def get_queryset(self):
        qs = super().get_queryset()
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return qs


class ActiviteViewSet(viewsets.ModelViewSet):
    queryset = Activite.objects.select_related('plan', 'responsable').order_by('ordre')
    serializer_class = ActiviteSerializer
    permission_classes = [CanReadPlan]

    def get_queryset(self):
        qs = super().get_queryset()
        plan_id = self.request.query_params.get('plan')
        statut = self.request.query_params.get('statut')
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        if statut:
            qs = qs.filter(statut=statut)
        return qs


class JalonViewSet(viewsets.ModelViewSet):
    queryset = Jalon.objects.select_related('projet').order_by('date_prevue')
    serializer_class = JalonSerializer
    permission_classes = [CanReadPlan]

    def get_queryset(self):
        qs = super().get_queryset()
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return qs
