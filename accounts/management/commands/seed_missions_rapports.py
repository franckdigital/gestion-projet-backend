"""
Seed missions enrichies (avec membres et rapports de mission)
et rapports d'avancement multi-contextes (projet, tache, reunion, mission).

Usage : python manage.py seed_missions_rapports [--reset]
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


MISSIONS_DATA = [
    {
        'objet': 'Mission terrain de suivi – Projet Sante Communautaire Abidjan-Nord',
        'type_mission': 'supervision',
        'description': 'Mission de supervision et d\'appui technique aux equipes du projet sante dans les districts d\'Abidjan-Nord. Evaluation de l\'avancement physique, resolution des blocages et validation des donnees de suivi.',
        'lieu_depart': 'Siege social – Abidjan Plateau',
        'destination': 'Abidjan-Nord – Districts sanitaires',
        'pays_destination': 'Cote d\'Ivoire',
        'objectifs': '1. Evaluer l\'avancement physique du projet (cible 65%)\n2. Valider les donnees du systeme de suivi numerise\n3. Identifier et resoudre les blocages operationnels\n4. Appuyer les equipes dans la preparation du rapport trimestriel',
        'resultats_attendus': 'Rapport de supervision valide\nPlan d\'actions correctives\nDonnees de suivi validees et actualisees\nPhoto-reportage des activites terrain',
        'date_debut_delta': -15, 'date_fin_delta': -12,
        'budget_prevu': 450000, 'budget_realise': 412000,
        'statut': 'terminee',
        'membres': [
            {'role': 'chef_mission', 'ij': 25000, 'transport': 15000, 'hebergement': 0},
            {'role': 'membre', 'ij': 15000, 'transport': 15000, 'hebergement': 0},
        ],
        'rapport': {
            'resume': 'La mission de supervision a permis de constater un avancement physique global de 68%, superieur a la cible initiale de 65%. Les 85 agents de sante formes montrent une bonne appropriation des outils. Le systeme de suivi numerise est pleinement operationnel dans 4 districts sur 5.',
            'objectifs_atteints': 'Avancement physique de 68% valide (cible 65%) - DEPASSE\nSysteme de suivi valide dans 4/5 districts - PARTIELLEMENT ATTEINT\nPlan d\'actions correctives elabore pour le district manquant - ATTEINT\n3 blocages majeurs identifies et resolus - ATTEINT',
            'observations': 'Fort engagement des equipes terrain malgre les conditions difficiles. Le district de Cocody presente un retard de 3 semaines lie au turnover du coordinateur. Les agents de sante sont particulierement motives et apportent une valeur ajoutee significative dans leurs communautes.',
            'recommandations': '1. Accelerer le recrutement du coordinateur du district de Cocody\n2. Renforcer la formation des agents sur le module nutrition\n3. Prevoir une mission de suivi supplementaire en juillet pour le district en retard\n4. Documenter les bonnes pratiques observees pour les partager avec les autres projets',
            'suite_a_donner': 'Mission de suivi complementaire prevue en juillet 2026 pour le district de Cocody\nFormation nutrition additionnelle planifiee pour 20 agents\nRapport de supervision transmis au bailleur',
            'statut': 'valide',
            'date_soumission': -13,
        },
    },
    {
        'objet': 'Mission de negociation – Protocole partenariat Conseil Regional Gbeke',
        'type_mission': 'partenariat',
        'description': 'Mission de negociation et de finalisation du protocole de partenariat avec le Conseil Regional du Gbeke pour la mise en oeuvre conjointe des activites du programme PRCC dans la region de Bouake.',
        'lieu_depart': 'Abidjan',
        'destination': 'Bouake – Siege Conseil Regional du Gbeke',
        'pays_destination': 'Cote d\'Ivoire',
        'objectifs': '1. Presenter le programme PRCC aux autorites regionales\n2. Negocier les modalites de partenariat\n3. Finaliser et signer le protocole d\'accord\n4. Elaborer le plan d\'action conjoint pour 2026-2027',
        'resultats_attendus': 'Protocole d\'accord signe\nPlan d\'action conjoint 2026-2027\nEngagement confirme des autorites locales',
        'date_debut_delta': -8, 'date_fin_delta': -7,
        'budget_prevu': 180000, 'budget_realise': 165000,
        'statut': 'terminee',
        'membres': [
            {'role': 'chef_mission', 'ij': 20000, 'transport': 30000, 'hebergement': 20000},
            {'role': 'membre', 'ij': 15000, 'transport': 30000, 'hebergement': 20000},
        ],
        'rapport': {
            'resume': 'La mission de negociation s\'est conclue par la signature du protocole d\'accord entre le programme PRCC et le Conseil Regional du Gbeke. Ce partenariat ouvre l\'acces a 12 nouveaux villages et permettra une co-implementation de 8 activites.',
            'objectifs_atteints': 'Presentation du programme effectuee - ATTEINT\nNegociation des modalites conclue avec succes - ATTEINT\nProtocole signe le 23 mai 2026 - ATTEINT\nPlan d\'action conjoint elabore en seance - ATTEINT',
            'observations': 'Les autorites regionales ont manifeste un fort interet pour le programme et souhaitent elargir le partenariat a d\'autres composantes. Le President du Conseil a personnellement signe le protocole en presence du Prefet de region.',
            'recommandations': '1. Organiser rapidement la reunion de demarrage du partenariat\n2. Etudier la possibilite d\'integrer les activites de gouvernance locale au partenariat\n3. Former les agents du Conseil aux outils de suivi du programme',
            'suite_a_donner': 'Reunion de demarrage partenariat prevue le 15 juin 2026\nTransmission du protocole signe a tous les partenaires',
            'statut': 'valide',
            'date_soumission': -6,
        },
    },
    {
        'objet': 'Mission de formation multiplicateurs – Techniques AGR Femmes Rurales Korhogo',
        'type_mission': 'formation',
        'description': 'Mission de formation des agents multiplicateurs locaux en techniques de gestion des activites generatrices de revenus pour les femmes rurales de la region des Savanes. Formation-action de 3 jours avec travaux pratiques.',
        'lieu_depart': 'Abidjan',
        'destination': 'Korhogo – Centre de Formation Professionnelle',
        'pays_destination': 'Cote d\'Ivoire',
        'objectifs': '1. Former 20 agents multiplicateurs aux techniques AGR\n2. Tester les outils pedagogiques developpes\n3. Certifier les agents formes\n4. Elaborer le plan de deploiement communautaire',
        'resultats_attendus': '20 agents multiplicateurs certifies\nOutils pedagogiques testes et valides\nPlan de deploiement communautaire\nRapport de formation',
        'date_debut_delta': 5, 'date_fin_delta': 7,
        'budget_prevu': 620000, 'budget_realise': 0,
        'statut': 'approuvee',
        'membres': [
            {'role': 'chef_mission', 'ij': 20000, 'transport': 45000, 'hebergement': 30000},
            {'role': 'consultant', 'ij': 50000, 'transport': 45000, 'hebergement': 30000},
            {'role': 'membre', 'ij': 15000, 'transport': 45000, 'hebergement': 30000},
        ],
        'rapport': None,
    },
    {
        'objet': 'Mission de supervision Banque Mondiale – Revue a mi-parcours PRCC',
        'type_mission': 'evaluation',
        'description': 'Mission conjointe de revue a mi-parcours avec la Banque Mondiale pour evaluer les performances du programme PRCC apres 18 mois d\'execution. Mission de 10 jours couvrant Abidjan, Bouake et Korhogo.',
        'lieu_depart': 'Abidjan (accueil de la delegation BM)',
        'destination': 'Abidjan, Bouake, Korhogo – Sites du programme',
        'pays_destination': 'Cote d\'Ivoire',
        'objectifs': '1. Evaluer les performances globales par rapport aux cibles du cadre logique\n2. Verifier la conformite fiduciaire des depenses\n3. Valider les ajustements proposes pour la phase 2\n4. Conduire des visites terrain dans les 3 regions\n5. Rencontrer les beneficiaires et partenaires locaux',
        'resultats_attendus': 'Rapport de supervision BM\nRecommandations formelles de la BM\nAjustements de la phase 2 valides\nRating du programme maintenu ou ameliore',
        'date_debut_delta': 10, 'date_fin_delta': 20,
        'budget_prevu': 1500000, 'budget_realise': 0,
        'statut': 'planifiee',
        'membres': [
            {'role': 'chef_mission', 'ij': 30000, 'transport': 75000, 'hebergement': 60000},
            {'role': 'membre', 'ij': 20000, 'transport': 75000, 'hebergement': 60000},
            {'role': 'membre', 'ij': 20000, 'transport': 75000, 'hebergement': 60000},
        ],
        'rapport': None,
    },
    {
        'objet': 'Mission terrain collecte donnees – Enquete beneficiaires S1 2026',
        'type_mission': 'terrain',
        'description': 'Mission de collecte de donnees terrain aupres des beneficiaires directs et indirects du programme pour alimenter le rapport de suivi du premier semestre 2026. Couverture de 45 villages.',
        'lieu_depart': 'Abidjan',
        'destination': '45 villages – Regions Abidjan, Bouake, Korhogo',
        'pays_destination': 'Cote d\'Ivoire',
        'objectifs': '1. Collecter les donnees sur les 25 indicateurs de suivi\n2. Conduire les focus groupes dans chaque zone\n3. Photographier les realisations principales\n4. Valider les donnees avec les equipes locales',
        'resultats_attendus': 'Base de donnees beneficiaires mise a jour\nRapport de collecte de donnees\n450 fiches individus completees\nPhoto-reportage des realisations',
        'date_debut_delta': -5, 'date_fin_delta': -1,
        'budget_prevu': 840000, 'budget_realise': 780000,
        'statut': 'en_cours',
        'membres': [
            {'role': 'chef_mission', 'ij': 20000, 'transport': 60000, 'hebergement': 45000},
            {'role': 'membre', 'ij': 12000, 'transport': 60000, 'hebergement': 45000},
            {'role': 'membre', 'ij': 12000, 'transport': 60000, 'hebergement': 45000},
            {'role': 'chauffeur', 'ij': 8000, 'transport': 0, 'hebergement': 45000},
        ],
        'rapport': None,
    },
    {
        'objet': 'Mission d\'audit financier externe – Exercice 2025',
        'type_mission': 'audit',
        'description': 'Mission d\'audit financier independant de l\'exercice 2025 menee par le cabinet d\'audit selectionne. Couverture du siege et des 3 antennes regionales.',
        'lieu_depart': 'Abidjan – Cabinet d\'audit',
        'destination': 'Abidjan, Bouake, Korhogo – Antennes regionales',
        'pays_destination': 'Cote d\'Ivoire',
        'objectifs': '1. Auditer les etats financiers de l\'exercice 2025\n2. Verifier la conformite des procedures comptables\n3. Evaluer l\'efficacite du controle interne\n4. Formuler des recommandations d\'amelioration',
        'resultats_attendus': 'Rapport d\'audit certifie\nOpinion du commissaire aux comptes\nLettre de recommandations au management\nPlan d\'amelioration du controle interne',
        'date_debut_delta': 20, 'date_fin_delta': 35,
        'budget_prevu': 4500000, 'budget_realise': 0,
        'statut': 'planifiee',
        'membres': [
            {'role': 'consultant', 'ij': 75000, 'transport': 30000, 'hebergement': 0},
            {'role': 'observateur', 'ij': 10000, 'transport': 0, 'hebergement': 0},
        ],
        'rapport': None,
    },
    {
        'objet': 'Mission d\'evaluation finale – Projet Eau Potable Zones Rurales',
        'type_mission': 'evaluation',
        'description': 'Mission d\'evaluation finale du Projet Eau Potable et Assainissement en Zones Rurales, projet cloture. Mesure de l\'atteinte des objectifs, des impacts et des enseignements a capitaliser.',
        'lieu_depart': 'Abidjan',
        'destination': 'Zones rurales beneficiaires – 35 villages',
        'pays_destination': 'Cote d\'Ivoire',
        'objectifs': '1. Mesurer l\'atteinte des cibles du cadre logique\n2. Evaluer la durabilite des realisations\n3. Identifier les facteurs de succes et les risques\n4. Formuler les recommandations pour les projets similaires',
        'resultats_attendus': 'Rapport d\'evaluation finale\nCapitalisation des lecons apprises\nRecommandations pour les futurs projets',
        'date_debut_delta': -30, 'date_fin_delta': -20,
        'budget_prevu': 2200000, 'budget_realise': 2150000,
        'statut': 'terminee',
        'membres': [
            {'role': 'chef_mission', 'ij': 30000, 'transport': 60000, 'hebergement': 45000},
            {'role': 'consultant', 'ij': 80000, 'transport': 60000, 'hebergement': 45000},
            {'role': 'membre', 'ij': 15000, 'transport': 60000, 'hebergement': 45000},
        ],
        'rapport': {
            'resume': 'L\'evaluation finale du Projet Eau Potable et Assainissement conclut a une atteinte globale des objectifs de 98%. Les 35 points d\'eau sont fonctionnels et frequentes. Le taux d\'acces a l\'eau potable est passe de 23% a 87% dans les zones ciblees. Les 200 latrines ameliorees sont en usage regulier.',
            'objectifs_atteints': '35 points d\'eau construits et fonctionnels - 100% ATTEINT\n200 latrines ameliorees - 100% ATTEINT\nTaux d\'acces eau potable passe de 23% a 87% - DEPASSE (cible 80%)\n12 500 personnes beneficiaires directs - ATTEINT\n340 agents WASH formes - DEPASSE (cible 300)',
            'observations': 'L\'appropriation des ouvrages par les communautes est excellente. Les comites de gestion villageois sont tous fonctionnels et collectent les contributions pour la maintenance. Quelques ouvrages (3 sur 35) presentent des defaillances mineures a corriger.',
            'recommandations': '1. Prevoir un programme de maintenance preventive des ouvrages\n2. Renforcer les capacites des comites de gestion en gestion financiere\n3. Envisager une extension du projet a 20 villages supplementaires\n4. Documenter les bonnes pratiques de gestion communautaire pour dissemination',
            'suite_a_donner': 'Maintenance corrective de 3 ouvrages defaillants\nFormation complementaire des comites de gestion\nRapport final transmis au bailleur et aux autorites',
            'statut': 'valide',
            'date_soumission': -18,
        },
    },
]

RAPPORTS_DATA = [
    # Sur projet
    {
        'type_objet': 'projet',
        'titre': 'Rapport mensuel d\'avancement – Projet Sante Communautaire – Juin 2026',
        'periode': 'mensuel',
        'date_delta': -2,
        'taux': 68,
        'observations': 'Le mois de juin 2026 a ete marque par l\'intensification des formations et le demarrage effectif des travaux de construction dans les 8 sites. Taux de formation agents de sante : 92% de la cible trimestrielle atteinte. Les enquetes beneficiaires avancent conformement au calendrier.',
        'problemes': 'Retard de livraison des equipements medicaux lots 2 et 3 (delai fournisseur : 2 semaines supplementaires)\nAcces difficile a 2 villages de montagne en periode de pluies\nAbsence du coordinateur du district de Cocody pour maladie (10 jours)',
        'recommandations': 'Anticiper les commandes du prochain trimestre avec un delai supplementaire\nPrevoir des voies d\'acces alternatives pour les villages isoles en saison des pluies\nAssurer une interim competente pour le coordinateur en conge maladie',
        'prochaines_etapes': 'Livraison et distribution equipements medicaux (semaine du 10 juin)\nCompletion formation nutrition dans 5 nouveaux sites\nPreparation rapport trimestriel Q2 2026',
        'statut': 'soumis',
    },
    {
        'type_objet': 'projet',
        'titre': 'Rapport trimestriel Q1 2026 – Programme AGRI-DEV',
        'periode': 'trimestriel',
        'date_delta': -60,
        'taux': 22,
        'observations': 'Premier trimestre 2026 marque par la mise en place des structures de gouvernance des 10 cooperatives et le demarrage des formations agricoles. 320 agriculteurs ont ete formes sur les techniques agro-ecologiques. Les plateformes d\'agregation sont en cours de construction.',
        'problemes': 'Retard dans l\'obtention des terrains pour 2 plateformes d\'agregation\nHausse du cout des materiaux de construction (+15%)\nDifficultees de recrutement des conseillers agricoles specialises',
        'recommandations': 'Accelerer les demarches foncierres avec les mairies\nRevoir le devis des constructions avec les entreprises\nElargir le vivier de recrutement aux agregataires et consultants independants',
        'prochaines_etapes': 'Resolution du foncier pour les 2 sites en attente\nFormation de 200 agriculteurs supplementaires en Q2\nLancement des plateformes operationnelles Q2',
        'statut': 'valide',
    },
    # Sur tache
    {
        'type_objet': 'tache',
        'titre': 'Rapport d\'execution – Formation 85 agents de sante – Module nutrition',
        'periode': 'mensuel',
        'date_delta': -5,
        'taux': 55,
        'observations': 'La formation du module nutrition infantile progresse conformement au planning. 47 agents sur 85 ont complete le module (55%). Les evaluations intermediaires montrent un taux de comprehension de 88%. La plateforme e-learning est utilisee en complement par 35 agents.',
        'problemes': 'Absence de 8 agents lors de la session du 20 mai (raisons diverses)\nDelai de certification plus long que prevu (traitement administratif)\nManque de materiel pedagogique pour le sous-module allaitement maternel',
        'recommandations': 'Organiser une session de rattrapage pour les 8 agents absents\nAccelerer le traitement des certificats de formation\nImprimer les supports manquants du sous-module allaitement',
        'prochaines_etapes': 'Session de rattrapage planifiee le 12 juin\nFormation des 38 agents restants – juin\nCertification de la 1re vague – 25 juin',
        'statut': 'brouillon',
    },
    {
        'type_objet': 'tache',
        'titre': 'Rapport de completion – Deploiement systeme suivi numerise',
        'periode': 'mensuel',
        'date_delta': -10,
        'taux': 70,
        'observations': 'Le deploiement du systeme de suivi numerise (application KoboToolbox) avance bien. 70% des enqueteurs sont formes et operationnels. 4 800 fiches beneficiaires ont ete collectees numeriquement sur les 6 000 prevues. La synchronisation en temps reel fonctionne dans les zones avec connexion.',
        'problemes': 'Problemes de connectivite dans 8 villages sans reseau mobile\nBatteries de 3 tablettes defectueuses\nResistances de 2 enqueteurs qui preferent le format papier',
        'recommandations': 'Prevoir la collecte hors ligne pour les zones sans reseau (mode offline de l\'application)\nRemplacement des 3 tablettes defectueuses\nAccompagnement renforce des 2 enqueteurs reticents',
        'prochaines_etapes': 'Configuration collecte hors ligne – semaine 1 juin\nRemplacement tablettes – demande en cours\nFormation complementaire 2 enqueteurs – semaine 2 juin',
        'statut': 'soumis',
    },
    # Sur reunion
    {
        'type_objet': 'reunion',
        'titre': 'Compte rendu – Revue technique indicateurs Q1 2026',
        'periode': 'trimestriel',
        'date_delta': -7,
        'taux': 72,
        'observations': 'La revue technique a rassemble 12 participants (techniciens et coordinateurs regionaux). L\'analyse des 25 indicateurs montre un taux d\'atteinte global de 72%. 18 indicateurs sont sur la bonne trajectoire. 7 indicateurs presentent des ecarts qui necessitent une attention particuliere.',
        'problemes': '3 indicateurs de sante en dessous des cibles : taux de consultation prenatale, vaccination DTP3, malnutrition aigue\nIndicateur d\'acces a l\'eau en retard dans la region de Man\nDonnees manquantes pour 2 villages difficiles d\'acces',
        'recommandations': 'Mettre en place un plan de rattrapage specifique pour les 3 indicateurs de sante en retard\nDiligencer la mission terrain pour les villages difficiles d\'acces\nRenforcer la coordination avec les services de sante departementaux',
        'prochaines_etapes': 'Plan de rattrapage elabore et valide par la Direction – 10 juin\nMission complementaire dans les villages isoles – 20 juin\nProchaine revue technique prevue en septembre 2026',
        'statut': 'valide',
    },
    {
        'type_objet': 'reunion',
        'titre': 'Compte rendu – Comite de Pilotage PRCC – Bilan semestriel S1 2026',
        'periode': 'semestriel',
        'date_delta': 5,
        'taux': 65,
        'observations': 'Le COPIL du 5 juin 2026 a rassemble 18 participants dont les representants des bailleurs UE, BM et AFD. Presentation du bilan semestriel : taux d\'execution physique 65% (cible 60%) et taux financier 58% (cible 65%). Ecart financier explique par le retard de livraison des equipements.',
        'problemes': 'Ecart entre taux physique (65%) et financier (58%) qui suscite des questions des bailleurs\nAtteinte partielle de 3 resultats clefs\nRetard dans le recrutement de 2 postes experts',
        'recommandations': 'Preparer une note explicative sur l\'ecart physique/financier pour rassurer les bailleurs\nReviser le plan de recrutement des postes experts\nMobiliser les ressources non decaissees avant fin Q3',
        'prochaines_etapes': 'Transmission note explicative aux bailleurs – 8 juin\nRelance processus recrutement postes experts – semaine 2 juin\nProchain COPIL – 5 septembre 2026',
        'statut': 'brouillon',
    },
    # Sur mission
    {
        'type_objet': 'mission',
        'titre': 'Rapport d\'execution – Mission collecte donnees beneficiaires S1 2026',
        'periode': 'semestriel',
        'date_delta': -1,
        'taux': 60,
        'observations': 'La mission de collecte est en cours dans sa 3eme journee. 27 villages sur 45 ont ete couverts (60%). La qualite des donnees collectees est satisfaisante. L\'equipe avance selon le planning avec quelques ajustements logistiques en raison des conditions de piste.',
        'problemes': 'Panne du vehicule principal – reparation de 6 heures\nPluies intenses ayant rendu impraticable la piste vers 3 villages\nUn enqueteur absent pour raisons personnelles (remplace en urgence)',
        'recommandations': 'Prevoir un vehicule de secours pour les missions terrain longues\nAdapter l\'itineraire en fonction de la meteorologie\nConstituer une liste d\'enqueteurs suppleants disponibles a court terme',
        'prochaines_etapes': 'Couverture des 18 villages restants – 2 prochains jours\nSaisie et validation des donnees – semaine suivante\nRapport de collecte complet dans les 7 jours',
        'statut': 'brouillon',
    },
    {
        'type_objet': 'mission',
        'titre': 'Rapport de synthese – Mission evaluation finale Projet Eau Potable',
        'periode': 'annuel',
        'date_delta': -20,
        'taux': 98,
        'observations': 'Mission d\'evaluation finale conclue avec succes. Taux d\'atteinte des objectifs de 98%. Les realisations physiques sont conformes aux specifications techniques. L\'appropriation communautaire est excellente. La durabilite des ouvrages est assuree par des mecanismes de gouvernance communautaire fonctionnels.',
        'problemes': 'Quelques ouvrages presentent des defaillances mineures (3 sur 35)\nComites de gestion de 5 villages manquent de competences en gestion financiere',
        'recommandations': 'Maintenance corrective de 3 ouvrages defaillants dans les 30 jours\nFormation complementaire des comites de gestion faibles\nDocumentation et dissemination des bonnes pratiques',
        'prochaines_etapes': 'Rapport final transmis aux bailleurs\nMise en oeuvre des recommandations prioritaires\nCapitalisation et partage des lecons apprises dans les autres projets',
        'statut': 'publie',
    },
]


class Command(BaseCommand):
    help = 'Seed missions enrichies (membres + rapports) et rapports d\'avancement multi-contextes'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les missions et rapports existants')

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        with transaction.atomic():
            admin = self._get_admin()
            if not admin:
                self.stdout.write(self.style.ERROR('[ERREUR] Aucun admin. Lancez seed_lot1 d\'abord.'))
                return

            users  = self._get_users()
            projet = self._get_projet()

            missions  = self._seed_missions(admin, users, projet)
            rapports  = self._seed_rapports(admin, users, projet, missions)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed missions_rapports termine !'))
        self.stdout.write(f'   - {len(missions)} missions (avec membres et rapports)')
        self.stdout.write(f'   - {len(rapports)} rapports d\'avancement (projet/tache/reunion/mission)')

    def _reset(self):
        from execution.models import Mission, RapportAvancement, MembreMission, RapportMission
        self.stdout.write(self.style.WARNING('[RESET] Suppression...'))
        RapportMission.objects.all().delete()
        MembreMission.objects.all().delete()
        RapportAvancement.objects.all().delete()
        Mission.objects.all().delete()
        self.stdout.write('   Termine.')

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_users(self):
        from accounts.models import User
        return list(User.objects.all()[:10])

    def _get_projet(self):
        from programmes_projets.models import Projet
        return Projet.objects.filter(statut='en_cours').first()

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Cree') if created else self.style.WARNING('Existant')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:80]}')

    # -- Missions --------------------------------------------------------------
    def _seed_missions(self, admin, users, projet):
        from execution.models import Mission, MembreMission, RapportMission

        self.stdout.write('\n>> Missions enrichies...')
        today = date.today()
        result = []

        for data in MISSIONS_DATA:
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
                    'pays_destination': data.get('pays_destination', "Cote d'Ivoire"),
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
            self._log('Mission', mission, created)
            result.append(mission)

            if created:
                # Membres
                members_users = [admin] + random.sample(users, min(len(data['membres']) - 1, len(users)))
                for j, role_data in enumerate(data['membres']):
                    user = members_users[j] if j < len(members_users) else admin
                    MembreMission.objects.get_or_create(
                        mission=mission,
                        user=user,
                        defaults={
                            'role_mission': role_data['role'],
                            'indemnite_journaliere': role_data['ij'],
                            'frais_transport': role_data['transport'],
                            'frais_hebergement': role_data.get('hebergement', 0),
                        }
                    )
                    self.stdout.write(f'    + Membre [{role_data["role"]}]: {user.nom_complet or user.email}')

                # Rapport de mission
                if data['rapport']:
                    rp = data['rapport']
                    date_soumission = today + timedelta(days=rp.get('date_soumission', -1)) if isinstance(rp.get('date_soumission'), int) else None
                    rapport, _ = RapportMission.objects.get_or_create(
                        mission=mission,
                        defaults={
                            'redacteur': admin,
                            'resume': rp.get('resume', ''),
                            'objectifs_atteints': rp.get('objectifs_atteints', ''),
                            'observations': rp.get('observations', ''),
                            'recommandations': rp.get('recommandations', ''),
                            'suite_a_donner': rp.get('suite_a_donner', ''),
                            'statut': rp.get('statut', 'brouillon'),
                            'date_soumission': date_soumission,
                            'valide_par': admin if rp.get('statut') == 'valide' else None,
                            'date_validation': timezone.now() if rp.get('statut') == 'valide' else None,
                        }
                    )
                    self.stdout.write(f'    + Rapport mission [{rp["statut"]}]')

        return result

    # -- Rapports d'avancement -------------------------------------------------
    def _seed_rapports(self, admin, users, projet, missions):
        from execution.models import RapportAvancement, Tache, Reunion

        self.stdout.write('\n>> Rapports d\'avancement multi-contextes...')
        today = date.today()
        taches   = list(Tache.objects.all()[:10])
        reunions = list(Reunion.objects.all()[:8])
        result   = []

        for i, data in enumerate(RAPPORTS_DATA):
            date_rapport = today + timedelta(days=data['date_delta'])

            # Lier au bon objet
            kwargs = {
                'type_objet': data['type_objet'],
                'titre': data['titre'],
                'periode': data['periode'],
                'date_rapport': date_rapport,
                'taux_realisation': data['taux'],
                'observations': data['observations'],
                'problemes': data['problemes'],
                'recommandations': data['recommandations'],
                'prochaines_etapes': data['prochaines_etapes'],
                'redacteur': admin,
                'statut': data['statut'],
                'valide_par': admin if data['statut'] in ('valide', 'publie') else None,
                'date_validation': timezone.now() if data['statut'] in ('valide', 'publie') else None,
            }

            if data['type_objet'] == 'projet':
                kwargs['projet'] = projet
            elif data['type_objet'] == 'tache' and taches:
                kwargs['tache'] = taches[i % len(taches)]
            elif data['type_objet'] == 'reunion' and reunions:
                kwargs['reunion'] = reunions[i % len(reunions)]
            elif data['type_objet'] == 'mission' and missions:
                kwargs['mission'] = missions[i % len(missions)]

            rapport, created = RapportAvancement.objects.get_or_create(
                titre=data['titre'],
                defaults=kwargs,
            )
            self._log(f'Rapport [{data["type_objet"]}][{data["statut"]}]', rapport, created)
            result.append(rapport)

        return result
