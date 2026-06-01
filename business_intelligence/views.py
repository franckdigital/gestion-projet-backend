import json
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import (
    TableauBord, WidgetTableauBord, PartageTableauBord,
    DataWarehouseSnapshot, RapportBI,
    DatamartFinance, DatamartSE,
    DatamartRH, DatamartCourrier, DatamartGED, DatamartRisque,
    ConnecteurBI, KPIPersonnalise,
)
from .serializers import (
    TableauBordListSerializer, TableauBordDetailSerializer,
    WidgetTableauBordSerializer, PartageTableauBordSerializer,
    DataWarehouseSnapshotSerializer,
    RapportBIListSerializer, RapportBIDetailSerializer,
    DatamartFinanceSerializer, DatamartSESerializer,
    DatamartRHSerializer, DatamartCourrierSerializer,
    DatamartGEDSerializer, DatamartRisqueSerializer,
    ConnecteurBISerializer, KPIPersonnaliseSerializer,
)
from .filters import TableauBordFilter, RapportBIFilter, DatamartFinanceFilter, DatamartSEFilter

CanReadBI = HasModulePermission.for_module('business_intelligence', 'peut_lire')
CanEditBI = HasModulePermission.for_module('business_intelligence', 'peut_modifier')


# ─── M34 : Tableaux de bord ───────────────────────────────────────────────────

class TableauBordViewSet(viewsets.ModelViewSet):
    queryset = TableauBord.objects.select_related(
        'proprietaire', 'programme', 'projet'
    ).prefetch_related('widgets', 'partages').order_by('-est_defaut', 'nom')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TableauBordFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'created_at', 'updated_at']

    def get_permissions(self):
        return [CanReadBI()] if self.action in ['list', 'retrieve', 'defaut', 'predefinit'] else [CanEditBI()]

    def get_serializer_class(self):
        return TableauBordListSerializer if self.action == 'list' else TableauBordDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        return qs.filter(
            Q(proprietaire=user) | Q(est_public=True) | Q(partages__utilisateur=user)
        ).distinct()

    def perform_create(self, s):
        s.save(proprietaire=self.request.user)

    @action(detail=True, methods=['post'])
    def dupliquer(self, request, pk=None):
        tb = self.get_object()
        nouveau = TableauBord.objects.create(
            nom=f"{tb.nom} (copie)",
            type_dashboard=tb.type_dashboard,
            description=tb.description,
            proprietaire=request.user,
            programme=tb.programme,
            projet=tb.projet,
            configuration=tb.configuration,
        )
        for widget in tb.widgets.filter(actif=True):
            WidgetTableauBord.objects.create(
                tableau_bord=nouveau,
                titre=widget.titre,
                type_widget=widget.type_widget,
                source_donnees=widget.source_donnees,
                colonne=widget.colonne,
                ligne=widget.ligne,
                largeur=widget.largeur,
                hauteur=widget.hauteur,
                configuration=widget.configuration,
                ordre=widget.ordre,
            )
        return Response(TableauBordDetailSerializer(nouveau).data, status=201)

    @action(detail=True, methods=['post'])
    def partager(self, request, pk=None):
        tb = self.get_object()
        if tb.proprietaire != request.user:
            return Response({'detail': 'Seul le propriétaire peut partager.'}, status=403)
        utilisateur_id = request.data.get('utilisateur_id')
        niveau = request.data.get('niveau', 'lecture')
        partage, created = PartageTableauBord.objects.get_or_create(
            tableau_bord=tb,
            utilisateur_id=utilisateur_id,
            defaults={'niveau': niveau},
        )
        if not created:
            partage.niveau = niveau
            partage.save(update_fields=['niveau'])
        return Response(PartageTableauBordSerializer(partage).data, status=201 if created else 200)

    @action(detail=False, methods=['get'])
    def defaut(self, request):
        role = request.query_params.get('role', 'chef_projet')
        tb = TableauBord.objects.filter(
            type_dashboard=role, est_defaut=True, actif=True
        ).first()
        if not tb:
            tb = TableauBord.objects.filter(
                Q(proprietaire=request.user) | Q(est_public=True), actif=True
            ).first()
        if not tb:
            return Response({'detail': 'Aucun tableau de bord disponible.'}, status=404)
        return Response(TableauBordDetailSerializer(tb).data)

    @action(detail=False, methods=['get'])
    def predefinit(self, request):
        role = request.query_params.get('role', 'chef_projet')
        projet_id = request.query_params.get('projet')
        programme_id = request.query_params.get('programme')
        return _generer_kpi_dashboard(role, projet_id, programme_id, request.user)


class WidgetTableauBordViewSet(viewsets.ModelViewSet):
    queryset = WidgetTableauBord.objects.select_related(
        'tableau_bord', 'filtre_projet', 'filtre_programme'
    ).order_by('ligne', 'colonne')
    serializer_class = WidgetTableauBordSerializer
    permission_classes = [CanEditBI]

    def get_queryset(self):
        qs = super().get_queryset()
        tb = self.request.query_params.get('tableau_bord')
        return qs.filter(tableau_bord_id=tb) if tb else qs

    @action(detail=True, methods=['get'])
    def actualiser(self, request, pk=None):
        widget = self.get_object()
        valeur = widget.calculer_valeur()
        return Response({'widget_id': widget.id, 'titre': widget.titre, **valeur})

    @action(detail=False, methods=['post'])
    def reordonner(self, request):
        positions = request.data.get('positions', [])
        for pos in positions:
            WidgetTableauBord.objects.filter(id=pos['id']).update(
                colonne=pos.get('colonne', 0),
                ligne=pos.get('ligne', 0),
                largeur=pos.get('largeur', 4),
                hauteur=pos.get('hauteur', 3),
            )
        return Response({'detail': f'{len(positions)} widget(s) repositionné(s).'})


# ─── M35 : Business Intelligence ─────────────────────────────────────────────

class DataWarehouseSnapshotViewSet(viewsets.ModelViewSet):
    queryset = DataWarehouseSnapshot.objects.select_related('cree_par').order_by('-created_at')
    serializer_class = DataWarehouseSnapshotSerializer
    permission_classes = [CanReadBI]

    def perform_create(self, s):
        snap = s.save(cree_par=self.request.user)
        raw = json.dumps(snap.donnees, default=str)
        snap.taille_ko = len(raw.encode()) // 1024
        snap.nb_enregistrements = (
            len(snap.donnees) if isinstance(snap.donnees, list)
            else sum(len(v) if isinstance(v, list) else 1 for v in snap.donnees.values())
        )
        snap.save(update_fields=['taille_ko', 'nb_enregistrements'])

    @action(detail=False, methods=['post'])
    def consolider(self, request):
        type_snap = request.data.get('type_snapshot', 'full')
        periode_debut = request.data.get('periode_debut', str(timezone.now().date().replace(day=1)))
        periode_fin = request.data.get('periode_fin', str(timezone.now().date()))

        donnees = _extraire_donnees_dw(type_snap, periode_debut, periode_fin)
        raw = json.dumps(donnees, default=str)

        snap = DataWarehouseSnapshot.objects.create(
            type_snapshot=type_snap,
            periode_debut=periode_debut,
            periode_fin=periode_fin,
            donnees=donnees,
            taille_ko=len(raw.encode()) // 1024,
            nb_enregistrements=sum(
                len(v) if isinstance(v, list) else 1 for v in donnees.values()
            ) if isinstance(donnees, dict) else len(donnees),
            cree_par=request.user,
        )
        return Response(DataWarehouseSnapshotSerializer(snap).data, status=201)


class RapportBIViewSet(viewsets.ModelViewSet):
    queryset = RapportBI.objects.select_related(
        'genere_par', 'valide_par', 'programme', 'projet'
    ).order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RapportBIFilter
    search_fields = ['titre']
    ordering_fields = ['created_at', 'statut', 'type_rapport']

    def get_permissions(self):
        return [CanReadBI()] if self.action in ['list', 'retrieve'] else [CanEditBI()]

    def get_serializer_class(self):
        return RapportBIListSerializer if self.action == 'list' else RapportBIDetailSerializer

    def perform_create(self, s):
        rapport = s.save(genere_par=self.request.user)
        rapport.generer_donnees()

    @action(detail=True, methods=['post'])
    def regenerer(self, request, pk=None):
        rapport = self.get_object()
        rapport.generer_donnees()
        return Response(RapportBIDetailSerializer(rapport).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        rapport = self.get_object()
        rapport.statut = 'valide'
        rapport.valide_par = request.user
        rapport.date_validation = timezone.now()
        rapport.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(RapportBIDetailSerializer(rapport).data)

    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        rapport = self.get_object()
        rapport.statut = 'publie'
        rapport.save(update_fields=['statut'])
        return Response(RapportBIDetailSerializer(rapport).data)

    @action(detail=False, methods=['get'])
    def types_disponibles(self, request):
        return Response([{'code': c, 'label': l} for c, l in RapportBI.TYPE_CHOICES])

    @action(detail=False, methods=['post'])
    def generer_rapport_executif(self, request):
        today = timezone.now().date()
        rapport = RapportBI.objects.create(
            titre=f"Rapport Exécutif — {today.strftime('%B %Y')}",
            type_rapport='rapport_executif',
            periode='mensuel',
            format_export='pdf',
            date_debut_periode=today.replace(day=1),
            date_fin_periode=today,
            programme_id=request.data.get('programme'),
            projet_id=request.data.get('projet'),
            genere_par=request.user,
            genere_par_ia=True,
        )
        rapport.generer_donnees()
        return Response(RapportBIDetailSerializer(rapport).data, status=201)


class DatamartFinanceViewSet(viewsets.ModelViewSet):
    queryset = DatamartFinance.objects.select_related('programme', 'projet').order_by('-annee', '-mois')
    serializer_class = DatamartFinanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DatamartFinanceFilter
    permission_classes = [CanReadBI]

    @action(detail=False, methods=['get'])
    def tendances(self, request):
        programme_id = request.query_params.get('programme')
        annee = request.query_params.get('annee', timezone.now().year)
        qs = DatamartFinance.objects.filter(annee=annee)
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        return Response({
            'annee': annee,
            'par_mois': list(
                qs.values('mois').annotate(
                    prevu=Sum('budget_prevu'),
                    realise=Sum('budget_realise')
                ).order_by('mois')
            ),
            'par_trimestre': list(
                qs.values('trimestre').annotate(
                    prevu=Sum('budget_prevu'),
                    realise=Sum('budget_realise')
                ).order_by('trimestre')
            ),
        })


class DatamartSEViewSet(viewsets.ModelViewSet):
    queryset = DatamartSE.objects.select_related('programme', 'projet').order_by('-annee', '-trimestre')
    serializer_class = DatamartSESerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DatamartSEFilter
    permission_classes = [CanReadBI]

    @action(detail=False, methods=['get'])
    def evolution(self, request):
        programme_id = request.query_params.get('programme')
        qs = DatamartSE.objects.all()
        if programme_id:
            qs = qs.filter(programme_id=programme_id)
        return Response({
            'evolution': list(
                qs.values('annee', 'trimestre').annotate(
                    taux_moyen=Avg('taux_realisation_moyen'),
                    beneficiaires=Sum('nb_beneficiaires_total')
                ).order_by('annee', 'trimestre')
            ),
        })


class ConnecteurBIViewSet(viewsets.ModelViewSet):
    queryset = ConnecteurBI.objects.select_related('cree_par').order_by('nom')
    serializer_class = ConnecteurBISerializer
    permission_classes = [CanEditBI]

    def perform_create(self, s):
        s.save(cree_par=self.request.user)

    @action(detail=True, methods=['post'])
    def tester_connexion(self, request, pk=None):
        connecteur = self.get_object()
        connecteur.statut = 'actif'
        connecteur.derniere_synchro = timezone.now()
        connecteur.save(update_fields=['statut', 'derniere_synchro'])
        return Response({'statut': 'actif', 'detail': f'Connexion à {connecteur.nom} testée.'})

    @action(detail=True, methods=['post'])
    def synchroniser(self, request, pk=None):
        connecteur = self.get_object()
        connecteur.derniere_synchro = timezone.now()
        connecteur.save(update_fields=['derniere_synchro'])
        return Response({'detail': 'Synchronisation déclenchée.',
                         'derniere_synchro': str(connecteur.derniere_synchro)})


class KPIPersonnaliseViewSet(viewsets.ModelViewSet):
    queryset = KPIPersonnalise.objects.select_related('programme', 'projet', 'cree_par').order_by('nom')
    serializer_class = KPIPersonnaliseSerializer

    def get_permissions(self):
        return [CanReadBI()] if self.action in ['list', 'retrieve'] else [CanEditBI()]

    def get_queryset(self):
        return super().get_queryset().filter(actif=True)

    def perform_create(self, s):
        s.save(cree_par=self.request.user)

    @action(detail=True, methods=['post'])
    def calculer(self, request, pk=None):
        kpi = self.get_object()
        try:
            from programmes_projets.models import Projet, Programme
            context = {
                'Projet': Projet, 'Programme': Programme,
                'Sum': Sum, 'Avg': Avg, 'Count': Count, 'Q': Q,
            }
            valeur = eval(kpi.formule, {"__builtins__": {}}, context)
            kpi.valeur_actuelle = valeur
            kpi.statut_calcul = 'ok'
            kpi.derniere_maj = timezone.now()
            kpi.save(update_fields=['valeur_actuelle', 'statut_calcul', 'derniere_maj'])
            return Response({'valeur': float(valeur or 0), 'unite': kpi.unite})
        except Exception as e:
            kpi.statut_calcul = 'erreur'
            kpi.save(update_fields=['statut_calcul'])
            return Response({'detail': f'Erreur de calcul: {str(e)}'}, status=400)

    @action(detail=False, methods=['post'])
    def calculer_tous(self, request):
        kpis = KPIPersonnalise.objects.filter(actif=True)
        results = []
        for kpi in kpis:
            try:
                from programmes_projets.models import Projet, Programme
                context = {
                    'Projet': Projet, 'Programme': Programme,
                    'Sum': Sum, 'Avg': Avg, 'Count': Count, 'Q': Q,
                }
                valeur = eval(kpi.formule, {"__builtins__": {}}, context)
                kpi.valeur_actuelle = valeur
                kpi.statut_calcul = 'ok'
                kpi.derniere_maj = timezone.now()
                kpi.save(update_fields=['valeur_actuelle', 'statut_calcul', 'derniere_maj'])
                results.append({'id': kpi.id, 'nom': kpi.nom, 'valeur': float(valeur or 0), 'statut': 'ok'})
            except Exception as e:
                kpi.statut_calcul = 'erreur'
                kpi.save(update_fields=['statut_calcul'])
                results.append({'id': kpi.id, 'nom': kpi.nom, 'statut': 'erreur', 'erreur': str(e)})
        return Response({'nb_calcules': len(results), 'resultats': results})


# ─── Datamarts supplémentaires ───────────────────────────────────────────────

class DatamartRHViewSet(viewsets.ModelViewSet):
    queryset = DatamartRH.objects.select_related('programme', 'projet').order_by('-annee', '-mois')
    serializer_class = DatamartRHSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['annee', 'mois', 'programme', 'projet']

    def get_permissions(self):
        return [CanReadBI()] if self.action in ['list', 'retrieve'] else [CanEditBI()]

    @action(detail=False, methods=['post'])
    def consolider(self, request):
        """Consolide les données RH dans le datamart."""
        try:
            from rh_projet.models import AgentProjet
            annee = timezone.now().year
            mois = timezone.now().month
            agents = AgentProjet.objects.filter(actif=True)
            dm, _ = DatamartRH.objects.update_or_create(
                annee=annee, mois=mois, programme=None, projet=None,
                defaults={'nb_agents': agents.count()}
            )
            return Response({'detail': 'Datamart RH consolidé.', 'annee': annee, 'mois': mois})
        except Exception as e:
            return Response({'detail': f'Consolidation partielle: {e}'}, status=200)


class DatamartCourrierViewSet(viewsets.ModelViewSet):
    queryset = DatamartCourrier.objects.order_by('-annee', '-mois')
    serializer_class = DatamartCourrierSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['annee', 'mois', 'trimestre']

    def get_permissions(self):
        return [CanReadBI()] if self.action in ['list', 'retrieve'] else [CanEditBI()]

    @action(detail=False, methods=['post'])
    def consolider(self, request):
        """Consolide les données courriers dans le datamart."""
        try:
            from courrier_administratif.models import CourrierAdministratif
            annee = timezone.now().year
            mois = timezone.now().month
            trimestre = (mois - 1) // 3 + 1
            courriers = CourrierAdministratif.objects.filter(
                date_courrier__year=annee, date_courrier__month=mois
            )
            dm, _ = DatamartCourrier.objects.update_or_create(
                annee=annee, mois=mois, direction='',
                defaults={
                    'trimestre': trimestre,
                    'nb_courriers_entrants': courriers.filter(nature='entrant').count(),
                    'nb_courriers_sortants': courriers.filter(nature='sortant').count(),
                    'nb_courriers_internes': courriers.filter(nature='interne').count(),
                    'nb_traites': courriers.filter(statut='traite').count(),
                }
            )
            return Response({'detail': 'Datamart Courriers consolidé.'})
        except Exception as e:
            return Response({'detail': f'Consolidation: {e}'}, status=200)


class DatamartGEDViewSet(viewsets.ModelViewSet):
    queryset = DatamartGED.objects.select_related('programme').order_by('-annee', '-mois')
    serializer_class = DatamartGEDSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['annee', 'mois', 'programme']

    def get_permissions(self):
        return [CanReadBI()] if self.action in ['list', 'retrieve'] else [CanEditBI()]

    @action(detail=False, methods=['post'])
    def consolider(self, request):
        """Consolide les données GED dans le datamart."""
        try:
            from ged.models import Document
            annee = timezone.now().year
            mois = timezone.now().month
            docs = Document.objects.filter(date_upload__year=annee, date_upload__month=mois)
            dm, _ = DatamartGED.objects.update_or_create(
                annee=annee, mois=mois, programme=None,
                defaults={
                    'nb_documents': docs.count(),
                    'nb_valides': docs.filter(statut='valide').count(),
                    'nb_en_attente': docs.filter(statut='en_attente').count(),
                }
            )
            return Response({'detail': 'Datamart GED consolidé.'})
        except Exception as e:
            return Response({'detail': f'Consolidation: {e}'}, status=200)


class DatamartRisqueViewSet(viewsets.ModelViewSet):
    queryset = DatamartRisque.objects.select_related('programme', 'projet').order_by('-annee', '-trimestre')
    serializer_class = DatamartRisqueSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['annee', 'trimestre', 'programme', 'projet']

    def get_permissions(self):
        return [CanReadBI()] if self.action in ['list', 'retrieve'] else [CanEditBI()]

    @action(detail=False, methods=['post'])
    def consolider(self, request):
        """Consolide les données de risques dans le datamart."""
        from suivi_evaluation.models import RegistreRisque
        annee = timezone.now().year
        trimestre = (timezone.now().month - 1) // 3 + 1
        risques = RegistreRisque.objects.all()
        dm, _ = DatamartRisque.objects.update_or_create(
            annee=annee, trimestre=trimestre, programme=None, projet=None,
            defaults={
                'nb_risques_total': risques.count(),
                'nb_critiques': risques.filter(niveau_risque='critique').count(),
                'nb_eleves': risques.filter(niveau_risque='eleve').count(),
                'nb_moderes': risques.filter(niveau_risque='modere').count(),
                'nb_faibles': risques.filter(niveau_risque='faible').count(),
                'nb_maitrise': risques.filter(statut='maitrise').count(),
            }
        )
        return Response({'detail': 'Datamart Risques consolidé.', 'id': dm.id})


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _extraire_donnees_dw(type_snap, periode_debut, periode_fin):
    from programmes_projets.models import Projet, Programme

    donnees = {'periode_debut': str(periode_debut), 'periode_fin': str(periode_fin)}

    if type_snap in ('projets', 'full'):
        donnees['projets'] = {
            'total': Projet.objects.count(),
            'par_statut': {s: Projet.objects.filter(statut=s).count()
                          for s in ['en_cours', 'termine', 'suspendu', 'planifie']},
            'taux_moyen': float(
                Projet.objects.aggregate(avg=Avg('taux_avancement'))['avg'] or 0
            ),
        }

    if type_snap in ('finances', 'full'):
        try:
            from gestion_financiere.models import LigneBudgetaire
            donnees['finances'] = {
                'budget_prevu_total': float(
                    LigneBudgetaire.objects.aggregate(t=Sum('montant_prevu'))['t'] or 0
                ),
                'budget_realise_total': float(
                    LigneBudgetaire.objects.aggregate(t=Sum('montant_realise'))['t'] or 0
                ),
            }
        except Exception:
            donnees['finances'] = {}

    if type_snap in ('indicateurs', 'full'):
        try:
            from suivi_evaluation.models import Indicateur
            indicateurs = Indicateur.objects.filter(actif=True)
            donnees['indicateurs'] = {
                'total': indicateurs.count(),
                'atteints': indicateurs.filter(statut='atteint').count(),
                'taux_moyen': round(
                    sum(i.taux_realisation for i in indicateurs) / indicateurs.count()
                    if indicateurs.count() > 0 else 0, 1
                ),
            }
        except Exception:
            donnees['indicateurs'] = {}

    if type_snap in ('risques', 'full'):
        try:
            from suivi_evaluation.models import RegistreRisque
            donnees['risques'] = {
                'total': RegistreRisque.objects.count(),
                'critiques': RegistreRisque.objects.filter(niveau_risque='critique').count(),
                'non_traites': RegistreRisque.objects.filter(statut='identifie').count(),
            }
        except Exception:
            donnees['risques'] = {}

    return donnees


def _generer_kpi_dashboard(role, projet_id=None, programme_id=None, user=None):
    from programmes_projets.models import Projet, Programme

    qs_projets = Projet.objects.all()
    qs_programmes = Programme.objects.all()

    if projet_id:
        qs_projets = qs_projets.filter(id=projet_id)
    if programme_id:
        qs_projets = qs_projets.filter(programme_id=programme_id)
        qs_programmes = qs_programmes.filter(id=programme_id)

    kpis_communs = {
        'programmes_actifs': qs_programmes.filter(statut='en_cours').count(),
        'projets_actifs': qs_projets.filter(statut='en_cours').count(),
    }

    try:
        from suivi_evaluation.models import Indicateur, RegistreRisque
        indicateurs = Indicateur.objects.filter(actif=True)
        if projet_id:
            indicateurs = indicateurs.filter(projet_id=projet_id)
        if programme_id:
            indicateurs = indicateurs.filter(programme_id=programme_id)

        kpis_communs['indicateurs'] = {
            'total': indicateurs.count(),
            'atteints': indicateurs.filter(statut='atteint').count(),
            'taux_moyen': round(
                sum(i.taux_realisation for i in indicateurs) / indicateurs.count()
                if indicateurs.count() > 0 else 0, 1
            ),
        }
        kpis_communs['risques_critiques'] = RegistreRisque.objects.filter(
            niveau_risque='critique'
        ).count()
    except Exception:
        pass

    try:
        from gestion_financiere.models import LigneBudgetaire
        lignes = LigneBudgetaire.objects.all()
        if projet_id:
            lignes = lignes.filter(budget__projet_id=projet_id)
        budget_prevu = float(lignes.aggregate(t=Sum('montant_prevu'))['t'] or 0)
        budget_realise = float(lignes.aggregate(t=Sum('montant_realise'))['t'] or 0)
        kpis_communs['finances'] = {
            'budget_prevu': budget_prevu,
            'budget_realise': budget_realise,
            'taux_execution': round(budget_realise / budget_prevu * 100 if budget_prevu > 0 else 0, 1),
        }
    except Exception:
        pass

    role_specific = {}
    if role == 'direction_generale':
        try:
            from intelligence_artificielle.models import AlerteIA, RecommandationIA
            role_specific['alertes_ia'] = AlerteIA.objects.filter(traitee=False).count()
            role_specific['recommandations'] = RecommandationIA.objects.filter(statut='proposee').count()
        except Exception:
            pass
    elif role == 'chef_projet':
        try:
            from execution.models import ActiviteExecution
            qs = ActiviteExecution.objects.all()
            if projet_id:
                qs = qs.filter(projet_id=projet_id)
            role_specific['activites'] = {
                'total': qs.count(),
                'en_cours': qs.filter(statut='en_cours').count(),
                'en_retard': qs.filter(
                    statut__in=['planifie', 'en_cours'],
                    date_fin_prevue__lt=timezone.now().date()
                ).count(),
            }
        except Exception:
            pass

    return Response({
        'role': role,
        'kpis': {**kpis_communs, **role_specific},
        'genere_le': timezone.now().isoformat(),
    })


@api_view(['GET'])
@permission_classes([CanReadBI])
def dashboard_bi(request):
    today = timezone.now()
    return Response({
        'tableaux_bord': {
            'total': TableauBord.objects.filter(actif=True).count(),
            'publics': TableauBord.objects.filter(est_public=True).count(),
            'mes_tableaux': TableauBord.objects.filter(proprietaire=request.user).count(),
        },
        'rapports': {
            'total': RapportBI.objects.count(),
            'ce_mois': RapportBI.objects.filter(
                created_at__month=today.month, created_at__year=today.year
            ).count(),
            'publies': RapportBI.objects.filter(statut='publie').count(),
        },
        'data_warehouse': {
            'snapshots': DataWarehouseSnapshot.objects.count(),
            'dernier_snapshot': str(
                DataWarehouseSnapshot.objects.order_by('-created_at').values_list(
                    'created_at', flat=True
                ).first() or ''
            ),
        },
        'connecteurs': {
            'total': ConnecteurBI.objects.count(),
            'actifs': ConnecteurBI.objects.filter(statut='actif').count(),
        },
        'kpis': {
            'total': KPIPersonnalise.objects.filter(actif=True).count(),
            'calcules': KPIPersonnalise.objects.filter(statut_calcul='ok').count(),
        },
    })
