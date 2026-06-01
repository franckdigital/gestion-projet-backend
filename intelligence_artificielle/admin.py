from django.contrib import admin
from .models import (
    ConversationIA, MessageIA,
    GenerationDocument,
    ModeleIA, AnalyseIAPredictive, AlerteIA, RecommandationIA,
    JournalIA,
)


class MessageIAInline(admin.TabularInline):
    model = MessageIA
    extra = 0
    fields = ['role', 'contenu', 'tokens_utilises', 'created_at']
    readonly_fields = ['created_at', 'tokens_utilises']


@admin.register(ConversationIA)
class ConversationIAAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'titre', 'contexte', 'projet', 'archivee', 'created_at']
    list_filter = ['contexte', 'archivee']
    search_fields = ['titre', 'utilisateur__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MessageIAInline]


@admin.register(GenerationDocument)
class GenerationDocumentAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_document', 'mode', 'statut', 'score_qualite',
                    'tokens_utilises', 'demande_par', 'created_at']
    list_filter = ['type_document', 'mode', 'statut', 'langue']
    search_fields = ['titre', 'instructions']
    readonly_fields = ['contenu_genere', 'statut', 'score_qualite', 'tokens_utilises',
                       'created_at', 'completed_at']


@admin.register(ModeleIA)
class ModeleIAAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_modele', 'statut', 'version', 'precision',
                    'nb_executions', 'derniere_execution']
    list_filter = ['type_modele', 'statut']
    readonly_fields = ['nb_executions', 'derniere_execution', 'created_at']


class AlerteIAInline(admin.TabularInline):
    model = AlerteIA
    extra = 0
    fields = ['type_alerte', 'niveau', 'titre', 'lue', 'traitee']


class RecommandationIAInline(admin.TabularInline):
    model = RecommandationIA
    extra = 0
    fields = ['type_recommandation', 'titre', 'priorite', 'statut']


@admin.register(AnalyseIAPredictive)
class AnalyseIAPredictiveAdmin(admin.ModelAdmin):
    list_display = ['type_analyse', 'projet', 'programme', 'statut',
                    'score_confiance', 'demande_par', 'created_at']
    list_filter = ['type_analyse', 'statut']
    readonly_fields = ['resultats', 'previsions', 'anomalies', 'statut',
                       'created_at', 'completed_at']
    inlines = [AlerteIAInline, RecommandationIAInline]


@admin.register(AlerteIA)
class AlerteIAAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_alerte', 'niveau', 'destinataire', 'lue', 'traitee', 'date_alerte']
    list_filter = ['niveau', 'type_alerte', 'lue', 'traitee']
    readonly_fields = ['date_alerte', 'date_traitement']


@admin.register(RecommandationIA)
class RecommandationIAAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_recommandation', 'priorite', 'statut',
                    'score_pertinence', 'created_at']
    list_filter = ['type_recommandation', 'statut', 'priorite']


@admin.register(JournalIA)
class JournalIAAdmin(admin.ModelAdmin):
    list_display = ['type_action', 'utilisateur', 'objet_type', 'tokens_utilises',
                    'duree_ms', 'succes', 'created_at']
    list_filter = ['type_action', 'succes']
    readonly_fields = ['created_at']
    search_fields = ['description', 'message_erreur']
