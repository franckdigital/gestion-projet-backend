"""
Seed M10 : Termes de Référence (TDR).

Crée des TDR réalistes de tous types et statuts avec sections structurées complètes :
  consultation, formation, étude, évaluation, audit, mission, recrutement.

Usage : python manage.py seed_tdr [--reset]
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


TDRS = [
    # -- Consultation ----------------------------------------------------------
    {
        'titre': 'TDR – Recrutement d\'un consultant en suivi-évaluation',
        'type': 'consultation',
        'statut': 'publie',
        'date_redaction_delta': -60,
        'budget': 8500000,
        'genere_ia': False,
        'contexte': (
            'Le Programme de Renforcement des Capacités Communautaires (PRCC) recherche un consultant '
            'expérimenté en suivi-évaluation pour appuyer l\'équipe programme dans le déploiement '
            'du système S&E, la collecte et l\'analyse des données d\'indicateurs, et la production '
            'des rapports d\'avancement.'
        ),
        'justification': (
            'Le poste de Responsable S&E étant vacant depuis 2 mois, le programme a besoin d\'un '
            'appui external pour assurer la continuité du système de suivi et la préparation de la '
            'revue à mi-parcours prévue en juin 2026.'
        ),
        'objectifs': (
            '1. Appuyer la mise en œuvre du système de suivi-évaluation du programme\n'
            '2. Former l\'équipe à l\'utilisation des outils numériques de collecte\n'
            '3. Analyser les données des indicateurs et produire les tableaux de bord\n'
            '4. Préparer les rapports trimestriels S&E\n'
            '5. Appuyer la préparation de la revue à mi-parcours'
        ),
        'resultats': (
            '- Système S&E opérationnel et alimenté en données\n'
            '- Tableau de bord trimestriel S&E produit\n'
            '- Rapport de revue à mi-parcours préparé\n'
            '- Équipe formée aux outils S&E numériques'
        ),
        'methodologie': (
            'Le consultant travaillera en étroite collaboration avec l\'équipe programme. '
            'Il utilisera une approche participative pour le renforcement de capacités, '
            'et les outils KoboToolbox/Power BI pour la gestion des données.'
        ),
        'livrables': (
            '1. Plan de travail détaillé – Semaine 1\n'
            '2. Rapport diagnostic du système S&E actuel – Semaine 2\n'
            '3. Tableau de bord S&E mis à jour – Mensuel\n'
            '4. Rapport trimestriel S&E Q2 2026\n'
            '5. Note de préparation revue à mi-parcours'
        ),
        'calendrier': '6 mois (avril – septembre 2026) – 20 jours/mois',
        'profil': (
            'Formation : Bac+5 en statistiques, démographie, sciences sociales ou discipline équivalente\n'
            'Expérience : Minimum 7 ans d\'expérience en S&E de projets/programmes de développement\n'
            'Compétences : Maîtrise KoboToolbox, SPSS/Stata, Excel avancé, Power BI\n'
            'Langues : Français courant exigé\n'
            'Références : Au moins 3 missions similaires au cours des 5 dernières années'
        ),
        'criteres': (
            'Évaluation technique (70%) :\n'
            '  - Formation et expérience générale : 20 pts\n'
            '  - Expérience spécifique S&E développement : 30 pts\n'
            '  - Méthodologie proposée : 20 pts\n'
            'Évaluation financière (30%) :\n'
            '  - Rapport qualité/prix de l\'offre financière'
        ),
        'modalites_paiement': '40% à la signature – 30% à mi-parcours – 30% à la livraison finale',
    },
    # -- Formation -------------------------------------------------------------
    {
        'titre': 'TDR – Formation des agents multiplicateurs en techniques AGR',
        'type': 'formation',
        'statut': 'valide',
        'date_redaction_delta': -20,
        'budget': 6200000,
        'genere_ia': False,
        'contexte': (
            'Dans le cadre de la composante développement économique du PRCC, le programme '
            'prévoit la formation de 20 agents multiplicateurs locaux en techniques de gestion '
            'des Activités Génératrices de Revenus (AGR), qui assureront ensuite la formation '
            'de 300 femmes rurales dans leurs zones d\'intervention.'
        ),
        'justification': (
            'La stratégie de formation en cascade permet d\'atteindre un plus grand nombre '
            'de bénéficiaires à moindre coût. Les agents multiplicateurs, issus des communautés, '
            'sont mieux acceptés et assurent une meilleure appropriation des compétences.'
        ),
        'objectifs': (
            '1. Former 20 agents multiplicateurs aux techniques AGR adaptées au contexte local\n'
            '2. Développer leurs compétences pédagogiques pour la formation communautaire\n'
            '3. Les certifier comme formateurs AGR reconnus par le programme\n'
            '4. Élaborer le plan de déploiement des formations communautaires'
        ),
        'resultats': (
            '- 20 agents certifiés formateurs AGR\n'
            '- Outils pédagogiques adaptés testés et validés\n'
            '- Plan de déploiement communautaire établi\n'
            '- Rapport de formation disponible'
        ),
        'methodologie': (
            'Formation-action de 5 jours :\n'
            '  J1-J2 : Modules techniques AGR (petite transformation, commerce, élevage)\n'
            '  J3    : Gestion financière simplifiée et accès au crédit\n'
            '  J4    : Techniques pédagogiques et animation communautaire\n'
            '  J5    : Mises en situation et évaluation des acquis'
        ),
        'livrables': (
            '- Guide du formateur AGR (adapté au contexte ivoirien)\n'
            '- Fiches techniques par type d\'AGR\n'
            '- Rapport de formation avec résultats d\'évaluation\n'
            '- Liste des 20 agents certifiés\n'
            '- Plan de déploiement communautaire'
        ),
        'calendrier': '5 jours de formation + 2 jours pour rapport = 7 jours au total',
        'profil': (
            'Consultants/formateurs recherchés :\n'
            'Consultant principal : Bac+4 en développement rural/économie, 10 ans expérience AGR\n'
            'Co-formateur : Praticien AGR reconnu en Côte d\'Ivoire\n'
            'Les deux consultants doivent justifier d\'expériences en formation communautaire'
        ),
        'criteres': (
            'Sélection sur dossier :\n'
            '  - CV et lettres de motivation\n'
            '  - Au moins 3 références de formations similaires\n'
            '  - Proposition pédagogique détaillée (5 pages max)\n'
            '  - Proposition financière'
        ),
        'modalites_paiement': '30% à la signature – 70% à la remise du rapport final',
    },
    # -- Étude -----------------------------------------------------------------
    {
        'titre': 'TDR – Étude de faisabilité plateformes d\'agrégation agricole',
        'type': 'etude',
        'statut': 'en_revision',
        'date_redaction_delta': -10,
        'budget': 12000000,
        'genere_ia': True,
        'contexte': (
            'Le PRCC prévoit la création de 5 plateformes d\'agrégation agricole dans les zones '
            'rurales de Bouaké et Korhogo pour faciliter la commercialisation des productions des '
            'coopératives. Une étude de faisabilité est nécessaire pour identifier les sites '
            'optimaux, évaluer la demande et concevoir le modèle économique.'
        ),
        'justification': (
            'Les coopératives agricoles membres du programme produisent des volumes croissants '
            'mais peinent à accéder aux marchés faute d\'infrastructures de stockage et de mise '
            'en marché. Les plateformes d\'agrégation constituent une solution structurante '
            'pour améliorer la compétitivité des filières.'
        ),
        'objectifs': (
            '1. Analyser les filières agricoles cibles et les flux de commercialisation\n'
            '2. Identifier et évaluer les sites potentiels pour les 5 plateformes\n'
            '3. Évaluer la demande et concevoir le modèle économique\n'
            '4. Analyser les besoins en infrastructure et estimer les coûts\n'
            '5. Proposer un plan d\'affaires pour chaque plateforme'
        ),
        'resultats': (
            '- Cartographie des filières agricoles et flux de commercialisation\n'
            '- Identification et évaluation de 10 sites candidats\n'
            '- Sélection et justification des 5 sites retenus\n'
            '- Modèles économiques détaillés pour chaque plateforme\n'
            '- Plans d\'affaires avec analyse financière sur 5 ans\n'
            '- Rapport de faisabilité complet avec recommandations'
        ),
        'methodologie': (
            'Phase 1 (2 semaines) : Revue documentaire et collecte données secondaires\n'
            'Phase 2 (3 semaines) : Enquêtes terrain dans les zones cibles\n'
            'Phase 3 (2 semaines) : Analyse et modélisation économique\n'
            'Phase 4 (1 semaine) : Restitution et rapport final\n\n'
            'Outils : Entretiens semi-directifs, focus groupes, observations terrain, '
            'analyses SIG, modèles financiers Excel.'
        ),
        'livrables': (
            '1. Rapport de démarrage avec plan de travail détaillé\n'
            '2. Rapport diagnostic filières et flux commerciaux\n'
            '3. Rapport d\'évaluation des sites candidats\n'
            '4. Plans d\'affaires des 5 plateformes retenues\n'
            '5. Rapport final de faisabilité'
        ),
        'calendrier': '8 semaines (juin – juillet 2026)',
        'profil': (
            'Équipe de consultants :\n'
            'Chef de mission : Expert filières agricoles et agro-économie, 12+ ans\n'
            'Spécialiste financier : Expert modélisation financière/plan d\'affaires\n'
            'Spécialiste SIG : Géographe pour analyse cartographique des sites\n'
            'Enquêteurs terrain : 4 enquêteurs bilingues (français/langues locales)'
        ),
        'criteres': (
            'Critères de sélection (méthode qualité + coût) :\n'
            '  Qualité technique (70%) : expérience équipe, méthodologie, références\n'
            '  Coût (30%) : rapport qualité/prix de l\'offre financière'
        ),
        'modalites_paiement': '25% démarrage – 35% rapport mi-parcours – 40% rapport final accepté',
    },
    # -- Évaluation ------------------------------------------------------------
    {
        'titre': 'TDR – Évaluation à mi-parcours du Programme PRCC',
        'type': 'evaluation',
        'statut': 'valide',
        'date_redaction_delta': -5,
        'budget': 35000000,
        'genere_ia': False,
        'contexte': (
            'Conformément aux dispositions de l\'accord de financement avec la Banque Mondiale, '
            'le Programme PRCC est soumis à une évaluation à mi-parcours après 18 mois d\'exécution. '
            'Cette évaluation externe et indépendante permettra d\'apprécier les progrès réalisés '
            'et de formuler des recommandations pour la phase 2 du programme.'
        ),
        'justification': (
            'L\'évaluation à mi-parcours est une exigence contractuelle et un outil de pilotage '
            'stratégique. Elle permettra de valider la pertinence de l\'approche, mesurer l\'efficacité '
            'des interventions, identifier les enseignements et orienter les ajustements nécessaires '
            'pour maximiser l\'impact en phase 2.'
        ),
        'objectifs': (
            '1. Apprécier la pertinence, l\'efficience et l\'efficacité des interventions\n'
            '2. Mesurer le niveau d\'atteinte des indicateurs du cadre de résultats\n'
            '3. Analyser la durabilité et l\'impact potentiel des changements observés\n'
            '4. Formuler des recommandations pour la phase 2 (2027-2028)\n'
            '5. Évaluer la conformité fiduciaire et les procédures de gestion'
        ),
        'resultats': (
            '- Note de démarrage avec méthodologie détaillée\n'
            '- Rapport préliminaire partagé avec toutes les parties prenantes\n'
            '- Rapport final d\'évaluation avec ratings par composante\n'
            '- Matrice de recommandations priorisées\n'
            '- Plan d\'amélioration pour la phase 2'
        ),
        'methodologie': (
            'Approche mixte quantitative et qualitative :\n'
            '  - Revue documentaire exhaustive (rapports, données S&E, audits)\n'
            '  - Visites terrain dans les 3 régions d\'intervention\n'
            '  - Entretiens avec équipe programme, partenaires, bailleurs\n'
            '  - Focus groupes avec bénéficiaires (250 personnes)\n'
            '  - Enquête quantitative auprès de 400 ménages\n'
            '  - Atelier de restitution et validation des conclusions'
        ),
        'livrables': (
            '1. Note de démarrage (J+5)\n'
            '2. Rapport de revue documentaire (J+10)\n'
            '3. Rapport de terrain – missions Abidjan, Bouaké, Korhogo (J+18)\n'
            '4. Rapport préliminaire pour commentaires (J+25)\n'
            '5. Rapport final d\'évaluation (J+35)\n'
            '6. Présentation des résultats en atelier (J+40)'
        ),
        'calendrier': '10 jours ouvrés de terrain + 30 jours d\'analyse et rapport = 6 semaines',
        'profil': (
            'Chef de mission évaluateur externe : PhD ou Bac+5, 15+ ans évaluation programmes développement\n'
            'Spécialiste thématique santé/nutrition : Médecin ou santé publique, 10+ ans\n'
            'Spécialiste thématique AGR/genre : Économiste rural, 10+ ans\n'
            'Expert S&E/données : Statisticien, maîtrise KoboToolbox et outils d\'analyse\n'
            'Tous indépendants du programme. Connaissance Afrique de l\'Ouest requise.'
        ),
        'criteres': (
            'Présélection sur dossier puis négociation avec shortlist :\n'
            '  Qualité technique (70%) : compétences équipe, méthodologie, expériences similaires\n'
            '  Offre financière (30%) : budget global et taux journaliers'
        ),
        'modalites_paiement': '20% signature – 30% rapport préliminaire – 50% rapport final accepté BM',
    },
    # -- Audit -----------------------------------------------------------------
    {
        'titre': 'TDR – Audit financier externe exercice 2025 et S1 2026',
        'type': 'audit',
        'statut': 'publie',
        'date_redaction_delta': -30,
        'budget': 18000000,
        'genere_ia': False,
        'contexte': (
            'Conformément aux dispositions fiduciaires de l\'accord de financement BM, le programme '
            'PRCC est soumis à un audit financier annuel conduit par un cabinet d\'audit indépendant '
            'agréé. Le présent TDR porte sur l\'audit de l\'exercice 2025 et du premier semestre 2026.'
        ),
        'justification': (
            'L\'audit indépendant garantit la transparence dans la gestion des ressources du programme '
            'et la conformité aux procédures financières BM. Ses conclusions permettent également '
            'd\'améliorer les systèmes de contrôle interne.'
        ),
        'objectifs': (
            '1. Exprimer une opinion sur les états financiers du programme pour 2025 et S1 2026\n'
            '2. Vérifier la conformité des dépenses aux règles BM et aux procédures nationales\n'
            '3. Évaluer l\'efficacité du système de contrôle interne\n'
            '4. Vérifier la régularité des procédures de passation des marchés\n'
            '5. Formuler des recommandations d\'amélioration'
        ),
        'resultats': (
            '- Opinion d\'audit sur les états financiers 2025 et S1 2026\n'
            '- Rapport sur le contrôle interne avec points faiblesses\n'
            '- Lettre de recommandations au management\n'
            '- Plan d\'amélioration du système fiduciaire'
        ),
        'methodologie': (
            'Méthode d\'audit conforme aux Normes Internationales d\'Audit (ISA) :\n'
            '  Phase 1 : Planification et évaluation des risques\n'
            '  Phase 2 : Tests sur les transactions (sondages statistiques)\n'
            '  Phase 3 : Vérification des procédures de passation de marchés\n'
            '  Phase 4 : Rapprochements bancaires et vérification des avances\n'
            '  Phase 5 : Rédaction et validation du rapport'
        ),
        'livrables': (
            '1. Rapport d\'audit des états financiers (avec opinion)\n'
            '2. Rapport sur le contrôle interne\n'
            '3. Lettre de recommandations (Management Letter)\n'
            '4. États financiers audités (format BM)'
        ),
        'calendrier': 'Démarrage juillet 2026 – Rapport final septembre 2026 (8 semaines)',
        'profil': (
            'Cabinet d\'audit agréé répondant aux critères suivants :\n'
            '  - Inscrit à l\'Ordre des Experts Comptables de Côte d\'Ivoire\n'
            '  - Accrédité par la Banque Mondiale (liste fiduciaire)\n'
            '  - Expérience vérifiable en audit de projets financés par les bailleurs\n'
            '  - Indépendant de l\'organisation gestionnaire\n'
            '  - Équipe dédiée : Associé responsable + 2 auditeurs seniors'
        ),
        'criteres': (
            'Sélection selon procédures BM – Sélection basée sur la qualité et le coût (SBQC) :\n'
            '  Qualification et expérience (50%) : accréditation, références, équipe\n'
            '  Proposition technique (20%) : approche, plan d\'audit, calendrier\n'
            '  Offre financière (30%) : honoraires globaux et taux journaliers'
        ),
        'modalites_paiement': '50% démarrage – 50% rapport final certifié',
    },
    # -- Mission ----------------------------------------------------------------
    {
        'titre': 'TDR – Mission de supervision et d\'appui technique – Districts sanitaires',
        'type': 'mission',
        'statut': 'valide',
        'date_redaction_delta': -15,
        'budget': 2500000,
        'genere_ia': False,
        'contexte': (
            'Dans le cadre du suivi des activités de santé communautaire, le programme organise '
            'des missions régulières de supervision et d\'appui technique dans les 5 districts '
            'sanitaires cibles. La présente mission couvre les districts d\'Adjamé, Yopougon et '
            'Cocody, avec focus sur la formation nutrition en cours.'
        ),
        'justification': (
            'La supervision rapprochée des agents de santé est essentielle pour assurer '
            'la qualité des activités de terrain, identifier les difficultés et apporter '
            'un appui technique ciblé. Elle contribue également à la collecte de données '
            'pour le rapport trimestriel Q2.'
        ),
        'objectifs': (
            '1. Superviser et appuyer les agents de santé dans les 3 districts\n'
            '2. Évaluer la qualité des formations dispensées et des pratiques\n'
            '3. Collecter les données de suivi des indicateurs de santé\n'
            '4. Identifier les difficultés et apporter des solutions immédiates\n'
            '5. Préparer des comptes rendus de supervision pour chaque district'
        ),
        'resultats': (
            '- 3 rapports de supervision districaux\n'
            '- Données de suivi collectées et saisies\n'
            '- Plan d\'actions correctives pour chaque district\n'
            '- Note de synthèse pour le rapport trimestriel'
        ),
        'methodologie': (
            'Visites de terrain sur 5 jours :\n'
            '  J1-J2 : District Adjamé – visites foyers, réunion équipe\n'
            '  J3    : District Yopougon – visites terrain\n'
            '  J4    : District Cocody – supervision agents\n'
            '  J5    : Consolidation données et rédaction note de synthèse'
        ),
        'livrables': (
            '- 3 fiches de supervision par district\n'
            '- Liste des problèmes identifiés et solutions apportées\n'
            '- Note de synthèse pour le rapport Q2\n'
            '- Données de suivi saisies dans KoboToolbox'
        ),
        'calendrier': '5 jours de mission (15-19 juin 2026)',
        'profil': (
            'Équipe de supervision interne :\n'
            '  Responsable de la mission : Responsable Volet Santé du programme\n'
            '  Chargé S&E : Responsable du système de suivi\n'
            '  Médecin conseil : Spécialiste nutrition de l\'équipe'
        ),
        'criteres': 'Mission interne – pas d\'appel d\'offres. Équipe désignée par le chef de projet.',
        'modalites_paiement': 'Per diem et frais selon barème programme',
    },
    # -- Recrutement -----------------------------------------------------------
    {
        'titre': 'TDR – Recrutement Responsable Suivi-Évaluation (poste permanent)',
        'type': 'recrutement',
        'statut': 'brouillon',
        'date_redaction_delta': 5,
        'budget': 0,
        'genere_ia': True,
        'contexte': (
            'Suite au départ du Responsable S&E en avril 2026, le programme PRCC recrute un '
            'titulaire permanent pour ce poste clé. Le poste est basé à Abidjan avec des '
            'déplacements fréquents dans les 3 régions d\'intervention.'
        ),
        'justification': (
            'Le Responsable S&E est essentiel pour assurer la qualité du système d\'information '
            'de gestion du programme, la rigueur des données et la production des rapports de '
            'performance exigés par le bailleur.'
        ),
        'objectifs': (
            'Recruter un Responsable S&E compétent et motivé pour assurer :\n'
            '  - La gestion et l\'animation du système S&E\n'
            '  - La collecte, vérification et analyse des données\n'
            '  - La production des rapports de performance\n'
            '  - Le renforcement des capacités S&E des partenaires'
        ),
        'resultats': (
            'Recrutement d\'un Responsable S&E qualifié sous 6 semaines après publication.'
        ),
        'methodologie': (
            'Processus de recrutement en 4 étapes :\n'
            '  1. Dépôt des candidatures (3 semaines)\n'
            '  2. Présélection sur dossier (1 semaine)\n'
            '  3. Tests écrits et entretiens (1 semaine)\n'
            '  4. Vérification des références et offre (1 semaine)'
        ),
        'livrables': 'Contrat de travail signé avec le candidat retenu',
        'calendrier': 'Prise de poste souhaitée : 1er août 2026',
        'profil': (
            'Diplôme : Bac+5 en statistiques, démographie, économie ou sciences sociales\n'
            'Expérience : 5+ ans en S&E de projets de développement\n'
            'Compétences : KoboToolbox, Power BI, Excel avancé, SPSS/Stata\n'
            'Qualités : Rigueur, autonomie, sens de la communication\n'
            'Langues : Français courant – Anglais opérationnel apprécié'
        ),
        'criteres': (
            'Présélection sur dossier selon grille critères :\n'
            '  Diplôme (20 pts) + Expérience globale (20 pts) + Expérience S&E (30 pts)\n'
            '  + Compétences techniques (20 pts) + Références (10 pts)'
        ),
        'modalites_paiement': 'Salaire selon grille de rémunération du programme',
    },
]


class Command(BaseCommand):
    help = 'Seed M10 — TDR (tous types, tous statuts, sections structurées complètes)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les TDR existants avant re-seed')

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
            programme = projet.programme

            count = self._seed_tdrs(admin, projet, programme)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Seed TDR terminé ! {count} TDR créés.'))

    def _reset(self):
        from planification.models import TDR
        self.stdout.write(self.style.WARNING('[RESET] Suppression TDR…'))
        TDR.objects.all().delete()
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

    def _seed_tdrs(self, admin, projet, programme):
        from planification.models import TDR
        self.stdout.write('\n>> TDR (M10)…')
        today = date.today()
        count = 0

        for data in TDRS:
            date_red = today + timedelta(days=data['date_redaction_delta'])

            tdr, created = TDR.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'type_tdr':             data['type'],
                    'statut':               data['statut'],
                    'projet':               projet,
                    'programme':            programme,
                    'contexte':             data.get('contexte', ''),
                    'justification':        data.get('justification', ''),
                    'objectifs':            data.get('objectifs', ''),
                    'resultats_attendus':   data.get('resultats', ''),
                    'methodologie':         data.get('methodologie', ''),
                    'livrables':            data.get('livrables', ''),
                    'calendrier':           data.get('calendrier', ''),
                    'budget_previsionnel':  data.get('budget', 0),
                    'profil_consultant':    data.get('profil', ''),
                    'criteres_selection':   data.get('criteres', ''),
                    'modalites_paiement':   data.get('modalites_paiement', ''),
                    'redige_par':           admin,
                    'date_redaction':       date_red,
                    'valide_par':           admin if data['statut'] in ('valide', 'publie') else None,
                    'date_validation':      timezone.now() if data['statut'] in ('valide', 'publie') else None,
                    'publie_par':           admin if data['statut'] == 'publie' else None,
                    'date_publication':     timezone.now() if data['statut'] == 'publie' else None,
                    'genere_par_ia':        data.get('genere_ia', False),
                    'prompt_ia':            'Génération automatique IA – revue et validée par l\'équipe' if data.get('genere_ia') else '',
                }
            )
            self._log(f'TDR [{data["type"]}][{data["statut"]}]', tdr, created)
            count += 1 if created else 0

        return count
