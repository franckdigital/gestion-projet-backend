from django.contrib import admin
from .models import (
    Partenaire, ContactPartenaire, LiaisonProjetPartenaire,
    Convention, RenouvellementConvention,
    AccesPortailPartenaire, DepotDocumentPortail,
)


# ─── M39 : Partenaires ────────────────────────────────────────────────────────

class ContactPartenaireInline(admin.TabularInline):
    model = ContactPartenaire
    extra = 0
    fields = ['nom', 'prenom', 'role', 'email', 'telephone', 'est_principal']


class LiaisonProjetPartenaireInline(admin.TabularInline):
    model = LiaisonProjetPartenaire
    extra = 0
    fields = ['projet', 'role', 'montant_finance', 'date_debut', 'date_fin']


@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = ['sigle', 'nom', 'type_partenaire', 'statut', 'pays', 'ville', 'email', 'created_at']
    list_filter = ['type_partenaire', 'statut', 'pays']
    search_fields = ['nom', 'sigle', 'email', 'contact_principal', 'ville']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ContactPartenaireInline, LiaisonProjetPartenaireInline]
    fieldsets = (
        ('Identification', {
            'fields': ('nom', 'sigle', 'type_partenaire', 'statut', 'logo', 'description')
        }),
        ('Localisation', {
            'fields': ('pays', 'ville', 'adresse', 'latitude', 'longitude')
        }),
        ('Coordonnées', {
            'fields': ('site_web', 'email', 'telephone',
                       'contact_principal', 'email_contact', 'telephone_contact')
        }),
        ('Compléments', {
            'fields': ('secteurs_intervention', 'notes', 'cree_par')
        }),
        ('Méta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ContactPartenaire)
class ContactPartenaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'partenaire', 'role', 'email', 'telephone', 'est_principal']
    list_filter = ['role', 'est_principal']
    search_fields = ['nom', 'prenom', 'email', 'partenaire__nom']
    raw_id_fields = ['partenaire']


@admin.register(LiaisonProjetPartenaire)
class LiaisonProjetPartenaireAdmin(admin.ModelAdmin):
    list_display = ['partenaire', 'projet', 'role', 'montant_finance', 'date_debut', 'date_fin']
    list_filter = ['role']
    search_fields = ['partenaire__nom', 'projet__titre']
    raw_id_fields = ['partenaire', 'projet']


# ─── M40 : Conventions ────────────────────────────────────────────────────────

class RenouvellementConventionInline(admin.TabularInline):
    model = RenouvellementConvention
    extra = 0
    fields = ['nouvelle_date_fin', 'nouveau_montant', 'motif', 'date_signature', 'effectue_par', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Convention)
class ConventionAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'intitule', 'type_convention', 'statut',
        'partenaire', 'montant', 'devise',
        'date_signature', 'date_fin', 'responsable', 'created_at',
    ]
    list_filter = ['type_convention', 'statut', 'devise']
    search_fields = ['reference', 'intitule', 'objet', 'partenaire__nom', 'signataire_externe']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    raw_id_fields = ['partenaire', 'programme', 'projet', 'signataire_interne', 'responsable', 'document_ged']
    inlines = [RenouvellementConventionInline]
    fieldsets = (
        ('Identification', {
            'fields': ('reference', 'intitule', 'type_convention', 'statut')
        }),
        ('Rattachements', {
            'fields': ('partenaire', 'programme', 'projet')
        }),
        ('Objet & Montant', {
            'fields': ('objet', 'montant', 'devise')
        }),
        ('Dates', {
            'fields': ('date_signature', 'date_debut', 'date_fin', 'date_expiration_alerte')
        }),
        ('Signataires', {
            'fields': ('signataire_interne', 'signataire_externe')
        }),
        ('Contenu', {
            'fields': ('clauses_principales', 'obligations_parties', 'conditions_renouvellement')
        }),
        ('Documents', {
            'fields': ('fichier', 'document_ged')
        }),
        ('Suivi', {
            'fields': ('responsable', 'notes')
        }),
        ('Méta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(RenouvellementConvention)
class RenouvellementConventionAdmin(admin.ModelAdmin):
    list_display = ['convention', 'nouvelle_date_fin', 'nouveau_montant', 'effectue_par', 'created_at']
    search_fields = ['convention__reference', 'convention__intitule']
    readonly_fields = ['created_at']
    raw_id_fields = ['convention', 'effectue_par']


# ─── M44 : Portail partenaire ────────────────────────────────────────────────

@admin.register(AccesPortailPartenaire)
class AccesPortailPartenaireAdmin(admin.ModelAdmin):
    list_display = [
        'partenaire', 'utilisateur', 'niveau_acces', 'statut',
        'date_debut', 'date_fin', 'accorde_par', 'created_at',
    ]
    list_filter = ['niveau_acces', 'statut']
    search_fields = ['partenaire__nom', 'utilisateur__email']
    raw_id_fields = ['partenaire', 'utilisateur', 'accorde_par']
    filter_horizontal = ['projets_accessibles', 'programmes_accessibles']
    readonly_fields = ['created_at']


@admin.register(DepotDocumentPortail)
class DepotDocumentPortailAdmin(admin.ModelAdmin):
    list_display = [
        'partenaire', 'titre', 'type_document', 'statut',
        'depose_par', 'valide_par', 'date_validation', 'created_at',
    ]
    list_filter = ['statut', 'type_document']
    search_fields = ['titre', 'description', 'partenaire__nom']
    raw_id_fields = ['partenaire', 'projet', 'depose_par', 'valide_par']
    readonly_fields = ['date_validation', 'created_at']
    fieldsets = (
        ('Document', {
            'fields': ('partenaire', 'projet', 'titre', 'description', 'fichier', 'type_document')
        }),
        ('Statut & Validation', {
            'fields': ('statut', 'depose_par', 'valide_par', 'date_validation', 'motif_rejet')
        }),
        ('Méta', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
