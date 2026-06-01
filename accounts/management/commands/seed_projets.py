"""
Seed donnees de demonstration pour :
  - Programmes (3 avec statuts varies)
  - Projets (8 projets sur les 3 programmes)
  - Cadres logiques + elements hierarchiques
  - Analyses SWOT + elements + strategies
  - Taches (tous les statuts)
  - Missions (tous les statuts)
  - Rapports d'avancement (tous les statuts)

Usage : python manage.py seed_projets [--reset]
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date


# ============================================================================
# DONNEES PROGRAMMES
# ============================================================================
PROGRAMMES_DATA = [
    {
        'code': 'PROG-2026-001',
        'intitule': 'Programme de Renforcement des Capacites Communautaires',
        'acronyme': 'PRCC',
        'description': (
            'Programme pluriannuel visant le renforcement integral des capacites des communautes locales '
            'dans les domaines de la sante, de l\'education, du developpement economique et de la gouvernance '
            'locale. Il couvre les regions d\'Abidjan, Bouake et Korhogo avec un accent particulier sur '
            'les populations vulnerables et les femmes rurales.'
        ),
        'contexte': (
            'Les communautes rurales de Cote d\'Ivoire font face a de nombreux defis : faible acces aux services '
            'sociaux de base, taux eleve de pauvrete, insuffisance des capacites institutionnelles locales. '
            'Ce programme repond a ces defis a travers une approche integree et participative.'
        ),
        'impacts_attendus': (
            '1. Amelioration durable des conditions de vie de 150 000 personnes\n'
            '2. Reduction de 30% du taux de pauvrete dans les zones ciblees\n'
            '3. Renforcement de la gouvernance locale dans 45 communes\n'
            '4. Creation de 2 500 emplois durables'
        ),
        'date_debut': '2024-01-01',
        'date_fin': '2028-12-31',
        'budget_total': 2500000000,
        'devise': 'XOF',
        'statut': 'en_cours',
        'taux_avancement': 38,
        'objectifs': [
            ('strategique', 'OS-01', 'Renforcer les capacites des communautes en matiere de sante et nutrition'),
            ('strategique', 'OS-02', 'Ameliorer l\'acces a une education de qualite pour les enfants et les femmes'),
            ('strategique', 'OS-03', 'Developper les activites economiques generatrices de revenus durables'),
            ('specifique', 'OS-04', 'Former 1 500 agents de sante communautaires d\'ici 2027'),
            ('specifique', 'OS-05', 'Scolariser 5 000 enfants supplementaires dans les zones rurales'),
            ('resultat', 'R-01', 'Reduction de 25% du taux de malnutrition infantile dans les zones ciblees'),
            ('resultat', 'R-02', 'Taux d\'alphabetisation des femmes adultes passe de 35% a 60%'),
        ],
    },
    {
        'code': 'PROG-2026-002',
        'intitule': 'Programme d\'Appui a l\'Agriculture Durable et a la Securite Alimentaire',
        'acronyme': 'AGRI-DEV',
        'description': (
            'Programme de developpement agricole axe sur la promotion de l\'agriculture durable, '
            'la diversification des cultures, l\'organisation des filieres agricoles et l\'amelioration '
            'de la securite alimentaire dans les regions rurales de l\'ouest et du nord du pays.'
        ),
        'contexte': (
            'La dependance aux cultures d\'exportation et les effets du changement climatique fragilisent '
            'la securite alimentaire des menages ruraux. Ce programme vise a diversifier et moderniser '
            'l\'agriculture familiale tout en preservant les ressources naturelles.'
        ),
        'impacts_attendus': (
            '1. Securite alimentaire amelioree pour 80 000 menages agricoles\n'
            '2. Revenus agricoles augmentes de 40% en moyenne\n'
            '3. 15 000 hectares de terres cultivees de maniere durable\n'
            '4. 25 cooperatives agricoles viables creees'
        ),
        'date_debut': '2025-03-01',
        'date_fin': '2029-02-28',
        'budget_total': 1800000000,
        'devise': 'XOF',
        'statut': 'en_cours',
        'taux_avancement': 22,
        'objectifs': [
            ('strategique', 'OS-01', 'Promouvoir l\'agriculture durable et resiliente au changement climatique'),
            ('strategique', 'OS-02', 'Organiser et structurer les filieres agricoles locales'),
            ('specifique', 'OS-03', 'Former 3 000 agriculteurs aux techniques agro-ecologiques'),
            ('specifique', 'OS-04', 'Creer et animer 25 cooperatives agricoles dans les zones ciblees'),
            ('resultat', 'R-01', 'Productivite agricole augmentee de 35% pour les cultures vivrieres'),
            ('resultat', 'R-02', 'Taux de pertes post-recolte reduit de 30% grace aux infrastructures de stockage'),
        ],
    },
    {
        'code': 'PROG-2024-003',
        'intitule': 'Programme de Gouvernance Locale et de Decentralisation',
        'acronyme': 'PROGOUV',
        'description': (
            'Programme acheve visant a renforcer la gouvernance locale et les processus de decentralisation '
            'dans 30 communes pilotes. Le programme a soutenu la mise en place de conseils consultatifs, '
            'renforce les capacites des elus locaux et ameliore la gestion des finances communales.'
        ),
        'contexte': (
            'La decentralisation effective reste un defi majeur en Cote d\'Ivoire. Ce programme a contribue '
            'a renforcer les institutions locales et a promouvoir la participation citoyenne dans la prise '
            'de decision au niveau communal.'
        ),
        'impacts_attendus': (
            '1. 30 communes dotees de plans de developpement local operationnels\n'
            '2. 450 elus locaux formes en gestion communale\n'
            '3. Taux de recouvrement fiscal communal ameliore de 45%\n'
            '4. 90 000 citoyens mobilises dans les processus participatifs'
        ),
        'date_debut': '2021-01-01',
        'date_fin': '2025-12-31',
        'budget_total': 950000000,
        'devise': 'XOF',
        'statut': 'termine',
        'taux_avancement': 100,
        'objectifs': [
            ('strategique', 'OS-01', 'Renforcer la gouvernance locale et la participation citoyenne'),
            ('strategique', 'OS-02', 'Ameliorer la gestion des finances et des services publics locaux'),
            ('specifique', 'OS-03', 'Elaborer des plans de developpement local dans 30 communes'),
            ('resultat', 'R-01', 'Plans de developpement local valides et mis en oeuvre dans toutes les communes ciblees'),
        ],
    },
]

# ============================================================================
# DONNEES PROJETS
# ============================================================================
PROJETS_DATA = [
    # Projets du PRCC
    {
        'code': 'PROJ-2024-001',
        'titre': 'Projet Sante Communautaire – Region d\'Abidjan',
        'description': 'Renforcement du systeme de sante communautaire dans les districts d\'Abidjan-Nord et Abidjan-Sud avec formation d\'agents de sante, rehabilitation de centres de sante et distribution de medicaments essentiels.',
        'programme_code': 'PROG-2026-001',
        'date_debut': '2024-03-01', 'date_fin_prevue': '2026-08-31',
        'budget_initial': 350000000, 'devise': 'XOF',
        'priorite': 'haute', 'statut': 'en_cours', 'taux_avancement': 62,
        'zone': 'ABJ',
    },
    {
        'code': 'PROJ-2024-002',
        'titre': 'Projet Education et Alphabetisation des Femmes – Bouake',
        'description': 'Programme d\'alphabetisation des femmes adultes et de scolarisation des filles dans 25 villages de la region de Bouake. Creation de 15 centres d\'alphabetisation et formation de 45 alphabetiseurs.',
        'programme_code': 'PROG-2026-001',
        'date_debut': '2024-06-01', 'date_fin_prevue': '2026-12-31',
        'budget_initial': 185000000, 'devise': 'XOF',
        'priorite': 'haute', 'statut': 'en_cours', 'taux_avancement': 45,
        'zone': 'BKO',
    },
    {
        'code': 'PROJ-2025-003',
        'titre': 'Projet Activites Generatrices de Revenus – Femmes Rurales Korhogo',
        'description': 'Appui a la creation et au developpement de 120 activites generatrices de revenus pour les femmes rurales de la region de Korhogo : transformation agroalimentaire, artisanat, petit commerce.',
        'programme_code': 'PROG-2026-001',
        'date_debut': '2025-01-01', 'date_fin_prevue': '2027-06-30',
        'budget_initial': 220000000, 'devise': 'XOF',
        'priorite': 'normale', 'statut': 'en_cours', 'taux_avancement': 28,
        'zone': 'KOR',
    },
    {
        'code': 'PROJ-2024-004',
        'titre': 'Projet Eau Potable et Assainissement – Zones Rurales',
        'description': 'Construction de 35 points d\'eau potable et de 200 latrines ameliorees dans les villages ruraux depourvus d\'acces a l\'eau potable. Sensibilisation a l\'hygiene et l\'assainissement.',
        'programme_code': 'PROG-2026-001',
        'date_debut': '2024-09-01', 'date_fin_prevue': '2025-08-31',
        'budget_initial': 275000000, 'devise': 'XOF',
        'priorite': 'critique', 'statut': 'termine', 'taux_avancement': 100,
        'zone': 'NAT',
    },
    # Projets d'AGRI-DEV
    {
        'code': 'PROJ-2025-005',
        'titre': 'Projet Cooperatives Agricoles et Marches – Region Ouest',
        'description': 'Creation et renforcement de 10 cooperatives agricoles dans la region de l\'Ouest. Appui a la mise en marche des produits agricoles via la creation de plateformes d\'agregation et de commercialisation.',
        'programme_code': 'PROG-2026-002',
        'date_debut': '2025-04-01', 'date_fin_prevue': '2028-03-31',
        'budget_initial': 420000000, 'devise': 'XOF',
        'priorite': 'haute', 'statut': 'en_cours', 'taux_avancement': 15,
        'zone': 'MAN',
    },
    {
        'code': 'PROJ-2025-006',
        'titre': 'Projet Agriculture Intelligente face au Climat – Savanes',
        'description': 'Introduction des techniques d\'agriculture intelligente face au climat dans la region des Savanes : varietes adaptees, techniques de conservation des sols, gestion rationnelle de l\'eau.',
        'programme_code': 'PROG-2026-002',
        'date_debut': '2025-07-01', 'date_fin_prevue': '2028-12-31',
        'budget_initial': 310000000, 'devise': 'XOF',
        'priorite': 'normale', 'statut': 'planifie', 'taux_avancement': 0,
        'zone': 'KOR',
    },
    # Projets de PROGOUV
    {
        'code': 'PROJ-2022-007',
        'titre': 'Projet Renforcement Capacites Elus Locaux – 30 Communes',
        'description': 'Formation intensive des elus locaux et du personnel communal en gestion administrative, financiere et technique. Mise en place de systemes d\'information de gestion communale.',
        'programme_code': 'PROG-2024-003',
        'date_debut': '2022-01-01', 'date_fin_prevue': '2024-12-31',
        'budget_initial': 380000000, 'devise': 'XOF',
        'priorite': 'haute', 'statut': 'cloture', 'taux_avancement': 100,
        'zone': 'NAT',
    },
    {
        'code': 'PROJ-2023-008',
        'titre': 'Projet Plans de Developpement Local Participatifs',
        'description': 'Elaboration participative des plans de developpement local dans 30 communes ciblees avec large mobilisation citoyenne, diagnostics territoriaux et ateliers de planification strategique.',
        'programme_code': 'PROG-2024-003',
        'date_debut': '2023-01-01', 'date_fin_prevue': '2025-06-30',
        'budget_initial': 195000000, 'devise': 'XOF',
        'priorite': 'normale', 'statut': 'cloture', 'taux_avancement': 100,
        'zone': 'NAT',
    },
]

# ============================================================================
# DONNEES CADRES LOGIQUES (template par projet)
# ============================================================================
def build_cadre_elements(projet_titre, domaine):
    return [
        # Niveau 1 : Objectif Global
        {
            'niveau': 'objectif_global',
            'code': 'OG',
            'description': f'Contribuer a l\'amelioration durable des conditions de vie des populations beneficiaires du {domaine}',
            'indicateurs_objectifs': 'Indice de developpement humain ameliore de 15 points\nTaux de pauvrete reduit de 25%',
            'sources_verification': 'Enquetes nationales sur les conditions de vie\nRapports INS\nEvaluations finales du programme',
            'hypotheses': 'Contexte politique et securitaire stable\nEngagement des autorites locales maintenu',
            'enfants': [
                {
                    'niveau': 'objectif_specifique',
                    'code': 'OS.1',
                    'description': f'Renforcer les capacites techniques et institutionnelles liees au {domaine} dans les zones ciblees',
                    'indicateurs_objectifs': '80% des beneficiaires appliquent les connaissances acquises\nNombre de structures renforcees augmente de 50%',
                    'sources_verification': 'Rapports de suivi trimestriels\nEnquetes de satisfaction\nVisites terrain',
                    'hypotheses': 'Volonte politique des autorites\nDisponibilite des ressources humaines qualifiees',
                    'enfants': [
                        {
                            'niveau': 'resultat',
                            'code': 'R.1.1',
                            'description': f'Les acteurs cles du {domaine} disposent des competences necessaires pour conduire leurs missions',
                            'indicateurs_objectifs': '500 agents formes avec un taux de satisfaction superieur a 80%\n90% des participants reussissent les evaluations finales',
                            'sources_verification': 'Fiches d\'evaluation des formations\nRapports des formateurs\nTests de connaissance',
                            'hypotheses': 'Disponibilite des beneficiaires aux formations\nQualite des formateurs assuree',
                            'enfants': [
                                {
                                    'niveau': 'activite',
                                    'code': 'A.1.1.1',
                                    'description': 'Concevoir et dispenser les modules de formation adaptes aux besoins identifies',
                                    'indicateurs_objectifs': '12 modules de formation developpes\n24 sessions de formation organisees',
                                    'sources_verification': 'Supports de formation valides\nFeuilles de presence\nPV de formation',
                                    'hypotheses': 'Budget de formation disponible\nLogistique assuree',
                                    'enfants': [
                                        {
                                            'niveau': 'sous_activite',
                                            'code': 'SA.1.1.1.1',
                                            'description': 'Realiser l\'evaluation des besoins en formation (EBF) aupres des beneficiaires cibles',
                                            'indicateurs_objectifs': 'EBF realisee dans 100% des zones ciblees\nRapport EBF valide',
                                            'sources_verification': 'Rapport d\'evaluation des besoins\nQuestionnaires remplis',
                                            'hypotheses': 'Acces aux zones garantis',
                                        },
                                        {
                                            'niveau': 'sous_activite',
                                            'code': 'SA.1.1.1.2',
                                            'description': 'Recruter et briefer les formateurs certifies pour les modules techniques',
                                            'indicateurs_objectifs': '15 formateurs recrutes et briefes\nContrats signes',
                                            'sources_verification': 'Contrats de consultation\nRapports de briefing',
                                            'hypotheses': 'Formateurs competents disponibles sur le marche',
                                        },
                                    ],
                                },
                                {
                                    'niveau': 'activite',
                                    'code': 'A.1.1.2',
                                    'description': 'Organiser des visites d\'etude et d\'echange de bonnes pratiques',
                                    'indicateurs_objectifs': '4 visites d\'etude organisees\n80 participants aux visites',
                                    'sources_verification': 'Rapports de visite\nListes de participants\nPhotographies',
                                    'hypotheses': 'Autorisations de deplacement accordees',
                                    'enfants': [],
                                },
                            ],
                        },
                        {
                            'niveau': 'resultat',
                            'code': 'R.1.2',
                            'description': f'Les infrastructures et equipements necessaires au {domaine} sont disponibles et fonctionnels',
                            'indicateurs_objectifs': '95% des infrastructures prevues livrees\nTaux de fonctionnalite superieur a 85% a 6 mois',
                            'sources_verification': 'PV de reception des travaux\nRapports d\'inspection\nEvaluations techniques',
                            'hypotheses': 'Qualite des materiaux assuree\nEntreprises competentes selectionnees',
                            'enfants': [
                                {
                                    'niveau': 'activite',
                                    'code': 'A.1.2.1',
                                    'description': 'Realiser les etudes techniques de faisabilite et les plans d\'execution',
                                    'indicateurs_objectifs': 'Etudes validees dans 100% des sites\nPlans d\'execution approuves',
                                    'sources_verification': 'Rapports d\'etudes techniques\nPlans architecturaux\nDevis quantitatifs',
                                    'hypotheses': 'Bureaux d\'etudes competents disponibles',
                                    'enfants': [],
                                },
                            ],
                        },
                    ],
                },
                {
                    'niveau': 'objectif_specifique',
                    'code': 'OS.2',
                    'description': f'Ameliorer l\'acces equitable aux services lies au {domaine} pour les groupes vulnerables',
                    'indicateurs_objectifs': 'Taux d\'acces des groupes vulnerables augmente de 40%\n70% des beneficiaires directs sont des femmes',
                    'sources_verification': 'Enquetes acces aux services\nRegistres des beneficiaires\nRapports des partenaires',
                    'hypotheses': 'Acceptation des groupes cibles\nAbsence de conflits communautaires',
                    'enfants': [
                        {
                            'niveau': 'resultat',
                            'code': 'R.2.1',
                            'description': 'Les mecanismes de ciblage et d\'inclusion des groupes vulnerables sont effectifs',
                            'indicateurs_objectifs': 'Systeme de ciblage valide et operationnel\n60% des beneficiaires issus de menages vulnerables',
                            'sources_verification': 'Criteres de ciblage documentes\nListes de beneficiaires verifiees\nRapports de conformite',
                            'hypotheses': 'Donnees sur les menages vulnerables disponibles',
                            'enfants': [
                                {
                                    'niveau': 'activite',
                                    'code': 'A.2.1.1',
                                    'description': 'Realiser le cartographie et le recensement des menages vulnerables dans les zones d\'intervention',
                                    'indicateurs_objectifs': '100% des zones cartographiees\nBase de donnees beneficiaires constituee',
                                    'sources_verification': 'Cartes d\'intervention\nBase de donnees validee\nPV de validation',
                                    'hypotheses': 'Cooperation des autorites locales',
                                    'enfants': [],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
    ]


# ============================================================================
# DONNEES SWOT (template par projet)
# ============================================================================
def build_swot_elements(domaine):
    return {
        'forces': [
            {'desc': f'Expertise technique reconnue dans le domaine du {domaine}', 'pond': 5},
            {'desc': 'Forte implantation locale et reseaux communautaires etendus', 'pond': 4},
            {'desc': 'Equipe pluridisciplinaire et experience confirmee en gestion de projets', 'pond': 4},
            {'desc': 'Partenariats solides avec les institutions gouvernementales et les bailleurs', 'pond': 3},
            {'desc': 'Systeme de suivi-evaluation robuste et base de donnees beneficiaires fiable', 'pond': 3},
        ],
        'faiblesses': [
            {'desc': 'Turnover frequent du personnel de terrain limitant la continuite des actions', 'pond': 4},
            {'desc': 'Dependance elevee aux financements exterieurs fragilisant la durabilite', 'pond': 4},
            {'desc': 'Capacites logistiques insuffisantes pour les zones d\'acces difficile', 'pond': 3},
            {'desc': 'Systeme de reporting interne perfectible et parfois chronophage', 'pond': 2},
        ],
        'opportunites': [
            {'desc': 'Priorite gouvernementale accordee au developpement du ' + domaine, 'pond': 5},
            {'desc': 'Disponibilite croissante de financements innovants (fonds verts, impact investing)', 'pond': 4},
            {'desc': 'Digitalisation croissante facilitant la collecte et l\'analyse des donnees', 'pond': 4},
            {'desc': 'Dynamique positive de la cooperation Sud-Sud et des echanges de bonnes pratiques', 'pond': 3},
            {'desc': 'Engagement croissant des collectivites locales dans le co-portage des projets', 'pond': 3},
        ],
        'menaces': [
            {'desc': 'Instabilite institutionnelle et risques politiques dans les zones d\'intervention', 'pond': 4},
            {'desc': 'Effets du changement climatique impactant les conditions d\'intervention', 'pond': 4},
            {'desc': 'Concurrence accrue entre ONG pour l\'acces aux financements disponibles', 'pond': 3},
            {'desc': 'Inflation des couts operationnels reductrice des marges de manoeuvre budgetaires', 'pond': 3},
            {'desc': 'Lenteur des procedures administratives des partenaires gouvernementaux', 'pond': 2},
        ],
    }

SWOT_STRATEGIES = [
    {
        'type_strategie': 'FO',
        'titre': 'Capitaliser sur l\'expertise pour saisir les nouvelles opportunites de financement',
        'description': 'Mobiliser l\'expertise technique reconnue et les partenariats etablis pour positionner strategiquement l\'organisation sur les nouveaux instruments de financement innovants et les appels d\'offres prioritaires.',
        'priorite': 'haute',
    },
    {
        'type_strategie': 'FM',
        'titre': 'Renforcer la resilience institutionnelle face aux risques politiques',
        'description': 'Utiliser la solidite des partenariats locaux et la diversification geographique pour attenuer l\'exposition aux risques politiques et securitaires dans les zones d\'intervention.',
        'priorite': 'haute',
    },
    {
        'type_strategie': 'FaO',
        'titre': 'Digitaliser la gestion pour reduire les faiblesses operationnelles',
        'description': 'Tirer parti de la digitalisation croissante pour moderniser les systemes de reporting, ameliorer la gestion des ressources humaines et renforcer la continuite operationnelle malgre le turnover du personnel.',
        'priorite': 'moyenne',
    },
    {
        'type_strategie': 'FaM',
        'titre': 'Diversifier les sources de financement pour reduire la vulnerabilite',
        'description': 'Adresser la dependance au financement exterieur en developpant une strategie de diversification : partenariats public-prive, fonds nationaux, contributions en nature des communautes et valorisation des ressources locales.',
        'priorite': 'haute',
    },
]

# ============================================================================
# DONNEES TACHES (tous les statuts)
# ============================================================================
TACHES_DATA = [
    # A faire
    {'titre': 'Elaborer le plan de communication du programme PRCC pour 2026', 'priorite': 'haute', 'statut': 'a_faire', 'description': 'Concevoir le plan de communication interne et externe pour l\'annee 2026, incluant la strategie digitale et les outils de visibilite.', 'echeance_delta': 20, 'avancement': 0},
    {'titre': 'Preparer le dossier de candidature au Fonds d\'Innovation AFD', 'priorite': 'critique', 'statut': 'a_faire', 'description': 'Constituer et finaliser le dossier complet de candidature pour l\'appel a propositions AFD 2026 avant la date de cloture.', 'echeance_delta': 45, 'avancement': 0},
    {'titre': 'Identifier et selectionner les partenaires de mise en oeuvre pour la phase 2', 'priorite': 'normale', 'statut': 'a_faire', 'description': 'Lancer le processus de selection des ONG partenaires locales pour la mise en oeuvre de la phase 2 du programme dans les nouvelles zones.', 'echeance_delta': 60, 'avancement': 0},
    {'titre': 'Rediger les termes de reference pour l\'evaluation a mi-parcours', 'priorite': 'haute', 'statut': 'a_faire', 'description': 'Elaborer les TDR detailles pour le recrutement du cabinet d\'evaluation charge de la revue a mi-parcours du programme PRCC.', 'echeance_delta': 30, 'avancement': 0},

    # En cours
    {'titre': 'Former les 85 agents de sante communautaires – Module nutrition', 'priorite': 'haute', 'statut': 'en_cours', 'description': 'Dispenser le module de formation sur la nutrition infantile aux agents de sante communautaires dans la region d\'Abidjan-Nord.', 'echeance_delta': 10, 'avancement': 55},
    {'titre': 'Mettre en place le systeme de suivi des beneficiaires numerise', 'priorite': 'critique', 'statut': 'en_cours', 'description': 'Deployer l\'application mobile de suivi des beneficiaires et former les 25 enqueteurs terrain a son utilisation.', 'echeance_delta': 15, 'avancement': 70},
    {'titre': 'Realiser les enquetes baseline dans les 12 nouveaux villages', 'priorite': 'haute', 'statut': 'en_cours', 'description': 'Conduire les enquetes de situation de reference dans les 12 villages integres dans la phase 2 du projet sante.', 'echeance_delta': 8, 'avancement': 40},
    {'titre': 'Elaborer le rapport d\'activites mensuel – Mai 2026', 'priorite': 'normale', 'statut': 'en_cours', 'description': 'Consolider les donnees de toutes les equipes terrain et rediger le rapport mensuel de mai 2026 pour transmission aux bailleurs.', 'echeance_delta': 5, 'avancement': 80},

    # En attente
    {'titre': 'Signer les accords de sous-subvention avec les ONG partenaires', 'priorite': 'critique', 'statut': 'en_attente', 'description': 'Finaliser et signer les accords de sous-subvention – en attente de la validation juridique des contrats par le bailleur.', 'echeance_delta': 12, 'avancement': 30},
    {'titre': 'Lancer les travaux de construction des 8 centres de sante', 'priorite': 'haute', 'statut': 'en_attente', 'description': 'Demarrer les travaux – en attente de l\'obtention des permis de construire aupres des mairies concernees.', 'echeance_delta': 25, 'avancement': 10},
    {'titre': 'Recevoir les equipements medicaux commandes – Lots 2 et 3', 'priorite': 'haute', 'statut': 'en_attente', 'description': 'Receptionner et distribuer les equipements medicaux – en attente de livraison du fournisseur (delai annonce : 3 semaines).', 'echeance_delta': 21, 'avancement': 0},

    # A valider
    {'titre': 'Valider le rapport d\'evaluation des besoins en formation – Region Korhogo', 'priorite': 'haute', 'statut': 'a_valider', 'description': 'Le rapport EBF est pret et soumis pour validation hierarchique avant diffusion aux formateurs.', 'echeance_delta': 3, 'avancement': 95},
    {'titre': 'Approuver le plan d\'action actualise Q2 2026', 'priorite': 'critique', 'statut': 'a_valider', 'description': 'Plan d\'action du deuxieme trimestre finalise et soumis au Directeur Executif pour approbation avant implementation.', 'echeance_delta': 2, 'avancement': 90},
    {'titre': 'Valider les criteres de selection des beneficiaires – AGR Femmes Rurales', 'priorite': 'normale', 'statut': 'a_valider', 'description': 'Criteres de ciblage et de selection des femmes beneficiaires des AGR soumis pour validation par le Comite de Pilotage.', 'echeance_delta': 5, 'avancement': 95},

    # Terminees
    {'titre': 'Realiser la mission de suivi terrain – Bouake – Avril 2026', 'priorite': 'haute', 'statut': 'terminee', 'description': 'Mission de suivi et d\'appui conseil aux equipes terrain de Bouake pour evaluer l\'avancement des activites du projet education.', 'echeance_delta': -10, 'avancement': 100},
    {'titre': 'Organiser l\'atelier de lancement de la phase 2 du PRCC', 'priorite': 'haute', 'statut': 'terminee', 'description': 'Atelier de lancement officiel de la deuxieme phase du programme avec tous les partenaires et les autorites locales.', 'echeance_delta': -20, 'avancement': 100},
    {'titre': 'Recruter et integrer les 5 nouveaux agents de terrain', 'priorite': 'normale', 'statut': 'terminee', 'description': 'Processus de recrutement, selection et integration des 5 nouveaux agents de terrain pour renforcer les equipes regionales.', 'echeance_delta': -15, 'avancement': 100},
    {'titre': 'Preparer et transmettre le rapport semestriel S2 2025', 'priorite': 'critique', 'statut': 'terminee', 'description': 'Rapport semestriel du second semestre 2025 finalise, valide et transmis a tous les bailleurs dans les delais.', 'echeance_delta': -45, 'avancement': 100},

    # Annulees
    {'titre': 'Organiser la foire agricole regionale – edition 2026 (annulee)', 'priorite': 'normale', 'statut': 'annulee', 'description': 'Foire agricole prevue en fevrier 2026 – annulee en raison des conditions meteorologiques defavorables et de la disponibilite insuffisante des exposants.', 'echeance_delta': -30, 'avancement': 15},
    {'titre': 'Mettre en place une radio communautaire locale (annulee)', 'priorite': 'faible', 'statut': 'annulee', 'description': 'Projet de creation d\'une radio communautaire annule suite au refus d\'agrement par l\'autorite de regulation de l\'audiovisuel.', 'echeance_delta': -60, 'avancement': 5},

    # Bloquees
    {'titre': 'Debuter les travaux de rehabilitation de la piste rurale de Soungalodougou', 'priorite': 'critique', 'statut': 'bloquee', 'description': 'Travaux bloques en raison d\'un litige foncier entre deux communautes sur le trace de la piste. Mediation en cours.', 'echeance_delta': -5, 'avancement': 20},
    {'titre': 'Importer les semences ameliorees pour la campagne agricole principale', 'priorite': 'critique', 'statut': 'bloquee', 'description': 'Importation bloquee aux douanes faute de certificat phytosanitaire. Dossier en cours de regularisation avec le Ministere de l\'Agriculture.', 'echeance_delta': -3, 'avancement': 35},
]

# ============================================================================
# DONNEES MISSIONS
# ============================================================================
MISSIONS_DATA = [
    {
        'objet': 'Mission de suivi et d\'appui technique – Projet Sante Communautaire Abidjan',
        'type_mission': 'supervision',
        'description': 'Mission de supervision et d\'appui technique aux equipes du projet sante pour evaluer l\'avancement, identifier les blocages et proposer des solutions correctives.',
        'destination': 'Abidjan – Districts nord et sud',
        'lieu_depart': 'Siege social Abidjan Plateau',
        'objectifs': '1. Evaluer l\'avancement physique et financier\n2. Appuyer les equipes dans la resolution des blocages\n3. Valider les donnees du systeme de suivi',
        'resultats_attendus': 'Rapport de supervision avec recommandations\nPlan d\'actions correctives\nDonnees de suivi validees',
        'date_debut_delta': -15, 'date_fin_delta': -12,
        'budget_prevu': 350000, 'budget_realise': 328000,
        'statut': 'terminee',
    },
    {
        'objet': 'Mission de negociation partenariat – Conseil Regional du Gbeke',
        'type_mission': 'partenariat',
        'description': 'Mission de negociation et de signature du protocole de partenariat avec le Conseil Regional du Gbeke pour la mise en oeuvre conjointe du projet d\'eau potable en zone rurale.',
        'destination': 'Bouake – Siege Conseil Regional',
        'lieu_depart': 'Abidjan',
        'objectifs': '1. Presenter le projet aux autorites regionales\n2. Negocier les termes du protocole de partenariat\n3. Signer le protocole',
        'resultats_attendus': 'Protocole de partenariat signe\nPlan d\'action conjoint elabore',
        'date_debut_delta': -8, 'date_fin_delta': -7,
        'budget_prevu': 180000, 'budget_realise': 165000,
        'statut': 'terminee',
    },
    {
        'objet': 'Mission de formation des agents multiplicateurs – Module AGR',
        'type_mission': 'formation',
        'description': 'Mission de formation des formateurs locaux en techniques de gestion des activites generatrices de revenus pour les femmes rurales de la region de Korhogo.',
        'destination': 'Korhogo',
        'lieu_depart': 'Abidjan',
        'objectifs': '1. Former 20 agents multiplicateurs en gestion d\'AGR\n2. Tester les outils pedagogiques adaptes\n3. Elaborer le plan de deploiement des formations communautaires',
        'resultats_attendus': '20 agents formes et certifies\nOutils pedagogiques valides\nCalendrier de deploiement elabore',
        'date_debut_delta': 5, 'date_fin_delta': 7,
        'budget_prevu': 520000, 'budget_realise': 0,
        'statut': 'approuvee',
    },
    {
        'objet': 'Mission de supervision Banque Mondiale – Revue a mi-parcours PRCC',
        'type_mission': 'evaluation',
        'description': 'Mission de revue a mi-parcours de la Banque Mondiale pour evaluer les performances du programme PRCC et valider les ajustements proposes pour la seconde phase.',
        'destination': 'Abidjan, Bouake, Korhogo',
        'lieu_depart': 'Abidjan (accueil delegation BM)',
        'objectifs': '1. Evaluer les performances globales du programme\n2. Verifier la conformite fiduciaire\n3. Valider les ajustements de la phase 2\n4. Identifier les lecons apprises',
        'resultats_attendus': 'Rapport de supervision BM\nRecommandations formelles\nAjustements valides\nRating du programme maintenu ou ameliore',
        'date_debut_delta': 10, 'date_fin_delta': 20,
        'budget_prevu': 1200000, 'budget_realise': 0,
        'statut': 'planifiee',
    },
    {
        'objet': 'Mission terrain de collecte de donnees – Enquete beneficiaires S1 2026',
        'type_mission': 'terrain',
        'description': 'Mission de collecte de donnees terrain aupres des beneficiaires directs et indirects du programme pour le rapport de suivi du premier semestre 2026.',
        'destination': '45 villages dans les regions d\'Abidjan, Bouake et Korhogo',
        'lieu_depart': 'Abidjan',
        'objectifs': '1. Collecter les donnees sur les 25 indicateurs de suivi\n2. Conduire les focus groupes communautaires\n3. Valider les donnees sur le terrain',
        'resultats_attendus': 'Base de donnees beneficiaires mise a jour\nRapport de collecte\nDonnees validees pour le rapport semestriel',
        'date_debut_delta': -5, 'date_fin_delta': -1,
        'budget_prevu': 840000, 'budget_realise': 750000,
        'statut': 'en_cours',
    },
    {
        'objet': 'Mission d\'audit financier externe – Exercice 2025',
        'type_mission': 'audit',
        'description': 'Mission d\'audit financier externe de l\'exercice 2025 menee par le cabinet independant selectionne conformement aux procedures des bailleurs.',
        'destination': 'Abidjan – Siege et antennes regionales',
        'lieu_depart': 'Cabinet d\'audit Abidjan',
        'objectifs': '1. Auditer les comptes de l\'exercice 2025\n2. Verifier la conformite des depenses\n3. Evaluer le systeme de controle interne',
        'resultats_attendus': 'Rapport d\'audit certifie\nLettre de recommandations\nPlan d\'amelioration du controle interne',
        'date_debut_delta': 20, 'date_fin_delta': 35,
        'budget_prevu': 3500000, 'budget_realise': 0,
        'statut': 'planifiee',
    },
    {
        'objet': 'Mission de prospection nouveaux partenaires – Region de Man',
        'type_mission': 'partenariat',
        'description': 'Mission de prospection et d\'identification de nouveaux partenaires locaux pour la mise en oeuvre du projet cooperatives agricoles dans la region de Man.',
        'destination': 'Man – Region de l\'Ouest',
        'lieu_depart': 'Abidjan',
        'objectifs': '1. Cartographier les acteurs locaux potentiels\n2. Conduire des entretiens exploratoires\n3. Identifier 3 a 5 partenaires viables',
        'resultats_attendus': 'Cartographie des acteurs\nFiches de presentation des partenaires potentiels\nRecommandations de partenariat',
        'date_debut_delta': -40, 'date_fin_delta': -37,
        'budget_prevu': 290000, 'budget_realise': 0,
        'statut': 'annulee',
    },
]

# ============================================================================
# DONNEES RAPPORTS D'AVANCEMENT
# ============================================================================
RAPPORTS_DATA = [
    {
        'periode': 'mensuel',
        'date_delta': -5,
        'taux_realisation': 78,
        'observations': 'Le mois de mai 2026 a ete marque par l\'intensification des activites de formation. 85 agents de sante ont ete formes, soit 92% de la cible trimestrielle. Les activites AGR progressent conformement au calendrier.',
        'problemes': '- Retard dans la livraison des equipements medicaux (lots 2 et 3) du au delai du fournisseur\n- Acces difficile a 3 villages de montagne en raison des pluies precoces\n- Turnover d\'un coordinateur regional ayant necessite un remplacement urgent',
        'recommandations': '- Anticiper les commandes d\'equipements pour le trimestre prochain\n- Prevoir des voies d\'acces alternatives pour les villages isoles\n- Renforcer le programme de retention du personnel cle',
        'prochaines_etapes': '- Livraison et distribution des equipements medicaux (semaine 1 de juin)\n- Demarrage des formations en nutrition infantile dans 5 nouveaux sites\n- Preparation du rapport trimestriel Q2 2026',
        'statut': 'valide',
    },
    {
        'periode': 'trimestriel',
        'date_delta': -15,
        'taux_realisation': 72,
        'observations': 'Rapport d\'avancement du premier trimestre 2026. Le taux d\'execution physique global est de 72%, legerement en dessous de la cible de 75%. Les activites de formation sont en avance (+15%) tandis que les travaux de construction accusent un retard de 3 semaines.',
        'problemes': '- Retard dans l\'obtention des permis de construire dans 2 communes\n- Hausse imprevisible du cout des materiaux de construction (+12%)\n- Difficultes de coordination avec le service de sante departemental\n- Un bailleur secondaire a tarde dans le deblocage des fonds de la tranche Q1',
        'recommandations': '- Accelerer les demarches aupres des mairies pour les permis de construire\n- Renogocier les contrats de travaux pour absorber la hausse des couts\n- Organiser une reunion de coordination inter-institutionnelle mensuelle\n- Formaliser un protocole de versement des fonds avec les bailleurs',
        'prochaines_etapes': '- Obtention des permis de construire et demarrage des travaux en Q2\n- Formation de 200 agents de sante supplementaires\n- Lancement de l\'enquete baseline dans les 12 nouveaux villages\n- Preparation de la revue a mi-parcours prevue pour Q3 2026',
        'statut': 'publie',
    },
    {
        'periode': 'semestriel',
        'date_delta': -90,
        'taux_realisation': 68,
        'observations': 'Rapport semestriel S2 2025. Ce semestre a ete marque par la mise en place des structures institutionnelles du programme, le recrutement de l\'equipe et le demarrage des premieres activites terrain. Le taux d\'execution est de 68%, conforme aux previsions pour une phase de demarrage.',
        'problemes': '- Retards dans le processus de recrutement du personnel specialise\n- Procedures de passation des marches plus longues que prevu\n- Quelques resistances initiales dans certaines communautes necessitant un travail de sensibilisation approfondi',
        'recommandations': '- Simplifier les procedures de recrutement avec validation par email\n- Anticiper les marches recurrents par des contrats cadres\n- Renforcer l\'equipe de facilitation communautaire',
        'prochaines_etapes': '- Montee en puissance des activites terrain en 2026\n- Recrutement des 5 coordinateurs regionaux restants\n- Lancement du systeme de suivi-evaluation numerise',
        'statut': 'publie',
    },
    {
        'periode': 'mensuel',
        'date_delta': -35,
        'taux_realisation': 65,
        'observations': 'Rapport du mois d\'avril 2026. Activites conformes aux previsions dans les regions d\'Abidjan et Bouake. La region de Korhogo enregistre un retard de 2 semaines sur les formations AGR suite aux conditions meteorologiques.',
        'problemes': '- Pluies exceptionnelles ayant bloque l\'acces a plusieurs villages de Korhogo\n- Panne du vehicule de l\'equipe terrain de Korhogo pendant 5 jours',
        'recommandations': '- Prevoir des vehicules de substitution en cas de panne\n- Adapter le calendrier des activites aux conditions saisonnieres',
        'prochaines_etapes': '- Rattrapage du retard de formation en mai-juin\n- Reparation ou remplacement du vehicule en panne',
        'statut': 'soumis',
    },
    {
        'periode': 'mensuel',
        'date_delta': -65,
        'taux_realisation': 58,
        'observations': 'Rapport du mois de mars 2026. Phase de demarrage des nouvelles activites de la periode. Les formations ont debute dans 3 regions avec des retours tres positifs des beneficiaires. Le taux de completion des modules est de 94%.',
        'problemes': '- Retard dans la validation des criteres de selection des beneficiaires AGR\n- Sous-effectif temporaire dans l\'equipe comptable',
        'recommandations': '- Accelerer la validation des criteres de selection\n- Recruter un comptable adjoint pour renforcer l\'equipe financiere',
        'prochaines_etapes': '- Validation et diffusion des criteres de selection\n- Demarrage des formations AGR en avril\n- Recrutement du comptable adjoint',
        'statut': 'brouillon',
    },
    {
        'periode': 'trimestriel',
        'date_delta': -110,
        'taux_realisation': 55,
        'observations': 'Rapport trimestriel Q4 2025. Cloture de l\'annee 2025 avec un taux d\'execution global de 55%, inferieur a la cible de 65% principalement en raison des retards de demarrage. Des mesures correctives ont ete implementees pour accelerer l\'execution en 2026.',
        'problemes': '- Demarrage effectif retarde de 2 mois par rapport au calendrier initial\n- Processus d\'approvisionnement plus long que prevu\n- Difficultes d\'acces a la documentation requise par certains bailleurs',
        'recommandations': '- Reviser le calendrier d\'execution pour tenir compte des delais reels\n- Simplifier les procedures d\'approvisionnement pour les petits montants\n- Etablir une liste de documents standards avec les bailleurs des le debut',
        'prochaines_etapes': '- Rattrapage progressif du retard en 2026\n- Intensification des activites terrain des le mois de janvier\n- Revision du cadre logique pour tenir compte des conditions initiales',
        'statut': 'publie',
    },
]


class Command(BaseCommand):
    help = 'Cree les donnees de demonstration pour programmes, projets, cadres logiques, SWOT, taches, missions et rapports'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les donnees existantes avant de recreer')

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        with transaction.atomic():
            admin = self._get_admin()
            if not admin:
                self.stdout.write(self.style.ERROR('[ERREUR] Aucun administrateur. Lancez seed_lot1 d\'abord.'))
                return

            users = list(__import__('accounts').models.User.objects.all()[:10])
            org   = self._get_org(admin)
            zones = self._get_zones()

            programmes = self._seed_programmes(admin, org, zones, users)
            projets    = self._seed_projets(admin, org, zones, programmes, users)
            self._seed_cadres_logiques(admin, projets)
            self._seed_swot(admin, projets)
            self._seed_taches(admin, users, projets)
            self._seed_missions(admin, projets)
            self._seed_rapports(admin, projets)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed projets termine avec succes !'))

    # -- Reset -----------------------------------------------------------------
    def _reset(self):
        from planification.models import CadreLogique, AnalyseSWOT
        from execution.models import Tache, Mission, RapportAvancement
        from programmes_projets.models import Programme, Projet, ObjectifProgramme

        self.stdout.write(self.style.WARNING('[RESET] Suppression donnees existantes...'))
        RapportAvancement.objects.all().delete()
        Mission.objects.all().delete()
        Tache.objects.all().delete()
        AnalyseSWOT.objects.all().delete()
        CadreLogique.objects.all().delete()
        Projet.objects.all().delete()
        Programme.objects.all().delete()
        self.stdout.write('   Termine.')

    # -- Helpers ---------------------------------------------------------------
    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_org(self, admin):
        from gouvernance.models import Organisation
        org, _ = Organisation.objects.get_or_create(
            sigle='ONG-DEMO',
            defaults={
                'nom': 'ONG Demonstration ERP',
                'type_organisation': 'ong',
                'pays': "Cote d'Ivoire",
                'ville': 'Abidjan',
                'email': 'contact@ong-demo.ci',
            }
        )
        return org

    def _get_zones(self):
        from programmes_projets.models import ZoneIntervention
        zones_map = {}
        for code, nom, region in [
            ('ABJ', 'Abidjan', 'Lagunes'),
            ('BKO', 'Bouake', 'Vallee du Bandama'),
            ('KOR', 'Korhogo', 'Savanes'),
            ('MAN', 'Man', 'Montagnes'),
            ('NAT', 'National', 'Tout le territoire'),
        ]:
            z, _ = ZoneIntervention.objects.get_or_create(
                code=code,
                defaults={'nom': nom, 'pays': "Cote d'Ivoire", 'region': region}
            )
            zones_map[code] = z
        return zones_map

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Cree') if created else self.style.WARNING('Existant')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:80]}')

    # -- Programmes ------------------------------------------------------------
    def _seed_programmes(self, admin, org, zones, users):
        from programmes_projets.models import Programme, ObjectifProgramme

        self.stdout.write('\n>> Programmes...')
        result = {}

        for data in PROGRAMMES_DATA:
            prog, created = Programme.objects.get_or_create(
                code=data['code'],
                defaults={
                    'intitule': data['intitule'],
                    'acronyme': data['acronyme'],
                    'description': data['description'],
                    'contexte': data['contexte'],
                    'impacts_attendus': data['impacts_attendus'],
                    'organisation': org,
                    'coordonnateur': admin,
                    'responsable': admin,
                    'date_debut': parse_date(data['date_debut']),
                    'date_fin': parse_date(data['date_fin']),
                    'budget_total': data['budget_total'],
                    'devise': data['devise'],
                    'statut': data['statut'],
                    'taux_avancement': data['taux_avancement'],
                    'created_by': admin,
                }
            )
            self._log('Programme', prog, created)

            if created:
                all_zones = list(zones.values())
                prog.zones_intervention.set(random.sample(all_zones, min(3, len(all_zones))))
                if users:
                    prog.equipe.set(random.sample(users, min(3, len(users))))

                for type_obj, code, libelle in data.get('objectifs', []):
                    ObjectifProgramme.objects.create(
                        programme=prog,
                        type_objectif=type_obj,
                        code=code,
                        libelle=libelle,
                        ordre=list(data['objectifs']).index((type_obj, code, libelle)),
                    )

            result[data['code']] = prog

        return result

    # -- Projets ---------------------------------------------------------------
    def _seed_projets(self, admin, org, zones, programmes, users):
        from programmes_projets.models import Projet, MembreEquipeProjet, LivrableProjet, JalonProjet

        self.stdout.write('\n>> Projets...')
        result = {}

        for data in PROJETS_DATA:
            programme = programmes.get(data.get('programme_code'))
            projet, created = Projet.objects.get_or_create(
                code=data['code'],
                defaults={
                    'titre': data['titre'],
                    'description': data['description'],
                    'programme': programme,
                    'organisation': org,
                    'chef_projet': admin,
                    'date_debut': parse_date(data['date_debut']),
                    'date_fin_prevue': parse_date(data['date_fin_prevue']),
                    'budget_initial': data['budget_initial'],
                    'devise': data['devise'],
                    'priorite': data['priorite'],
                    'statut': data['statut'],
                    'taux_avancement': data['taux_avancement'],
                    'created_by': admin,
                }
            )
            self._log('Projet', projet, created)

            if created:
                zone_code = data.get('zone', 'NAT')
                if zone_code in zones:
                    projet.zones_intervention.set([zones[zone_code]])

                MembreEquipeProjet.objects.get_or_create(
                    projet=projet, user=admin,
                    defaults={'role_projet': 'chef_projet'}
                )
                if users:
                    for u in random.sample(users, min(2, len(users))):
                        MembreEquipeProjet.objects.get_or_create(
                            projet=projet, user=u,
                            defaults={'role_projet': random.choice(['coordinateur', 'responsable_activite', 'agent_terrain'])}
                        )

                # Livrables
                livrables = [
                    ('L-001', 'Rapport de demarrage', 'rapport', 15, 'valide'),
                    ('L-002', 'Plan de travail annuel', 'plan', 30, 'valide'),
                    ('L-003', 'Rapport semestriel S1', 'rapport', 180, 'valide' if data['taux_avancement'] > 50 else 'en_cours'),
                    ('L-004', 'Rapport final', 'rapport', 365, 'planifie' if data['taux_avancement'] < 80 else 'valide'),
                ]
                debut = parse_date(data['date_debut'])
                for code_l, titre_l, type_l, delta_l, statut_l in livrables:
                    LivrableProjet.objects.get_or_create(
                        projet=projet, code=code_l,
                        defaults={'titre': titre_l, 'type_livrable': type_l, 'date_prevue': debut + timedelta(days=delta_l), 'statut': statut_l}
                    )

                # Jalons
                jalons = [
                    ('Demarrage effectif du projet', 0, 'atteint'),
                    ('Premiere revue trimestrielle', 90, 'atteint' if data['taux_avancement'] > 20 else 'a_venir'),
                    ('Revue a mi-parcours', 180, 'atteint' if data['taux_avancement'] > 50 else 'a_venir'),
                    ('Revue finale et cloture', 330, 'atteint' if data['taux_avancement'] == 100 else 'a_venir'),
                ]
                for libelle_j, delta_j, statut_j in jalons:
                    JalonProjet.objects.get_or_create(
                        projet=projet, libelle=libelle_j,
                        defaults={'date_prevue': debut + timedelta(days=delta_j), 'statut': statut_j}
                    )

            result[data['code']] = projet

        return result

    # -- Cadres logiques -------------------------------------------------------
    def _seed_cadres_logiques(self, admin, projets):
        from planification.models import CadreLogique, ElementCadreLogique

        self.stdout.write('\n>> Cadres logiques...')

        domaines = [
            'sante communautaire', 'education et alphabetisation', 'activites generatrices de revenus',
            'eau et assainissement', 'agriculture cooperative', 'agriculture intelligente',
            'gouvernance locale', 'planification participative'
        ]

        for i, (code, projet) in enumerate(projets.items()):
            domaine = domaines[i % len(domaines)]
            statut_cadre = 'valide' if projet.taux_avancement > 30 else 'brouillon'

            cadre, created = CadreLogique.objects.get_or_create(
                projet=projet,
                defaults={
                    'titre': f'Cadre Logique – {projet.titre}',
                    'version': '2.0' if projet.taux_avancement > 50 else '1.0',
                    'description': f'Cadre logique du {projet.titre} definissant la hierarchie des objectifs, resultats et activites.',
                    'statut': statut_cadre,
                    'created_by': admin,
                    'valide_par': admin if statut_cadre == 'valide' else None,
                    'date_validation': timezone.now() if statut_cadre == 'valide' else None,
                }
            )
            self._log('Cadre logique', cadre, created)

            if created:
                self._create_elements(cadre, build_cadre_elements(projet.titre, domaine), None, admin)

    def _create_elements(self, cadre, elements_data, parent, admin):
        from planification.models import ElementCadreLogique
        for i, elem in enumerate(elements_data):
            obj = ElementCadreLogique.objects.create(
                cadre=cadre,
                parent=parent,
                niveau=elem['niveau'],
                code=elem['code'],
                description=elem['description'],
                indicateurs_objectifs=elem.get('indicateurs_objectifs', ''),
                sources_verification=elem.get('sources_verification', ''),
                hypotheses=elem.get('hypotheses', ''),
                ordre=i,
            )
            if elem.get('enfants'):
                self._create_elements(cadre, elem['enfants'], obj, admin)

    # -- SWOT ------------------------------------------------------------------
    def _seed_swot(self, admin, projets):
        from planification.models import AnalyseSWOT, ElementSWOT, StrategieSWOT

        self.stdout.write('\n>> Analyses SWOT...')

        domaines = ['sante', 'education', 'AGR', 'WASH', 'agriculture', 'agriculture climatique', 'gouvernance', 'planification']

        for i, (code, projet) in enumerate(projets.items()):
            domaine = domaines[i % len(domaines)]
            statut_swot = 'finalise' if projet.taux_avancement > 25 else 'brouillon'

            swot, created = AnalyseSWOT.objects.get_or_create(
                projet=projet,
                defaults={
                    'titre': f'Analyse SWOT – {projet.titre}',
                    'description': f'Analyse strategique des forces, faiblesses, opportunites et menaces du projet en matiere de {domaine}.',
                    'contexte': f'Cette analyse a ete realisee lors de la phase de planification du projet afin d\'identifier les facteurs internes et externes influencant sa mise en oeuvre.',
                    'date_analyse': date.today() - timedelta(days=random.randint(30, 180)),
                    'statut': statut_swot,
                    'created_by': admin,
                }
            )
            self._log('Analyse SWOT', swot, created)

            if created:
                elements_data = build_swot_elements(domaine)
                elements_crees = {'force': [], 'faiblesse': [], 'opportunite': [], 'menace': []}
                for cat, items in elements_data.items():
                    cat_key = cat[:-1] if cat.endswith('s') else cat
                    for j, item in enumerate(items):
                        el = ElementSWOT.objects.create(
                            analyse=swot,
                            categorie=cat_key,
                            description=item['desc'],
                            ponderation=item['pond'],
                            classement=j + 1,
                        )
                        elements_crees[cat_key].append(el)

                for strat in SWOT_STRATEGIES:
                    s = StrategieSWOT.objects.create(
                        analyse=swot,
                        type_strategie=strat['type_strategie'],
                        titre=strat['titre'],
                        description=strat['description'],
                        priorite=strat['priorite'],
                    )

    # -- Taches ----------------------------------------------------------------
    def _seed_taches(self, admin, users, projets):
        from execution.models import Tache

        self.stdout.write('\n>> Taches (tous statuts)...')
        today = date.today()
        projets_list = list(projets.values())

        for i, data in enumerate(TACHES_DATA):
            assignee = random.choice(users) if users else admin
            echeance = today + timedelta(days=data['echeance_delta'])

            tache, created = Tache.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'description': data['description'],
                    'priorite': data['priorite'],
                    'statut': data['statut'],
                    'assignee': assignee,
                    'date_debut': echeance - timedelta(days=14),
                    'date_echeance': echeance,
                    'date_completion': today + timedelta(days=data['echeance_delta']) if data['statut'] == 'terminee' else None,
                    'taux_avancement': data['avancement'],
                    'estimation_heures': random.choice([4, 8, 16, 24, 40]),
                    'heures_realisees': data['avancement'] * random.choice([4, 8, 16]) / 100,
                    'created_by': admin,
                    'ordre': i,
                }
            )
            self._log(f'Tache [{data["statut"]}]', tache, created)

    # -- Missions --------------------------------------------------------------
    def _seed_missions(self, admin, projets):
        from execution.models import Mission

        self.stdout.write('\n>> Missions (tous statuts)...')
        today = date.today()
        projets_list = list(projets.values())

        for i, data in enumerate(MISSIONS_DATA):
            projet = projets_list[i % len(projets_list)]
            date_debut = today + timedelta(days=data['date_debut_delta'])
            date_fin   = today + timedelta(days=data['date_fin_delta'])

            mission, created = Mission.objects.get_or_create(
                objet=data['objet'],
                defaults={
                    'type_mission': data['type_mission'],
                    'description': data['description'],
                    'projet': projet,
                    'lieu_depart': data.get('lieu_depart', 'Abidjan'),
                    'destination': data['destination'],
                    'date_debut': date_debut,
                    'date_fin': date_fin,
                    'budget_prevu': data['budget_prevu'],
                    'budget_realise': data.get('budget_realise', 0),
                    'demandeur': admin,
                    'approuve_par': admin if data['statut'] in ('approuvee', 'en_cours', 'terminee') else None,
                    'date_approbation': timezone.now() if data['statut'] in ('approuvee', 'en_cours', 'terminee') else None,
                    'statut': data['statut'],
                    'objectifs': data.get('objectifs', ''),
                    'resultats_attendus': data.get('resultats_attendus', ''),
                }
            )
            self._log(f'Mission [{data["statut"]}]', mission, created)

    # -- Rapports d'avancement -------------------------------------------------
    def _seed_rapports(self, admin, projets):
        from execution.models import RapportAvancement

        self.stdout.write('\n>> Rapports d\'avancement (tous statuts)...')
        today = date.today()
        projets_list = [p for p in projets.values() if p.statut in ('en_cours', 'termine', 'cloture')]
        if not projets_list:
            projets_list = list(projets.values())

        for i, data in enumerate(RAPPORTS_DATA):
            projet = projets_list[i % len(projets_list)]
            date_rapport = today + timedelta(days=data['date_delta'])

            rapport, created = RapportAvancement.objects.get_or_create(
                projet=projet,
                periode=data['periode'],
                date_rapport=date_rapport,
                defaults={
                    'taux_realisation': data['taux_realisation'],
                    'observations': data['observations'],
                    'problemes': data['problemes'],
                    'recommandations': data['recommandations'],
                    'prochaines_etapes': data['prochaines_etapes'],
                    'redacteur': admin,
                    'statut': data['statut'],
                    'valide_par': admin if data['statut'] in ('valide', 'publie') else None,
                    'date_validation': timezone.now() if data['statut'] in ('valide', 'publie') else None,
                }
            )
            self._log(f'Rapport [{data["statut"]}]', rapport, created)
