from django.contrib import admin
from .models import (
    CourrierEntrant, CourrierSortant,
    CircuitValidation, EtapeCircuit, Parapheur, VisaParapheur, Diligence,
)


class DiligenceInline(admin.TabularInline):
    model = Diligence
    extra = 0
    fields = ['type_diligence', 'description', 'responsable', 'echeance', 'statut']


@admin.register(CourrierEntrant)
class CourrierEntrantAdmin(admin.ModelAdmin):
    list_display = ['numero', 'objet', 'expediteur', 'date_reception', 'urgence',
                    'canal', 'statut', 'affecte_a', 'ocr_effectue']
    list_filter = ['urgence', 'canal', 'statut', 'ocr_effectue']
    search_fields = ['numero', 'expediteur', 'objet', 'texte_ocr']
    readonly_fields = ['numero', 'created_at', 'updated_at']
    inlines = [DiligenceInline]


@admin.register(CourrierSortant)
class CourrierSortantAdmin(admin.ModelAdmin):
    list_display = ['reference', 'type_courrier', 'objet', 'destinataire',
                    'date_courrier', 'statut', 'redacteur', 'signataire']
    list_filter = ['type_courrier', 'statut']
    search_fields = ['reference', 'objet', 'destinataire', 'corps']
    readonly_fields = ['reference', 'created_at', 'updated_at', 'date_signature']


class EtapeCircuitInline(admin.TabularInline):
    model = EtapeCircuit
    extra = 0
    fields = ['ordre', 'nom_etape', 'validateur', 'role', 'obligatoire', 'delai_jours']


@admin.register(CircuitValidation)
class CircuitValidationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'est_actif', 'created_at']
    inlines = [EtapeCircuitInline]


class VisaInline(admin.TabularInline):
    model = VisaParapheur
    extra = 0
    fields = ['ordre', 'validateur', 'decision', 'commentaire', 'date_visa']
    readonly_fields = ['date_visa']


@admin.register(Parapheur)
class ParapheurAdmin(admin.ModelAdmin):
    list_display = ['reference', 'intitule', 'statut', 'etape_courante', 'soumis_par', 'date_soumission']
    list_filter = ['statut']
    readonly_fields = ['reference', 'date_soumission']
    inlines = [VisaInline]


@admin.register(Diligence)
class DiligenceAdmin(admin.ModelAdmin):
    list_display = ['courrier', 'type_diligence', 'responsable', 'echeance', 'statut']
    list_filter = ['type_diligence', 'statut']
