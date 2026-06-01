from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import HasModulePermission
from .models import (
    Canal, MembreCanal, Message, LectureMessage,
    Notification, PreferenceNotification, ActiviteRecente, GroupeTravail,
    Evenement, ParticipantEvenement, DepenseEvenement,
)
from .serializers import (
    CanalListSerializer, CanalDetailSerializer, MembreCanalSerializer,
    MessageSerializer, NotificationSerializer, PreferenceNotificationSerializer,
    ActiviteRecenteSerializer, GroupeTravailSerializer,
    EvenementListSerializer, EvenementDetailSerializer,
    ParticipantEvenementSerializer, DepenseEvenementSerializer,
)

CanReadCollab = HasModulePermission.for_module('collaboration', 'peut_lire')
CanEditCollab = HasModulePermission.for_module('collaboration', 'peut_modifier')


# ─── Messagerie ───────────────────────────────────────────────────────────────

class CanalViewSet(viewsets.ModelViewSet):
    queryset = Canal.objects.prefetch_related('memberships', 'messages').filter(archive=False)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['nom', 'description']
    permission_classes = [CanReadCollab]

    def get_serializer_class(self):
        return CanalListSerializer if self.action == 'list' else CanalDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('mes_canaux'):
            qs = qs.filter(memberships__utilisateur=self.request.user)
        projet = self.request.query_params.get('projet')
        if projet:
            qs = qs.filter(projet_id=projet)
        return qs

    def perform_create(self, s):
        canal = s.save(cree_par=self.request.user)
        MembreCanal.objects.create(canal=canal, utilisateur=self.request.user, role='admin')

    @action(detail=True, methods=['post'])
    def rejoindre(self, request, pk=None):
        canal = self.get_object()
        if canal.est_prive:
            return Response({'detail': 'Canal privé — invitation requise.'}, status=403)
        mb, created = MembreCanal.objects.get_or_create(
            canal=canal, utilisateur=request.user,
            defaults={'role': 'membre'}
        )
        return Response(MembreCanalSerializer(mb).data, status=201 if created else 200)

    @action(detail=True, methods=['post'])
    def quitter(self, request, pk=None):
        canal = self.get_object()
        MembreCanal.objects.filter(canal=canal, utilisateur=request.user).delete()
        return Response({'detail': 'Canal quitté.'})

    @action(detail=True, methods=['post'])
    def inviter(self, request, pk=None):
        canal = self.get_object()
        user_ids = request.data.get('user_ids', [])
        created = 0
        for uid in user_ids:
            _, ok = MembreCanal.objects.get_or_create(
                canal=canal, utilisateur_id=uid, defaults={'role': 'membre'}
            )
            if ok:
                created += 1
        return Response({'invites': created})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        canal = self.get_object()
        qs = canal.messages.filter(supprime=False).order_by('created_at')
        limite = int(request.query_params.get('limite', 50))
        offset = int(request.query_params.get('offset', 0))
        qs = qs[offset:offset + limite]
        return Response(MessageSerializer(qs, many=True, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def archiver(self, request, pk=None):
        canal = self.get_object()
        canal.archive = True
        canal.save(update_fields=['archive'])
        return Response({'detail': 'Canal archivé.'})


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.filter(supprime=False).order_by('created_at')
    serializer_class = MessageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [CanReadCollab]

    def get_queryset(self):
        qs = super().get_queryset()
        canal = self.request.query_params.get('canal')
        return qs.filter(canal_id=canal) if canal else qs

    def perform_create(self, s):
        msg = s.save(auteur=self.request.user)
        LectureMessage.objects.get_or_create(message=msg, utilisateur=self.request.user)

    @action(detail=True, methods=['post'])
    def marquer_lu(self, request, pk=None):
        msg = self.get_object()
        LectureMessage.objects.get_or_create(message=msg, utilisateur=request.user)
        return Response({'lu': True})

    @action(detail=True, methods=['post'])
    def reagir(self, request, pk=None):
        msg = self.get_object()
        emoji = request.data.get('emoji', '')
        if not emoji:
            return Response({'detail': 'emoji requis.'}, status=400)
        reactions = msg.reactions or {}
        if emoji not in reactions:
            reactions[emoji] = []
        user_id = str(request.user.id)
        if user_id in reactions[emoji]:
            reactions[emoji].remove(user_id)
        else:
            reactions[emoji].append(user_id)
        msg.reactions = reactions
        msg.save(update_fields=['reactions'])
        return Response({'reactions': msg.reactions})

    @action(detail=True, methods=['delete'])
    def supprimer(self, request, pk=None):
        msg = self.get_object()
        if msg.auteur != request.user:
            return Response({'detail': 'Action non autorisée.'}, status=403)
        msg.supprime = True
        msg.contenu = '[Message supprimé]'
        msg.save(update_fields=['supprime', 'contenu'])
        return Response({'detail': 'Message supprimé.'})

    @action(detail=True, methods=['put'])
    def modifier(self, request, pk=None):
        msg = self.get_object()
        if msg.auteur != request.user:
            return Response({'detail': 'Action non autorisée.'}, status=403)
        msg.contenu = request.data.get('contenu', msg.contenu)
        msg.modifie = True
        msg.save(update_fields=['contenu', 'modifie'])
        return Response(MessageSerializer(msg, context={'request': request}).data)


# ─── Notifications ────────────────────────────────────────────────────────────

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [CanReadCollab]

    def get_queryset(self):
        return Notification.objects.filter(destinataire=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        n = self.get_object()
        n.marquer_lue()
        return Response(NotificationSerializer(n).data)

    @action(detail=False, methods=['post'])
    def tout_marquer_lu(self, request):
        count = Notification.objects.filter(
            destinataire=request.user, lue=False
        ).update(lue=True, date_lecture=timezone.now())
        return Response({'marquees': count})

    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        qs = Notification.objects.filter(destinataire=request.user, lue=False).order_by('-created_at')
        return Response({
            'count': qs.count(),
            'notifications': NotificationSerializer(qs[:20], many=True).data,
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = Notification.objects.filter(destinataire=request.user)
        return Response({
            'total': qs.count(),
            'non_lues': qs.filter(lue=False).count(),
            'critiques': qs.filter(priorite='critique', lue=False).count(),
            'par_type': {
                t: qs.filter(type_notification=t, lue=False).count()
                for t, _ in Notification.TYPE_CHOICES
                if qs.filter(type_notification=t, lue=False).exists()
            },
        })


class PreferenceNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = PreferenceNotificationSerializer
    permission_classes = [CanReadCollab]

    def get_queryset(self):
        return PreferenceNotification.objects.filter(utilisateur=self.request.user)

    def get_object(self):
        pref, _ = PreferenceNotification.objects.get_or_create(utilisateur=self.request.user)
        return pref

    def perform_create(self, s):
        s.save(utilisateur=self.request.user)


# ─── Centre d'activités ───────────────────────────────────────────────────────

class ActiviteRecenteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActiviteRecenteSerializer
    permission_classes = [CanReadCollab]

    def get_queryset(self):
        return ActiviteRecente.objects.filter(utilisateur=self.request.user).order_by('-created_at')[:50]


# ─── Groupes ──────────────────────────────────────────────────────────────────

class GroupeTravailViewSet(viewsets.ModelViewSet):
    queryset = GroupeTravail.objects.filter(actif=True).prefetch_related('membres')
    serializer_class = GroupeTravailSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom', 'description']
    permission_classes = [CanReadCollab]

    def get_queryset(self):
        qs = super().get_queryset()
        projet = self.request.query_params.get('projet')
        if projet:
            qs = qs.filter(projet_id=projet)
        return qs

    def perform_create(self, s):
        groupe = s.save(cree_par=self.request.user)
        groupe.membres.add(self.request.user)

    @action(detail=True, methods=['post'])
    def ajouter_membre(self, request, pk=None):
        g = self.get_object()
        user_ids = request.data.get('user_ids', [])
        for uid in user_ids:
            g.membres.add(uid)
        return Response(GroupeTravailSerializer(g).data)

    @action(detail=True, methods=['post'])
    def retirer_membre(self, request, pk=None):
        g = self.get_object()
        user_id = request.data.get('user_id')
        g.membres.remove(user_id)
        return Response({'detail': 'Membre retiré.'})


# ─── M43 : Événements ─────────────────────────────────────────────────────────

class EvenementViewSet(viewsets.ModelViewSet):
    queryset = Evenement.objects.select_related(
        'organisateur', 'projet', 'programme'
    ).prefetch_related('participants', 'depenses').order_by('-date_debut')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['titre', 'description', 'lieu', 'objectifs']
    ordering_fields = ['date_debut', 'statut', 'type_evenement']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [CanReadCollab()] if self.action in ['list', 'retrieve'] else [CanEditCollab()]

    def get_serializer_class(self):
        return EvenementListSerializer if self.action == 'list' else EvenementDetailSerializer

    def perform_create(self, s):
        s.save(organisateur=self.request.user)

    @action(detail=True, methods=['post'])
    def ouvrir_inscriptions(self, request, pk=None):
        ev = self.get_object()
        ev.statut = 'ouvert_inscriptions'
        ev.save(update_fields=['statut'])
        return Response(EvenementDetailSerializer(ev).data)

    @action(detail=True, methods=['post'])
    def demarrer(self, request, pk=None):
        ev = self.get_object()
        ev.statut = 'en_cours'
        ev.save(update_fields=['statut'])
        return Response(EvenementDetailSerializer(ev).data)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        ev = self.get_object()
        ev.statut = 'termine'
        cr = request.data.get('compte_rendu', '')
        if cr:
            ev.compte_rendu = cr
        ev.budget_realise = ev.depenses.aggregate(
            t=__import__('django.db.models', fromlist=['Sum']).Sum('montant')
        ).get('t') or 0
        ev.save(update_fields=['statut', 'compte_rendu', 'budget_realise'])
        return Response(EvenementDetailSerializer(ev).data)

    @action(detail=True, methods=['post'])
    def inscrire(self, request, pk=None):
        ev = self.get_object()
        participant, created = ParticipantEvenement.objects.get_or_create(
            evenement=ev,
            utilisateur=request.user,
            defaults={
                'email': request.user.email,
                'statut': 'inscrit',
            }
        )
        return Response(ParticipantEvenementSerializer(participant).data,
                        status=201 if created else 200)

    @action(detail=True, methods=['post'])
    def scanner_presence(self, request, pk=None):
        ev = self.get_object()
        code_badge = request.data.get('code_badge')
        email = request.data.get('email')
        qs = ev.participants.all()
        if code_badge:
            qs = qs.filter(code_badge=code_badge)
        elif email:
            qs = qs.filter(email=email)
        else:
            return Response({'detail': 'code_badge ou email requis.'}, status=400)
        participant = qs.first()
        if not participant:
            return Response({'detail': 'Participant non trouvé.'}, status=404)
        participant.statut = 'present'
        participant.heure_arrivee = timezone.now()
        participant.qr_code_scan = True
        participant.save(update_fields=['statut', 'heure_arrivee', 'qr_code_scan'])
        return Response(ParticipantEvenementSerializer(participant).data)

    @action(detail=True, methods=['get'])
    def liste_presences(self, request, pk=None):
        ev = self.get_object()
        participants = ev.participants.all()
        return Response({
            'inscrits': participants.count(),
            'presents': participants.filter(statut='present').count(),
            'absents': participants.filter(statut='absent').count(),
            'participants': ParticipantEvenementSerializer(participants, many=True).data,
        })

    @action(detail=False, methods=['get'])
    def a_venir(self, request):
        qs = Evenement.objects.filter(
            date_debut__gte=timezone.now(),
            statut__in=['planifie', 'ouvert_inscriptions']
        ).order_by('date_debut')[:10]
        return Response(EvenementListSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def mes_evenements(self, request):
        qs = Evenement.objects.filter(
            participants__utilisateur=request.user
        ).order_by('-date_debut')[:20]
        return Response(EvenementListSerializer(qs, many=True).data)


class ParticipantEvenementViewSet(viewsets.ModelViewSet):
    queryset = ParticipantEvenement.objects.select_related('evenement', 'utilisateur')
    serializer_class = ParticipantEvenementSerializer
    permission_classes = [CanEditCollab]

    def get_queryset(self):
        qs = super().get_queryset()
        ev = self.request.query_params.get('evenement')
        return qs.filter(evenement_id=ev) if ev else qs

    @action(detail=True, methods=['post'])
    def confirmer(self, request, pk=None):
        p = self.get_object()
        p.statut = 'confirme'
        p.save(update_fields=['statut'])
        return Response(ParticipantEvenementSerializer(p).data)


class DepenseEvenementViewSet(viewsets.ModelViewSet):
    queryset = DepenseEvenement.objects.select_related('evenement', 'saisi_par')
    serializer_class = DepenseEvenementSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [CanEditCollab]

    def get_queryset(self):
        qs = super().get_queryset()
        ev = self.request.query_params.get('evenement')
        return qs.filter(evenement_id=ev) if ev else qs

    def perform_create(self, s):
        s.save(saisi_par=self.request.user)


# ─── Dashboard collaboration ──────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([CanReadCollab])
def dashboard_collaboration(request):
    user = request.user
    mes_canaux = Canal.objects.filter(memberships__utilisateur=user, archive=False)
    return Response({
        'messagerie': {
            'canaux': mes_canaux.count(),
            'messages_non_lus': Message.objects.filter(
                canal__in=mes_canaux
            ).exclude(lectures__utilisateur=user).exclude(auteur=user).count(),
        },
        'notifications': {
            'non_lues': Notification.objects.filter(destinataire=user, lue=False).count(),
            'critiques': Notification.objects.filter(
                destinataire=user, priorite='critique', lue=False
            ).count(),
        },
        'groupes': GroupeTravail.objects.filter(membres=user, actif=True).count(),
        'activites_recentes': ActiviteRecenteSerializer(
            ActiviteRecente.objects.filter(utilisateur=user).order_by('-created_at')[:10],
            many=True
        ).data,
    })


@api_view(['POST'])
@permission_classes([CanEditCollab])
def envoyer_notification_bulk(request):
    user_ids = request.data.get('user_ids', [])
    titre = request.data.get('titre', '')
    message = request.data.get('message', '')
    type_notif = request.data.get('type', 'systeme')
    canal = request.data.get('canal', 'interne')
    priorite = request.data.get('priorite', 'normale')
    if not user_ids or not titre:
        return Response({'detail': 'user_ids et titre requis.'}, status=400)
    created = []
    for uid in user_ids:
        n = Notification.envoyer(
            destinataire_id=uid,
            type_notif=type_notif,
            titre=titre,
            message=message,
            canal=canal,
            priorite=priorite,
            cree_par=request.user,
        )
        created.append(n.id)
    return Response({'envoyees': len(created), 'ids': created}, status=201)
