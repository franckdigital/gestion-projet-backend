from django.db.models import Count, Sum, Avg, Q
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
    ActiviteExecution, AffectationRessource, DependanceActivite, RapportActivite,
    Tache, ChecklistItem, DependanceTache, CommentaireTache, HistoriqueTache,
    Livrable, VersionLivrable, ValidationLivrable, CommentaireLivrable,
    Reunion, ParticipantReunion, PointOrdreJour, CompteRendu,
    DecisionReunion, ActionReunion,
    Mission, MembreMission, OrdreMission, RapportMission, RapportAvancement,
)
from .serializers import (
    ActiviteExecutionListSerializer, ActiviteExecutionDetailSerializer,
    ActiviteExecutionCreateSerializer, AffectationRessourceSerializer,
    DependanceActiviteSerializer, RapportActiviteSerializer,
    TacheListSerializer, TacheDetailSerializer, ChecklistItemSerializer,
    DependanceTacheSerializer, CommentaireTacheSerializer, HistoriqueTacheSerializer,
    LivrableListSerializer, LivrableDetailSerializer, VersionLivrableSerializer,
    ValidationLivrableSerializer, CommentaireLivrableSerializer,
    ReunionListSerializer, ReunionDetailSerializer, ParticipantReunionSerializer,
    PointOrdreJourSerializer, CompteRenduSerializer, DecisionReunionSerializer,
    ActionReunionSerializer, MissionListSerializer, MissionDetailSerializer,
    MembreMissionSerializer, OrdreMissionSerializer, RapportMissionSerializer,
    RapportAvancementSerializer,
)
from .filters import ActiviteExecutionFilter, TacheFilter, LivrableFilter, ReunionFilter, MissionFilter

CanReadExec = HasModulePermission.for_module('execution', 'peut_lire')
CanEditExec = HasModulePermission.for_module('execution', 'peut_modifier')
CanValidateExec = HasModulePermission.for_module('execution', 'peut_valider')


# ─── M13 ─────────────────────────────────────────────────────────────────────

class ActiviteExecutionViewSet(viewsets.ModelViewSet):
    queryset = ActiviteExecution.objects.select_related(
        'projet', 'programme', 'responsable', 'created_by'
    ).prefetch_related('affectations', 'taches').order_by('ordre', 'date_debut_prevue')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ActiviteExecutionFilter
    search_fields = ['code', 'intitule', 'description']
    ordering_fields = ['code', 'date_debut_prevue', 'priorite', 'taux_avancement']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'kantt_data', 'kanban', 'stats']:
            return [CanReadExec()]
        return [CanEditExec()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ActiviteExecutionListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ActiviteExecutionCreateSerializer
        return ActiviteExecutionDetailSerializer

    def perform_create(self, serializer):
        act = serializer.save(created_by=self.request.user)
        AuditLog.log(self.request.user, 'create', module='execution',
                     objet_type='ActiviteExecution', objet_id=act.id, request=self.request)

    @action(detail=True, methods=['post'])
    def demarrer(self, request, pk=None):
        act = self.get_object()
        if act.statut not in ('planifiee', 'en_attente', 'suspendue'):
            return Response({'detail': 'Statut incompatible.'}, status=400)
        act.demarrer()
        return Response(ActiviteExecutionDetailSerializer(act).data)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        act = self.get_object()
        act.terminer()
        return Response(ActiviteExecutionDetailSerializer(act).data)

    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        act = self.get_object()
        act.suspendre(request.data.get('motif', ''))
        return Response(ActiviteExecutionDetailSerializer(act).data)

    @action(detail=True, methods=['post'])
    def update_avancement(self, request, pk=None):
        act = self.get_object()
        taux = request.data.get('taux_avancement', 0)
        if not (0 <= float(taux) <= 100):
            return Response({'detail': 'Taux entre 0 et 100.'}, status=400)
        act.taux_avancement = taux
        act.save(update_fields=['taux_avancement'])
        return Response({'taux_avancement': float(taux)})

    @action(detail=False, methods=['get'])
    def kanban(self, request):
        projet_id = request.query_params.get('projet')
        qs = ActiviteExecution.objects.all()
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return Response({
            s: ActiviteExecutionListSerializer(qs.filter(statut=s).order_by('ordre'), many=True).data
            for s, _ in ActiviteExecution.STATUT_CHOICES
        })

    @action(detail=False, methods=['get'])
    def gantt_data(self, request):
        projet_id = request.query_params.get('projet')
        if not projet_id:
            return Response({'detail': 'projet requis.'}, status=400)
        activites = ActiviteExecution.objects.filter(
            projet_id=projet_id
        ).prefetch_related('dependances_sortantes').order_by('ordre')
        return Response([{
            'id': a.id, 'code': a.code, 'title': a.intitule, 'statut': a.statut,
            'priorite': a.priorite, 'start': a.date_debut_prevue, 'end': a.date_fin_prevue,
            'start_reelle': a.date_debut_reelle, 'end_reelle': a.date_fin_reelle,
            'taux': float(a.taux_avancement), 'responsable_id': a.responsable_id,
            'parent_id': a.parent_id,
            'deps': [{'cible': d.activite_cible_id, 'type': d.type_dependance} for d in a.dependances_sortantes.all()],
        } for a in activites])

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        act = self.get_object()
        taches = act.taches.all()
        return Response({
            'taux_avancement': float(act.taux_avancement), 'est_en_retard': act.est_en_retard,
            'taches': {'total': taches.count(), 'terminees': taches.filter(statut='terminee').count(),
                       'en_retard': sum(1 for t in taches if t.est_en_retard)},
            'budget': {'prevu': float(act.budget_prevu), 'realise': float(act.budget_realise)},
        })


class AffectationRessourceViewSet(viewsets.ModelViewSet):
    queryset = AffectationRessource.objects.select_related('activite', 'utilisateur')
    serializer_class = AffectationRessourceSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        a = self.request.query_params.get('activite')
        return qs.filter(activite_id=a) if a else qs


class DependanceActiviteViewSet(viewsets.ModelViewSet):
    queryset = DependanceActivite.objects.all()
    serializer_class = DependanceActiviteSerializer
    permission_classes = [CanReadExec]


class RapportActiviteViewSet(viewsets.ModelViewSet):
    queryset = RapportActivite.objects.order_by('-date_rapport')
    serializer_class = RapportActiviteSerializer
    permission_classes = [CanReadExec]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        a = self.request.query_params.get('activite')
        return qs.filter(activite_id=a) if a else qs

    def perform_create(self, s):
        s.save(redacteur=self.request.user)


# ─── M14 ─────────────────────────────────────────────────────────────────────

class TacheViewSet(viewsets.ModelViewSet):
    queryset = Tache.objects.select_related('activite', 'assignee', 'created_by').prefetch_related('checklist', 'sous_taches').order_by('ordre', 'date_echeance')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TacheFilter
    search_fields = ['code', 'titre']
    ordering_fields = ['priorite', 'date_echeance', 'taux_avancement']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'kanban', 'mes_taches', 'stats_equipe']:
            return [CanReadExec()]
        return [CanEditExec()]

    def get_serializer_class(self):
        return TacheListSerializer if self.action == 'list' else TacheDetailSerializer

    def perform_create(self, s):
        t = s.save(created_by=self.request.user)
        HistoriqueTache.objects.create(tache=t, user=self.request.user, action='Creee', nouveau_statut=t.statut)

    @action(detail=False, methods=['get'])
    def kanban(self, request):
        activite_id = request.query_params.get('activite')
        projet_id = request.query_params.get('projet')
        qs = Tache.objects.filter(parent__isnull=True)
        if activite_id:
            qs = qs.filter(activite_id=activite_id)
        elif projet_id:
            qs = qs.filter(activite__projet_id=projet_id)
        return Response({s: {'label': l, 'taches': TacheListSerializer(qs.filter(statut=s).order_by('ordre'), many=True).data}
                         for s, l in Tache.STATUT_CHOICES})

    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        t = self.get_object()
        ns = request.data.get('statut')
        if ns not in [s[0] for s in Tache.STATUT_CHOICES]:
            return Response({'detail': 'Statut invalide.'}, status=400)
        old = t.statut
        t.statut = ns
        if ns == 'terminee':
            t.date_completion = timezone.now().date()
            t.taux_avancement = 100
        t.save()
        HistoriqueTache.objects.create(tache=t, user=request.user, action='Statut modifie', ancien_statut=old, nouveau_statut=ns)
        return Response(TacheDetailSerializer(t).data)

    @action(detail=False, methods=['get'])
    def mes_taches(self, request):
        qs = Tache.objects.filter(Q(assignee=request.user) | Q(co_assignees=request.user)).exclude(statut__in=['terminee', 'annulee']).order_by('date_echeance')
        return Response(TacheListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def stats_equipe(self, request):
        projet_id = request.query_params.get('projet')
        qs = Tache.objects.filter(activite__projet_id=projet_id) if projet_id else Tache.objects.all()
        return Response({
            'total': qs.count(), 'terminees': qs.filter(statut='terminee').count(),
            'en_cours': qs.filter(statut='en_cours').count(),
            'en_retard': sum(1 for t in qs if t.est_en_retard),
            'critiques': qs.filter(priorite='critique').count(),
        })


class ChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItem.objects.order_by('ordre')
    serializer_class = ChecklistItemSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        t = self.request.query_params.get('tache')
        return qs.filter(tache_id=t) if t else qs

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        item = self.get_object()
        item.uncomplete_item() if item.complete else item.complete_item(request.user)
        return Response(ChecklistItemSerializer(item).data)


class DependanceTacheViewSet(viewsets.ModelViewSet):
    queryset = DependanceTache.objects.select_related('tache_source', 'tache_cible')
    serializer_class = DependanceTacheSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        tache_id = self.request.query_params.get('tache')
        projet_id = self.request.query_params.get('projet')
        if tache_id:
            qs = qs.filter(Q(tache_source_id=tache_id) | Q(tache_cible_id=tache_id))
        elif projet_id:
            qs = qs.filter(
                Q(tache_source__activite__projet_id=projet_id) |
                Q(tache_cible__activite__projet_id=projet_id)
            )
        return qs


class HistoriqueTacheViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HistoriqueTache.objects.select_related('tache', 'user').order_by('created_at')
    serializer_class = HistoriqueTacheSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        t = self.request.query_params.get('tache')
        return qs.filter(tache_id=t) if t else qs


class CommentaireTacheViewSet(viewsets.ModelViewSet):
    queryset = CommentaireTache.objects.select_related('auteur').order_by('created_at')
    serializer_class = CommentaireTacheSerializer
    permission_classes = [CanReadExec]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(auteur=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        t = self.request.query_params.get('tache')
        return qs.filter(tache_id=t) if t else qs


# ─── M15 ─────────────────────────────────────────────────────────────────────

class LivrableViewSet(viewsets.ModelViewSet):
    queryset = Livrable.objects.select_related('projet', 'activite', 'responsable', 'created_by').prefetch_related('versions', 'validations').order_by('date_prevue')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LivrableFilter
    search_fields = ['code', 'titre']
    ordering_fields = ['date_prevue', 'statut']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadExec()]
        if self.action in ['approuver_etape', 'rejeter_etape', 'publier']:
            return [CanValidateExec()]
        return [CanEditExec()]

    def get_serializer_class(self):
        return LivrableListSerializer if self.action == 'list' else LivrableDetailSerializer

    def perform_create(self, s):
        livrable = s.save(created_by=self.request.user)
        for etape, ordre in [('chef_projet', 1), ('responsable_programme', 2), ('coordonnateur', 3), ('final', 4)]:
            ValidationLivrable.objects.create(livrable=livrable, etape=etape, ordre=ordre)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        l = self.get_object()
        if l.statut != 'brouillon':
            return Response({'detail': 'Seul un brouillon peut etre soumis.'}, status=400)
        l.soumettre()
        return Response(LivrableDetailSerializer(l).data)

    @action(detail=True, methods=['post'])
    def approuver_etape(self, request, pk=None):
        l = self.get_object()
        etape = request.data.get('etape')
        try:
            v = l.validations.get(etape=etape, statut='en_attente')
        except ValidationLivrable.DoesNotExist:
            return Response({'detail': 'Etape introuvable.'}, status=404)
        v.approuver(request.user, request.data.get('commentaire', ''))
        if not l.validations.filter(statut='en_attente').exists():
            l.statut = 'valide'
            l.date_livraison = l.date_livraison or timezone.now().date()
            l.save(update_fields=['statut', 'date_livraison'])
        return Response(LivrableDetailSerializer(l).data)

    @action(detail=True, methods=['post'])
    def rejeter_etape(self, request, pk=None):
        l = self.get_object()
        etape = request.data.get('etape')
        try:
            v = l.validations.get(etape=etape, statut='en_attente')
        except ValidationLivrable.DoesNotExist:
            return Response({'detail': 'Etape introuvable.'}, status=404)
        v.rejeter(request.user, request.data.get('commentaire', ''))
        return Response(LivrableDetailSerializer(l).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        l = self.get_object()
        if l.statut != 'valide':
            return Response({'detail': 'Seul un livrable valide peut etre publie.'}, status=400)
        l.publier()
        # Archivage automatique dans la GED (M15 §6)
        ged_ref = self._archiver_ged(l, request.user)
        data = LivrableDetailSerializer(l).data
        data['ged_reference'] = ged_ref
        return Response(data)

    def _archiver_ged(self, livrable, user):
        """Crée automatiquement un document GED pour ce livrable publié."""
        try:
            from ged.models import Document, Categorie
            # Catégorie GED "livrables" ou à défaut la première disponible
            cat = Categorie.objects.filter(domaine='projet').first()
            # Type GED selon le type de livrable
            type_map = {
                'rapport': 'rapport', 'etude': 'rapport', 'tdr': 'tdr',
                'manuel': 'rapport', 'document': 'rapport', 'logiciel': 'autre',
                'plateforme': 'autre', 'bdd': 'autre', 'api': 'autre',
            }
            type_ged = type_map.get(livrable.type_livrable, 'livrable')
            # Récupérer le fichier depuis la dernière version
            derniere_version = livrable.versions.filter(est_courante=True).first()
            doc = Document.objects.create(
                titre=livrable.titre,
                description=livrable.description or f"Livrable {livrable.code} — archivé automatiquement depuis M15",
                type_document=type_ged,
                categorie=cat,
                projet=livrable.projet,
                activite=livrable.activite,
                version=livrable.version_courante or '1.0',
                confidentialite='interne',
                statut='publie',
                auteur=user,
                source=f"M15 — Livrable {livrable.code}",
                mots_cles=f"livrable {livrable.type_livrable} {livrable.code}",
            )
            if derniere_version and derniere_version.fichier:
                import shutil, os
                from django.core.files import File
                try:
                    doc.fichier.save(
                        os.path.basename(derniere_version.fichier.name),
                        File(derniere_version.fichier.open('rb')),
                        save=True,
                    )
                except Exception:
                    pass
            return doc.reference
        except Exception:
            return None

    @action(detail=True, methods=['get'])
    def lien_ged(self, request, pk=None):
        """Retourne la référence GED du livrable si disponible."""
        l = self.get_object()
        try:
            from ged.models import Document
            docs = Document.objects.filter(
                source__icontains=l.code
            ).values('id', 'reference', 'titre', 'statut', 'created_at')
            return Response({'livrable': l.code, 'documents_ged': list(docs)})
        except Exception:
            return Response({'livrable': l.code, 'documents_ged': []})


class VersionLivrableViewSet(viewsets.ModelViewSet):
    queryset = VersionLivrable.objects.order_by('-date_upload')
    serializer_class = VersionLivrableSerializer
    permission_classes = [CanReadExec]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(uploaded_by=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        l = self.request.query_params.get('livrable')
        return qs.filter(livrable_id=l) if l else qs


class CommentaireLivrableViewSet(viewsets.ModelViewSet):
    queryset = CommentaireLivrable.objects.order_by('created_at')
    serializer_class = CommentaireLivrableSerializer
    permission_classes = [CanReadExec]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(auteur=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        l = self.request.query_params.get('livrable')
        return qs.filter(livrable_id=l) if l else qs


# ─── M16 Reunions ─────────────────────────────────────────────────────────────

class ReunionViewSet(viewsets.ModelViewSet):
    queryset = Reunion.objects.select_related('organisateur', 'projet', 'programme', 'created_by').prefetch_related('participants', 'points_ordre_jour').order_by('-date', '-heure_debut')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ReunionFilter
    search_fields = ['objet', 'reference', 'lieu']
    permission_classes = [CanReadExec]

    def get_serializer_class(self):
        return ReunionListSerializer if self.action == 'list' else ReunionDetailSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user, organisateur=self.request.user)

    @action(detail=True, methods=['post'])
    def confirmer(self, request, pk=None):
        r = self.get_object()
        r.statut = 'confirmee'
        r.save(update_fields=['statut'])
        return Response(ReunionDetailSerializer(r).data)

    @action(detail=True, methods=['post'])
    def reporter(self, request, pk=None):
        r = self.get_object()
        r.statut = 'reportee'
        nd = request.data.get('nouvelle_date')
        if nd:
            r.date = nd
        r.save()
        return Response(ReunionDetailSerializer(r).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        r = self.get_object()
        r.statut = 'annulee'
        r.save(update_fields=['statut'])
        return Response(ReunionDetailSerializer(r).data)

    @action(detail=True, methods=['post'])
    def marquer_tenue(self, request, pk=None):
        r = self.get_object()
        r.statut = 'tenue'
        r.save(update_fields=['statut'])
        return Response(ReunionDetailSerializer(r).data)

    @action(detail=True, methods=['post'])
    def envoyer_invitations(self, request, pk=None):
        r = self.get_object()
        count = r.participants.filter(utilisateur__isnull=False).count()
        r.participants.filter(utilisateur__isnull=False).update(date_invitation=timezone.now())
        r.rappel_envoye = True
        r.save(update_fields=['rappel_envoye'])
        return Response({'detail': f'{count} invitation(s) envoyee(s).', 'count': count})

    @action(detail=True, methods=['post'])
    def generer_cr_ia(self, request, pk=None):
        """
        Génère un compte rendu structuré par IA à partir de :
        - L'ordre du jour
        - Les décisions existantes
        - Les actions issues du CR (si saisi en texte libre dans notes_ia)
        - Le texte brut fourni en request.data['notes'] (optionnel)
        """
        reunion = self.get_object()
        notes_libres = request.data.get('notes', '')

        points = list(reunion.points_ordre_jour.order_by('ordre').values('intitule', 'duree_prevue', 'notes'))
        participants = list(reunion.participants.filter(statut_presence__in=['present', 'confirme']).values(
            'utilisateur__first_name', 'utilisateur__last_name',
            'nom_externe', 'fonction_externe', 'organisation_externe'
        ))

        # ── Synthèse ─────────────────────────────────────────────────────────
        synthese_lines = [
            f"Réunion du {reunion.date} — {reunion.objet}",
            f"Organisateur : {getattr(reunion.organisateur, 'get_full_name', lambda: str(reunion.organisateur))()}",
            f"Lieu / Plateforme : {reunion.lieu or reunion.plateforme or 'Non précisé'}",
            f"Durée prévue : {reunion.heure_debut or '—'} → {reunion.heure_fin or '—'}",
        ]
        synthese = '\n'.join(synthese_lines)

        # ── Participants ──────────────────────────────────────────────────────
        part_lines = []
        for p in participants:
            if p.get('utilisateur__first_name'):
                part_lines.append(f"• {p['utilisateur__first_name']} {p['utilisateur__last_name']}")
            elif p.get('nom_externe'):
                org = f" ({p['organisation_externe']})" if p.get('organisation_externe') else ''
                part_lines.append(f"• {p['nom_externe']}{org}")
        participants_txt = '\n'.join(part_lines) if part_lines else '(aucun participant enregistré)'

        # ── Points discussions ────────────────────────────────────────────────
        disc_lines = []
        for i, pt in enumerate(points, 1):
            dur = f" [{pt['duree_prevue']} min]" if pt.get('duree_prevue') else ''
            disc_lines.append(f"{i}. {pt['intitule']}{dur}")
            if pt.get('notes'):
                disc_lines.append(f"   → {pt['notes']}")
        discussions = '\n'.join(disc_lines) if disc_lines else 'Points non renseignés dans l\'ordre du jour.'

        # ── Détection d'actions depuis les notes libres ───────────────────────
        actions_detectees = []
        if notes_libres:
            TRIGGER_MOTS = ['envoyer', 'préparer', 'organiser', 'valider', 'soumettre',
                            'contacter', 'relancer', 'finaliser', 'produire', 'rédiger',
                            'transmettre', 'partager', 'convoquer', 'planifier', 'assurer']
            for ligne in notes_libres.split('\n'):
                ligne = ligne.strip().lstrip('•-*').strip()
                if not ligne:
                    continue
                if any(mot in ligne.lower() for mot in TRIGGER_MOTS):
                    actions_detectees.append(ligne)
                elif ligne.startswith(('Action:', 'ACTION:', 'À faire:', 'Todo:')):
                    actions_detectees.append(ligne.split(':', 1)[-1].strip())

        # ── Décisions en texte ────────────────────────────────────────────────
        decisions_existantes = list(
            reunion.compte_rendu.decisions.values('intitule', 'responsable__first_name', 'echeance')
            if hasattr(reunion, 'compte_rendu') else []
        )
        decisions_txt = ''
        if decisions_existantes:
            decisions_txt = '\n'.join(
                f"• {d['intitule']} — Resp. {d.get('responsable__first_name', '?')} — Échéance : {d.get('echeance', '?')}"
                for d in decisions_existantes
            )

        # ── Créer / mettre à jour le CR ───────────────────────────────────────
        cr, created = CompteRendu.objects.get_or_create(
            reunion=reunion,
            defaults={'redacteur': request.user}
        )
        cr.synthese        = synthese
        cr.participants_presents = participants
        cr.discussions     = discussions
        if decisions_txt:
            cr.decisions_prises = decisions_txt
        cr.genere_par_ia   = True
        cr.save(update_fields=['synthese', 'participants_presents', 'discussions', 'decisions_prises', 'genere_par_ia'])

        # ── Créer automatiquement des ActionReunion depuis les notes ─────────
        from .models import ActionReunion
        actions_crees = []
        for action_txt in actions_detectees:
            if not cr.actions.filter(libelle=action_txt).exists():
                ActionReunion.objects.create(compte_rendu=cr, libelle=action_txt)
                actions_crees.append(action_txt)

        return Response({
            **CompteRenduSerializer(cr).data,
            'actions_ia_detectees': actions_crees,
            'nb_actions': len(actions_crees),
        })


class ParticipantReunionViewSet(viewsets.ModelViewSet):
    queryset = ParticipantReunion.objects.select_related('reunion', 'utilisateur')
    serializer_class = ParticipantReunionSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        r = self.request.query_params.get('reunion')
        return qs.filter(reunion_id=r) if r else qs

    @action(detail=True, methods=['post'])
    def confirmer_presence(self, request, pk=None):
        p = self.get_object()
        p.statut_presence = 'confirme'
        p.date_confirmation = timezone.now()
        p.save(update_fields=['statut_presence', 'date_confirmation'])
        return Response(ParticipantReunionSerializer(p).data)

    @action(detail=True, methods=['post'])
    def marquer_present(self, request, pk=None):
        p = self.get_object()
        p.statut_presence = 'present'
        p.save(update_fields=['statut_presence'])
        return Response(ParticipantReunionSerializer(p).data)


class PointOrdreJourViewSet(viewsets.ModelViewSet):
    queryset = PointOrdreJour.objects.all().order_by('ordre')
    serializer_class = PointOrdreJourSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        r = self.request.query_params.get('reunion')
        return qs.filter(reunion_id=r) if r else qs


class CompteRenduViewSet(viewsets.ModelViewSet):
    queryset = CompteRendu.objects.prefetch_related('decisions', 'actions').order_by('-created_at')
    serializer_class = CompteRenduSerializer
    permission_classes = [CanReadExec]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(redacteur=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        cr = self.get_object()
        cr.statut = 'valide'
        cr.valide_par = request.user
        cr.date_validation = timezone.now()
        cr.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(CompteRenduSerializer(cr).data)

    @action(detail=True, methods=['post'])
    def generer_taches(self, request, pk=None):
        cr = self.get_object()
        activite_id = request.data.get('activite_id')
        activite = None
        if activite_id:
            try:
                activite = ActiviteExecution.objects.get(id=activite_id)
            except ActiviteExecution.DoesNotExist:
                pass
        created = []
        for ai in cr.actions.filter(tache_generee__isnull=True):
            t = ai.generer_tache(activite=activite, created_by=request.user)
            created.append({'action': ai.libelle, 'tache_id': t.id})
        return Response({'taches_creees': len(created), 'details': created})


class DecisionReunionViewSet(viewsets.ModelViewSet):
    queryset = DecisionReunion.objects.all().order_by('echeance')
    serializer_class = DecisionReunionSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        cr = self.request.query_params.get('compte_rendu')
        return qs.filter(compte_rendu_id=cr) if cr else qs


class ActionReunionViewSet(viewsets.ModelViewSet):
    queryset = ActionReunion.objects.all().order_by('echeance')
    serializer_class = ActionReunionSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        cr = self.request.query_params.get('compte_rendu')
        resp = self.request.query_params.get('responsable')
        if cr:
            qs = qs.filter(compte_rendu_id=cr)
        if resp:
            qs = qs.filter(responsable_id=resp)
        return qs


# ─── M16 Missions ─────────────────────────────────────────────────────────────

class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.select_related('projet', 'programme', 'demandeur', 'approuve_par').prefetch_related('membres').order_by('-date_debut')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MissionFilter
    search_fields = ['reference', 'objet', 'destination']
    permission_classes = [CanReadExec]

    def get_serializer_class(self):
        return MissionListSerializer if self.action == 'list' else MissionDetailSerializer

    def perform_create(self, s):
        s.save(demandeur=self.request.user)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        m = self.get_object()
        if m.statut != 'planifiee':
            return Response({'detail': 'Mission deja traitee.'}, status=400)
        m.approuver(request.user)
        return Response(MissionDetailSerializer(m).data)

    @action(detail=True, methods=['post'])
    def demarrer(self, request, pk=None):
        m = self.get_object()
        m.statut = 'en_cours'
        m.save(update_fields=['statut'])
        return Response(MissionDetailSerializer(m).data)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        m = self.get_object()
        m.statut = 'terminee'
        m.save(update_fields=['statut'])
        return Response(MissionDetailSerializer(m).data)

    @action(detail=True, methods=['post'])
    def generer_ordre_mission(self, request, pk=None):
        m = self.get_object()
        membres = list(m.membres.values_list('user__first_name', 'user__last_name'))
        noms = ', '.join(f"{p[0]} {p[1]}" for p in membres)
        contenu = f"ORDRE DE MISSION\nObjet: {m.objet}\nDestination: {m.destination}\nPeriode: {m.date_debut} au {m.date_fin}\nMembres: {noms or 'N/A'}\nBudget: {m.budget_prevu}"
        om, _ = OrdreMission.objects.get_or_create(mission=m, defaults={'signataire': request.user, 'contenu': contenu, 'statut': 'emis'})
        if not _:
            om.contenu = contenu
            om.statut = 'emis'
            om.save(update_fields=['contenu', 'statut'])
        return Response(OrdreMissionSerializer(om).data)


class MembreMissionViewSet(viewsets.ModelViewSet):
    queryset = MembreMission.objects.select_related('mission', 'user')
    serializer_class = MembreMissionSerializer
    permission_classes = [CanReadExec]

    def get_queryset(self):
        qs = super().get_queryset()
        m = self.request.query_params.get('mission')
        return qs.filter(mission_id=m) if m else qs


class OrdreMissionViewSet(viewsets.ModelViewSet):
    queryset = OrdreMission.objects.all()
    serializer_class = OrdreMissionSerializer
    permission_classes = [CanReadExec]
    parser_classes = [MultiPartParser, FormParser]


class RapportMissionViewSet(viewsets.ModelViewSet):
    queryset = RapportMission.objects.all()
    serializer_class = RapportMissionSerializer
    permission_classes = [CanReadExec]
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
        return Response(RapportMissionSerializer(r).data)


class RapportAvancementViewSet(viewsets.ModelViewSet):
    queryset = RapportAvancement.objects.order_by('-date_rapport')
    serializer_class = RapportAvancementSerializer
    permission_classes = [CanReadExec]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, s):
        s.save(redacteur=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params.get('projet')
        return qs.filter(projet_id=p) if p else qs


# ─── Dashboard ────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadExec])
def dashboard_execution(request):
    projet_id = request.query_params.get('projet')
    today = timezone.now().date()

    qs_act = ActiviteExecution.objects.all()
    qs_tache = Tache.objects.all()
    qs_livrable = Livrable.objects.all()
    qs_reunion = Reunion.objects.all()
    qs_mission = Mission.objects.all()

    if projet_id:
        qs_act = qs_act.filter(projet_id=projet_id)
        qs_tache = qs_tache.filter(activite__projet_id=projet_id)
        qs_livrable = qs_livrable.filter(projet_id=projet_id)
        qs_reunion = qs_reunion.filter(projet_id=projet_id)
        qs_mission = qs_mission.filter(projet_id=projet_id)

    return Response({
        'activites': {
            'total': qs_act.count(), 'en_cours': qs_act.filter(statut='en_cours').count(),
            'terminees': qs_act.filter(statut='terminee').count(),
            'en_retard': sum(1 for a in qs_act if a.est_en_retard),
            'taux_moyen': float(qs_act.aggregate(avg=Avg('taux_avancement'))['avg'] or 0),
        },
        'taches': {
            'total': qs_tache.count(), 'en_cours': qs_tache.filter(statut='en_cours').count(),
            'terminees': qs_tache.filter(statut='terminee').count(),
            'en_retard': sum(1 for t in qs_tache if t.est_en_retard),
            'critiques': qs_tache.filter(priorite='critique').count(),
        },
        'livrables': {
            'total': qs_livrable.count(), 'valides': qs_livrable.filter(statut='valide').count(),
            'en_retard': sum(1 for l in qs_livrable if l.est_en_retard),
            'rejetes': qs_livrable.filter(statut='rejete').count(),
        },
        'reunions': {
            'ce_mois': qs_reunion.filter(date__month=today.month, date__year=today.year).count(),
            'a_venir': qs_reunion.filter(date__gte=today, statut__in=['planifiee', 'confirmee']).count(),
            'tenues': qs_reunion.filter(statut='tenue').count(),
        },
        'missions': {
            'total': qs_mission.count(), 'en_cours': qs_mission.filter(statut='en_cours').count(),
            'terminees': qs_mission.filter(statut='terminee').count(),
        },
    })
