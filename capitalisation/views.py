from django.db.models import Count, Q
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
    FicheCapitalisation, EntreeBibliotheque, CommentaireFiche, CentreConnaissance,
)
from .serializers import (
    FicheCapitalisationListSerializer, FicheCapitalisationDetailSerializer,
    FicheCapitalisationCreateSerializer,
    EntreeBibliothequeListSerializer, EntreeBibliothequeDetailSerializer,
    CommentaireFicheSerializer,
    CentreConnaissanceListSerializer, CentreConnaissanceDetailSerializer,
)
from .filters import (
    FicheCapitalisationFilter, EntreeBibliothequeFilter,
    CommentaireFicheFilter, CentreConnaissanceFilter,
)

CanReadCap = HasModulePermission.for_module('capitalisation', 'peut_lire')
CanEditCap = HasModulePermission.for_module('capitalisation', 'peut_modifier')
CanValidateCap = HasModulePermission.for_module('capitalisation', 'peut_valider')


# ─── FicheCapitalisation ─────────────────────────────────────────────────────

class FicheCapitalisationViewSet(viewsets.ModelViewSet):
    queryset = FicheCapitalisation.objects.select_related(
        'auteur', 'valide_par', 'programme', 'projet', 'document_ged'
    ).prefetch_related('contributeurs', 'commentaires').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FicheCapitalisationFilter
    search_fields = ['reference', 'titre', 'mots_cles', 'lecon_principale', 'solution_approche']
    ordering_fields = ['created_at', 'titre', 'statut', 'nb_consultations', 'nb_favoris']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'recherche_full_text']:
            return [CanReadCap()]
        if self.action in ['valider', 'publier']:
            return [CanValidateCap()]
        return [CanEditCap()]

    def get_serializer_class(self):
        if self.action == 'list':
            return FicheCapitalisationListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return FicheCapitalisationCreateSerializer
        return FicheCapitalisationDetailSerializer

    def perform_create(self, serializer):
        fiche = serializer.save(auteur=self.request.user)
        AuditLog.log(self.request.user, 'create', module='capitalisation',
                     objet_type='FicheCapitalisation', objet_id=fiche.id, request=self.request)

    # ── Actions de workflow ──────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        """Soumet la fiche pour validation (brouillon → soumise)."""
        fiche = self.get_object()
        if fiche.statut != 'brouillon':
            return Response(
                {'detail': 'Seules les fiches en brouillon peuvent être soumises.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fiche.statut = 'soumise'
        fiche.save(update_fields=['statut', 'updated_at'])
        AuditLog.log(request.user, 'update', module='capitalisation',
                     objet_type='FicheCapitalisation', objet_id=fiche.id, request=request,
                     details={'detail': 'Fiche soumise pour validation'})
        return Response(FicheCapitalisationDetailSerializer(fiche).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide la fiche (soumise → validée)."""
        fiche = self.get_object()
        if fiche.statut != 'soumise':
            return Response(
                {'detail': 'Seules les fiches soumises peuvent être validées.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fiche.statut = 'validee'
        fiche.valide_par = request.user
        fiche.date_validation = timezone.now()
        fiche.save(update_fields=['statut', 'valide_par', 'date_validation', 'updated_at'])
        AuditLog.log(request.user, 'update', module='capitalisation',
                     objet_type='FicheCapitalisation', objet_id=fiche.id, request=request,
                     details={'detail': 'Fiche validée'})
        return Response(FicheCapitalisationDetailSerializer(fiche).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        """Publie la fiche (validée → publiée)."""
        fiche = self.get_object()
        if fiche.statut not in ('validee', 'soumise'):
            return Response(
                {'detail': 'La fiche doit être validée ou soumise pour être publiée.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fiche.statut = 'publiee'
        if not fiche.valide_par:
            fiche.valide_par = request.user
            fiche.date_validation = timezone.now()
        fiche.save(update_fields=['statut', 'valide_par', 'date_validation', 'updated_at'])
        AuditLog.log(request.user, 'update', module='capitalisation',
                     objet_type='FicheCapitalisation', objet_id=fiche.id, request=request,
                     details={'detail': 'Fiche publiée'})
        return Response(FicheCapitalisationDetailSerializer(fiche).data)

    @action(detail=True, methods=['post'])
    def incrementer_consultation(self, request, pk=None):
        """Incrémente le compteur de consultations."""
        fiche = self.get_object()
        FicheCapitalisation.objects.filter(pk=fiche.pk).update(
            nb_consultations=fiche.nb_consultations + 1
        )
        fiche.refresh_from_db(fields=['nb_consultations'])
        return Response({'nb_consultations': fiche.nb_consultations})

    @action(detail=False, methods=['get'])
    def recherche_full_text(self, request):
        """Recherche dans titre, mots_cles, tags (JSON), lecon_principale."""
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response(
                {'detail': 'Paramètre "q" requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = FicheCapitalisation.objects.filter(
            Q(titre__icontains=q)
            | Q(mots_cles__icontains=q)
            | Q(lecon_principale__icontains=q)
            | Q(solution_approche__icontains=q)
            | Q(recommandation__icontains=q)
        ).select_related('auteur', 'programme', 'projet').order_by('-nb_consultations', '-created_at')
        serializer = FicheCapitalisationListSerializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})

    @action(detail=False, methods=['post'])
    def generer_ia(self, request):
        """
        Génère une fiche de capitalisation assistée par IA.
        Crée une fiche en brouillon avec genere_par_ia=True.
        """
        titre = request.data.get('titre', '')
        domaine = request.data.get('domaine', 'gestion_projet')
        type_fiche = request.data.get('type_fiche', 'lecon_apprise')
        contexte = request.data.get('contexte', '')
        programme_id = request.data.get('programme')
        projet_id = request.data.get('projet')

        if not titre:
            return Response(
                {'detail': 'Le titre est requis pour la génération IA.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Simulation de génération IA : contenu généré automatiquement
        lecon_generee = (
            f"[Généré par IA] Sur la base du contexte fourni pour « {titre} », "
            "la leçon principale identifiée est : l'importance d'une approche structurée "
            "et participative dans la mise en œuvre des activités."
        )
        solution_generee = (
            f"[Généré par IA] Approche proposée pour « {titre} » : "
            "mettre en place un mécanisme de coordination régulière entre les parties prenantes, "
            "documenter les processus dès le démarrage et assurer un suivi continu des indicateurs."
        )

        fiche = FicheCapitalisation.objects.create(
            titre=titre,
            type_fiche=type_fiche,
            domaine=domaine,
            statut='brouillon',
            auteur=request.user,
            contexte=contexte,
            lecon_principale=lecon_generee,
            solution_approche=solution_generee,
            recommandation='[Généré par IA] À compléter et valider par un expert.',
            genere_par_ia=True,
            programme_id=programme_id,
            projet_id=projet_id,
        )
        AuditLog.log(request.user, 'create', module='capitalisation',
                     objet_type='FicheCapitalisation', objet_id=fiche.id, request=request,
                     details={'detail': 'Fiche générée par IA'})
        return Response(
            FicheCapitalisationDetailSerializer(fiche).data,
            status=status.HTTP_201_CREATED,
        )


# ─── EntreeBibliotheque ───────────────────────────────────────────────────────

class EntreeBibliothequeViewSet(viewsets.ModelViewSet):
    queryset = EntreeBibliotheque.objects.select_related(
        'ajoute_par', 'programme', 'projet'
    ).order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EntreeBibliothequeFilter
    search_fields = ['titre', 'description', 'auteur', 'organisation', 'mots_cles']
    ordering_fields = ['titre', 'categorie', 'annee_publication', 'nb_telechargements', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'telecharger']:
            return [CanReadCap()]
        return [CanEditCap()]

    def get_serializer_class(self):
        if self.action == 'list':
            return EntreeBibliothequeListSerializer
        return EntreeBibliothequeDetailSerializer

    def perform_create(self, serializer):
        entree = serializer.save(ajoute_par=self.request.user)
        AuditLog.log(self.request.user, 'create', module='capitalisation',
                     objet_type='EntreeBibliotheque', objet_id=entree.id, request=self.request)

    @action(detail=True, methods=['post'])
    def telecharger(self, request, pk=None):
        """Incrémente le compteur de téléchargements et retourne le lien de fichier."""
        entree = self.get_object()
        EntreeBibliotheque.objects.filter(pk=entree.pk).update(
            nb_telechargements=entree.nb_telechargements + 1
        )
        entree.refresh_from_db(fields=['nb_telechargements'])

        fichier_url = request.build_absolute_uri(entree.fichier.url) if entree.fichier else None
        return Response({
            'nb_telechargements': entree.nb_telechargements,
            'fichier_url': fichier_url,
            'url_externe': entree.url_externe,
        })


# ─── CommentaireFiche ─────────────────────────────────────────────────────────

class CommentaireFicheViewSet(viewsets.ModelViewSet):
    queryset = CommentaireFiche.objects.select_related('auteur', 'fiche', 'en_reponse_a').order_by(
        'created_at')
    serializer_class = CommentaireFicheSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CommentaireFicheFilter
    ordering_fields = ['created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadCap()]
        return [CanEditCap()]

    def perform_create(self, serializer):
        commentaire = serializer.save(auteur=self.request.user)
        AuditLog.log(self.request.user, 'create', module='capitalisation',
                     objet_type='CommentaireFiche', objet_id=commentaire.id, request=self.request)


# ─── CentreConnaissance ───────────────────────────────────────────────────────

class CentreConnaissanceViewSet(viewsets.ModelViewSet):
    queryset = CentreConnaissance.objects.select_related('responsable').prefetch_related(
        'fiches', 'entrees_bibliotheque'
    ).order_by('domaine', 'nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CentreConnaissanceFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'domaine', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadCap()]
        return [CanEditCap()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CentreConnaissanceListSerializer
        return CentreConnaissanceDetailSerializer


# ─── Dashboard Capitalisation ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([HasModulePermission.for_module('capitalisation', 'peut_lire')])
def dashboard_capitalisation(request):
    """Dashboard capitalisation : statistiques et fiches top consultées."""
    # Fiches par type
    fiches_par_type = list(
        FicheCapitalisation.objects.values('type_fiche')
        .annotate(nb=Count('id'))
        .order_by('type_fiche')
    )

    # Fiches par domaine
    fiches_par_domaine = list(
        FicheCapitalisation.objects.values('domaine')
        .annotate(nb=Count('id'))
        .order_by('domaine')
    )

    # Fiches par statut
    fiches_par_statut = list(
        FicheCapitalisation.objects.values('statut')
        .annotate(nb=Count('id'))
        .order_by('statut')
    )

    # Compteurs globaux
    nb_fiches_total = FicheCapitalisation.objects.count()
    nb_fiches_publiees = FicheCapitalisation.objects.filter(statut='publiee').count()
    nb_fiches_ia = FicheCapitalisation.objects.filter(genere_par_ia=True).count()
    nb_entrees_bibliotheque = EntreeBibliotheque.objects.count()
    nb_centres = CentreConnaissance.objects.filter(actif=True).count()

    # Top fiches les plus consultées
    top_fiches_qs = (
        FicheCapitalisation.objects
        .filter(statut='publiee')
        .select_related('auteur')
        .order_by('-nb_consultations')[:10]
    )
    top_fiches = FicheCapitalisationListSerializer(top_fiches_qs, many=True).data

    # Fiches récentes
    fiches_recentes_qs = (
        FicheCapitalisation.objects
        .select_related('auteur')
        .order_by('-created_at')[:5]
    )
    fiches_recentes = FicheCapitalisationListSerializer(fiches_recentes_qs, many=True).data

    from django.db.models import Sum

    nb_lecons = FicheCapitalisation.objects.filter(type_fiche='lecon_apprise').count()
    nb_bonnes_pratiques = FicheCapitalisation.objects.filter(type_fiche='bonne_pratique').count()
    nb_commentaires = CommentaireFiche.objects.count()
    total_telechargements = EntreeBibliotheque.objects.aggregate(t=Sum('nb_telechargements'))['t'] or 0
    nb_vues_mois = FicheCapitalisation.objects.filter(
        updated_at__month=timezone.now().month, updated_at__year=timezone.now().year
    ).aggregate(v=Sum('nb_consultations'))['v'] or 0

    return Response({
        'fiches': {
            'total': nb_fiches_total,
            'publiees': nb_fiches_publiees,
            'ia': nb_fiches_ia,
            'lecons_apprises': nb_lecons,
            'bonnes_pratiques': nb_bonnes_pratiques,
            'vues_mois': nb_vues_mois,
            'par_type': fiches_par_type,
            'par_domaine': fiches_par_domaine,
            'par_statut': fiches_par_statut,
        },
        'bibliotheque': {
            'total': nb_entrees_bibliotheque,
            'telechargements': int(total_telechargements),
        },
        'centres': {
            'total': nb_centres,
        },
        'commentaires': {
            'total': nb_commentaires,
        },
        'top_fiches': top_fiches,
        'fiches_recentes': fiches_recentes,
        # Rétrocompatibilité
        'nb_fiches_total': nb_fiches_total,
        'nb_fiches_publiees': nb_fiches_publiees,
        'nb_entrees_bibliotheque': nb_entrees_bibliotheque,
        'nb_centres': nb_centres,
    })
