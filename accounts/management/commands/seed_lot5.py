"""
Seed données de démonstration pour le Lot 5 — Gestion Financière :
  M21 : Budgets + Lignes budgétaires + Révisions
  M22 : Fournisseurs + Dépenses + Avances + Engagements
  M23 : Conventions + Tranches + Cofinancements + Rapports bailleur
  Trésorerie : Plans + Lignes
  Rapports financiers

Usage : python manage.py seed_lot5 [--reset]
"""
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# -- Données --------------------------------------------------------------------

FOURNISSEURS = [
    {
        'nom': 'Cabinet EXPERTISE CONSEIL CI',
        'type': 'consultant', 'pays': "Côte d'Ivoire",
        'email': 'contact@expertise-conseil.ci', 'telephone': '+225 27 20 31 45 67',
        'contact_principal': 'Dr. Kouassi Amon', 'numero_contribuable': 'A123456789',
        'banque': 'SGBCI', 'rib': 'CI20CI0010100120001234567',
    },
    {
        'nom': 'SOLIDAR TECH SARL',
        'type': 'entreprise', 'pays': "Côte d'Ivoire",
        'email': 'info@solidartech.ci', 'telephone': '+225 27 20 22 33 44',
        'contact_principal': 'M. Bamba Seydou', 'numero_contribuable': 'B987654321',
        'banque': 'BICICI', 'rib': 'CI20CI0020200229876543210',
    },
    {
        'nom': 'HEALTH SUPPLIES WEST AFRICA',
        'type': 'entreprise', 'pays': 'Ghana',
        'email': 'supply@hswa.gh', 'telephone': '+233 30 222 0000',
        'contact_principal': 'Mrs. Ama Owusu', 'numero_contribuable': 'GH-VAT-2024-789',
        'banque': 'Ghana Commercial Bank', 'rib': 'GH-GCB-0012345678',
    },
    {
        'nom': 'IMPRIMERIE NATIONALE CI',
        'type': 'administration', 'pays': "Côte d'Ivoire",
        'email': 'commandes@imprimerie-nat.ci', 'telephone': '+225 27 20 21 00 00',
        'contact_principal': 'Direction Commerciale', 'banque': 'Trésor Public', 'rib': 'TRESOR-001',
    },
    {
        'nom': 'TRANSPORT EXCELLENCE ABIDJAN',
        'type': 'entreprise', 'pays': "Côte d'Ivoire",
        'email': 'reza@tea-transport.ci', 'telephone': '+225 07 07 07 07 07',
        'contact_principal': 'Reza Ghahremani', 'banque': 'NSIA Banque', 'rib': 'CI20CI0050500512345678',
    },
    {
        'nom': 'Prof. Diallo Mamadou — Consultant Senior',
        'type': 'consultant', 'pays': 'Sénégal',
        'email': 'diallo.m@consulting.sn', 'telephone': '+221 77 123 45 67',
        'contact_principal': 'Prof. Diallo Mamadou',
    },
]

BUDGETS_DATA = [
    {
        'type': 'projet', 'exercice': 2026,
        'intitule': 'Budget opérationnel PRCC 2026 — Composante Santé',
        'montant_initial': 485_000_000, 'montant_revise': 520_000_000,
        'montant_engage': 198_500_000, 'montant_depense': 156_230_000,
        'statut': 'en_execution', 'devise': 'XOF',
        'lignes': [
            { 'code': '611', 'libelle': 'Honoraires consultants santé', 'categorie': 'honoraires', 'montant': 85_000_000, 'engage': 65_000_000, 'depense': 52_000_000 },
            { 'code': '612', 'libelle': 'Formations ASC (5 sessions)', 'categorie': 'formations', 'montant': 45_000_000, 'engage': 38_500_000, 'depense': 32_100_000 },
            { 'code': '613', 'libelle': 'Missions terrain districts', 'categorie': 'missions', 'montant': 28_000_000, 'engage': 18_000_000, 'depense': 15_430_000 },
            { 'code': '614', 'libelle': 'Équipements médicaux de base', 'categorie': 'equipements', 'montant': 120_000_000, 'engage': 48_000_000, 'depense': 38_700_000 },
            { 'code': '615', 'libelle': 'Fournitures de bureau et communication', 'categorie': 'fournitures', 'montant': 12_000_000, 'engage': 8_000_000, 'depense': 7_500_000 },
            { 'code': '616', 'libelle': 'Travaux réhabilitation centres de santé', 'categorie': 'travaux', 'montant': 195_000_000, 'engage': 21_000_000, 'depense': 10_500_000 },
        ],
    },
    {
        'type': 'projet', 'exercice': 2026,
        'intitule': 'Budget opérationnel PRCC 2026 — Composante AGR',
        'montant_initial': 320_000_000, 'montant_revise': 0,
        'montant_engage': 95_600_000, 'montant_depense': 72_450_000,
        'statut': 'en_execution', 'devise': 'XOF',
        'lignes': [
            { 'code': '621', 'libelle': 'Formation entrepreneuriat femmes', 'categorie': 'formations', 'montant': 55_000_000, 'engage': 45_000_000, 'depense': 38_000_000 },
            { 'code': '622', 'libelle': 'Fonds de garantie micro-crédits', 'categorie': 'autre', 'montant': 150_000_000, 'engage': 30_000_000, 'depense': 20_000_000 },
            { 'code': '623', 'libelle': 'Accompagnement coopératives', 'categorie': 'honoraires', 'montant': 65_000_000, 'engage': 15_600_000, 'depense': 12_450_000 },
            { 'code': '624', 'libelle': 'Matériel agricole et semences', 'categorie': 'equipements', 'montant': 50_000_000, 'engage': 5_000_000, 'depense': 2_000_000 },
        ],
    },
    {
        'type': 'programme', 'exercice': 2026,
        'intitule': 'Budget consolidé Programme PRCC 2026',
        'montant_initial': 1_250_000_000, 'montant_revise': 0,
        'montant_engage': 412_000_000, 'montant_depense': 298_750_000,
        'statut': 'approuve', 'devise': 'XOF',
        'lignes': [],
    },
    {
        'type': 'projet', 'exercice': 2025,
        'intitule': 'Budget PRCC 2025 — Exercice clôturé',
        'montant_initial': 450_000_000, 'montant_revise': 0,
        'montant_engage': 430_000_000, 'montant_depense': 425_000_000,
        'statut': 'cloture', 'devise': 'XOF',
        'lignes': [],
    },
]

DEPENSES_DATA = [
    {
        'libelle': 'Honoraires consultation Dr. Kouassi — Module nutrition ANJE',
        'type': 'projet', 'montant': 8_500_000, 'devise': 'XOF',
        'delta': -45, 'statut': 'paye', 'mode_paiement': 'virement',
        'type_piece': 'facture', 'numero_piece': 'FAC-2026-0142',
        'description': 'Consultation 10 jours pour développement module ANJE et formation formateurs.',
        'fournisseur_idx': 0,
    },
    {
        'libelle': 'Formation session 1 — 85 agents Abobo District',
        'type': 'formation', 'montant': 12_350_000, 'devise': 'XOF',
        'delta': -30, 'statut': 'paye', 'mode_paiement': 'cheque',
        'type_piece': 'bordereau', 'numero_piece': 'BOR-2026-0089',
        'fournisseur_idx': 1,
    },
    {
        'libelle': "Mission terrain — Districts Adjamé et Yopougon",
        'type': 'mission', 'montant': 3_250_000, 'devise': 'XOF',
        'delta': -20, 'statut': 'approuve', 'mode_paiement': 'especes',
        'type_piece': 'recu', 'numero_piece': 'REÇ-2026-0234',
        'fournisseur_idx': 4,
    },
    {
        'libelle': 'Lot équipements médicaux — Centres de santé Abobo',
        'type': 'investissement', 'montant': 38_700_000, 'devise': 'XOF',
        'delta': -15, 'statut': 'paye', 'mode_paiement': 'virement',
        'type_piece': 'facture', 'numero_piece': 'FAC-2026-0198',
        'fournisseur_idx': 2,
    },
    {
        'libelle': 'Fournitures bureau Q1 2026',
        'type': 'fonctionnement', 'montant': 1_850_000, 'devise': 'XOF',
        'delta': -10, 'statut': 'validation_finance', 'mode_paiement': 'mobile_money',
        'type_piece': 'recu', 'numero_piece': 'REÇ-2026-0312',
        'fournisseur_idx': 3,
    },
    {
        'libelle': 'Formation entrepreneuriat femmes — Batch 1',
        'type': 'formation', 'montant': 18_000_000, 'devise': 'XOF',
        'delta': -7, 'statut': 'paye', 'mode_paiement': 'virement',
        'type_piece': 'contrat', 'numero_piece': 'CTR-2026-0045',
        'fournisseur_idx': 5,
    },
    {
        'libelle': 'Impression supports pédagogiques ASC',
        'type': 'projet', 'montant': 2_150_000, 'devise': 'XOF',
        'delta': -3, 'statut': 'soumis', 'mode_paiement': 'cheque',
        'type_piece': 'bon_commande', 'numero_piece': 'BC-2026-0067',
        'fournisseur_idx': 3,
    },
    {
        'libelle': 'Carburant véhicules terrain — Mars 2026',
        'type': 'fonctionnement', 'montant': 985_000, 'devise': 'XOF',
        'delta': -1, 'statut': 'brouillon', 'mode_paiement': 'especes',
        'type_piece': 'recu', 'numero_piece': 'REÇ-2026-0401',
        'fournisseur_idx': 4,
    },
]

ENGAGEMENTS_DATA = [
    {
        'type': 'contrat', 'libelle': 'Contrat construction 8 centres de santé',
        'montant': 195_000_000, 'devise': 'XOF', 'montant_liquide': 45_000_000,
        'delta': -60, 'statut': 'en_cours', 'echeance_delta': 120,
        'fournisseur_idx': 1,
        'description': 'Contrat travaux construction et réhabilitation de 8 centres de santé communautaires dans 5 districts.',
    },
    {
        'type': 'bon_commande', 'libelle': 'BC équipements médicaux lot 2',
        'montant': 22_500_000, 'devise': 'XOF', 'montant_liquide': 0,
        'delta': -10, 'statut': 'approuve', 'echeance_delta': 45,
        'fournisseur_idx': 2,
        'description': 'Équipements médicaux pour les 4 centres restants : glucomètres, tensiomètres, balances pédiatriques.',
    },
    {
        'type': 'contrat', 'libelle': 'Contrat consultant senior formation multiplicateurs',
        'montant': 15_000_000, 'devise': 'XOF', 'montant_liquide': 15_000_000,
        'delta': -90, 'statut': 'liquide', 'echeance_delta': -10,
        'fournisseur_idx': 5,
        'description': 'Contrat 30 jours formation 20 formateurs-multiplicateurs ASC.',
    },
    {
        'type': 'demande_achat', 'libelle': 'DA matériel agricole coopératives',
        'montant': 8_500_000, 'devise': 'XOF', 'montant_liquide': 0,
        'delta': -5, 'statut': 'soumis', 'echeance_delta': 30,
        'fournisseur_idx': None,
        'description': 'Outils manuels et semences améliorées pour 5 coopératives pilotes.',
    },
]

AVANCES_DATA = [
    {
        'type': 'mission', 'motif': 'Mission terrain districts Nord — 10 jours',
        'montant': 450_000, 'devise': 'XOF',
        'delta': -25, 'statut': 'justifiee',
        'montant_justifie': 420_000, 'montant_rembourse': 30_000,
        'limite_delta': 10,
    },
    {
        'type': 'mission', 'motif': 'Atelier formation formateurs — Bouaké',
        'montant': 680_000, 'devise': 'XOF',
        'delta': -8, 'statut': 'partiellement_justifiee',
        'montant_justifie': 380_000, 'montant_rembourse': 0,
        'limite_delta': 15,
    },
    {
        'type': 'fournisseur', 'motif': 'Avance fournisseur équipements — HSWA',
        'montant': 10_000_000, 'devise': 'XOF',
        'delta': -45, 'statut': 'accordee',
        'montant_justifie': 0, 'montant_rembourse': 0,
        'limite_delta': 60,
        'fournisseur_idx': 2,
    },
    {
        'type': 'activite', 'motif': 'Avance organisation événement Journée Santé',
        'montant': 1_200_000, 'devise': 'XOF',
        'delta': -70, 'statut': 'non_justifiee',
        'montant_justifie': 0, 'montant_rembourse': 0,
        'limite_delta': -10,
    },
]

CONVENTIONS_DATA = [
    {
        'type': 'subvention', 'statut': 'active',
        'intitule': 'Convention de financement PRCC 2024-2028 — Union Européenne',
        'montant_total': 4_500_000_000, 'devise': 'XOF',
        'montant_recu': 2_250_000_000,
        'date_debut_delta': -540, 'date_fin_delta': 900,
        'date_sig_delta': -570,
        'frequence': 'Semestrielle', 'rapport_exige': True,
        'conditions': 'Rapports financiers semestriels. Audit annuel obligatoire. Respect des lignes directrices DEVCO.',
        'tranches': [
            { 'numero': 1, 'libelle': 'Tranche de démarrage', 'montant': 1_125_000_000, 'pct': 25, 'statut': 'recue', 'recu': 1_125_000_000, 'date_delta': -540 },
            { 'numero': 2, 'libelle': 'Tranche intermédiaire', 'montant': 1_125_000_000, 'pct': 25, 'statut': 'recue', 'recu': 1_125_000_000, 'date_delta': -180 },
            { 'numero': 3, 'libelle': 'Tranche de continuation', 'montant': 1_125_000_000, 'pct': 25, 'statut': 'prevue', 'recu': 0, 'date_delta': 90 },
            { 'numero': 4, 'libelle': 'Tranche finale', 'montant': 1_125_000_000, 'pct': 25, 'statut': 'prevue', 'recu': 0, 'date_delta': 360 },
        ],
        'rapports': [
            { 'type': 'financier', 'titre': 'Rapport financier semestriel S1 2025', 'statut': 'valide', 'debut_delta': -360, 'fin_delta': -180, 'taux': 43.2 },
            { 'type': 'financier', 'titre': 'Rapport financier semestriel S2 2025', 'statut': 'soumis', 'debut_delta': -180, 'fin_delta': -1, 'taux': 62.5 },
        ],
    },
    {
        'type': 'don', 'statut': 'active',
        'intitule': 'Accord de don AFD — Volet eau et assainissement',
        'montant_total': 850_000_000, 'devise': 'XOF',
        'montant_recu': 425_000_000,
        'date_debut_delta': -365, 'date_fin_delta': 730,
        'date_sig_delta': -390,
        'frequence': 'Trimestrielle', 'rapport_exige': True,
        'conditions': 'Rapports trimestriels. Passation des marchés selon code OHADA.',
        'tranches': [
            { 'numero': 1, 'libelle': '1ère tranche — 50%', 'montant': 425_000_000, 'pct': 50, 'statut': 'recue', 'recu': 425_000_000, 'date_delta': -365 },
            { 'numero': 2, 'libelle': '2ème tranche — 50%', 'montant': 425_000_000, 'pct': 50, 'statut': 'demandee', 'recu': 0, 'date_delta': 90 },
        ],
        'rapports': [],
    },
    {
        'type': 'cofinancement', 'statut': 'signee',
        'intitule': 'Accord de cofinancement USAID — Composante gouvernance',
        'montant_total': 620_000_000, 'devise': 'XOF',
        'montant_recu': 155_000_000,
        'date_debut_delta': -60, 'date_fin_delta': 1095,
        'date_sig_delta': -90,
        'frequence': 'Annuelle', 'rapport_exige': True,
        'conditions': 'Rapport annuel. Visite de terrain annuelle USAID/MEL.',
        'tranches': [
            { 'numero': 1, 'libelle': 'Tranche initiale 25%', 'montant': 155_000_000, 'pct': 25, 'statut': 'recue', 'recu': 155_000_000, 'date_delta': -60 },
            { 'numero': 2, 'libelle': 'Tranche 2 — 35%', 'montant': 217_000_000, 'pct': 35, 'statut': 'prevue', 'recu': 0, 'date_delta': 305 },
            { 'numero': 3, 'libelle': 'Tranche finale 40%', 'montant': 248_000_000, 'pct': 40, 'statut': 'prevue', 'recu': 0, 'date_delta': 730 },
        ],
        'rapports': [],
    },
]

RAPPORTS_FIN_DATA = [
    {
        'type': 'budgetaire', 'periode': 'trimestriel',
        'titre': 'Rapport budgétaire T1 2026 — Programme PRCC',
        'debut_delta': -90, 'fin_delta': -1, 'date_rapport_delta': -5,
        'statut': 'valide',
        'montant_budget': 1_250_000_000, 'montant_depense': 298_750_000, 'montant_engage': 412_000_000,
        'taux': 23.9,
        'contenu': 'Le T1 2026 affiche un taux d\'exécution de 23.9%, légèrement en deçà de la cible trimestrielle de 25%. Les retards observés sur la composante travaux sont compensés par une bonne performance de la composante formation.',
    },
    {
        'type': 'depenses', 'periode': 'mensuel',
        'titre': 'Rapport des dépenses — Février 2026',
        'debut_delta': -60, 'fin_delta': -31, 'date_rapport_delta': -28,
        'statut': 'publie',
        'montant_budget': 0, 'montant_depense': 45_285_000, 'montant_engage': 0,
        'taux': 0,
        'contenu': 'Dépenses du mois de février 2026. Principales dépenses : formation ASC (12.35M), équipements médicaux (38.7M), consultants (8.5M).',
    },
    {
        'type': 'tresorerie', 'periode': 'trimestriel',
        'titre': 'Rapport de trésorerie Q1 2026',
        'debut_delta': -90, 'fin_delta': -1, 'date_rapport_delta': -2,
        'statut': 'soumis',
        'montant_budget': 0, 'montant_depense': 0, 'montant_engage': 0,
        'taux': 0,
        'contenu': 'Analyse des flux de trésorerie du 1er trimestre 2026. Solde de trésorerie positif. Prochaine tranche AFD attendue en avril 2026.',
    },
    {
        'type': 'audit', 'periode': 'annuel',
        'titre': "Rapport d'audit exercice 2025",
        'debut_delta': -365, 'fin_delta': -1, 'date_rapport_delta': -30,
        'statut': 'valide',
        'montant_budget': 450_000_000, 'montant_depense': 425_000_000, 'montant_engage': 430_000_000,
        'taux': 94.4,
        'contenu': "L'audit 2025 n'a révélé aucune irrégularité majeure. Le taux d'exécution de 94.4% est conforme aux attentes. 2 recommandations mineures sur la traçabilité des avances ont été émises.",
    },
]

TRESORERIE_DATA = {
    'periode': 'mensuel', 'devise': 'XOF',
    'lignes': [
        # Flux entrants
        { 'type': 'entrant', 'cat': 'financement', 'libelle': 'Tranche UE — versement T2 2026', 'mois': 4, 'prevu': 562_500_000, 'realise': 0 },
        { 'type': 'entrant', 'cat': 'financement', 'libelle': 'Tranche AFD — versement T2 2026', 'mois': 4, 'prevu': 212_500_000, 'realise': 0 },
        { 'type': 'entrant', 'cat': 'recouvrement', 'libelle': 'Remboursement avance fournisseur HSWA', 'mois': 5, 'prevu': 10_000_000, 'realise': 0 },
        { 'type': 'entrant', 'cat': 'financement', 'libelle': 'Tranche USAID — versement Q3', 'mois': 7, 'prevu': 217_000_000, 'realise': 0 },
        { 'type': 'entrant', 'cat': 'remboursement_avance', 'libelle': 'Remboursements avances missions', 'mois': 6, 'prevu': 1_500_000, 'realise': 750_000 },
        # Flux réalisés mois précédents
        { 'type': 'entrant', 'cat': 'financement', 'libelle': 'Tranche UE reçue T1', 'mois': 1, 'prevu': 562_500_000, 'realise': 562_500_000 },
        { 'type': 'entrant', 'cat': 'financement', 'libelle': 'Tranche AFD reçue T1', 'mois': 1, 'prevu': 212_500_000, 'realise': 212_500_000 },
        # Flux sortants
        { 'type': 'sortant', 'cat': 'depense_projet', 'libelle': 'Paiements fournisseurs — Jan 2026', 'mois': 1, 'prevu': 65_000_000, 'realise': 58_230_000 },
        { 'type': 'sortant', 'cat': 'depense_projet', 'libelle': 'Paiements fournisseurs — Fév 2026', 'mois': 2, 'prevu': 75_000_000, 'realise': 45_285_000 },
        { 'type': 'sortant', 'cat': 'depense_projet', 'libelle': 'Paiements fournisseurs — Mar 2026', 'mois': 3, 'prevu': 80_000_000, 'realise': 52_700_000 },
        { 'type': 'sortant', 'cat': 'salaire', 'libelle': 'Salaires équipe PRCC — Jan-Mar', 'mois': 1, 'prevu': 18_000_000, 'realise': 18_000_000 },
        { 'type': 'sortant', 'cat': 'salaire', 'libelle': 'Salaires équipe PRCC — Fév', 'mois': 2, 'prevu': 18_000_000, 'realise': 18_000_000 },
        { 'type': 'sortant', 'cat': 'salaire', 'libelle': 'Salaires équipe PRCC — Mar', 'mois': 3, 'prevu': 18_000_000, 'realise': 18_000_000 },
        { 'type': 'sortant', 'cat': 'mission', 'libelle': 'Missions terrain T1', 'mois': 2, 'prevu': 8_500_000, 'realise': 6_200_000 },
        { 'type': 'sortant', 'cat': 'depense_projet', 'libelle': 'Acompte travaux centres santé', 'mois': 3, 'prevu': 45_000_000, 'realise': 45_000_000 },
        # Prévisions T2-T4
        { 'type': 'sortant', 'cat': 'depense_projet', 'libelle': 'Paiements fournisseurs — Avr 2026', 'mois': 4, 'prevu': 85_000_000, 'realise': 0 },
        { 'type': 'sortant', 'cat': 'depense_projet', 'libelle': 'Paiements fournisseurs — Mai-Jun', 'mois': 5, 'prevu': 90_000_000, 'realise': 0 },
        { 'type': 'sortant', 'cat': 'salaire', 'libelle': 'Salaires T2 2026', 'mois': 4, 'prevu': 54_000_000, 'realise': 0 },
        { 'type': 'sortant', 'cat': 'mission', 'libelle': 'Missions terrain T2', 'mois': 5, 'prevu': 12_000_000, 'realise': 0 },
    ],
}


class Command(BaseCommand):
    help = 'Seed Lot 5 — Gestion Financière complète (M21, M22, M23 + Trésorerie + Rapports)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les données financières existantes')

    def handle(self, *args, **options):
        admin = self._get_admin()
        if not admin:
            self.stdout.write(self.style.ERROR('[ERREUR] Aucun admin. Lancez seed_lot1 d\'abord.'))
            return
        projet = self._get_projet()
        if not projet:
            self.stdout.write(self.style.ERROR('[ERREUR] Aucun projet actif. Lancez seed_projets d\'abord.'))
            return
        bailleur = self._get_bailleur()
        if not bailleur:
            self.stdout.write(self.style.ERROR('[ERREUR] Aucun bailleur. Lancez seed_lot1 d\'abord.'))
            return

        self.stdout.write(f'[INFO] Projet : {projet.code} | Admin : {admin.email}')
        self.stdout.write(f'[INFO] Bailleur : {bailleur}')

        try:
            with transaction.atomic():
                if options['reset']:
                    self._reset()
                fournisseurs = self._seed_fournisseurs()
                budgets      = self._seed_budgets(admin, projet)
                self._seed_depenses(admin, projet, fournisseurs, budgets)
                self._seed_engagements(admin, fournisseurs, budgets)
                self._seed_avances(admin, projet, fournisseurs)
                self._seed_conventions(admin, projet, bailleur)
                self._seed_rapports(admin, projet)
                self._seed_tresorerie(admin, projet)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'[ERREUR] Transaction annulée : {exc}'))
            import traceback; traceback.print_exc()
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed Lot 5 terminé !'))

    # -- Helpers --------------------------------------------------------------

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_projet(self):
        from programmes_projets.models import Projet
        return Projet.objects.filter(statut='en_cours').first()

    def _get_bailleur(self):
        from gouvernance.models import Bailleur, Organisation
        b = Bailleur.objects.first()
        if not b:
            org = Organisation.objects.first()
            if not org:
                self.stdout.write(self.style.WARNING('[WARN] Aucune organisation — seed_lot1 requis pour créer un bailleur.'))
                return None
            b = Bailleur.objects.create(
                nom='Union Européenne', type_bailleur='international',
                pays_origine='Belgique', email='eu-delegation@ue.int',
                organisation=org,
            )
        return b

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Créé') if created else self.style.WARNING('Existe')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:80]}')

    def _reset(self):
        from gestion_financiere.models import (
            Budget, Fournisseur, Depense, Avance, Engagement,
            Convention, PlanTresorerie, RapportFinancier,
        )
        self.stdout.write(self.style.WARNING('[RESET] Suppression données financières…'))
        for Model in [RapportFinancier, PlanTresorerie, Convention, Engagement, Avance, Depense, Budget, Fournisseur]:
            n = Model.objects.all().delete()
            self.stdout.write(f'   {Model.__name__}: {n[0]} supprimé(s)')

    # -- M22 : Fournisseurs ----------------------------------------------------

    def _seed_fournisseurs(self):
        from gestion_financiere.models import Fournisseur
        self.stdout.write('\n>> Fournisseurs…')
        result = []
        for data in FOURNISSEURS:
            f, created = Fournisseur.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'type_fournisseur': data['type'],
                    'pays': data.get('pays', ''),
                    'email': data.get('email', ''),
                    'telephone': data.get('telephone', ''),
                    'contact_principal': data.get('contact_principal', ''),
                    'numero_contribuable': data.get('numero_contribuable', ''),
                    'banque': data.get('banque', ''),
                    'rib': data.get('rib', ''),
                    'actif': True,
                }
            )
            self._log('Fournisseur', f, created)
            result.append(f)
        return result

    # -- M21 : Budgets ---------------------------------------------------------

    def _seed_budgets(self, admin, projet):
        from gestion_financiere.models import Budget, LigneBudgetaire, RevisionBudgetaire
        self.stdout.write('\n>> Budgets (M21)…')
        result = []
        today = date.today()

        for data in BUDGETS_DATA:
            b, created = Budget.objects.get_or_create(
                intitule=data['intitule'],
                exercice=data['exercice'],
                defaults={
                    'type_budget': data['type'],
                    'projet': projet if data['type'] == 'projet' else None,
                    'devise': data['devise'],
                    'montant_initial': data['montant_initial'],
                    'montant_revise': data.get('montant_revise', 0),
                    'montant_engage': data['montant_engage'],
                    'montant_depense': data['montant_depense'],
                    'statut': data['statut'],
                    'created_by': admin,
                    'approuve_par': admin if data['statut'] in ('approuve', 'en_execution', 'cloture') else None,
                    'date_approbation': today if data['statut'] in ('approuve', 'en_execution', 'cloture') else None,
                }
            )
            self._log('Budget', b, created)

            if created and data.get('montant_revise'):
                RevisionBudgetaire.objects.create(
                    budget=b, numero_revision=1,
                    motif='Révision Q2 2026 — ajustement composante travaux',
                    montant_avant=data['montant_initial'],
                    montant_apres=data['montant_revise'],
                    valide_par=admin,
                )

            if created:
                for l in data.get('lignes', []):
                    LigneBudgetaire.objects.create(
                        budget=b,
                        code=l['code'],
                        libelle=l['libelle'],
                        categorie=l['categorie'],
                        montant_prevu=l['montant'],
                        montant_engage=l.get('engage', 0),
                        montant_depense=l.get('depense', 0),
                    )
                    self.stdout.write(f'    + Ligne [{l["code"]}] {l["libelle"][:50]}')

            result.append(b)
        return result

    # -- M22 : Dépenses --------------------------------------------------------

    def _seed_depenses(self, admin, projet, fournisseurs, budgets):
        from gestion_financiere.models import Depense, LigneBudgetaire
        self.stdout.write('\n>> Dépenses (M22)…')
        today = date.today()
        budget = budgets[0] if budgets else None

        for data in DEPENSES_DATA:
            libelle = data['libelle']
            if Depense.objects.filter(libelle=libelle).exists():
                self.stdout.write(self.style.WARNING(f'  [Existe] {libelle[:55]}'))
                continue

            four = fournisseurs[data['fournisseur_idx']] if data.get('fournisseur_idx') is not None else None
            dep_date = today + timedelta(days=data['delta'])

            # Trouver une ligne budgétaire si disponible
            ligne = None
            if budget:
                ligne = LigneBudgetaire.objects.filter(budget=budget).first()

            Depense.objects.create(
                libelle=libelle,
                type_depense=data['type'],
                montant=data['montant'],
                devise=data['devise'],
                date_depense=dep_date,
                date_paiement=dep_date + timedelta(days=3) if data['statut'] == 'paye' else None,
                mode_paiement=data['mode_paiement'],
                type_piece=data['type_piece'],
                numero_piece=data['numero_piece'],
                description=data.get('description', ''),
                statut=data['statut'],
                projet=projet,
                fournisseur=four,
                ligne_budgetaire=ligne,
                saisi_par=admin,
                valide_finance_par=admin if data['statut'] in ('validation_finance', 'approuve', 'paye') else None,
                approuve_par=admin if data['statut'] in ('approuve', 'paye') else None,
                date_approbation=timezone.now() if data['statut'] in ('approuve', 'paye') else None,
            )
            self.stdout.write(self.style.SUCCESS(f'  [Créé] Dépense: {libelle[:55]}'))

    # -- Engagements -----------------------------------------------------------

    def _seed_engagements(self, admin, fournisseurs, budgets):
        from gestion_financiere.models import Engagement, LigneBudgetaire
        self.stdout.write('\n>> Engagements…')
        today = date.today()
        budget = budgets[0] if budgets else None

        for data in ENGAGEMENTS_DATA:
            libelle = data['libelle']
            if Engagement.objects.filter(libelle=libelle).exists():
                self.stdout.write(self.style.WARNING(f'  [Existe] {libelle[:55]}'))
                continue

            four = fournisseurs[data['fournisseur_idx']] if data.get('fournisseur_idx') is not None else None
            ligne = None
            if budget:
                ligne = LigneBudgetaire.objects.filter(budget=budget).first()

            Engagement.objects.create(
                type_engagement=data['type'],
                libelle=libelle,
                description=data.get('description', ''),
                montant=data['montant'],
                devise=data['devise'],
                montant_liquide=data['montant_liquide'],
                date_engagement=today + timedelta(days=data['delta']),
                date_echeance=today + timedelta(days=data['echeance_delta']),
                statut=data['statut'],
                fournisseur=four,
                ligne_budgetaire=ligne,
                approuve_par=admin if data['statut'] in ('approuve', 'en_cours', 'liquide') else None,
                date_approbation=timezone.now() if data['statut'] in ('approuve', 'en_cours', 'liquide') else None,
                created_by=admin,
            )
            self.stdout.write(self.style.SUCCESS(f'  [Créé] Engagement: {libelle[:55]}'))

    # -- Avances ---------------------------------------------------------------

    def _seed_avances(self, admin, projet, fournisseurs):
        from gestion_financiere.models import Avance
        self.stdout.write('\n>> Avances…')
        today = date.today()

        for data in AVANCES_DATA:
            motif = data['motif']
            if Avance.objects.filter(motif=motif).exists():
                self.stdout.write(self.style.WARNING(f'  [Existe] {motif[:55]}'))
                continue

            four = fournisseurs[data['fournisseur_idx']] if data.get('fournisseur_idx') is not None else None

            Avance.objects.create(
                type_avance=data['type'],
                motif=motif,
                montant=data['montant'],
                devise=data['devise'],
                montant_justifie=data['montant_justifie'],
                montant_rembourse=data['montant_rembourse'],
                date_accord=today + timedelta(days=data['delta']),
                date_limite_justification=today + timedelta(days=data['limite_delta']),
                statut=data['statut'],
                projet=projet,
                fournisseur=four,
                accorde_par=admin,
                beneficiaire=admin,
            )
            self.stdout.write(self.style.SUCCESS(f'  [Créé] Avance: {motif[:55]}'))

    # -- M23 : Conventions -----------------------------------------------------

    def _seed_conventions(self, admin, projet, bailleur):
        from gestion_financiere.models import Convention, TrancheFinancement, RapportBailleur
        self.stdout.write('\n>> Conventions (M23)…')
        today = date.today()

        for data in CONVENTIONS_DATA:
            intitule = data['intitule']
            conv, created = Convention.objects.get_or_create(
                intitule=intitule,
                defaults={
                    'type_convention': data['type'],
                    'bailleur': bailleur,
                    'projet': projet,
                    'montant_total': data['montant_total'],
                    'devise': data['devise'],
                    'montant_recu': data['montant_recu'],
                    'statut': data['statut'],
                    'date_debut': today + timedelta(days=data['date_debut_delta']),
                    'date_fin': today + timedelta(days=data['date_fin_delta']),
                    'date_signature': today + timedelta(days=data['date_sig_delta']),
                    'frequence_rapport': data['frequence'],
                    'rapport_exige': data['rapport_exige'],
                    'conditions_particulieres': data['conditions'],
                    'responsable': admin,
                    'created_by': admin,
                }
            )
            self._log('Convention', conv, created)

            if created:
                for t in data.get('tranches', []):
                    TrancheFinancement.objects.create(
                        convention=conv,
                        numero=t['numero'],
                        libelle=t['libelle'],
                        montant_prevu=t['montant'],
                        montant_recu=t['recu'],
                        pourcentage=t['pct'],
                        statut=t['statut'],
                        date_prevue=today + timedelta(days=t['date_delta']),
                        date_reception=today + timedelta(days=t['date_delta']) if t['statut'] == 'recue' else None,
                    )
                    self.stdout.write(f'    + Tranche {t["numero"]}: {t["libelle"]} ({t["pct"]}%)')

                for r in data.get('rapports', []):
                    RapportBailleur.objects.create(
                        convention=conv,
                        type_rapport=r['type'],
                        titre=r['titre'],
                        statut=r['statut'],
                        periode_debut=today + timedelta(days=r['debut_delta']),
                        periode_fin=today + timedelta(days=r['fin_delta']),
                        taux_execution=r['taux'],
                        redacteur=admin,
                        valide_par=admin if r['statut'] == 'valide' else None,
                        date_validation=timezone.now() if r['statut'] == 'valide' else None,
                    )
                    self.stdout.write(self.style.SUCCESS(f'    + Rapport: {r["titre"][:50]}'))

    # -- Rapports financiers ---------------------------------------------------

    def _seed_rapports(self, admin, projet):
        from gestion_financiere.models import RapportFinancier
        self.stdout.write('\n>> Rapports financiers…')
        today = date.today()

        for data in RAPPORTS_FIN_DATA:
            titre = data['titre']
            r, created = RapportFinancier.objects.get_or_create(
                titre=titre,
                defaults={
                    'type_rapport': data['type'],
                    'periode': data['periode'],
                    'projet': projet,
                    'date_debut_periode': today + timedelta(days=data['debut_delta']),
                    'date_fin_periode': today + timedelta(days=data['fin_delta']),
                    'date_rapport': today + timedelta(days=data['date_rapport_delta']),
                    'statut': data['statut'],
                    'montant_budget': data['montant_budget'],
                    'montant_depense': data['montant_depense'],
                    'montant_engage': data['montant_engage'],
                    'taux_execution': data['taux'],
                    'contenu': data['contenu'],
                    'redacteur': admin,
                    'valide_par': admin if data['statut'] in ('valide', 'publie') else None,
                    'date_validation': timezone.now() if data['statut'] in ('valide', 'publie') else None,
                }
            )
            self._log('Rapport financier', r, created)

    # -- Plan de trésorerie ----------------------------------------------------

    def _seed_tresorerie(self, admin, projet):
        from gestion_financiere.models import PlanTresorerie, LigneTresorerie
        self.stdout.write('\n>> Plan de trésorerie…')
        exercice = date.today().year

        plan, created = PlanTresorerie.objects.get_or_create(
            projet=projet,
            exercice=exercice,
            defaults={
                'periode': TRESORERIE_DATA['periode'],
                'devise': TRESORERIE_DATA['devise'],
                'created_by': admin,
            }
        )
        self._log('Plan de trésorerie', plan, created)

        if created:
            for l in TRESORERIE_DATA['lignes']:
                LigneTresorerie.objects.create(
                    plan=plan,
                    type_flux=l['type'],
                    categorie=l['cat'],
                    libelle=l['libelle'],
                    mois=l['mois'],
                    annee=exercice,
                    montant_prevu=l['prevu'],
                    montant_realise=l['realise'],
                )
            self.stdout.write(f'   {len(TRESORERIE_DATA["lignes"])} lignes de trésorerie créées.')
