"""
Seed M20 — Cadre de résultats, Théorie du changement, Leçons apprises.

Crée un cadre de résultats hiérarchique complet (Impact->Effet->Résultat->Produit->Activité)
avec théorie du changement détaillée et 5 leçons apprises capitalisées.

Usage : python manage.py seed_cadre [--reset]
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# -- Niveaux du cadre (ordre d'insertion = ordre hiérarchique) ----------------

NIVEAUX = [
    # IMPACT (racine)
    {
        'code': 'IMP-01',
        'niveau': 'impact',
        'intitule': 'Réduction durable de la pauvreté et amélioration du bien-être des communautés des 45 villages d\'intervention du programme PRCC',
        'taux': 28,
        'parent': None,
        'ordre': 1,
    },

    # EFFETS (niveau 2)
    {
        'code': 'EFF-01',
        'niveau': 'effet',
        'intitule': 'Amélioration de l\'état nutritionnel et sanitaire des populations ciblées (0-59 mois et femmes en âge de procréer)',
        'taux': 45,
        'parent': 'IMP-01',
        'ordre': 1,
    },
    {
        'code': 'EFF-02',
        'niveau': 'effet',
        'intitule': 'Augmentation durable et significative des revenus des ménages ruraux bénéficiaires',
        'taux': 22,
        'parent': 'IMP-01',
        'ordre': 2,
    },
    {
        'code': 'EFF-03',
        'niveau': 'effet',
        'intitule': 'Amélioration de l\'accès à une éducation de qualité et réduction du taux d\'analphabétisme',
        'taux': 35,
        'parent': 'IMP-01',
        'ordre': 3,
    },
    {
        'code': 'EFF-04',
        'niveau': 'effet',
        'intitule': 'Renforcement de la gouvernance locale et de la participation citoyenne dans 45 communes',
        'taux': 18,
        'parent': 'IMP-01',
        'ordre': 4,
    },

    # RÉSULTATS Santé (niveau 3 — sous EFF-01)
    {
        'code': 'RES-01',
        'niveau': 'resultat',
        'intitule': '500 agents de santé communautaires certifiés et opérationnels dans les 5 districts sanitaires',
        'taux': 42,
        'parent': 'EFF-01',
        'ordre': 1,
    },
    {
        'code': 'RES-02',
        'niveau': 'resultat',
        'intitule': '8 centres de santé construits, réhabilités et équipés avec du matériel médical conforme',
        'taux': 50,
        'parent': 'EFF-01',
        'ordre': 2,
    },
    {
        'code': 'RES-03',
        'niveau': 'resultat',
        'intitule': 'Taux de couverture DTP3 porté de 52% à 90% dans les districts d\'Abobo, Adjamé et Yopougon',
        'taux': 68,
        'parent': 'EFF-01',
        'ordre': 3,
    },
    {
        'code': 'RES-04',
        'niveau': 'resultat',
        'intitule': 'Prévalence de la malnutrition aiguë réduite de 14.2% à moins de 8% chez les enfants < 5 ans',
        'taux': 35,
        'parent': 'EFF-01',
        'ordre': 4,
    },

    # RÉSULTATS AGR (niveau 3 — sous EFF-02)
    {
        'code': 'RES-05',
        'niveau': 'resultat',
        'intitule': '25 coopératives agricoles agréées, structurées et pleinement opérationnelles dans les zones Nord',
        'taux': 32,
        'parent': 'EFF-02',
        'ordre': 1,
    },
    {
        'code': 'RES-06',
        'niveau': 'resultat',
        'intitule': '1 500 femmes rurales formées en entrepreneuriat, gestion financière et techniques AGR',
        'taux': 20,
        'parent': 'EFF-02',
        'ordre': 2,
    },
    {
        'code': 'RES-07',
        'niveau': 'resultat',
        'intitule': '150 micro-crédits accordés et remboursés via le fonds de garantie du programme',
        'taux': 15,
        'parent': 'EFF-02',
        'ordre': 3,
    },

    # RÉSULTATS Éducation (niveau 3 — sous EFF-03)
    {
        'code': 'RES-08',
        'niveau': 'resultat',
        'intitule': '5 000 enfants déscolarisés ou jamais scolarisés intégrés dans des structures d\'accueil',
        'taux': 40,
        'parent': 'EFF-03',
        'ordre': 1,
    },
    {
        'code': 'RES-09',
        'niveau': 'resultat',
        'intitule': '500 femmes adultes (18-45 ans) alphabétisées et certifiées en lecture-écriture-calcul',
        'taux': 25,
        'parent': 'EFF-03',
        'ordre': 2,
    },

    # RÉSULTATS Gouvernance (niveau 3 — sous EFF-04)
    {
        'code': 'RES-10',
        'niveau': 'resultat',
        'intitule': '180 élus locaux formés en gouvernance participative et planification locale',
        'taux': 35,
        'parent': 'EFF-04',
        'ordre': 1,
    },
    {
        'code': 'RES-11',
        'niveau': 'resultat',
        'intitule': '15 Plans de Développement Locaux (PDL) élaborés de façon participative et adoptés',
        'taux': 10,
        'parent': 'EFF-04',
        'ordre': 2,
    },

    # PRODUITS Santé (niveau 4 — sous RES-01)
    {
        'code': 'PRO-01',
        'niveau': 'produit',
        'intitule': 'Curriculum de formation ASC validé et 3 sessions de formation organisées (85 agents/session)',
        'taux': 65,
        'parent': 'RES-01',
        'ordre': 1,
    },
    {
        'code': 'PRO-02',
        'niveau': 'produit',
        'intitule': 'Système de suivi numérique (KoboToolbox) déployé dans les 5 districts et 25 enquêteurs formés',
        'taux': 100,
        'parent': 'RES-01',
        'ordre': 2,
    },
    {
        'code': 'PRO-03',
        'niveau': 'produit',
        'intitule': 'Équipements médicaux de base acquis et distribués dans les 8 centres de santé',
        'taux': 40,
        'parent': 'RES-02',
        'ordre': 1,
    },

    # ACTIVITÉS (niveau 5 — exemples sous PRO-01)
    {
        'code': 'ACT-01',
        'niveau': 'activite',
        'intitule': 'Formation session 1 : 85 agents District Abobo (Module Nutrition + ANJE + KoboCollect)',
        'taux': 100,
        'parent': 'PRO-01',
        'ordre': 1,
    },
    {
        'code': 'ACT-02',
        'niveau': 'activite',
        'intitule': 'Formation session 2 : 38 agents Districts Adjamé & Yopougon (+ session rattrapage)',
        'taux': 15,
        'parent': 'PRO-01',
        'ordre': 2,
    },
    {
        'code': 'ACT-03',
        'niveau': 'activite',
        'intitule': 'Appel d\'offres, sélection entreprise et suivi travaux construction 8 centres de santé',
        'taux': 50,
        'parent': 'PRO-03',
        'ordre': 1,
    },
]

# -- Théorie du changement -----------------------------------------------------

THEORIE_CHANGEMENT = {
    'titre': 'Théorie du changement — Programme PRCC 2024-2028',
    'version': '2.0',
    'contexte': (
        'Les communautés rurales de Côte d\'Ivoire font face à des défis multidimensionnels qui se renforcent '
        'mutuellement : un taux de pauvreté de 45% dans les zones ciblées, une couverture sanitaire insuffisante '
        '(52% DTP3), un taux d\'analphabétisme féminin de 65%, et une faible organisation des filières agricoles. '
        'Ces défis sont aggravés par les effets du changement climatique et les inégalités de genre.\n\n'
        'Le PRCC intervient dans ce contexte complexe avec une approche intégrée, combinant renforcement des '
        'capacités individuelles, développement économique communautaire et amélioration de la gouvernance locale. '
        'L\'intervention cible 45 villages dans les régions d\'Abidjan, Bouaké et Korhogo, touchant directement '
        '150 000 bénéficiaires sur une période de 5 ans (2024-2028).'
    ),
    'probleme_central': (
        'Vulnérabilité chronique et multidimensionnelle des communautés rurales ciblées, caractérisée par :\n'
        '• Insécurité alimentaire et malnutrition infantile élevée (14.2% de malnutrition aiguë)\n'
        '• Accès limité aux services de santé de base (un centre de santé pour 8 000 habitants)\n'
        '• Faible niveau d\'instruction, notamment chez les femmes (65% d\'analphabétisme)\n'
        '• Revenus agricoles précaires et absence de diversification économique\n'
        '• Gouvernance locale faible et faible participation des communautés aux décisions'
    ),
    'vision_changement': (
        'D\'ici 2028, les 150 000 bénéficiaires du programme PRCC vivent dans des communautés résilientes, '
        'où chaque enfant a accès à des soins de qualité, où les femmes contribuent activement à l\'économie '
        'locale, où les jeunes ont accès à une éducation de qualité, et où les communautés participent '
        'pleinement aux décisions qui les concernent.\n\n'
        'La malnutrition infantile sera réduite à moins de 8%, les revenus des ménages ruraux auront augmenté '
        'de 40% en moyenne, et le taux d\'alphabétisation des femmes adultes aura progressé de 35% à 60%.'
    ),
    'hypotheses_changement': (
        'H1 — Santé : Si les agents de santé communautaires sont formés, supervisés et équipés, ils améliorent '
        'significativement les pratiques nutritionnelles et sanitaires des ménages qui leur font confiance.\n\n'
        'H2 — AGR : Si les femmes ont accès à des formations en entrepreneuriat et à des micro-crédits adaptés, '
        'elles développent des activités génératrices de revenus viables qui améliorent les conditions de vie '
        'de l\'ensemble du ménage (effet multiplicateur genre).\n\n'
        'H3 — Coopératives : Si les coopératives agricoles sont structurées et accompagnées professionnellement, '
        'elles accèdent aux marchés régionaux et augmentent durablement les revenus de leurs membres.\n\n'
        'H4 — Éducation : Si les femmes adultes sont alphabétisées et si des structures d\'accueil sont créées '
        'pour les enfants déscolarisés, le capital humain des communautés s\'améliore sur le long terme.\n\n'
        'H5 — Gouvernance : Si les élus locaux et les communautés sont impliqués dans la planification, '
        'les services publics s\'améliorent et les réalisations du programme sont appropriées et durables.'
    ),
    'facteurs_risque': (
        'R1 — Instabilité politico-sécuritaire : Risque de perturbations dans certaines zones d\'intervention '
        'affectant les activités terrain et la mobilisation des équipes.\n\n'
        'R2 — Chocs climatiques : Sécheresses ou inondations pouvant compromettre les récoltes des coopératives '
        'et retarder les travaux de construction.\n\n'
        'R3 — Résistances culturelles : Certaines pratiques ancestrales (pesage des enfants perçu comme mauvais '
        'présage, refus de vaccination) peuvent freiner l\'atteinte des indicateurs de santé.\n\n'
        'R4 — Turnover du personnel : Départ d\'agents de santé formés vers d\'autres structures sans mécanisme '
        'de remplacement rapide, réduisant l\'impact des investissements formation.\n\n'
        'R5 — Délais administratifs : Procédures d\'agrément des coopératives et permis de construire plus '
        'longs que prévu, retardant le démarrage de composantes entières.'
    ),
}

# -- Leçons apprises ------------------------------------------------------------

LECONS = [
    {
        'type_lecon': 'bonne_pratique',
        'titre': 'Formation en cascade avec agents multiplicateurs locaux',
        'domaine': 'Formation & Renforcement de capacités',
        'contexte': (
            'Composante santé — formation de 500 agents de santé communautaires (ASC). '
            'Face au défi de former un grand nombre d\'agents dans des zones dispersées avec un budget limité, '
            'l\'équipe a adopté une stratégie de formation en cascade.'
        ),
        'description': (
            'La stratégie consiste à former en priorité 20 "formateurs-multiplicateurs" locaux issus des communautés, '
            'qui à leur tour forment les agents dans leurs zones d\'intervention. Cette approche a permis de :\n'
            '• Réduire le coût par agent formé de 35% par rapport à une formation centralisée\n'
            '• Améliorer le taux de rétention des compétences grâce au suivi par des formateurs proches\n'
            '• Créer des champions locaux de la santé communautaire reconnus et respectés\n'
            '• Former 210 agents en 3 mois au lieu des 6 mois initialement prévus'
        ),
        'recommandation': (
            'Systématiser cette approche dans toutes les composantes de formation du programme et dans les '
            'futurs projets. Prévoir un budget spécifique pour la formation, le suivi et la revalorisation '
            'des formateurs-multiplicateurs. Documenter les profils des multiplicateurs les plus efficaces '
            'pour informer le ciblage dans d\'autres zones.'
        ),
    },
    {
        'type_lecon': 'difficulte',
        'titre': 'Délais d\'agrément des coopératives agricoles : sous-estimation critique',
        'domaine': 'AGR & Développement économique',
        'contexte': (
            'Composante AGR — structuration de 25 coopératives dans la zone Nord. '
            'La planification initiale prévoyait un délai d\'agrément officiel de 4 semaines après dépôt du dossier '
            'au Ministère de l\'Agriculture et du Développement Rural (MINADER).'
        ),
        'description': (
            'Les délais réels d\'agrément ont été 3 à 6 fois supérieurs aux estimations (3-6 mois au lieu d\'1 mois), '
            'pour des raisons multiples :\n'
            '• Dossiers incomplets liés à l\'analphabétisme des responsables des coopératives\n'
            '• Personnel MINADER insuffisant dans les antennes régionales\n'
            '• Procédures administratives complexes non documentées\n'
            '• Absence de relation préalable avec l\'administration locale\n\n'
            'Conséquence : la composante AGR a pris 5 mois de retard, affectant les indicateurs S1 2026 '
            'et créant une sous-exécution budgétaire de 8 points.'
        ),
        'recommandation': (
            '1. Intégrer les délais administratifs réels (6 mois minimum) dans la planification initiale\n'
            '2. Établir un protocole de partenariat avec le MINADER dès la phase de conception\n'
            '3. Recruter un facilitateur administratif local dédié aux démarches d\'agrément\n'
            '4. Pré-remplir les dossiers avec les futures coopératives 3 mois avant le dépôt officiel\n'
            '5. Prévoir un mécanisme de flexibilité budgétaire pour absorber les retards'
        ),
    },
    {
        'type_lecon': 'innovation',
        'titre': 'Collecte de données hors-ligne avec KoboToolbox en zones sans connectivité',
        'domaine': 'Suivi-Évaluation & Données',
        'contexte': (
            'Déploiement du système S&E numérique dans 45 villages dont 18 sont des zones blanches '
            '(sans réseau mobile). La collecte papier classique générait des erreurs de saisie, des pertes '
            'de données et des délais de consolidation de 3-4 semaines.'
        ),
        'description': (
            'L\'adoption de KoboCollect en mode hors-ligne a transformé la collecte terrain :\n'
            '• Configuration des formulaires pour fonctionner sans connectivité (mode offline complet)\n'
            '• Synchronisation automatique lors du retour en zone couverte\n'
            '• Contrôles de qualité intégrés (valeurs min/max, questions obligatoires, skip logic)\n'
            '• Géolocalisation GPS automatique des points de collecte\n\n'
            'Résultats mesurés :\n'
            '• Réduction des erreurs de saisie de 67% (vs collecte papier)\n'
            '• Délai de consolidation réduit de 3-4 semaines à 3-4 jours\n'
            '• 100% des 6 000 fiches bénéficiaires collectées numériquement\n'
            '• Économie estimée de 40 heures/mois de saisie manuelle'
        ),
        'recommandation': (
            'Étendre cette approche à tous les programmes de l\'organisation. Former une équipe interne '
            'de "super-utilisateurs KoboToolbox" capables de configurer et maintenir les formulaires. '
            'Documenter le processus de configuration pour faciliter la réplication. '
            'Intégrer une formation KoboCollect dans le parcours d\'induction de tous les nouveaux enquêteurs.'
        ),
    },
    {
        'type_lecon': 'recommandation',
        'titre': 'Implication des autorités locales dès la conception : condition de succès',
        'domaine': 'Gouvernance & Partenariats',
        'contexte': (
            'Comparaison entre deux sous-zones d\'intervention : dans la sous-zone A, les maires et chefs '
            'de village ont été impliqués dès l\'atelier de démarrage. Dans la sous-zone B, ils ont été '
            'informés 3 mois après le début des activités.'
        ),
        'description': (
            'L\'analyse comparative révèle des écarts significatifs :\n\n'
            'Sous-zone A (co-conception) :\n'
            '• Taux de participation aux activités : 87%\n'
            '• Conflits fonciers (pour la construction) : 0\n'
            '• Délai de démarrage des travaux : 3 semaines\n'
            '• Appropriation communautaire : très forte\n\n'
            'Sous-zone B (information tardive) :\n'
            '• Taux de participation : 54%\n'
            '• Conflits fonciers : 3 cas nécessitant une médiation\n'
            '• Délai de démarrage des travaux : 11 semaines\n'
            '• Appropriation communautaire : faible\n\n'
            'Conclusion : l\'implication précoce des autorités locales est un facteur déterminant '
            'pour l\'efficacité et la durabilité des interventions.'
        ),
        'recommandation': (
            '1. Organiser systématiquement des ateliers de co-conception avec les autorités locales '
            'AVANT le démarrage de chaque composante\n'
            '2. Signer des protocoles de partenariat formels avec les mairies et conseils régionaux\n'
            '3. Intégrer les chefs de village comme "points focaux communautaires" rémunérés\n'
            '4. Inclure une clause d\'approbation communautaire dans tous les plans de travail trimestriels'
        ),
    },
    {
        'type_lecon': 'lecon',
        'titre': 'Fréquence de supervision des agents terrain et qualité des données',
        'domaine': 'Supervision & Qualité des données',
        'contexte': (
            'Analyse comparative des performances des agents de santé communautaires selon '
            'la fréquence de supervision reçue : mensuelle (groupe A, 45 agents) vs trimestrielle '
            '(groupe B, 42 agents). Étude conduite sur 6 mois, districts Abobo et Adjamé.'
        ),
        'description': (
            'Les données comparatives montrent des écarts significatifs et durables :\n\n'
            'Groupe A (supervision mensuelle) :\n'
            '• Taux de visite domiciliaire : 94% de la cible\n'
            '• Qualité des données collectées (score) : 88/100\n'
            '• Détection précoce malnutrition : 3.2 cas/agent/mois\n'
            '• Satisfaction des ménages : 91%\n\n'
            'Groupe B (supervision trimestrielle) :\n'
            '• Taux de visite : 62% de la cible\n'
            '• Qualité données : 64/100\n'
            '• Détection malnutrition : 1.8 cas/agent/mois\n'
            '• Satisfaction : 73%\n\n'
            'Surcoût de la supervision mensuelle estimé à 2.8M FCFA/an, largement compensé '
            'par l\'amélioration de la performance et l\'atteinte des indicateurs.'
        ),
        'recommandation': (
            'Budgétiser obligatoirement la supervision mensuelle des agents terrain dans tous les projets '
            'similaires. Le ROI de la supervision rapprochée est démontré. '
            'Développer des outils de supervision légers (checklist KoboCollect) pour réduire le temps '
            'consacré à chaque supervision et permettre de couvrir plus d\'agents par superviseur.'
        ),
    },
]


class Command(BaseCommand):
    help = 'Seed M20 — Cadre de résultats complet + Théorie du changement + Leçons apprises'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les données cadre existantes')

    def handle(self, *args, **options):
        admin = self._get_admin()
        if not admin:
            self.stdout.write(self.style.ERROR('[ERREUR] Aucun admin. Lancez seed_lot1 d\'abord.'))
            return
        projet = self._get_projet()
        if not projet:
            self.stdout.write(self.style.ERROR('[ERREUR] Aucun projet actif. Lancez seed_projets d\'abord.'))
            return

        self.stdout.write(f'[INFO] Projet cible : {projet.code} — {projet.titre or projet.code}')

        # Reset ET création dans le même transaction.atomic pour que le reset
        # soit annulé si la création échoue
        try:
            with transaction.atomic():
                if options['reset']:
                    self._reset()
                self._seed_cadre(admin, projet)
                self._seed_theorie(admin, projet)
                self._seed_lecons(admin, projet)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'[ERREUR] Transaction annulée : {exc}'))
            import traceback; traceback.print_exc()
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Seed cadre résultats terminé pour {projet.code} !'))

    def _reset(self):
        from suivi_evaluation.models import CadreResultats, NiveauResultat, TheorieChangement, LeconApprise
        self.stdout.write(self.style.WARNING('[RESET] Suppression cadre résultats…'))
        n1 = NiveauResultat.objects.all().delete()
        n2 = CadreResultats.objects.all().delete()
        n3 = TheorieChangement.objects.all().delete()
        n4 = LeconApprise.objects.all().delete()
        self.stdout.write(f'   Niveaux supprimés : {n1[0]} | Cadres : {n2[0]} | TC : {n3[0]} | Leçons : {n4[0]}')

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_projet(self):
        from programmes_projets.models import Projet
        return Projet.objects.filter(statut='en_cours').first()

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Créé') if created else self.style.WARNING('Existe')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:80]}')

    def _seed_cadre(self, admin, projet):
        from suivi_evaluation.models import CadreResultats, NiveauResultat

        # Vérifier si un cadre existe déjà
        cadre_existant = CadreResultats.objects.filter(projet=projet).first()
        if cadre_existant:
            self.stdout.write(self.style.WARNING(f'  [Existe] Cadre déjà présent (id={cadre_existant.id}) — on l\'utilise'))
            cadre = cadre_existant
        else:
            cadre = CadreResultats.objects.create(
                projet=projet,
                titre=f'Cadre de résultats — {projet.code} (PRCC 2024-2028)',
                description=(
                    'Cadre hiérarchique des résultats du Programme de Renforcement des Capacités '
                    'Communautaires (PRCC). Structuré en 5 niveaux : Impact, Effets, Résultats, '
                    'Produits et Activités. Validé par le comité de pilotage en janvier 2024.'
                ),
                version='2.0',
                created_by=admin,
                valide_par=admin,
                date_validation=date.today(),
            )
            self.stdout.write(self.style.SUCCESS(f'  [Créé] Cadre de résultats id={cadre.id}'))

        self.stdout.write('\n   >> Niveaux de résultats…')
        code_to_obj = {}

        # Pré-charger les niveaux existants pour ce cadre (évite les doublons)
        existants = {n.code: n for n in NiveauResultat.objects.filter(cadre=cadre)}
        nb_crees = 0

        for n in NIVEAUX:
            if n['code'] in existants:
                code_to_obj[n['code']] = existants[n['code']]
                indent = '  ' * ['impact','effet','resultat','produit','activite','intrant'].index(n['niveau'])
                self.stdout.write(self.style.WARNING(f'    {indent}~ [EXISTE] {n["code"]}'))
                continue
            parent = code_to_obj.get(n['parent']) if n['parent'] else None
            niveau = NiveauResultat.objects.create(
                cadre=cadre,
                parent=parent,
                niveau=n['niveau'],
                code=n['code'],
                intitule=n['intitule'],
                taux_avancement=n['taux'],
                ordre=n['ordre'],
            )
            code_to_obj[n['code']] = niveau
            indent = '  ' * ['impact','effet','resultat','produit','activite','intrant'].index(n['niveau'])
            self.stdout.write(f'    {indent}+ [{n["niveau"].upper()[:3]}] {n["code"]} — {n["intitule"][:55]}…')
            nb_crees += 1

        self.stdout.write(f'   {nb_crees} niveaux créés ({len(existants)} déjà existants).')
        return cadre

    def _seed_theorie(self, admin, projet):
        from suivi_evaluation.models import TheorieChangement

        self.stdout.write('\n   >> Théorie du changement…')
        data = THEORIE_CHANGEMENT

        if TheorieChangement.objects.filter(projet=projet).exists():
            self.stdout.write(self.style.WARNING('  [Existe] Théorie du changement déjà présente — ignorée'))
            return

        tc = TheorieChangement.objects.create(
            projet=projet,
            titre=data['titre'],
            version=data['version'],
            contexte=data['contexte'],
            probleme_central=data['probleme_central'],
            vision_changement=data['vision_changement'],
            hypotheses_changement=data['hypotheses_changement'],
            facteurs_risque=data['facteurs_risque'],
            created_by=admin,
        )
        self.stdout.write(self.style.SUCCESS(f'  [Créé] Théorie du changement id={tc.id}'))

    def _seed_lecons(self, admin, projet):
        from suivi_evaluation.models import LeconApprise

        self.stdout.write('\n   >> Leçons apprises…')
        nb = 0
        for data in LECONS:
            if LeconApprise.objects.filter(titre=data['titre']).exists():
                self.stdout.write(self.style.WARNING(f'  [Existe] {data["titre"][:50]}'))
                continue
            lecon = LeconApprise.objects.create(
                type_lecon=data['type_lecon'],
                domaine=data['domaine'],
                contexte=data['contexte'],
                description=data['description'],
                recommandation=data['recommandation'],
                titre=data['titre'],
                projet=projet,
                auteur=admin,
                statut='valide',
                valide_par=admin,
            )
            self.stdout.write(self.style.SUCCESS(f'  [Créé] Leçon [{data["type_lecon"]}]: {data["titre"][:55]}'))
            nb += 1
        self.stdout.write(f'   {nb} leçons créées.')
