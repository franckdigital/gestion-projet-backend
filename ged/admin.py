from django.contrib import admin
from .models import (
    Categorie, Document, VersionDocument, DossierDocument,
    WorkflowValidation, SignatureElectronique, LienPartage, AccesDocument,
    AuditDocument, CommentaireDocument,
    PlanConservation, BoiteArchive, DocumentArchive, DemandeDestruction,
    ModeleDocument, EntreesBibliotheque,
)


# ─── Plan de classement ───────────────────────────────────────────────────────

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'domaine', 'parent', 'ordre', 'actif', 'duree_conservation_ans']
    list_filter = ['domaine', 'actif']
    search_fields = ['nom', 'code']


# ─── M24 : Documents ─────────────────────────────────────────────────────────

class VersionDocumentInline(admin.TabularInline):
    model = VersionDocument
    extra = 0
    fields = ['numero_version', 'fichier', 'commentaire', 'modifie_par', 'date_version']
    readonly_fields = ['date_version']


class WorkflowValidationInline(admin.TabularInline):
    model = WorkflowValidation
    extra = 0
    fields = ['ordre', 'validateur', 'role_validateur', 'statut', 'date_validation']
    readonly_fields = ['date_validation']


class SignatureInline(admin.TabularInline):
    model = SignatureElectronique
    extra = 0
    fields = ['ordre', 'signataire', 'type_signature', 'statut', 'date_signature']
    readonly_fields = ['date_signature', 'empreinte']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['reference', 'titre', 'type_document', 'statut', 'confidentialite',
                    'version', 'est_version_courante', 'categorie', 'auteur',
                    'type_fichier', 'ocr_effectue', 'created_at']
    list_filter = ['type_document', 'statut', 'confidentialite', 'langue', 'ocr_effectue']
    search_fields = ['reference', 'titre', 'mots_cles', 'texte_ocr']
    readonly_fields = ['reference', 'empreinte_sha256', 'ocr_effectue', 'date_ocr',
                       'created_at', 'updated_at', 'horodatage']
    inlines = [VersionDocumentInline, WorkflowValidationInline, SignatureInline]
    fieldsets = (
        ('Identification', {'fields': ('reference', 'titre', 'description', 'type_document',
                                       'categorie', 'confidentialite', 'langue', 'statut')}),
        ('Rattachements ERP', {'fields': ('programme', 'projet', 'activite')}),
        ('Fichier', {'fields': ('fichier', 'url_externe', 'type_fichier', 'taille_fichier',
                                'empreinte_sha256', 'version', 'est_version_courante',
                                'document_parent')}),
        ('Métadonnées', {'fields': ('mots_cles', 'source', 'auteur_externe', 'auteur', 'tags')}),
        ('OCR', {'fields': ('ocr_effectue', 'date_ocr', 'texte_ocr')}),
        ('IA', {'fields': ('resume_auto', 'mots_cles_auto', 'categorie_suggeree', 'score_doublon')}),
        ('Archivage', {'fields': ('date_expiration', 'date_archivage',
                                   'date_destruction_prevue', 'horodatage')}),
        ('Validation', {'fields': ('valide_par', 'date_validation', 'notes')}),
        ('Méta', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(VersionDocument)
class VersionDocumentAdmin(admin.ModelAdmin):
    list_display = ['document', 'numero_version', 'modifie_par', 'date_version']
    readonly_fields = ['date_version']


@admin.register(DossierDocument)
class DossierDocumentAdmin(admin.ModelAdmin):
    list_display = ['nom', 'parent', 'projet', 'programme', 'responsable', 'confidentiel']
    filter_horizontal = ['documents']


@admin.register(WorkflowValidation)
class WorkflowValidationAdmin(admin.ModelAdmin):
    list_display = ['document', 'ordre', 'validateur', 'role_validateur', 'statut', 'date_validation']
    list_filter = ['statut']
    readonly_fields = ['date_validation']


@admin.register(SignatureElectronique)
class SignatureElectroniqueAdmin(admin.ModelAdmin):
    list_display = ['document', 'signataire', 'type_signature', 'statut', 'date_signature', 'ordre']
    list_filter = ['type_signature', 'statut']
    readonly_fields = ['empreinte', 'date_signature', 'created_at']


@admin.register(LienPartage)
class LienPartageAdmin(admin.ModelAdmin):
    list_display = ['document', 'token', 'email_destinataire', 'actif',
                    'nb_telechargements', 'date_expiration', 'created_at']
    list_filter = ['actif']
    readonly_fields = ['token', 'nb_telechargements', 'created_at']


@admin.register(AuditDocument)
class AuditDocumentAdmin(admin.ModelAdmin):
    list_display = ['document', 'action', 'utilisateur', 'ip_address', 'created_at']
    list_filter = ['action']
    readonly_fields = ['created_at']


# ─── M25 : Archivage ─────────────────────────────────────────────────────────

@admin.register(PlanConservation)
class PlanConservationAdmin(admin.ModelAdmin):
    list_display = ['categorie', 'duree_active_ans', 'duree_intermediaire_ans',
                    'duree_totale_ans', 'sort_final']


class DocumentArchiveInline(admin.TabularInline):
    model = DocumentArchive
    extra = 0
    fields = ['document', 'reference_archive', 'date_archivage', 'archive_par']
    readonly_fields = ['date_archivage', 'horodatage_legal']


@admin.register(BoiteArchive)
class BoiteArchiveAdmin(admin.ModelAdmin):
    list_display = ['reference', 'intitule', 'statut', 'service_producteur',
                    'annee_debut', 'annee_fin', 'chiffree', 'created_at']
    list_filter = ['statut', 'chiffree']
    search_fields = ['reference', 'intitule']
    readonly_fields = ['reference', 'created_at']
    inlines = [DocumentArchiveInline]


@admin.register(DemandeDestruction)
class DemandeDestructionAdmin(admin.ModelAdmin):
    list_display = ['id', 'statut', 'propose_par', 'date_proposition',
                    'valide_par', 'autorise_par', 'date_execution']
    list_filter = ['statut']
    filter_horizontal = ['documents']
    readonly_fields = ['date_proposition', 'created_at']


# ─── Bibliothèque ─────────────────────────────────────────────────────────────

@admin.register(ModeleDocument)
class ModeleDocumentAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_modele', 'langue', 'version', 'actif', 'nb_utilisations']
    list_filter = ['type_modele', 'langue', 'actif']
    search_fields = ['titre', 'description']
    readonly_fields = ['nb_utilisations', 'created_at', 'updated_at']


@admin.register(EntreesBibliotheque)
class EntreeBibliothequeAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'langue', 'est_public', 'nb_telechargements', 'created_at']
    list_filter = ['categorie', 'langue', 'est_public']
    search_fields = ['titre', 'description', 'mots_cles']
    readonly_fields = ['nb_telechargements', 'created_at']
