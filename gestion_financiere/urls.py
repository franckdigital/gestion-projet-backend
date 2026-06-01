from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BudgetViewSet, LigneBudgetaireViewSet, RevisionBudgetaireViewSet,
    FournisseurViewSet, DepenseViewSet, AvanceViewSet, EngagementViewSet,
    ConventionViewSet, TrancheFinancementViewSet, CofinancementViewSet,
    RapportBailleurViewSet, PlanTresorerieViewSet, LigneTresorerieViewSet,
    RapportFinancierViewSet,
    CompteBancaireViewSet, MouvementBancaireViewSet, RapprochementBancaireViewSet,
    dashboard_financier, dashboard_tresorerie, analyse_ia_financiere,
    depassements_budgetaires,
)

router = DefaultRouter()

# M21 — Budget
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'lignes-budgetaires', LigneBudgetaireViewSet, basename='ligne-budgetaire')
router.register(r'revisions-budget', RevisionBudgetaireViewSet, basename='revision-budget')

# M22 — Dépenses
router.register(r'fournisseurs', FournisseurViewSet, basename='fournisseur')
router.register(r'depenses', DepenseViewSet, basename='depense')
router.register(r'avances', AvanceViewSet, basename='avance')
router.register(r'engagements', EngagementViewSet, basename='engagement')

# M23 — Conventions & Financements
router.register(r'conventions', ConventionViewSet, basename='convention')
router.register(r'tranches-financement', TrancheFinancementViewSet, basename='tranche-financement')
router.register(r'cofinancements', CofinancementViewSet, basename='cofinancement')
router.register(r'rapports-bailleur', RapportBailleurViewSet, basename='rapport-bailleur')

# Trésorerie prévisionnelle
router.register(r'plans-tresorerie', PlanTresorerieViewSet, basename='plan-tresorerie')
router.register(r'lignes-tresorerie', LigneTresorerieViewSet, basename='ligne-tresorerie')

# Trésorerie avancée — Comptes bancaires
router.register(r'comptes-bancaires', CompteBancaireViewSet, basename='compte-bancaire')
router.register(r'mouvements-bancaires', MouvementBancaireViewSet, basename='mouvement-bancaire')
router.register(r'rapprochements-bancaires', RapprochementBancaireViewSet, basename='rapprochement-bancaire')

# Rapports financiers
router.register(r'rapports-financiers', RapportFinancierViewSet, basename='rapport-financier')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_financier, name='dashboard-financier'),
    path('dashboard/tresorerie/', dashboard_tresorerie, name='dashboard-tresorerie'),
    path('ia/analyse/', analyse_ia_financiere, name='analyse-ia-financiere'),
    path('depassements/', depassements_budgetaires, name='depassements-budgetaires'),
]
