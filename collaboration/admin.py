from django.contrib import admin
from .models import (
    Canal, MembreCanal, Message, LectureMessage,
    Notification, PreferenceNotification, ActiviteRecente, GroupeTravail,
)


class MembreCanalInline(admin.TabularInline):
    model = MembreCanal
    extra = 0
    fields = ['utilisateur', 'role', 'notifications_actives']


@admin.register(Canal)
class CanalAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_canal', 'est_prive', 'archive', 'projet', 'programme', 'cree_par', 'created_at']
    list_filter = ['type_canal', 'est_prive', 'archive']
    search_fields = ['nom', 'description']
    inlines = [MembreCanalInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['canal', 'auteur', 'type_message', 'contenu', 'modifie', 'supprime', 'created_at']
    list_filter = ['type_message', 'supprime', 'modifie']
    search_fields = ['contenu']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_notification', 'destinataire', 'priorite',
                    'canal', 'lue', 'envoyee', 'created_at']
    list_filter = ['type_notification', 'priorite', 'canal', 'lue', 'envoyee']
    search_fields = ['titre', 'message']
    readonly_fields = ['created_at', 'date_lecture', 'date_envoi']


@admin.register(GroupeTravail)
class GroupeTravailAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_groupe', 'actif', 'projet', 'programme', 'cree_par', 'created_at']
    list_filter = ['type_groupe', 'actif']
    filter_horizontal = ['membres']


@admin.register(ActiviteRecente)
class ActiviteRecenteAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'type_activite', 'titre', 'created_at']
    list_filter = ['type_activite']
