from django.contrib import admin
from .models import (
    Organisation, Direction, SousDirection, Service, Site,
    Partenaire, Bailleur, ComiteDirecteur
)


class DirectionInline(admin.TabularInline):
    model = Direction
    extra = 0
    fields = ['code', 'nom', 'responsable', 'actif']


class SiteInline(admin.TabularInline):
    model = Site
    extra = 0
    fields = ['code', 'nom', 'type_site', 'ville', 'actif']


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['sigle', 'nom', 'type_organisation', 'statut', 'pays', 'created_at']
    list_filter = ['type_organisation', 'statut', 'pays']
    search_fields = ['nom', 'sigle', 'email']
    inlines = [DirectionInline, SiteInline]
    readonly_fields = ['created_at', 'updated_at']


class SousDirectionInline(admin.TabularInline):
    model = SousDirection
    extra = 0
    fields = ['code', 'nom', 'responsable', 'actif']


class ServiceDirectionInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ['code', 'intitule', 'responsable', 'actif']
    fk_name = 'direction'


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'organisation', 'responsable', 'actif']
    list_filter = ['organisation', 'actif']
    search_fields = ['nom', 'code']
    inlines = [SousDirectionInline, ServiceDirectionInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['code', 'intitule', 'direction', 'responsable', 'actif']
    list_filter = ['direction__organisation', 'actif']
    search_fields = ['intitule', 'code']


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'type_site', 'ville', 'organisation', 'actif']
    list_filter = ['type_site', 'organisation', 'actif']
    search_fields = ['nom', 'code', 'ville']


@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = ['sigle', 'nom', 'type_partenaire', 'statut', 'pays']
    list_filter = ['type_partenaire', 'statut']
    search_fields = ['nom', 'sigle', 'email']


@admin.register(Bailleur)
class BailleurAdmin(admin.ModelAdmin):
    list_display = ['sigle', 'nom', 'type_bailleur', 'pays_origine', 'actif']
    list_filter = ['type_bailleur', 'actif']
    search_fields = ['nom', 'sigle']


@admin.register(ComiteDirecteur)
class ComiteDirecteurAdmin(admin.ModelAdmin):
    list_display = ['intitule', 'organisation', 'date_tenue', 'statut']
    list_filter = ['statut', 'organisation']
    search_fields = ['intitule']
    filter_horizontal = ['participants']
