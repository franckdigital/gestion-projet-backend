"""
Service d'analyse financière par IA — modèles statistiques purs (sans ML externe).

Algorithmes implémentés :
  1. Régression linéaire pondérée sur les dépenses mensuelles
     (les mois récents ont un poids plus élevé)
  2. Détection de saisonnalité (volatilité inter-mensuelle)
  3. Simulation de 3 scénarios basée sur moyenne ± écart-type
  4. Analyse de variance budgétaire par catégorie de ligne
  5. Alertes précoces hiérarchisées avec sévérité
  6. Recommandations priorisées et actionnables
  7. Score de santé financière composite (0–100)
"""
import math
from collections import defaultdict

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone


# ─── Primitives statistiques (zéro dépendance externe) ──────────────────────

def _moy(vals):
    return sum(vals) / len(vals) if vals else 0.0


def _sigma(vals):
    if len(vals) < 2:
        return 0.0
    mu = _moy(vals)
    return math.sqrt(sum((v - mu) ** 2 for v in vals) / (len(vals) - 1))


def _regression_ponderee(xs, ys, poids=None):
    """
    Régression linéaire pondérée y = a·x + b (moindres carrés pondérés).
    Retourne (a, b).
    """
    n = len(xs)
    if n < 2:
        return 0.0, float(ys[0]) if ys else 0.0
    if poids is None:
        poids = [1.0] * n
    sw = sum(poids)
    swx = sum(poids[i] * xs[i] for i in range(n))
    swy = sum(poids[i] * ys[i] for i in range(n))
    swx2 = sum(poids[i] * xs[i] ** 2 for i in range(n))
    swxy = sum(poids[i] * xs[i] * ys[i] for i in range(n))
    denom = sw * swx2 - swx ** 2
    if abs(denom) < 1e-9:
        return 0.0, swy / sw
    a = (sw * swxy - swx * swy) / denom
    b = (swy - a * swx) / sw
    return a, b


def _r_squared(xs, ys, a, b):
    """Coefficient de détermination R² de la régression."""
    if not ys:
        return 0.0
    mu_y = _moy(ys)
    ss_tot = sum((y - mu_y) ** 2 for y in ys)
    ss_res = sum((ys[i] - (a * xs[i] + b)) ** 2 for i in range(len(xs)))
    return 1.0 - ss_res / ss_tot if ss_tot > 1e-9 else 1.0


# ─── Analyse principale ──────────────────────────────────────────────────────

def analyser(budgets_qs, depenses_qs, exercice: int) -> dict:
    """
    Analyse financière complète pour un exercice.

    Paramètres :
      budgets_qs  — QuerySet Budget (filtrés par exercice/projet/programme)
      depenses_qs — QuerySet Depense payées (filtrés de même)
      exercice    — int

    Retourne un dict structuré prêt pour la réponse API.
    """
    today = timezone.now()
    mois_ecoule = today.month  # 1 … 12

    # ── Totaux budget ────────────────────────────────────────────────────────
    total_initial = float(budgets_qs.aggregate(s=Sum('montant_initial'))['s'] or 0)
    total_revise = float(budgets_qs.aggregate(s=Sum('montant_revise'))['s'] or 0)
    total_budget = total_revise if total_revise else total_initial
    total_depense = float(budgets_qs.aggregate(s=Sum('montant_depense'))['s'] or 0)
    total_engage = float(budgets_qs.aggregate(s=Sum('montant_engage'))['s'] or 0)

    # ── Dépenses mensuelles réelles ──────────────────────────────────────────
    monthly_raw = (
        depenses_qs
        .annotate(_mois=TruncMonth('date_depense'))
        .values('_mois')
        .annotate(total=Sum('montant'))
        .order_by('_mois')
    )
    monthly = {r['_mois'].month: float(r['total'])
               for r in monthly_raw if r.get('_mois')}

    # ── Régression linéaire pondérée ─────────────────────────────────────────
    xs = sorted(monthly.keys())
    ys = [monthly[m] for m in xs]
    # Poids croissants : le dernier mois vaut le double du premier
    n_pts = len(xs)
    poids = [1.0 + (i / max(n_pts - 1, 1)) for i in range(n_pts)] if n_pts > 1 else [1.0]

    pente, intercept = _regression_ponderee(xs, ys, poids)
    r2 = _r_squared(xs, ys, pente, intercept) if n_pts >= 2 else None

    # Projections mois par mois (historique réel + extrapolation)
    projections_mensuelles = {}
    for m in range(1, 13):
        if m in monthly:
            projections_mensuelles[m] = monthly[m]
        elif m <= mois_ecoule:
            projections_mensuelles[m] = 0.0
        else:
            projections_mensuelles[m] = max(0.0, round(pente * m + intercept, 2))

    projection_annuelle = sum(projections_mensuelles.values())
    depense_realisee = sum(monthly.get(m, 0.0) for m in range(1, mois_ecoule + 1))

    # ── Scénarios (optimiste / réaliste / pessimiste) ────────────────────────
    vals_mensuelles = list(monthly.values())
    mu = _moy(vals_mensuelles) if vals_mensuelles else (
        total_depense / max(mois_ecoule, 1)
    )
    sigma = _sigma(vals_mensuelles)
    mois_restants = 12 - mois_ecoule

    scenario_optimiste = round(depense_realisee + max(0, mu - sigma) * mois_restants, 2)
    scenario_realiste = round(depense_realisee + mu * mois_restants, 2)
    scenario_pessimiste = round(depense_realisee + (mu + sigma) * mois_restants, 2)

    # ── Taux d'exécution attendu vs réel ────────────────────────────────────
    taux_attendu = round(mois_ecoule / 12 * 100, 1)
    taux_reel = round(total_depense / total_budget * 100, 1) if total_budget else 0.0
    ecart_execution = round(taux_reel - taux_attendu, 1)

    # ── Analyse par catégorie (lignes budgétaires) ───────────────────────────
    analyse_categories = []
    for budget in budgets_qs.prefetch_related('lignes'):
        par_cat = defaultdict(lambda: {'prevu': 0.0, 'engage': 0.0, 'depense': 0.0})
        for ligne in budget.lignes.all():
            c = ligne.categorie
            par_cat[c]['prevu'] += float(ligne.montant_prevu)
            par_cat[c]['engage'] += float(ligne.montant_engage)
            par_cat[c]['depense'] += float(ligne.montant_depense)
        for cat, v in par_cat.items():
            taux_cat = round(v['depense'] / v['prevu'] * 100, 1) if v['prevu'] else 0.0
            ecart = round(v['engage'] - v['prevu'], 2)
            statut = (
                'depassement' if ecart > 0
                else 'sous_utilisation' if taux_cat < 15 and mois_ecoule > 5
                else 'normal'
            )
            analyse_categories.append({
                'categorie': cat,
                'budget_reference': budget.reference,
                'montant_prevu': v['prevu'],
                'montant_engage': v['engage'],
                'montant_depense': v['depense'],
                'taux_execution': taux_cat,
                'ecart_budget': ecart,
                'statut': statut,
            })

    # ── Alertes précoces ────────────────────────────────────────────────────
    alertes = []

    if total_budget and ecart_execution < -20:
        alertes.append({
            'code': 'EXEC_RETARD_CRITIQUE',
            'severite': 'haute',
            'message': (
                f"Exécution à {taux_reel}% vs {taux_attendu}% attendu "
                f"— retard de {abs(ecart_execution)} points au mois {mois_ecoule}."
            ),
            'impact': 'Risque de non-absorption des fonds disponibles.',
        })
    elif total_budget and ecart_execution < -10:
        alertes.append({
            'code': 'EXEC_RETARD',
            'severite': 'moyenne',
            'message': f"Légère sous-exécution : {taux_reel}% réel vs {taux_attendu}% attendu.",
            'impact': 'À surveiller pour éviter un retard cumulatif.',
        })

    if total_budget and scenario_pessimiste > total_budget * 1.05:
        surcharge = round((scenario_pessimiste / total_budget - 1) * 100, 1)
        alertes.append({
            'code': 'RISQUE_DEPASSEMENT',
            'severite': 'haute',
            'message': (
                f"Scénario défavorable : projection {scenario_pessimiste:,.0f} "
                f"({surcharge}% au-dessus du budget {total_budget:,.0f})."
            ),
            'impact': 'Un avenant budgétaire sera probablement nécessaire.',
        })
    elif total_budget and projection_annuelle > total_budget:
        alertes.append({
            'code': 'PROJECTION_DEPASSEMENT',
            'severite': 'moyenne',
            'message': (
                f"Projection par régression ({projection_annuelle:,.0f}) "
                f"dépasse le budget ({total_budget:,.0f}) de "
                f"{round(projection_annuelle - total_budget):,.0f}."
            ),
            'impact': 'Surveiller l\'évolution des dépenses les prochains mois.',
        })

    for cat_data in analyse_categories:
        if cat_data['statut'] == 'depassement':
            alertes.append({
                'code': 'CATEGORIE_DEPASSEE',
                'severite': 'haute',
                'message': (
                    f"[{cat_data['budget_reference']}] Catégorie « {cat_data['categorie']} » "
                    f"— dépassement de {cat_data['ecart_budget']:,.0f}."
                ),
                'impact': "Engagement excédentaire par rapport au montant prévu.",
            })
        if cat_data['statut'] == 'sous_utilisation':
            alertes.append({
                'code': 'SOUS_UTILISATION',
                'severite': 'faible',
                'message': (
                    f"[{cat_data['budget_reference']}] Catégorie « {cat_data['categorie']} » "
                    f"— seulement {cat_data['taux_execution']}% réalisé à M{mois_ecoule}."
                ),
                'impact': "Crédits sous-utilisés — réallocation possible.",
            })

    if total_engage > total_budget * 0.95 and total_depense < total_budget * 0.5:
        alertes.append({
            'code': 'SATURATION_ENGAGEMENTS',
            'severite': 'moyenne',
            'message': f"Engagements à {round(total_engage/total_budget*100, 1)}% du budget avec seulement {taux_reel}% dépensé.",
            'impact': 'Risque de blocage sur de nouvelles dépenses.',
        })

    # ── Recommandations priorisées ──────────────────────────────────────────
    recommandations = []
    codes_hauts = {a['code'] for a in alertes if a['severite'] == 'haute'}

    if 'RISQUE_DEPASSEMENT' in codes_hauts or 'PROJECTION_DEPASSEMENT' in codes_hauts:
        recommandations.append({
            'priorite': 1,
            'action': 'Émettre un avenant budgétaire',
            'detail': (
                'Le niveau de dépenses prévu risque de dépasser le budget approuvé. '
                'Initier un avenant avant la fin du trimestre.'
            ),
        })
    if 'EXEC_RETARD_CRITIQUE' in codes_hauts:
        recommandations.append({
            'priorite': 1 if not recommandations else 2,
            'action': 'Accélérer le plan de décaissement',
            'detail': (
                'Organiser une revue de portefeuille pour identifier les blocages '
                'opérationnels et administratifs.'
            ),
        })
    if 'CATEGORIE_DEPASSEE' in codes_hauts:
        recommandations.append({
            'priorite': 2,
            'action': 'Régulariser les lignes en dépassement',
            'detail': 'Procéder à des virements de crédits ou émettre un bon de révision.',
        })
    cat_sous_util = [a for a in alertes if a['code'] == 'SOUS_UTILISATION']
    if cat_sous_util:
        recommandations.append({
            'priorite': 3,
            'action': 'Réallouer les crédits sous-utilisés',
            'detail': (
                f"{len(cat_sous_util)} catégorie(s) en sous-utilisation peuvent "
                'financer des besoins urgents ou des activités supplémentaires.'
            ),
        })
    if 'SATURATION_ENGAGEMENTS' in {a['code'] for a in alertes}:
        recommandations.append({
            'priorite': 2,
            'action': 'Liquider les engagements en attente',
            'detail': 'Prioriser le paiement des fournisseurs pour libérer de la capacité d\'engagement.',
        })
    if not recommandations:
        recommandations.append({
            'priorite': 1,
            'action': 'Maintenir le rythme d\'exécution',
            'detail': 'Le budget s\'exécute conformément aux prévisions. Continuer le suivi mensuel.',
        })

    # ── Score de santé financière composite (0–100) ──────────────────────────
    score = 100
    for a in alertes:
        score -= {'haute': 20, 'moyenne': 10, 'faible': 3}.get(a['severite'], 5)
    score = max(0, min(100, score))
    risque = 'eleve' if score < 40 else 'moyen' if score < 70 else 'faible'

    return {
        'exercice': exercice,
        'mois_analyse': mois_ecoule,
        'score_sante': score,
        'risque_global': risque,
        'execution': {
            'taux_reel': taux_reel,
            'taux_attendu': taux_attendu,
            'ecart_points': ecart_execution,
            'total_budget': total_budget,
            'total_revise': total_revise,
            'total_depense': total_depense,
            'total_engage': total_engage,
            'solde_disponible': round(total_budget - total_engage, 2),
        },
        'regression': {
            'pente_mensuelle': round(pente, 2),
            'intercept': round(intercept, 2),
            'r_carre': round(r2, 4) if r2 is not None else None,
            'projection_annuelle': round(projection_annuelle, 2),
            'projections_par_mois': {str(m): round(v, 2) for m, v in projections_mensuelles.items()},
        },
        'scenarios': {
            'optimiste': scenario_optimiste,
            'realiste': scenario_realiste,
            'pessimiste': scenario_pessimiste,
            'budget_reference': total_budget,
            'ecart_realiste': round(scenario_realiste - total_budget, 2),
            'ecart_pessimiste': round(scenario_pessimiste - total_budget, 2),
        },
        'alertes': alertes,
        'analyse_categories': sorted(analyse_categories, key=lambda x: x['taux_execution']),
        'recommandations': sorted(recommandations, key=lambda x: x['priorite']),
    }
