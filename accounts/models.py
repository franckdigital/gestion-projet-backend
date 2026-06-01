import uuid
import secrets
import pyotp
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class MODULE(models.TextChoices):
    GOUVERNANCE = 'gouvernance', 'Gouvernance & Administration'
    PROGRAMMES_PROJETS = 'programmes_projets', 'Programmes & Projets'
    PLANIFICATION = 'planification', 'Planification'
    EXECUTION = 'execution', 'Exécution'
    SUIVI_EVALUATION = 'suivi_evaluation', 'Suivi-Évaluation'
    FINANCES = 'finances', 'Gestion Financière'
    GED = 'ged', 'GED & Archivage'
    COURRIER_INTELLIGENT = 'courrier_intelligent', 'Courrier Intelligent'
    COURRIER_ADMINISTRATIF = 'courrier_administratif', 'Courrier Administratif'
    COLLABORATION = 'collaboration', 'Collaboration'
    MOBILE = 'mobile', 'Mobile Terrain'
    IA = 'ia', 'Intelligence Artificielle'
    BI = 'bi', 'Business Intelligence'
    MARCHES_PUBLICS = 'marches_publics', 'Marchés Publics'
    RH = 'rh', 'RH Projet'
    LOGISTIQUE = 'logistique', 'Logistique'
    PARTENAIRES = 'partenaires', 'Partenaires & Bailleurs'
    SIG = 'sig', 'SIG'
    CAPITALISATION = 'capitalisation', 'Capitalisation'


class Role(models.Model):
    TYPE_CHOICES = [
        ('direction_generale', 'Direction Générale'),
        ('directeur_general', 'Directeur Général'),
        ('directeur_executif', 'Directeur Exécutif'),
        ('coordonnateur_programme', 'Coordonnateur Programme'),
        ('responsable_programme', 'Responsable Programme'),
        ('chef_projet', 'Chef Projet'),
        ('responsable_activite', 'Responsable Activité'),
        ('agent_terrain', 'Agent Terrain'),
        ('responsable_se', 'Responsable S&E'),
        ('analyste_se', 'Analyste S&E'),
        ('comptable', 'Comptable'),
        ('controleur_financier', 'Contrôleur Financier'),
        ('archiviste', 'Archiviste'),
        ('gestionnaire_ged', 'Gestionnaire GED'),
        ('administrateur', 'Administrateur'),
        ('super_administrateur', 'Super Administrateur'),
        ('personnalise', 'Rôle personnalisé'),
    ]

    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    type_role = models.CharField(max_length=30, choices=TYPE_CHOICES, default='personnalise')
    couleur = models.CharField(max_length=7, default='#6366f1', blank=True)
    est_systeme = models.BooleanField(default=False)
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='roles_crees'
    )

    class Meta:
        verbose_name = 'Rôle'
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def duplicate(self, nouveau_nom, created_by=None):
        new_role = Role.objects.create(
            nom=nouveau_nom,
            code=f"{self.code}_copie_{uuid.uuid4().hex[:6]}",
            description=self.description,
            type_role='personnalise',
            created_by=created_by,
        )
        for perm in self.permissions.all():
            Permission.objects.create(
                role=new_role,
                module=perm.module,
                peut_lire=perm.peut_lire,
                peut_creer=perm.peut_creer,
                peut_modifier=perm.peut_modifier,
                peut_valider=perm.peut_valider,
                peut_supprimer=perm.peut_supprimer,
                peut_exporter=perm.peut_exporter,
                peut_imprimer=perm.peut_imprimer,
            )
        return new_role


class Permission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    module = models.CharField(max_length=30, choices=MODULE.choices)
    peut_lire = models.BooleanField(default=False)
    peut_creer = models.BooleanField(default=False)
    peut_modifier = models.BooleanField(default=False)
    peut_valider = models.BooleanField(default=False)
    peut_supprimer = models.BooleanField(default=False)
    peut_exporter = models.BooleanField(default=False)
    peut_imprimer = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Permission'
        unique_together = ['role', 'module']

    def __str__(self):
        return f"{self.role.nom} — {self.get_module_display()}"


class User(AbstractUser):
    MFA_METHOD_CHOICES = [
        ('none', 'Aucune'),
        ('email', 'OTP Email'),
        ('sms', 'OTP SMS'),
        ('totp_google', 'Google Authenticator'),
        ('totp_microsoft', 'Microsoft Authenticator'),
    ]

    # Identification
    email = models.EmailField(unique=True)
    matricule = models.CharField(max_length=30, unique=True, null=True, blank=True)

    # Profil
    telephone = models.CharField(max_length=20, blank=True)
    telephone_mobile = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='photos_profil/', null=True, blank=True)
    langue = models.CharField(max_length=5, default='fr')

    # Informations professionnelles
    poste = models.CharField(max_length=200, blank=True)
    fonction = models.CharField(max_length=200, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    manager = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordonnes'
    )

    # Rattachement organisationnel
    organisation = models.ForeignKey(
        'gouvernance.Organisation', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='utilisateurs',
    )
    direction = models.ForeignKey(
        'gouvernance.Direction', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='utilisateurs',
    )
    service = models.ForeignKey(
        'gouvernance.Service', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='utilisateurs',
    )
    site = models.ForeignKey(
        'gouvernance.Site', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='utilisateurs',
    )

    # Rôles
    roles = models.ManyToManyField(Role, related_name='utilisateurs', blank=True)

    # MFA
    mfa_enabled = models.BooleanField(default=False)
    mfa_method = models.CharField(max_length=20, choices=MFA_METHOD_CHOICES, default='none')
    mfa_secret = models.CharField(max_length=64, blank=True)

    # Sécurité
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    # Préférences
    preferences = models.JSONField(default=dict, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def nom_complet(self):
        return self.get_full_name()

    @property
    def est_verrouille(self):
        return bool(self.locked_until and timezone.now() < self.locked_until)

    @property
    def est_super_admin(self):
        return self.is_superuser or self.roles.filter(code='super_administrateur').exists()

    def has_module_perm(self, module, action='peut_lire'):
        if self.est_super_admin:
            return True
        return Permission.objects.filter(
            role__in=self.roles.filter(actif=True),
            module=module,
            **{action: True},
        ).exists()

    def get_permissions_matrix(self):
        if self.est_super_admin:
            return {
                m: {
                    'peut_lire': True, 'peut_creer': True, 'peut_modifier': True,
                    'peut_valider': True, 'peut_supprimer': True, 'peut_exporter': True,
                    'peut_imprimer': True,
                }
                for m, _ in MODULE.choices
            }
        matrix = {}
        for perm in Permission.objects.filter(role__in=self.roles.filter(actif=True)):
            m = perm.module
            if m not in matrix:
                matrix[m] = {k: False for k in ['peut_lire', 'peut_creer', 'peut_modifier',
                                                  'peut_valider', 'peut_supprimer', 'peut_exporter',
                                                  'peut_imprimer']}
            for field in matrix[m]:
                matrix[m][field] = matrix[m][field] or getattr(perm, field)
        return matrix

    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def reset_failed_attempts(self):
        if self.failed_login_attempts > 0 or self.locked_until:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def generate_mfa_secret(self):
        self.mfa_secret = pyotp.random_base32()
        self.save(update_fields=['mfa_secret'])
        return self.mfa_secret

    def get_totp_uri(self, issuer='ERP Gestion Projets'):
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.provisioning_uri(name=self.email, issuer_name=issuer)

    def verify_totp(self, code):
        if not self.mfa_secret:
            return False
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(code, valid_window=1)


class MFADevice(models.Model):
    TYPE_CHOICES = [
        ('totp', 'TOTP Authenticator'),
        ('email', 'OTP Email'),
        ('sms', 'OTP SMS'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_devices')
    type_device = models.CharField(max_length=10, choices=TYPE_CHOICES)
    secret = models.CharField(max_length=64)
    confirmed = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dispositif MFA'


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Token réinitialisation'

    @property
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    @classmethod
    def create_for_user(cls, user, ip=None):
        cls.objects.filter(user=user, used=False).update(used=True)
        return cls.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=2),
            ip_address=ip,
        )


class OTPCode(models.Model):
    TYPE_CHOICES = [
        ('login_mfa', 'MFA Connexion'),
        ('password_reset', 'Réinitialisation MDP'),
        ('email_verify', 'Vérification email'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=10)
    type_otp = models.CharField(max_length=20, choices=TYPE_CHOICES)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Code OTP'

    @property
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    @classmethod
    def generate(cls, user, type_otp):
        cls.objects.filter(user=user, type_otp=type_otp, used=False).update(used=True)
        code = secrets.randbelow(900000) + 100000
        return cls.objects.create(
            user=user,
            code=str(code),
            type_otp=type_otp,
            expires_at=timezone.now() + timedelta(minutes=10),
        )


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_info = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Session utilisateur'
        ordering = ['-created_at']

    def terminate(self):
        self.is_active = False
        self.ended_at = timezone.now()
        self.save(update_fields=['is_active', 'ended_at'])


class LoginAttempt(models.Model):
    RESULT_CHOICES = [
        ('success', 'Succès'),
        ('failed', 'Échec'),
        ('locked', 'Compte verrouillé'),
        ('mfa_required', 'MFA requis'),
        ('mfa_failed', 'Échec MFA'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='login_attempts'
    )
    email_tente = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    resultat = models.CharField(max_length=15, choices=RESULT_CHOICES)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tentative de connexion'
        ordering = ['-created_at']


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('view', 'Consultation'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('permission_change', 'Changement permission'),
        ('password_change', 'Changement mot de passe'),
        ('account_locked', 'Compte verrouillé'),
        ('account_unlocked', 'Compte déverrouillé'),
        ('mfa_enabled', 'MFA activé'),
        ('mfa_disabled', 'MFA désactivé'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=30, blank=True)
    objet_type = models.CharField(max_length=100, blank=True)
    objet_id = models.CharField(max_length=50, blank=True)
    objet_repr = models.CharField(max_length=200, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'audit"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.action} — {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    @classmethod
    def log(cls, user, action, module='', objet_type='', objet_id='', objet_repr='',
            details=None, request=None):
        ip = None
        ua = ''
        if request:
            ip = cls._get_ip(request)
            ua = request.META.get('HTTP_USER_AGENT', '')
        cls.objects.create(
            user=user,
            action=action,
            module=module,
            objet_type=objet_type,
            objet_id=str(objet_id),
            objet_repr=objet_repr,
            details=details or {},
            ip_address=ip,
            user_agent=ua,
        )

    @staticmethod
    def _get_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
