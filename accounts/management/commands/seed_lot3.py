"""
Seed données de démonstration pour le Lot 3 — Exécution des projets :
  M13 : Activités d'exécution + dépendances + affectations
  M14 : Tâches + sous-tâches + checklist + dépendances
  M15 : Livrables
  M16 : Réunions + participants + PV + missions

Et pour la Planification :
  Plans de travail + Activités planifiées + Jalons
  Plans d'action + Items
  Programme d'activités + ActivitésPA

Usage : python manage.py seed_lot3 [--reset]
"""
import random
from datetime import date, timedelta, time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# -- Données activités d'exécution (M13) --------------------------------------

ACTIVITES_DATA = [
    {
        'code': 'ACT-2026-001',
        'intitule': 'Formation des agents de santé communautaires – Module nutrition',
        'description': (
            'Formation intensive de 85 agents de santé communautaires sur le module nutrition infantile '
            'et maternelle. Couvre les techniques d\'évaluation nutritionnelle, les pratiques ANJE, '
            'et l\'utilisation des outils de collecte numérique KoboToolbox.'
        ),
        'priorite': 'critique', 'statut': 'en_cours',
        'debut_delta': -30, 'fin_delta': 15,
        'budget_prevu': 4500000, 'budget_realise': 2100000, 'taux': 65,
        'ordre': 1,
    },
    {
        'code': 'ACT-2026-002',
        'intitule': 'Déploiement système de suivi numérique – Phase 1',
        'description': (
            'Déploiement de l\'application KoboToolbox dans les 5 districts sanitaires cibles. '
            'Installation des équipements, formation des enquêteurs, paramétrage des formulaires '
            'de collecte et mise en place de la synchronisation des données en temps réel.'
        ),
        'priorite': 'haute', 'statut': 'terminee',
        'debut_delta': -60, 'fin_delta': -10,
        'budget_prevu': 3200000, 'budget_realise': 3050000, 'taux': 100,
        'ordre': 2,
    },
    {
        'code': 'ACT-2026-003',
        'intitule': 'Construction et réhabilitation de 8 centres de santé',
        'description': (
            'Travaux de construction de 3 nouveaux centres de santé et réhabilitation de 5 centres '
            'existants dans les zones rurales d\'Abidjan-Nord. Inclut équipement médical de base, '
            'raccordement eau/électricité et mobilier.'
        ),
        'priorite': 'critique', 'statut': 'en_cours',
        'debut_delta': -45, 'fin_delta': 45,
        'budget_prevu': 18000000, 'budget_realise': 8500000, 'taux': 48,
        'ordre': 3,
    },
    {
        'code': 'ACT-2026-004',
        'intitule': 'Enquête de base – mesure des indicateurs de référence',
        'description': (
            'Conduite de l\'enquête de base auprès de 1 200 ménages pour mesurer les valeurs initiales '
            'des 25 indicateurs du cadre de résultats. Collecte quantitative et qualitative, '
            'analyse des données et production du rapport d\'enquête.'
        ),
        'priorite': 'haute', 'statut': 'terminee',
        'debut_delta': -90, 'fin_delta': -50,
        'budget_prevu': 6500000, 'budget_realise': 6200000, 'taux': 100,
        'ordre': 4,
    },
    {
        'code': 'ACT-2026-005',
        'intitule': 'Mise en place des coopératives agricoles – Zone Nord',
        'description': (
            'Organisation et structuration de 10 coopératives agricoles dans la région Nord. '
            'Formations en gestion coopérative, rédaction des statuts, ouverture des comptes bancaires '
            'et premiers plans d\'affaires.'
        ),
        'priorite': 'normale', 'statut': 'en_attente',
        'debut_delta': 10, 'fin_delta': 70,
        'budget_prevu': 5800000, 'budget_realise': 0, 'taux': 0,
        'ordre': 5,
    },
    {
        'code': 'ACT-2026-006',
        'intitule': 'Campagne de vaccination – 45 villages cibles',
        'description': (
            'Organisation et conduite de la campagne de vaccination DTP3 dans 45 villages. '
            'Mobilisation communautaire, approvisionnement en vaccins, formation des équipes mobiles '
            'et suivi de la couverture vaccinale.'
        ),
        'priorite': 'critique', 'statut': 'planifiee',
        'debut_delta': 5, 'fin_delta': 25,
        'budget_prevu': 2800000, 'budget_realise': 0, 'taux': 0,
        'ordre': 6,
    },
    {
        'code': 'ACT-2026-007',
        'intitule': 'Formation en alphabétisation fonctionnelle – Femmes rurales',
        'description': (
            'Programme d\'alphabétisation fonctionnelle pour 500 femmes rurales de 18-45 ans. '
            '120 heures de formation sur 6 mois, avec modules lecture, écriture, calcul et gestion '
            'des finances du ménage. Formation des animatrices communautaires.'
        ),
        'priorite': 'haute', 'statut': 'suspendue',
        'debut_delta': -20, 'fin_delta': 40,
        'budget_prevu': 7200000, 'budget_realise': 1800000, 'taux': 25,
        'ordre': 7, 'motif': 'Attente recrutement de 3 animatrices supplémentaires',
    },
    {
        'code': 'ACT-2026-008',
        'intitule': 'Audit financier intermédiaire – Exercice S1 2026',
        'description': (
            'Audit financier indépendant couvrant le premier semestre 2026. '
            'Vérification des pièces justificatives, contrôle des procédures d\'achat, '
            'rapprochement des soldes bancaires et production du rapport d\'audit certifié.'
        ),
        'priorite': 'haute', 'statut': 'planifiee',
        'debut_delta': 20, 'fin_delta': 50,
        'budget_prevu': 3500000, 'budget_realise': 0, 'taux': 0,
        'ordre': 8,
    },
]

DEPENDANCES_ACTIVITE = [
    (0, 2, 'FD', 0),   # ACT-001 -> ACT-003 (Fin->Début)
    (1, 0, 'FD', 5),   # ACT-002 -> ACT-001 (Fin->Début, +5j)
    (3, 4, 'FD', 0),   # ACT-004 -> ACT-005 (Fin->Début)
    (5, 6, 'DD', 0),   # ACT-006 -> ACT-007 (Début->Début)
]

# -- Données tâches (M14) ------------------------------------------------------

TACHES_DATA = [
    # Tâches pour ACT-001
    {
        'idx_activite': 0,
        'code': 'T-001', 'titre': 'Élaborer le curriculum de formation nutrition',
        'description': 'Rédiger le programme pédagogique, les fiches de séances et les supports de formation pour le module nutrition infantile et maternelle.',
        'priorite': 'critique', 'statut': 'terminee',
        'debut_delta': -30, 'fin_delta': -20,
        'estimation': 40, 'heures_realisees': 38, 'taux': 100,
        'checklist': ['Rédiger le plan de formation', 'Créer les fiches pédagogiques', 'Préparer les supports visuels', 'Valider avec le responsable médical'],
    },
    {
        'idx_activite': 0,
        'code': 'T-002', 'titre': 'Réserver les salles de formation – 3 districts',
        'description': 'Identifier et réserver les espaces de formation dans les 3 districts sanitaires : Abobo, Adjamé, Yopougon.',
        'priorite': 'haute', 'statut': 'terminee',
        'debut_delta': -28, 'fin_delta': -22,
        'estimation': 8, 'heures_realisees': 6, 'taux': 100,
        'checklist': ['Contacter le DS Abobo', 'Contacter le DS Adjamé', 'Contacter le DS Yopougon', 'Confirmer les réservations'],
    },
    {
        'idx_activite': 0,
        'code': 'T-003', 'titre': 'Former les 47 agents – Session 1 (District Abobo)',
        'description': 'Conduite de la première session de formation pour les 47 agents du district d\'Abobo. Formation de 3 jours avec évaluation des acquis.',
        'priorite': 'critique', 'statut': 'en_cours',
        'debut_delta': -10, 'fin_delta': 5,
        'estimation': 120, 'heures_realisees': 75, 'taux': 62,
        'checklist': ['Accueil et inscription des participants', 'Module 1 : Évaluation nutritionnelle', 'Module 2 : Pratiques ANJE', 'Module 3 : Outils numériques', 'Évaluation finale des acquis'],
    },
    {
        'idx_activite': 0,
        'code': 'T-004', 'titre': 'Former les 38 agents – Session 2 (Districts Adjamé & Yop.)',
        'description': 'Deuxième session de formation pour les 38 agents restants. Inclut une session de rattrapage pour les absents.',
        'priorite': 'critique', 'statut': 'a_faire',
        'debut_delta': 8, 'fin_delta': 15,
        'estimation': 100, 'heures_realisees': 0, 'taux': 0,
        'checklist': [],
    },
    {
        'idx_activite': 0,
        'code': 'T-005', 'titre': 'Produire le rapport de formation',
        'description': 'Rédiger le rapport final de la formation avec résultats des évaluations, photos, liste des certifiés et recommandations.',
        'priorite': 'normale', 'statut': 'a_faire',
        'debut_delta': 16, 'fin_delta': 20,
        'estimation': 20, 'heures_realisees': 0, 'taux': 0,
        'checklist': [],
    },
    # Tâches pour ACT-002
    {
        'idx_activite': 1,
        'code': 'T-006', 'titre': 'Installation des tablettes – 5 districts',
        'description': 'Installation et configuration de 25 tablettes Android avec l\'application KoboCollect dans les 5 districts sanitaires.',
        'priorite': 'haute', 'statut': 'terminee',
        'debut_delta': -60, 'fin_delta': -50,
        'estimation': 30, 'heures_realisees': 28, 'taux': 100,
        'checklist': ['Flasher les tablettes', 'Installer KoboCollect', 'Configurer les formulaires', 'Tester la synchronisation'],
    },
    {
        'idx_activite': 1,
        'code': 'T-007', 'titre': 'Former les enquêteurs à KoboCollect',
        'description': 'Formation pratique de 25 enquêteurs à l\'utilisation de l\'application de collecte de données sur mobile.',
        'priorite': 'haute', 'statut': 'terminee',
        'debut_delta': -50, 'fin_delta': -40,
        'estimation': 40, 'heures_realisees': 38, 'taux': 100,
        'checklist': ['Session théorique', 'Exercices pratiques', 'Test de collecte réel', 'Certification des enquêteurs'],
    },
    # Tâches pour ACT-003
    {
        'idx_activite': 2,
        'code': 'T-008', 'titre': 'Appel d\'offres entreprises de construction',
        'description': 'Lancer l\'appel d\'offres pour les travaux de construction et réhabilitation des 8 centres de santé.',
        'priorite': 'critique', 'statut': 'terminee',
        'debut_delta': -45, 'fin_delta': -35,
        'estimation': 50, 'heures_realisees': 48, 'taux': 100,
        'checklist': ['Préparer les DAO', 'Publier l\'appel d\'offres', 'Dépouillement des offres', 'Sélection de l\'entreprise'],
    },
    {
        'idx_activite': 2,
        'code': 'T-009', 'titre': 'Supervision chantier – Sites 1 à 4',
        'description': 'Supervision hebdomadaire des travaux sur les 4 premiers sites de construction. Vérification conformité technique, avancement et qualité.',
        'priorite': 'haute', 'statut': 'en_cours',
        'debut_delta': -30, 'fin_delta': 20,
        'estimation': 160, 'heures_realisees': 80, 'taux': 50,
        'checklist': ['Rapport semaine 1', 'Rapport semaine 2', 'Rapport semaine 3', 'Rapport semaine 4'],
    },
    {
        'idx_activite': 2,
        'code': 'T-010', 'titre': 'Acquisition équipements médicaux',
        'description': 'Procédure d\'achat des équipements médicaux de base pour les 8 centres : lits, matériel de soins, réfrigérateurs à vaccins.',
        'priorite': 'haute', 'statut': 'en_attente',
        'debut_delta': -5, 'fin_delta': 30,
        'estimation': 60, 'heures_realisees': 10, 'taux': 15,
        'checklist': ['Lister les équipements', 'Demander les devis', 'Validation du budget', 'Passer commande'],
    },
    # Tâches projet divers (sans activité)
    {
        'idx_activite': None,
        'code': 'T-011', 'titre': 'Préparation rapport trimestriel Q2 2026',
        'description': 'Collecte des données auprès de tous les responsables d\'activités, consolidation et rédaction du rapport trimestriel Q2 2026.',
        'priorite': 'haute', 'statut': 'a_valider',
        'debut_delta': -7, 'fin_delta': 3,
        'estimation': 40, 'heures_realisees': 36, 'taux': 90,
        'checklist': ['Collecte données activités', 'Collecte données financières', 'Rédaction narrative', 'Validation chef de projet'],
    },
    {
        'idx_activite': None,
        'code': 'T-012', 'titre': 'Révision du budget prévisionnel S2 2026',
        'description': 'Révision et actualisation du budget prévisionnel pour le second semestre 2026 intégrant les économies réalisées et les dépassements anticipés.',
        'priorite': 'critique', 'statut': 'bloquee',
        'debut_delta': -15, 'fin_delta': -2,
        'estimation': 24, 'heures_realisees': 5, 'taux': 20,
        'checklist': [],
        'notes': 'Bloquée : attente des chiffres finaux de l\'audit S1 de l\'activité ACT-2026-008',
    },
    {
        'idx_activite': None,
        'code': 'T-013', 'titre': 'Organisation COPIL trimestriel – Juillet 2026',
        'description': 'Organisation du Comité de Pilotage trimestriel : convocations, ordre du jour, préparation des présentations, logistique.',
        'priorite': 'normale', 'statut': 'a_faire',
        'debut_delta': 5, 'fin_delta': 25,
        'estimation': 30, 'heures_realisees': 0, 'taux': 0,
        'checklist': ['Rédiger convocation', 'Préparer ordre du jour', 'Préparer présentations', 'Réserver la salle', 'Envoyer les invitations'],
    },
    {
        'idx_activite': 5,
        'code': 'T-014', 'titre': 'Planification logistique campagne vaccination',
        'description': 'Planifier les itinéraires, équipes mobiles, chaîne du froid et calendrier de la campagne vaccination dans les 45 villages.',
        'priorite': 'critique', 'statut': 'en_cours',
        'debut_delta': 5, 'fin_delta': 12,
        'estimation': 30, 'heures_realisees': 8, 'taux': 25,
        'checklist': ['Carte des villages', 'Composition des équipes', 'Réquisition des véhicules', 'Commande des vaccins'],
    },
    {
        'idx_activite': 5,
        'code': 'T-015', 'titre': 'Mobilisation communautaire – Sensibilisation vaccination',
        'description': 'Mobiliser les relais communautaires et les leaders pour sensibiliser les ménages avant la campagne.',
        'priorite': 'haute', 'statut': 'a_faire',
        'debut_delta': 8, 'fin_delta': 18,
        'estimation': 50, 'heures_realisees': 0, 'taux': 0,
        'checklist': [],
    },
]

DEPENDANCES_TACHE = [
    (0, 2, 'FD'),   # T-001 -> T-003 (curriculum -> session 1)
    (1, 2, 'FD'),   # T-002 -> T-003 (réservation -> session 1)
    (2, 3, 'FD'),   # T-003 -> T-004 (session 1 -> session 2)
    (3, 4, 'FD'),   # T-004 -> T-005 (session 2 -> rapport)
    (5, 6, 'FD'),   # T-006 -> T-007 (tablettes -> formation enquêteurs)
    (7, 8, 'FD'),   # T-008 -> T-009 (AO -> supervision)
    (8, 9, 'DD'),   # T-009 -> T-010 (supervision -> acquisition — Début->Début)
    (13, 14, 'FD'), # T-014 -> T-015 (planification -> mobilisation)
]

# -- Données livrables (M15) ---------------------------------------------------

LIVRABLES_DATA = [
    {
        'code': 'LIV-001', 'titre': 'Rapport d\'enquête de base – Indicateurs de référence',
        'type': 'rapport', 'statut': 'publie',
        'description': 'Rapport complet de l\'enquête de base avec résultats sur les 25 indicateurs de référence, analyse par zone et recommandations pour le suivi.',
        'date_delta': -45, 'version': '2.0',
        'idx_activite': 3,
    },
    {
        'code': 'LIV-002', 'titre': 'Curriculum formation agents de santé – Module nutrition',
        'type': 'manuel', 'statut': 'valide',
        'description': 'Guide pédagogique complet pour la formation des agents de santé communautaires sur le module nutrition infantile et maternelle.',
        'date_delta': -20, 'version': '1.1',
        'idx_activite': 0,
    },
    {
        'code': 'LIV-003', 'titre': 'Rapport trimestriel Q1 2026 – Programme PRCC',
        'type': 'rapport', 'statut': 'soumis',
        'description': 'Rapport d\'avancement du premier trimestre 2026 : activités réalisées, indicateurs atteints, dépenses et plan pour Q2.',
        'date_delta': 3, 'version': '0.9',
        'idx_activite': None,
    },
    {
        'code': 'LIV-004', 'titre': 'Base de données bénéficiaires – KoboToolbox',
        'type': 'bdd', 'statut': 'valide',
        'description': 'Base de données consolidée des 6 000 bénéficiaires avec leurs informations socio-économiques, sanitaires et nutritionnelles.',
        'date_delta': -15, 'version': '1.0',
        'idx_activite': 1,
    },
    {
        'code': 'LIV-005', 'titre': 'TDR – Campagne de vaccination DTP3',
        'type': 'tdr', 'statut': 'valide',
        'description': 'Termes de référence détaillés pour la campagne de vaccination DTP3 dans les 45 villages cibles.',
        'date_delta': 10, 'version': '1.0',
        'idx_activite': 5,
    },
    {
        'code': 'LIV-006', 'titre': 'Rapport de supervision – Travaux construction S1 2026',
        'type': 'rapport', 'statut': 'brouillon',
        'description': 'Rapport de supervision mi-parcours des travaux de construction des 8 centres de santé : état d\'avancement, qualité, délais.',
        'date_delta': 15, 'version': '0.1',
        'idx_activite': 2,
    },
]

# -- Données réunions (M16) ----------------------------------------------------

REUNIONS_DATA = [
    {
        'type': 'comite_pilotage',
        'objet': 'Comité de Pilotage Q1 2026 – Bilan et orientations',
        'description': 'Revue du premier trimestre 2026, validation des ajustements programmatiques et budgétaires, orientations pour Q2.',
        'date_delta': -30,
        'heure_debut': time(9, 0), 'heure_fin': time(13, 0),
        'lieu': 'Salle de conférence – Siège PRCC, Plateau Abidjan',
        'plateforme': 'presentiel',
        'statut': 'tenue',
        'nb_participants': 3,
        'avec_pv': True,
        'points_odj': [
            ('Bilan activités Q1 2026', 'Revue détaillée de chaque activité', 30),
            ('Situation financière', 'Analyse des dépenses et projections', 20),
            ('Risques et mesures correctives', 'Identification et réponses aux risques majeurs', 25),
            ('Plan Q2 2026', 'Validation des priorités du deuxième trimestre', 20),
            ('Questions diverses', '', 15),
        ],
    },
    {
        'type': 'comite_technique',
        'objet': 'Revue technique indicateurs S&E – Mai 2026',
        'description': 'Analyse des indicateurs de suivi-évaluation, validation des données collectées et ajustements du cadre de résultats.',
        'date_delta': -7,
        'heure_debut': time(14, 0), 'heure_fin': time(17, 0),
        'lieu': 'Salle de réunion B – Siège PRCC',
        'plateforme': 'hybride',
        'statut': 'tenue',
        'nb_participants': 2,
        'avec_pv': True,
        'points_odj': [
            ('Analyse des 25 indicateurs', 'État d\'atteinte et trajectoire', 60),
            ('Points d\'alerte', 'Indicateurs à risque – mesures correctives', 45),
            ('Prochaines étapes', 'Plan de collecte données Q2', 30),
        ],
    },
    {
        'type': 'interne',
        'objet': 'Réunion coordination équipe – Planification campagne vaccination',
        'description': 'Coordination opérationnelle pour la préparation de la campagne de vaccination DTP3 dans les 45 villages.',
        'date_delta': 3,
        'heure_debut': time(8, 30), 'heure_fin': time(10, 30),
        'lieu': 'Salle de réunion A – Siège PRCC',
        'plateforme': 'presentiel',
        'statut': 'planifiee',
        'nb_participants': 2,
        'avec_pv': False,
        'points_odj': [
            ('Cartographie des villages', 'Répartition géographique et itinéraires', 30),
            ('Composition des équipes mobiles', 'Affectation du personnel', 20),
            ('Logistique et chaîne du froid', 'Approvisionnement en vaccins', 25),
            ('Calendrier de déploiement', 'Planning jour par jour', 20),
        ],
    },
    {
        'type': 'partenaires',
        'objet': 'Réunion de coordination avec les partenaires d\'exécution',
        'description': 'Réunion trimestrielle de coordination avec les ONG partenaires et les directions régionales pour aligner les activités terrain.',
        'date_delta': 10,
        'heure_debut': time(10, 0), 'heure_fin': time(12, 30),
        'lieu': 'Salle Polyvalente – Conseil Régional',
        'plateforme': 'presentiel',
        'statut': 'planifiee',
        'nb_participants': 2,
        'avec_pv': False,
        'points_odj': [
            ('Avancement des activités partenaires', 'Point de situation par partenaire', 45),
            ('Difficultés communes', 'Partage des problèmes et solutions', 30),
            ('Coordination terrain', 'Synergies et complémentarités', 30),
        ],
    },
]

# -- Données planification : Plans de travail + Jalons -------------------------

PLANS_TRAVAIL_DATA = [
    {
        'nom': 'Plan de Travail 2026 – Programme PRCC',
        'annee': 2026, 'trimestre': None, 'statut': 'en_cours',
        'activites': [
            {
                'code': 'PT-2026-01', 'libelle': 'Activités de renforcement des capacités en santé',
                'description': 'Formation, équipement et appui aux structures de santé communautaires.',
                'statut': 'en_cours', 'debut_delta': -90, 'fin_delta': 90,
                'budget': 22000000, 'taux': 45, 'ordre': 1,
                'sous_activites': [
                    {
                        'code': 'PT-2026-01.1', 'libelle': 'Formation agents de santé',
                        'statut': 'en_cours', 'debut_delta': -30, 'fin_delta': 15,
                        'budget': 4500000, 'taux': 65, 'ordre': 1,
                    },
                    {
                        'code': 'PT-2026-01.2', 'libelle': 'Déploiement système suivi numérique',
                        'statut': 'terminee', 'debut_delta': -60, 'fin_delta': -10,
                        'budget': 3200000, 'taux': 100, 'ordre': 2,
                    },
                    {
                        'code': 'PT-2026-01.3', 'libelle': 'Campagne de vaccination DTP3',
                        'statut': 'planifiee', 'debut_delta': 5, 'fin_delta': 25,
                        'budget': 2800000, 'taux': 0, 'ordre': 3,
                    },
                ],
            },
            {
                'code': 'PT-2026-02', 'libelle': 'Infrastructures sanitaires',
                'description': 'Construction et réhabilitation des centres de santé.',
                'statut': 'en_cours', 'debut_delta': -45, 'fin_delta': 120,
                'budget': 18000000, 'taux': 38, 'ordre': 2,
                'sous_activites': [
                    {
                        'code': 'PT-2026-02.1', 'libelle': 'Construction 3 centres de santé',
                        'statut': 'en_cours', 'debut_delta': -45, 'fin_delta': 45,
                        'budget': 10000000, 'taux': 40, 'ordre': 1,
                    },
                    {
                        'code': 'PT-2026-02.2', 'libelle': 'Réhabilitation 5 centres existants',
                        'statut': 'planifiee', 'debut_delta': 10, 'fin_delta': 90,
                        'budget': 8000000, 'taux': 0, 'ordre': 2,
                    },
                ],
            },
            {
                'code': 'PT-2026-03', 'libelle': 'Développement économique et AGR',
                'description': 'Structuration des coopératives et appui aux activités génératrices de revenus.',
                'statut': 'planifiee', 'debut_delta': 10, 'fin_delta': 180,
                'budget': 14000000, 'taux': 0, 'ordre': 3,
                'sous_activites': [],
            },
        ],
    },
]

JALONS_DATA = [
    {
        'libelle': 'Démarrage officiel du Programme PRCC',
        'description': 'Cérémonie officielle de démarrage avec toutes les parties prenantes.',
        'date_delta': -180, 'statut': 'atteint',
    },
    {
        'libelle': 'Rapport enquête de base validé et soumis au bailleur',
        'description': 'Livraison du rapport d\'enquête de base avec tous les indicateurs de référence.',
        'date_delta': -45, 'statut': 'atteint',
    },
    {
        'libelle': 'Revue à mi-parcours du programme',
        'description': 'Mission de revue à mi-parcours avec le bailleur (Banque Mondiale).',
        'date_delta': 20, 'statut': 'a_venir',
    },
    {
        'libelle': '500 agents de santé formés et certifiés',
        'description': 'Cible intermédiaire de formation atteinte à la mi-programme.',
        'date_delta': 90, 'statut': 'a_venir',
    },
    {
        'libelle': 'Fin des travaux de construction – Phase 1',
        'description': 'Réception provisoire des 3 premiers centres de santé construits.',
        'date_delta': 45, 'statut': 'a_venir',
    },
    {
        'libelle': 'Rapport annuel 2026 soumis au bailleur',
        'description': 'Soumission du rapport annuel 2026 avec évaluation de l\'atteinte des résultats.',
        'date_delta': 210, 'statut': 'a_venir',
    },
]

# -- Données plan d'action (M11) -----------------------------------------------

PLAN_ACTION_DATA = {
    'titre': 'Plan d\'Action Q2-Q3 2026 – Programme PRCC',
    'periode': 'trimestriel', 'annee': 2026, 'trimestre': 2,
    'statut': 'en_cours', 'budget_total': 35000000,
    'items': [
        {
            'code': 'PA-01', 'libelle': 'Former 85 agents de santé – Module nutrition',
            'responsable_idx': 0, 'debut_delta': -30, 'fin_delta': 15,
            'budget': 4500000, 'taux': 65, 'statut': 'en_cours',
            'indicateur': 'Nombre d\'agents formés et certifiés', 'livrable': 'Rapport de formation',
        },
        {
            'code': 'PA-02', 'libelle': 'Construire et réhabiliter 8 centres de santé',
            'responsable_idx': 0, 'debut_delta': -45, 'fin_delta': 45,
            'budget': 18000000, 'taux': 48, 'statut': 'en_cours',
            'indicateur': 'Nombre de centres réceptionnés', 'livrable': 'PV de réception',
        },
        {
            'code': 'PA-03', 'libelle': 'Conduire campagne vaccination DTP3 – 45 villages',
            'responsable_idx': 0, 'debut_delta': 5, 'fin_delta': 25,
            'budget': 2800000, 'taux': 0, 'statut': 'planifie',
            'indicateur': 'Couverture vaccinale DTP3 (%)', 'livrable': 'Rapport de campagne',
        },
        {
            'code': 'PA-04', 'libelle': 'Structurer 10 coopératives agricoles – Zone Nord',
            'responsable_idx': 0, 'debut_delta': 10, 'fin_delta': 70,
            'budget': 5800000, 'taux': 0, 'statut': 'planifie',
            'indicateur': 'Nombre de coopératives opérationnelles', 'livrable': 'Statuts des coopératives',
        },
        {
            'code': 'PA-05', 'libelle': 'Formation alphabétisation – 500 femmes rurales',
            'responsable_idx': 0, 'debut_delta': -20, 'fin_delta': 40,
            'budget': 7200000, 'taux': 25, 'statut': 'en_cours',
            'indicateur': 'Nombre de femmes ayant achevé la formation', 'livrable': 'Rapport de formation',
        },
        {
            'code': 'PA-06', 'libelle': 'Audit financier intermédiaire S1 2026',
            'responsable_idx': 0, 'debut_delta': 20, 'fin_delta': 50,
            'budget': 3500000, 'taux': 0, 'statut': 'planifie',
            'indicateur': 'Rapport d\'audit certifié disponible', 'livrable': 'Rapport d\'audit certifié',
        },
        {
            'code': 'PA-07', 'libelle': 'Enquête de suivi bénéficiaires S1 2026',
            'responsable_idx': 0, 'debut_delta': -5, 'fin_delta': 10,
            'budget': 1500000, 'taux': 60, 'statut': 'en_cours',
            'indicateur': 'Nombre de ménages enquêtés', 'livrable': 'Base de données mise à jour',
        },
        {
            'code': 'PA-08', 'libelle': 'Revue à mi-parcours – Préparation et conduite',
            'responsable_idx': 0, 'debut_delta': 15, 'fin_delta': 25,
            'budget': 1500000, 'taux': 0, 'statut': 'planifie',
            'indicateur': 'Rapport de revue disponible et validé', 'livrable': 'Rapport de revue à mi-parcours',
        },
    ],
}


class Command(BaseCommand):
    help = 'Seed données Lot 3 (M13-M16 Exécution + Planification)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les données du Lot 3 existantes avant de re-seeder')

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
            users = self._get_users()
            programme = projet.programme

            activites = self._seed_activites(admin, users, projet, programme)
            taches = self._seed_taches(admin, users, activites, projet)
            self._seed_livrables(admin, projet, activites)
            self._seed_reunions(admin, users, projet)
            self._seed_planification(admin, projet, users)
            self._seed_plan_action(admin, users, projet, programme)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed Lot 3 terminé !'))

    # -- Helpers ---------------------------------------------------------------

    def _reset(self):
        from execution.models import (
            ActiviteExecution, Tache, Livrable, Reunion, DependanceActivite, DependanceTache
        )
        from planification.models import PlanTravail, Jalon, PlanAction
        self.stdout.write(self.style.WARNING('[RESET] Suppression données Lot 3…'))
        DependanceTache.objects.all().delete()
        DependanceActivite.objects.all().delete()
        Tache.objects.all().delete()
        ActiviteExecution.objects.all().delete()
        Livrable.objects.all().delete()
        Reunion.objects.all().delete()
        PlanTravail.objects.all().delete()
        Jalon.objects.all().delete()
        PlanAction.objects.all().delete()
        self.stdout.write('   Terminé.')

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_users(self):
        from accounts.models import User
        return list(User.objects.all()[:8])

    def _get_projet(self):
        from programmes_projets.models import Projet
        return Projet.objects.filter(statut='en_cours').first()

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Créé') if created else self.style.WARNING('Existe')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:80]}')

    def _pick_user(self, users, idx=0):
        if not users:
            return None
        return users[idx % len(users)]

    # -- M13 : Activités d'exécution -----------------------------------------

    def _seed_activites(self, admin, users, projet, programme):
        from execution.models import ActiviteExecution, AffectationRessource, DependanceActivite
        self.stdout.write('\n>> Activités d\'exécution (M13)…')
        today = date.today()
        result = []

        for i, data in enumerate(ACTIVITES_DATA):
            debut = today + timedelta(days=data['debut_delta'])
            fin = today + timedelta(days=data['fin_delta'])
            resp = self._pick_user(users, i)
            act, created = ActiviteExecution.objects.get_or_create(
                code=data['code'],
                defaults={
                    'intitule': data['intitule'],
                    'description': data['description'],
                    'projet': projet,
                    'programme': programme,
                    'priorite': data['priorite'],
                    'statut': data['statut'],
                    'responsable': resp,
                    'date_debut_prevue': debut,
                    'date_fin_prevue': fin,
                    'date_debut_reelle': debut if data['statut'] in ('en_cours', 'terminee', 'suspendue') else None,
                    'date_fin_reelle': fin if data['statut'] == 'terminee' else None,
                    'budget_prevu': data['budget_prevu'],
                    'budget_realise': data['budget_realise'],
                    'taux_avancement': data['taux'],
                    'ordre': data['ordre'],
                    'motif_suspension': data.get('motif', ''),
                    'created_by': admin,
                    'valide_par': admin if data['statut'] in ('terminee', 'archivee') else None,
                }
            )
            self._log('Activité', act, created)
            result.append(act)

            if created:
                # Affectation ressource principale
                AffectationRessource.objects.create(
                    activite=act,
                    type_ressource='utilisateur',
                    utilisateur=resp,
                    taux_affectation=100,
                    date_debut=debut,
                    date_fin=fin,
                )
                if i + 1 < len(users):
                    AffectationRessource.objects.create(
                        activite=act,
                        type_ressource='utilisateur',
                        utilisateur=users[(i + 1) % len(users)],
                        taux_affectation=50,
                        date_debut=debut,
                        date_fin=fin,
                    )

        # Dépendances entre activités
        self.stdout.write('\n   Dépendances activités…')
        for src_idx, cible_idx, type_dep, decalage in DEPENDANCES_ACTIVITE:
            if src_idx < len(result) and cible_idx < len(result):
                dep, created = DependanceActivite.objects.get_or_create(
                    activite_source=result[src_idx],
                    activite_cible=result[cible_idx],
                    defaults={'type_dependance': type_dep, 'decalage_jours': decalage},
                )
                self._log(f'Dép. activité [{type_dep}]', dep, created)

        return result

    # -- M14 : Tâches ---------------------------------------------------------

    def _seed_taches(self, admin, users, activites, projet):
        from execution.models import Tache, ChecklistItem, DependanceTache
        self.stdout.write('\n>> Tâches (M14)…')
        today = date.today()
        result = []

        for i, data in enumerate(TACHES_DATA):
            idx_act = data.get('idx_activite')
            activite = activites[idx_act] if idx_act is not None and idx_act < len(activites) else None
            debut = today + timedelta(days=data['debut_delta']) if data['debut_delta'] is not None else None
            fin = today + timedelta(days=data['fin_delta']) if data['fin_delta'] is not None else None
            assignee = self._pick_user(users, i)

            tache, created = Tache.objects.get_or_create(
                code=data['code'],
                defaults={
                    'activite': activite,
                    'titre': data['titre'],
                    'description': data['description'],
                    'priorite': data['priorite'],
                    'statut': data['statut'],
                    'assignee': assignee,
                    'date_debut': debut,
                    'date_echeance': fin,
                    'date_completion': fin if data['statut'] == 'terminee' else None,
                    'estimation_heures': data['estimation'],
                    'heures_realisees': data['heures_realisees'],
                    'taux_avancement': data['taux'],
                    'notes': data.get('notes', ''),
                    'ordre': i,
                    'created_by': admin,
                }
            )
            self._log('Tâche', tache, created)
            result.append(tache)

            if created and data.get('checklist'):
                for j, libelle in enumerate(data['checklist']):
                    ChecklistItem.objects.create(
                        tache=tache,
                        libelle=libelle,
                        complete=(data['statut'] == 'terminee' or j < len(data['checklist']) // 2),
                        ordre=j,
                    )

        # Dépendances entre tâches
        self.stdout.write('\n   Dépendances tâches…')
        for src_idx, cible_idx, type_dep in DEPENDANCES_TACHE:
            if src_idx < len(result) and cible_idx < len(result):
                dep, created = DependanceTache.objects.get_or_create(
                    tache_source=result[src_idx],
                    tache_cible=result[cible_idx],
                    defaults={'type_dependance': type_dep},
                )
                self._log(f'Dép. tâche [{type_dep}]', dep, created)

        return result

    # -- M15 : Livrables ------------------------------------------------------

    def _seed_livrables(self, admin, projet, activites):
        from execution.models import Livrable, VersionLivrable, ValidationLivrable
        self.stdout.write('\n>> Livrables (M15)…')
        today = date.today()

        for i, data in enumerate(LIVRABLES_DATA):
            idx_act = data.get('idx_activite')
            activite = activites[idx_act] if idx_act is not None and idx_act < len(activites) else None
            date_prevue = today + timedelta(days=data['date_delta'])

            livrable, created = Livrable.objects.get_or_create(
                code=data['code'],
                defaults={
                    'titre': data['titre'],
                    'description': data['description'],
                    'type_livrable': data['type'],
                    'projet': projet,
                    'activite': activite,
                    'responsable': admin,
                    'date_prevue': date_prevue,
                    'date_livraison': date_prevue if data['statut'] in ('valide', 'publie') else None,
                    'statut': data['statut'],
                    'version_courante': data['version'],
                    'created_by': admin,
                }
            )
            self._log('Livrable', livrable, created)

            if created:
                # Version courante
                VersionLivrable.objects.create(
                    livrable=livrable,
                    numero_version=data['version'],
                    uploaded_by=admin,
                    est_courante=True,
                    description_changements='Version initiale' if data['version'].endswith('.0') else 'Révision suite aux commentaires',
                )
                # Workflow validation
                for etape, ordre in [('chef_projet', 1), ('responsable_programme', 2), ('coordonnateur', 3), ('final', 4)]:
                    statut_val = 'approuve' if data['statut'] in ('valide', 'publie') else 'en_attente'
                    ValidationLivrable.objects.create(
                        livrable=livrable, etape=etape, ordre=ordre,
                        statut=statut_val,
                        validateur=admin if statut_val == 'approuve' else None,
                        date_validation=timezone.now() if statut_val == 'approuve' else None,
                    )

    # -- M16 : Réunions -------------------------------------------------------

    def _seed_reunions(self, admin, users, projet):
        from execution.models import Reunion, ParticipantReunion, PointOrdreJour, CompteRendu, DecisionReunion, ActionReunion
        self.stdout.write('\n>> Réunions (M16)…')
        today = date.today()

        for i, data in enumerate(REUNIONS_DATA):
            date_reunion = today + timedelta(days=data['date_delta'])
            reunion, created = Reunion.objects.get_or_create(
                objet=data['objet'],
                defaults={
                    'type_reunion': data['type'],
                    'description': data['description'],
                    'organisateur': admin,
                    'projet': projet,
                    'date': date_reunion,
                    'heure_debut': data['heure_debut'],
                    'heure_fin': data.get('heure_fin'),
                    'lieu': data['lieu'],
                    'plateforme': data['plateforme'],
                    'statut': data['statut'],
                    'created_by': admin,
                }
            )
            self._log('Réunion', reunion, created)

            if created:
                # Participants
                participants = [admin] + random.sample(users, min(data['nb_participants'], len(users)))
                for j, u in enumerate(participants):
                    statut_presence = 'present' if data['statut'] == 'tenue' else 'invite'
                    ParticipantReunion.objects.get_or_create(
                        reunion=reunion,
                        utilisateur=u,
                        defaults={
                            'type_participant': 'interne',
                            'statut_presence': statut_presence,
                            'role_reunion': 'Président' if j == 0 else 'Membre',
                        }
                    )

                # Points ordre du jour
                for ordre_num, (intitule, desc, duree) in enumerate(data['points_odj'], 1):
                    PointOrdreJour.objects.create(
                        reunion=reunion, ordre=ordre_num, intitule=intitule,
                        description=desc, duree_prevue=duree, responsable=admin,
                    )

                # Compte rendu pour les réunions tenues
                if data.get('avec_pv') and data['statut'] == 'tenue':
                    cr, _ = CompteRendu.objects.get_or_create(
                        reunion=reunion,
                        defaults={
                            'redacteur': admin,
                            'synthese': f"Réunion {data['type']} tenue le {date_reunion.strftime('%d/%m/%Y')}. Tous les points à l\'ordre du jour ont été examinés. Les participants ont approuvé les orientations proposées.",
                            'discussions': "Les échanges ont porté sur les points prévus. Des ajustements ont été proposés sur certaines activités.",
                            'decisions_prises': "1. Validation du rapport d\'avancement\n2. Approbation du budget révisé\n3. Confirmation du planning Q2",
                            'statut': 'valide',
                            'valide_par': admin,
                            'date_validation': timezone.now(),
                        }
                    )
                    # Décisions et actions
                    dec, _ = DecisionReunion.objects.get_or_create(
                        compte_rendu=cr,
                        intitule='Accélérer les activités en retard',
                        defaults={
                            'description': 'Mettre en place un plan de rattrapage pour les activités présentant un retard > 2 semaines.',
                            'responsable': admin,
                            'echeance': today + timedelta(days=14),
                            'statut': 'en_cours',
                        }
                    )
                    ActionReunion.objects.get_or_create(
                        compte_rendu=cr,
                        libelle='Préparer le plan de rattrapage',
                        defaults={
                            'decision': dec,
                            'responsable': admin,
                            'echeance': today + timedelta(days=7),
                            'statut': 'a_faire',
                        }
                    )

    # -- Planification : Plans + Jalons ----------------------------------------

    def _seed_planification(self, admin, projet, users):
        from planification.models import PlanTravail, Activite, Jalon
        self.stdout.write('\n>> Planification : Plans de travail + Jalons…')
        today = date.today()

        for pt_data in PLANS_TRAVAIL_DATA:
            pt, created = PlanTravail.objects.get_or_create(
                projet=projet,
                annee=pt_data['annee'],
                defaults={
                    'nom': pt_data['nom'],
                    'trimestre': pt_data.get('trimestre'),
                    'statut': pt_data['statut'],
                    'valide_par': admin if pt_data['statut'] != 'brouillon' else None,
                    'date_validation': date.today() if pt_data['statut'] != 'brouillon' else None,
                }
            )
            self._log('Plan de travail', pt, created)

            if created:
                for act_data in pt_data['activites']:
                    debut = today + timedelta(days=act_data['debut_delta'])
                    fin = today + timedelta(days=act_data['fin_delta'])
                    act = Activite.objects.create(
                        plan=pt,
                        code=act_data['code'],
                        libelle=act_data['libelle'],
                        description=act_data.get('description', ''),
                        statut=act_data['statut'],
                        date_debut_prevue=debut,
                        date_fin_prevue=fin,
                        date_debut_reelle=debut if act_data['statut'] in ('en_cours', 'terminee') else None,
                        date_fin_reelle=fin if act_data['statut'] == 'terminee' else None,
                        budget_prevu=act_data['budget'],
                        taux_avancement=act_data['taux'],
                        ordre=act_data['ordre'],
                        responsable=admin,
                    )
                    self.stdout.write(f'    + Activité PT: {act.code}')

                    for sa_data in act_data.get('sous_activites', []):
                        d2 = today + timedelta(days=sa_data['debut_delta'])
                        f2 = today + timedelta(days=sa_data['fin_delta'])
                        sa = Activite.objects.create(
                            plan=pt, parent=act,
                            code=sa_data['code'], libelle=sa_data['libelle'],
                            statut=sa_data['statut'],
                            date_debut_prevue=d2, date_fin_prevue=f2,
                            date_debut_reelle=d2 if sa_data['statut'] in ('en_cours', 'terminee') else None,
                            date_fin_reelle=f2 if sa_data['statut'] == 'terminee' else None,
                            budget_prevu=sa_data['budget'],
                            taux_avancement=sa_data['taux'],
                            ordre=sa_data['ordre'],
                            responsable=admin,
                        )
                        self.stdout.write(f'       +-- Sous-act: {sa.code}')

        # Jalons
        self.stdout.write('\n   Jalons…')
        for jdata in JALONS_DATA:
            date_prevue = today + timedelta(days=jdata['date_delta'])
            jalon, created = Jalon.objects.get_or_create(
                projet=projet,
                libelle=jdata['libelle'],
                defaults={
                    'description': jdata['description'],
                    'date_prevue': date_prevue,
                    'date_reelle': date_prevue if jdata['statut'] == 'atteint' else None,
                    'statut': jdata['statut'],
                }
            )
            self._log('Jalon', jalon, created)

    # -- M11 : Plan d'action ----------------------------------------------------

    def _seed_plan_action(self, admin, users, projet, programme):
        from planification.models import PlanAction, ActionPlanItem
        self.stdout.write('\n>> Plan d\'action (M11)…')
        today = date.today()
        data = PLAN_ACTION_DATA

        pa, created = PlanAction.objects.get_or_create(
            titre=data['titre'],
            defaults={
                'projet': projet,
                'programme': programme,
                'periode': data['periode'],
                'annee': data['annee'],
                'trimestre': data.get('trimestre'),
                'statut': data['statut'],
                'budget_total': data['budget_total'],
                'valide_par': admin,
                'date_validation': timezone.now(),
                'created_by': admin,
            }
        )
        self._log('Plan d\'action', pa, created)

        if created:
            for i, item_data in enumerate(data['items']):
                debut = today + timedelta(days=item_data['debut_delta'])
                fin = today + timedelta(days=item_data['fin_delta'])
                resp = self._pick_user(users, item_data['responsable_idx'])
                item = ActionPlanItem.objects.create(
                    plan=pa,
                    code=item_data['code'],
                    libelle=item_data['libelle'],
                    responsable=resp,
                    date_debut=debut,
                    date_fin=fin,
                    budget_prevu=item_data['budget'],
                    taux_avancement=item_data['taux'],
                    statut=item_data['statut'],
                    indicateur_realisation=item_data['indicateur'],
                    livrable_attendu=item_data['livrable'],
                    ordre=i,
                )
                self.stdout.write(f'    + Item PA: {item.code} — {item.libelle[:50]}')
