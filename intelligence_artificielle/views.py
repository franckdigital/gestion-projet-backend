from django.db.models import Count, Q, Avg
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import (
    ConversationIA, MessageIA,
    GenerationDocument,
    ModeleIA, AnalyseIAPredictive, AlerteIA, RecommandationIA,
    JournalIA,
)
from .serializers import (
    ConversationIAListSerializer, ConversationIADetailSerializer, MessageIASerializer,
    GenerationDocumentListSerializer, GenerationDocumentDetailSerializer,
    ModeleIASerializer,
    AnalyseIAPredictiveListSerializer, AnalyseIAPredictiveDetailSerializer,
    AlerteIASerializer, RecommandationIASerializer,
    JournalIASerializer,
)
from .filters import (
    ConversationIAFilter, GenerationDocumentFilter,
    AnalyseIAPredictiveFilter, AlerteIAFilter, JournalIAFilter,
)

CanReadIA = HasModulePermission.for_module('intelligence_artificielle', 'peut_lire')
CanEditIA = HasModulePermission.for_module('intelligence_artificielle', 'peut_modifier')


# ─── M31 : Assistant IA ───────────────────────────────────────────────────────

class ConversationIAViewSet(viewsets.ModelViewSet):
    queryset = ConversationIA.objects.select_related(
        'utilisateur', 'projet', 'programme'
    ).prefetch_related('messages').order_by('-updated_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ConversationIAFilter
    search_fields = ['titre']
    ordering_fields = ['created_at', 'updated_at']

    def get_permissions(self):
        return [CanReadIA()] if self.action in ['list', 'retrieve'] else [CanEditIA()]

    def get_serializer_class(self):
        return ConversationIAListSerializer if self.action == 'list' else ConversationIADetailSerializer

    def get_queryset(self):
        return super().get_queryset().filter(utilisateur=self.request.user)

    def perform_create(self, s):
        s.save(utilisateur=self.request.user)

    @action(detail=True, methods=['post'])
    def envoyer_message(self, request, pk=None):
        conv = self.get_object()
        contenu_user = request.data.get('contenu', '').strip()
        if not contenu_user:
            return Response({'detail': 'Le message ne peut pas être vide.'}, status=400)

        msg_user = MessageIA.objects.create(
            conversation=conv,
            role='user',
            contenu=contenu_user,
        )

        reponse_ia = self._generer_reponse(conv, contenu_user)
        msg_ia = MessageIA.objects.create(
            conversation=conv,
            role='assistant',
            contenu=reponse_ia,
            tokens_utilises=len(reponse_ia.split()),
            duree_traitement_ms=150,
        )

        conv.updated_at = timezone.now()
        conv.save(update_fields=['updated_at'])

        JournalIA.objects.create(
            type_action='conversation',
            utilisateur=request.user,
            objet_type='ConversationIA',
            objet_id=conv.id,
            description=f"Message envoyé dans la conversation {conv.id}",
            parametres_entree={'message': contenu_user},
            resultats_sortie={'reponse': reponse_ia[:200]},
            tokens_utilises=msg_ia.tokens_utilises,
            succes=True,
        )

        return Response({
            'message_user': MessageIASerializer(msg_user).data,
            'message_ia': MessageIASerializer(msg_ia).data,
        })

    def _generer_reponse(self, conv, question):
        q = question.lower()
        from programmes_projets.models import Projet, Programme

        if any(k in q for k in ['retard', 'en retard', 'delay']):
            projets_retard = Projet.objects.filter(statut='en_retard').count()
            return (f"Selon les données actuelles, {projets_retard} projet(s) sont en retard. "
                    f"Je vous recommande de consulter le tableau de bord Exécution pour plus de détails.")

        if any(k in q for k in ['actif', 'actifs', 'en cours']):
            p = Programme.objects.filter(statut='en_cours').count()
            prj = Projet.objects.filter(statut='en_cours').count()
            return f"Il y a actuellement {p} programme(s) et {prj} projet(s) actifs."

        if any(k in q for k in ['budget', 'financ', 'dépense']):
            return ("Je peux analyser les données budgétaires disponibles. "
                    "Veuillez préciser le programme ou projet concerné.")

        if any(k in q for k in ['indicateur', 'résultat', 'performance']):
            return ("Pour analyser les indicateurs, consultez le module Suivi & Évaluation. "
                    "Je peux vous aider à interpréter les données si vous me précisez le programme.")

        return (f"Bonjour ! Je suis l'assistant IA de votre ERP de gestion de projets. "
                f"Je peux vous aider sur : les projets, programmes, budgets, indicateurs, "
                f"courriers et documents. Comment puis-je vous aider ?")

    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        conv = self.get_object()
        conv.archivee = True
        conv.save(update_fields=['archivee'])
        return Response({'archivee': True})

    @action(detail=False, methods=['get'])
    def mes_conversations(self, request):
        qs = ConversationIA.objects.filter(
            utilisateur=request.user, archivee=False
        ).order_by('-updated_at')[:20]
        return Response(ConversationIAListSerializer(qs, many=True).data)

    @action(detail=False, methods=['post'])
    def recherche_intelligente(self, request):
        """Recherche transversale dans les modules ERP."""
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'detail': 'query requis.'}, status=400)

        results = {}
        from programmes_projets.models import Projet, Programme

        projets = Projet.objects.filter(
            Q(titre__icontains=query) | Q(description__icontains=query)
        )[:5]
        results['projets'] = [{'id': p.id, 'titre': p.titre, 'statut': p.statut} for p in projets]

        programmes = Programme.objects.filter(
            Q(intitule__icontains=query) | Q(description__icontains=query)
        )[:5]
        results['programmes'] = [{'id': p.id, 'intitule': p.intitule, 'statut': p.statut}
                                  for p in programmes]

        from ged.models import Document
        docs = Document.objects.filter(
            Q(titre__icontains=query) | Q(mots_cles__icontains=query)
        )[:5]
        results['documents'] = [{'id': d.id, 'titre': d.titre, 'type': d.type_document}
                                 for d in docs]

        JournalIA.objects.create(
            type_action='classification',
            utilisateur=request.user,
            description=f"Recherche intelligente: {query}",
            parametres_entree={'query': query},
            resultats_sortie={k: len(v) for k, v in results.items()},
            succes=True,
        )

        return Response({'query': query, 'resultats': results,
                         'total': sum(len(v) for v in results.values())})


class MessageIAViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MessageIA.objects.order_by('created_at')
    serializer_class = MessageIASerializer
    permission_classes = [CanReadIA]

    def get_queryset(self):
        qs = super().get_queryset()
        conv = self.request.query_params.get('conversation')
        return qs.filter(conversation_id=conv) if conv else qs.filter(
            conversation__utilisateur=self.request.user
        )


# ─── M32 : Génération documentaire IA ────────────────────────────────────────

class GenerationDocumentViewSet(viewsets.ModelViewSet):
    queryset = GenerationDocument.objects.select_related(
        'demande_par', 'valide_par', 'projet', 'programme', 'document_ged'
    ).order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = GenerationDocumentFilter
    search_fields = ['titre', 'instructions']
    ordering_fields = ['created_at', 'completed_at', 'statut']

    def get_permissions(self):
        return [CanReadIA()] if self.action in ['list', 'retrieve'] else [CanEditIA()]

    def get_serializer_class(self):
        return GenerationDocumentListSerializer if self.action == 'list' else GenerationDocumentDetailSerializer

    def perform_create(self, s):
        gen = s.save(demande_par=self.request.user)
        gen.executer()
        JournalIA.objects.create(
            type_action='generation',
            utilisateur=self.request.user,
            objet_type='GenerationDocument',
            objet_id=gen.id,
            description=f"Génération: {gen.titre}",
            parametres_entree={'type': gen.type_document, 'mode': gen.mode},
            resultats_sortie={'statut': gen.statut, 'tokens': gen.tokens_utilises},
            tokens_utilises=gen.tokens_utilises,
            succes=gen.statut == 'complete',
        )

    @action(detail=True, methods=['post'])
    def regenerer(self, request, pk=None):
        gen = self.get_object()
        gen.statut = 'en_attente'
        gen.contenu_genere = ''
        gen.save(update_fields=['statut', 'contenu_genere'])
        gen.executer()
        return Response(GenerationDocumentDetailSerializer(gen).data)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        gen = self.get_object()
        gen.statut = 'valide'
        gen.valide_par = request.user
        gen.date_validation = timezone.now()
        gen.save(update_fields=['statut', 'valide_par', 'date_validation'])
        return Response(GenerationDocumentDetailSerializer(gen).data)

    @action(detail=True, methods=['post'])
    def exporter_ged(self, request, pk=None):
        gen = self.get_object()
        if gen.statut not in ('complete', 'valide'):
            return Response({'detail': 'La génération doit être complète pour être exportée.'}, status=400)
        from ged.models import Document
        doc = Document.objects.create(
            titre=gen.titre,
            description=gen.instructions,
            type_document='rapport',
            contenu_html=gen.contenu_genere,
            auteur=request.user,
            statut='brouillon',
        )
        gen.document_ged = doc
        gen.save(update_fields=['document_ged'])
        return Response({'detail': 'Document exporté vers la GED.', 'document_id': doc.id})

    @action(detail=False, methods=['get'])
    def types_disponibles(self, request):
        return Response([{'code': c, 'label': l} for c, l in GenerationDocument.TYPE_CHOICES])


# ─── M33 : IA Prédictive ──────────────────────────────────────────────────────

class ModeleIAViewSet(viewsets.ModelViewSet):
    queryset = ModeleIA.objects.order_by('type_modele', 'nom')
    serializer_class = ModeleIASerializer
    permission_classes = [CanReadIA]

    @action(detail=True, methods=['post'])
    def executer(self, request, pk=None):
        modele = self.get_object()
        modele.nb_executions += 1
        modele.derniere_execution = timezone.now()
        modele.save(update_fields=['nb_executions', 'derniere_execution'])
        return Response({'detail': f'Modèle {modele.nom} exécuté.', 'nb_executions': modele.nb_executions})


class AnalyseIAPredictiveViewSet(viewsets.ModelViewSet):
    queryset = AnalyseIAPredictive.objects.select_related(
        'modele', 'demande_par', 'projet', 'programme'
    ).prefetch_related('alertes', 'recommandations').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AnalyseIAPredictiveFilter
    ordering_fields = ['created_at', 'completed_at', 'score_confiance']

    def get_permissions(self):
        return [CanReadIA()] if self.action in ['list', 'retrieve'] else [CanEditIA()]

    def get_serializer_class(self):
        return AnalyseIAPredictiveListSerializer if self.action == 'list' else AnalyseIAPredictiveDetailSerializer

    def perform_create(self, s):
        analyse = s.save(demande_par=self.request.user)
        self._executer_analyse(analyse)

    def _executer_analyse(self, analyse):
        try:
            analyse.statut = 'en_cours'
            analyse.save(update_fields=['statut'])

            previsions = []
            anomalies = []
            recommandations_text = ''

            if analyse.type_analyse == 'prevision_budget':
                from gestion_financiere.models import LigneBudgetaire
                lignes = LigneBudgetaire.objects.filter(
                    budget__projet=analyse.projet
                ) if analyse.projet else LigneBudgetaire.objects.none()
                total = float(lignes.aggregate(
                    t=__import__('django.db.models', fromlist=['Sum']).Sum('montant_prevu')
                ).get('t') or 0)
                consomme = float(lignes.aggregate(
                    t=__import__('django.db.models', fromlist=['Sum']).Sum('montant_realise')
                ).get('t') or 0)
                taux = (consomme / total * 100) if total > 0 else 0
                previsions = [{'type': 'budget', 'taux_consommation': round(taux, 2),
                               'montant_prevu': total, 'montant_consomme': consomme}]
                if taux > 85:
                    anomalies.append({'type': 'depassement_imminent', 'niveau': 'critique',
                                      'message': f'Consommation à {round(taux, 1)}%'})
                    AlerteIA.objects.create(
                        analyse=analyse,
                        type_alerte='depassement_budget',
                        niveau='critique',
                        titre='Risque de dépassement budgétaire',
                        message=f'Le budget est consommé à {round(taux, 1)}%. Risque de dépassement.',
                        destinataire=analyse.demande_par,
                    )
                recommandations_text = (
                    f"Taux de consommation: {round(taux, 1)}%. "
                    + ("Action corrective recommandée." if taux > 85 else "Consommation normale.")
                )

            elif analyse.type_analyse == 'detection_retard':
                from execution.models import ActiviteExecution
                activites_retard = ActiviteExecution.objects.filter(
                    statut__in=['planifie', 'en_cours'],
                    date_fin_prevue__lt=timezone.now().date()
                )
                if analyse.projet:
                    activites_retard = activites_retard.filter(projet=analyse.projet)
                nb = activites_retard.count()
                previsions = [{'activites_en_retard': nb,
                               'details': list(activites_retard.values('titre', 'date_fin_prevue')[:5])}]
                if nb > 0:
                    AlerteIA.objects.create(
                        analyse=analyse,
                        type_alerte='retard_prevu',
                        niveau='critique' if nb > 5 else 'warning',
                        titre=f'{nb} activité(s) en retard détectée(s)',
                        message=f'{nb} activités ont dépassé leur date de fin prévue.',
                        destinataire=analyse.demande_par,
                    )
                    RecommandationIA.objects.create(
                        analyse=analyse,
                        type_recommandation='revision_calendrier',
                        titre='Révision du calendrier recommandée',
                        description=f'{nb} activités en retard nécessitent une révision du planning.',
                        priorite=3 if nb > 3 else 2,
                        projet=analyse.projet,
                    )
                recommandations_text = f"{nb} retard(s) détecté(s). {'Action urgente requise.' if nb > 0 else 'Aucun retard.'}"

            else:
                previsions = [{'message': f"Analyse {analyse.get_type_analyse_display()} simulée."}]
                recommandations_text = "Analyse effectuée avec succès."

            analyse.previsions = previsions
            analyse.anomalies = anomalies
            analyse.suggestions_ia = recommandations_text
            analyse.score_confiance = 82
            analyse.statut = 'complete'
            analyse.completed_at = timezone.now()
            analyse.save()

            JournalIA.objects.create(
                type_action='analyse_predictive',
                utilisateur=analyse.demande_par,
                objet_type='AnalyseIAPredictive',
                objet_id=analyse.id,
                description=f"Analyse prédictive: {analyse.get_type_analyse_display()}",
                resultats_sortie={'nb_previsions': len(previsions), 'nb_anomalies': len(anomalies)},
                succes=True,
            )

        except Exception as e:
            analyse.statut = 'erreur'
            analyse.save(update_fields=['statut'])

    @action(detail=False, methods=['post'])
    def analyser_projet(self, request):
        projet_id = request.data.get('projet')
        if not projet_id:
            return Response({'detail': 'projet requis.'}, status=400)

        analyse = AnalyseIAPredictive.objects.create(
            type_analyse='detection_retard',
            projet_id=projet_id,
            demande_par=request.user,
        )
        self._executer_analyse(analyse)
        return Response(AnalyseIAPredictiveDetailSerializer(analyse).data, status=201)

    @action(detail=False, methods=['get'])
    def synthese_executive(self, request):
        """Synthèse exécutive IA pour la direction."""
        from programmes_projets.models import Projet, Programme
        from suivi_evaluation.models import RegistreRisque

        projets = Projet.objects.all()
        programmes = Programme.objects.all()
        risques_critiques = RegistreRisque.objects.filter(niveau_risque='critique').count()
        alertes_non_traitees = AlerteIA.objects.filter(traitee=False).count()

        return Response({
            'resume': {
                'programmes_actifs': programmes.filter(statut='en_cours').count(),
                'projets_actifs': projets.filter(statut='en_cours').count(),
                'projets_critiques': projets.filter(statut='en_retard').count(),
                'risques_critiques': risques_critiques,
                'alertes_ia': alertes_non_traitees,
            },
            'recommandations_prioritaires': list(
                RecommandationIA.objects.filter(
                    statut='proposee', priorite__gte=3
                ).values('titre', 'type_recommandation', 'priorite')[:5]
            ),
            'tendances': {
                'analyses_cette_semaine': AnalyseIAPredictive.objects.filter(
                    created_at__gte=timezone.now() - __import__('datetime').timedelta(days=7)
                ).count(),
                'documents_generes': GenerationDocument.objects.filter(
                    statut='complete',
                    created_at__gte=timezone.now() - __import__('datetime').timedelta(days=30)
                ).count(),
            },
            'genere_le': timezone.now().isoformat(),
        })


class AlerteIAViewSet(viewsets.ModelViewSet):
    queryset = AlerteIA.objects.select_related('analyse', 'destinataire').order_by('-date_alerte')
    serializer_class = AlerteIASerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = AlerteIAFilter
    search_fields = ['titre', 'message']

    def get_permissions(self):
        return [CanReadIA()] if self.action in ['list', 'retrieve'] else [CanEditIA()]

    def get_queryset(self):
        return super().get_queryset().filter(
            Q(destinataire=self.request.user) | Q(destinataire__isnull=True)
        )

    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        alerte = self.get_object()
        alerte.lue = True
        alerte.save(update_fields=['lue'])
        return Response({'lue': True})

    @action(detail=True, methods=['post'])
    def marquer_traitee(self, request, pk=None):
        alerte = self.get_object()
        alerte.traitee = True
        alerte.lue = True
        alerte.date_traitement = timezone.now()
        alerte.save(update_fields=['traitee', 'lue', 'date_traitement'])
        return Response({'traitee': True})

    @action(detail=False, methods=['post'])
    def tout_marquer_lue(self, request):
        count = AlerteIA.objects.filter(
            destinataire=request.user, lue=False
        ).update(lue=True)
        return Response({'marquees': count})


class RecommandationIAViewSet(viewsets.ModelViewSet):
    queryset = RecommandationIA.objects.select_related(
        'analyse', 'projet', 'programme', 'acceptee_par'
    ).order_by('-priorite', '-created_at')
    serializer_class = RecommandationIASerializer
    permission_classes = [CanReadIA]

    @action(detail=True, methods=['post'])
    def accepter(self, request, pk=None):
        rec = self.get_object()
        rec.statut = 'acceptee'
        rec.acceptee_par = request.user
        rec.date_decision = timezone.now()
        rec.save(update_fields=['statut', 'acceptee_par', 'date_decision'])
        return Response(RecommandationIASerializer(rec).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        rec = self.get_object()
        rec.statut = 'rejetee'
        rec.acceptee_par = request.user
        rec.date_decision = timezone.now()
        rec.motif_rejet = request.data.get('motif', '')
        rec.save(update_fields=['statut', 'acceptee_par', 'date_decision', 'motif_rejet'])
        return Response(RecommandationIASerializer(rec).data)


class JournalIAViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JournalIA.objects.select_related('utilisateur').order_by('-created_at')
    serializer_class = JournalIASerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JournalIAFilter
    search_fields = ['description', 'message_erreur']
    permission_classes = [CanReadIA]


@api_view(['GET'])
@permission_classes([CanReadIA])
def dashboard_ia(request):
    today = timezone.now()
    return Response({
        'assistant': {
            'conversations_actives': ConversationIA.objects.filter(
                archivee=False, utilisateur=request.user
            ).count(),
            'messages_total': MessageIA.objects.filter(
                conversation__utilisateur=request.user
            ).count(),
        },
        'generation': {
            'total': GenerationDocument.objects.count(),
            'cette_semaine': GenerationDocument.objects.filter(
                created_at__gte=today - __import__('datetime').timedelta(days=7)
            ).count(),
            'par_type': {t: GenerationDocument.objects.filter(type_document=t).count()
                        for t, _ in GenerationDocument.TYPE_CHOICES[:5]},
        },
        'predictif': {
            'analyses_total': AnalyseIAPredictive.objects.count(),
            'alertes_non_traitees': AlerteIA.objects.filter(traitee=False).count(),
            'alertes_critiques': AlerteIA.objects.filter(
                niveau='critique', traitee=False
            ).count(),
            'recommandations_en_attente': RecommandationIA.objects.filter(statut='proposee').count(),
        },
        'journal': {
            'total_actions': JournalIA.objects.count(),
            'erreurs': JournalIA.objects.filter(succes=False).count(),
            'tokens_utilises_total': JournalIA.objects.aggregate(
                t=__import__('django.db.models', fromlist=['Sum']).Sum('tokens_utilises')
            ).get('t') or 0,
        },
    })
