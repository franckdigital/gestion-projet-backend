import io
import pandas as pd
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import (
    User, Role, Permission, OTPCode, PasswordResetToken,
    UserSession, LoginAttempt, AuditLog, MODULE
)
from .serializers import (
    LoginSerializer, OTPVerifySerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, ChangePasswordSerializer,
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    RoleSerializer, RoleCreateSerializer, PermissionSerializer,
    UserSessionSerializer, LoginAttemptSerializer, AuditLogSerializer,
    MFASetupSerializer, MFAVerifySetupSerializer, MFADisableSerializer,
)
from .permissions import IsAdminOrSuperAdmin, IsSuperAdmin
from .filters import UserFilter, RoleFilter, AuditLogFilter, LoginAttemptFilter
from .utils import (
    get_client_ip, send_otp_email, send_password_reset_email,
    send_account_locked_email, send_new_login_notification
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


def _get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


# ─── Authentication ───────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        # Log failed attempt
        email_tente = request.data.get('login', '')
        user = None
        try:
            if '@' in email_tente:
                user = User.objects.get(email=email_tente)
            else:
                user = User.objects.filter(
                    Q(username=email_tente) | Q(matricule=email_tente)
                ).first()
        except User.DoesNotExist:
            pass

        if user:
            user.increment_failed_attempts()
            if user.est_verrouille:
                send_account_locked_email(user)
                LoginAttempt.objects.create(
                    user=user, email_tente=email_tente,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    resultat='locked',
                )
                return Response(
                    {'detail': 'Compte verrouillé suite à trop de tentatives.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        LoginAttempt.objects.create(
            user=user, email_tente=email_tente,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            resultat='failed',
            details={'errors': serializer.errors},
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.validated_data['user']
    ip = get_client_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')

    user.reset_failed_attempts()

    # MFA check
    if user.mfa_enabled and user.mfa_method != 'none':
        if user.mfa_method in ('email', 'sms'):
            otp = OTPCode.generate(user, 'login_mfa')
            send_otp_email(user, otp)
        LoginAttempt.objects.create(
            user=user, email_tente=user.email, ip_address=ip, user_agent=ua, resultat='mfa_required'
        )
        return Response({'mfa_required': True, 'user_id': user.id, 'mfa_method': user.mfa_method})

    # Issue tokens
    tokens = _get_tokens(user)

    # Update user metadata
    user.last_login_ip = ip
    user.last_activity = timezone.now()
    user.save(update_fields=['last_login_ip', 'last_activity'])

    # Create session
    session = UserSession.objects.create(
        user=user, ip_address=ip, user_agent=ua,
        device_info={'remember_me': serializer.validated_data.get('remember_me', False)}
    )

    LoginAttempt.objects.create(
        user=user, email_tente=user.email, ip_address=ip, user_agent=ua, resultat='success'
    )
    AuditLog.log(user, 'login', request=request)

    # Notify on new IP
    if user.last_login_ip and user.last_login_ip != ip:
        send_new_login_notification(user, ip, ua)

    return Response({
        **tokens,
        'user': UserSerializer(user).data,
        'session_token': str(session.token),
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        user = User.objects.get(id=serializer.validated_data['user_id'])
    except User.DoesNotExist:
        return Response({'detail': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    code = serializer.validated_data['code']
    type_otp = serializer.validated_data['type_otp']
    ip = get_client_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')

    # TOTP verify
    if user.mfa_method in ('totp_google', 'totp_microsoft'):
        if not user.verify_totp(code):
            LoginAttempt.objects.create(
                user=user, email_tente=user.email, ip_address=ip, user_agent=ua, resultat='mfa_failed'
            )
            return Response({'detail': 'Code invalide.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        otp_obj = OTPCode.objects.filter(
            user=user, type_otp=type_otp, used=False, code=code
        ).order_by('-created_at').first()

        if not otp_obj or not otp_obj.is_valid:
            LoginAttempt.objects.create(
                user=user, email_tente=user.email, ip_address=ip, user_agent=ua, resultat='mfa_failed'
            )
            return Response({'detail': 'Code invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.used = True
        otp_obj.save()

    tokens = _get_tokens(user)
    user.last_login_ip = ip
    user.last_activity = timezone.now()
    user.save(update_fields=['last_login_ip', 'last_activity'])

    session = UserSession.objects.create(user=user, ip_address=ip, user_agent=ua)
    LoginAttempt.objects.create(
        user=user, email_tente=user.email, ip_address=ip, user_agent=ua, resultat='success'
    )
    AuditLog.log(user, 'login', request=request)

    return Response({**tokens, 'user': UserSerializer(user).data, 'session_token': str(session.token)})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        user = User.objects.get(email=serializer.validated_data['email'])
        token = PasswordResetToken.create_for_user(user, ip=get_client_ip(request))
        send_password_reset_email(user, token)
    except User.DoesNotExist:
        pass  # Silent fail for security

    return Response({'detail': 'Si cet email existe, un lien de réinitialisation a été envoyé.'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        token_obj = PasswordResetToken.objects.get(token=serializer.validated_data['token'])
    except PasswordResetToken.DoesNotExist:
        return Response({'detail': 'Token invalide.'}, status=status.HTTP_400_BAD_REQUEST)

    if not token_obj.is_valid:
        return Response({'detail': 'Token expiré ou déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

    user = token_obj.user
    user.set_password(serializer.validated_data['new_password'])
    user.password_changed_at = timezone.now()
    user.must_change_password = False
    user.save(update_fields=['password', 'password_changed_at', 'must_change_password'])

    token_obj.used = True
    token_obj.save()

    AuditLog.log(user, 'password_change', request=request)
    return Response({'detail': 'Mot de passe réinitialisé avec succès.'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if not user.check_password(serializer.validated_data['old_password']):
        return Response({'detail': 'Mot de passe actuel incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(serializer.validated_data['new_password'])
    user.password_changed_at = timezone.now()
    user.must_change_password = False
    user.save(update_fields=['password', 'password_changed_at', 'must_change_password'])

    AuditLog.log(user, 'password_change', request=request)
    return Response({'detail': 'Mot de passe modifié avec succès.'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    try:
        refresh = request.data.get('refresh')
        if refresh:
            from rest_framework_simplejwt.tokens import RefreshToken as RT
            RT(refresh).blacklist()
    except Exception:
        pass

    UserSession.objects.filter(user=request.user, is_active=True).update(
        is_active=False, ended_at=timezone.now()
    )
    AuditLog.log(request.user, 'logout', request=request)
    return Response({'detail': 'Déconnecté avec succès.'})


# ─── MFA ─────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mfa_setup(request):
    serializer = MFASetupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    method = serializer.validated_data['method']
    user.mfa_method = method

    if method in ('totp_google', 'totp_microsoft'):
        secret = user.generate_mfa_secret()
        totp_uri = user.get_totp_uri()
        return Response({'secret': secret, 'totp_uri': totp_uri, 'method': method})
    else:
        otp = OTPCode.generate(user, 'email_verify')
        send_otp_email(user, otp)
        user.save(update_fields=['mfa_method'])
        return Response({'message': 'Code OTP envoyé.', 'method': method})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mfa_verify_setup(request):
    serializer = MFAVerifySetupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    code = serializer.validated_data['code']

    if user.mfa_method in ('totp_google', 'totp_microsoft'):
        if not user.verify_totp(code):
            return Response({'detail': 'Code invalide.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        otp_obj = OTPCode.objects.filter(
            user=user, type_otp='email_verify', used=False, code=code
        ).order_by('-created_at').first()
        if not otp_obj or not otp_obj.is_valid:
            return Response({'detail': 'Code invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)
        otp_obj.used = True
        otp_obj.save()

    user.mfa_enabled = True
    user.save(update_fields=['mfa_enabled', 'mfa_method'])
    AuditLog.log(user, 'mfa_enabled', request=request)
    return Response({'detail': 'MFA activé avec succès.'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mfa_disable(request):
    serializer = MFADisableSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if not user.check_password(serializer.validated_data['password']):
        return Response({'detail': 'Mot de passe incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

    user.mfa_enabled = False
    user.mfa_method = 'none'
    user.mfa_secret = ''
    user.save(update_fields=['mfa_enabled', 'mfa_method', 'mfa_secret'])
    AuditLog.log(user, 'mfa_disabled', request=request)
    return Response({'detail': 'MFA désactivé.'})


# ─── Users ViewSet ────────────────────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related(
        'organisation', 'direction', 'service', 'site', 'manager'
    ).prefetch_related('roles__permissions').order_by('last_name', 'first_name')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['first_name', 'last_name', 'email', 'matricule', 'poste']
    ordering_fields = ['last_name', 'first_name', 'email', 'date_joined']
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        AuditLog.log(
            self.request.user, 'create', module='gouvernance',
            objet_type='User', objet_id=user.id, objet_repr=str(user),
            request=self.request,
        )

    def perform_update(self, serializer):
        user = serializer.save()
        AuditLog.log(
            self.request.user, 'update', module='gouvernance',
            objet_type='User', objet_id=user.id, objet_repr=str(user),
            request=self.request,
        )

    def perform_destroy(self, instance):
        AuditLog.log(
            self.request.user, 'delete', module='gouvernance',
            objet_type='User', objet_id=instance.id, objet_repr=str(instance),
            request=self.request,
        )
        instance.delete()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def lock(self, request, pk=None):
        user = self.get_object()
        from datetime import timedelta
        user.locked_until = timezone.now() + timedelta(hours=24)
        user.save(update_fields=['locked_until'])
        AuditLog.log(request.user, 'account_locked', objet_type='User', objet_id=user.id, request=request)
        return Response({'detail': 'Compte verrouillé.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def unlock(self, request, pk=None):
        user = self.get_object()
        user.locked_until = None
        user.failed_login_attempts = 0
        user.save(update_fields=['locked_until', 'failed_login_attempts'])
        AuditLog.log(request.user, 'account_unlocked', objet_type='User', objet_id=user.id, request=request)
        return Response({'detail': 'Compte déverrouillé.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        token = PasswordResetToken.create_for_user(user, ip=get_client_ip(request))
        send_password_reset_email(user, token)
        return Response({'detail': 'Lien de réinitialisation envoyé.'})

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrSuperAdmin],
            parser_classes=[MultiPartParser, FormParser])
    def import_csv(self, request):
        fichier = request.FILES.get('fichier')
        if not fichier:
            return Response({'detail': 'Fichier requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            name = fichier.name.lower()
            if name.endswith('.csv'):
                df = pd.read_csv(fichier)
            else:
                df = pd.read_excel(fichier)
        except Exception as e:
            return Response({'detail': f'Erreur lecture fichier : {e}'}, status=status.HTTP_400_BAD_REQUEST)

        created, errors = [], []
        required = {'email', 'first_name', 'last_name'}
        missing = required - set(df.columns)
        if missing:
            return Response(
                {'detail': f"Colonnes manquantes : {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for i, row in df.iterrows():
            try:
                if User.objects.filter(email=row['email']).exists():
                    errors.append({'ligne': i + 2, 'email': row['email'], 'erreur': 'Email déjà utilisé'})
                    continue
                import secrets as sec
                pwd = sec.token_urlsafe(12)
                user = User.objects.create_user(
                    email=row['email'],
                    username=row.get('username', row['email'].split('@')[0]),
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    matricule=row.get('matricule') or None,
                    poste=row.get('poste', ''),
                    telephone=row.get('telephone', ''),
                    password=pwd,
                    must_change_password=True,
                )
                token = PasswordResetToken.create_for_user(user)
                send_password_reset_email(user, token)
                created.append({'email': user.email, 'id': user.id})
            except Exception as e:
                errors.append({'ligne': i + 2, 'email': row.get('email', ''), 'erreur': str(e)})

        AuditLog.log(
            request.user, 'import', module='gouvernance',
            details={'created': len(created), 'errors': len(errors)},
            request=request,
        )
        return Response({'created': len(created), 'errors': errors, 'details': created})

    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrSuperAdmin])
    def stats(self, request):
        from django.utils import timezone as tz
        total = User.objects.count()
        actifs = User.objects.filter(is_active=True).count()
        connectes_auj = User.objects.filter(
            last_activity__date=tz.now().date()
        ).count()
        verrouilles = User.objects.filter(locked_until__gt=tz.now()).count()

        by_role = (
            Role.objects.annotate(nb=Count('utilisateurs', filter=Q(utilisateurs__is_active=True)))
            .values('nom', 'nb')
            .order_by('-nb')
        )

        return Response({
            'total': total,
            'actifs': actifs,
            'inactifs': total - actifs,
            'connectes_aujourd_hui': connectes_auj,
            'verrouilles': verrouilles,
            'par_role': list(by_role),
        })


# ─── Roles ViewSet ────────────────────────────────────────────────────────────

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.prefetch_related('permissions').order_by('nom')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RoleFilter
    search_fields = ['nom', 'code', 'description']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrSuperAdmin()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RoleCreateSerializer
        return RoleSerializer

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        if role.est_systeme:
            return Response(
                {'detail': 'Les rôles système ne peuvent pas être supprimés.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def duplicate(self, request, pk=None):
        role = self.get_object()
        nouveau_nom = request.data.get('nom', f"Copie de {role.nom}")
        new_role = role.duplicate(nouveau_nom, created_by=request.user)
        return Response(RoleSerializer(new_role).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrSuperAdmin])
    def set_permissions(self, request, pk=None):
        role = self.get_object()
        permissions_data = request.data.get('permissions', [])

        role.permissions.all().delete()
        created = []
        for perm_data in permissions_data:
            perm_data['role'] = role.id
            s = PermissionSerializer(data=perm_data)
            if s.is_valid():
                p = Permission.objects.create(role=role, **{
                    k: v for k, v in perm_data.items() if k != 'role'
                })
                created.append(p)

        AuditLog.log(request.user, 'permission_change', objet_type='Role',
                     objet_id=role.id, objet_repr=role.nom, request=request)
        return Response(RoleSerializer(role).data)

    @action(detail=False, methods=['get'])
    def matrix(self, request):
        roles = Role.objects.filter(actif=True).prefetch_related('permissions')
        modules = [{'code': code, 'label': label} for code, label in MODULE.choices]
        result = []
        for role in roles:
            row = {'role': {'id': role.id, 'nom': role.nom, 'code': role.code}, 'permissions': {}}
            for perm in role.permissions.all():
                row['permissions'][perm.module] = {
                    'peut_lire': perm.peut_lire, 'peut_creer': perm.peut_creer,
                    'peut_modifier': perm.peut_modifier, 'peut_valider': perm.peut_valider,
                    'peut_supprimer': perm.peut_supprimer, 'peut_exporter': perm.peut_exporter,
                    'peut_imprimer': perm.peut_imprimer,
                }
            result.append(row)
        return Response({'modules': modules, 'matrix': result})


# ─── Sessions & Audit ─────────────────────────────────────────────────────────

class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.est_super_admin:
            return UserSession.objects.select_related('user').order_by('-created_at')
        return UserSession.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        session = self.get_object()
        if session.user != request.user and not request.user.est_super_admin:
            return Response({'detail': 'Permission refusée.'}, status=status.HTTP_403_FORBIDDEN)
        session.terminate()
        return Response({'detail': 'Session terminée.'})

    @action(detail=False, methods=['post'])
    def terminate_all(self, request):
        UserSession.objects.filter(user=request.user, is_active=True).update(
            is_active=False, ended_at=timezone.now()
        )
        return Response({'detail': 'Toutes les sessions terminées.'})


class LoginAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LoginAttemptSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LoginAttemptFilter
    search_fields = ['email_tente', 'ip_address']
    ordering_fields = ['created_at']
    queryset = LoginAttempt.objects.select_related('user').order_by('-created_at')


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ['objet_repr', 'ip_address']
    ordering_fields = ['created_at']
    queryset = AuditLog.objects.select_related('user').order_by('-created_at')


# ─── Dashboard Sécurité ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def dashboard_securite(request):
    today = timezone.now().date()
    connexions_aujourd_hui = LoginAttempt.objects.filter(
        created_at__date=today, resultat='success'
    ).count()
    echecs_aujourd_hui = LoginAttempt.objects.filter(
        created_at__date=today, resultat='failed'
    ).count()
    comptes_verrouilles = User.objects.filter(locked_until__gt=timezone.now()).count()
    sessions_actives = UserSession.objects.filter(is_active=True).count()
    alertes = LoginAttempt.objects.filter(
        created_at__date=today, resultat__in=['locked', 'mfa_failed']
    ).count()

    connexions_semaine = []
    from datetime import timedelta
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        connexions_semaine.append({
            'date': d.isoformat(),
            'succes': LoginAttempt.objects.filter(created_at__date=d, resultat='success').count(),
            'echecs': LoginAttempt.objects.filter(created_at__date=d, resultat='failed').count(),
        })

    return Response({
        'connexions_aujourd_hui': connexions_aujourd_hui,
        'echecs_aujourd_hui': echecs_aujourd_hui,
        'comptes_verrouilles': comptes_verrouilles,
        'sessions_actives': sessions_actives,
        'alertes_securite': alertes,
        'connexions_semaine': connexions_semaine,
    })
