from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.est_super_admin)


class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.est_super_admin:
            return True
        return request.user.roles.filter(
            code__in=['administrateur', 'super_administrateur']
        ).exists()


class HasModulePermission(BasePermission):
    """Usage: HasModulePermission.for_module('gouvernance', 'peut_creer')"""
    module = None
    action = 'peut_lire'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_module_perm(self.module, self.action)

    @classmethod
    def for_module(cls, module, action='peut_lire'):
        return type(
            f'HasPerm_{module}_{action}',
            (cls,),
            {'module': module, 'action': action},
        )


class CanReadModule(BasePermission):
    module = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_module_perm(self.module, 'peut_lire')


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.est_super_admin:
            return True
        return obj == request.user or request.user.roles.filter(
            code__in=['administrateur', 'super_administrateur']
        ).exists()
