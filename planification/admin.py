from django.contrib import admin
from .models import (
    CadreLogique, ElementCadreLogique,
    AnalyseSWOT, ElementSWOT, StrategieSWOT,
    TDR, PlanAction, ActionPlanItem,
    ProgrammeActivites, ActivitePA,
    PlanTravail, Activite, Jalon,
)


class ElementCadreInline(admin.TabularInline):
    model = ElementCadreLogique
    extra = 0
    fields = ['niveau', 'code', 'description', 'ordre', 'actif']


@admin.register(CadreLogique)
class CadreLogiqueAdmin(admin.ModelAdmin):
    list_display = ['titre', 'version', 'statut', 'projet', 'programme', 'created_at']
    list_filter = ['statut']
    inlines = [ElementCadreInline]


@admin.register(AnalyseSWOT)
class AnalyseSWOTAdmin(admin.ModelAdmin):
    list_display = ['titre', 'statut', 'date_analyse', 'projet', 'programme']
    list_filter = ['statut']


@admin.register(TDR)
class TDRAdmin(admin.ModelAdmin):
    list_display = ['reference', 'titre', 'type_tdr', 'statut', 'redige_par', 'budget_previsionnel']
    list_filter = ['type_tdr', 'statut']
    search_fields = ['reference', 'titre']
    readonly_fields = ['reference', 'created_at', 'updated_at']


class ActionItemInline(admin.TabularInline):
    model = ActionPlanItem
    extra = 0
    fields = ['code', 'libelle', 'responsable', 'date_debut', 'date_fin', 'statut', 'taux_avancement']


@admin.register(PlanAction)
class PlanActionAdmin(admin.ModelAdmin):
    list_display = ['titre', 'periode', 'annee', 'statut', 'projet', 'programme']
    list_filter = ['statut', 'periode', 'annee']
    inlines = [ActionItemInline]


class ActivitePAInline(admin.TabularInline):
    model = ActivitePA
    extra = 0
    fields = ['code', 'libelle', 'responsable', 'date_debut_prevue', 'date_fin_prevue', 'statut', 'taux_avancement']


@admin.register(ProgrammeActivites)
class ProgrammeActivitesAdmin(admin.ModelAdmin):
    list_display = ['reference', 'titre', 'annee', 'statut', 'projet', 'programme']
    list_filter = ['statut', 'annee', 'periode']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [ActivitePAInline]


class ActiviteInline(admin.TabularInline):
    model = Activite
    extra = 0
    fields = ['code', 'libelle', 'statut', 'date_debut_prevue', 'date_fin_prevue', 'taux_avancement']


@admin.register(PlanTravail)
class PlanTravailAdmin(admin.ModelAdmin):
    list_display = ['nom', 'projet', 'annee', 'trimestre', 'statut']
    list_filter = ['statut', 'annee']
    inlines = [ActiviteInline]
