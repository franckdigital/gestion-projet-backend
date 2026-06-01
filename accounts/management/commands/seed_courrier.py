"""
Seed données de démonstration pour :
  - Courriers administratifs entrants & sortants
  - Diligences
  - Réunions (avec participants)
  - Événements (avec participants)

Usage : python manage.py seed_courrier [--reset]
"""
import random
from datetime import date, time, timedelta, datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# -- Données courriers entrants ------------------------------------------------
ENTRANTS = [
    {
        'expediteur': 'Ministère du Plan et du Développement',
        'organisation_expediteur': 'Direction de la Planification Nationale',
        'email_expediteur': 'planification@mplan.gouv.ci',
        'objet': 'Transmission du rapport d\'évaluation du Plan National de Développement 2021-2025',
        'description': 'Veuillez trouver ci-joint le rapport complet d\'évaluation à mi-parcours du PND. Une réunion de restitution est prévue pour le 15 juin 2026.',
        'urgence': 'urgent',
        'canal': 'email',
        'statut': 'affecte',
    },
    {
        'expediteur': 'Union Européenne – Délégation en Côte d\'Ivoire',
        'organisation_expediteur': 'Section Coopération',
        'email_expediteur': 'delegation.abidjan@eeas.europa.eu',
        'objet': 'Demande de rapport d\'avancement – Projet AGRI-DEV Q1 2026',
        'description': 'Conformément aux termes de la convention de financement, nous sollicitons la transmission du rapport d\'avancement du premier trimestre 2026 avant le 30 mai 2026.',
        'urgence': 'tres_urgent',
        'canal': 'email',
        'statut': 'en_cours',
    },
    {
        'expediteur': 'Banque Mondiale – Bureau Abidjan',
        'organisation_expediteur': 'Département Développement Social',
        'email_expediteur': 'bm.abidjan@worldbank.org',
        'objet': 'Notification de mission de supervision – Projet d\'Appui aux Communautés Rurales',
        'description': 'Une mission de supervision conjointe est programmée du 10 au 20 juin 2026. Prière de préparer les documents de suivi financier et technique.',
        'urgence': 'urgent',
        'canal': 'email',
        'statut': 'recu',
    },
    {
        'expediteur': 'Dr. Konan Yao Brice',
        'organisation_expediteur': 'Mairie de Bouaké',
        'email_expediteur': 'maire.bouake@mairiehouake.ci',
        'objet': 'Demande de partenariat pour l\'aménagement du marché municipal de Bouaké',
        'description': 'La Mairie de Bouaké sollicite un partenariat avec votre organisation pour le financement et l\'accompagnement technique du projet d\'aménagement du marché municipal.',
        'urgence': 'normal',
        'canal': 'papier',
        'statut': 'recu',
    },
    {
        'expediteur': 'USAID Côte d\'Ivoire',
        'organisation_expediteur': 'Bureau des Programmes de Développement',
        'email_expediteur': 'programs@usaid-ci.gov',
        'objet': 'Invitation à l\'atelier régional de partage des bonnes pratiques – Juin 2026',
        'description': 'USAID Côte d\'Ivoire vous invite à participer à l\'atelier régional de partage des bonnes pratiques en matière de développement rural qui se tiendra à Grand-Bassam les 18 et 19 juin 2026.',
        'urgence': 'normal',
        'canal': 'email',
        'statut': 'traite',
    },
    {
        'expediteur': 'Direction Régionale des Impôts – Abidjan',
        'organisation_expediteur': 'Direction Générale des Impôts',
        'email_expediteur': 'dgi.abidjan@impots.gouv.ci',
        'objet': 'Notification de contrôle fiscal – Exercice 2025',
        'description': 'Votre organisation est notifiée d\'un contrôle fiscal portant sur l\'exercice 2025. Prière de préparer les pièces comptables pour le 5 juin 2026.',
        'urgence': 'tres_urgent',
        'canal': 'papier',
        'statut': 'affecte',
    },
    {
        'expediteur': 'Mme Ouattara Fatoumata',
        'organisation_expediteur': 'Réseau des Femmes pour le Développement Rural',
        'email_expediteur': 'rfdr@rfdr-ci.org',
        'objet': 'Demande de subvention pour activités génératrices de revenus – Korhogo',
        'description': 'Notre réseau regroupe 450 femmes dans la région de Korhogo. Nous sollicitons un appui financier pour le démarrage de 12 activités génératrices de revenus.',
        'urgence': 'normal',
        'canal': 'papier',
        'statut': 'recu',
    },
    {
        'expediteur': 'Ministère de la Santé',
        'organisation_expediteur': 'Direction de la Santé Communautaire',
        'email_expediteur': 'sante.communautaire@sante.gouv.ci',
        'objet': 'Protocole de collaboration pour la campagne de vaccination communautaire',
        'description': 'Suite aux échanges lors de la réunion du 12 avril, nous transmettons le projet de protocole de collaboration pour validation et signature.',
        'urgence': 'urgent',
        'canal': 'email',
        'statut': 'en_cours',
    },
    {
        'expediteur': 'AFD – Agence Française de Développement',
        'organisation_expediteur': 'Direction des Opérations Afrique de l\'Ouest',
        'email_expediteur': 'afrique.ouest@afd.fr',
        'objet': 'Appel à propositions – Fonds d\'Innovation pour le Développement 2026',
        'description': 'L\'AFD lance un appel à propositions pour son Fonds d\'Innovation pour le Développement. Clôture des candidatures : 30 juillet 2026.',
        'urgence': 'normal',
        'canal': 'email',
        'statut': 'traite',
    },
    {
        'expediteur': 'Conseil Régional du Gbêkê',
        'organisation_expediteur': 'Présidence du Conseil Régional',
        'email_expediteur': 'presidence@conseil-gbeke.ci',
        'objet': 'Invitation à la cérémonie de lancement du Plan Régional de Développement 2026-2030',
        'description': 'Nous avons l\'honneur de vous inviter à la cérémonie officielle de lancement du Plan Régional de Développement du Gbêkê qui aura lieu le 20 juin 2026 à Bouaké.',
        'urgence': 'normal',
        'canal': 'papier',
        'statut': 'cloture',
    },
]

# -- Données courriers sortants ------------------------------------------------
SORTANTS = [
    {
        'type_courrier': 'lettre',
        'objet': 'Réponse à la demande de rapport d\'avancement – Projet AGRI-DEV Q1 2026',
        'corps': (
            'Monsieur le Délégué,\n\n'
            'En réponse à votre courrier du 15 mai 2026 relatif au rapport d\'avancement du Projet AGRI-DEV pour le premier trimestre 2026, '
            'nous avons l\'honneur de vous transmettre en pièce jointe ledit rapport dûment validé par notre Directeur Exécutif.\n\n'
            'Ce rapport fait état d\'un taux d\'exécution physique de 78% et d\'un taux d\'exécution financière de 72% à fin mars 2026. '
            'Les principales réalisations concernent la mise en place de 15 coopératives agricoles et la formation de 320 agriculteurs.\n\n'
            'Nous restons disponibles pour tout complément d\'information.\n\n'
            'Veuillez agréer, Monsieur le Délégué, l\'expression de notre haute considération.'
        ),
        'destinataire': 'M. Jean-Pierre Müller',
        'organisation_destinataire': 'Union Européenne – Délégation en Côte d\'Ivoire',
        'email_destinataire': 'delegation.abidjan@eeas.europa.eu',
        'statut': 'expedie',
    },
    {
        'type_courrier': 'note_service',
        'objet': 'Procédures de préparation des documents pour la mission de supervision Banque Mondiale',
        'corps': (
            'Objet : Préparation documents mission Banque Mondiale – 10 au 20 juin 2026\n\n'
            'À l\'attention de tous les responsables de projets,\n\n'
            'Suite à la notification de la mission de supervision de la Banque Mondiale programmée du 10 au 20 juin 2026, '
            'chaque responsable de projet est prié de préparer les documents suivants :\n\n'
            '1. Rapport d\'avancement Q1 2026 (physique et financier)\n'
            '2. Plan d\'action actualisé\n'
            '3. Tableau de suivi des indicateurs\n'
            '4. Rapports de audit si disponibles\n\n'
            'Ces documents doivent être transmis à la Direction Générale au plus tard le 5 juin 2026.'
        ),
        'destinataire': 'Tous les responsables de projets',
        'organisation_destinataire': 'Direction interne',
        'statut': 'expedie',
    },
    {
        'type_courrier': 'lettre',
        'objet': 'Accusé de réception – Demande de partenariat Mairie de Bouaké',
        'corps': (
            'Monsieur le Maire,\n\n'
            'Nous accusons bonne réception de votre courrier du 2 mai 2026 relatif à la demande de partenariat '
            'pour l\'aménagement du marché municipal de Bouaké.\n\n'
            'Votre demande a été enregistrée et transmise à notre Comité de Partenariat pour analyse. '
            'Nous reviendrons vers vous dans un délai de 30 jours avec notre position.\n\n'
            'Veuillez agréer, Monsieur le Maire, l\'expression de notre considération distinguée.'
        ),
        'destinataire': 'Dr. Konan Yao Brice',
        'organisation_destinataire': 'Mairie de Bouaké',
        'email_destinataire': 'maire.bouake@mairiehouake.ci',
        'statut': 'expedie',
    },
    {
        'type_courrier': 'rapport',
        'objet': 'Rapport d\'activités mensuel – Avril 2026',
        'corps': (
            'Le présent rapport rend compte des activités réalisées au cours du mois d\'avril 2026.\n\n'
            'FAITS SAILLANTS DU MOIS :\n'
            '• Formation de 85 agents communautaires à Korhogo\n'
            '• Lancement de 3 nouvelles coopératives féminines à Man\n'
            '• Organisation de 2 ateliers de sensibilisation (450 participants)\n'
            '• Mission de suivi dans 12 villages de la région du Gbêkê\n\n'
            'TAUX D\'EXÉCUTION GLOBAL : 74% (physique) / 68% (financier)\n\n'
            'DÉFIS RENCONTRÉS :\n'
            'Difficultés d\'accès à certaines zones en raison des pluies précoces.\n\n'
            'PERSPECTIVES POUR MAI 2026 :\n'
            'Poursuite des formations, organisation de la journée du paysan.'
        ),
        'destinataire': 'M. Henri Dupont, Directeur',
        'organisation_destinataire': 'Agence Française de Développement',
        'email_destinataire': 'afrique.ouest@afd.fr',
        'statut': 'signe',
    },
    {
        'type_courrier': 'lettre',
        'objet': 'Confirmation de participation – Atelier USAID Bonnes Pratiques',
        'corps': (
            'Madame, Monsieur,\n\n'
            'Suite à votre invitation relative à l\'atelier régional de partage des bonnes pratiques '
            'en matière de développement rural prévu les 18 et 19 juin 2026 à Grand-Bassam, '
            'nous avons le plaisir de confirmer notre participation.\n\n'
            'Notre délégation sera composée de :\n'
            '1. M. Diallo Ibrahima – Directeur des Opérations\n'
            '2. Mme Koné Aminata – Coordinatrice Programmes Ruraux\n'
            '3. M. Touré Salif – Expert Suivi-Évaluation\n\n'
            'Veuillez agréer l\'expression de notre considération distinguée.'
        ),
        'destinataire': 'Représentant Résidentiel',
        'organisation_destinataire': 'USAID Côte d\'Ivoire',
        'email_destinataire': 'programs@usaid-ci.gov',
        'statut': 'expedie',
    },
    {
        'type_courrier': 'decision',
        'objet': 'Décision de mise en place du Comité de Pilotage du Programme PRCC',
        'corps': (
            'Le Directeur Exécutif,\n\n'
            'VU les statuts et règlement intérieur de l\'organisation,\n'
            'VU la convention de financement signée avec les bailleurs,\n'
            'CONSIDÉRANT la nécessité d\'assurer un pilotage stratégique du Programme PRCC,\n\n'
            'DÉCIDE :\n\n'
            'Article 1 : Il est créé un Comité de Pilotage (COPIL) du Programme de Renforcement des Capacités Communautaires.\n'
            'Article 2 : Le COPIL est composé de :\n'
            '  - Le Directeur Exécutif (Président)\n'
            '  - Le Directeur des Opérations\n'
            '  - Le Responsable Financier\n'
            '  - Les Représentants des bailleurs\n'
            '  - Les Représentants des bénéficiaires\n'
            'Article 3 : Le COPIL se réunit trimestriellement.\n\n'
            'Fait à Abidjan, le 31 mai 2026.'
        ),
        'destinataire': 'Membres du COPIL PRCC',
        'organisation_destinataire': 'Interne',
        'statut': 'signe',
    },
    {
        'type_courrier': 'lettre',
        'objet': 'Demande de prorogation du délai de soumission – Appel à propositions AFD 2026',
        'corps': (
            'Madame, Monsieur,\n\n'
            'Nous avons bien pris connaissance de votre appel à propositions pour le Fonds d\'Innovation '
            'pour le Développement 2026 avec une date de clôture fixée au 30 juillet 2026.\n\n'
            'Notre organisation est en cours de finalisation d\'une proposition innovante sur la thématique '
            'de l\'agriculture climatiquement intelligente. Cependant, en raison des contraintes calendaires '
            'liées à nos opérations terrain, nous sollicitons respectueusement une prorogation du délai '
            'de 15 jours, soit jusqu\'au 14 août 2026.\n\n'
            'Nous vous remercions de l\'attention que vous voudrez bien accorder à cette requête.'
        ),
        'destinataire': 'Direction des Opérations Afrique de l\'Ouest',
        'organisation_destinataire': 'Agence Française de Développement',
        'email_destinataire': 'afrique.ouest@afd.fr',
        'statut': 'expedie',
    },
    {
        'type_courrier': 'note_service',
        'objet': 'Organisation de la réponse au contrôle fiscal DGI – Exercice 2025',
        'corps': (
            'À l\'attention du Responsable Financier et Comptable,\n\n'
            'Suite à la notification de contrôle fiscal reçue de la Direction Générale des Impôts, '
            'je vous instruis de :\n\n'
            '1. Constituer immédiatement le dossier de réponse au contrôle\n'
            '2. Rassembler toutes les pièces comptables de l\'exercice 2025\n'
            '3. Prendre contact avec notre cabinet d\'audit pour assistance\n'
            '4. Me soumettre un rapport de situation avant le 3 juin 2026\n\n'
            'Ce dossier est PRIORITAIRE. Mobilisez toutes les ressources nécessaires.'
        ),
        'destinataire': 'M. N\'Guessan Paul – Responsable Financier',
        'organisation_destinataire': 'Direction Financière',
        'statut': 'expedie',
    },
]

# -- Données diligences --------------------------------------------------------
DILIGENCES_DATA = [
    {
        'type_diligence': 'action',
        'description': 'Préparer et transmettre à l\'UE le rapport d\'avancement AGRI-DEV Q1 2026 dûment validé',
        'statut': 'realisee',
        'resultat': 'Rapport transmis le 22 mai 2026 par email. Accusé de réception reçu le 23 mai.',
        'echeance_delta': -10,
    },
    {
        'type_diligence': 'action',
        'description': 'Constituer le dossier complet pour la mission de supervision Banque Mondiale (rapports, tableaux de suivi, audits)',
        'statut': 'en_cours',
        'echeance_delta': 10,
    },
    {
        'type_diligence': 'decision',
        'description': 'Décider de la participation ou non à l\'atelier AFD sur les innovations agricoles',
        'statut': 'realisee',
        'resultat': 'Décision prise de participer avec une délégation de 3 personnes. Inscription confirmée.',
        'echeance_delta': -5,
    },
    {
        'type_diligence': 'action',
        'description': 'Rassembler tous les documents comptables de l\'exercice 2025 pour le contrôle fiscal DGI',
        'statut': 'en_cours',
        'echeance_delta': 4,
    },
    {
        'type_diligence': 'action',
        'description': 'Préparer la réponse à la demande de partenariat de la Mairie de Bouaké – Analyse de faisabilité',
        'statut': 'ouverte',
        'echeance_delta': 15,
    },
    {
        'type_diligence': 'action',
        'description': 'Finaliser et soumettre la candidature au Fonds d\'Innovation AFD 2026',
        'statut': 'ouverte',
        'echeance_delta': 45,
    },
    {
        'type_diligence': 'tache',
        'description': 'Organiser la réunion de préparation à la mission de supervision BM avec tous les responsables de projets',
        'statut': 'ouverte',
        'echeance_delta': 5,
    },
    {
        'type_diligence': 'action',
        'description': 'Traiter la demande de subvention du Réseau des Femmes pour le Développement Rural – Korhogo',
        'statut': 'ouverte',
        'echeance_delta': 30,
    },
    {
        'type_diligence': 'action',
        'description': 'Contresigner le protocole de collaboration avec le Ministère de la Santé et retourner une exemplaire',
        'statut': 'en_cours',
        'echeance_delta': 7,
    },
    {
        'type_diligence': 'tache',
        'description': 'Préparer le discours et les supports de présentation pour la cérémonie de lancement du PRD Gbêkê',
        'statut': 'cloturee',
        'resultat': 'Discours préparé et validé. Présentation PowerPoint finalisée. Intervention réalisée avec succès.',
        'echeance_delta': -15,
    },
    {
        'type_diligence': 'activite',
        'description': 'Réaliser la mission de suivi terrain dans les 12 villages de la région du Gbêkê – Rapport à produire',
        'statut': 'realisee',
        'resultat': 'Mission réalisée du 22 au 26 avril 2026. Rapport de mission transmis à la Direction le 30 avril.',
        'echeance_delta': -20,
    },
    {
        'type_diligence': 'action',
        'description': 'Élaborer et diffuser la note de service sur la procédure de préparation des documents pour la supervision BM',
        'statut': 'realisee',
        'resultat': 'Note de service élaborée et transmise à tous les responsables le 25 mai 2026.',
        'echeance_delta': -6,
    },
]

# -- Données réunions ----------------------------------------------------------
REUNIONS_DATA = [
    {
        'type_reunion': 'comite_pilotage',
        'objet': 'Comité de Pilotage PRCC – Bilan semestriel S1 2026',
        'description': 'Réunion trimestrielle du COPIL pour faire le bilan de l\'exécution du programme au premier semestre 2026 et valider le plan d\'action S2.',
        'date_delta': 5,
        'heure_debut': time(9, 0),
        'heure_fin': time(13, 0),
        'lieu': 'Salle de Conférence A – Siège Social, Abidjan Plateau',
        'plateforme': 'presentiel',
        'statut': 'planifiee',
        'participants_externes': [
            {'nom': 'M. Jean-Pierre Müller', 'email': 'jp.muller@eeas.eu', 'org': 'Délégation UE'},
            {'nom': 'Mme Sophie Leclerc', 'email': 's.leclerc@afd.fr', 'org': 'AFD'},
            {'nom': 'M. Mamadou Diallo', 'email': 'm.diallo@worldbank.org', 'org': 'Banque Mondiale'},
        ],
    },
    {
        'type_reunion': 'interne',
        'objet': 'Réunion de préparation à la mission de supervision Banque Mondiale',
        'description': 'Réunion interne urgente pour coordonner la préparation des documents et la logistique de la mission de supervision BM du 10 au 20 juin 2026.',
        'date_delta': 2,
        'heure_debut': time(14, 0),
        'heure_fin': time(17, 0),
        'lieu': 'Salle de Réunion B – 2ème étage',
        'plateforme': 'presentiel',
        'statut': 'confirmee',
        'participants_externes': [],
    },
    {
        'type_reunion': 'partenaires',
        'objet': 'Réunion de négociation du protocole de collaboration – Ministère de la Santé',
        'description': 'Finalisation et signature du protocole de collaboration pour la campagne de vaccination communautaire dans les zones d\'intervention du programme.',
        'date_delta': 8,
        'heure_debut': time(10, 0),
        'heure_fin': time(12, 0),
        'lieu': 'Ministère de la Santé – Direction de la Santé Communautaire, Abidjan',
        'plateforme': 'presentiel',
        'statut': 'planifiee',
        'participants_externes': [
            {'nom': 'Dr. Kouassi Ange', 'email': 'a.kouassi@sante.gouv.ci', 'org': 'Ministère de la Santé'},
            {'nom': 'Mme Traoré N\'Goné', 'email': 'n.traore@sante.gouv.ci', 'org': 'Dir. Santé Communautaire'},
        ],
    },
    {
        'type_reunion': 'comite_technique',
        'objet': 'Revue technique des indicateurs de performance Q1 2026',
        'description': 'Analyse approfondie des indicateurs de suivi-évaluation du programme pour le premier trimestre. Identification des écarts et proposition de mesures correctives.',
        'date_delta': -7,
        'heure_debut': time(8, 30),
        'heure_fin': time(11, 30),
        'lieu': 'Salle de Réunion A – Siège',
        'plateforme': 'presentiel',
        'statut': 'tenue',
        'participants_externes': [],
    },
    {
        'type_reunion': 'bailleurs',
        'objet': 'Point de situation avec l\'USAID – Programmes en cours',
        'description': 'Réunion mensuelle de suivi avec la représentation USAID pour faire le point sur l\'avancement des programmes cofinancés et discuter des prochaines étapes.',
        'date_delta': -3,
        'heure_debut': time(15, 0),
        'heure_fin': time(16, 30),
        'lieu': 'Résidence USAID – Cocody',
        'plateforme': 'presentiel',
        'statut': 'tenue',
        'participants_externes': [
            {'nom': 'Mme Gloria Williams', 'email': 'g.williams@usaid.gov', 'org': 'USAID'},
            {'nom': 'M. Franck Assi', 'email': 'f.assi@usaid-ci.gov', 'org': 'USAID CI'},
        ],
    },
    {
        'type_reunion': 'interne',
        'objet': 'Réunion hebdomadaire de coordination opérationnelle',
        'description': 'Coordination hebdomadaire de toutes les directions pour le suivi des activités en cours, identification des blocages et planification de la semaine.',
        'date_delta': 1,
        'heure_debut': time(8, 0),
        'heure_fin': time(9, 30),
        'lieu': 'Salle de Conférence – Siège',
        'plateforme': 'hybride',
        'lien_visio': 'https://meet.google.com/erp-reunion-hebdo',
        'statut': 'confirmee',
        'participants_externes': [],
    },
    {
        'type_reunion': 'atelier',
        'objet': 'Atelier de planification stratégique 2026-2027',
        'description': 'Atelier de deux jours pour la planification stratégique de la deuxième phase du programme. Révision du cadre logique, des indicateurs et du plan d\'action.',
        'date_delta': 15,
        'heure_debut': time(8, 0),
        'heure_fin': time(17, 0),
        'lieu': 'Hôtel Ivoire – Salle Bassam, Abidjan',
        'plateforme': 'presentiel',
        'statut': 'planifiee',
        'participants_externes': [
            {'nom': 'M. Kofi Mensah', 'email': 'k.mensah@consultant-dev.com', 'org': 'Cabinet Conseil MENSAH & Associés'},
            {'nom': 'Dr. Amina Ba', 'email': 'a.ba@evaluation-afrique.org', 'org': 'Cabinet Évaluation Afrique'},
        ],
    },
    {
        'type_reunion': 'formation',
        'objet': 'Formation des équipes terrain – Techniques de collecte de données numérique',
        'description': 'Formation pratique sur les outils numériques de collecte de données (ODK, KoboToolbox) à l\'attention des agents de terrain et des coordinateurs régionaux.',
        'date_delta': 20,
        'heure_debut': time(9, 0),
        'heure_fin': time(16, 0),
        'lieu': 'Centre de Formation NTICDEV – Zone 4, Abidjan',
        'plateforme': 'presentiel',
        'statut': 'planifiee',
        'participants_externes': [
            {'nom': 'M. Eric Bah', 'email': 'e.bah@nticdev.ci', 'org': 'NTICDEV – Formateur'},
        ],
    },
]

# -- Données événements --------------------------------------------------------
EVENEMENTS_DATA = [
    {
        'titre': 'Atelier National de Renforcement des Capacités en Suivi-Évaluation',
        'type_evenement': 'atelier',
        'description': 'Cet atelier national réunit les responsables de suivi-évaluation de toutes les organisations partenaires pour un renforcement des capacités sur les méthodes d\'évaluation participative et les outils numériques de collecte de données.',
        'objectifs': '1. Maîtriser les méthodes d\'évaluation participative\n2. Utiliser les outils numériques de collecte (ODK, KoboToolbox)\n3. Produire des rapports de qualité\n4. Harmoniser les pratiques S&E entre organisations',
        'date_debut_delta': 12,
        'duree_heures': 8,
        'lieu': 'Hôtel Sofitel Ivoire – Grand Salon, Abidjan',
        'nb_participants_attendus': 80,
        'budget_prevu': 12000000,
        'est_public': False,
        'inscription_requise': True,
        'statut': 'ouvert_inscriptions',
        'participants': [
            {'nom': 'Mme Koné Rokiatou', 'email': 'r.kone@ong-sante.ci', 'org': 'ONG Santé Pour Tous'},
            {'nom': 'M. Diallo Seydou', 'email': 's.diallo@caritas.ci', 'org': 'Caritas Côte d\'Ivoire'},
            {'nom': 'Mme Touré Fatoumata', 'email': 'f.toure@croixrouge.ci', 'org': 'Croix Rouge CI'},
        ],
    },
    {
        'titre': 'Conférence Internationale sur le Développement Rural Durable en Afrique de l\'Ouest',
        'type_evenement': 'conference',
        'description': 'Conférence internationale réunissant décideurs, praticiens et chercheurs pour partager les expériences et innovations en matière de développement rural durable dans les pays d\'Afrique de l\'Ouest.',
        'objectifs': '1. Partager les meilleures pratiques de développement rural\n2. Créer des réseaux de collaboration régionaux\n3. Formuler des recommandations politiques\n4. Promouvoir les innovations agricoles adaptées au climat',
        'date_debut_delta': 30,
        'duree_heures': 16,
        'lieu': 'Palais des Congrès d\'Abidjan',
        'nb_participants_attendus': 300,
        'budget_prevu': 50000000,
        'est_public': True,
        'inscription_requise': True,
        'statut': 'ouvert_inscriptions',
        'participants': [
            {'nom': 'Prof. Amadou Kouyaté', 'email': 'a.kouyate@univ-abidjan.edu', 'org': 'Université Félix Houphouët-Boigny'},
            {'nom': 'Dr. Marie-Claire Dupont', 'email': 'm.dupont@cirad.fr', 'org': 'CIRAD'},
        ],
    },
    {
        'titre': 'Formation sur la Gestion Axée sur les Résultats (GAR) – Korhogo',
        'type_evenement': 'formation',
        'description': 'Formation décentralisée sur la Gestion Axée sur les Résultats pour les équipes terrain basées dans la région des Savanes. Formation pratique avec études de cas tirées des projets en cours.',
        'objectifs': '1. Comprendre les principes de la GAR\n2. Élaborer des cadres logiques rigoureux\n3. Définir et mesurer des indicateurs SMART\n4. Produire des rapports orientés résultats',
        'date_debut_delta': -5,
        'duree_heures': 16,
        'lieu': 'Maison des Organisations – Korhogo',
        'nb_participants_attendus': 35,
        'budget_prevu': 3500000,
        'est_public': False,
        'inscription_requise': True,
        'statut': 'termine',
        'participants': [
            {'nom': 'M. Coulibaly Ibrahim', 'email': 'i.coulibaly@terrain.ci', 'org': 'Équipe terrain Korhogo'},
            {'nom': 'Mme Bamba Aïcha', 'email': 'a.bamba@terrain.ci', 'org': 'Équipe terrain Korhogo'},
            {'nom': 'M. Soro Youssouf', 'email': 'y.soro@terrain.ci', 'org': 'Coordinateur Régional Savanes'},
        ],
    },
    {
        'titre': 'Forum des Femmes Rurales – Édition 2026',
        'type_evenement': 'forum',
        'description': 'Forum annuel réunissant les femmes rurales bénéficiaires des programmes de développement pour partager leurs expériences, exposer leurs productions et plaider pour l\'amélioration de leurs conditions.',
        'objectifs': '1. Valoriser les réalisations des femmes rurales\n2. Créer des synergies entre groupements féminins\n3. Présenter les produits des AGR aux acheteurs potentiels\n4. Formuler des recommandations aux décideurs',
        'date_debut_delta': 25,
        'duree_heures': 8,
        'lieu': 'Espace Culturel de Bouaké',
        'nb_participants_attendus': 500,
        'budget_prevu': 8000000,
        'est_public': True,
        'inscription_requise': False,
        'statut': 'planifie',
        'participants': [
            {'nom': 'Mme Ouattara Fatoumata', 'email': 'f.ouattara@rfdr.ci', 'org': 'RFDR'},
            {'nom': 'Mme N\'Goran Adjoua', 'email': 'a.ngoran@women-dev.ci', 'org': 'Association Femmes Développement'},
        ],
    },
    {
        'titre': 'Séminaire de Clôture du Projet AGRI-DEV – Résultats et Perspectives',
        'type_evenement': 'seminaire',
        'description': 'Séminaire officiel de clôture du Projet AGRI-DEV avec présentation des résultats, leçons apprises et perspectives pour la capitalisation. En présence des bailleurs et partenaires institutionnels.',
        'objectifs': '1. Restituer les résultats atteints sur toute la durée du projet\n2. Partager les leçons apprises\n3. Présenter le plan de capitalisation et de durabilité\n4. Valider les recommandations pour les projets futurs',
        'date_debut_delta': 45,
        'duree_heures': 6,
        'lieu': 'Hôtel Pullman Abidjan – Salle Panorama',
        'nb_participants_attendus': 120,
        'budget_prevu': 20000000,
        'est_public': False,
        'inscription_requise': True,
        'statut': 'planifie',
        'participants': [
            {'nom': 'M. Jean-Pierre Müller', 'email': 'jp.muller@eeas.eu', 'org': 'Délégation UE'},
            {'nom': 'Mme Sophie Leclerc', 'email': 's.leclerc@afd.fr', 'org': 'AFD'},
            {'nom': 'M. Mamadou Diallo', 'email': 'm.diallo@worldbank.org', 'org': 'Banque Mondiale'},
            {'nom': 'Mme Gloria Williams', 'email': 'g.williams@usaid.gov', 'org': 'USAID'},
        ],
    },
]


class Command(BaseCommand):
    help = 'Crée les données de démonstration pour le courrier administratif, les réunions et événements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime les données existantes avant de créer les nouvelles',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        with transaction.atomic():
            admin = self._get_admin()
            if not admin:
                self.stdout.write(self.style.ERROR('[ERREUR] Aucun administrateur trouve. Lancez d\'abord seed_lot1.'))
                return

            users = self._get_users()

            entrants   = self._seed_entrants(admin, users)
            sortants   = self._seed_sortants(admin, users)
            diligences = self._seed_diligences(admin, users, entrants)
            reunions   = self._seed_reunions(admin, users)
            evenements = self._seed_evenements(admin, users)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed termine avec succes !'))
        self.stdout.write(f'   - {len(entrants)} courriers entrants')
        self.stdout.write(f'   - {len(sortants)} courriers sortants')
        self.stdout.write(f'   - {len(diligences)} diligences')
        self.stdout.write(f'   - {len(reunions)} reunions')
        self.stdout.write(f'   - {len(evenements)} evenements')

    # -- Reset ----------------------------------------------------------------

    def _reset(self):
        from courrier_administratif.models import CourrierEntrant, CourrierSortant, Diligence
        from execution.models import Reunion, ParticipantReunion
        from collaboration.models import Evenement, ParticipantEvenement

        self.stdout.write(self.style.WARNING('[RESET] Suppression des donnees existantes...'))
        ParticipantReunion.objects.all().delete()
        Diligence.objects.all().delete()
        CourrierSortant.objects.all().delete()
        CourrierEntrant.objects.all().delete()
        ParticipantEvenement.objects.all().delete()
        Evenement.objects.all().delete()
        Reunion.objects.all().delete()
        self.stdout.write('   Donnees supprimees.')

    # -- Helpers --------------------------------------------------------------

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_users(self):
        from accounts.models import User
        users = list(User.objects.all()[:10])
        return users

    def _log(self, label, obj, created):
        status = self.style.SUCCESS('Cree') if created else self.style.WARNING('Existant')
        self.stdout.write(f'  [{status}] {label}: {obj}')

    # -- Courriers entrants ---------------------------------------------------

    def _seed_entrants(self, admin, users):
        from courrier_administratif.models import CourrierEntrant
        today = date.today()
        created_list = []

        self.stdout.write('\n>> Courriers entrants...')
        for i, data in enumerate(ENTRANTS):
            delta = -(len(ENTRANTS) - i) * 3
            date_reception = today + timedelta(days=delta)

            affecte_a = None
            if data['statut'] in ('affecte', 'en_cours', 'traite') and users:
                affecte_a = random.choice(users)

            obj, created = CourrierEntrant.objects.get_or_create(
                objet=data['objet'],
                defaults={
                    'expediteur': data['expediteur'],
                    'organisation_expediteur': data.get('organisation_expediteur', ''),
                    'email_expediteur': data.get('email_expediteur', ''),
                    'description': data.get('description', ''),
                    'urgence': data['urgence'],
                    'canal': data['canal'],
                    'statut': data['statut'],
                    'date_reception': date_reception,
                    'affecte_a': affecte_a,
                    'instruction_affectation': 'Traiter en priorité et préparer un projet de réponse.' if affecte_a else '',
                    'date_affectation': timezone.now() if affecte_a else None,
                    'enregistre_par': admin,
                }
            )
            self._log('Entrant', f'{obj.numero} – {obj.objet[:50]}…', created)
            created_list.append(obj)

        return created_list

    # -- Courriers sortants ---------------------------------------------------

    def _seed_sortants(self, admin, users):
        from courrier_administratif.models import CourrierSortant
        today = date.today()
        created_list = []

        self.stdout.write('\n>> Courriers sortants...')
        for i, data in enumerate(SORTANTS):
            delta = -(len(SORTANTS) - i) * 2
            date_courrier = today + timedelta(days=delta)

            redacteur = random.choice(users) if users else admin

            obj, created = CourrierSortant.objects.get_or_create(
                objet=data['objet'],
                defaults={
                    'type_courrier': data['type_courrier'],
                    'corps': data.get('corps', ''),
                    'destinataire': data['destinataire'],
                    'organisation_destinataire': data.get('organisation_destinataire', ''),
                    'email_destinataire': data.get('email_destinataire', ''),
                    'date_courrier': date_courrier,
                    'date_expedition': date_courrier + timedelta(days=1) if data['statut'] in ('expedie', 'archive') else None,
                    'statut': data['statut'],
                    'redacteur': redacteur,
                }
            )
            self._log('Sortant', f'{obj.reference} – {obj.objet[:50]}…', created)
            created_list.append(obj)

        return created_list

    # -- Diligences -----------------------------------------------------------

    def _seed_diligences(self, admin, users, entrants):
        from courrier_administratif.models import Diligence
        today = date.today()
        created_list = []

        self.stdout.write('\n>> Diligences...')
        for i, data in enumerate(DILIGENCES_DATA):
            echeance = today + timedelta(days=data.get('echeance_delta', 14))
            responsable = random.choice(users) if users else admin
            courrier = entrants[i % len(entrants)] if entrants and i < 6 else None

            obj, created = Diligence.objects.get_or_create(
                description=data['description'],
                defaults={
                    'courrier': courrier,
                    'type_diligence': data['type_diligence'],
                    'statut': data['statut'],
                    'echeance': echeance,
                    'resultat': data.get('resultat', ''),
                    'responsable': responsable,
                    'assigne_par': admin,
                }
            )
            self._log('Diligence', f'{obj.description[:60]}…', created)
            created_list.append(obj)

        return created_list

    # -- Réunions -------------------------------------------------------------

    def _seed_reunions(self, admin, users):
        from execution.models import Reunion, ParticipantReunion
        today = date.today()
        created_list = []

        self.stdout.write('\n>> Reunions...')
        for data in REUNIONS_DATA:
            date_reunion = today + timedelta(days=data['date_delta'])

            obj, created = Reunion.objects.get_or_create(
                objet=data['objet'],
                defaults={
                    'type_reunion': data['type_reunion'],
                    'description': data.get('description', ''),
                    'organisateur': admin,
                    'created_by': admin,
                    'date': date_reunion,
                    'heure_debut': data['heure_debut'],
                    'heure_fin': data.get('heure_fin'),
                    'lieu': data.get('lieu', ''),
                    'plateforme': data.get('plateforme', 'presentiel'),
                    'lien_visio': data.get('lien_visio', ''),
                    'statut': data['statut'],
                    'notes': '',
                }
            )
            self._log('Réunion', f'{obj.reference} – {obj.objet[:50]}…', created)
            created_list.append(obj)

            if not created:
                continue

            # Participants internes : admin + 1-2 users aléatoires
            internal_users = [admin] + random.sample(users, min(2, len(users)))
            for u in set(internal_users):
                ParticipantReunion.objects.get_or_create(
                    reunion=obj,
                    utilisateur=u,
                    defaults={
                        'type_participant': 'interne',
                        'statut_presence': random.choice(['invite', 'confirme', 'present']),
                        'date_invitation': timezone.now(),
                    }
                )

            # Participants externes
            for pe in data.get('participants_externes', []):
                ParticipantReunion.objects.get_or_create(
                    reunion=obj,
                    email_externe=pe['email'],
                    defaults={
                        'nom_externe': pe['nom'],
                        'organisation_externe': pe.get('org', ''),
                        'type_participant': 'partenaire',
                        'statut_presence': random.choice(['invite', 'confirme']),
                        'date_invitation': timezone.now(),
                    }
                )

        return created_list

    # -- Événements -----------------------------------------------------------

    def _seed_evenements(self, admin, users):
        from collaboration.models import Evenement, ParticipantEvenement
        now = timezone.now()
        created_list = []

        self.stdout.write('\n>> Evenements...')
        for data in EVENEMENTS_DATA:
            date_debut = now + timedelta(days=data['date_debut_delta'])
            date_fin   = date_debut + timedelta(hours=data['duree_heures'])

            obj, created = Evenement.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'type_evenement': data['type_evenement'],
                    'description': data.get('description', ''),
                    'objectifs': data.get('objectifs', ''),
                    'date_debut': date_debut,
                    'date_fin': date_fin,
                    'lieu': data.get('lieu', ''),
                    'nb_participants_attendus': data.get('nb_participants_attendus'),
                    'budget_prevu': data.get('budget_prevu', 0),
                    'est_public': data.get('est_public', False),
                    'inscription_requise': data.get('inscription_requise', True),
                    'statut': data['statut'],
                    'organisateur': admin,
                    'ordre_du_jour': '',
                    'compte_rendu': '',
                }
            )
            self._log('Événement', f'{obj.titre[:60]}…', created)
            created_list.append(obj)

            if not created:
                continue

            # Participants internes
            internal_users = random.sample(users, min(3, len(users)))
            for u in internal_users:
                ParticipantEvenement.objects.get_or_create(
                    evenement=obj,
                    utilisateur=u,
                    defaults={
                        'statut': random.choice(['inscrit', 'confirme']),
                    }
                )

            # Participants externes
            for pe in data.get('participants', []):
                try:
                    ParticipantEvenement.objects.get_or_create(
                        evenement=obj,
                        email=pe['email'],
                        defaults={
                            'nom_externe': pe['nom'],
                            'organisation': pe.get('org', ''),
                            'statut': 'inscrit',
                        }
                    )
                except Exception:
                    pass

        return created_list
