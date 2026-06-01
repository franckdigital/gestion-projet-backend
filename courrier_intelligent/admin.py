from django.contrib import admin
from .models import CompteEmail, Email, PieceJointeEmail, ActionEmail, EtiquetteEmail


@admin.register(CompteEmail)
class CompteEmailAdmin(admin.ModelAdmin):
    list_display = ['adresse_email', 'type_compte', 'utilisateur', 'statut', 'est_principal', 'derniere_synchro']
    list_filter = ['type_compte', 'statut', 'est_principal']


class PieceJointeInline(admin.TabularInline):
    model = PieceJointeEmail
    extra = 0
    fields = ['nom_fichier', 'type_mime', 'taille', 'fichier']


class ActionEmailInline(admin.TabularInline):
    model = ActionEmail
    extra = 0
    fields = ['type_action', 'description', 'responsable', 'echeance', 'statut']


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['sujet', 'direction', 'expediteur_email', 'statut', 'priorite',
                    'est_lu', 'score_urgence', 'traite_par_ia', 'projet', 'created_at']
    list_filter = ['direction', 'statut', 'priorite', 'est_lu', 'traite_par_ia']
    search_fields = ['sujet', 'expediteur', 'expediteur_email', 'corps_texte']
    readonly_fields = ['created_at', 'updated_at', 'lu_le']
    inlines = [PieceJointeInline, ActionEmailInline]


@admin.register(ActionEmail)
class ActionEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'type_action', 'description', 'responsable', 'echeance', 'statut']
    list_filter = ['type_action', 'statut', 'detectee_par_ia']


@admin.register(EtiquetteEmail)
class EtiquetteEmailAdmin(admin.ModelAdmin):
    list_display = ['nom', 'couleur', 'utilisateur']
