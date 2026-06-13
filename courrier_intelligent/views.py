from django.db import models as db_models
import logging
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import CompteEmail, SignatureEmail, TemplateReponse, Email, PieceJointeEmail, ActionEmail, EtiquetteEmail, LienEmail, RegleClassification
from .serializers import (
    CompteEmailSerializer, SignatureEmailSerializer, TemplateReponseSerializer,
    EmailListSerializer, EmailDetailSerializer,
    EmailCreateSerializer, PieceJointeSerializer, ActionEmailSerializer, EtiquetteSerializer,
    LienEmailSerializer, RegleClassificationSerializer,
)
from .filters import EmailFilter

CanReadCI = HasModulePermission.for_module('courrier_intelligent', 'peut_lire')
CanEditCI = HasModulePermission.for_module('courrier_intelligent', 'peut_modifier')


class CompteEmailViewSet(viewsets.ModelViewSet):
    serializer_class = CompteEmailSerializer
    permission_classes = [CanReadCI]

    def get_queryset(self):
        return CompteEmail.objects.filter(utilisateur=self.request.user)

    def perform_create(self, s):
        s.save(utilisateur=self.request.user)

    @action(detail=False, methods=['get'])
    def detecter_config(self, request):
        """Auto-détecte SMTP/IMAP pour un email donné."""
        from .services import detect_smtp_config, detect_imap_config, detect_pop3_config
        email_addr = request.query_params.get('email', '')
        if not email_addr:
            return Response({'detail': 'Paramètre email requis.'}, status=400)
        return Response({
            'smtp': detect_smtp_config(email_addr),
            'imap': detect_imap_config(email_addr),
            'pop3': detect_pop3_config(email_addr),
        })

    @action(detail=True, methods=['post'])
    def tester_connexion(self, request, pk=None):
        """Teste réellement la connexion SMTP et IMAP."""
        from .services import tester_connexion
        compte = self.get_object()
        resultat = tester_connexion(compte)
        if resultat['success']:
            compte.statut = 'actif'
            compte.save(update_fields=['statut'])
        else:
            compte.statut = 'erreur'
            compte.save(update_fields=['statut'])
        return Response(resultat)

    @action(detail=True, methods=['post'])
    def synchroniser(self, request, pk=None):
        """Synchronise les emails via Celery (non-bloquant) ou directement en fallback."""
        compte = self.get_object()
        try:
            from .tasks import sync_compte_email
            sync_compte_email.delay(compte.id)
            return Response({'success': True, 'message': 'Synchronisation lancée en arrière-plan.'})
        except Exception:
            from .services import sync_compte
            resultat = sync_compte(compte)
            return Response(resultat)

    @action(detail=False, methods=['post'])
    def synchroniser_tous(self, request):
        """Lance la synchronisation de tous les comptes actifs via Celery."""
        try:
            from .tasks import sync_tous_comptes
            task = sync_tous_comptes.delay()
            return Response({'success': True, 'task_id': task.id, 'message': 'Synchronisation globale lancée.'})
        except Exception as exc:
            return Response({'success': False, 'message': str(exc)}, status=500)

    @action(detail=True, methods=['post'])
    def envoyer_email(self, request, pk=None):
        """Envoie un email via SMTP avec le compte configuré."""
        from .services import envoyer_email
        compte = self.get_object()
        email_id = request.data.get('email_id')
        if not email_id:
            return Response({'detail': 'email_id requis.'}, status=400)
        try:
            email_obj = Email.objects.get(id=email_id)
        except Email.DoesNotExist:
            return Response({'detail': 'Email introuvable.'}, status=404)
        resultat = envoyer_email(compte, email_obj)
        if resultat['success']:
            email_obj.statut = 'repondu'
            email_obj.date_envoi = timezone.now()
            email_obj.save(update_fields=['statut', 'date_envoi'])
        return Response(resultat)


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.select_related(
        'compte', 'projet', 'programme', 'cree_par'
    ).prefetch_related('pieces_jointes', 'action_emails', 'etiquettes').order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EmailFilter
    search_fields = ['sujet', 'corps_texte', 'expediteur', 'expediteur_email', 'resume_ia']
    ordering_fields = ['date_reception', 'priorite', 'score_urgence']
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        return [CanReadCI()] if self.action in ['list', 'retrieve'] else [CanEditCI()]

    def get_serializer_class(self):
        if self.action == 'list':
            return EmailListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return EmailCreateSerializer
        return EmailDetailSerializer

    def perform_create(self, s):
        import uuid
        data = s.validated_data
        en_reponse_a = data.get('en_reponse_a')

        # Propagate or generate thread_id to link the reply chain
        thread_id = ''
        if en_reponse_a:
            if en_reponse_a.thread_id:
                thread_id = en_reponse_a.thread_id
            else:
                thread_id = str(uuid.uuid4())
                en_reponse_a.thread_id = thread_id
                en_reponse_a.save(update_fields=['thread_id'])

        s.save(
            cree_par=self.request.user,
            date_envoi=timezone.now() if data.get('direction') == 'sortant' else None,
            thread_id=thread_id,
        )

    @action(detail=True, methods=['post'])
    def envoyer(self, request, pk=None):
        """Envoie l'email via SMTP (appelé après upload des PJ)."""
        from .services import envoyer_email
        email = self.get_object()
        compte = (
            CompteEmail.objects.filter(utilisateur=request.user, est_principal=True, statut='actif').first()
            or CompteEmail.objects.filter(utilisateur=request.user, statut='actif').first()
        )
        if not compte:
            return Response({'success': False, 'message': 'Aucun compte email actif configuré.'}, status=400)

        def _send():
            from .models import Email as E
            try:
                result = envoyer_email(compte, email)
                if result.get('success'):
                    E.objects.filter(id=email.id).update(statut='repondu' if email.en_reponse_a_id else email.statut)
            except Exception as exc:
                logger.warning(f"SMTP send failed: {exc}")

        import threading
        threading.Thread(target=_send, daemon=True).start()
        return Response({'success': True, 'message': 'Envoi en cours…'})

    @action(detail=True, methods=['post'])
    def marquer_lu(self, request, pk=None):
        email = self.get_object()
        email.marquer_lu()
        return Response({'statut': email.statut, 'lu': email.est_lu})

    @action(detail=True, methods=['post'])
    def marquer_non_lu(self, request, pk=None):
        email = self.get_object()
        email.est_lu = False
        email.statut = 'non_lu'
        email.save(update_fields=['est_lu', 'statut'])
        return Response({'statut': email.statut})

    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        email = self.get_object()
        email.statut = 'archive'
        email.save(update_fields=['statut'])
        return Response({'statut': 'archive'})

    @action(detail=True, methods=['post'])
    def analyse_ia(self, request, pk=None):
        email = self.get_object()
        corps = email.corps_texte or ''
        mots_urgents = ['urgent', 'important', 'délai', 'deadline', 'immédiat']
        score = min(sum(2 for m in mots_urgents if m.lower() in corps.lower()) * 20, 100)
        actions = [
            {'texte': ligne.strip(), 'type': 'action'}
            for ligne in corps.split('\n')
            if any(k in ligne.lower() for k in ['envoyer', 'préparer', 'valider', 'organiser', 'soumettre'])
        ][:5]
        email.resume_ia = f"[IA] {email.sujet}. {corps[:200]}..."
        email.actions_detectees = actions
        email.score_urgence = score
        email.traite_par_ia = True
        email.categorie_ia = f"Projet: {email.projet}" if email.projet else "Non classifié"
        email.save(update_fields=['resume_ia', 'actions_detectees', 'score_urgence',
                                   'traite_par_ia', 'categorie_ia'])
        return Response({
            'resume': email.resume_ia, 'nb_actions': len(actions),
            'score_urgence': score, 'categorie': email.categorie_ia,
        })

    @action(detail=True, methods=['post'])
    def classifier(self, request, pk=None):
        email = self.get_object()
        if request.data.get('projet'):
            email.projet_id = request.data['projet']
        if request.data.get('programme'):
            email.programme_id = request.data['programme']
        email.save()
        return Response(EmailDetailSerializer(email).data)

    @action(detail=True, methods=['post'])
    def generer_action(self, request, pk=None):
        email = self.get_object()
        a = ActionEmail.objects.create(
            email=email,
            type_action=request.data.get('type_action', 'tache'),
            description=request.data.get('description', ''),
            responsable_id=request.data.get('responsable'),
            echeance=request.data.get('echeance'),
            detectee_par_ia=False,
        )
        return Response(ActionEmailSerializer(a).data, status=201)

    @action(detail=True, methods=['post'])
    def archiver_ged(self, request, pk=None):
        email = self.get_object()
        if email.archive_ged:
            return Response({'detail': 'Email déjà archivé dans la GED.'})
        email.archive_ged = True
        email.save(update_fields=['archive_ged'])
        return Response({'detail': 'Email archivé dans la GED.'})

    @action(detail=True, methods=['post'])
    def assigner_etiquette(self, request, pk=None):
        """Ajouter ou retirer une étiquette d'un email."""
        email = self.get_object()
        etiquette_id = request.data.get('etiquette_id')
        action_type = request.data.get('action', 'add')
        try:
            etiquette = EtiquetteEmail.objects.get(id=etiquette_id)
            if action_type == 'remove':
                etiquette.emails.remove(email)
            else:
                etiquette.emails.add(email)
            return Response(EtiquetteSerializer(email.etiquettes.all(), many=True).data)
        except EtiquetteEmail.DoesNotExist:
            return Response({'detail': 'Étiquette introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def non_lus(self, request):
        qs = Email.objects.filter(est_lu=False, direction='entrant').order_by('-created_at')[:50]
        return Response(EmailListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now()
        qs = Email.objects.all()
        return Response({
            'total': qs.count(),
            'non_lus': qs.filter(est_lu=False, direction='entrant').count(),
            'urgents': qs.filter(score_urgence__gte=80).count(),
            'ce_mois': qs.filter(created_at__month=today.month, created_at__year=today.year).count(),
            'traites_ia': qs.filter(traite_par_ia=True).count(),
        })


class LienEmailViewSet(viewsets.ModelViewSet):
    queryset = LienEmail.objects.select_related('email', 'cree_par').order_by('-created_at')
    serializer_class = LienEmailSerializer
    permission_classes = [CanReadCI]

    def get_queryset(self):
        qs = super().get_queryset()
        email_id = self.request.query_params.get('email')
        return qs.filter(email_id=email_id) if email_id else qs

    def perform_create(self, s):
        s.save(cree_par=self.request.user)


class PieceJointeViewSet(viewsets.ModelViewSet):
    queryset = PieceJointeEmail.objects.order_by('-created_at')
    serializer_class = PieceJointeSerializer
    permission_classes = [CanReadCI]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        e = self.request.query_params.get('email')
        return qs.filter(email_id=e) if e else qs


class ActionEmailViewSet(viewsets.ModelViewSet):
    queryset = ActionEmail.objects.order_by('echeance')
    serializer_class = ActionEmailSerializer
    permission_classes = [CanEditCI]

    def get_queryset(self):
        qs = super().get_queryset()
        e = self.request.query_params.get('email')
        return qs.filter(email_id=e) if e else qs

    @action(detail=True, methods=['post'])
    def convertir(self, request, pk=None):
        a = self.get_object()
        a.statut = 'convertie'
        a.objet_genere_type = request.data.get('type', '')
        a.objet_genere_id = request.data.get('id')
        a.save(update_fields=['statut', 'objet_genere_type', 'objet_genere_id'])
        return Response(ActionEmailSerializer(a).data)


class EtiquetteViewSet(viewsets.ModelViewSet):
    serializer_class = EtiquetteSerializer
    permission_classes = [CanReadCI]

    def get_queryset(self):
        return EtiquetteEmail.objects.filter(utilisateur=self.request.user)

    def perform_create(self, s):
        s.save(utilisateur=self.request.user)


class RegleClassificationViewSet(viewsets.ModelViewSet):
    serializer_class = RegleClassificationSerializer
    permission_classes = [CanEditCI]

    def get_queryset(self):
        return RegleClassification.objects.order_by('priorite', 'nom')

    def perform_create(self, s):
        s.save(cree_par=self.request.user)


@api_view(['GET'])
@permission_classes([CanReadCI])
def dashboard_courrier_intelligent(request):
    today = timezone.now()
    qs = Email.objects.all()
    return Response({
        'total': qs.count(),
        'entrants': qs.filter(direction='entrant').count(),
        'sortants': qs.filter(direction='sortant').count(),
        'non_lus': qs.filter(est_lu=False, direction='entrant').count(),
        'urgents': qs.filter(score_urgence__gte=80).count(),
        'traites_ia': qs.filter(traite_par_ia=True).count(),
        'ce_mois': qs.filter(created_at__month=today.month, created_at__year=today.year).count(),
        'par_projet': list(
            qs.filter(projet__isnull=False).values('projet__titre').annotate(nb=Count('id'))[:10]
        ),
    })


class SignatureEmailViewSet(viewsets.ModelViewSet):
    serializer_class = SignatureEmailSerializer
    permission_classes = [CanReadCI]

    def get_queryset(self):
        return SignatureEmail.objects.filter(utilisateur=self.request.user).order_by('-est_principale', 'nom')

    def perform_create(self, s):
        s.save(utilisateur=self.request.user)

    @action(detail=True, methods=['post'])
    def definir_principale(self, request, pk=None):
        sig = self.get_object()
        sig.est_principale = True
        sig.save()
        return Response(SignatureEmailSerializer(sig).data)


class TemplateReponseViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateReponseSerializer

    def get_permissions(self):
        return [CanReadCI()] if self.action in ['list', 'retrieve'] else [CanEditCI()]

    def get_queryset(self):
        user = self.request.user
        return TemplateReponse.objects.filter(
            actif=True
        ).filter(
            models.Q(est_global=True) | models.Q(cree_par=user)
        ).order_by('type_template', 'titre')

    def perform_create(self, s):
        s.save(cree_par=self.request.user)

    @action(detail=True, methods=['post'])
    def utiliser(self, request, pk=None):
        tpl = self.get_object()
        tpl.nb_utilisations += 1
        tpl.save(update_fields=['nb_utilisations'])
        return Response(TemplateReponseSerializer(tpl).data)
