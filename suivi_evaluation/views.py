from django.db.models import Count, Sum, Avg, Q, Max
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
    Indicateur, ValeurCiblePeriode, CollecteIndicateur, AlerteIndicateur,
    FormulaireDynamique, ChampFormulaire, SoumissionFormulaire, ReponseChamp,
    Enquete, SectionEnquete, QuestionEnquete, ReponseEnquete, ReponseQuestion,
    CadreResultats, NiveauResultat, TheorieChangement,
    Evaluation, CritereEvaluation, LeconApprise,
    RapportSE, AnalysePredictive, PointSIG,
    RegistreRisque, PlanMitigation, SuiviRisque, AlerteRisque,
)
from .serializers import (
    IndicateurListSerializer, IndicateurDetailSerializer,
    ValeurCiblePeriodeSerializer, CollecteIndicateurSerializer, AlerteIndicateurSerializer,
    FormulaireDynamiqueListSerializer, FormulaireDynamiqueDetailSerializer,
    ChampFormulaireSerializer, SoumissionFormulaireSerializer, ReponseChampSerializer,
    EnqueteListSerializer, EnqueteDetailSerializer, SectionEnqueteSerializer,
    QuestionEnqueteSerializer, ReponseEnqueteSerializer, ReponseQuestionSerializer,
    CadreResultatsSerializer, NiveauResultatSerializer, TheorieChangementSerializer,
    EvaluationListSerializer, EvaluationDetailSerializer, CritereEvaluationSerializer,
    LeconApprisSerializer, RapportSESerializer, AnalysePredictiveSerializer, PointSIGSerializer,
    RegistreRisqueListSerializer, RegistreRisqueDetailSerializer,
    PlanMitigationSerializer, SuiviRisqueSerializer, AlerteRisqueSerializer,
)
from .filters import (
    IndicateurFilter, CollecteIndicateurFilter, FormulaireFilter, SoumissionFilter,
    EnqueteFilter, ReponseEnqueteFilter, EvaluationFilter, LeconApprisFilter,
    RapportSEFilter, PointSIGFilter, RegistreRisqueFilter,
)

CanReadSE = HasModulePermission.for_module('suivi_evaluation', 'peut_lire')
CanEditSE = HasModulePermission.for_module('suivi_evaluation', 'peut_modifier')
CanValidateSE = HasModulePermission.for_module('suivi_evaluation', 'peut_valider')


# ─── M17 : Indicateurs ───────────────────────────────────────────────────────

class IndicateurViewSet(viewsets.ModelViewSet):
    queryset = Indicateur.objects.select_related(
        'projet', 'programme', 'responsable', 'created_by'
    ).prefetch_related('collectes', 'cibles_periodes', 'alertes').order_by('ordre', 'code')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = IndicateurFilter
    search_fields = ['code', 'intitule', 'description']
    ordering_fields = ['code', 'statut', 'taux_realisation', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'evolution', 'stats', 'tableau_bord']:
            return [CanReadSE()]
        if self.action in ['valider_collecte', 'rejeter_collecte']:
            return [CanValidateSE()]
        return [CanEditSE()]

    def get_serializer_class(self):
        if self.action == 'list':
            return IndicateurListSerializer
        return IndicateurDetailSerializer

    def perform_create(self, s):
        ind = s.save(created_by=self.request.user)
        AuditLog.log(self.request.user, 'create', module='suivi_evaluation',
                     objet_type='Indicateur', objet_id=ind.id, request=self.request)

    @action(detail=True, methods=['get'])
    def evolution(self, request, pk=None):
        ind = self.get_object()
        collectes = ind.collectes.filter(statut='valide').order_by('date_collecte')
        cibles = ind.cibles_periodes.order_by('annee', 'trimestre')
        return Response({
            'indicateur': {'code': ind.code, 'intitule': ind.intitule,
                           'unite': ind.unite_mesure, 'baseline': float(ind.valeur_baseline or 0),
                           'cible_globale': float(ind.valeur_cible_globale or 0)},
            'historique': [{'date': str(c.date_collecte), 'valeur': float(c.valeur_reelle),
                            'disaggregee': c.valeur_disaggregee} for c in collectes],
            'cibles_periodes': ValeurCiblePeriodeSerializer(cibles, many=True).data,
        })

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        ind = self.get_object()
        collectes = ind.collectes.filter(statut='valide')
        return Response({
            'taux_realisation': ind.taux_realisation,
            'statut': ind.statut,
            'nb_collectes': collectes.count(),
            'derniere_valeur': float(ind.valeur_realisee or 0),
            'valeur_cible': float(ind.valeur_cible_globale or 0),
            'alertes_actives': ind.alertes.filter(lue=False).count(),
        })

    @action(detail=False, methods=['get'])
    def tableau_bord(self, request):
        projet_id = request.query_params.get('projet')
        programme_id = request.query_params.get('programme')
        qs = Indicateur.objects.filter(actif=True)
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        return Response({
            'total': qs.count(),
            'par_statut': {s: qs.filter(statut=s).count() for s, _ in Indicateur.STATUT_CHOICES},
            'par_type': {t: qs.filter(type_indicateur=t).count() for t, _ in Indicateur.TYPE_CHOICES},
            'en_alerte': qs.filter(alertes__lue=False).distinct().count(),
        })

    @action(detail=False, methods=['post'])
    def generer_alertes(self, request):
        projet_id = request.data.get('projet')
        qs = Indicateur.objects.filter(actif=True)
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        created = 0
        for ind in qs:
            if ind.taux_realisation < 80 and ind.statut not in ('atteint',):
                AlerteIndicateur.objects.get_or_create(
                    indicateur=ind,
                    type_alerte='cible_non_atteinte',
                    lue=False,
                    defaults={
                        'niveau': 'critique' if ind.taux_realisation < 50 else 'warning',
                        'message': f"L'indicateur {ind.code} est à {ind.taux_realisation}% de sa cible.",
                        'destinataire': ind.responsable,
                    }
                )
                created += 1
        return Response({'alertes_generees': created})


class ValeurCiblePeriodeViewSet(viewsets.ModelViewSet):
    queryset = ValeurCiblePeriode.objects.order_by('annee', 'trimestre')
    serializer_class = ValeurCiblePeriodeSerializer
    permission_classes = [CanEditSE]

    def get_queryset(self):
        qs = super().get_queryset()
        ind = self.request.query_params.get('indicateur')
        return qs.filter(indicateur_id=ind) if ind else qs


class CollecteIndicateurViewSet(viewsets.ModelViewSet):
    queryset = CollecteIndicateur.objects.select_related(
        'indicateur', 'collecteur', 'valide_par'
    ).order_by('-date_collecte')
    serializer_class = CollecteIndicateurSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CollecteIndicateurFilter
    ordering_fields = ['date_collecte', 'valeur_reelle', 'statut']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadSE()]
        if self.action in ['valider', 'rejeter']:
            return [CanValidateSE()]
        return [CanEditSE()]

    def perform_create(self, s):
        s.save(collecteur=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        c = self.get_object()
        if c.statut not in ('brouillon', 'soumis'):
            return Response({'detail': 'Collecte déjà traitée.'}, status=400)
        c.valider(request.user)
        return Response(CollecteIndicateurSerializer(c).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        c = self.get_object()
        c.rejeter(request.user, request.data.get('motif', ''))
        return Response(CollecteIndicateurSerializer(c).data)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        c = self.get_object()
        c.statut = 'soumis'
        c.save(update_fields=['statut'])
        return Response(CollecteIndicateurSerializer(c).data)


class AlerteIndicateurViewSet(viewsets.ModelViewSet):
    queryset = AlerteIndicateur.objects.select_related('indicateur', 'destinataire').order_by('-date_alerte')
    serializer_class = AlerteIndicateurSerializer
    permission_classes = [CanReadSE]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('mes_alertes'):
            qs = qs.filter(destinataire=self.request.user)
        if self.request.query_params.get('non_lues'):
            qs = qs.filter(lue=False)
        return qs

    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        a = self.get_object()
        a.lue = True
        a.date_lecture = timezone.now()
        a.save(update_fields=['lue', 'date_lecture'])
        return Response(AlerteIndicateurSerializer(a).data)

    @action(detail=False, methods=['post'])
    def tout_marquer_lu(self, request):
        qs = AlerteIndicateur.objects.filter(destinataire=request.user, lue=False)
        count = qs.count()
        qs.update(lue=True, date_lecture=timezone.now())
        return Response({'marquees': count})


# ─── M18 : Formulaires dynamiques ────────────────────────────────────────────

class FormulaireDynamiqueViewSet(viewsets.ModelViewSet):
    queryset = FormulaireDynamique.objects.select_related(
        'projet', 'programme', 'created_by'
    ).prefetch_related('champs').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FormulaireFilter
    search_fields = ['titre', 'code', 'description']
    permission_classes = [CanReadSE]

    def get_serializer_class(self):
        return FormulaireDynamiqueListSerializer if self.action == 'list' else FormulaireDynamiqueDetailSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        f = self.get_object()
        f.statut = 'publie'
        f.save(update_fields=['statut'])
        return Response(FormulaireDynamiqueDetailSerializer(f).data)

    @action(detail=True, methods=['post'])
    def fermer(self, request, pk=None):
        f = self.get_object()
        f.statut = 'ferme'
        f.save(update_fields=['statut'])
        return Response(FormulaireDynamiqueDetailSerializer(f).data)

    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        f = self.get_object()
        soumissions = f.soumissions.all()
        return Response({
            'total_soumissions': soumissions.count(),
            'soumissions_validees': soumissions.filter(statut='valide').count(),
            'soumissions_rejetees': soumissions.filter(statut='rejete').count(),
            'hors_ligne': soumissions.filter(soumis_hors_ligne=True).count(),
            'avec_gps': soumissions.filter(latitude__isnull=False).count(),
        })

    @action(detail=True, methods=['get'])
    def exporter_donnees(self, request, pk=None):
        f = self.get_object()
        soumissions = f.soumissions.filter(statut='valide').prefetch_related('reponses__champ')
        champs = list(f.champs.order_by('ordre'))
        rows = []
        for s in soumissions:
            row = {'soumission_id': s.id, 'date': str(s.created_at.date()),
                   'collecteur': str(s.soumetteur), 'lat': float(s.latitude or 0),
                   'lon': float(s.longitude or 0)}
            reponses = {r.champ_id: r for r in s.reponses.all()}
            for c in champs:
                r = reponses.get(c.id)
                row[c.libelle] = (r.valeur_texte or r.valeur_nombre or r.valeur_date
                                  if r else None)
            rows.append(row)
        return Response({'formulaire': f.titre, 'nb_lignes': len(rows), 'donnees': rows})


class ChampFormulaireViewSet(viewsets.ModelViewSet):
    queryset = ChampFormulaire.objects.order_by('ordre')
    serializer_class = ChampFormulaireSerializer
    permission_classes = [CanEditSE]

    def get_queryset(self):
        qs = super().get_queryset()
        f = self.request.query_params.get('formulaire')
        return qs.filter(formulaire_id=f) if f else qs


class SoumissionFormulaireViewSet(viewsets.ModelViewSet):
    queryset = SoumissionFormulaire.objects.select_related(
        'formulaire', 'soumetteur', 'valide_par'
    ).prefetch_related('reponses').order_by('-created_at')
    serializer_class = SoumissionFormulaireSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SoumissionFilter
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [CanReadSE]

    def perform_create(self, s):
        s.save(soumetteur=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        s = self.get_object()
        s.valider(request.user)
        return Response(SoumissionFormulaireSerializer(s).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        s = self.get_object()
        s.rejeter(request.user, request.data.get('motif', ''))
        return Response(SoumissionFormulaireSerializer(s).data)

    def get_queryset(self):
        qs = super().get_queryset()
        f = self.request.query_params.get('formulaire')
        return qs.filter(formulaire_id=f) if f else qs


# ─── M19 : Enquêtes ───────────────────────────────────────────────────────────

class EnqueteViewSet(viewsets.ModelViewSet):
    queryset = Enquete.objects.select_related(
        'projet', 'programme', 'responsable', 'created_by'
    ).prefetch_related('sections', 'questions').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EnqueteFilter
    search_fields = ['code', 'titre', 'description']
    permission_classes = [CanReadSE]

    def get_serializer_class(self):
        return EnqueteListSerializer if self.action == 'list' else EnqueteDetailSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        e = self.get_object()
        e.statut = 'active'
        e.save(update_fields=['statut'])
        return Response(EnqueteDetailSerializer(e).data)

    @action(detail=True, methods=['post'])
    def fermer(self, request, pk=None):
        e = self.get_object()
        e.statut = 'fermee'
        e.save(update_fields=['statut'])
        return Response(EnqueteDetailSerializer(e).data)

    @action(detail=True, methods=['get'])
    def analyse(self, request, pk=None):
        enquete = self.get_object()
        reponses = enquete.reponses.filter(statut__in=['soumis', 'complete'])
        questions = enquete.questions.all()
        resultats = []
        for q in questions:
            rq = ReponseQuestion.objects.filter(
                reponse_enquete__in=reponses, question=q
            )
            res = {'question_id': q.id, 'libelle': q.libelle, 'type': q.type_question,
                   'nb_reponses': rq.count()}
            if q.type_question in ('choix_unique', 'choix_multiple'):
                freq = {}
                for r in rq:
                    choices = r.valeur_choix if isinstance(r.valeur_choix, list) else [r.valeur_texte]
                    for c in choices:
                        freq[c] = freq.get(c, 0) + 1
                res['frequences'] = freq
            elif q.type_question in ('nombre', 'note', 'likert'):
                vals = [float(r.valeur_nombre) for r in rq if r.valeur_nombre is not None]
                if vals:
                    res['moyenne'] = round(sum(vals) / len(vals), 2)
                    res['min'] = min(vals)
                    res['max'] = max(vals)
                    vals_sorted = sorted(vals)
                    mid = len(vals_sorted) // 2
                    res['mediane'] = vals_sorted[mid] if len(vals_sorted) % 2 else \
                        (vals_sorted[mid - 1] + vals_sorted[mid]) / 2
            resultats.append(res)
        return Response({
            'enquete': enquete.titre,
            'nb_reponses': reponses.count(),
            'taux_completion': enquete.taux_completion,
            'resultats': resultats,
        })

    @action(detail=True, methods=['get'])
    def rapport_statistique(self, request, pk=None):
        enquete = self.get_object()
        reponses = enquete.reponses.all()
        return Response({
            'meta': {'titre': enquete.titre, 'type': enquete.type_enquete,
                     'date': str(timezone.now().date())},
            'participation': {
                'total_repondants': reponses.count(),
                'complete': reponses.filter(statut='complete').count(),
                'en_cours': reponses.filter(statut='en_cours').count(),
                'par_canal': {c: reponses.filter(canal=c).count()
                              for c, _ in Enquete.CANAL_CHOICES},
                'hors_ligne': reponses.filter(soumis_hors_ligne=True).count(),
                'duree_moyenne': reponses.aggregate(avg=Avg('duree_completion'))['avg'],
            },
        })


class SectionEnqueteViewSet(viewsets.ModelViewSet):
    queryset = SectionEnquete.objects.prefetch_related('questions').order_by('ordre')
    serializer_class = SectionEnqueteSerializer
    permission_classes = [CanEditSE]

    def get_queryset(self):
        qs = super().get_queryset()
        e = self.request.query_params.get('enquete')
        return qs.filter(enquete_id=e) if e else qs


class QuestionEnqueteViewSet(viewsets.ModelViewSet):
    queryset = QuestionEnquete.objects.order_by('ordre')
    serializer_class = QuestionEnqueteSerializer
    permission_classes = [CanEditSE]

    def get_queryset(self):
        qs = super().get_queryset()
        e = self.request.query_params.get('enquete')
        s = self.request.query_params.get('section')
        if e:
            qs = qs.filter(enquete_id=e)
        if s:
            qs = qs.filter(section_id=s)
        return qs


class ReponseEnqueteViewSet(viewsets.ModelViewSet):
    queryset = ReponseEnquete.objects.select_related(
        'enquete', 'repondant'
    ).prefetch_related('reponses_questions').order_by('-created_at')
    serializer_class = ReponseEnqueteSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReponseEnqueteFilter
    permission_classes = [CanReadSE]

    def perform_create(self, s):
        s.save(repondant=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        e = self.request.query_params.get('enquete')
        return qs.filter(enquete_id=e) if e else qs

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        r = self.get_object()
        r.statut = 'soumis'
        r.soumis_le = timezone.now()
        r.save(update_fields=['statut', 'soumis_le'])
        return Response(ReponseEnqueteSerializer(r).data)


# ─── M20 : Cadre de résultats ─────────────────────────────────────────────────

class CadreResultatsViewSet(viewsets.ModelViewSet):
    queryset = CadreResultats.objects.select_related(
        'projet', 'programme', 'created_by'
    ).prefetch_related('niveaux').order_by('-created_at')
    serializer_class = CadreResultatsSerializer
    permission_classes = [CanReadSE]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params.get('projet')
        prog = self.request.query_params.get('programme')
        if p:
            qs = qs.filter(projet_id=p)
        if prog:
            qs = qs.filter(programme_id=prog)
        return qs

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        c = self.get_object()
        c.valide_par = request.user
        c.date_validation = timezone.now().date()
        c.save(update_fields=['valide_par', 'date_validation'])
        return Response(CadreResultatsSerializer(c).data)


class NiveauResultatViewSet(viewsets.ModelViewSet):
    queryset = NiveauResultat.objects.prefetch_related('indicateurs', 'enfants').order_by('niveau', 'ordre')
    serializer_class = NiveauResultatSerializer
    permission_classes = [CanEditSE]

    def get_queryset(self):
        qs = super().get_queryset()
        cadre = self.request.query_params.get('cadre')
        niveau = self.request.query_params.get('niveau')
        if cadre:
            qs = qs.filter(cadre_id=cadre)
        if niveau:
            qs = qs.filter(niveau=niveau)
        return qs


class TheorieChangementViewSet(viewsets.ModelViewSet):
    queryset = TheorieChangement.objects.select_related('projet', 'programme', 'created_by')
    serializer_class = TheorieChangementSerializer
    permission_classes = [CanReadSE]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params.get('projet')
        if p:
            qs = qs.filter(projet_id=p)
        return qs

    def perform_create(self, s):
        s.save(created_by=self.request.user)


class EvaluationViewSet(viewsets.ModelViewSet):
    queryset = Evaluation.objects.select_related(
        'projet', 'programme', 'responsable', 'created_by'
    ).prefetch_related('criteres', 'lecons').order_by('-date_debut')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EvaluationFilter
    search_fields = ['reference', 'titre']
    ordering_fields = ['date_debut', 'note_globale', 'statut']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanReadSE()]
        return [CanEditSE()]

    def get_serializer_class(self):
        return EvaluationListSerializer if self.action == 'list' else EvaluationDetailSerializer

    def perform_create(self, s):
        e = s.save(created_by=self.request.user)
        AuditLog.log(self.request.user, 'create', module='suivi_evaluation',
                     objet_type='Evaluation', objet_id=e.id, request=self.request)

    @action(detail=True, methods=['post'])
    def noter(self, request, pk=None):
        ev = self.get_object()
        criteres_data = request.data.get('criteres', [])
        for cd in criteres_data:
            CritereEvaluation.objects.update_or_create(
                evaluation=ev, critere=cd['critere'],
                defaults={'note': cd['note'], 'observation': cd.get('observation', '')}
            )
        notes = ev.criteres.values_list('note', flat=True)
        if notes:
            ev.note_globale = round(sum(notes) / len(notes), 2)
            ev.save(update_fields=['note_globale'])
        return Response(EvaluationDetailSerializer(ev).data)

    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        ev = self.get_object()
        ns = request.data.get('statut')
        if ns not in [s[0] for s in Evaluation.STATUT_CHOICES]:
            return Response({'detail': 'Statut invalide.'}, status=400)
        ev.statut = ns
        ev.save(update_fields=['statut'])
        return Response(EvaluationDetailSerializer(ev).data)


class CritereEvaluationViewSet(viewsets.ModelViewSet):
    queryset = CritereEvaluation.objects.all()
    serializer_class = CritereEvaluationSerializer
    permission_classes = [CanEditSE]

    def get_queryset(self):
        qs = super().get_queryset()
        ev = self.request.query_params.get('evaluation')
        return qs.filter(evaluation_id=ev) if ev else qs


class LeconApprisViewSet(viewsets.ModelViewSet):
    queryset = LeconApprise.objects.select_related(
        'projet', 'programme', 'evaluation', 'auteur', 'valide_par'
    ).order_by('-created_at')
    serializer_class = LeconApprisSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LeconApprisFilter
    search_fields = ['titre', 'description', 'domaine']
    permission_classes = [CanReadSE]

    def perform_create(self, s):
        s.save(auteur=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        l = self.get_object()
        l.statut = 'valide'
        l.valide_par = request.user
        l.save(update_fields=['statut', 'valide_par'])
        return Response(LeconApprisSerializer(l).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        l = self.get_object()
        l.statut = 'publie'
        l.save(update_fields=['statut'])
        return Response(LeconApprisSerializer(l).data)


# ─── Rapports S&E ─────────────────────────────────────────────────────────────

class RapportSEViewSet(viewsets.ModelViewSet):
    queryset = RapportSE.objects.select_related(
        'projet', 'programme', 'redacteur', 'valide_par'
    ).order_by('-date_rapport')
    serializer_class = RapportSESerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RapportSEFilter
    search_fields = ['reference', 'titre']
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [CanReadSE]

    def perform_create(self, s):
        s.save(redacteur=self.request.user)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        r = self.get_object()
        r.statut = 'valide'
        r.valide_par = request.user
        r.date_validation = timezone.now()
        r.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(RapportSESerializer(r).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        r = self.get_object()
        r.statut = 'publie'
        r.save(update_fields=['statut'])
        return Response(RapportSESerializer(r).data)

    @action(detail=False, methods=['post'])
    def generer_automatique(self, request):
        projet_id = request.data.get('projet')
        programme_id = request.data.get('programme')
        type_rapport = request.data.get('type_rapport', 'suivi_evaluation')
        periode = request.data.get('periode', 'trimestriel')

        indicateurs = Indicateur.objects.filter(actif=True)
        if projet_id:
            indicateurs = indicateurs.filter(projet_id=projet_id)
        if programme_id:
            indicateurs = indicateurs.filter(programme_id=programme_id)

        atteints = indicateurs.filter(statut='atteint').count()
        non_atteints = indicateurs.filter(statut='non_atteint').count()
        total = indicateurs.count()

        synthese = (
            f"Sur {total} indicateurs suivis, {atteints} ont atteint leur cible "
            f"({round(atteints/total*100 if total else 0, 1)}%). "
            f"{non_atteints} indicateurs n'ont pas atteint leur cible."
        )

        rapport = RapportSE.objects.create(
            projet_id=projet_id,
            programme_id=programme_id,
            titre=f"Rapport {periode} S&E — {timezone.now().strftime('%B %Y')}",
            type_rapport=type_rapport,
            periode=periode,
            date_rapport=timezone.now().date(),
            synthese=synthese,
            redacteur=request.user,
            statut='brouillon',
            genere_par_ia=True,
        )
        rapport.indicateurs_inclus.set(indicateurs)
        return Response(RapportSESerializer(rapport).data, status=201)


# ─── Analyse prédictive ───────────────────────────────────────────────────────

class AnalysePredictiveViewSet(viewsets.ModelViewSet):
    queryset = AnalysePredictive.objects.select_related(
        'indicateur', 'projet', 'demande_par'
    ).order_by('-created_at')
    serializer_class = AnalysePredictiveSerializer
    permission_classes = [CanReadSE]

    def perform_create(self, s):
        analyse = s.save(demande_par=self.request.user)
        self._executer_analyse(analyse)

    def _executer_analyse(self, analyse):
        """
        Moteur d'analyse statistique.
        - Indicateur fourni : régression linéaire sur l'historique des collectes
        - Projet fourni    : analyse de portefeuille (taux moyen, indicateurs critiques)
        - Aucun périmètre  : analyse globale de tous les indicateurs actifs
        """
        import math
        from datetime import timedelta

        def _regression(xs, ys):
            """Régression linéaire y=a*x+b. Retourne (a, b, r2)."""
            n = len(xs)
            if n < 2:
                return 0.0, ys[0] if ys else 0.0, 0.0
            mu_x = sum(xs) / n
            mu_y = sum(ys) / n
            num = sum((xs[i] - mu_x) * (ys[i] - mu_y) for i in range(n))
            den = sum((xs[i] - mu_x) ** 2 for i in range(n))
            a = num / den if den else 0.0
            b = mu_y - a * mu_x
            ss_res = sum((ys[i] - (a * xs[i] + b)) ** 2 for i in range(n))
            ss_tot = sum((ys[i] - mu_y) ** 2 for i in range(n))
            r2 = max(0.0, 1 - ss_res / ss_tot) if ss_tot > 1e-9 else 1.0
            return a, b, r2

        try:
            # ── CAS 1 : indicateur fourni ─────────────────────────────────────
            if analyse.indicateur:
                ind = analyse.indicateur
                collectes = list(ind.collectes.filter(statut='valide').order_by('date_collecte'))
                valeurs = [float(c.valeur_reelle) for c in collectes]
                nb = len(valeurs)

                if nb >= 2:
                    xs = list(range(nb))
                    pente, intercept, r2 = _regression(xs, valeurs)
                    sigma = math.sqrt(
                        sum((valeurs[i] - (pente * xs[i] + intercept)) ** 2 for i in range(nb)) / nb
                    ) if nb > 1 else 0

                    # Prévisions (4 trimestres)
                    derniere_date = collectes[-1].date_collecte
                    previsions = []
                    for i in range(1, 5):
                        val_prev = intercept + pente * (nb - 1 + i)
                        marge = sigma * (1 + 0.1 * i)
                        previsions.append({
                            'date': str(derniere_date + timedelta(days=90 * i)),
                            'valeur_prevue': round(val_prev, 2),
                            'intervalle_confiance': round(marge, 2),
                        })

                    # Risques
                    tx = ind.taux_realisation
                    risques = []
                    if tx < 50:
                        risques.append(f"Performance critique : {tx}% de réalisation — objectif très loin d'être atteint")
                    elif tx < 75:
                        risques.append(f"Performance insuffisante : {tx}% — indicateur à surveiller de près")
                    if pente < 0:
                        risques.append(f"Tendance décroissante détectée ({round(pente, 2)} unités/période)")
                    if sigma > abs(pente) * 2 and pente != 0:
                        risques.append("Forte volatilité inter-périodes — données peu stables")

                    # Suggestions
                    sugg = []
                    direction = "positive ↗" if pente > 0 else "négative ↘"
                    sugg.append(f"Tendance {direction} de {abs(round(pente, 2))} unités/période (R²={round(r2, 2)}).")
                    if tx < 80:
                        sugg.append(f"Taux de réalisation : {tx}%. Renforcer les activités liées à cet indicateur.")
                    proj_fin = previsions[-1]['valeur_prevue'] if previsions else None
                    if proj_fin and ind.valeur_cible_globale:
                        ecart = round(float(ind.valeur_cible_globale) - proj_fin, 2)
                        if ecart > 0:
                            sugg.append(f"À ce rythme, l'écart résiduel à la cible sera de {ecart} unités.")
                        else:
                            sugg.append(f"La cible devrait être dépassée de {abs(ecart)} unités à ce rythme.")

                    analyse.resultats = {
                        'nb_points': nb,
                        'valeur_initiale': round(valeurs[0], 2),
                        'valeur_finale': round(valeurs[-1], 2),
                        'pente': round(pente, 4),
                        'r_carre': round(r2, 4),
                        'sigma': round(sigma, 4),
                        'taux_realisation': tx,
                        'tendance': 'hausse' if pente > 0 else 'baisse',
                        'cible_globale': float(ind.valeur_cible_globale) if ind.valeur_cible_globale else None,
                    }
                    analyse.previsions = previsions
                    analyse.risques_detectes = risques
                    analyse.suggestions = '\n'.join(sugg)
                    # Confiance : qualité regression + quantité données
                    analyse.confiance_score = round(min(95, 30 + r2 * 40 + nb * 3), 1)
                else:
                    analyse.resultats = {
                        'message': f"Seulement {nb} collecte(s) validée(s) — minimum 2 requis pour l'analyse.",
                        'taux_realisation': ind.taux_realisation,
                    }
                    analyse.suggestions = "Enrichir l'historique de collecte pour obtenir une analyse plus fiable."
                    analyse.confiance_score = 15.0

            # ── CAS 2 : périmètre projet ──────────────────────────────────────
            elif analyse.projet:
                qs_ind = Indicateur.objects.filter(projet=analyse.projet, actif=True)
                nb_ind = qs_ind.count()
                ind_list = list(qs_ind)
                taux_moyen = round(sum(i.taux_realisation for i in ind_list) / nb_ind, 1) if nb_ind else 0

                atteints      = qs_ind.filter(statut='atteint').count()
                non_atteints  = qs_ind.filter(statut='non_atteint').count()
                en_cours      = qs_ind.filter(statut='en_cours').count()
                ind_critiques = [i.intitule for i in ind_list if i.taux_realisation < 40]

                risques = []
                if taux_moyen < 50:
                    risques.append(f"Performance globale insuffisante : {taux_moyen}% de réalisation en moyenne")
                for n in ind_critiques[:3]:
                    risques.append(f"Indicateur critique : {n}")

                sugg = [
                    f"Portefeuille projet : {taux_moyen}% de réalisation sur {nb_ind} indicateurs.",
                    f"{atteints} atteint(s), {en_cours} en cours, {non_atteints} non atteint(s).",
                ]
                if non_atteints > 0:
                    sugg.append(f"Prioriser les {non_atteints} indicateur(s) non atteint(s).")

                analyse.resultats = {
                    'nb_indicateurs': nb_ind,
                    'taux_moyen': taux_moyen,
                    'atteints': atteints,
                    'en_cours': en_cours,
                    'non_atteints': non_atteints,
                }
                analyse.risques_detectes = risques
                analyse.suggestions = '\n'.join(sugg)
                analyse.confiance_score = round(min(85, 40 + nb_ind * 4), 1)

            # ── CAS 3 : analyse globale ───────────────────────────────────────
            else:
                qs_ind = Indicateur.objects.filter(actif=True)
                nb = qs_ind.count()
                ind_list = list(qs_ind)
                taux_moyen = round(sum(i.taux_realisation for i in ind_list) / nb, 1) if nb else 0
                atteints = qs_ind.filter(statut='atteint').count()
                en_alerte = qs_ind.filter(statut='non_atteint').count()

                analyse.resultats = {
                    'nb_indicateurs': nb,
                    'taux_moyen': taux_moyen,
                    'atteints': atteints,
                    'en_alerte': en_alerte,
                    'taux_atteinte': round(atteints / nb * 100, 1) if nb else 0,
                }
                analyse.suggestions = (
                    f"Analyse globale : {taux_moyen}% de réalisation sur {nb} indicateurs actifs. "
                    f"{atteints} atteints, {en_alerte} en alerte."
                )
                analyse.confiance_score = round(min(75, 35 + nb * 2), 1)

            analyse.statut = 'complete'
            analyse.completed_at = timezone.now()
            analyse.save()

        except Exception as exc:
            analyse.statut = 'erreur'
            analyse.resultats = {'erreur': str(exc)}
            analyse.save(update_fields=['statut', 'resultats'])

    @action(detail=True, methods=['post'])
    def lancer(self, request, pk=None):
        """Relance ou exécute une analyse en attente ou en erreur."""
        analyse = self.get_object()
        if analyse.statut == 'en_cours':
            return Response({'detail': 'Analyse déjà en cours.'}, status=400)
        analyse.statut = 'en_cours'
        analyse.save(update_fields=['statut'])
        self._executer_analyse(analyse)
        return Response(AnalysePredictiveSerializer(analyse).data)

    @action(detail=False, methods=['post'])
    def analyser_projet(self, request):
        projet_id = request.data.get('projet')
        if not projet_id:
            return Response({'detail': 'projet requis.'}, status=400)
        indicateurs = Indicateur.objects.filter(projet_id=projet_id, actif=True)
        results = []
        for ind in indicateurs:
            collectes = list(ind.collectes.filter(statut='valide').order_by('date_collecte'))
            if len(collectes) >= 2:
                valeurs = [float(c.valeur_reelle) for c in collectes]
                tendance = valeurs[-1] - valeurs[-2]
                results.append({
                    'indicateur': ind.code, 'taux': ind.taux_realisation,
                    'tendance': 'hausse' if tendance > 0 else 'baisse',
                    'delta': round(tendance, 4),
                })
        return Response({'projet_id': projet_id, 'nb_indicateurs': len(results), 'analyses': results})


# ─── SIG ──────────────────────────────────────────────────────────────────────

class PointSIGViewSet(viewsets.ModelViewSet):
    queryset = PointSIG.objects.select_related('projet', 'programme', 'indicateur', 'created_by')
    serializer_class = PointSIGSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = PointSIGFilter
    search_fields = ['titre', 'description']
    permission_classes = [CanReadSE]

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def geojson(self, request):
        qs = self.filter_queryset(self.get_queryset())
        features = []
        for p in qs:
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [float(p.longitude), float(p.latitude)]},
                'properties': {
                    'id': p.id, 'type': p.type_point, 'titre': p.titre,
                    'description': p.description, 'valeur': float(p.valeur or 0),
                    'couleur': p.couleur, 'icone': p.icone,
                    'projet_id': p.projet_id, 'programme_id': p.programme_id,
                    'donnees_extra': p.donnees_extra,
                },
            })
        return Response({'type': 'FeatureCollection', 'features': features})

    @action(detail=False, methods=['get'])
    def carte_indicateurs(self, request):
        projet_id = request.query_params.get('projet')
        programme_id = request.query_params.get('programme')
        qs = PointSIG.objects.filter(actif=True, type_point='indicateur')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        data = PointSIGSerializer(qs, many=True).data
        return Response({'points': data, 'total': len(data)})


# ─── Dashboard S&E ────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadSE])
def dashboard_se(request):
    projet_id = request.query_params.get('projet')
    programme_id = request.query_params.get('programme')
    today = timezone.now().date()

    qs_ind = Indicateur.objects.filter(actif=True)
    qs_coll = CollecteIndicateur.objects.all()
    qs_enq = Enquete.objects.all()
    qs_eval = Evaluation.objects.all()

    if projet_id:
        qs_ind = qs_ind.filter(projet_id=projet_id)
        qs_coll = qs_coll.filter(indicateur__projet_id=projet_id)
        qs_enq = qs_enq.filter(projet_id=projet_id)
        qs_eval = qs_eval.filter(projet_id=projet_id)
    if programme_id:
        qs_ind = qs_ind.filter(programme_id=programme_id)
        qs_coll = qs_coll.filter(indicateur__programme_id=programme_id)
        qs_enq = qs_enq.filter(programme_id=programme_id)
        qs_eval = qs_eval.filter(programme_id=programme_id)

    taux_moyen = 0
    indicateurs_list = list(qs_ind)
    if indicateurs_list:
        taux_moyen = round(
            sum(i.taux_realisation for i in indicateurs_list) / len(indicateurs_list), 1
        )

    return Response({
        'indicateurs': {
            'total': len(indicateurs_list),
            'atteints': qs_ind.filter(statut='atteint').count(),
            'en_cours': qs_ind.filter(statut='en_cours').count(),
            'non_atteints': qs_ind.filter(statut='non_atteint').count(),
            'taux_moyen': taux_moyen,
            'en_alerte': AlerteIndicateur.objects.filter(
                indicateur__in=qs_ind, lue=False
            ).count(),
        },
        'collectes': {
            'total': qs_coll.count(),
            'validees': qs_coll.filter(statut='valide').count(),
            'en_attente': qs_coll.filter(statut__in=['brouillon', 'soumis']).count(),
            'ce_mois': qs_coll.filter(
                date_collecte__month=today.month, date_collecte__year=today.year
            ).count(),
        },
        'enquetes': {
            'total': qs_enq.count(),
            'actives': qs_enq.filter(statut='active').count(),
            'reponses_total': ReponseEnquete.objects.filter(enquete__in=qs_enq).count(),
        },
        'evaluations': {
            'total': qs_eval.count(),
            'en_cours': qs_eval.filter(statut='en_cours').count(),
            'note_moyenne': qs_eval.aggregate(avg=Avg('note_globale'))['avg'],
        },
        'lecons_apprises': LeconApprise.objects.filter(
            Q(projet_id=projet_id) if projet_id else Q()
        ).filter(statut='publie').count(),
    })


# ─── M29 : Gestion des Risques ───────────────────────────────────────────────

class RegistreRisqueViewSet(viewsets.ModelViewSet):
    queryset = RegistreRisque.objects.select_related(
        'projet', 'programme', 'activite', 'responsable', 'created_by'
    ).prefetch_related('plans_mitigation', 'suivis', 'alertes_risque').order_by('-score_risque')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RegistreRisqueFilter
    search_fields = ['reference', 'intitule', 'description', 'causes', 'consequences']
    ordering_fields = ['score_risque', 'probabilite', 'impact', 'date_identification']

    def get_permissions(self):
        return [CanReadSE()] if self.action in ['list', 'retrieve'] else [CanEditSE()]

    def get_serializer_class(self):
        return RegistreRisqueListSerializer if self.action == 'list' else RegistreRisqueDetailSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def ajouter_suivi(self, request, pk=None):
        risque = self.get_object()
        suivi = SuiviRisque.objects.create(
            risque=risque,
            date_suivi=request.data.get('date_suivi', timezone.now().date()),
            probabilite=request.data.get('probabilite', risque.probabilite),
            impact=request.data.get('impact', risque.impact),
            statut=request.data.get('statut', risque.statut),
            tendance=request.data.get('tendance', risque.tendance),
            observations=request.data.get('observations', ''),
            actions_prises=request.data.get('actions_prises', ''),
            suivi_par=request.user,
        )
        risque.probabilite = suivi.probabilite
        risque.impact = suivi.impact
        risque.tendance = suivi.tendance
        risque.statut = suivi.statut
        risque.date_revue = suivi.date_suivi
        risque.save()
        return Response(SuiviRisqueSerializer(suivi).data, status=201)

    @action(detail=True, methods=['post'])
    def ajouter_plan_mitigation(self, request, pk=None):
        risque = self.get_object()
        plan = PlanMitigation.objects.create(
            risque=risque,
            type_mitigation=request.data.get('type_mitigation', 'prevention'),
            description=request.data.get('description', ''),
            objectif=request.data.get('objectif', ''),
            responsable_id=request.data.get('responsable'),
            date_debut=request.data.get('date_debut'),
            date_fin=request.data.get('date_fin'),
            cout_estime=request.data.get('cout_estime', 0),
        )
        if risque.statut == 'identifie':
            risque.statut = 'en_cours_traitement'
            risque.save(update_fields=['statut'])
        return Response(PlanMitigationSerializer(plan).data, status=201)

    @action(detail=False, methods=['get'])
    def matrice(self, request):
        risques = RegistreRisque.objects.all()
        if request.query_params.get('projet'):
            risques = risques.filter(projet_id=request.query_params['projet'])
        if request.query_params.get('programme'):
            risques = risques.filter(programme_id=request.query_params['programme'])
        matrice = {
            'critique': list(risques.filter(niveau_risque='critique').values(
                'id', 'reference', 'intitule', 'score_risque', 'probabilite', 'impact')),
            'important': list(risques.filter(niveau_risque='important').values(
                'id', 'reference', 'intitule', 'score_risque', 'probabilite', 'impact')),
            'modere': list(risques.filter(niveau_risque='modere').values(
                'id', 'reference', 'intitule', 'score_risque', 'probabilite', 'impact')),
            'faible': list(risques.filter(niveau_risque='faible').values(
                'id', 'reference', 'intitule', 'score_risque', 'probabilite', 'impact')),
        }
        return Response(matrice)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = RegistreRisque.objects.all()
        return Response({
            'total': qs.count(),
            'par_niveau': {
                'critique': qs.filter(niveau_risque='critique').count(),
                'important': qs.filter(niveau_risque='important').count(),
                'modere': qs.filter(niveau_risque='modere').count(),
                'faible': qs.filter(niveau_risque='faible').count(),
            },
            'par_categorie': {c: qs.filter(categorie=c).count()
                             for c, _ in RegistreRisque.CATEGORIE_CHOICES},
            'par_statut': {s: qs.filter(statut=s).count()
                          for s, _ in RegistreRisque.STATUT_CHOICES},
            'non_traites': qs.filter(statut='identifie').count(),
            'critiques_non_traites': qs.filter(
                niveau_risque='critique', statut='identifie'
            ).count(),
        })


class PlanMitigationViewSet(viewsets.ModelViewSet):
    queryset = PlanMitigation.objects.select_related('risque', 'responsable').order_by('date_debut')
    serializer_class = PlanMitigationSerializer
    permission_classes = [CanEditSE]

    def get_queryset(self):
        qs = super().get_queryset()
        r = self.request.query_params.get('risque')
        return qs.filter(risque_id=r) if r else qs

    @action(detail=True, methods=['post'])
    def marquer_realise(self, request, pk=None):
        plan = self.get_object()
        plan.statut = 'realise'
        plan.resultat = request.data.get('resultat', '')
        plan.probabilite_residuelle = request.data.get('probabilite_residuelle')
        plan.impact_residuel = request.data.get('impact_residuel')
        plan.save()
        return Response(PlanMitigationSerializer(plan).data)


class SuiviRisqueViewSet(viewsets.ModelViewSet):
    queryset = SuiviRisque.objects.select_related('risque', 'suivi_par').order_by('-date_suivi')
    serializer_class = SuiviRisqueSerializer
    permission_classes = [CanReadSE]

    def get_queryset(self):
        qs = super().get_queryset()
        r = self.request.query_params.get('risque')
        return qs.filter(risque_id=r) if r else qs

    def perform_create(self, s):
        s.save(suivi_par=self.request.user)


class AlerteRisqueViewSet(viewsets.ModelViewSet):
    queryset = AlerteRisque.objects.select_related('risque', 'destinataire').order_by('-date_alerte')
    serializer_class = AlerteRisqueSerializer
    permission_classes = [CanReadSE]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('non_lues'):
            qs = qs.filter(lue=False)
        return qs.filter(
            Q(destinataire=self.request.user) | Q(destinataire__isnull=True)
        )

    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        alerte = self.get_object()
        alerte.lue = True
        alerte.date_lecture = timezone.now()
        alerte.save(update_fields=['lue', 'date_lecture'])
        return Response({'lue': True})


@api_view(['GET'])
@permission_classes([CanReadSE])
def dashboard_direction(request):
    from programmes_projets.models import Programme, Projet

    qs_ind   = Indicateur.objects.filter(actif=True)
    ind_list = list(qs_ind)
    nb_ind   = len(ind_list)
    taux_moyen = round(
        sum(i.taux_realisation for i in ind_list) / nb_ind, 1
    ) if nb_ind else 0
    tx_atteinte = round(
        qs_ind.filter(statut='atteint').count() / nb_ind * 100, 1
    ) if nb_ind else 0

    # Risques critiques (niveau=critique ou score > 15)
    risques_critiques = RegistreRisque.objects.filter(
        niveau_risque='critique'
    ).count()

    # Répartition indicateurs par type
    from django.db.models import Count
    par_type = list(
        qs_ind.values('type_indicateur').annotate(nb=Count('id')).order_by('-nb')
    )

    # Évolution mensuelle des collectes (6 derniers mois)
    from django.db.models.functions import TruncMonth
    today = timezone.now()
    collectes_mensuelles = list(
        CollecteIndicateur.objects.filter(
            statut='valide',
            date_collecte__gte=today.date().replace(day=1)
        ).annotate(mois=TruncMonth('date_collecte'))
        .values('mois').annotate(nb=Count('id')).order_by('mois')
    )

    projets_qs = Projet.objects.filter(statut='en_cours')
    # Projets avec indicateurs en alerte (critique)
    projets_critiques = qs_ind.filter(
        statut='non_atteint'
    ).values_list('projet_id', flat=True).distinct().count()

    return Response({
        # KPIs exécutifs
        'programmes_actifs':    Programme.objects.filter(statut='en_cours').count(),
        'projets_actifs':       projets_qs.count(),
        'taux_atteinte_global': tx_atteinte,
        'taux_realisation_moyen': taux_moyen,
        # Indicateurs
        'indicateurs': {
            'total':            nb_ind,
            'atteints':         qs_ind.filter(statut='atteint').count(),
            'partiels':         qs_ind.filter(statut='partiellement_atteint').count(),
            'non_atteints':     qs_ind.filter(statut='non_atteint').count(),
            'en_cours':         qs_ind.filter(statut='en_cours').count(),
            'par_type':         par_type,
        },
        # Alertes et risques
        'alertes_actives':      AlerteIndicateur.objects.filter(lue=False).count(),
        'risques_critiques':    risques_critiques,
        'projets_critiques':    projets_critiques,
        # Évaluations
        'evaluations': {
            'total':            Evaluation.objects.count(),
            'en_cours':         Evaluation.objects.filter(statut='en_cours').count(),
            'note_moyenne':     round(float(
                Evaluation.objects.aggregate(a=Avg('note_globale'))['a'] or 0
            ), 2),
        },
        # Enquêtes
        'enquetes': {
            'actives':          Enquete.objects.filter(statut='active').count(),
            'reponses_total':   ReponseEnquete.objects.count(),
        },
        # Capitalisation
        'lecons_publiees':      LeconApprise.objects.filter(statut='publie').count(),
        'bonnes_pratiques':     LeconApprise.objects.filter(
            statut='publie', type_lecon='bonne_pratique'
        ).count(),
    })
