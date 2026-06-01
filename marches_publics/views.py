from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import (
    PlanPassationMarche, DemandeAchat, AppelOffre,
    SoumissionnaireOffre, ContratMarche, AvenantContrat,
)
from .serializers import (
    PlanPassationMarcheListSerializer, PlanPassationMarcheDetailSerializer,
    DemandeAchatListSerializer, DemandeAchatDetailSerializer,
    AppelOffreListSerializer, AppelOffreDetailSerializer,
    SoumissionnaireOffreSerializer, SoumissionnaireOffreListSerializer,
    ContratMarcheListSerializer, ContratMarcheDetailSerializer,
    AvenantContratSerializer,
)
from .filters import (
    PlanPassationMarcheFilter, DemandeAchatFilter, AppelOffreFilter,
    SoumissionnaireOffreFilter, ContratMarcheFilter, AvenantContratFilter,
)

CanReadMP = HasModulePermission.for_module('marches_publics', 'peut_lire')
CanEditMP = HasModulePermission.for_module('marches_publics', 'peut_modifier')
CanValidateMP = HasModulePermission.for_module('marches_publics', 'peut_valider')


# ─── Plan de passation des marchés ───────────────────────────────────────────

class PlanPassationMarcheViewSet(viewsets.ModelViewSet):
    queryset = PlanPassationMarche.objects.select_related(
        'programme', 'projet', 'cree_par', 'valide_par'
    ).prefetch_related('demandes', 'appels_offre').order_by('-annee', 'titre')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PlanPassationMarcheFilter
    search_fields = ['titre', 'description']
    ordering_fields = ['annee', 'titre', 'statut', 'budget_total_prevu', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadMP()]
        if self.action in ['valider', 'publier']:
            return [CanValidateMP()]
        return [CanEditMP()]

    def get_serializer_class(self):
        if self.action == 'list':
            return PlanPassationMarcheListSerializer
        return PlanPassationMarcheDetailSerializer

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        plan = self.get_object()
        if plan.statut != 'brouillon':
            return Response(
                {'detail': 'Seul un plan en brouillon peut être validé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        plan.statut = 'valide'
        plan.valide_par = request.user
        plan.date_validation = timezone.now().date()
        plan.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(PlanPassationMarcheDetailSerializer(plan).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        plan = self.get_object()
        if plan.statut not in ('brouillon', 'valide'):
            return Response(
                {'detail': 'Le plan doit être en brouillon ou validé pour être publié.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        plan.statut = 'publie'
        if not plan.valide_par:
            plan.valide_par = request.user
            plan.date_validation = timezone.now().date()
        plan.save()
        return Response(PlanPassationMarcheDetailSerializer(plan).data)


# ─── Demande d'achat ─────────────────────────────────────────────────────────

class DemandeAchatViewSet(viewsets.ModelViewSet):
    queryset = DemandeAchat.objects.select_related(
        'programme', 'projet', 'plan_passation', 'demandeur', 'valideur'
    ).order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DemandeAchatFilter
    search_fields = ['reference', 'titre', 'description']
    ordering_fields = ['created_at', 'statut', 'priorite', 'budget_estime', 'date_besoin']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadMP()]
        if self.action in ['valider', 'rejeter']:
            return [CanValidateMP()]
        return [CanEditMP()]

    def get_serializer_class(self):
        if self.action == 'list':
            return DemandeAchatListSerializer
        return DemandeAchatDetailSerializer

    def perform_create(self, serializer):
        serializer.save(demandeur=self.request.user)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        da = self.get_object()
        if da.statut != 'brouillon':
            return Response(
                {'detail': 'Seule une demande en brouillon peut être soumise.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        da.statut = 'soumise'
        da.save(update_fields=['statut'])
        return Response(DemandeAchatDetailSerializer(da).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        da = self.get_object()
        if da.statut not in ('soumise', 'en_validation'):
            return Response(
                {'detail': 'La demande doit être soumise ou en validation pour être validée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        da.statut = 'validee'
        da.valideur = request.user
        da.date_validation = timezone.now()
        da.save(update_fields=['statut', 'valideur', 'date_validation'])
        return Response(DemandeAchatDetailSerializer(da).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        da = self.get_object()
        if da.statut not in ('soumise', 'en_validation'):
            return Response(
                {'detail': 'La demande doit être soumise ou en validation pour être rejetée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        motif = request.data.get('motif', '')
        da.statut = 'rejetee'
        da.valideur = request.user
        da.date_validation = timezone.now()
        da.motif_rejet = motif
        da.save(update_fields=['statut', 'valideur', 'date_validation', 'motif_rejet'])
        return Response(DemandeAchatDetailSerializer(da).data)


# ─── Appel d'offres ──────────────────────────────────────────────────────────

class AppelOffreViewSet(viewsets.ModelViewSet):
    queryset = AppelOffre.objects.select_related(
        'demande_achat', 'plan_passation', 'programme', 'projet', 'responsable'
    ).prefetch_related('soumissionnaires', 'contrats').order_by('-date_publication', '-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AppelOffreFilter
    search_fields = ['reference', 'titre', 'description']
    ordering_fields = ['date_publication', 'date_limite_soumission', 'statut', 'budget_estime', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadMP()]
        if self.action in ['publier', 'attribuer']:
            return [CanValidateMP()]
        return [CanEditMP()]

    def get_serializer_class(self):
        if self.action == 'list':
            return AppelOffreListSerializer
        return AppelOffreDetailSerializer

    def perform_create(self, serializer):
        serializer.save(responsable=self.request.user)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        ao = self.get_object()
        if ao.statut != 'preparation':
            return Response(
                {'detail': "L'appel d'offres doit être en préparation pour être publié."},
                status=status.HTTP_400_BAD_REQUEST
            )
        ao.statut = 'publie'
        if not ao.date_publication:
            ao.date_publication = timezone.now().date()
        ao.save()
        return Response(AppelOffreDetailSerializer(ao).data)

    @action(detail=True, methods=['post'])
    def evaluer(self, request, pk=None):
        """
        Passe l'appel d'offres en statut 'evaluation'.
        Marque les soumissionnaires conformes/non-conformes selon les données fournies.
        """
        ao = self.get_object()
        if ao.statut not in ('publie', 'ouvert'):
            return Response(
                {'detail': "L'appel d'offres doit être publié ou ouvert pour lancer l'évaluation."},
                status=status.HTTP_400_BAD_REQUEST
            )
        ao.statut = 'evaluation'
        ao.save(update_fields=['statut'])

        # Mise à jour optionnelle des statuts soumissionnaires passés dans le body
        evaluations = request.data.get('evaluations', [])
        for ev in evaluations:
            sid = ev.get('soumissionnaire_id')
            s_statut = ev.get('statut')
            if sid and s_statut:
                SoumissionnaireOffre.objects.filter(
                    id=sid, appel_offre=ao
                ).update(statut=s_statut)

        return Response(AppelOffreDetailSerializer(ao).data)

    @action(detail=True, methods=['post'])
    def attribuer(self, request, pk=None):
        """
        Marque un soumissionnaire comme sélectionné et passe l'AO au statut 'attribue'.
        Requiert soumissionnaire_id dans le body.
        """
        ao = self.get_object()
        if ao.statut != 'evaluation':
            return Response(
                {'detail': "L'appel d'offres doit être en évaluation pour être attribué."},
                status=status.HTTP_400_BAD_REQUEST
            )
        soumissionnaire_id = request.data.get('soumissionnaire_id')
        if not soumissionnaire_id:
            return Response(
                {'detail': 'soumissionnaire_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            soumissionnaire = SoumissionnaireOffre.objects.get(
                id=soumissionnaire_id, appel_offre=ao
            )
        except SoumissionnaireOffre.DoesNotExist:
            return Response(
                {'detail': 'Soumissionnaire introuvable pour cet appel d\'offres.'},
                status=status.HTTP_404_NOT_FOUND
            )
        # Désélectionner tous les autres
        ao.soumissionnaires.exclude(id=soumissionnaire.id).filter(
            statut='selectionne'
        ).update(statut='qualifie')
        # Sélectionner le gagnant
        soumissionnaire.statut = 'selectionne'
        soumissionnaire.save(update_fields=['statut'])
        # Passer l'AO à attribué
        ao.statut = 'attribue'
        ao.save(update_fields=['statut'])
        return Response(AppelOffreDetailSerializer(ao).data)


# ─── Soumissionnaire ─────────────────────────────────────────────────────────

class SoumissionnaireOffreViewSet(viewsets.ModelViewSet):
    queryset = SoumissionnaireOffre.objects.select_related(
        'appel_offre'
    ).order_by('-note_globale')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SoumissionnaireOffreFilter
    search_fields = ['nom_entreprise', 'pays', 'email', 'contact']
    ordering_fields = ['note_globale', 'note_technique', 'note_financiere',
                       'montant_offre', 'date_soumission', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadMP()]
        if self.action == 'noter':
            return [CanValidateMP()]
        return [CanEditMP()]

    def get_serializer_class(self):
        if self.action == 'list':
            return SoumissionnaireOffreListSerializer
        return SoumissionnaireOffreSerializer

    @action(detail=True, methods=['post'])
    def noter(self, request, pk=None):
        """
        Met à jour les notes technique et/ou financière et recalcule la note globale.
        """
        soumissionnaire = self.get_object()
        note_technique = request.data.get('note_technique')
        note_financiere = request.data.get('note_financiere')
        poids_technique = request.data.get('poids_technique')
        poids_financier = request.data.get('poids_financier')
        observations = request.data.get('observations', '')

        update_fields = []
        if note_technique is not None:
            soumissionnaire.note_technique = note_technique
            update_fields.append('note_technique')
        if note_financiere is not None:
            soumissionnaire.note_financiere = note_financiere
            update_fields.append('note_financiere')
        if poids_technique is not None:
            soumissionnaire.poids_technique = poids_technique
            update_fields.append('poids_technique')
        if poids_financier is not None:
            soumissionnaire.poids_financier = poids_financier
            update_fields.append('poids_financier')
        if observations:
            soumissionnaire.observations = observations
            update_fields.append('observations')

        if update_fields:
            soumissionnaire.save(update_fields=update_fields)

        # Recalculer la note globale si les deux notes sont présentes
        soumissionnaire.calculer_note_globale()
        soumissionnaire.refresh_from_db()

        return Response(SoumissionnaireOffreSerializer(soumissionnaire).data)


# ─── Contrat marché ──────────────────────────────────────────────────────────

class ContratMarcheViewSet(viewsets.ModelViewSet):
    queryset = ContratMarche.objects.select_related(
        'appel_offre', 'soumissionnaire', 'programme', 'projet', 'gestionnaire'
    ).prefetch_related('avenants').order_by('-date_signature', '-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ContratMarcheFilter
    search_fields = ['reference', 'titre', 'prestataire_nom', 'objet']
    ordering_fields = ['date_signature', 'date_fin_prevue', 'montant_ttc',
                       'montant_realise', 'statut', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'stats']:
            return [CanReadMP()]
        if self.action in ['signer', 'solde']:
            return [CanValidateMP()]
        return [CanEditMP()]

    def get_serializer_class(self):
        if self.action == 'list':
            return ContratMarcheListSerializer
        return ContratMarcheDetailSerializer

    def perform_create(self, serializer):
        serializer.save(gestionnaire=self.request.user)

    @action(detail=True, methods=['post'])
    def signer(self, request, pk=None):
        contrat = self.get_object()
        if contrat.statut != 'en_preparation':
            return Response(
                {'detail': 'Le contrat doit être en préparation pour être signé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        date_signature = request.data.get('date_signature', timezone.now().date())
        contrat.statut = 'signe'
        contrat.date_signature = date_signature
        if not contrat.date_debut:
            contrat.date_debut = date_signature
        contrat.save()
        return Response(ContratMarcheDetailSerializer(contrat).data)

    @action(detail=True, methods=['post'])
    def solde(self, request, pk=None):
        contrat = self.get_object()
        if contrat.statut not in ('signe', 'en_cours', 'suspendu'):
            return Response(
                {'detail': 'Le contrat doit être signé, en cours ou suspendu pour être soldé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        montant_realise = request.data.get('montant_realise')
        date_fin_reelle = request.data.get('date_fin_reelle', timezone.now().date())
        contrat.statut = 'solde'
        contrat.date_fin_reelle = date_fin_reelle
        if montant_realise is not None:
            contrat.montant_realise = montant_realise
        contrat.save()
        return Response(ContratMarcheDetailSerializer(contrat).data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        contrat = self.get_object()
        return Response({
            'reference': contrat.reference,
            'titre': contrat.titre,
            'statut': contrat.statut,
            'montant_ttc': float(contrat.montant_ttc),
            'montant_realise': float(contrat.montant_realise),
            'taux_execution': contrat.taux_execution,
            'est_en_retard': contrat.est_en_retard,
            'nb_avenants': contrat.avenants.count(),
            'montant_avenants': float(
                contrat.avenants.aggregate(total=Sum('montant_supplementaire'))['total'] or 0
            ),
            'dernier_avenant': contrat.avenants.order_by('-numero_avenant').values(
                'numero_avenant', 'motif', 'statut', 'date_signature'
            ).first(),
        })


# ─── Avenant contrat ─────────────────────────────────────────────────────────

class AvenantContratViewSet(viewsets.ModelViewSet):
    queryset = AvenantContrat.objects.select_related('contrat').order_by('numero_avenant')
    serializer_class = AvenantContratSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AvenantContratFilter
    ordering_fields = ['numero_avenant', 'date_signature', 'montant_supplementaire', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadMP()]
        if self.action == 'signer':
            return [CanValidateMP()]
        return [CanEditMP()]

    def get_queryset(self):
        qs = super().get_queryset()
        contrat_id = self.request.query_params.get('contrat')
        return qs.filter(contrat_id=contrat_id) if contrat_id else qs

    @action(detail=True, methods=['post'])
    def signer(self, request, pk=None):
        avenant = self.get_object()
        if avenant.statut != 'en_preparation':
            return Response(
                {'detail': "L'avenant doit être en préparation pour être signé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        date_signature = request.data.get('date_signature', timezone.now().date())
        avenant.statut = 'signe'
        avenant.date_signature = date_signature
        avenant.save(update_fields=['statut', 'date_signature'])

        # Mettre à jour le contrat si nouveau montant ou nouvelle date de fin
        contrat = avenant.contrat
        update_contrat_fields = []
        if avenant.nouveau_montant_ttc:
            contrat.montant_ttc = avenant.nouveau_montant_ttc
            update_contrat_fields.append('montant_ttc')
        elif avenant.montant_supplementaire:
            contrat.montant_ttc = float(contrat.montant_ttc) + float(avenant.montant_supplementaire)
            update_contrat_fields.append('montant_ttc')
        if avenant.nouvelle_date_fin:
            contrat.date_fin_prevue = avenant.nouvelle_date_fin
            update_contrat_fields.append('date_fin_prevue')
        if update_contrat_fields:
            contrat.save(update_fields=update_contrat_fields)

        return Response(AvenantContratSerializer(avenant).data)


# ─── Dashboard marchés publics ───────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadMP])
def dashboard_marches(request):
    projet_id = request.query_params.get('projet')
    programme_id = request.query_params.get('programme')
    today = timezone.now().date()

    qs_plans = PlanPassationMarche.objects.all()
    qs_da = DemandeAchat.objects.all()
    qs_ao = AppelOffre.objects.all()
    qs_contrats = ContratMarche.objects.all()

    if projet_id:
        qs_plans = qs_plans.filter(projet_id=projet_id)
        qs_da = qs_da.filter(projet_id=projet_id)
        qs_ao = qs_ao.filter(projet_id=projet_id)
        qs_contrats = qs_contrats.filter(projet_id=projet_id)
    if programme_id:
        qs_plans = qs_plans.filter(programme_id=programme_id)
        qs_da = qs_da.filter(programme_id=programme_id)
        qs_ao = qs_ao.filter(programme_id=programme_id)
        qs_contrats = qs_contrats.filter(programme_id=programme_id)

    # Taux d'exécution moyen sur les contrats signés/en cours
    contrats_list = list(qs_contrats.filter(statut__in=['signe', 'en_cours', 'solde']))
    taux_execution_moyen = 0
    if contrats_list:
        taux_execution_moyen = round(
            sum(c.taux_execution for c in contrats_list) / len(contrats_list), 1
        )

    budget_total = qs_contrats.aggregate(total=Sum('montant_ttc'))['total'] or 0
    montant_realise_total = qs_contrats.aggregate(total=Sum('montant_realise'))['total'] or 0

    return Response({
        'plans_passation': {
            'total': qs_plans.count(),
            'par_statut': {
                s: qs_plans.filter(statut=s).count()
                for s, _ in PlanPassationMarche.STATUT_CHOICES
            },
            'budget_total_prevu': float(
                qs_plans.aggregate(total=Sum('budget_total_prevu'))['total'] or 0
            ),
        },
        'demandes_achat': {
            'total': qs_da.count(),
            'par_statut': {
                s: qs_da.filter(statut=s).count()
                for s, _ in DemandeAchat.STATUT_CHOICES
            },
            'urgentes': qs_da.filter(
                priorite__in=['urgente', 'tres_urgente'],
                statut__in=['brouillon', 'soumise', 'en_validation']
            ).count(),
        },
        'appels_offre': {
            'total': qs_ao.count(),
            'par_statut': {
                s: qs_ao.filter(statut=s).count()
                for s, _ in AppelOffre.STATUT_CHOICES
            },
            'en_cours': qs_ao.filter(statut__in=['publie', 'ouvert', 'evaluation']).count(),
        },
        'contrats': {
            'total': qs_contrats.count(),
            'par_statut': {
                s: qs_contrats.filter(statut=s).count()
                for s, _ in ContratMarche.STATUT_CHOICES
            },
            'budget_total': float(budget_total),
            'montant_realise_total': float(montant_realise_total),
            'taux_execution_moyen': taux_execution_moyen,
            'en_retard': qs_contrats.filter(
                date_fin_prevue__lt=today,
                statut__in=['signe', 'en_cours']
            ).count(),
        },
        'avenants': {
            'total': AvenantContrat.objects.filter(
                contrat__in=qs_contrats
            ).count(),
            'en_preparation': AvenantContrat.objects.filter(
                contrat__in=qs_contrats,
                statut='en_preparation'
            ).count(),
        },
    })
