"""
Seed données de démonstration pour le Lot 4 — Suivi-Évaluation :
  M17 : Indicateurs + Collectes + Alertes + Cibles par période
  M18 : Formulaires dynamiques + Champs + Soumissions
  M19 : Enquêtes + Sections + Questions + Réponses
  M20 : Cadre de résultats + Niveaux + Théorie du changement + Évaluations + Leçons

Usage : python manage.py seed_lot4 [--reset]
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# -- Indicateurs ----------------------------------------------------------------

# Mappage vers UNITE_CHOICES valides du modèle
# ('nombre','pourcentage','montant','taux','score','indice','autre')
def _unite(val):
    MAP = {'%': 'pourcentage', 'FCFA': 'montant'}
    return MAP.get(val, 'autre'), (val if val not in MAP else '')


INDICATEURS = [
    # Impact
    {
        'code': 'IND-IMP-001',
        'intitule': 'Taux de réduction de la pauvreté dans les zones cibles',
        'type': 'impact', 'unite': '%', 'frequence': 'annuelle', 'mode': 'manuel',
        'baseline': 45.0, 'cible': 30.0, 'realise': 38.5, 'statut': 'partiellement_atteint',
        'description': 'Proportion de ménages vivant sous le seuil de pauvreté dans les 45 villages d\'intervention.',
        'source': 'Enquête ménage annuelle – INS Côte d\'Ivoire',
        'collectes': [
            {'delta': -365, 'valeur': 45.0, 'statut': 'valide'},
            {'delta': -180, 'valeur': 42.3, 'statut': 'valide'},
            {'delta': -30,  'valeur': 38.5, 'statut': 'valide'},
        ],
    },
    {
        'code': 'IND-IMP-002',
        'intitule': 'Nombre d\'emplois créés par le programme',
        'type': 'impact', 'unite': 'Emplois', 'frequence': 'annuelle', 'mode': 'manuel',
        'baseline': 0, 'cible': 2500.0, 'realise': 820.0, 'statut': 'partiellement_atteint',
        'description': 'Emplois directs et indirects générés par les activités du programme.',
        'source': 'Rapports coopératives + enquête AGR',
        'collectes': [
            {'delta': -180, 'valeur': 450, 'statut': 'valide'},
            {'delta': -60,  'valeur': 680, 'statut': 'valide'},
            {'delta': -10,  'valeur': 820, 'statut': 'valide'},
        ],
    },
    # Résultats
    {
        'code': 'IND-RES-001',
        'intitule': 'Nombre d\'agents de santé communautaires formés',
        'type': 'resultat', 'unite': 'Agents', 'frequence': 'trimestrielle', 'mode': 'manuel',
        'baseline': 0, 'cible': 500.0, 'realise': 210.0, 'statut': 'en_cours',
        'description': 'Total des agents de santé communautaires ayant suivi et réussi la formation certifiante.',
        'source': 'Registre de formation + certificats émis',
        'collectes': [
            {'delta': -90, 'valeur': 85,  'statut': 'valide'},
            {'delta': -30, 'valeur': 125, 'statut': 'valide'},
            {'delta': -5,  'valeur': 210, 'statut': 'soumis'},
        ],
    },
    {
        'code': 'IND-RES-002',
        'intitule': 'Taux de couverture vaccinale DTP3 dans les zones cibles',
        'type': 'resultat', 'unite': '%', 'frequence': 'semestrielle', 'mode': 'formule',
        'baseline': 52.0, 'cible': 90.0, 'realise': 68.5, 'statut': 'en_cours',
        'description': 'Proportion d\'enfants de 0-23 mois ayant reçu les 3 doses de DTP dans les districts cibles.',
        'source': 'Système DHIS2 – District Sanitaire',
        'formule': '(Enfants vaccinés DTP3 / Total enfants cibles) × 100',
        'collectes': [
            {'delta': -180, 'valeur': 52.0, 'statut': 'valide'},
            {'delta': -60,  'valeur': 63.2, 'statut': 'valide'},
            {'delta': -10,  'valeur': 68.5, 'statut': 'valide'},
        ],
    },
    {
        'code': 'IND-RES-003',
        'intitule': 'Nombre de coopératives agricoles opérationnelles',
        'type': 'resultat', 'unite': 'Coopératives', 'frequence': 'semestrielle', 'mode': 'manuel',
        'baseline': 2, 'cible': 25.0, 'realise': 8.0, 'statut': 'partiellement_atteint',
        'description': 'Coopératives ayant reçu l\'agrément officiel et étant en activité réelle.',
        'source': 'Registre Ministère Agriculture + rapports terrain',
        'collectes': [
            {'delta': -90, 'valeur': 5, 'statut': 'valide'},
            {'delta': -20, 'valeur': 8, 'statut': 'valide'},
        ],
    },
    {
        'code': 'IND-RES-004',
        'intitule': 'Taux d\'alphabétisation des femmes adultes (18-45 ans)',
        'type': 'effet', 'unite': '%', 'frequence': 'annuelle', 'mode': 'formule',
        'baseline': 35.0, 'cible': 60.0, 'realise': 41.0, 'statut': 'en_cours',
        'description': 'Proportion de femmes adultes sachant lire et écrire dans les zones d\'intervention.',
        'source': 'Enquête alphabétisation – équipe programme',
        'formule': '(Femmes alphabétisées / Total femmes enquêtées) × 100',
        'collectes': [
            {'delta': -365, 'valeur': 35.0, 'statut': 'valide'},
            {'delta': -30,  'valeur': 41.0, 'statut': 'valide'},
        ],
    },
    # Indicateurs financiers
    {
        'code': 'IND-FIN-001',
        'intitule': 'Taux d\'exécution budgétaire global',
        'type': 'financier', 'unite': '%', 'frequence': 'mensuelle', 'mode': 'formule',
        'baseline': 0, 'cible': 95.0, 'realise': 58.3, 'statut': 'en_cours',
        'description': 'Rapport entre les dépenses réelles et le budget prévu pour la période.',
        'source': 'Système comptable – rapport financier mensuel',
        'formule': '(Dépenses réelles / Budget prévu) × 100',
        'collectes': [
            {'delta': -90, 'valeur': 22.5, 'statut': 'valide'},
            {'delta': -60, 'valeur': 38.7, 'statut': 'valide'},
            {'delta': -30, 'valeur': 49.2, 'statut': 'valide'},
            {'delta': -5,  'valeur': 58.3, 'statut': 'valide'},
        ],
    },
    {
        'code': 'IND-ACT-001',
        'intitule': 'Nombre de formations réalisées',
        'type': 'activite', 'unite': 'Sessions', 'frequence': 'mensuelle', 'mode': 'manuel',
        'baseline': 0, 'cible': 48.0, 'realise': 31.0, 'statut': 'en_cours',
        'description': 'Total de sessions de formation organisées sur toutes les composantes du programme.',
        'source': 'Registres de présence + rapports formation',
        'collectes': [
            {'delta': -60, 'valeur': 12, 'statut': 'valide'},
            {'delta': -30, 'valeur': 22, 'statut': 'valide'},
            {'delta': -5,  'valeur': 31, 'statut': 'valide'},
        ],
    },
    {
        'code': 'IND-ACT-002',
        'intitule': 'Nombre de bénéficiaires directs atteints',
        'type': 'resultat', 'unite': 'Personnes', 'frequence': 'trimestrielle', 'mode': 'manuel',
        'baseline': 0, 'cible': 150000.0, 'realise': 42800.0, 'statut': 'en_cours',
        'description': 'Nombre cumulé de bénéficiaires directs ayant bénéficié d\'au moins une activité du programme.',
        'source': 'Base de données KoboToolbox',
        'collectes': [
            {'delta': -120, 'valeur': 18500, 'statut': 'valide'},
            {'delta': -60,  'valeur': 31200, 'statut': 'valide'},
            {'delta': -10,  'valeur': 42800, 'statut': 'valide'},
        ],
    },
    {
        'code': 'IND-RES-005',
        'intitule': 'Taux de malnutrition aiguë chez les enfants < 5 ans',
        'type': 'effet', 'unite': '%', 'frequence': 'semestrielle', 'mode': 'manuel',
        'baseline': 14.2, 'cible': 8.0, 'realise': 11.5, 'statut': 'partiellement_atteint',
        'description': 'Prévalence de la malnutrition aiguë (PB < 125 mm) chez les enfants de 6-59 mois.',
        'source': 'Enquête SMART semestrielle',
        'collectes': [
            {'delta': -180, 'valeur': 14.2, 'statut': 'valide'},
            {'delta': -30,  'valeur': 11.5, 'statut': 'valide'},
        ],
    },
]

# -- Formulaires ----------------------------------------------------------------

FORMULAIRES = [
    {
        'titre': 'Fiche de suivi agent de santé communautaire',
        'description': 'Formulaire de suivi mensuel des activités des agents de santé communautaires dans les districts.',
        'statut': 'publie',
        'allow_offline': True, 'require_gps': True, 'require_photo': False,
        'champs': [
            {'libelle': 'Code de l\'agent', 'type': 'texte', 'ordre': 1, 'obligatoire': True},
            {'libelle': 'District sanitaire', 'type': 'choix_unique', 'ordre': 2, 'obligatoire': True, 'options': ['Abobo', 'Adjamé', 'Yopougon', 'Cocody', 'Autre']},
            {'libelle': 'Nombre de visites domiciliaires réalisées', 'type': 'nombre', 'ordre': 3, 'obligatoire': True},
            {'libelle': 'Nombre d\'enfants pesés', 'type': 'nombre', 'ordre': 4, 'obligatoire': True},
            {'libelle': 'Nombre de cas de malnutrition détectés', 'type': 'nombre', 'ordre': 5, 'obligatoire': True},
            {'libelle': 'Difficultés rencontrées', 'type': 'texte_long', 'ordre': 6, 'obligatoire': False},
            {'libelle': 'Photo du rapport papier', 'type': 'photo', 'ordre': 7, 'obligatoire': False},
            {'libelle': 'Localisation GPS', 'type': 'gps', 'ordre': 8, 'obligatoire': True},
            {'libelle': 'Date de la collecte', 'type': 'date', 'ordre': 9, 'obligatoire': True},
        ],
    },
    {
        'titre': 'Formulaire réception chantier centre de santé',
        'description': 'Fiche de réception provisoire des travaux de construction des centres de santé.',
        'statut': 'publie',
        'allow_offline': True, 'require_gps': True, 'require_photo': True,
        'champs': [
            {'libelle': 'Code du centre de santé', 'type': 'texte', 'ordre': 1, 'obligatoire': True},
            {'libelle': 'Localisation GPS du site', 'type': 'gps', 'ordre': 2, 'obligatoire': True},
            {'libelle': 'Taux d\'avancement des travaux (%)', 'type': 'nombre', 'ordre': 3, 'obligatoire': True},
            {'libelle': 'Conformité de la toiture', 'type': 'choix_unique', 'ordre': 4, 'obligatoire': True, 'options': ['Conforme', 'Non conforme', 'Partiellement conforme']},
            {'libelle': 'Conformité installation électrique', 'type': 'choix_unique', 'ordre': 5, 'obligatoire': True, 'options': ['Conforme', 'Non conforme', 'Partiellement conforme']},
            {'libelle': 'Réserves et non-conformités', 'type': 'texte_long', 'ordre': 6, 'obligatoire': False},
            {'libelle': 'Photos du chantier', 'type': 'photo', 'ordre': 7, 'obligatoire': True},
            {'libelle': 'Note globale de l\'avancement', 'type': 'nombre', 'ordre': 8, 'obligatoire': True},
        ],
    },
    {
        'titre': 'Fiche d\'enregistrement bénéficiaire AGR',
        'description': 'Enregistrement des bénéficiaires des activités génératrices de revenus.',
        'statut': 'brouillon',
        'allow_offline': True, 'require_gps': False, 'require_photo': False,
        'champs': [
            {'libelle': 'Nom complet', 'type': 'texte', 'ordre': 1, 'obligatoire': True},
            {'libelle': 'Âge', 'type': 'nombre', 'ordre': 2, 'obligatoire': True},
            {'libelle': 'Sexe', 'type': 'choix_unique', 'ordre': 3, 'obligatoire': True, 'options': ['Féminin', 'Masculin']},
            {'libelle': 'Village', 'type': 'texte', 'ordre': 4, 'obligatoire': True},
            {'libelle': 'Type d\'AGR pratiquée', 'type': 'choix_multiple', 'ordre': 5, 'obligatoire': True, 'options': ['Maraîchage', 'Élevage', 'Commerce', 'Transformation', 'Artisanat']},
            {'libelle': 'Revenu mensuel estimé (FCFA)', 'type': 'nombre', 'ordre': 6, 'obligatoire': False},
            {'libelle': 'A-t-il/elle bénéficié d\'un micro-crédit ?', 'type': 'choix_unique', 'ordre': 7, 'obligatoire': True, 'options': ['Oui', 'Non']},
        ],
    },
]

# -- Enquêtes -------------------------------------------------------------------

ENQUETES = [
    {
        'titre': 'Enquête de satisfaction – Programme PRCC 2026',
        'type': 'satisfaction',
        'statut': 'actif',
        'nb_reponses_attendues': 500,
        'objectifs': 'Mesurer le niveau de satisfaction des bénéficiaires avec les activités du programme PRCC.',
        'methodologie': 'Enquête par questionnaire auprès d\'un échantillon stratifié de 500 bénéficiaires dans les 3 régions.',
        'debut_delta': -30, 'fin_delta': 30,
        'sections': [
            {
                'titre': 'Informations générales',
                'questions': [
                    {'libelle': 'Dans quelle région êtes-vous ?', 'type': 'choix_unique', 'options': ['Abidjan', 'Bouaké', 'Korhogo']},
                    {'libelle': 'Êtes-vous un bénéficiaire direct du programme ?', 'type': 'choix_unique', 'options': ['Oui', 'Non']},
                    {'libelle': 'Depuis combien de temps êtes-vous bénéficiaire ?', 'type': 'choix_unique', 'options': ['< 6 mois', '6-12 mois', '> 1 an']},
                ],
            },
            {
                'titre': 'Satisfaction générale',
                'questions': [
                    {'libelle': 'Êtes-vous satisfait des formations reçues ?', 'type': 'likert'},
                    {'libelle': 'Les activités du programme répondent-elles à vos besoins ?', 'type': 'likert'},
                    {'libelle': 'Comment évaluez-vous la qualité de l\'accompagnement ?', 'type': 'note'},
                    {'libelle': 'Le programme a-t-il amélioré vos conditions de vie ?', 'type': 'choix_unique', 'options': ['Beaucoup', 'Un peu', 'Pas du tout']},
                ],
            },
            {
                'titre': 'Suggestions',
                'questions': [
                    {'libelle': 'Que recommanderiez-vous pour améliorer le programme ?', 'type': 'texte_long'},
                    {'libelle': 'Avez-vous d\'autres besoins non couverts par le programme ?', 'type': 'texte_long'},
                ],
            },
        ],
    },
    {
        'titre': 'Enquête baseline – Indicateurs nutrition 2026',
        'type': 'baseline',
        'statut': 'ferme',
        'nb_reponses_attendues': 1200,
        'objectifs': 'Établir les valeurs de référence des indicateurs nutritionnels pour le suivi de l\'impact du programme.',
        'methodologie': 'Enquête SMART auprès de 1 200 ménages – échantillonnage systématique.',
        'debut_delta': -180, 'fin_delta': -120,
        'sections': [
            {
                'titre': 'Anthropométrie enfants 0-59 mois',
                'questions': [
                    {'libelle': 'Poids de l\'enfant (kg)', 'type': 'nombre'},
                    {'libelle': 'Taille de l\'enfant (cm)', 'type': 'nombre'},
                    {'libelle': 'Périmètre brachial (mm)', 'type': 'nombre'},
                    {'libelle': 'Œdèmes bilatéraux présents ?', 'type': 'choix_unique', 'options': ['Oui', 'Non']},
                ],
            },
            {
                'titre': 'Pratiques ANJE',
                'questions': [
                    {'libelle': 'L\'enfant a-t-il été allaité exclusivement jusqu\'à 6 mois ?', 'type': 'choix_unique', 'options': ['Oui', 'Non', 'Ne sait pas']},
                    {'libelle': 'Nombre de repas par jour pour l\'enfant', 'type': 'nombre'},
                    {'libelle': 'Diversité alimentaire (score sur 8)', 'type': 'nombre'},
                ],
            },
        ],
    },
    {
        'titre': 'Enquête d\'évaluation mi-parcours – Impact AGR',
        'type': 'impact',
        'statut': 'brouillon',
        'nb_reponses_attendues': 300,
        'objectifs': 'Mesurer l\'impact des activités AGR sur les revenus et les conditions de vie des bénéficiaires.',
        'methodologie': 'Enquête comparative avant/après auprès des membres des coopératives.',
        'debut_delta': 15, 'fin_delta': 60,
        'sections': [
            {
                'titre': 'Revenus et activités économiques',
                'questions': [
                    {'libelle': 'Revenu mensuel moyen (FCFA)', 'type': 'nombre'},
                    {'libelle': 'Activités génératrices de revenus pratiquées', 'type': 'choix_multiple', 'options': ['Maraîchage', 'Élevage', 'Commerce', 'Transformation', 'Artisanat', 'Autre']},
                    {'libelle': 'Vos revenus ont-ils augmenté depuis votre adhésion à la coopérative ?', 'type': 'choix_unique', 'options': ['Oui, beaucoup', 'Oui, un peu', 'Non', 'Impossible à dire']},
                    {'libelle': 'Taux d\'augmentation estimé des revenus (%)', 'type': 'nombre'},
                ],
            },
        ],
    },
]

# -- Cadre de résultats ---------------------------------------------------------

CADRE_RESULTATS_NIVEAUX = [
    # Impact
    {'code': 'IMP-01', 'niveau': 'impact', 'intitule': 'Réduction durable de la pauvreté et amélioration du bien-être des communautés des zones d\'intervention', 'taux': 28, 'parent': None, 'ordre': 1},
    # Effets
    {'code': 'EFF-01', 'niveau': 'effet', 'intitule': 'Amélioration de l\'état nutritionnel et sanitaire des populations cibles', 'taux': 45, 'parent': 'IMP-01', 'ordre': 1},
    {'code': 'EFF-02', 'niveau': 'effet', 'intitule': 'Augmentation durable des revenus des ménages ruraux', 'taux': 22, 'parent': 'IMP-01', 'ordre': 2},
    {'code': 'EFF-03', 'niveau': 'effet', 'intitule': 'Amélioration de l\'accès à une éducation de qualité', 'taux': 35, 'parent': 'IMP-01', 'ordre': 3},
    # Résultats
    {'code': 'RES-01', 'niveau': 'resultat', 'intitule': '500 agents de santé communautaires formés et opérationnels', 'taux': 42, 'parent': 'EFF-01', 'ordre': 1},
    {'code': 'RES-02', 'niveau': 'resultat', 'intitule': '8 centres de santé construits et équipés', 'taux': 50, 'parent': 'EFF-01', 'ordre': 2},
    {'code': 'RES-03', 'niveau': 'resultat', 'intitule': 'Couverture DTP3 portée à 90% dans les 5 districts', 'taux': 68, 'parent': 'EFF-01', 'ordre': 3},
    {'code': 'RES-04', 'niveau': 'resultat', 'intitule': '25 coopératives agricoles viables opérationnelles', 'taux': 32, 'parent': 'EFF-02', 'ordre': 1},
    {'code': 'RES-05', 'niveau': 'resultat', 'intitule': '1 500 femmes rurales formées en entrepreneuriat', 'taux': 20, 'parent': 'EFF-02', 'ordre': 2},
    {'code': 'RES-06', 'niveau': 'resultat', 'intitule': '5 000 enfants scolarisés dans les zones rurales', 'taux': 40, 'parent': 'EFF-03', 'ordre': 1},
    {'code': 'RES-07', 'niveau': 'resultat', 'intitule': '500 femmes adultes alphabétisées', 'taux': 25, 'parent': 'EFF-03', 'ordre': 2},
]

# -- Évaluations ----------------------------------------------------------------

EVALUATIONS = [
    {
        'titre': 'Évaluation initiale – Analyse de la situation de départ PRCC',
        'type': 'initiale', 'statut': 'validee',
        'debut_delta': -400, 'fin_delta': -360,
        'note': 3.5,
        'objectifs': 'Analyser la situation initiale dans les zones d\'intervention et définir les valeurs de référence du programme.',
        'conclusions': 'La situation initiale révèle des besoins importants dans les domaines de la santé, nutrition, éducation et AGR. Les communautés ciblées présentent des indicateurs de développement en-deçà de la moyenne nationale.',
        'recommandations': 'Prioriser les activités de formation des ASC et de construction des centres de santé. Renforcer le volet AGR en ciblant spécifiquement les femmes-chefs de ménage.',
        'criteres': [
            {'c': 'pertinence', 'n': 5, 'obs': 'L\'intervention répond parfaitement aux besoins identifiés.', 'forts': 'Excellente connaissance du terrain et des communautés.', 'faibles': ''},
            {'c': 'coherence',  'n': 4, 'obs': 'Bonne cohérence avec les priorités nationales.', 'forts': 'Alignement avec la stratégie nationale de développement.', 'faibles': 'Quelques gaps dans la coordination intersectorielle.'},
        ],
    },
    {
        'titre': 'Évaluation à mi-parcours – Programme PRCC 2024-2025',
        'type': 'mi_parcours', 'statut': 'publiee',
        'debut_delta': -90, 'fin_delta': -50,
        'note': 3.8,
        'objectifs': 'Apprécier les performances du programme après 18 mois d\'exécution et orienter la phase 2.',
        'conclusions': 'Le programme atteint un taux d\'exécution physique de 65% (supérieur à la cible de 60%) mais un retard financier de 7 points. Les composantes santé et éducation progressent bien. La composante AGR accuse un retard dû aux délais d\'agrément des coopératives.',
        'recommandations': '1. Accélérer les procédures d\'agrément des coopératives avec les autorités\n2. Renforcer l\'appui technique au volet AGR\n3. Réviser les cibles de la composante gouvernance\n4. Maintenir le rythme des activités de santé communautaire',
        'criteres': [
            {'c': 'pertinence',  'n': 5, 'obs': 'Toujours très pertinent.', 'forts': 'Forte adhésion communautaire.', 'faibles': ''},
            {'c': 'efficacite',  'n': 4, 'obs': 'Bon niveau d\'atteinte des résultats à mi-parcours.', 'forts': '65% d\'exécution physique.', 'faibles': 'Retard composante AGR.'},
            {'c': 'efficience',  'n': 3, 'obs': 'Gestion budgétaire à améliorer.', 'forts': '', 'faibles': 'Sous-exécution financière de 7 points.'},
            {'c': 'impact',      'n': 3, 'obs': 'Effets précoces observés.', 'forts': 'Réduction malnutrition de 14.2% à 11.5%.', 'faibles': 'Trop tôt pour mesurer l\'impact.'},
            {'c': 'durabilite',  'n': 4, 'obs': 'Mécanismes de durabilité en place.', 'forts': 'Comités de gestion communautaires actifs.', 'faibles': ''},
            {'c': 'coherence',   'n': 4, 'obs': 'Bonne cohérence globale.', 'forts': 'Synergies avec les autres programmes.', 'faibles': ''},
        ],
    },
    {
        'titre': 'Évaluation de performance – Composante Santé Q1 2026',
        'type': 'intermediaire', 'statut': 'validee',
        'debut_delta': -45, 'fin_delta': -20,
        'note': 4.2,
        'objectifs': 'Évaluer spécifiquement les performances de la composante santé après 6 mois d\'activités intensives.',
        'conclusions': 'La composante santé atteint ses objectifs intermédiaires avec un taux de formation de 42% (210/500 agents) et un déploiement complet du système numérique de collecte dans les 5 districts.',
        'recommandations': 'Accélérer les sessions de formation (sessions 2 et 3) pour atteindre la cible annuelle de 500 agents. Renforcer le suivi des agents formés dans leurs communautés.',
        'criteres': [
            {'c': 'efficacite', 'n': 4, 'obs': '42% de la cible annuelle atteinte à mi-année.', 'forts': 'Qualité des formations validée.', 'faibles': 'Rythme à accélérer.'},
            {'c': 'efficience', 'n': 5, 'obs': 'Coût par agent formé en-dessous du budget.', 'forts': 'Optimisation logistique réussie.', 'faibles': ''},
        ],
    },
]

# -- Leçons apprises ------------------------------------------------------------

LECONS = [
    {
        'type': 'bonne_pratique',
        'titre': 'Formation en cascade avec agents multiplicateurs',
        'contexte': 'Composante santé – formation des agents de santé communautaires',
        'description': 'La stratégie de formation en cascade (former des formateurs locaux qui forment les agents) a permis d\'atteindre un plus grand nombre d\'agents à moindre coût, avec une meilleure appropriation locale des compétences.',
        'recommandation': 'Systématiser l\'approche multiplicateurs dans toutes les activités de formation du programme. Prévoir un budget spécifique pour la formation et le suivi des formateurs.',
        'domaine': 'Formation',
    },
    {
        'type': 'difficulte',
        'titre': 'Délais d\'agrément des coopératives agricoles',
        'contexte': 'Composante AGR – structuration des coopératives',
        'description': 'Les procédures administratives d\'agrément officiel des coopératives auprès du Ministère de l\'Agriculture ont pris 2 à 3 fois plus de temps que prévu (3-6 mois au lieu d\'1 mois estimé), créant un retard significant dans le démarrage des activités AGR.',
        'recommandation': 'Intégrer les délais administratifs réels dans la planification. Établir un partenariat formalisé avec le Ministère de l\'Agriculture dès la phase de conception du programme.',
        'domaine': 'AGR',
    },
    {
        'type': 'innovation',
        'titre': 'Utilisation de KoboToolbox pour la collecte hors ligne',
        'contexte': 'Système S&E – collecte de données terrain',
        'description': 'Le déploiement de l\'application KoboToolbox en mode hors ligne pour la collecte de données dans les zones sans connectivité a permis de collecter des données de qualité dans les villages les plus isolés, avec synchronisation lors des retours en zone couverte.',
        'recommandation': 'Étendre cette approche à tous les programmes de l\'organisation. Documenter le processus de configuration et former une équipe interne de super-utilisateurs.',
        'domaine': 'S&E',
    },
    {
        'type': 'recommandation',
        'titre': 'Impliquer les autorités locales dès la conception',
        'contexte': 'Gouvernance – coordination avec les collectivités',
        'description': 'L\'implication tardive des maires et présidents de conseils régionaux dans la conception des activités a généré des résistances et des retards dans certaines zones. Les activités co-conçues avec les autorités locales ont mieux démarré et sont mieux appropriées.',
        'recommandation': 'Organiser systématiquement des ateliers de co-conception avec les autorités locales avant le démarrage de chaque composante. Signature de protocoles de partenariat formels.',
        'domaine': 'Gouvernance',
    },
    {
        'type': 'lecon',
        'titre': 'Importance du suivi rapproché des agents terrain',
        'contexte': 'Supervision – agents de santé communautaires',
        'description': 'Les agents ayant bénéficié d\'une supervision mensuelle ont affiché des performances significativement supérieures (taux de visite +35%, qualité données +28%) par rapport aux agents supervisés trimestriellement.',
        'recommandation': 'Budgétiser la supervision mensuelle des agents terrain dans tous les projets futurs. Le coût supplémentaire est largement compensé par la meilleure performance.',
        'domaine': 'Santé',
    },
]

# -- Rapports S&E ---------------------------------------------------------------

RAPPORTS = [
    {
        'titre': 'Rapport S&E – Bilan Q1 2026 – Programme PRCC',
        'type': 'suivi_evaluation', 'periode': 'trimestriel',
        'statut': 'publie', 'date_delta': -45, 'ia': False,
        'resume': 'Le premier trimestre 2026 affiche un taux d\'exécution physique de 62%, supérieur à la cible de 58%. 210 agents de santé ont été formés, le système de suivi numérique est pleinement opérationnel, et les travaux de construction avancent à 48%.',
        'analyse': 'La composante santé progresse selon le planning. La composante AGR accuse un retard lié aux procédures d\'agrément des coopératives. La composante éducation est légèrement en avance grâce à la distribution précoce des kits scolaires.',
        'conclusions': 'Le programme est globalement sur la bonne trajectoire pour atteindre ses objectifs annuels. La qualité des données collectées s\'est améliorée avec le déploiement de KoboToolbox.',
        'recommandations': 'Accélérer les démarches d\'agrément des coopératives. Renforcer la supervision des agents de santé dans le district de Cocody en retard. Préparer les modalités de la revue à mi-parcours.',
        'prochaines': 'Revue à mi-parcours – Juin 2026\nRapport trimestriel Q2 – Juillet 2026\nÉvaluation composante AGR – Août 2026',
    },
    {
        'titre': 'Rapport de performance – Indicateurs S1 2026',
        'type': 'indicateurs', 'periode': 'semestriel',
        'statut': 'valide', 'date_delta': -10, 'ia': False,
        'resume': 'Analyse des 10 indicateurs clés du cadre de résultats pour le premier semestre 2026.',
        'analyse': '7 indicateurs sur 10 sont sur la bonne trajectoire. 3 indicateurs présentent des écarts : couverture DTP3 (68.5% vs 75% cible semestrielle), coopératives opérationnelles (8 vs 15 cible), et taux alphabétisation (41% vs 48% cible).',
        'conclusions': 'Tendance globale positive mais vigilance nécessaire sur les 3 indicateurs en retard.',
        'recommandations': 'Plan de rattrapage pour les indicateurs AGR et alphabétisation. Mission de terrain pour accélérer la vaccination DTP3.',
        'prochaines': 'Actualisation indicateurs – Juillet 2026\nRevue avec bailleur – Août 2026',
    },
    {
        'titre': 'Rapport IA – Analyse prédictive des tendances Q3 2026',
        'type': 'performance', 'periode': 'trimestriel',
        'statut': 'brouillon', 'date_delta': 5, 'ia': True,
        'resume': 'Rapport généré automatiquement par le système IA basé sur l\'analyse des tendances des 6 derniers mois.',
        'analyse': 'L\'analyse prédictive des données S&E suggère que le programme est en bonne voie pour atteindre 78% de ses indicateurs annuels. Les projections pour Q3 indiquent une accélération probable de la composante santé avec les sessions de formation 2 et 3.',
        'conclusions': 'Projection optimiste pour le Q3 sous réserve de la résolution des blocages AGR.',
        'recommandations': 'Intervenir rapidement sur les 3 indicateurs en retard. Renforcer la collecte de données pour affiner les projections.',
        'prochaines': 'Validation rapport IA – Juillet 2026',
    },
]


class Command(BaseCommand):
    help = 'Seed données Lot 4 (S&E) — M17-M20 complets'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les données S&E avant de re-seeder')

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        with transaction.atomic():
            admin = self._get_admin()
            if not admin:
                self.stdout.write(self.style.ERROR('[ERREUR] Aucun admin. Lancez seed_lot1 d\'abord.'))
                return
            projet = self._get_projet()
            if not projet:
                self.stdout.write(self.style.ERROR('[ERREUR] Aucun projet. Lancez seed_projets d\'abord.'))
                return

            indicateurs = self._seed_indicateurs(admin, projet)
            self._seed_formulaires(admin, projet)
            self._seed_enquetes(admin, projet)
            cadre = self._seed_cadre_resultats(admin, projet)
            self._seed_evaluations(admin, projet)
            self._seed_lecons(admin, projet)
            self._seed_rapports(admin, projet)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed Lot 4 terminé !'))

    def _reset(self):
        from suivi_evaluation.models import (
            Indicateur, CollecteIndicateur, AlerteIndicateur,
            FormulaireDynamique, Enquete, CadreResultats,
            Evaluation, LeconApprise, RapportSE,
        )
        self.stdout.write(self.style.WARNING('[RESET] Suppression données S&E…'))
        RapportSE.objects.all().delete()
        LeconApprise.objects.all().delete()
        Evaluation.objects.all().delete()
        CadreResultats.objects.all().delete()
        Enquete.objects.all().delete()
        FormulaireDynamique.objects.all().delete()
        CollecteIndicateur.objects.all().delete()
        AlerteIndicateur.objects.all().delete()
        Indicateur.objects.all().delete()
        self.stdout.write('   Terminé.')

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_projet(self):
        from programmes_projets.models import Projet
        return Projet.objects.filter(statut='en_cours').first()

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Créé') if created else self.style.WARNING('Existe')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:80]}')

    # -- M17 : Indicateurs -----------------------------------------------------

    def _seed_indicateurs(self, admin, projet):
        from suivi_evaluation.models import Indicateur, CollecteIndicateur, AlerteIndicateur, ValeurCiblePeriode
        self.stdout.write('\n>> Indicateurs (M17)…')
        today = date.today()
        result = []

        for data in INDICATEURS:
            unite_mesure_val, unite_perso = _unite(data['unite'])

            ind, created = Indicateur.objects.get_or_create(
                code=data['code'],
                defaults={
                    'intitule': data['intitule'],
                    'description': data.get('description', ''),
                    'type_indicateur': data['type'],
                    'unite_mesure': unite_mesure_val,
                    'unite_personnalisee': unite_perso,
                    'frequence_collecte': data['frequence'],
                    'mode_calcul': data['mode'],
                    'formule': data.get('formule', ''),
                    'valeur_baseline': data.get('baseline'),
                    'valeur_cible_globale': data.get('cible'),
                    'valeur_realisee': data.get('realise'),
                    'statut': data['statut'],
                    'source_verification': data.get('source', ''),
                    'projet': projet,
                    'responsable_collecte': admin,
                    'responsable': admin,
                    'created_by': admin,
                }
            )
            self._log('Indicateur', ind, created)
            result.append(ind)

            if created:
                # Collectes
                for c in data.get('collectes', []):
                    dc = today + timedelta(days=c['delta'])
                    CollecteIndicateur.objects.create(
                        indicateur=ind,
                        date_collecte=dc,
                        valeur_reelle=c['valeur'],
                        statut=c['statut'],
                        collecteur=admin,
                        valide_par=admin if c['statut'] == 'valide' else None,
                        date_validation=timezone.now() if c['statut'] == 'valide' else None,
                        source_donnee=ind.source_verification,
                    )

                # Cibles par période (Q1, Q2, Q3, Q4)
                for q in range(1, 5):
                    ValeurCiblePeriode.objects.create(
                        indicateur=ind,
                        annee=today.year,
                        trimestre=q,
                        valeur_cible=data.get('cible', 0) * q / 4 if data.get('cible') else 0,
                        valeur_realisee=data.get('realise', 0) if q <= 2 else None,
                    )

                # Alerte si non atteint
                if ind.statut in ('non_atteint', 'partiellement_atteint'):
                    AlerteIndicateur.objects.create(
                        indicateur=ind,
                        type_alerte='cible_non_atteinte',
                        niveau='warning' if ind.statut == 'partiellement_atteint' else 'critique',
                        message=f"L'indicateur {ind.code} est en dessous de sa cible : {ind.valeur_realisee} / {ind.valeur_cible_globale} {ind.unite_mesure}",
                        destinataire=admin,
                    )

        return result

    # -- M18 : Formulaires -----------------------------------------------------

    def _seed_formulaires(self, admin, projet):
        from suivi_evaluation.models import FormulaireDynamique, ChampFormulaire
        self.stdout.write('\n>> Formulaires (M18)…')

        for data in FORMULAIRES:
            form, created = FormulaireDynamique.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'description': data['description'],
                    'statut': data['statut'],
                    'allow_offline': data['allow_offline'],
                    'require_gps': data['require_gps'],
                    'require_photo': data['require_photo'],
                    'projet': projet,
                    'created_by': admin,
                }
            )
            self._log('Formulaire', form, created)

            if created:
                for ch in data['champs']:
                    opts = ch.get('options', [])
                    ChampFormulaire.objects.create(
                        formulaire=form,
                        type_champ=ch['type'],
                        libelle=ch['libelle'],
                        ordre=ch['ordre'],
                        obligatoire=ch['obligatoire'],
                        options=opts if isinstance(opts, list) else [],
                    )
                    self.stdout.write(f'    + Champ [{ch["type"]}]: {ch["libelle"][:50]}')

    # -- M19 : Enquêtes --------------------------------------------------------

    def _seed_enquetes(self, admin, projet):
        from suivi_evaluation.models import Enquete, SectionEnquete, QuestionEnquete
        self.stdout.write('\n>> Enquêtes (M19)…')
        today = date.today()

        for data in ENQUETES:
            enq, created = Enquete.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'type_enquete': data['type'],
                    'statut': data['statut'],
                    'nb_reponses_attendues': data['nb_reponses_attendues'],
                    'objectifs': data['objectifs'],
                    'methodologie': data['methodologie'],
                    'date_debut': today + timedelta(days=data['debut_delta']),
                    'date_fin': today + timedelta(days=data['fin_delta']),
                    'projet': projet,
                    'responsable': admin,
                    'created_by': admin,
                    'allow_anonymous': True,
                    'canaux': ['web', 'mobile'],
                }
            )
            self._log('Enquête', enq, created)

            if created:
                for i, sec_data in enumerate(data['sections']):
                    sec = SectionEnquete.objects.create(
                        enquete=enq, titre=sec_data['titre'], ordre=i + 1
                    )
                    self.stdout.write(f'    + Section: {sec.titre}')
                    for j, q_data in enumerate(sec_data['questions']):
                        opts = q_data.get('options', [])
                        QuestionEnquete.objects.create(
                            enquete=enq,
                            section=sec,
                            libelle=q_data['libelle'],
                            type_question=q_data['type'],
                            obligatoire=True,
                            ordre=j + 1,
                            options=opts if isinstance(opts, list) else [],
                        )

    # -- M20 : Cadre de résultats -----------------------------------------------

    def _seed_cadre_resultats(self, admin, projet):
        from suivi_evaluation.models import CadreResultats, NiveauResultat, TheorieChangement
        self.stdout.write('\n>> Cadre de résultats (M20)…')

        cadre, created = CadreResultats.objects.get_or_create(
            projet=projet,
            defaults={
                'titre': f'Cadre de résultats — {projet.code}',
                'description': 'Cadre hiérarchique des résultats du Programme PRCC.',
                'version': '2.0',
                'created_by': admin,
                'valide_par': admin,
                'date_validation': timezone.now(),
            }
        )
        self._log('Cadre de résultats', cadre, created)

        if created:
            # Créer les niveaux
            code_to_obj = {}
            for n in CADRE_RESULTATS_NIVEAUX:
                parent = code_to_obj.get(n['parent']) if n['parent'] else None
                niv = NiveauResultat.objects.create(
                    cadre=cadre,
                    parent=parent,
                    niveau=n['niveau'],
                    code=n['code'],
                    intitule=n['intitule'],
                    taux_avancement=n['taux'],
                    ordre=n['ordre'],
                )
                code_to_obj[n['code']] = niv
                self.stdout.write(f'    + Niveau [{n["niveau"]}]: {n["code"]} — {n["intitule"][:50]}')

            # Théorie du changement
            tc, _ = TheorieChangement.objects.get_or_create(
                projet=projet,
                defaults={
                    'titre': 'Théorie du changement — Programme PRCC',
                    'contexte': 'Les communautés rurales de Côte d\'Ivoire font face à des défis multidimensionnels : pauvreté, insécurité alimentaire, accès limité aux services de santé et d\'éducation. Le PRCC intervient dans ce contexte pour catalyser des changements durables.',
                    'probleme_central': 'Vulnérabilité chronique des communautés rurales : faible accès aux services sociaux de base, faibles revenus, malnutrition infantile élevée et faible accès à l\'éducation.',
                    'vision_changement': 'D\'ici 2028, les 150 000 bénéficiaires du programme vivent dans des communautés résilientes avec un accès équitable aux services de santé, d\'éducation et des opportunités économiques durables.',
                    'hypotheses_changement': '1. Si les agents de santé sont formés et soutenus, ils améliorent les pratiques nutritionnelles et sanitaires\n2. Si les femmes ont accès à des AGR viables, leurs revenus augmentent et améliorent le bien-être du ménage\n3. Si les coopératives sont structurées et appuyées, elles accèdent aux marchés et améliorent les revenus\n4. Si les communautés sont impliquées dans la gouvernance, les services publics s\'améliorent',
                    'facteurs_risque': '1. Instabilité politique et sécuritaire dans certaines zones\n2. Chocs climatiques (sécheresses, inondations)\n3. Résistances culturelles aux changements de pratiques\n4. Turnover du personnel clé du programme',
                    'version': '1.0',
                    'created_by': admin,
                }
            )
            self.stdout.write(f'    + Théorie du changement créée')

        return cadre

    # -- M20 : Évaluations -----------------------------------------------------

    def _seed_evaluations(self, admin, projet):
        from suivi_evaluation.models import Evaluation, CritereEvaluation
        self.stdout.write('\n>> Évaluations (M20)…')
        today = date.today()

        for data in EVALUATIONS:
            eval_, created = Evaluation.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'type_evaluation': data['type'],
                    'statut': data['statut'],
                    'date_debut': today + timedelta(days=data['debut_delta']),
                    'date_fin': today + timedelta(days=data['fin_delta']),
                    'note_globale': data.get('note'),
                    'description': data.get('objectifs', ''),
                    'conclusions': data.get('conclusions', ''),
                    'recommandations': data.get('recommandations', ''),
                    'projet': projet,
                    'responsable': admin,
                    'created_by': admin,
                }
            )
            self._log('Évaluation', eval_, created)

            if created:
                for c in data.get('criteres', []):
                    CritereEvaluation.objects.create(
                        evaluation=eval_,
                        critere=c['c'],
                        note=c['n'],
                        observation=c.get('obs', ''),
                        points_forts=c.get('forts', ''),
                        points_faibles=c.get('faibles', ''),
                    )
                    self.stdout.write(f'    + Critère [{c["c"]}]: {c["n"]}/5')

    # -- M20 : Leçons apprises -------------------------------------------------

    def _seed_lecons(self, admin, projet):
        from suivi_evaluation.models import LeconApprise
        self.stdout.write('\n>> Leçons apprises…')

        for data in LECONS:
            lecon, created = LeconApprise.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'type_lecon': data['type'],
                    'contexte': data.get('contexte', ''),
                    'description': data.get('description', ''),
                    'recommandation': data.get('recommandation', ''),
                    'domaine': data.get('domaine', ''),
                    'projet': projet,
                    'auteur': admin,
                    'statut': 'valide',
                    'valide_par': admin,
                }
            )
            self._log('Leçon', lecon, created)

    # -- Rapports S&E ----------------------------------------------------------

    def _seed_rapports(self, admin, projet):
        from suivi_evaluation.models import RapportSE
        self.stdout.write('\n>> Rapports S&E…')
        today = date.today()

        for data in RAPPORTS:
            rpt, created = RapportSE.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'type_rapport': data['type'],
                    'periode': data['periode'],
                    'statut': data['statut'],
                    'date_rapport': today + timedelta(days=data['date_delta']),
                    'synthese': data.get('resume', ''),
                    'principales_realisations': data.get('analyse', ''),
                    'contenu': data.get('conclusions', ''),
                    'recommandations': data.get('recommandations', ''),
                    'perspectives': data.get('prochaines', ''),
                    'projet': projet,
                    'redacteur': admin,
                    'genere_par_ia': data.get('ia', False),
                    'valide_par': admin if data['statut'] in ('valide', 'publie') else None,
                    'date_validation': timezone.now() if data['statut'] in ('valide', 'publie') else None,
                }
            )
            self._log('Rapport S&E', rpt, created)
