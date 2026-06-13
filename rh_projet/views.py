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
    EmployeProjet, AffectationRH, FeuilleTemps,
    LigneFeuilleTemps, EvaluationPerformance, BesoinFormation,
    DemandeConge, DemandeAbsence, OccurrenceSpeciale,
)
from .serializers import (
    EmployeProjetListSerializer, EmployeProjetDetailSerializer, EmployeProjetMinimalSerializer,
    AffectationRHListSerializer, AffectationRHDetailSerializer,
    FeuilleTempsListSerializer, FeuilleTempsDetailSerializer,
    LigneFeuilleTempsSerializer,
    EvaluationPerformanceListSerializer, EvaluationPerformanceDetailSerializer,
    BesoinFormationListSerializer, BesoinFormationDetailSerializer,
    DemandeCongeListSerializer, DemandeCongeDetailSerializer,
    DemandeAbsenceListSerializer, DemandeAbsenceDetailSerializer,
    OccurrenceSpecialeSerializer,
)
from .filters import (
    EmployeProjetFilter, AffectationRHFilter, FeuilleTempsFilter,
    LigneFeuilleTempsFilter, EvaluationPerformanceFilter, BesoinFormationFilter,
)

CanReadRH = HasModulePermission.for_module('rh_projet', 'peut_lire')
CanEditRH = HasModulePermission.for_module('rh_projet', 'peut_modifier')
CanValidateRH = HasModulePermission.for_module('rh_projet', 'peut_valider')


# ─── EmployeProjet ────────────────────────────────────────────────────────────

class EmployeProjetViewSet(viewsets.ModelViewSet):
    queryset = EmployeProjet.objects.select_related('utilisateur').prefetch_related(
        'affectations'
    ).order_by('nom', 'prenom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EmployeProjetFilter
    search_fields = ['matricule', 'nom', 'prenom', 'email', 'poste', 'specialite']
    ordering_fields = ['nom', 'prenom', 'date_embauche', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'stats', 'charger_occupations']:
            return [CanReadRH()]
        return [CanEditRH()]

    def get_serializer_class(self):
        return EmployeProjetListSerializer if self.action == 'list' else EmployeProjetDetailSerializer

    def perform_create(self, s):
        emp = s.save()
        AuditLog.log(self.request.user, 'create', module='rh_projet',
                     objet_type='EmployeProjet', objet_id=emp.id, request=self.request)

    @action(detail=True, methods=['get'])
    def charger_occupations(self, request, pk=None):
        """Retourne le taux d'occupation de l'employé par période (affectations actives)."""
        emp = self.get_object()
        affectations = emp.affectations.filter(statut='active').select_related(
            'projet', 'programme', 'activite'
        )
        total_taux = affectations.aggregate(s=Sum('taux_affectation'))['s'] or 0
        data = []
        for aff in affectations:
            ref = str(aff.projet or aff.programme or aff.activite or 'N/A')
            data.append({
                'id': aff.id,
                'reference': ref,
                'role': aff.role,
                'taux_affectation': aff.taux_affectation,
                'date_debut': aff.date_debut,
                'date_fin': aff.date_fin,
                'statut': aff.statut,
            })
        return Response({
            'employe': EmployeProjetMinimalSerializer(emp).data,
            'taux_occupation_total': total_taux,
            'taux_occupation_max': emp.taux_occupation_max,
            'disponibilite': max(0, emp.taux_occupation_max - total_taux),
            'affectations': data,
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques RH globales : répartition par type et par statut."""
        qs = EmployeProjet.objects.all()
        par_type = list(
            qs.values('type_personnel').annotate(nb=Count('id')).order_by('-nb')
        )
        par_statut = list(
            qs.values('statut').annotate(nb=Count('id')).order_by('-nb')
        )
        par_niveau = list(
            qs.values('niveau_expertise').annotate(nb=Count('id')).order_by('-nb')
        )
        taux_moyen = EmployeProjet.objects.filter(
            affectations__statut='active'
        ).annotate(
            taux_total=Sum('affectations__taux_affectation')
        ).aggregate(moy=Avg('taux_total'))['moy'] or 0

        return Response({
            'total_employes': qs.count(),
            'actifs': qs.filter(statut='actif').count(),
            'par_type': par_type,
            'par_statut': par_statut,
            'par_niveau': par_niveau,
            'taux_affectation_moyen': round(float(taux_moyen), 1),
        })


# ─── AffectationRH ────────────────────────────────────────────────────────────

class AffectationRHViewSet(viewsets.ModelViewSet):
    queryset = AffectationRH.objects.select_related(
        'employe', 'programme', 'projet', 'activite', 'cree_par'
    ).order_by('-date_debut')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AffectationRHFilter
    search_fields = ['role', 'employe__nom', 'employe__prenom', 'employe__matricule']
    ordering_fields = ['date_debut', 'taux_affectation', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadRH()]
        return [CanEditRH()]

    def get_serializer_class(self):
        return AffectationRHListSerializer if self.action == 'list' else AffectationRHDetailSerializer

    def perform_create(self, s):
        s.save(cree_par=self.request.user)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        aff = self.get_object()
        if aff.statut == 'terminee':
            return Response({'detail': 'Affectation déjà terminée.'}, status=400)
        aff.statut = 'terminee'
        aff.date_fin = request.data.get('date_fin') or timezone.now().date()
        aff.save(update_fields=['statut', 'date_fin'])
        return Response(AffectationRHDetailSerializer(aff).data)

    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        aff = self.get_object()
        aff.statut = 'suspendue'
        aff.save(update_fields=['statut'])
        return Response(AffectationRHDetailSerializer(aff).data)

    @action(detail=True, methods=['post'])
    def reactiver(self, request, pk=None):
        aff = self.get_object()
        if aff.statut not in ('suspendue', 'annulee'):
            return Response({'detail': 'Impossible de réactiver une affectation dans ce statut.'}, status=400)
        aff.statut = 'active'
        aff.save(update_fields=['statut'])
        return Response(AffectationRHDetailSerializer(aff).data)


# ─── FeuilleTemps ─────────────────────────────────────────────────────────────

class FeuilleTempsViewSet(viewsets.ModelViewSet):
    queryset = FeuilleTemps.objects.select_related(
        'employe', 'valideur'
    ).prefetch_related('lignes').order_by('-annee', '-mois')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FeuilleTempsFilter
    search_fields = ['employe__nom', 'employe__prenom', 'employe__matricule']
    ordering_fields = ['annee', 'mois', 'total_heures', 'montant_total']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadRH()]
        if self.action in ['valider', 'rejeter']:
            return [CanValidateRH()]
        return [CanEditRH()]

    def get_serializer_class(self):
        return FeuilleTempsListSerializer if self.action == 'list' else FeuilleTempsDetailSerializer

    def perform_create(self, s):
        feuille = s.save()
        AuditLog.log(self.request.user, 'create', module='rh_projet',
                     objet_type='FeuilleTemps', objet_id=feuille.id, request=self.request)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        feuille = self.get_object()
        if feuille.statut not in ('brouillon', 'rejetee'):
            return Response({'detail': 'Seule une feuille en brouillon ou rejetée peut être soumise.'}, status=400)
        feuille.calculer_totaux()
        feuille.statut = 'soumise'
        feuille.save(update_fields=['statut'])
        return Response(FeuilleTempsDetailSerializer(feuille).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        feuille = self.get_object()
        if feuille.statut != 'soumise':
            return Response({'detail': 'Seule une feuille soumise peut être validée.'}, status=400)
        feuille.statut = 'validee'
        feuille.valideur = request.user
        feuille.date_validation = timezone.now()
        feuille.motif_rejet = ''
        feuille.save(update_fields=['statut', 'valideur', 'date_validation', 'motif_rejet'])
        AuditLog.log(request.user, 'update', module='rh_projet',
                     objet_type='FeuilleTemps', objet_id=feuille.id, request=request)
        return Response(FeuilleTempsDetailSerializer(feuille).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        feuille = self.get_object()
        if feuille.statut != 'soumise':
            return Response({'detail': 'Seule une feuille soumise peut être rejetée.'}, status=400)
        motif = request.data.get('motif', '')
        if not motif:
            return Response({'detail': 'Un motif de rejet est requis.'}, status=400)
        feuille.statut = 'rejetee'
        feuille.motif_rejet = motif
        feuille.valideur = request.user
        feuille.date_validation = timezone.now()
        feuille.save(update_fields=['statut', 'motif_rejet', 'valideur', 'date_validation'])
        return Response(FeuilleTempsDetailSerializer(feuille).data)

    @action(detail=True, methods=['post'])
    def recalculer(self, request, pk=None):
        feuille = self.get_object()
        if feuille.statut == 'validee':
            return Response({'detail': 'Impossible de recalculer une feuille validée.'}, status=400)
        feuille.calculer_totaux()
        return Response(FeuilleTempsDetailSerializer(feuille).data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        qs = FeuilleTemps.objects.filter(statut='soumise').select_related('employe')
        return Response(FeuilleTempsListSerializer(qs, many=True).data)


# ─── LigneFeuilleTemps ────────────────────────────────────────────────────────

class LigneFeuilleTempsViewSet(viewsets.ModelViewSet):
    queryset = LigneFeuilleTemps.objects.select_related(
        'feuille', 'projet', 'activite'
    ).order_by('date')
    serializer_class = LigneFeuilleTempsSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = LigneFeuilleTempsFilter
    search_fields = ['description']
    permission_classes = [CanEditRH]

    def get_queryset(self):
        qs = super().get_queryset()
        feuille = self.request.query_params.get('feuille')
        return qs.filter(feuille_id=feuille) if feuille else qs

    def perform_create(self, s):
        ligne = s.save()
        ligne.feuille.calculer_totaux()

    def perform_update(self, s):
        ligne = s.save()
        ligne.feuille.calculer_totaux()

    def perform_destroy(self, instance):
        feuille = instance.feuille
        instance.delete()
        feuille.calculer_totaux()


# ─── EvaluationPerformance ────────────────────────────────────────────────────

class EvaluationPerformanceViewSet(viewsets.ModelViewSet):
    queryset = EvaluationPerformance.objects.select_related(
        'employe', 'evaluateur', 'projet'
    ).order_by('-annee', 'employe__nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EvaluationPerformanceFilter
    search_fields = ['employe__nom', 'employe__prenom', 'employe__matricule']
    ordering_fields = ['annee', 'note_globale', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadRH()]
        if self.action in ['valider']:
            return [CanValidateRH()]
        return [CanEditRH()]

    def get_serializer_class(self):
        return (EvaluationPerformanceListSerializer
                if self.action == 'list'
                else EvaluationPerformanceDetailSerializer)

    def perform_create(self, s):
        ev = s.save(evaluateur=self.request.user)
        AuditLog.log(self.request.user, 'create', module='rh_projet',
                     objet_type='EvaluationPerformance', objet_id=ev.id, request=self.request)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        ev = self.get_object()
        if ev.statut not in ('brouillon', 'en_cours'):
            return Response({'detail': 'Statut incompatible pour la soumission.'}, status=400)
        ev.statut = 'soumise'
        ev.save(update_fields=['statut'])
        return Response(EvaluationPerformanceDetailSerializer(ev).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        ev = self.get_object()
        if ev.statut != 'soumise':
            return Response({'detail': "Seule une évaluation soumise peut être validée."}, status=400)
        ev.statut = 'validee'
        ev.save(update_fields=['statut'])
        AuditLog.log(request.user, 'update', module='rh_projet',
                     objet_type='EvaluationPerformance', objet_id=ev.id, request=request)
        return Response(EvaluationPerformanceDetailSerializer(ev).data)


# ─── BesoinFormation ─────────────────────────────────────────────────────────

class BesoinFormationViewSet(viewsets.ModelViewSet):
    queryset = BesoinFormation.objects.select_related(
        'employe', 'projet', 'identifie_par'
    ).order_by('-priorite', 'date_souhaitee')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BesoinFormationFilter
    search_fields = ['intitule', 'domaine', 'organisme_formation',
                     'employe__nom', 'employe__prenom']
    ordering_fields = ['priorite', 'date_souhaitee', 'cout_estime', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadRH()]
        if self.action in ['valider']:
            return [CanValidateRH()]
        return [CanEditRH()]

    def get_serializer_class(self):
        return (BesoinFormationListSerializer
                if self.action == 'list'
                else BesoinFormationDetailSerializer)

    def perform_create(self, s):
        s.save(identifie_par=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        besoin = self.get_object()
        if besoin.statut != 'identifie':
            return Response({'detail': 'Seul un besoin identifié peut être validé.'}, status=400)
        besoin.statut = 'valide'
        besoin.save(update_fields=['statut'])
        return Response(BesoinFormationDetailSerializer(besoin).data)

    @action(detail=True, methods=['post'])
    def planifier(self, request, pk=None):
        besoin = self.get_object()
        if besoin.statut not in ('identifie', 'valide'):
            return Response({'detail': 'Statut incompatible pour la planification.'}, status=400)
        besoin.statut = 'planifie'
        date_souhaitee = request.data.get('date_souhaitee')
        organisme = request.data.get('organisme_formation', '')
        if date_souhaitee:
            besoin.date_souhaitee = date_souhaitee
        if organisme:
            besoin.organisme_formation = organisme
        besoin.save(update_fields=['statut', 'date_souhaitee', 'organisme_formation'])
        return Response(BesoinFormationDetailSerializer(besoin).data)

    @action(detail=True, methods=['post'])
    def marquer_realise(self, request, pk=None):
        besoin = self.get_object()
        if besoin.statut not in ('planifie', 'valide'):
            return Response({'detail': 'La formation doit être planifiée ou validée.'}, status=400)
        besoin.statut = 'realise'
        besoin.date_realisation = request.data.get('date_realisation') or timezone.now().date()
        cout_reel = request.data.get('cout_reel')
        if cout_reel is not None:
            besoin.cout_reel = cout_reel
        besoin.save(update_fields=['statut', 'date_realisation', 'cout_reel'])
        return Response(BesoinFormationDetailSerializer(besoin).data)

    @action(detail=False, methods=['get'])
    def prioritaires(self, request):
        qs = BesoinFormation.objects.filter(
            priorite__in=['haute', 'critique'],
            statut__in=['identifie', 'valide', 'planifie']
        ).select_related('employe', 'projet').order_by('-priorite', 'date_souhaitee')
        return Response(BesoinFormationListSerializer(qs, many=True).data)


# ─── Dashboard RH ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadRH])
def dashboard_rh(request):
    projet_id = request.query_params.get('projet')
    aujourd_hui = timezone.now().date()
    mois_courant = aujourd_hui.month
    annee_courante = aujourd_hui.year

    qs_employes = EmployeProjet.objects.all()
    qs_affectations = AffectationRH.objects.filter(statut='active')
    qs_feuilles = FeuilleTemps.objects.all()
    qs_besoins = BesoinFormation.objects.all()

    if projet_id:
        qs_affectations = qs_affectations.filter(projet_id=projet_id)
        qs_feuilles = qs_feuilles.filter(employe__affectations__projet_id=projet_id).distinct()
        qs_besoins = qs_besoins.filter(projet_id=projet_id)

    # Effectif
    total_employes = qs_employes.count()
    actifs = qs_employes.filter(statut='actif').count()

    # Taux d'affectation moyen
    taux_moyen = qs_affectations.aggregate(moy=Avg('taux_affectation'))['moy'] or 0

    # Feuilles de temps
    feuilles_en_attente = qs_feuilles.filter(statut='soumise').count()
    feuilles_mois = qs_feuilles.filter(mois=mois_courant, annee=annee_courante)

    # Besoins de formation
    besoins_prioritaires = qs_besoins.filter(
        priorite__in=['haute', 'critique'],
        statut__in=['identifie', 'valide']
    ).count()
    cout_formations = float(
        qs_besoins.filter(statut__in=['valide', 'planifie']).aggregate(
            s=Sum('cout_estime'))['s'] or 0
    )

    # Evaluations en attente
    evaluations_en_attente = EvaluationPerformance.objects.filter(statut='soumise').count()

    # Contrats expirant dans 30 jours
    from datetime import timedelta
    expiration_limite = aujourd_hui + timedelta(days=30)
    contrats_a_expirer = qs_employes.filter(
        date_fin_contrat__lte=expiration_limite,
        date_fin_contrat__gte=aujourd_hui,
        statut='actif',
    ).count()

    return Response({
        'effectif': {
            'total': total_employes,
            'actifs': actifs,
            'par_type': list(
                qs_employes.values('type_personnel').annotate(nb=Count('id'))
            ),
        },
        'affectations': {
            'actives': qs_affectations.count(),
            'taux_affectation_moyen': round(float(taux_moyen), 1),
        },
        'feuilles_temps': {
            'en_attente_validation': feuilles_en_attente,
            'mois_courant': {
                'total': feuilles_mois.count(),
                'validees': feuilles_mois.filter(statut='validee').count(),
                'soumises': feuilles_mois.filter(statut='soumise').count(),
                'brouillons': feuilles_mois.filter(statut='brouillon').count(),
            },
        },
        'formations': {
            'besoins_prioritaires': besoins_prioritaires,
            'cout_estime_total': cout_formations,
            'par_statut': list(
                qs_besoins.values('statut').annotate(nb=Count('id'))
            ),
        },
        'evaluations': {
            'en_attente_validation': evaluations_en_attente,
        },
        'alertes': {
            'contrats_a_expirer_30j': contrats_a_expirer,
        },
    })


# ─── DemandeConge ─────────────────────────────────────────────────────────────

class DemandeCongeViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['motif', 'employe__nom', 'employe__prenom']
    ordering_fields = ['date_debut', 'date_fin', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'mes_conges', 'calendrier', 'stats']:
            return [HasModulePermission.for_module('rh_projet', 'peut_lire')()]
        if self.action in ['approuver', 'rejeter']:
            return [HasModulePermission.for_module('rh_projet', 'peut_valider')()]
        return [HasModulePermission.for_module('rh_projet', 'peut_modifier')()]

    def get_queryset(self):
        return DemandeConge.objects.select_related('employe', 'approuve_par').order_by('-created_at')

    def get_serializer_class(self):
        return DemandeCongeListSerializer if self.action == 'list' else DemandeCongeDetailSerializer

    @action(detail=False, methods=['get'])
    def mes_conges(self, request):
        employe = EmployeProjet.objects.filter(utilisateur=request.user).first()
        if not employe:
            return Response({'detail': 'Profil employe introuvable.'}, status=404)
        qs = DemandeConge.objects.filter(employe=employe).order_by('-created_at')
        return Response(DemandeCongeListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        qs = DemandeConge.objects.filter(statut='soumise').order_by('date_debut')
        return Response(DemandeCongeListSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        demande = self.get_object()
        if demande.statut != 'brouillon':
            return Response({'detail': 'Seul un brouillon peut etre soumis.'}, status=400)
        demande.soumettre()
        return Response(DemandeCongeDetailSerializer(demande).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        demande = self.get_object()
        if demande.statut != 'soumise':
            return Response({'detail': 'Seule une demande soumise peut etre approuvee.'}, status=400)
        demande.approuver(request.user)
        AuditLog.log(request.user, 'approve', module='rh_projet',
                     objet_type='DemandeConge', objet_id=demande.id, request=request)
        return Response(DemandeCongeDetailSerializer(demande).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        demande = self.get_object()
        motif = request.data.get('motif', '')
        demande.rejeter(request.user, motif)
        return Response(DemandeCongeDetailSerializer(demande).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        demande = self.get_object()
        if demande.statut in ('approuvee', 'rejetee'):
            return Response({'detail': 'Impossible d annuler une demande deja traitee.'}, status=400)
        demande.statut = 'annulee'
        demande.save(update_fields=['statut'])
        return Response(DemandeCongeDetailSerializer(demande).data)

    @action(detail=False, methods=['get'])
    def calendrier(self, request):
        qs = DemandeConge.objects.filter(statut='approuvee').select_related('employe')
        data = [
            {
                'id': d.id,
                'titre': f"Conge {d.employe.nom_complet}",
                'type': d.type_conge,
                'debut': d.date_debut,
                'fin': d.date_fin,
                'jours': float(d.nombre_jours),
            }
            for d in qs
        ]
        return Response(data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = DemandeConge.objects.all()
        return Response({
            'total': qs.count(),
            'en_attente': qs.filter(statut='soumise').count(),
            'approuvees': qs.filter(statut='approuvee').count(),
            'rejetees': qs.filter(statut='rejetee').count(),
            'par_type': list(qs.values('type_conge').annotate(nb=Count('id'))),
        })


# ─── DemandeAbsence ───────────────────────────────────────────────────────────

class DemandeAbsenceViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['motif', 'employe__nom', 'employe__prenom']
    ordering_fields = ['date_absence', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'mes_absences', 'stats']:
            return [HasModulePermission.for_module('rh_projet', 'peut_lire')()]
        if self.action in ['approuver', 'rejeter']:
            return [HasModulePermission.for_module('rh_projet', 'peut_valider')()]
        return [HasModulePermission.for_module('rh_projet', 'peut_modifier')()]

    def get_queryset(self):
        return DemandeAbsence.objects.select_related('employe', 'approuve_par').order_by('-date_absence')

    def get_serializer_class(self):
        return DemandeAbsenceListSerializer if self.action == 'list' else DemandeAbsenceDetailSerializer

    @action(detail=False, methods=['get'])
    def mes_absences(self, request):
        employe = EmployeProjet.objects.filter(utilisateur=request.user).first()
        if not employe:
            return Response({'detail': 'Profil employe introuvable.'}, status=404)
        qs = DemandeAbsence.objects.filter(employe=employe).order_by('-date_absence')
        return Response(DemandeAbsenceListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        qs = DemandeAbsence.objects.filter(statut='soumise').order_by('date_absence')
        return Response(DemandeAbsenceListSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        demande = self.get_object()
        if demande.statut != 'soumise':
            return Response({'detail': 'Seule une demande soumise peut etre approuvee.'}, status=400)
        demande.approuver(request.user)
        return Response(DemandeAbsenceDetailSerializer(demande).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        demande = self.get_object()
        motif = request.data.get('motif', '')
        demande.rejeter(request.user, motif)
        return Response(DemandeAbsenceDetailSerializer(demande).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = DemandeAbsence.objects.all()
        return Response({
            'total': qs.count(),
            'en_attente': qs.filter(statut='soumise').count(),
            'approuvees': qs.filter(statut='approuvee').count(),
            'par_type': list(qs.values('type_absence').annotate(nb=Count('id'))),
        })


# ─── OccurrenceSpeciale ───────────────────────────────────────────────────────

class OccurrenceSpecialeViewSet(viewsets.ModelViewSet):
    serializer_class = OccurrenceSpecialeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['description', 'employe__nom', 'employe__prenom']
    ordering_fields = ['date_evenement', 'created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [HasModulePermission.for_module('rh_projet', 'peut_lire')()]
        if self.action == 'valider':
            return [HasModulePermission.for_module('rh_projet', 'peut_valider')()]
        return [HasModulePermission.for_module('rh_projet', 'peut_modifier')()]

    def get_queryset(self):
        return OccurrenceSpeciale.objects.select_related('employe', 'valide_par').order_by('-date_evenement')

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        occ = self.get_object()
        if occ.statut != 'soumise':
            return Response({'detail': 'Seule une occurrence soumise peut etre validee.'}, status=400)
        occ.valider(request.user)
        AuditLog.log(request.user, 'validate', module='rh_projet',
                     objet_type='OccurrenceSpeciale', objet_id=occ.id, request=request)
        return Response(OccurrenceSpecialeSerializer(occ).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        occ = self.get_object()
        occ.statut = 'rejetee'
        occ.valide_par = request.user
        occ.date_validation = timezone.now()
        occ.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(OccurrenceSpecialeSerializer(occ).data)
