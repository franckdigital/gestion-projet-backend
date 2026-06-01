from django.contrib import admin
from .models import (
    Budget, RevisionBudgetaire, LigneBudgetaire,
    BudgetProjet, LigneBudgetaireLegacy, DepenseLegacy,
    Fournisseur, Depense, Avance, Engagement,
    Convention, TrancheFinancement, Cofinancement, RapportBailleur,
    PlanTresorerie, LigneTresorerie, RapportFinancier,
)


# ─── M21 : Budgets ────────────────────────────────────────────────────────────

class LigneBudgetaireInline(admin.TabularInline):
    model = LigneBudgetaire
    extra = 0
    fields = ['code', 'libelle', 'categorie', 'montant_prevu', 'montant_engage', 'montant_depense']
    readonly_fields = ['montant_engage', 'montant_depense']


class RevisionInline(admin.TabularInline):
    model = RevisionBudgetaire
    extra = 0
    fields = ['numero_revision', 'date_revision', 'motif', 'montant_avant', 'montant_apres', 'valide_par']
    readonly_fields = ['date_revision']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['reference', 'type_budget', 'exercice', 'statut', 'devise',
                    'montant_initial', 'montant_depense', 'projet', 'programme']
    list_filter = ['type_budget', 'statut', 'exercice', 'devise']
    search_fields = ['reference', 'intitule']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [LigneBudgetaireInline, RevisionInline]
    fieldsets = (
        ('Identification', {'fields': ('reference', 'type_budget', 'exercice', 'intitule', 'devise')}),
        ('Rattachements', {'fields': ('projet', 'programme')}),
        ('Montants', {'fields': ('montant_initial', 'montant_revise', 'montant_engage', 'montant_depense')}),
        ('Workflow', {'fields': ('statut', 'soumis_par', 'date_soumission',
                                 'valide_finance_par', 'date_validation_finance',
                                 'approuve_par', 'date_approbation', 'motif_rejet')}),
        ('Méta', {'fields': ('notes', 'created_by', 'created_at', 'updated_at')}),
    )


@admin.register(LigneBudgetaire)
class LigneBudgetaireAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'categorie', 'budget',
                    'montant_prevu', 'montant_engage', 'montant_depense']
    list_filter = ['categorie', 'budget__exercice']
    search_fields = ['code', 'libelle']


@admin.register(RevisionBudgetaire)
class RevisionBudgetaireAdmin(admin.ModelAdmin):
    list_display = ['budget', 'numero_revision', 'date_revision', 'montant_avant', 'montant_apres']
    readonly_fields = ['date_revision', 'created_at']


# ─── M22 : Fournisseurs et Dépenses ──────────────────────────────────────────

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'type_fournisseur', 'pays', 'email', 'telephone', 'actif']
    list_filter = ['type_fournisseur', 'actif', 'pays']
    search_fields = ['code', 'nom', 'email']
    readonly_fields = ['code', 'created_at']


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ['reference', 'libelle', 'type_depense', 'statut', 'montant', 'devise',
                    'date_depense', 'fournisseur', 'projet']
    list_filter = ['type_depense', 'statut', 'mode_paiement', 'devise']
    search_fields = ['reference', 'libelle', 'numero_piece']
    readonly_fields = ['reference', 'montant_base', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {'fields': ('reference', 'libelle', 'description', 'type_depense')}),
        ('Rattachements', {'fields': ('ligne_budgetaire', 'projet', 'activite', 'fournisseur')}),
        ('Montant', {'fields': ('montant', 'devise', 'taux_change', 'montant_base')}),
        ('Paiement', {'fields': ('date_depense', 'date_paiement', 'mode_paiement',
                                  'type_piece', 'numero_piece', 'justificatif')}),
        ('Workflow', {'fields': ('statut', 'saisi_par', 'valide_responsable_par',
                                  'valide_finance_par', 'approuve_par', 'date_approbation',
                                  'motif_rejet')}),
        ('Méta', {'fields': ('notes', 'created_at', 'updated_at')}),
    )


@admin.register(Avance)
class AvanceAdmin(admin.ModelAdmin):
    list_display = ['reference', 'type_avance', 'statut', 'montant', 'devise',
                    'montant_justifie', 'beneficiaire', 'date_accord', 'date_limite_justification']
    list_filter = ['type_avance', 'statut', 'devise']
    search_fields = ['reference', 'motif']
    readonly_fields = ['reference', 'created_at']


@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ['reference', 'type_engagement', 'libelle', 'statut', 'montant',
                    'montant_liquide', 'fournisseur', 'date_engagement', 'date_echeance']
    list_filter = ['type_engagement', 'statut', 'devise']
    search_fields = ['reference', 'libelle']
    readonly_fields = ['reference', 'created_at', 'updated_at']


# ─── M23 : Conventions ────────────────────────────────────────────────────────

class TrancheFinancementInline(admin.TabularInline):
    model = TrancheFinancement
    extra = 0
    fields = ['numero', 'libelle', 'montant_prevu', 'montant_recu', 'pourcentage',
              'date_prevue', 'date_reception', 'statut']
    readonly_fields = ['created_at']


class CofinancementInline(admin.TabularInline):
    model = Cofinancement
    extra = 0
    fields = ['bailleur', 'montant', 'devise', 'pourcentage', 'montant_recu']


@admin.register(Convention)
class ConventionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'intitule', 'type_convention', 'statut', 'bailleur',
                    'montant_total', 'montant_recu', 'devise', 'date_debut', 'date_fin']
    list_filter = ['type_convention', 'statut', 'devise']
    search_fields = ['reference', 'intitule']
    readonly_fields = ['reference', 'created_at', 'updated_at']
    inlines = [TrancheFinancementInline, CofinancementInline]
    fieldsets = (
        ('Identification', {'fields': ('reference', 'type_convention', 'intitule', 'statut')}),
        ('Rattachements', {'fields': ('bailleur', 'programme', 'projet', 'responsable')}),
        ('Période', {'fields': ('date_signature', 'date_debut', 'date_fin')}),
        ('Montants', {'fields': ('montant_total', 'devise', 'montant_recu')}),
        ('Conditions', {'fields': ('conditions_particulieres', 'rapport_exige',
                                   'frequence_rapport', 'fichier_convention')}),
        ('Méta', {'fields': ('notes', 'created_by', 'created_at', 'updated_at')}),
    )


@admin.register(TrancheFinancement)
class TrancheFinancementAdmin(admin.ModelAdmin):
    list_display = ['convention', 'numero', 'libelle', 'montant_prevu', 'montant_recu',
                    'pourcentage', 'statut', 'date_prevue', 'date_reception']
    list_filter = ['statut']


@admin.register(RapportBailleur)
class RapportBailleurAdmin(admin.ModelAdmin):
    list_display = ['reference', 'titre', 'type_rapport', 'convention', 'statut',
                    'periode_debut', 'periode_fin', 'redacteur']
    list_filter = ['type_rapport', 'statut']
    readonly_fields = ['reference', 'created_at']


# ─── Trésorerie ───────────────────────────────────────────────────────────────

class LigneTresorerieInline(admin.TabularInline):
    model = LigneTresorerie
    extra = 0
    fields = ['type_flux', 'categorie', 'libelle', 'mois', 'annee',
              'montant_prevu', 'montant_realise']


@admin.register(PlanTresorerie)
class PlanTresorerieAdmin(admin.ModelAdmin):
    list_display = ['exercice', 'periode', 'projet', 'programme', 'devise', 'created_at']
    list_filter = ['exercice', 'periode']
    inlines = [LigneTresorerieInline]
    readonly_fields = ['created_at', 'updated_at']


# ─── Rapport financier ────────────────────────────────────────────────────────

@admin.register(RapportFinancier)
class RapportFinancierAdmin(admin.ModelAdmin):
    list_display = ['reference', 'titre', 'type_rapport', 'periode', 'date_rapport',
                    'statut', 'taux_execution', 'genere_par_ia', 'redacteur']
    list_filter = ['type_rapport', 'statut', 'periode', 'genere_par_ia']
    search_fields = ['reference', 'titre']
    readonly_fields = ['reference', 'created_at', 'updated_at']


# ─── Legacy ───────────────────────────────────────────────────────────────────

@admin.register(BudgetProjet)
class BudgetProjetAdmin(admin.ModelAdmin):
    list_display = ['projet', 'exercice', 'montant_initial', 'statut']
    list_filter = ['statut', 'exercice']
