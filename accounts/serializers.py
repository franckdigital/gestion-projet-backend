from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import (
    User, Role, Permission, MFADevice, PasswordResetToken,
    OTPCode, UserSession, LoginAttempt, AuditLog, MODULE
)
from .utils import validate_password_strength


# ─── Auth ────────────────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(help_text="Email, nom d'utilisateur ou matricule")
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(default=False, required=False)

    def validate(self, data):
        login = data.get('login', '').strip()
        password = data.get('password', '')

        user = None
        # Try email
        if '@' in login:
            user = authenticate(request=self.context.get('request'), username=login, password=password)
        if user is None:
            # Try username
            try:
                u = User.objects.get(username=login)
                user = authenticate(request=self.context.get('request'), username=u.email, password=password)
            except User.DoesNotExist:
                pass
        if user is None:
            # Try matricule
            try:
                u = User.objects.get(matricule=login)
                user = authenticate(request=self.context.get('request'), username=u.email, password=password)
            except User.DoesNotExist:
                pass

        if user is None:
            raise serializers.ValidationError("Identifiants incorrects.")

        if not user.is_active:
            raise serializers.ValidationError("Ce compte est désactivé.")

        if user.est_verrouille:
            raise serializers.ValidationError(
                f"Compte verrouillé. Réessayez après {user.locked_until.strftime('%H:%M')}."
            )

        data['user'] = user
        return data


class OTPVerifySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=10)
    type_otp = serializers.ChoiceField(choices=['login_mfa', 'password_reset', 'email_verify'])


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        errors = validate_password_strength(data['new_password'])
        if errors:
            raise serializers.ValidationError(errors)
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        errors = validate_password_strength(data['new_password'])
        if errors:
            raise serializers.ValidationError(errors)
        return data


# ─── Permissions & Roles ─────────────────────────────────────────────────────

class PermissionSerializer(serializers.ModelSerializer):
    module_label = serializers.CharField(source='get_module_display', read_only=True)

    class Meta:
        model = Permission
        fields = ['id', 'module', 'module_label', 'peut_lire', 'peut_creer', 'peut_modifier',
                  'peut_valider', 'peut_supprimer', 'peut_exporter', 'peut_imprimer']


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    nb_utilisateurs = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'nom', 'code', 'description', 'type_role', 'couleur', 'est_systeme', 'actif',
                  'permissions', 'nb_utilisateurs', 'created_at', 'updated_at']
        read_only_fields = ['id', 'est_systeme', 'created_at', 'updated_at']

    def get_nb_utilisateurs(self, obj):
        return obj.utilisateurs.filter(is_active=True).count()


class RoleCreateSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, required=False)

    class Meta:
        model = Role
        fields = ['nom', 'code', 'description', 'type_role', 'couleur', 'permissions']

    def create(self, validated_data):
        permissions_data = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)
        for perm_data in permissions_data:
            Permission.objects.create(role=role, **perm_data)
        return role

    def update(self, instance, validated_data):
        permissions_data = validated_data.pop('permissions', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if permissions_data is not None:
            instance.permissions.all().delete()
            for perm_data in permissions_data:
                Permission.objects.create(role=instance, **perm_data)
        return instance


class RolePermissionMatrixSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()
    permissions = serializers.ListField(child=serializers.DictField())


# ─── User ─────────────────────────────────────────────────────────────────────

class UserMinimalSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'email', 'nom_complet', 'photo', 'poste']


class UserSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()
    roles = RoleSerializer(many=True, read_only=True)
    permissions_matrix = serializers.SerializerMethodField()
    est_verrouille = serializers.ReadOnlyField()
    organisation_nom = serializers.CharField(source='organisation.nom', read_only=True)
    direction_nom = serializers.CharField(source='direction.nom', read_only=True)
    service_nom = serializers.CharField(source='service.intitule', read_only=True)
    site_nom = serializers.CharField(source='site.nom', read_only=True)
    manager_nom = serializers.CharField(source='manager.nom_complet', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'nom_complet',
            'matricule', 'telephone', 'telephone_mobile', 'photo',
            'poste', 'fonction', 'date_embauche',
            'organisation', 'organisation_nom', 'direction', 'direction_nom',
            'service', 'service_nom', 'site', 'site_nom',
            'manager', 'manager_nom',
            'roles', 'permissions_matrix',
            'mfa_enabled', 'mfa_method',
            'is_active', 'est_verrouille', 'failed_login_attempts',
            'last_login', 'last_login_ip', 'last_activity',
            'must_change_password', 'date_joined', 'langue', 'preferences',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'failed_login_attempts']

    def get_permissions_matrix(self, obj):
        return obj.get_permissions_matrix()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    roles_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'matricule',
            'password', 'confirm_password',
            'telephone', 'telephone_mobile', 'poste', 'fonction', 'date_embauche',
            'organisation', 'direction', 'service', 'site', 'manager',
            'roles_ids', 'langue',
        ]

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        errors = validate_password_strength(data['password'])
        if errors:
            raise serializers.ValidationError({"password": errors})
        return data

    def create(self, validated_data):
        roles_ids = validated_data.pop('roles_ids', [])
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if roles_ids:
            user.roles.set(Role.objects.filter(id__in=roles_ids))
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    roles_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'matricule', 'telephone', 'telephone_mobile',
            'photo', 'poste', 'fonction', 'date_embauche',
            'organisation', 'direction', 'service', 'site', 'manager',
            'is_active', 'roles_ids', 'langue', 'preferences',
        ]

    def update(self, instance, validated_data):
        roles_ids = validated_data.pop('roles_ids', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if roles_ids is not None:
            instance.roles.set(Role.objects.filter(id__in=roles_ids))
        return instance


class UserImportSerializer(serializers.Serializer):
    fichier = serializers.FileField()


# ─── Session & Audit ──────────────────────────────────────────────────────────

class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ['id', 'token', 'ip_address', 'user_agent', 'device_info',
                  'is_active', 'last_activity', 'created_at', 'ended_at']
        read_only_fields = ['__all__']


class LoginAttemptSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = LoginAttempt
        fields = ['id', 'user', 'user_email', 'email_tente', 'ip_address',
                  'user_agent', 'resultat', 'details', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    user_nom = serializers.CharField(source='user.nom_complet', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_nom', 'action', 'module', 'objet_type',
                  'objet_id', 'objet_repr', 'details', 'ip_address', 'created_at']


# ─── MFA ─────────────────────────────────────────────────────────────────────

class MFASetupSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['email', 'sms', 'totp_google', 'totp_microsoft'])


class MFAVerifySetupSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=10)


class MFADisableSerializer(serializers.Serializer):
    password = serializers.CharField()


# ─── Custom JWT ──────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
