from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.models import AuditLog
from accounts.permissions import IsAdminOrSuperAdmin, HasModulePermission
from .models import (
    ZoneIntervention, Programme, ObjectifProgramme, PartenaireProgramme,
    DocumentProgramme, Projet, MembreEquipeProjet, RisqueProjet,
    LivrableProjet, JalonProjet,
)
from .serializers import (
    ZoneInterventionSerializer, ProgrammeListSerializer, ProgrammeDetailSerializer,
    ProgrammeCreateSerializer, ObjectifProgrammeSerializer, PartenaireProgrammeSerializer,
    DocumentProgrammeSerializer, ProjetListSerializer, ProjetDetailSerializer,
    ProjetCreateSerializer, MembreEquipeSerializer, RisqueSerializer,
    LivrableSerializer, JalonProjetSerializer,
)
from .filters import ProgrammeFilter, ProjetFilter, RisqueFilter


CanReadPP = HasModulePermission.for_module('programmes_projets', 'peut_lire')
CanCreatePP = HasModulePermission.for_module('programmes_projets', 'peut_creer')
CanEditPP = HasModulePermission.for_module('programmes_projets', 'peut_modifier')
CanValidatePP = HasModulePermission.for_module('programmes_projets', 'peut_valider')


class ZoneInterventionViewSet(viewsets.ModelViewSet):
    queryset = ZoneIntervention.objects.filter(actif=True).order_by('pays', 'nom')
    serializer_class = ZoneInterventionSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nom', 'code', 'pays', 'region']
    permission_classes = [permissions.IsAuthenticated]


class ProgrammeViewSet(viewsets.ModelViewSet):
    queryset = Programme.objects.select_related(
        'organisation', 'coordonnateur', 'responsable', 'bailleur', 'valide_par', 'created_by'
    ).prefetch_related('zones_intervention', 'projets').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProgrammeFilter
    search_fields = ['code', 'intitule', 'acronyme', 'description']
    ordering_fields = ['code', 'intitule', 'date_debut', 'budget_total', 'taux_avancement']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'dashboard']:
            return [CanReadPP()]
        if self.action == 'create':
            return [CanCreatePP()]
        if self.action in ['update', 'partial_update']:
            return [CanEditPP()]
        if self.action in ['soumettre', 'valider', 'activer', 'suspendre', 'cloturer']:
            return [CanValidatePP()]
        return [IsAdminOrSuperAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProgrammeListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProgrammeCreateSerializer
        return ProgrammeDetailSerializer

    def perform_create(self, serializer):
        programme = serializer.save(created_by=self.request.user)
        AuditLog.log(self.request.user, 'create', module='programmes_projets',
                     objet_type='Programme', objet_id=programme.id, objet_repr=str(programme),
                     request=self.request)

    def perform_update(self, serializer):
        programme = serializer.save()
        AuditLog.log(self.request.user, 'update', module='programmes_projets',
                     objet_type='Programme', objet_id=programme.id, objet_repr=str(programme),
                     request=self.request)

    def destroy(self, request, *args, **kwargs):
        prog = self.get_object()
        if prog.statut not in ('brouillon', 'archive'):
            return Response(
                {'detail': 'Seuls les programmes en brouillon ou archivés peuvent être supprimés.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        prog = self.get_object()
        if prog.statut != 'brouillon':
            return Response({'detail': 'Seul un brouillon peut être soumis.'}, status=400)
        if not prog.objectifs.exists():
            return Response({'detail': 'Le programme doit avoir au moins un objectif.'}, status=400)
        prog.soumettre(request.user)
        AuditLog.log(request.user, 'update', module='programmes_projets',
                     objet_type='Programme', objet_id=prog.id,
                     details={'action': 'soumission'}, request=request)
        return Response(ProgrammeDetailSerializer(prog).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        prog = self.get_object()
        if prog.statut not in ('soumis',):
            return Response({'detail': 'Seul un programme soumis peut être validé.'}, status=400)
        prog.valider(request.user)
        AuditLog.log(request.user, 'update', module='programmes_projets',
                     objet_type='Programme', objet_id=prog.id,
                     details={'action': 'validation'}, request=request)
        return Response(ProgrammeDetailSerializer(prog).data)

    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        prog = self.get_object()
        if prog.statut not in ('valide', 'en_preparation'):
            return Response({'detail': 'Le programme doit être validé pour être activé.'}, status=400)
        prog.activer()
        return Response(ProgrammeDetailSerializer(prog).data)

    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        prog = self.get_object()
        if prog.statut != 'en_cours':
            return Response({'detail': 'Seul un programme en cours peut être suspendu.'}, status=400)
        motif = request.data.get('motif', '')
        prog.suspendre(motif)
        return Response(ProgrammeDetailSerializer(prog).data)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        prog = self.get_object()
        if prog.statut in ('cloture', 'archive'):
            return Response({'detail': 'Programme déjà clôturé.'}, status=400)
        prog.cloturer()
        AuditLog.log(request.user, 'update', module='programmes_projets',
                     objet_type='Programme', objet_id=prog.id,
                     details={'action': 'cloture'}, request=request)
        return Response(ProgrammeDetailSerializer(prog).data)

    @action(detail=True, methods=['post'])
    def dupliquer(self, request, pk=None):
        prog = self.get_object()
        import uuid
        nouveau_code = f"{prog.code}-COPIE-{uuid.uuid4().hex[:4].upper()}"
        nouveau_titre = request.data.get('intitule', f"Copie de {prog.intitule}")
        new_prog = Programme.objects.create(
            code=nouveau_code,
            intitule=nouveau_titre,
            acronyme=prog.acronyme,
            description=prog.description,
            organisation=prog.organisation,
            bailleur=prog.bailleur,
            coordonnateur=prog.coordonnateur,
            responsable=prog.responsable,
            date_debut=prog.date_debut,
            date_fin=prog.date_fin,
            budget_total=prog.budget_total,
            devise=prog.devise,
            contexte=prog.contexte,
            impacts_attendus=prog.impacts_attendus,
            statut='brouillon',
            created_by=request.user,
        )
        new_prog.zones_intervention.set(prog.zones_intervention.all())
        for obj in prog.objectifs.all():
            ObjectifProgramme.objects.create(
                programme=new_prog, type_objectif=obj.type_objectif,
                code=obj.code, libelle=obj.libelle, description=obj.description,
                ordre=obj.ordre,
            )
        return Response(ProgrammeDetailSerializer(new_prog).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        prog = self.get_object()
        projets = prog.projets.all()
        budget_consomme = 0
        try:
            from gestion_financiere.models import BudgetProjet
            budget_consomme = BudgetProjet.objects.filter(
                projet__programme=prog
            ).aggregate(total=Sum('montant_initial'))['total'] or 0
        except Exception:
            pass

        return Response({
            'programme': ProgrammeListSerializer(prog).data,
            'nb_projets': projets.count(),
            'projets_actifs': projets.filter(statut='en_cours').count(),
            'projets_termines': projets.filter(statut__in=['termine', 'cloture']).count(),
            'projets_en_retard': sum(1 for p in projets if p.est_en_retard),
            'budget_total': float(prog.budget_total),
            'budget_consomme': float(budget_consomme),
            'taux_consommation': round(float(budget_consomme) / float(prog.budget_total) * 100, 2)
            if prog.budget_total else 0,
            'taux_avancement': float(prog.taux_avancement),
        })


class ObjectifProgrammeViewSet(viewsets.ModelViewSet):
    queryset = ObjectifProgramme.objects.filter(actif=True).order_by('type_objectif', 'ordre')
    serializer_class = ObjectifProgrammeSerializer
    permission_classes = [CanReadPP]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        qs = super().get_queryset()
        programme_id = self.request.query_params.get('programme')
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        return qs


class DocumentProgrammeViewSet(viewsets.ModelViewSet):
    queryset = DocumentProgramme.objects.all().order_by('-created_at')
    serializer_class = DocumentProgrammeSerializer
    permission_classes = [CanReadPP]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        programme_id = self.request.query_params.get('programme')
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        return qs


class ProjetViewSet(viewsets.ModelViewSet):
    queryset = Projet.objects.select_related(
        'programme', 'organisation', 'chef_projet', 'valide_par', 'created_by'
    ).prefetch_related('zones_intervention', 'membres_equipe', 'risques', 'livrables', 'jalons')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProjetFilter
    search_fields = ['code', 'titre', 'description']
    ordering_fields = ['code', 'titre', 'date_debut', 'budget_initial', 'taux_avancement', 'priorite']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'dashboard', 'gantt']:
            return [CanReadPP()]
        if self.action == 'create':
            return [CanCreatePP()]
        if self.action in ['update', 'partial_update']:
            return [CanEditPP()]
        if self.action in ['valider', 'activer', 'suspendre', 'cloturer']:
            return [CanValidatePP()]
        return [IsAdminOrSuperAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjetListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProjetCreateSerializer
        return ProjetDetailSerializer

    def perform_create(self, serializer):
        projet = serializer.save(created_by=self.request.user)
        # Auto-add chef projet to team
        if projet.chef_projet:
            MembreEquipeProjet.objects.get_or_create(
                projet=projet, user=projet.chef_projet,
                defaults={'role_projet': 'chef_projet'}
            )
        AuditLog.log(self.request.user, 'create', module='programmes_projets',
                     objet_type='Projet', objet_id=projet.id, objet_repr=str(projet),
                     request=self.request)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        projet = self.get_object()
        if projet.statut not in ('brouillon', 'planifie'):
            return Response({'detail': 'Statut incompatible pour la validation.'}, status=400)
        projet.valider(request.user)
        return Response(ProjetDetailSerializer(projet).data)

    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        projet = self.get_object()
        if projet.statut != 'valide':
            return Response({'detail': 'Le projet doit être validé pour être activé.'}, status=400)
        projet.activer()
        return Response(ProjetDetailSerializer(projet).data)

    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        projet = self.get_object()
        motif = request.data.get('motif', '')
        projet.suspendre(motif)
        return Response(ProjetDetailSerializer(projet).data)

    @action(detail=True, methods=['post'])
    def cloturer(self, request, pk=None):
        projet = self.get_object()
        # Check livrables
        livrables_non_valides = projet.livrables.exclude(statut='valide')
        if livrables_non_valides.exists() and not request.data.get('force', False):
            return Response({
                'detail': f'{livrables_non_valides.count()} livrable(s) non validé(s). Forcez la clôture avec force=true.',
                'livrables_en_attente': livrables_non_valides.count(),
            }, status=400)
        projet.cloturer()
        return Response(ProjetDetailSerializer(projet).data)

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        projet = self.get_object()
        risques = projet.risques.all()
        livrables = projet.livrables.all()
        jalons = projet.jalons.all()
        membres = projet.membres_equipe.filter(is_active=True)

        from django.utils import timezone as tz
        today = tz.now().date()

        return Response({
            'projet': ProjetListSerializer(projet).data,
            'avancement': float(projet.taux_avancement),
            'risques': {
                'total': risques.count(),
                'critiques': risques.filter(niveau_risque='critique').count(),
                'eleves': risques.filter(niveau_risque='eleve').count(),
                'en_cours': risques.filter(statut='en_cours_traitement').count(),
            },
            'livrables': {
                'total': livrables.count(),
                'valides': livrables.filter(statut='valide').count(),
                'en_cours': livrables.filter(statut='en_cours').count(),
                'en_retard': livrables.filter(statut='planifie', date_prevue__lt=today).count(),
            },
            'jalons': {
                'total': jalons.count(),
                'atteints': jalons.filter(statut='atteint').count(),
                'manques': jalons.filter(statut='manque').count(),
                'a_venir': jalons.filter(statut='a_venir', date_prevue__gte=today).count(),
            },
            'equipe': membres.count(),
            'budget': {
                'initial': float(projet.budget_initial),
                'revise': float(projet.budget_revise),
                'actuel': float(projet.budget_actuel),
            },
        })

    @action(detail=True, methods=['get'])
    def gantt(self, request, pk=None):
        from planification.models import Activite, PlanTravail
        projet = self.get_object()
        plans = PlanTravail.objects.filter(projet=projet).prefetch_related('activites')
        gantt_data = []
        for plan in plans:
            for activite in plan.activites.all().order_by('ordre'):
                gantt_data.append({
                    'id': activite.id,
                    'code': activite.code,
                    'libelle': activite.libelle,
                    'statut': activite.statut,
                    'date_debut': activite.date_debut_prevue,
                    'date_fin': activite.date_fin_prevue,
                    'date_debut_reelle': activite.date_debut_reelle,
                    'date_fin_reelle': activite.date_fin_reelle,
                    'responsable': activite.responsable_id,
                    'taux_avancement': float(activite.taux_avancement),
                    'parent_id': activite.parent_id,
                })
        jalons = [
            {
                'id': j.id, 'libelle': j.libelle, 'date_prevue': j.date_prevue,
                'date_reelle': j.date_reelle, 'statut': j.statut, 'type': 'jalon'
            }
            for j in projet.jalons_planif.all()
        ]
        return Response({'activites': gantt_data, 'jalons': jalons})


class MembreEquipeViewSet(viewsets.ModelViewSet):
    queryset = MembreEquipeProjet.objects.select_related('user', 'projet').order_by('projet', 'role_projet')
    serializer_class = MembreEquipeSerializer
    permission_classes = [CanReadPP]

    def get_queryset(self):
        qs = super().get_queryset()
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return qs


class RisqueViewSet(viewsets.ModelViewSet):
    queryset = RisqueProjet.objects.select_related('projet', 'responsable_suivi').order_by('-date_identification')
    serializer_class = RisqueSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RisqueFilter
    search_fields = ['titre', 'description']
    permission_classes = [CanReadPP]

    def get_queryset(self):
        qs = super().get_queryset()
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return qs


class LivrableViewSet(viewsets.ModelViewSet):
    queryset = LivrableProjet.objects.select_related('projet', 'validateur').order_by('date_prevue')
    serializer_class = LivrableSerializer
    permission_classes = [CanReadPP]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return qs

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        livrable = self.get_object()
        if livrable.statut != 'soumis':
            return Response({'detail': 'Le livrable doit être soumis pour être validé.'}, status=400)
        livrable.valider(request.user)
        return Response(LivrableSerializer(livrable).data)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        livrable = self.get_object()
        livrable.statut = 'soumis'
        livrable.save(update_fields=['statut'])
        return Response(LivrableSerializer(livrable).data)


class PartenaireProgrammeViewSet(viewsets.ModelViewSet):
    queryset = PartenaireProgramme.objects.select_related('programme', 'partenaire').order_by('programme', 'type_participation')
    serializer_class = PartenaireProgrammeSerializer
    permission_classes = [CanReadPP]

    def get_queryset(self):
        qs = super().get_queryset()
        programme_id = self.request.query_params.get('programme')
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        return qs


class JalonProjetViewSet(viewsets.ModelViewSet):
    queryset = JalonProjet.objects.select_related('projet').order_by('date_prevue')
    serializer_class = JalonProjetSerializer
    permission_classes = [CanReadPP]

    def get_queryset(self):
        qs = super().get_queryset()
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return qs


# ─── Dashboard Portefeuille ────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadPP])
def portefeuille_dashboard(request):
    org_id = request.query_params.get('organisation')
    prog_qs = Programme.objects.all()
    proj_qs = Projet.objects.all()
    if org_id:
        prog_qs = prog_qs.filter(organisation_id=org_id)
        proj_qs = proj_qs.filter(organisation_id=org_id)

    projets_list = list(proj_qs)
    today = timezone.now().date()

    par_statut = dict(proj_qs.values_list('statut').annotate(nb=Count('id')))
    par_priorite = dict(proj_qs.values_list('priorite').annotate(nb=Count('id')))
    par_org = list(
        proj_qs.values('organisation__nom')
        .annotate(nb=Count('id'), budget=Sum('budget_initial'))
        .order_by('-nb')
    )

    return Response({
        'total_programmes': prog_qs.count(),
        'programmes_actifs': prog_qs.filter(statut='en_cours').count(),
        'total_projets': proj_qs.count(),
        'projets_actifs': proj_qs.filter(statut='en_cours').count(),
        'projets_en_retard': sum(1 for p in projets_list if p.est_en_retard),
        'projets_critiques': proj_qs.filter(priorite='critique').count(),
        'budget_total_programmes': prog_qs.aggregate(t=Sum('budget_total'))['t'] or 0,
        'budget_total_projets': proj_qs.aggregate(t=Sum('budget_initial'))['t'] or 0,
        'taux_avancement_moyen': proj_qs.filter(statut='en_cours').aggregate(
            avg=Avg('taux_avancement')
        )['avg'] or 0,
        'par_statut': par_statut,
        'par_priorite': par_priorite,
        'par_organisation': par_org,
    })
