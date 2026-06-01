"""
Seed données de démonstration pour le Lot 7 :
  M26 : Collaboration — Groupes, Canaux, Messages, Notifications
  M27 : Courrier administratif — Circuits de validation, Parapheurs, Modèles
  M28 : Courrier intelligent — Comptes email, Signatures, Templates, Règles, Emails

Usage : python manage.py seed_lot7 [--reset]
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# -- M26 : Collaboration -------------------------------------------------------

GROUPES_TRAVAIL = [
    {
        'nom': 'Coordination Santé – PRCC',
        'type_groupe': 'projet',
        'description': 'Groupe de coordination de la composante santé du programme PRCC. Regroupe les équipes terrain, les superviseurs et la coordination nationale.',
    },
    {
        'nom': 'Gestion Financière & Budget',
        'type_groupe': 'transversal',
        'description': 'Groupe dédié au suivi financier, aux validations budgétaires et à la gestion des dépenses du programme.',
    },
    {
        'nom': 'Équipe AGR & Coopératives',
        'type_groupe': 'projet',
        'description': 'Groupe de travail pour la composante AGR : structuration des coopératives, formation entrepreneuriat, suivi des bénéficiaires.',
    },
    {
        'nom': 'Équipe terrain – Districts Nord',
        'type_groupe': 'terrain',
        'description': 'Coordination opérationnelle des agents terrain déployés dans les districts du Nord : Korhogo, Boundiali, Ferkessédougou.',
    },
    {
        'nom': 'Comité Directeur PRCC',
        'type_groupe': 'comite',
        'description': 'Comité directeur stratégique du programme. Comprend le DG, les responsables de composantes et les représentants des bailleurs.',
    },
]

CANAUX = [
    {
        'nom': 'Général – PRCC',
        'type_canal': 'general',
        'description': 'Canal officiel du programme PRCC. Annonces, informations générales et communications officielles.',
        'est_prive': False,
        'messages': [
            'Bienvenue sur la plateforme collaborative du Programme PRCC ! Ce canal est réservé aux annonces officielles.',
            'Rappel : le rapport trimestriel Q1 doit être soumis avant le 15 juin 2026. Merci de coordonner avec vos équipes.',
            'La revue à mi-parcours avec la Banque Mondiale est confirmée pour le 20 juin 2026. Préparez vos tableaux de bord.',
            'Félicitations à l\'équipe santé pour avoir atteint la cible de 210 agents formés en mai 2026 !',
        ],
    },
    {
        'nom': 'Composante Santé',
        'type_canal': 'projet',
        'description': 'Coordination de la composante santé : formations ASC, campagnes vaccination, suivi nutritionnel.',
        'est_prive': False,
        'messages': [
            'Session 2 de formation (Districts Adjamé & Yopougon) confirmée pour le 15 juin. 38 agents attendus.',
            'Résultats Session 1 : 85/85 agents formés, score moyen évaluation : 78/100. Excellent résultat !',
            'Problème signalé : 3 tablettes KoboCollect défectueuses au District de Cocody. Contacter la logistique.',
            'La chaîne du froid pour la campagne vaccination est opérationnelle dans 42 des 45 villages. 3 restants en cours.',
        ],
    },
    {
        'nom': 'Finances & Budget',
        'type_canal': 'projet',
        'description': 'Suivi budgétaire, validation des dépenses et coordination financière du programme.',
        'est_prive': True,
        'messages': [
            'Taux d\'exécution budgétaire global S1 : 58.3% (cible : 60%). Légèrement en dessous — actions correctives en cours.',
            'La tranche UE Q2 (562.5M FCFA) n\'a pas encore été reçue. Relance envoyée le 28 mai. Délai prévu : 15 juin.',
            'Audit financier S1 programmé du 25 juin au 5 juillet. Préparer les justificatifs des 8 dépenses > 5M FCFA.',
        ],
    },
    {
        'nom': 'Terrain & Opérations',
        'type_canal': 'terrain',
        'description': 'Canal des équipes terrain. Rapports quotidiens, incidents, besoins logistiques.',
        'est_prive': False,
        'messages': [
            'Rapport terrain du 30/05 : 12 visites domiciliaires réalisées à Abobo-Baoulé. 3 cas malnutrition référés.',
            'Panne véhicule Toyota HZJ sur l\'axe Bouaké-Brobo. Agent Coulibaly en attente de secours. Logistique informée.',
            'Collecte données terminée — 87 ménages enquêtés ce jour dans le village de Kpata. Synchronisation OK.',
            'Alerte : pluies fortes prévues demain dans la région de Man. Reporters les visites des villages enclavés.',
        ],
    },
    {
        'nom': 'Direction & Stratégie',
        'type_canal': 'direction',
        'description': 'Canal de communication de la Direction Générale. Orientations stratégiques et décisions.',
        'est_prive': True,
        'messages': [
            'Réunion stratégique semestrielle fixée au 10 juin 2026, 09h00. Ordre du jour partagé sur GED.',
            'Note de la DG : en raison des bons résultats de la composante santé, nous proposons de réallouer 15M FCFA vers la composante AGR en retard.',
        ],
    },
]

NOTIFICATIONS_DATA = [
    {
        'titre': 'Rapport trimestriel Q1 à valider',
        'message': 'Le rapport d\'avancement Q1 2026 vous a été soumis pour validation. Délai : 3 jours.',
        'type_notification': 'validation',
        'priorite': 'haute',
        'lien': '/rapports/se/1/',
    },
    {
        'titre': 'Alerte indicateur — Taux vaccination DTP3',
        'message': 'L\'indicateur IND-RES-002 est en dessous de sa cible semestrielle : 68.5% vs 75% attendu.',
        'type_notification': 'alerte',
        'priorite': 'critique',
        'lien': '/se/indicateurs/IND-RES-002/',
    },
    {
        'titre': 'Dépense en attente d\'approbation',
        'message': 'La dépense "Lot équipements médicaux — Centres de santé Abobo" (38.7M FCFA) est en attente de votre approbation.',
        'type_notification': 'action_requise',
        'priorite': 'haute',
        'lien': '/finances/depenses/4/',
    },
    {
        'titre': 'Nouveau document partagé',
        'message': 'Aminata Traoré a partagé "TDR Campagne Vaccination DTP3 — Juin 2026" avec votre groupe.',
        'type_notification': 'info',
        'priorite': 'normale',
        'lien': '/ged/documents/5/',
    },
    {
        'titre': 'Mission terrain approuvée',
        'message': 'Votre ordre de mission pour les districts Adjamé & Yopougon (03-07 juin) a été approuvé.',
        'type_notification': 'info',
        'priorite': 'normale',
        'lien': '/execution/missions/3/',
    },
    {
        'titre': 'Réunion COPIL dans 3 jours',
        'message': 'Rappel : Comité de Pilotage trimestriel prévu le 10 juin 2026 à 09h00. Ordre du jour disponible.',
        'type_notification': 'rappel',
        'priorite': 'haute',
        'lien': '/execution/reunions/',
    },
    {
        'titre': 'Tranche de financement reçue',
        'message': 'La tranche AFD (425M FCFA) a été reçue sur le compte du programme. Mise à jour de la trésorerie effectuée.',
        'type_notification': 'info',
        'priorite': 'normale',
        'lien': '/finances/conventions/2/',
    },
    {
        'titre': 'Formulaire terrain synchronisé',
        'message': '87 nouvelles soumissions KoboCollect reçues depuis les agents terrain du District de Kpata.',
        'type_notification': 'info',
        'priorite': 'basse',
        'lien': '/se/formulaires/1/',
    },
]


# -- M27 : Courrier administratif — Circuits & Parapheurs ----------------------

CIRCUITS_VALIDATION = [
    {
        'nom': 'Circuit d\'approbation Direction Générale',
        'description': 'Circuit standard de validation des documents officiels nécessitant l\'approbation de la Direction Générale. Utilisé pour les rapports externes, conventions et engagements financiers importants.',
        'etapes': [
            {'ordre': 1, 'nom_etape': 'Validation Coordination Projet',  'obligatoire': True,  'delai': 2, 'role_code': 'chef_projet'},
            {'ordre': 2, 'nom_etape': 'Contrôle Financier',              'obligatoire': True,  'delai': 2, 'role_code': 'controleur_financier'},
            {'ordre': 3, 'nom_etape': 'Approbation Direction Générale',   'obligatoire': True,  'delai': 1, 'role_code': 'direction_generale'},
        ],
    },
    {
        'nom': 'Circuit de validation financière',
        'description': 'Circuit de validation des dépenses et engagements financiers. Obligatoire pour toute dépense > 500 000 FCFA.',
        'etapes': [
            {'ordre': 1, 'nom_etape': 'Vérification Responsable Activité', 'obligatoire': True,  'delai': 1, 'role_code': 'chef_projet'},
            {'ordre': 2, 'nom_etape': 'Approbation Contrôle Financier',    'obligatoire': True,  'delai': 2, 'role_code': 'controleur_financier'},
            {'ordre': 3, 'nom_etape': 'Autorisation DG (> 5M FCFA)',       'obligatoire': False, 'delai': 1, 'role_code': 'direction_generale'},
        ],
    },
    {
        'nom': 'Circuit publication GED',
        'description': 'Circuit de validation pour la publication officielle des documents dans la GED. Documents techniques et rapports.',
        'etapes': [
            {'ordre': 1, 'nom_etape': 'Révision technique',             'obligatoire': True,  'delai': 3, 'role_code': 'chef_projet'},
            {'ordre': 2, 'nom_etape': 'Validation Gestionnaire GED',   'obligatoire': True,  'delai': 1, 'role_code': 'gestionnaire_ged'},
        ],
    },
    {
        'nom': 'Circuit courrier officiel sortant',
        'description': 'Circuit pour les courriers officiels adressés aux autorités et bailleurs. Signature obligatoire DG.',
        'etapes': [
            {'ordre': 1, 'nom_etape': 'Rédaction et révision',        'obligatoire': True,  'delai': 2, 'role_code': 'chef_projet'},
            {'ordre': 2, 'nom_etape': 'Visa Responsable S&E',         'obligatoire': False, 'delai': 1, 'role_code': 'responsable_se'},
            {'ordre': 3, 'nom_etape': 'Signature Direction Générale', 'obligatoire': True,  'delai': 1, 'role_code': 'direction_generale'},
        ],
    },
]

MODELES_COURRIER = [
    {
        'nom': 'Lettre de demande de fonds',
        'type_courrier': 'sortant',
        'description': 'Modèle de lettre pour les demandes de décaissement auprès des bailleurs de fonds.',
        'objet': 'Demande de décaissement — [NOM_PROGRAMME] — Tranche [N°]',
        'corps': """Monsieur/Madame le/la [TITRE],

Je vous adresse la présente lettre pour solliciter le décaissement de la tranche [N°] de notre convention de financement n° [REF_CONVENTION] relative au [NOM_PROGRAMME].

Conformément aux termes de ladite convention, nous avons l'honneur de vous soumettre :
- Le rapport d'avancement de la période [PERIODE]
- L'état des dépenses certifié
- Les justificatifs comptables

Taux d'exécution physique : [TAUX_PHYSIQUE]%
Taux d'exécution financière : [TAUX_FINANCIER]%

Dans l'attente de votre réponse favorable, nous vous prions d'agréer, Monsieur/Madame, l'expression de notre haute considération.

[SIGNATURE_DG]""",
    },
    {
        'nom': 'Note de service interne',
        'type_courrier': 'interne',
        'description': 'Modèle de note de service pour les communications officielles internes.',
        'objet': 'Note de service n° [NS-XXXX] — [OBJET]',
        'corps': """NOTE DE SERVICE N° [NS-XXXX]

À : [DESTINATAIRES]
De : Direction Générale / [DIRECTION_EMETTRICE]
Date : [DATE]
Objet : [OBJET_DETAILLE]

[CORPS_MESSAGE]

La présente note prend effet à compter de sa date de signature.

[SIGNATAIRE]""",
    },
    {
        'nom': 'Lettre d\'invitation à réunion',
        'type_courrier': 'sortant',
        'description': 'Convocation officielle pour les comités de pilotage et réunions techniques.',
        'objet': 'Convocation — [TYPE_REUNION] du [DATE_REUNION]',
        'corps': """Monsieur/Madame,

J'ai l'honneur de vous convier à la réunion [TYPE_REUNION] du [NOM_PROGRAMME] qui se tiendra :

📅 Date : [DATE_REUNION]
⏰ Heure : [HEURE_DEBUT]
📍 Lieu : [LIEU]

Ordre du jour :
[ORDRE_DU_JOUR]

Merci de confirmer votre présence avant le [DATE_CONFIRMATION].

[SIGNATAIRE]""",
    },
    {
        'nom': 'Accusé de réception',
        'type_courrier': 'sortant',
        'description': 'Accusé de réception standard pour les courriers officiels reçus.',
        'objet': 'Accusé de réception — Votre courrier du [DATE_COURRIER] — [REFERENCE]',
        'corps': """Monsieur/Madame,

Nous accusons réception de votre correspondance référencée [REFERENCE] en date du [DATE_COURRIER], relative à [OBJET_COURRIER].

Ce courrier a été enregistré sous la référence [REF_INTERNE] et transmis à [SERVICE_COMPETENT] pour traitement dans les meilleurs délais.

[SIGNATAIRE]""",
    },
]

PARAPHEURS_DATA = [
    {
        'reference': 'PAR-2026-001',
        'intitule': 'Rapport financier S1 2026 — Pour approbation DG',
        'statut': 'en_circuit',
        'etape_courante': 2,
        'circuit_idx': 0,
        'notes': 'Rapport semestriel obligatoire pour la convention UE. Délai de soumission : 30 juin 2026.',
    },
    {
        'reference': 'PAR-2026-002',
        'intitule': 'Convention partenariat Mairie de Korhogo — Signature DG',
        'statut': 'en_circuit',
        'etape_courante': 3,
        'circuit_idx': 3,
        'notes': 'Convention de partenariat pour faciliter les activités terrain dans la région de Korhogo.',
    },
    {
        'reference': 'PAR-2026-003',
        'intitule': 'TDR Audit financier intermédiaire — Validation',
        'statut': 'cloture',
        'etape_courante': None,
        'circuit_idx': 2,
        'notes': 'TDR validé et envoyé au cabinet d\'audit le 15 mai 2026.',
    },
]


# -- M28 : Courrier intelligent ------------------------------------------------

COMPTES_EMAIL = [
    {
        'nom_affichage': 'PRCC — Coordination Générale',
        'adresse_email': 'coordination@prcc-ong.ci',
        'type_compte': 'imap',
        'serveur_entrant': 'mail.prcc-ong.ci',
        'port_entrant': 993,
        'serveur_sortant': 'smtp.prcc-ong.ci',
        'port_sortant': 587,
        'ssl_entrant': True,
        'ssl_sortant': True,
        'identifiant': 'coordination@prcc-ong.ci',
        'mot_de_passe': 'encrypted_demo_pass',
        'statut': 'connecte',
        'est_principal': True,
    },
    {
        'nom_affichage': 'PRCC — Direction Financière',
        'adresse_email': 'finances@prcc-ong.ci',
        'type_compte': 'imap',
        'serveur_entrant': 'mail.prcc-ong.ci',
        'port_entrant': 993,
        'serveur_sortant': 'smtp.prcc-ong.ci',
        'port_sortant': 587,
        'ssl_entrant': True,
        'ssl_sortant': True,
        'identifiant': 'finances@prcc-ong.ci',
        'mot_de_passe': 'encrypted_demo_pass',
        'statut': 'connecte',
        'est_principal': False,
    },
]

TEMPLATES_REPONSE = [
    {
        'titre': 'Accusé réception — Rapport bailleur',
        'type_template': 'accusé_réception',
        'sujet_template': 'Re: {sujet_original} — Accusé de réception',
        'corps_html': '<p>Madame, Monsieur,</p><p>Nous accusons réception de votre message du {date_reception} concernant {objet}. Votre demande a été transmise à la personne compétente et vous recevrez une réponse dans un délai de <strong>{delai}</strong>.</p><p>Cordialement,<br>{signature}</p>',
        'corps_texte': 'Nous accusons réception de votre message du {date_reception} concernant {objet}. Une réponse vous sera apportée dans {delai}.',
        'variables': ['sujet_original', 'date_reception', 'objet', 'delai', 'signature'],
    },
    {
        'titre': 'Réponse demande de rapport',
        'type_template': 'rapport',
        'sujet_template': 'Transmission rapport {type_rapport} — {programme} — {periode}',
        'corps_html': '<p>Monsieur/Madame,</p><p>Suite à votre demande, nous avons l\'honneur de vous transmettre le <strong>{type_rapport}</strong> du programme <strong>{programme}</strong> pour la période <strong>{periode}</strong>.</p><p>Ce rapport a été préparé conformément aux exigences de la convention de financement n° {ref_convention}.</p><p>Nous restons disponibles pour tout éclaircissement.</p><p>Cordialement,<br>{signature}</p>',
        'corps_texte': 'Veuillez trouver ci-joint le {type_rapport} du programme {programme} pour la période {periode}.',
        'variables': ['type_rapport', 'programme', 'periode', 'ref_convention', 'signature'],
    },
    {
        'titre': 'Convocation réunion',
        'type_template': 'convocation',
        'sujet_template': 'Convocation — {type_reunion} — {date_reunion}',
        'corps_html': '<p>Madame, Monsieur,</p><p>J\'ai l\'honneur de vous convier à la réunion <strong>{type_reunion}</strong> qui se tiendra :</p><ul><li>📅 <strong>Date</strong> : {date_reunion}</li><li>⏰ <strong>Heure</strong> : {heure_debut}</li><li>📍 <strong>Lieu</strong> : {lieu}</li></ul><p>Merci de confirmer votre présence avant le {date_confirmation}.</p><p>Cordialement,<br>{signature}</p>',
        'corps_texte': 'Convocation à la réunion {type_reunion} du {date_reunion} à {heure_debut} au {lieu}.',
        'variables': ['type_reunion', 'date_reunion', 'heure_debut', 'lieu', 'date_confirmation', 'signature'],
    },
    {
        'titre': 'Réponse demande de partenariat',
        'type_template': 'partenariat',
        'sujet_template': 'Re: Demande de partenariat — {nom_organisation}',
        'corps_html': '<p>Madame, Monsieur,</p><p>Nous avons bien reçu votre demande de partenariat datée du {date_demande} et nous vous remercions de l\'intérêt que vous portez à notre programme <strong>{nom_programme}</strong>.</p><p>Après examen de votre proposition, nous sommes {decision} d\'envisager une collaboration avec votre organisation.</p><p>{message_complementaire}</p><p>Cordialement,<br>{signature}</p>',
        'corps_texte': 'Suite à votre demande de partenariat, nous vous informons que nous sommes {decision} d\'envisager une collaboration.',
        'variables': ['nom_organisation', 'date_demande', 'nom_programme', 'decision', 'message_complementaire', 'signature'],
    },
]

REGLES_CLASSIFICATION = [
    {
        'nom': 'Urgence bailleur',
        'description': 'Classe comme urgent tout email provenant de bailleurs (UE, AFD, BM, USAID) contenant les mots "urgent", "deadline" ou "délai".',
        'priorite': 1,
        'operateur': 'ET',
        'conditions': [
            {'champ': 'expediteur_email', 'operateur': 'contient_un_de', 'valeur': ['@eeas.europa.eu', '@afd.fr', '@worldbank.org', '@usaid.gov']},
            {'champ': 'sujet', 'operateur': 'contient_un_de', 'valeur': ['urgent', 'deadline', 'délai', 'échéance']},
        ],
        'action': 'marquer_urgent',
        'parametres_action': {'priorite': 'tres_urgent', 'etiquette': 'Bailleur-Urgent', 'notifier': True},
    },
    {
        'nom': 'Classement rapports financiers',
        'description': 'Archive automatiquement les rapports financiers reçus dans le dossier GED "Finances 2026".',
        'priorite': 2,
        'operateur': 'OU',
        'conditions': [
            {'champ': 'sujet', 'operateur': 'contient_un_de', 'valeur': ['rapport financier', 'état des dépenses', 'budget', 'trésorerie']},
            {'champ': 'sujet', 'operateur': 'contient', 'valeur': 'facture'},
        ],
        'action': 'archiver_ged',
        'parametres_action': {'categorie_ged': 'CAT-FIN', 'dossier': 'Finances 2026'},
    },
    {
        'nom': 'Auto-réponse hors bureau',
        'description': 'Envoie un accusé de réception automatique à tout email reçu sur le compte principal pendant les absences.',
        'priorite': 3,
        'operateur': 'ET',
        'conditions': [
            {'champ': 'direction', 'operateur': 'egal', 'valeur': 'entrant'},
            {'champ': 'expediteur_email', 'operateur': 'ne_contient_pas', 'valeur': '@prcc-ong.ci'},
        ],
        'action': 'envoyer_template',
        'parametres_action': {'template': 'Accusé réception — Rapport bailleur', 'actif': False},
    },
    {
        'nom': 'Signalement spam/démarchage',
        'description': 'Identifie et filtre les emails de démarchage commercial non sollicités.',
        'priorite': 10,
        'operateur': 'OU',
        'conditions': [
            {'champ': 'sujet', 'operateur': 'contient_un_de', 'valeur': ['promotion', 'offre spéciale', 'ne manquez pas', 'abonnez-vous', 'newsletter']},
            {'champ': 'corps_texte', 'operateur': 'contient', 'valeur': 'désabonner'},
        ],
        'action': 'marquer_spam',
        'parametres_action': {'etiquette': 'Spam'},
    },
]

ETIQUETTES_EMAIL = [
    {'nom': 'Bailleur-UE',       'couleur': '#1a56db'},
    {'nom': 'Bailleur-AFD',      'couleur': '#0e9f6e'},
    {'nom': 'Bailleur-BM',       'couleur': '#d03801'},
    {'nom': 'Bailleur-Urgent',   'couleur': '#e02424'},
    {'nom': 'Rapport',           'couleur': '#7e3af2'},
    {'nom': 'Finances',          'couleur': '#057a55'},
    {'nom': 'Partenaire',        'couleur': '#f59e0b'},
    {'nom': 'Terrain',           'couleur': '#10b981'},
    {'nom': 'Spam',              'couleur': '#9ca3af'},
    {'nom': 'À-suivre',          'couleur': '#f97316'},
]

EMAILS_DATA = [
    {
        'direction': 'entrant',
        'sujet': 'Demande de rapport d\'avancement Q1 2026 — Convention UE n° CI-2024-001',
        'expediteur': 'Section Coopération — Délégation UE',
        'expediteur_email': 'delegation.abidjan@eeas.europa.eu',
        'destinataires': ['coordination@prcc-ong.ci'],
        'corps_texte': 'Conformément à l\'article 12 de la convention de financement, nous sollicitons la transmission du rapport d\'avancement Q1 2026 avant le 30 mai 2026. Merci de nous confirmer la date de transmission.',
        'corps_html': '<p>Madame, Monsieur,</p><p>Conformément à l\'article 12 de la convention de financement n° CI-2024-001, nous sollicitons la transmission du rapport d\'avancement du premier trimestre 2026 <strong>avant le 30 mai 2026</strong>.</p><p>Merci de confirmer la date de transmission.</p><p>Cordialement,<br>Section Coopération — Délégation UE</p>',
        'priorite': 'haute',
        'statut': 'lu',
        'est_lu': True,
        'delta': -15,
        'etiquettes': ['Bailleur-UE', 'Rapport', 'À-suivre'],
        'resume_ia': 'Demande urgente de rapport Q1 2026 par la délégation UE. Délai : 30 mai 2026. Action requise : préparer et envoyer le rapport.',
        'score_urgence': 82,
        'suggestion_reponse_ia': 'Envoyer accusé de réception et confirmer la date de transmission du rapport. Utiliser le template "Réponse demande de rapport".',
    },
    {
        'direction': 'entrant',
        'sujet': 'Mission de supervision BM — Documents préparatoires',
        'expediteur': 'Banque Mondiale — Bureau Abidjan',
        'expediteur_email': 'bm.abidjan@worldbank.org',
        'destinataires': ['coordination@prcc-ong.ci'],
        'corps_texte': 'Dans le cadre de la mission de supervision prévue du 10 au 20 juin 2026, nous vous prions de préparer les documents suivants : 1) Rapport financier à jour, 2) Tableaux de suivi des indicateurs, 3) Registre des risques actualisé.',
        'corps_html': '<p>Dans le cadre de la mission de supervision prévue du <strong>10 au 20 juin 2026</strong>, nous vous prions de préparer :<br><ol><li>Rapport financier à jour</li><li>Tableaux de suivi des indicateurs</li><li>Registre des risques actualisé</li></ol></p>',
        'priorite': 'haute',
        'statut': 'lu',
        'est_lu': True,
        'delta': -8,
        'etiquettes': ['Bailleur-BM', 'Rapport'],
        'resume_ia': 'La Banque Mondiale demande des documents préparatoires pour la mission de supervision du 10-20 juin.',
        'score_urgence': 75,
        'suggestion_reponse_ia': 'Accuser réception et envoyer la liste des documents à préparer à l\'équipe. Deadline : 7 juin.',
    },
    {
        'direction': 'entrant',
        'sujet': 'Demande de partenariat — Programme Nutrition Infantile',
        'expediteur': 'ONG Solidarité Sahel',
        'expediteur_email': 'partenariat@solidarite-sahel.org',
        'destinataires': ['coordination@prcc-ong.ci'],
        'corps_texte': 'Notre organisation souhaite explorer les possibilités de collaboration avec votre programme PRCC sur la composante nutrition. Nous intervenons dans 3 régions du Nord et avons des synergies potentielles avec vos activités.',
        'corps_html': '<p>Notre organisation souhaite explorer les possibilités de collaboration sur la composante nutrition. Nous intervenons dans 3 régions du Nord et voyons des synergies potentielles.</p>',
        'priorite': 'normale',
        'statut': 'non_lu',
        'est_lu': False,
        'delta': -3,
        'etiquettes': ['Partenaire'],
        'resume_ia': 'Demande de partenariat d\'une ONG active dans le Nord. Synergie potentielle sur la composante nutrition.',
        'score_urgence': 35,
        'suggestion_reponse_ia': 'Utiliser le template "Réponse demande de partenariat" pour accuser réception et planifier une réunion exploratoire.',
    },
    {
        'direction': 'sortant',
        'sujet': 'Transmission rapport d\'avancement Q1 2026 — Convention UE n° CI-2024-001',
        'expediteur': 'PRCC — Coordination Générale',
        'expediteur_email': 'coordination@prcc-ong.ci',
        'destinataires': ['delegation.abidjan@eeas.europa.eu'],
        'destinataires_cc': ['finances@prcc-ong.ci'],
        'corps_texte': 'Madame, Monsieur, Suite à votre demande du 16 mai, nous avons l\'honneur de vous transmettre le rapport d\'avancement Q1 2026 du Programme PRCC. Taux d\'exécution physique : 62%. Taux d\'exécution financière : 58.3%. Le rapport est joint en pièce jointe.',
        'corps_html': '<p>Madame, Monsieur,</p><p>Suite à votre demande du 16 mai, nous avons l\'honneur de vous transmettre le rapport d\'avancement Q1 2026 du Programme PRCC :</p><ul><li>Taux d\'exécution physique : <strong>62%</strong></li><li>Taux d\'exécution financière : <strong>58.3%</strong></li></ul><p>Veuillez trouver le rapport complet en pièce jointe.</p>',
        'priorite': 'haute',
        'statut': 'envoye',
        'est_lu': True,
        'delta': -12,
        'etiquettes': ['Bailleur-UE', 'Rapport'],
        'resume_ia': 'Envoi du rapport Q1 2026 à la délégation UE. Document soumis dans les délais.',
        'score_urgence': 60,
    },
    {
        'direction': 'entrant',
        'sujet': 'Notification décaissement — Tranche 2 Convention AFD',
        'expediteur': 'AFD — Direction des Opérations',
        'expediteur_email': 'operations.abidjan@afd.fr',
        'destinataires': ['coordination@prcc-ong.ci', 'finances@prcc-ong.ci'],
        'corps_texte': 'Nous vous informons que le décaissement de la 2ème tranche de votre convention AFD (425 000 000 FCFA) a été effectué ce jour. Les fonds ont été virés sur votre compte SGBCI n° CI-PRCC-2024.',
        'corps_html': '<p>Nous vous informons que le décaissement de la <strong>2ème tranche</strong> de votre convention AFD (<strong>425 000 000 FCFA</strong>) a été effectué ce jour.</p>',
        'priorite': 'haute',
        'statut': 'lu',
        'est_lu': True,
        'delta': -20,
        'etiquettes': ['Bailleur-AFD', 'Finances'],
        'resume_ia': 'Confirmation de réception de la tranche 2 AFD (425M FCFA). Mettre à jour la trésorerie et aviser le contrôleur financier.',
        'score_urgence': 65,
        'suggestion_reponse_ia': 'Envoyer accusé de réception à l\'AFD. Mettre à jour le plan de trésorerie. Notifier l\'équipe finances.',
    },
    {
        'direction': 'sortant',
        'sujet': 'Convocation — Comité de Pilotage PRCC — 10 juin 2026',
        'expediteur': 'PRCC — Direction Générale',
        'expediteur_email': 'coordination@prcc-ong.ci',
        'destinataires': ['delegation.abidjan@eeas.europa.eu', 'operations.abidjan@afd.fr', 'bm.abidjan@worldbank.org'],
        'corps_texte': 'Nous avons l\'honneur de vous convier au Comité de Pilotage du Programme PRCC qui se tiendra le 10 juin 2026 à 09h00 au Siège du PRCC, Plateau Abidjan. Ordre du jour : bilan S1, révision des cibles, orientations S2.',
        'corps_html': '<p>Nous vous convions au <strong>Comité de Pilotage du Programme PRCC</strong> :<br>📅 10 juin 2026 | ⏰ 09h00 | 📍 Siège PRCC, Plateau Abidjan</p>',
        'priorite': 'normale',
        'statut': 'envoye',
        'est_lu': True,
        'delta': -5,
        'etiquettes': ['Bailleur-UE', 'Bailleur-AFD', 'Bailleur-BM'],
        'resume_ia': 'Convocations envoyées aux 3 bailleurs pour le COPIL du 10 juin 2026.',
        'score_urgence': 55,
    },
]


# ==============================================================================

class Command(BaseCommand):
    help = 'Seed Lot 7 — Collaboration (M26), Courrier admin (M27), Courrier intelligent (M28)'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Supprime les données Lot 7 avant de re-seeder')

    def handle(self, *args, **options):
        admin = self._get_admin()
        if not admin:
            self.stdout.write(self.style.ERROR('[ERREUR] Aucun admin. Lancez seed_lot1 d\'abord.'))
            return

        users = self._get_users()
        projet = self._get_projet()
        programme = self._get_programme()

        self.stdout.write(f'[INFO] Admin : {admin.email} | Utilisateurs : {len(users)} | Projet : {projet.code if projet else "—"}')

        if options['reset']:
            self._reset()

        try:
            with transaction.atomic():
                # M26 — Collaboration
                groupes  = self._seed_groupes(admin, users, projet, programme)
                canaux   = self._seed_canaux(admin, users, projet, programme)
                self._seed_notifications(admin, users)

                # M27 — Courrier administratif
                circuits = self._seed_circuits(users)
                self._seed_parapheurs(admin, circuits, projet)
                self._seed_modeles_courrier(admin)

                # M28 — Courrier intelligent
                comptes  = self._seed_comptes_email(admin)
                self._seed_templates_reponse(admin)
                self._seed_regles_classification(admin, comptes)
                etiquettes = self._seed_etiquettes(admin)
                self._seed_emails(admin, projet, comptes, etiquettes)

        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'[ERREUR] : {exc}'))
            import traceback; traceback.print_exc()
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Seed Lot 7 terminé !'))

    # -- Helpers ---------------------------------------------------------------

    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _get_users(self):
        from accounts.models import User
        return list(User.objects.all()[:12])

    def _get_projet(self):
        from programmes_projets.models import Projet
        return Projet.objects.filter(statut='en_cours').first()

    def _get_programme(self):
        from programmes_projets.models import Programme
        return Programme.objects.first()

    def _pick_user(self, users, idx=0):
        return users[idx % len(users)] if users else None

    def _log(self, label, obj, created):
        s = self.style.SUCCESS('Créé') if created else self.style.WARNING('Existe')
        self.stdout.write(f'  [{s}] {label}: {str(obj)[:75]}')

    def _reset(self):
        from collaboration.models import Canal, GroupeTravail, Notification
        from courrier_administratif.models import CircuitValidation, Parapheur, ModeleCourrierSortant
        from courrier_intelligent.models import CompteEmail, TemplateReponse, RegleClassification, EtiquetteEmail, Email
        self.stdout.write(self.style.WARNING('[RESET] Suppression données Lot 7…'))
        for M in [Email, EtiquetteEmail, RegleClassification, TemplateReponse, CompteEmail,
                  ModeleCourrierSortant, Parapheur, CircuitValidation,
                  Notification, Canal, GroupeTravail]:
            n, _ = M.objects.all().delete()
            self.stdout.write(f'   {M.__name__}: {n} supprimé(s)')

    # -- M26 : Collaboration ---------------------------------------------------

    def _seed_groupes(self, admin, users, projet, programme):
        from collaboration.models import GroupeTravail
        self.stdout.write('\n>> Groupes de travail (M26)…')
        result = []
        for i, data in enumerate(GROUPES_TRAVAIL):
            gt, created = GroupeTravail.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'type_groupe': data['type_groupe'],
                    'description': data['description'],
                    'projet': projet,
                    'programme': programme,
                    'actif': True,
                    'cree_par': admin,
                }
            )
            self._log('Groupe', gt, created)
            if created:
                membres = users[: min(4, len(users))]
                gt.membres.set(membres)
            result.append(gt)
        return result

    def _seed_canaux(self, admin, users, projet, programme):
        from collaboration.models import Canal, MembreCanal, Message
        self.stdout.write('\n>> Canaux & Messages (M26)…')
        result = []
        for i, data in enumerate(CANAUX):
            canal, created = Canal.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'type_canal': data['type_canal'],
                    'description': data['description'],
                    'projet': projet,
                    'programme': programme,
                    'est_prive': data['est_prive'],
                    'cree_par': admin,
                }
            )
            self._log('Canal', canal, created)

            if created:
                # Membres du canal
                membres = users if not data['est_prive'] else users[:3]
                for user in membres:
                    MembreCanal.objects.get_or_create(canal=canal, utilisateur=user)

                # Messages
                for j, texte in enumerate(data.get('messages', [])):
                    auteur = self._pick_user(users, j)
                    Message.objects.create(
                        canal=canal,
                        auteur=auteur,
                        type_message='texte',
                        contenu=texte,
                    )
                    self.stdout.write(f'    + Message: {texte[:60]}…')

            result.append(canal)
        return result

    def _seed_notifications(self, admin, users):
        from collaboration.models import Notification
        self.stdout.write('\n>> Notifications (M26)…')
        for i, data in enumerate(NOTIFICATIONS_DATA):
            dest = self._pick_user(users, i)
            if not dest:
                continue
            notif, created = Notification.objects.get_or_create(
                titre=data['titre'],
                destinataire=dest,
                defaults={
                    'type_notification': data['type_notification'],
                    'message': data['message'],
                    'priorite': data['priorite'],
                    'lien': data.get('lien', ''),
                    'lue': (i % 3 == 0),
                    'envoyee': True,
                    'date_envoi': timezone.now(),
                    'cree_par': admin,
                }
            )
            self._log('Notification', notif, created)

    # -- M27 : Courrier administratif ------------------------------------------

    def _seed_circuits(self, users):
        from accounts.models import Role
        from courrier_administratif.models import CircuitValidation, EtapeCircuit
        self.stdout.write('\n>> Circuits de validation (M27)…')
        result = []

        # Mapping rôle → utilisateur disponible
        role_user_map = {}
        for user in users:
            for role in user.roles.all():
                if role.code not in role_user_map:
                    role_user_map[role.code] = user

        for data in CIRCUITS_VALIDATION:
            circ, created = CircuitValidation.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'description': data['description'],
                    'est_actif': True,
                }
            )
            self._log('Circuit', circ, created)

            if created:
                try:
                    role_dg = Role.objects.filter(code='direction_generale').first()
                    for etape in data['etapes']:
                        role = Role.objects.filter(code=etape['role_code']).first()
                        validateur = role_user_map.get(etape['role_code'])
                        EtapeCircuit.objects.create(
                            circuit=circ,
                            ordre=etape['ordre'],
                            nom_etape=etape['nom_etape'],
                            validateur=validateur,
                            role=role,
                            obligatoire=etape['obligatoire'],
                            delai_jours=etape['delai'],
                        )
                        self.stdout.write(f'    + Étape {etape["ordre"]}: {etape["nom_etape"]}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'    [WARN] Étapes : {e}'))

            result.append(circ)
        return result

    def _seed_parapheurs(self, admin, circuits, projet):
        from courrier_administratif.models import Parapheur
        self.stdout.write('\n>> Parapheurs (M27)…')
        for data in PARAPHEURS_DATA:
            circuit = circuits[data['circuit_idx']] if data['circuit_idx'] < len(circuits) else None
            # etape_courante est un IntegerField (numéro d'ordre de l'étape)
            etape_num = data.get('etape_courante') or 1

            par, created = Parapheur.objects.get_or_create(
                reference=data['reference'],
                defaults={
                    'intitule': data['intitule'],
                    'circuit': circuit,
                    'statut': data['statut'],
                    'etape_courante': etape_num,
                    'soumis_par': admin,
                    'date_soumission': timezone.now() - timedelta(days=5),
                    'notes': data.get('notes', ''),
                }
            )
            self._log('Parapheur', par, created)

    def _seed_modeles_courrier(self, admin):
        from courrier_administratif.models import ModeleCourrierSortant
        self.stdout.write('\n>> Modèles de courrier (M27)…')
        for data in MODELES_COURRIER:
            m, created = ModeleCourrierSortant.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'type_courrier': data['type_courrier'],
                    'description': data['description'],
                    'objet': data['objet'],
                    'corps': data['corps'],
                    'actif': True,
                    'cree_par': admin,
                }
            )
            self._log('Modèle courrier', m, created)

    # -- M28 : Courrier intelligent --------------------------------------------

    def _seed_comptes_email(self, admin):
        from courrier_intelligent.models import CompteEmail, SignatureEmail
        self.stdout.write('\n>> Comptes email (M28)…')
        result = []
        for data in COMPTES_EMAIL:
            compte, created = CompteEmail.objects.get_or_create(
                adresse_email=data['adresse_email'],
                defaults={
                    'utilisateur': admin,
                    'type_compte': data['type_compte'],
                    'nom_affichage': data['nom_affichage'],
                    'serveur_entrant': data['serveur_entrant'],
                    'port_entrant': data['port_entrant'],
                    'serveur_sortant': data['serveur_sortant'],
                    'port_sortant': data['port_sortant'],
                    'ssl_entrant': data['ssl_entrant'],
                    'ssl_sortant': data['ssl_sortant'],
                    'identifiant': data['identifiant'],
                    'mot_de_passe': data['mot_de_passe'],
                    'statut': data['statut'],
                    'est_principal': data['est_principal'],
                }
            )
            self._log('Compte email', compte, created)

            if created:
                SignatureEmail.objects.create(
                    utilisateur=admin,
                    compte=compte,
                    nom=f"Signature — {data['nom_affichage']}",
                    contenu_html=f"<p><strong>{admin.get_full_name()}</strong><br>{data['nom_affichage']}<br>Programme PRCC — ONG Démonstration ERP<br>📧 {data['adresse_email']} | 📞 +225 07 07 11 22 33</p>",
                    contenu_texte=f"{admin.get_full_name()}\n{data['nom_affichage']}\nProgramme PRCC\n{data['adresse_email']}",
                    est_principale=data['est_principal'],
                )
                self.stdout.write(f'    + Signature créée')

            result.append(compte)
        return result

    def _seed_templates_reponse(self, admin):
        from courrier_intelligent.models import TemplateReponse
        self.stdout.write('\n>> Templates de réponse (M28)…')
        for data in TEMPLATES_REPONSE:
            t, created = TemplateReponse.objects.get_or_create(
                titre=data['titre'],
                defaults={
                    'type_template': data['type_template'],
                    'sujet_template': data['sujet_template'],
                    'corps_html': data['corps_html'],
                    'corps_texte': data['corps_texte'],
                    'variables': data['variables'],
                    'langue': 'fr',
                    'est_global': True,
                    'cree_par': admin,
                    'actif': True,
                }
            )
            self._log('Template', t, created)

    def _seed_regles_classification(self, admin, comptes):
        from courrier_intelligent.models import RegleClassification
        self.stdout.write('\n>> Règles de classification (M28)…')
        for data in REGLES_CLASSIFICATION:
            r, created = RegleClassification.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'description': data['description'],
                    'actif': True,
                    'priorite': data['priorite'],
                    'operateur': data['operateur'],
                    'conditions': data['conditions'],
                    'action': data['action'],
                    'parametres_action': data['parametres_action'],
                    'cree_par': admin,
                    'nb_applications': 0,
                }
            )
            self._log('Règle', r, created)

    def _seed_etiquettes(self, admin):
        from courrier_intelligent.models import EtiquetteEmail
        self.stdout.write('\n>> Étiquettes email (M28)…')
        result = {}
        for data in ETIQUETTES_EMAIL:
            e, created = EtiquetteEmail.objects.get_or_create(
                nom=data['nom'],
                utilisateur=admin,
                defaults={'couleur': data['couleur']},
            )
            self._log('Étiquette', e, created)
            result[data['nom']] = e
        return result

    def _seed_emails(self, admin, projet, comptes, etiquettes):
        from courrier_intelligent.models import Email
        self.stdout.write('\n>> Emails (M28)…')
        today = date.today()
        compte = comptes[0] if comptes else None

        for data in EMAILS_DATA:
            sujet = data['sujet']
            if Email.objects.filter(sujet=sujet, expediteur_email=data['expediteur_email']).exists():
                self.stdout.write(self.style.WARNING(f'  [Existe] {sujet[:60]}'))
                continue

            email = Email.objects.create(
                compte=compte,
                direction=data['direction'],
                sujet=sujet,
                corps_html=data['corps_html'],
                corps_texte=data['corps_texte'],
                expediteur=data['expediteur'],
                expediteur_email=data['expediteur_email'],
                destinataires=data.get('destinataires', []),
                destinataires_cc=data.get('destinataires_cc', []),
                date_reception=timezone.now() - timedelta(days=abs(data['delta'])) if data['direction'] == 'entrant' else None,
                date_envoi=timezone.now() - timedelta(days=abs(data['delta'])) if data['direction'] == 'sortant' else None,
                priorite=data['priorite'],
                statut=data['statut'],
                est_lu=data.get('est_lu', False),
                lu_le=timezone.now() if data.get('est_lu') else None,
                projet=projet,
                resume_ia=data.get('resume_ia', ''),
                score_urgence=data.get('score_urgence', 50),
                traite_par_ia=bool(data.get('resume_ia')),
                suggestion_reponse_ia=data.get('suggestion_reponse_ia', ''),
                cree_par=admin,
            )
            # Attacher les étiquettes
            for nom_etiquette in data.get('etiquettes', []):
                etiq = etiquettes.get(nom_etiquette)
                if etiq:
                    email.etiquettes.add(etiq)

            self.stdout.write(self.style.SUCCESS(f'  [Créé] Email [{data["direction"]}]: {sujet[:60]}'))
