from django.contrib import admin
from .models import (
    ZoneIntervention, Programme, ObjectifProgramme, PartenaireProgramme,
    DocumentProgramme, Projet, MembreEquipeProjet, RisqueProjet,
    LivrableProjet, JalonProjet,
)


@admin.register(ZoneIntervention)
class ZoneInterventionAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'pays', 'region', 'actif']
    list_filter = ['pays', 'actif']
    search_fields = ['nom', 'code']


class ObjectifInline(admin.TabularInline):
    model = ObjectifProgramme
    extra = 0
    fields = ['type_objectif', 'code', 'libelle', 'ordre', 'actif']


class DocumentInline(admin.TabularInline):
    model = DocumentProgramme
    extra = 0
    fields = ['type_document', 'titre', 'statut']


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ['code', 'intitule', 'organisation', 'statut', 'coordonnateur',
                    'date_debut', 'date_fin', 'budget_total']
    list_filter = ['statut', 'organisation', 'devise']
    search_fields = ['code', 'intitule', 'acronyme']
    inlines = [ObjectifInline, DocumentInline]
    readonly_fields = ['created_at', 'updated_at', 'taux_avancement']
    filter_horizontal = ['zones_intervention', 'equipe', 'bailleurs_supplementaires']


class MembreInline(admin.TabularInline):
    model = MembreEquipeProjet
    extra = 0
    fields = ['user', 'role_projet', 'date_affectation', 'is_active']


class LivrableInline(admin.TabularInline):
    model = LivrableProjet
    extra = 0
    fields = ['code', 'titre', 'type_livrable', 'date_prevue', 'statut']


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ['code', 'titre', 'programme', 'statut', 'priorite', 'chef_projet',
                    'date_debut', 'date_fin_prevue', 'taux_avancement']
    list_filter = ['statut', 'priorite', 'organisation']
    search_fields = ['code', 'titre']
    inlines = [MembreInline, LivrableInline]
    readonly_fields = ['created_at', 'updated_at', 'taux_avancement']
    filter_horizontal = ['zones_intervention']


@admin.register(RisqueProjet)
class RisqueAdmin(admin.ModelAdmin):
    list_display = ['titre', 'projet', 'categorie', 'probabilite', 'impact', 'niveau_risque', 'statut']
    list_filter = ['niveau_risque', 'categorie', 'statut']
