# -*- coding: utf-8 -*-
"""Génère OFFRE_COMMERCIALE_COMPLETE.docx — offre détaillée basée sur les modèles réels."""

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── Palette ──────────────────────────────────────────────────────────────────
C_NAVY    = (0x1A, 0x37, 0x6C)
C_BLUE    = (0x1F, 0x6F, 0xB8)
C_LBLUE   = (0xD6, 0xE4, 0xF7)
C_GREY    = (0xF2, 0xF4, 0xF7)
C_WHITE   = (0xFF, 0xFF, 0xFF)
C_ORANGE  = (0xE8, 0x6C, 0x1E)
C_GREEN   = (0x1E, 0x8A, 0x44)
C_BLACK   = (0x1A, 0x1A, 0x2E)


def hex3(c): return f"{c[0]:02X}{c[1]:02X}{c[2]:02X}"
def rgb(c):  return RGBColor(c[0], c[1], c[2])


# ── Primitives ────────────────────────────────────────────────────────────────
def cell_bg(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex3(color))
    tcPr.append(shd)


def cell_border(cell, color=C_BLUE, sz='4'):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement('w:tcBorders')
    for side in ('top', 'left', 'bottom', 'right'):
        e = OxmlElement(f'w:{side}')
        e.set(qn('w:val'), 'single')
        e.set(qn('w:sz'), sz)
        e.set(qn('w:color'), hex3(color))
        borders.append(e)
    tcPr.append(borders)


def run(para, text, bold=False, italic=False, size=11, color=C_BLACK, font='Calibri'):
    r = para.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    r.font.name = font
    r.font.color.rgb = rgb(color)
    return r


def para_space(doc, before=0, after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after  = Pt(after)
    return p


def h1(doc, text):
    """Titre de section avec filet bleu sous-jacent."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after  = Pt(6)
    run(p, text, bold=True, size=14, color=C_NAVY)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'), 'single'); bot.set(qn('w:sz'), '8')
    bot.set(qn('w:space'), '4');    bot.set(qn('w:color'), hex3(C_BLUE))
    pBdr.append(bot); pPr.append(pBdr)
    return p


def h2(doc, text, color=C_BLUE):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)
    run(p, text, bold=True, size=12, color=color)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(2)
    run(p, text, bold=True, size=11, color=C_NAVY)
    return p


def body(doc, text, size=11, color=C_BLACK, indent=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(4)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    run(p, text, size=size, color=color)
    return p


def bullet(doc, items, indent=0.5):
    for item in items:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after  = Pt(2)
        p.paragraph_format.left_indent  = Cm(indent)
        if isinstance(item, tuple):
            run(p, item[0], bold=True, size=10.5, color=C_NAVY)
            run(p, item[1], size=10.5, color=C_BLACK)
        else:
            run(p, item, size=10.5, color=C_BLACK)


def table(doc, headers, rows, widths=None, stripe=True):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        cell_bg(c, C_NAVY)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(p, h, bold=True, size=10, color=C_WHITE)

    # Data rows
    for ri, row_data in enumerate(rows):
        bg = C_GREY if (stripe and ri % 2 == 0) else C_WHITE
        for ci, val in enumerate(row_data):
            c = t.rows[ri+1].cells[ci]
            cell_bg(c, bg)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if isinstance(val, tuple):
                run(p, val[0], bold=True, size=9.5, color=C_NAVY)
                run(p, val[1], size=9.5)
            else:
                run(p, val, size=9.5)

    # Column widths
    if widths:
        for c_i, w in enumerate(widths):
            for row in t.rows:
                row.cells[c_i].width = Cm(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def callout(doc, text, color=C_LBLUE, text_color=C_NAVY):
    """Boîte colorée pour notes importantes."""
    t = doc.add_table(rows=1, cols=1)
    t.style = 'Table Grid'
    c = t.rows[0].cells[0]
    cell_bg(c, color)
    cell_border(c, color=C_BLUE, sz='6')
    p = c.paragraphs[0]
    p.paragraph_format.left_indent = Cm(0.3)
    run(p, text, italic=True, size=10.5, color=text_color)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


# ══════════════════════════════════════════════════════════════════════════════
doc = Document()
for sec in doc.sections:
    sec.top_margin = sec.bottom_margin = Cm(2)
    sec.left_margin = sec.right_margin = Cm(2.5)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE DE GARDE
# ══════════════════════════════════════════════════════════════════════════════
# Fond bleu marine — bandeau titre
banner_tbl = doc.add_table(rows=1, cols=1)
banner_tbl.style = 'Table Grid'
bc = banner_tbl.rows[0].cells[0]
cell_bg(bc, C_NAVY)
bc.width = Cm(17)
for _ in range(5):
    bp = bc.add_paragraph()
    bp.paragraph_format.space_after = Pt(0)
p_title = bc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p_title, 'OFFRE COMMERCIALE', bold=True, size=32, color=C_WHITE, font='Calibri')
p_sub = bc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p_sub, 'Plateforme ERP Intégrée de Gestion de Projets & Administration', bold=False, size=14, color=C_LBLUE)
for _ in range(3):
    bc.add_paragraph().paragraph_format.space_after = Pt(0)

doc.add_paragraph()

# Stats en boîte
stats_tbl = doc.add_table(rows=1, cols=4)
stats_tbl.style = 'Table Grid'
stats_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
stat_data = [
    ('23', 'Modules'),
    ('330+', 'Fonctionnalités'),
    ('100%', 'Intégré'),
    ('IA', 'Embarquée'),
]
for i, (num, lbl) in enumerate(stat_data):
    c = stats_tbl.rows[0].cells[i]
    cell_bg(c, C_LBLUE if i % 2 == 0 else C_GREY)
    c.width = Cm(4)
    p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, num + '\n', bold=True, size=22, color=C_NAVY)
    run(p, lbl, size=10, color=C_BLUE)

doc.add_paragraph()

# Infos doc
meta_tbl = doc.add_table(rows=4, cols=2)
meta_tbl.style = 'Table Grid'
meta_tbl.alignment = WD_TABLE_ALIGNMENT.RIGHT
meta_data = [
    ('Référence',  'OC-2026-001'),
    ('Date',       '13 juin 2026'),
    ('Validité',   '30 jours'),
    ('Contact',    'franckalain.ai@gmail.com'),
]
for ri, (k, v) in enumerate(meta_data):
    c0 = meta_tbl.rows[ri].cells[0]; c1 = meta_tbl.rows[ri].cells[1]
    cell_bg(c0, C_NAVY); cell_bg(c1, C_WHITE)
    c0.width = Cm(4); c1.width = Cm(8)
    run(c0.paragraphs[0], k, bold=True, size=10, color=C_WHITE)
    run(c1.paragraphs[0], v, size=10, color=C_BLACK)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  SOMMAIRE
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, 'SOMMAIRE')
toc = [
    ('1.', 'Présentation générale'),
    ('2.', 'Modules fonctionnels détaillés'),
    ('   2.1', 'Gouvernance & Structure organisationnelle'),
    ('   2.2', 'Programmes & Gestion de projets'),
    ('   2.3', 'Planification stratégique'),
    ('   2.4', 'Exécution & Suivi des activités'),
    ('   2.5', 'Suivi & Évaluation'),
    ('   2.6', 'Gestion financière & Comptabilité'),
    ('   2.7', 'Gestion Électronique de Documents (GED)'),
    ('   2.8', 'Courrier administratif'),
    ('   2.9', 'Courrier intelligent'),
    ('   2.10', 'Collaboration & Communication'),
    ('   2.11', 'Mobile terrain'),
    ('   2.12', 'Intelligence Artificielle'),
    ('   2.13', 'Business Intelligence & Tableaux de bord'),
    ('   2.14', 'Marchés publics & Achats'),
    ('   2.15', 'Ressources Humaines Projet'),
    ('   2.16', 'Logistique & Parc matériel'),
    ('   2.17', 'Partenaires & Bailleurs'),
    ('   2.18', 'Système d\'Information Géographique (SIG)'),
    ('   2.19', 'Capitalisation & Gestion des connaissances'),
    ('   2.20', 'Diligences'),
    ('   2.21', 'Événements'),
    ('   2.22', 'Gestion de la Qualité'),
    ('   2.23', 'Sécurité & Gestion des accès'),
    ('3.', 'Architecture technique'),
    ('4.', 'Sécurité & Conformité'),
    ('5.', 'Plan de mise en oeuvre'),
    ('6.', 'Proposition commerciale'),
    ('7.', 'Garanties & Niveaux de service'),
    ('8.', 'Conditions générales'),
]
for num, title in toc:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    run(p, f'{num:<8}', bold=(not num.startswith(' ')), size=10.5, color=C_NAVY)
    run(p, title, size=10.5, color=C_BLACK)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  1. PRÉSENTATION GÉNÉRALE
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, '1.  PRÉSENTATION GÉNÉRALE')

body(doc,
    'Notre plateforme ERP est une solution logicielle intégrée, développée sur mesure pour '
    'répondre aux besoins spécifiques des organisations publiques, parapubliques et des ONG '
    'qui gèrent des portefeuilles de projets de développement. Elle couvre l\'intégralité '
    'du cycle de vie des projets, depuis la gouvernance stratégique jusqu\'à la capitalisation '
    'des expériences, en passant par la planification, l\'exécution, le suivi-évaluation, '
    'la gestion financière et documentaire.')

callout(doc,
    'La solution repose sur 23 modules interconnectés, plus de 330 objets métier, '
    'une architecture REST sécurisée et une intelligence artificielle embarquée pour '
    'automatiser les tâches répétitives et enrichir la prise de décision.')

h2(doc, 'Organisations cibles')
bullet(doc, [
    'Ministères et directions nationales gérant des projets et programmes',
    'Agences d\'exécution de projets financés par des bailleurs internationaux (Banque Mondiale, AFD, PNUD, UE...)',
    'ONG et organisations de développement à implantation nationale et régionale',
    'Collectivités territoriales et établissements publics',
    'Cabinets de conseil et entreprises de maîtrise d\'œuvre',
])

h2(doc, 'Valeur ajoutée clé')
table(doc,
    ['Enjeu', 'Problème résolu', 'Bénéfice concret'],
    [
        ('Pilotage', 'Données éparpillées dans des fichiers Excel', 'Tableau de bord temps réel, une seule source de vérité'),
        ('Conformité bailleurs', 'Rapports fastidieux et manuel', 'Génération automatique de rapports financiers et S&E'),
        ('Traçabilité', 'Courrier et documents non tracés', 'GED + courrier avec circuit de validation et horodatage légal'),
        ('Terrain', 'Remontée d\'information lente', 'Collecte mobile hors-ligne synchronisée en temps réel'),
        ('Risques', 'Gestion réactive des risques', 'Registre des risques, alertes automatiques, plans de mitigation'),
        ('IA', 'Rédaction chronophage de documents', 'Génération automatique de TDR, rapports, comptes-rendus'),
    ],
    widths=[3.5, 5.5, 7])

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  2. MODULES FONCTIONNELS DÉTAILLÉS
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, '2.  MODULES FONCTIONNELS DÉTAILLÉS')

# ── 2.1 GOUVERNANCE ──────────────────────────────────────────────────────────
h2(doc, '2.1  Gouvernance & Structure organisationnelle')
body(doc,
    'Ce module constitue le référentiel institutionnel de la plateforme. Il structure '
    'l\'organisation, ses entités et ses partenaires, et offre les outils de pilotage '
    'stratégique au niveau des comités de direction.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Référentiel organisationnel : ', 'Gestion de l\'organisation, des directions, sous-directions, services et sites géolocalisés avec responsables désignés.'),
    ('Répertoire des partenaires : ', 'Profils complets (type, pays, domaines d\'intervention, contacts, logo) avec gestion du cycle de partenariat.'),
    ('Répertoire des bailleurs : ', 'Fiches bailleurs avec exigences de reporting, conditions de financement et historique des relations.'),
    ('Comités de direction : ', 'Planification des sessions, gestion de l\'ordre du jour, liste des participants, comptes-rendus officiels.'),
    ('Organigramme dynamique : ', 'Visualisation en temps réel de la hiérarchie organisationnelle.'),
])

# ── 2.2 PROGRAMMES & PROJETS ──────────────────────────────────────────────────
h2(doc, '2.2  Programmes & Gestion de projets')
body(doc,
    'Module central de la plateforme, il permet de gérer l\'ensemble du portefeuille de '
    'programmes et de projets, depuis leur création jusqu\'à leur clôture.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Portefeuille de programmes : ', 'Création de programmes multi-bailleurs avec zones d\'intervention, budget total, équipe, statut et circuit de validation.'),
    ('Gestion des projets : ', 'Projets rattachés à des programmes, avec chef de projet, budget initial/révisé, priorité, taux d\'avancement calculé automatiquement.'),
    ('Équipes projet : ', 'Affectation des membres avec rôle, taux d\'affectation et période.'),
    ('Gestion des risques : ', 'Identification, cotation (probabilité × impact), mesures de mitigation et de contingence, responsable de suivi.'),
    ('Livrables & Jalons : ', 'Suivi des livrables avec critères d\'acceptation, versionnage de fichiers et circuit de validation.'),
    ('Objectifs du programme : ', 'Arborescence d\'objectifs (général, spécifiques, résultats) avec indicateurs de mesure.'),
    ('Documents associés : ', 'Bibliothèque de documents par programme/projet avec contrôle des versions.'),
])

# ── 2.3 PLANIFICATION ────────────────────────────────────────────────────────
h2(doc, '2.3  Planification stratégique')
body(doc,
    'Module dédié à la planification opérationnelle et stratégique des projets, '
    'avec des outils d\'analyse reconnus internationalement.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Cadre logique : ', 'Construction du cadre logique par niveaux (impact, outcomes, outputs, activités) avec indicateurs, sources de vérification et hypothèses.'),
    ('Analyse SWOT : ', 'Analyse des forces/faiblesses/opportunités/menaces avec pondération, et génération automatique de stratégies par l\'IA.'),
    ('Termes de Référence (TDR) : ', 'Rédaction structurée des TDR (contexte, objectifs, livrables, profil consultant, critères de sélection) avec assistance IA.'),
    ('Plan d\'action : ', 'Plan périodique (annuel, trimestriel, mensuel) avec tâches, responsables, budget prévu/réalisé, indicateurs de réalisation.'),
    ('Programme d\'activités (PA) : ', 'Programme détaillé lié au cadre logique, avec activités, co-responsables, dates et budgets.'),
    ('Plan de travail : ', 'Décomposition hiérarchique des activités avec dépendances et Gantt interactif.'),
    ('Théorie du changement : ', 'Modélisation visuelle de la théorie du changement en JSON avec hypothèses et facteurs de risque.'),
])

# ── 2.4 EXÉCUTION ────────────────────────────────────────────────────────────
h2(doc, '2.4  Exécution & Suivi des activités')
body(doc,
    'Module opérationnel qui couvre l\'ensemble des activités quotidiennes d\'exécution : '
    'tâches, réunions, missions et rapports d\'avancement.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Gestion des activités : ', 'Activités hiérarchisées (parent/enfant) avec priorité, statut, budget prévu/réalisé, taux d\'avancement, affectation de ressources et dépendances.'),
    ('Gestion des tâches : ', 'Tâches avec checklists, sous-tâches, estimation du temps, co-assignation, historique complet des modifications.'),
    ('Gestion des réunions : ', 'Planification, convocations, points d\'ordre du jour, compte-rendu structuré (synthèse, décisions, actions), génération IA du CR.'),
    ('Gestion des missions : ', 'Ordres de mission, membres, indemnités journalières, frais de transport/hébergement, rapport de mission validé.'),
    ('Rapports d\'avancement : ', 'Rapports périodiques avec taux de réalisation, problèmes rencontrés, recommandations et prochaines étapes.'),
    ('Livrables versionnés : ', 'Gestion des versions de livrables avec circuit de validation multi-étapes et commentaires.'),
    ('Affectation des ressources : ', 'Allocation de ressources humaines et matérielles aux activités avec taux d\'affectation et période.'),
])

# ── 2.5 SUIVI & ÉVALUATION ───────────────────────────────────────────────────
h2(doc, '2.5  Suivi & Évaluation (S&E)')
body(doc,
    'Module complet de mesure de la performance, conforme aux standards internationaux '
    '(OCDE/CAD, PNUD, Banque Mondiale) et intégrant des outils de collecte de données terrain.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Cadre de résultats : ', 'Niveaux de résultats hiérarchisés (impact, outcome, output, activité) avec taux d\'avancement agrégé automatiquement.'),
    ('Indicateurs SMART : ', 'Définition complète : baseline, cible globale, unité de mesure, fréquence de collecte, désagrégation (genre, âge, zone), mode de calcul.'),
    ('Collecte d\'indicateurs : ', 'Saisie des valeurs réalisées avec géolocalisation, fichier justificatif, désagrégation et circuit de validation.'),
    ('Formulaires dynamiques : ', 'Constructeur de formulaires avec champs conditionnels, formules de calcul, contraintes de validation, collecte GPS et photo.'),
    ('Enquêtes : ', 'Enquêtes multi-canaux avec sections, questions de types variés (Likert, choix multiple, texte, GPS), collecte anonyme.'),
    ('Registre des risques : ', 'Registre complet avec probabilité × impact, niveau de risque, tendance, plans de mitigation et suivi périodique.'),
    ('Évaluations : ', 'Gestion des évaluations (mi-parcours, finale, thématique) avec critères OCDE (pertinence, efficacité, efficience, impact, durabilité).'),
    ('Leçons apprises : ', 'Capitalisation structurée des leçons avec recommandations, conditions de réplicabilité et tags.'),
    ('Analyse prédictive IA : ', 'Prévisions de performance des indicateurs par modèles IA avec score de confiance et suggestions.'),
    ('Rapports S&E automatisés : ', 'Génération de rapports périodiques avec données JSON structurées et assistance IA rédactionnelle.'),
])

# ── 2.6 GESTION FINANCIÈRE ───────────────────────────────────────────────────
h2(doc, '2.6  Gestion financière & Comptabilité analytique')
body(doc,
    'Module financier complet couvrant le cycle budgétaire, les dépenses, les engagements, '
    'la trésorerie, les conventions de financement et le rapprochement bancaire.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Gestion des budgets : ', 'Budgets initial et révisés par programme/projet/exercice, avec lignes budgétaires (unité × quantité × coût unitaire), suivi des engagements et dépenses.'),
    ('Circuit de validation budgétaire : ', 'Workflow multi-niveaux : responsable → finance → approbateur, avec motif de rejet et historique.'),
    ('Saisie des dépenses : ', 'Enregistrement avec ligne budgétaire, fournisseur, justificatif, mode de paiement et multi-devises avec taux de change.'),
    ('Gestion des avances : ', 'Avances de fonds avec suivi des justifications et remboursements.'),
    ('Engagements financiers : ', 'Engagements préalables à la dépense pour réservation budgétaire.'),
    ('Conventions de financement : ', 'Suivi complet des conventions bailleurs : tranches, cofinancements, conditions, rapports exigés.'),
    ('Rapports bailleurs : ', 'Rapports financiers périodiques par convention avec taux d\'exécution et montants par période.'),
    ('Plan de trésorerie : ', 'Prévisions de flux entrants/sortants par mois avec suivi réel.'),
    ('Comptes bancaires : ', 'Gestion multi-comptes avec mouvements, soldes et rapprochement bancaire automatisé.'),
    ('Rapports financiers automatisés : ', 'États financiers (budget vs réalisé, taux d\'exécution) générés automatiquement avec export Excel/PDF.'),
    ('Gestion des fournisseurs : ', 'Répertoire des fournisseurs avec RIB bancaire, numéro fiscal et historique des paiements.'),
])

# ── 2.7 GED ──────────────────────────────────────────────────────────────────
h2(doc, '2.7  Gestion Électronique de Documents (GED)')
body(doc,
    'GED complète avec coffre-fort numérique, versionnage, OCR automatique, workflow de validation, '
    'signature électronique et archivage légal.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Plan de classement : ', 'Arborescence de catégories documentaires avec domaines, durées de conservation et plans de conservation archivistique.'),
    ('Référentiel de documents : ', 'Chaque document dispose d\'une référence unique, d\'une empreinte SHA-256 pour l\'intégrité, d\'un niveau de confidentialité et d\'un statut.'),
    ('Versionnage automatique : ', 'Historique complet des versions avec auteur, date, taille et empreinte de chaque version.'),
    ('OCR automatique : ', 'Extraction de texte sur les scans (PDF, images) via PyMuPDF + Tesseract pour la recherche plein texte.'),
    ('IA documentaire : ', 'Résumé automatique, extraction de mots-clés, suggestion de catégorie et détection de doublons.'),
    ('Workflow de validation : ', 'Circuit de validation multi-niveaux paramétrable avec délais, alertes et historique des décisions.'),
    ('Signature électronique : ', 'Signatures multi-niveaux avec horodatage, certificat et vérification de l\'empreinte.'),
    ('Liens de partage sécurisés : ', 'Liens temporaires avec mot de passe, limite de téléchargements et date d\'expiration.'),
    ('Gestion des accès : ', 'Contrôle des droits par document avec niveaux (lecture, modification) et expiration.'),
    ('Coffre-fort numérique : ', 'Archivage légal avec boîtes d\'archives chiffrées AES-256-GCM, horodatage légal et procès-verbal de destruction.'),
    ('Journal d\'audit complet : ', 'Traçabilité de toutes les actions sur les documents (consultation, téléchargement, modification, suppression).'),
    ('Bibliothèque de modèles : ', 'Modèles de documents réutilisables avec instructions de remplissage.'),
])

# ── 2.8 COURRIER ADMINISTRATIF ───────────────────────────────────────────────
h2(doc, '2.8  Courrier administratif')
body(doc,
    'Système de gestion du courrier entrant et sortant avec numérotation automatique, '
    'circuit de visa (parapheur électronique) et intégration GED.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Courrier entrant : ', 'Enregistrement avec numéro unique, scan/OCR automatique, affectation à un agent avec instructions, traçabilité du traitement.'),
    ('Courrier sortant : ', 'Rédaction avec modèles, référencement automatique, liaison au courrier entrant si réponse, signature et expédition.'),
    ('Parapheur électronique : ', 'Circuit de visa paramétrable (étapes, validateurs, délais), suivi en temps réel, décision (visa/refus) avec commentaire.'),
    ('Diligences courrier : ', 'Extraction automatique des diligences du courrier entrant avec assignation, délai et suivi.'),
    ('Modèles de courrier : ', 'Bibliothèque de modèles par type (note, lettre, circulaire) avec variables de fusion.'),
    ('Statistiques courrier : ', 'Tableaux de bord du traitement (délais moyens, volumes, taux de traitement) par direction.'),
])

# ── 2.9 COURRIER INTELLIGENT ─────────────────────────────────────────────────
h2(doc, '2.9  Courrier intelligent (messagerie IA)')
body(doc,
    'Module de gestion de la messagerie électronique avec synchronisation IMAP/SMTP, '
    'classification automatique par règles et IA, et détection d\'actions.')
h3(doc, 'Fonctionnalités détaillées')
bullet(doc, [
    ('Comptes email multi-protocoles : ', 'Connexion IMAP/SMTP avec SSL, gestion de plusieurs comptes par utilisateur, synchronisation automatique.'),
    ('Classification automatique : ', 'Règles de classification personnalisées (expéditeur, objet, contenu) avec actions automatiques (catégorisation, affectation, archivage).'),
    ('Analyse IA des emails : ', 'Résumé automatique, détection des actions et échéances, score d\'urgence, suggestion de réponse.'),
    ('Archivage GED automatique : ', 'Archivage des emails importants dans la GED avec pièces jointes liées.'),
    ('Actions et suivi : ', 'Extraction des actions détectées dans les emails et création de tâches liées.'),
    ('Étiquettes et filtres : ', 'Système d\'étiquettes colorées, filtres avancés et recherche plein texte.'),
    ('Templates de réponse : ', 'Bibliothèque de réponses types avec variables de fusion et multi-langues.'),
])

# ── 2.10 COLLABORATION ───────────────────────────────────────────────────────
h2(doc, '2.10  Collaboration & Communication interne')
bullet(doc, [
    ('Canaux de discussion : ', 'Canaux publics/privés par projet ou programme, messagerie instantanée, réactions et mentions @.'),
    ('Notifications intelligentes : ', 'Notifications multi-canaux (email, SMS, push, WhatsApp) avec plages horaires de silence et préférences par type.'),
    ('Groupes de travail : ', 'Espaces de travail thématiques avec membres, documents et discussions.'),
    ('Activité récente : ', 'Fil d\'actualité personnalisé de toutes les actions relatives aux projets suivis.'),
])

# ── 2.11 MOBILE TERRAIN ──────────────────────────────────────────────────────
h2(doc, '2.11  Mobile terrain')
bullet(doc, [
    ('Sessions terrain : ', 'Enregistrement des sessions de collecte avec géolocalisation de début/fin et mode hors-ligne.'),
    ('Collecte multi-types : ', 'Collecte de données numériques, photos, fichiers audio/vidéo, formulaires dynamiques avec GPS.'),
    ('Pointage terrain : ', 'Pointage des agents avec photo-preuve, GPS et validation superviseur.'),
    ('Synchronisation : ', 'Synchronisation bidirectionnelle avec comptage des éléments envoyés/reçus et gestion des conflits.'),
    ('QR Code : ', 'Scan QR pour identifier équipements, bénéficiaires ou points d\'intervention.'),
])

# ── 2.12 INTELLIGENCE ARTIFICIELLE ──────────────────────────────────────────
h2(doc, '2.12  Intelligence Artificielle')
body(doc,
    'Module transversal d\'IA qui enrichit toutes les fonctions de la plateforme '
    'avec des capacités de génération, d\'analyse et de recommandation.')
bullet(doc, [
    ('Assistant conversationnel : ', 'Chatbot contextuel (projet, programme) avec historique de conversation, tokens suivis et score de confiance.'),
    ('Génération de documents : ', 'Génération automatique de TDR, rapports S&E, comptes-rendus de réunion, rapports financiers en un clic.'),
    ('Analyse prédictive : ', 'Modèles IA pour prévoir les performances des indicateurs, détecter les anomalies budgétaires et suggérer des actions correctives.'),
    ('Alertes IA : ', 'Détection proactive de risques, dérives de délais ou de budget, avec notifications priorisées.'),
    ('Recommandations : ', 'Suggestions actionnables avec score de pertinence, justification et suivi de l\'acceptation/rejet.'),
    ('Journal d\'audit IA : ', 'Traçabilité de toutes les interactions IA (tokens utilisés, durée, résultats) pour contrôle et conformité.'),
])

# ── 2.13 BUSINESS INTELLIGENCE ───────────────────────────────────────────────
h2(doc, '2.13  Business Intelligence & Tableaux de bord')
bullet(doc, [
    ('Tableaux de bord personnalisables : ', 'Création de dashboards avec widgets configurables (KPI, graphiques, jauges, cartes) positionnés en grille.'),
    ('Widgets multi-sources : ', 'Connexion aux datamarts Finance, S&E, RH, Courrier, GED et Risques pour des indicateurs croisés.'),
    ('Partage de dashboards : ', 'Partage avec contrôle des droits (lecture, modification) entre utilisateurs et équipes.'),
    ('Datamarts métier : ', 'Entrepôts de données pré-agrégés par mois/trimestre pour Finance, S&E, RH, Courrier, GED et Risques.'),
    ('KPI personnalisés : ', 'Création de KPI avec formules, seuils d\'alerte (bas/haut) et actualisation automatique.'),
    ('Rapports BI : ', 'Génération de rapports périodiques avec export multi-format (Excel, PDF, CSV).'),
    ('Connecteurs externes : ', 'Intégration avec outils BI tiers (Power BI, Tableau, etc.) via API.'),
])

# ── 2.14 MARCHÉS PUBLICS ─────────────────────────────────────────────────────
h2(doc, '2.14  Marchés publics & Achats')
bullet(doc, [
    ('Plan de passation des marchés : ', 'Planification annuelle des marchés par programme/projet avec budget total prévu et suivi de réalisation.'),
    ('Demandes d\'achat : ', 'Workflow de demandes avec justification technique, spécifications, estimation budgétaire et circuit de validation.'),
    ('Appels d\'offres : ', 'Publication DAO (Dossier d\'Appel d\'Offres), critères d\'évaluation pondérés, date limite de soumission.'),
    ('Évaluation des offres : ', 'Notation technique et financière des soumissionnaires avec calcul automatique de la note globale pondérée.'),
    ('Gestion des contrats : ', 'Contrats avec montant TTC, calendrier de paiement, conditions, garanties, pénalités, suivi d\'exécution.'),
    ('Avenants : ', 'Gestion des avenants avec recalcul du montant global et extension de délai.'),
])

# ── 2.15 RH PROJET ───────────────────────────────────────────────────────────
h2(doc, '2.15  Ressources Humaines Projet')
bullet(doc, [
    ('Dossiers employés : ', 'Profils complets (type, compétences, taux journalier, CV) avec suivi du taux d\'occupation maximum.'),
    ('Affectations RH : ', 'Affectation des agents aux programmes/projets/activités avec taux d\'affectation et période.'),
    ('Feuilles de temps : ', 'Saisie journalière par projet/activité, validation mensuelle, calcul automatique du montant total.'),
    ('Évaluations de performance : ', 'Grilles d\'évaluation paramétrables par critères avec notes, axes d\'amélioration et objectifs.'),
    ('Plan de formation : ', 'Identification des besoins de formation avec priorisation, suivi de réalisation et coûts.'),
    ('Congés & absences : ', 'Demandes de congé/absence avec workflow d\'approbation, décompte automatique et états.'),
])

# ── 2.16 LOGISTIQUE ──────────────────────────────────────────────────────────
h2(doc, '2.16  Logistique & Parc matériel')
bullet(doc, [
    ('Flotte de véhicules : ', 'Suivi de l\'état, kilométrage, assurance, vignette et prochain entretien de chaque véhicule.'),
    ('Missions véhicules : ', 'Bons de mission avec conducteur, trajet, carburant consommé, coûts et approbation.'),
    ('Entretiens : ', 'Planification et suivi des entretiens préventifs/curatifs avec coûts et prochaines échéances.'),
    ('Inventaire des équipements : ', 'Registre d\'inventaire avec code, numéro de série, affectation, lieu, valeur et garantie.'),
    ('Gestion des stocks : ', 'Magasins avec articles, niveaux de stock d\'alerte, mouvements (entrée/sortie/transfert) et valorisation.'),
])

# ── 2.17 PARTENAIRES & BAILLEURS ─────────────────────────────────────────────
h2(doc, '2.17  Partenaires & Bailleurs')
bullet(doc, [
    ('Répertoire des partenaires : ', 'Profils enrichis avec secteurs d\'intervention, contacts multiples, géolocalisation et notes.'),
    ('Conventions de partenariat : ', 'Gestion des conventions avec signataires, clauses, obligations des parties, alertes d\'expiration.'),
    ('Renouvellements : ', 'Suivi des renouvellements avec historique des modifications de durée et montant.'),
    ('Portail partenaire : ', 'Espace extranet pour que les partenaires déposent et consultent des documents avec droits configurables.'),
    ('Liaisons projets : ', 'Association partenaire-projet avec rôle, montant financé et période.'),
])

# ── 2.18 SIG ─────────────────────────────────────────────────────────────────
h2(doc, '2.18  Système d\'Information Géographique (SIG)')
bullet(doc, [
    ('Zones géographiques : ', 'Référentiel hiérarchique de zones (pays, région, département, commune) avec superficie et population.'),
    ('Couches cartographiques : ', 'Couches personnalisées avec style d\'affichage, opacité, icônes et filtres par programme/projet.'),
    ('Points cartographiques : ', 'Géolocalisation des sites de projet, infrastructures, points de collecte avec valeurs d\'indicateurs associées.'),
    ('Cartographie des infrastructures : ', 'Infrastructures avec statut, capacité, population bénéficiaire, date de mise en service et coût.'),
    ('Cartes composées : ', 'Composition de cartes multi-couches avec position centrale et niveau de zoom par défaut.'),
    ('Export géographique : ', 'Export des données géographiques en GeoJSON pour intégration avec QGIS ou autres SIG.'),
])

# ── 2.19 CAPITALISATION ──────────────────────────────────────────────────────
h2(doc, '2.19  Capitalisation & Gestion des connaissances')
bullet(doc, [
    ('Fiches de capitalisation : ', 'Documentation structurée des expériences (contexte, problème, solution, résultats, recommandation) avec niveau de réplicabilité.'),
    ('Bibliothèque de ressources : ', 'Bibliothèque documentaire (études, guides, rapports) avec recherche plein texte et téléchargements trackés.'),
    ('Centres de connaissances : ', 'Espaces thématiques regroupant fiches et bibliothèque par domaine d\'expertise.'),
    ('Génération IA : ', 'Rédaction assistée des fiches de capitalisation à partir des données du projet.'),
    ('Indicateurs d\'utilisation : ', 'Suivi des consultations et favoris pour identifier les ressources les plus utiles.'),
])

# ── 2.20 DILIGENCES ──────────────────────────────────────────────────────────
h2(doc, '2.20  Diligences')
bullet(doc, [
    ('Registre des diligences : ', 'Enregistrement de toutes les diligences (issues du courrier, des réunions, des missions) avec émetteur, responsable et délai.'),
    ('Suivi d\'avancement : ', 'Rapports de suivi périodiques avec taux d\'avancement, actions réalisées et prochaines étapes.'),
    ('Relances automatiques : ', 'Notifications de relance aux responsables avec message personnalisé.'),
    ('Tableau de bord : ', 'Vue globale des diligences par statut, priorité et délai de traitement.'),
])

# ── 2.21 ÉVÉNEMENTS ──────────────────────────────────────────────────────────
h2(doc, '2.21  Événements')
bullet(doc, [
    ('Planification : ', 'Organisation d\'événements (ateliers, conférences, formations, cérémonies) avec lieu, programme, objectifs et résultats attendus.'),
    ('Gestion des participants : ', 'Inscriptions, confirmations, présence par QR code, badges et évaluations post-événement.'),
    ('Suivi budgétaire : ', 'Dépenses par catégorie avec fournisseurs et récapitulatif budget prévu/réalisé.'),
    ('Compte-rendu structuré : ', 'Documentation des résultats et points de suivi.'),
])

# ── 2.22 GESTION QUALITÉ ────────────────────────────────────────────────────
h2(doc, '2.22  Gestion de la Qualité')
bullet(doc, [
    ('Non-conformités : ', 'Enregistrement des non-conformités (majeures/mineures) avec analyse de cause racine, impact et responsable de traitement.'),
    ('Plans d\'action qualité : ', 'Actions correctives et préventives (CAPA) avec délai, réalisation et vérification d\'efficacité.'),
    ('Audits internes : ', 'Planification et conduite d\'audits avec périmètre, critères, rapport de synthèse et comptage des écarts.'),
    ('Indicateurs qualité : ', 'KPI qualité avec valeur cible, valeur actuelle, fréquence de mesure et alertes automatiques.'),
])

# ── 2.23 SÉCURITÉ & ACCÈS ───────────────────────────────────────────────────
h2(doc, '2.23  Sécurité & Gestion des accès')
bullet(doc, [
    ('Authentification forte : ', 'Authentification JWT + 2FA obligatoire (TOTP via application ou OTP par SMS/email).'),
    ('Gestion des rôles & permissions : ', 'Droits granulaires par module (lire, créer, modifier, valider, supprimer, exporter, imprimer) assignés aux rôles.'),
    ('Verrouillage de compte : ', 'Blocage automatique après N tentatives échouées avec durée configurable.'),
    ('Sessions utilisateur : ', 'Suivi des sessions actives (IP, user-agent, device) avec révocation à distance.'),
    ('Journal d\'audit global : ', 'Log complet de toutes les actions (qui, quoi, quand, depuis quelle IP) pour conformité et investigations.'),
    ('Mots de passe : ', 'Politique de changement obligatoire, réinitialisation sécurisée par token UUID expirant.'),
])

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  3. ARCHITECTURE TECHNIQUE
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, '3.  ARCHITECTURE TECHNIQUE')

h2(doc, '3.1  Stack technologique')
table(doc,
    ['Couche', 'Technologie', 'Version', 'Rôle'],
    [
        ('Backend',        'Django',                 '6.x',     'Framework web principal'),
        ('API',            'Django REST Framework',  '3.17',    'API REST JSON'),
        ('Authentification','SimpleJWT',             '5.5',     'Tokens JWT + refresh'),
        ('2FA',            'pyOTP',                  '2.9',     'TOTP / OTP multi-canal'),
        ('Base de données','PostgreSQL',             '15+',     'SGBD relationnel principal'),
        ('Cache',          'Redis',                  '6+',      'Cache applicatif + sessions'),
        ('Tâches async',   'Celery',                 '5.6',     'Tâches différées et récurrentes'),
        ('Planificateur',  'Celery Beat',            '2.9',     'Tâches périodiques'),
        ('Stockage',       'Django Storages',        '1.14',    'S3 / Azure / Local'),
        ('OCR',            'PyMuPDF + Tesseract',    '1.24/0.3','Extraction de texte'),
        ('Documents',      'python-docx',            '1.1',     'Génération DOCX'),
        ('Chiffrement',    'Cryptography',           '44.0',    'AES-256-GCM'),
        ('Data analyse',   'Pandas + openpyxl',      '3.x',     'Calcul et exports Excel'),
        ('Documentation',  'drf-spectacular',        '0.29',    'OpenAPI / Swagger'),
        ('Déploiement',    'Gunicorn + Nginx',       'latest',  'Production Linux'),
    ],
    widths=[3.5, 4, 2, 7])

h2(doc, '3.2  Architecture déployée')
bullet(doc, [
    ('Serveur applicatif : ', 'Gunicorn (workers multiples) derrière un reverse-proxy Nginx avec HTTPS/TLS.'),
    ('Base de données : ', 'PostgreSQL avec sauvegardes automatiques quotidiennes et réplication possible.'),
    ('File de messages : ', 'Redis pour le cache, les sessions et la file Celery.'),
    ('Stockage fichiers : ', 'Compatible S3 (AWS, MinIO, OVH Object Storage) ou stockage local avec migration transparente.'),
    ('API documentée : ', 'Interface Swagger interactive pour les intégrations tierces.'),
    ('Multi-tenant possible : ', 'Architecture prête pour la séparation de données par organisation.'),
])

h2(doc, '3.3  Intégrations externes possibles')
table(doc,
    ['Système', 'Type d\'intégration', 'Usage'],
    [
        ('Power BI / Tableau',    'API REST + connecteur',   'Dashboards avancés'),
        ('QGIS / ArcGIS',         'Export GeoJSON',          'Cartographie SIG'),
        ('Messagerie email',      'IMAP/SMTP',               'Courrier intelligent'),
        ('SMS / WhatsApp',        'API gateway',             'Notifications terrain'),
        ('Systèmes financiers',   'API REST',                'Import/export données'),
        ('Active Directory/LDAP', 'SSO possible',            'Authentification centralisée'),
    ],
    widths=[4, 5, 7.5])

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  4. SÉCURITÉ & CONFORMITÉ
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, '4.  SÉCURITÉ & CONFORMITÉ')
table(doc,
    ['Domaine', 'Mesure mise en oeuvre', 'Standard'],
    [
        ('Authentification',     'JWT + 2FA TOTP obligatoire, codes de secours',                    'NIST 800-63B'),
        ('Contrôle d\'accès',   'RBAC granulaire par module et action',                              'ISO 27001'),
        ('Chiffrement au repos', 'AES-256-GCM pour les documents archivés',                          'FIPS 140-2'),
        ('Chiffrement transit',  'HTTPS/TLS 1.3 obligatoire',                                        'PCI-DSS'),
        ('Intégrité documents',  'Empreinte SHA-256 sur chaque fichier et version',                   'ISO 15489'),
        ('Horodatage légal',     'Horodatage des archives avec valeur probante',                      'eIDAS'),
        ('Journal d\'audit',    'Log immuable de toutes les actions utilisateur',                     'SOC 2 Type II'),
        ('Verrouillage compte',  'Blocage après N échecs, alerte sécurité',                          'OWASP'),
        ('Sauvegarde',           'Sauvegardes automatiques quotidiennes chiffrées',                   'RTO < 4h'),
        ('Données personnelles', 'Gestion des droits d\'accès, suppression sur demande',             'RGPD'),
    ],
    widths=[4, 8, 4.5])

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  5. PLAN DE MISE EN OEUVRE
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, '5.  PLAN DE MISE EN OEUVRE')
h2(doc, '5.1  Phasage du projet')
table(doc,
    ['Phase', 'Durée', 'Activités', 'Livrables'],
    [
        ('Phase 0\nCadrage',          'S1–S2',   'Audit organisationnel, recueil des besoins, validation du périmètre, identification des données à migrer', 'Rapport d\'audit, cahier des charges validé'),
        ('Phase 1\nInfrastructure',   'S3–S4',   'Provisionnement serveur, installation OS/SGBD, déploiement application, configuration SSL/DNS', 'Environnement de recette opérationnel'),
        ('Phase 2\nParamétrages',     'S5–S6',   'Configuration organisation, rôles, droits, workflows de validation, intégration email, cartographie', 'Plateforme configurée et paramétrée'),
        ('Phase 3\nMigration',        'S7–S8',   'Import données existantes (utilisateurs, projets, documents, budgets), nettoyage, validation', 'Données migrées et vérifiées'),
        ('Phase 4\nFormation',        'S9–S10',  'Formation administrateurs (2 j), utilisateurs (3 j), super-utilisateurs référents (1 j)', 'Équipes formées, guide utilisateur livré'),
        ('Phase 5\nRecette',          'S11',     'Tests métier avec les équipes clientes, corrections des écarts, validation finale', 'PV de recette signé'),
        ('Phase 6\nProduction',       'S12',     'Bascule en production, monitoring post-déploiement (30 jours), support renforcé', 'Système en production, rapport de démarrage'),
    ],
    widths=[2.8, 1.5, 7.5, 4.7])

h2(doc, '5.2  Équipe projet proposée')
table(doc,
    ['Rôle', 'Responsabilité', 'Allocation'],
    [
        ('Chef de projet',          'Pilotage global, interface client, reporting',              '50 %'),
        ('Architecte technique',    'Infrastructure, déploiement, sécurité',                    '100 % phases 1–2'),
        ('Développeur senior',      'Paramétrage, migration, adaptations spécifiques',          '100 %'),
        ('Formateur',               'Formation utilisateurs et administrateurs',                '100 % phase 4'),
        ('Support technique',       'Assistance post-déploiement (hotline)',                    'Permanent'),
    ],
    widths=[4, 9, 3.5])

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  6. PROPOSITION COMMERCIALE
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, '6.  PROPOSITION COMMERCIALE')
callout(doc,
    'Les tarifs ci-dessous sont indicatifs. Un devis personnalisé sera établi après '
    'audit de vos besoins, de votre infrastructure existante et du nombre d\'utilisateurs.',
    color=C_GREY, text_color=C_NAVY)

h2(doc, '6.1  Structure tarifaire')
table(doc,
    ['Prestation', 'Description', 'Unité', 'Tarif'],
    [
        ('Licence logicielle — Starter',   '5 modules au choix, jusqu\'à 20 utilisateurs',            'Forfait',    'Sur devis'),
        ('Licence logicielle — Pro',       '12 modules, jusqu\'à 50 utilisateurs',                    'Forfait',    'Sur devis'),
        ('Licence logicielle — Entreprise','23 modules complets, utilisateurs illimités',             'Forfait',    'Sur devis'),
        ('Déploiement & configuration',    'Installation, paramétrage métier, intégrations',          'Forfait',    'Sur devis'),
        ('Migration de données',           'Import données existantes (Excel, CSV, base existante)',  'Jour/homme', 'Sur devis'),
        ('Formation administrateurs',      'Formation technique (2 jours, jusqu\'à 5 personnes)',    'Session',    'Sur devis'),
        ('Formation utilisateurs',         'Formation fonctionnelle (3 jours, jusqu\'à 20 pers.)',   'Session',    'Sur devis'),
        ('Maintenance & support annuel',   'Mises à jour, corrections, support technique 5j/7',      'An',         'Sur devis'),
        ('Hébergement managé',             'Serveur dédié, sauvegardes, monitoring 24h/7j',          'Mois',       'Sur devis'),
        ('Développement sur mesure',       'Modules ou fonctionnalités additionnels',                'Jour/homme', 'Sur devis'),
    ],
    widths=[4.5, 6.5, 2, 3.5])

h2(doc, '6.2  Options et modules complémentaires')
table(doc,
    ['Option', 'Description', 'Tarif'],
    [
        ('Module IA avancé',        'Modèles IA personnalisés entraînés sur vos données',    'Sur devis'),
        ('Intégration SSO/LDAP',    'Authentification Active Directory / LDAP centralisée', 'Sur devis'),
        ('Application mobile native','App iOS/Android dédiée pour la collecte terrain',     'Sur devis'),
        ('Connecteur Power BI',     'Connecteur direct vers Power BI pour reporting avancé','Sur devis'),
        ('Formation avancée',       'Formation sur mesure sur site, durée à définir',        'Sur devis'),
        ('Audit de sécurité',       'Test de pénétration et rapport de conformité',         'Sur devis'),
    ],
    widths=[4.5, 8.5, 3.5])

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  7. GARANTIES & NIVEAUX DE SERVICE
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, '7.  GARANTIES & NIVEAUX DE SERVICE (SLA)')
table(doc,
    ['Indicateur', 'Niveau garanti', 'Pénalité en cas de non-respect'],
    [
        ('Disponibilité plateforme',        '99,5 % / mois (hors maintenance planifiée)',    'Crédit de service proportionnel'),
        ('Délai de réponse — Incident P1',  '< 2 heures (indisponibilité totale)',           'Escalade direction technique'),
        ('Délai de réponse — Incident P2',  '< 4 heures (perte de fonctionnalité critique)','Support renforcé'),
        ('Délai de réponse — Incident P3',  '< 1 jour ouvré (anomalie non bloquante)',       '--'),
        ('Délai de réponse — Demande',      '< 3 jours ouvrés (évolution, question)',        '--'),
        ('Sauvegardes',                     'Quotidiennes, rétention 30 jours',              'Restauration gratuite'),
        ('Mises à jour de sécurité',        'Sous 72h après publication de correctif',       '--'),
        ('Maintenance planifiée',           'Hors heures ouvrables, préavis 48h',            '--'),
        ('Plages de support',               'Lun.–Ven. 8h–18h (heure locale)',               'Astreinte disponible sur option'),
    ],
    widths=[5.5, 6, 5])

h2(doc, '7.2  Garanties supplémentaires')
bullet(doc, [
    'Garantie de réversibilité : export complet des données dans des formats ouverts (JSON, CSV, Excel) à tout moment.',
    'Propriété des données : les données du client restent en tout temps sa propriété exclusive.',
    'Confidentialité : accord de confidentialité (NDA) signé avant le démarrage du projet.',
    'Code source : possibilité de dépôt du code source en séquestre (escrow) selon les modalités contractuelles.',
    'Conformité RGPD : registre des traitements, droit à l\'oubli, portabilité et minimisation des données.',
])

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
#  8. CONDITIONS GÉNÉRALES
# ══════════════════════════════════════════════════════════════════════════════
h1(doc, '8.  CONDITIONS GÉNÉRALES & MODALITÉS')

h2(doc, '8.1  Modalités de paiement')
bullet(doc, [
    '30 % à la signature du contrat (acompte)',
    '40 % à la réception de l\'environnement de recette (Phase 5)',
    '30 % à la mise en production (Phase 6)',
    'Maintenance : paiement annuel en début de période',
])

h2(doc, '8.2  Conditions générales')
bullet(doc, [
    'Validité de l\'offre : 30 jours à compter de la date d\'émission (13 juin 2026).',
    'Les prix sont exprimés hors taxes. TVA applicable selon la législation en vigueur.',
    'Les délais indiqués sont des estimations basées sur un projet standard ; ils seront ajustés après l\'audit de cadrage.',
    'Toute modification de périmètre en cours de projet fera l\'objet d\'un avenant signé des deux parties.',
    'La présente offre est soumise à l\'acceptation d\'un bon de commande ou d\'un contrat de prestation.',
])

h2(doc, '8.3  Droit applicable & Juridiction')
body(doc,
    'Le contrat sera soumis au droit applicable dans le pays du client. '
    'Tout litige sera soumis à la juridiction compétente, après tentative de résolution amiable '
    'dans un délai de 30 jours.')

doc.add_paragraph()
doc.add_paragraph()

# Pied de page / Closing
closing_tbl = doc.add_table(rows=1, cols=1)
cc = closing_tbl.rows[0].cells[0]
cell_bg(cc, C_NAVY)
p1 = cc.add_paragraph()
p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p1, 'OFFRE CONFIDENTIELLE — À L\'ATTENTION EXCLUSIVE DU DESTINATAIRE',
    bold=True, size=10, color=C_WHITE)
p2 = cc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p2, 'Référence : OC-2026-001  |  Date : 13 juin 2026  |  Validité : 30 jours',
    size=9.5, color=C_LBLUE)
p3 = cc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p3, 'Contact : franckalain.ai@gmail.com',
    size=9.5, color=C_LBLUE)

# ── Sauvegarde ────────────────────────────────────────────────────────────────
output = 'OFFRE_COMMERCIALE_COMPLETE.docx'
doc.save(output)
print(f'OK  Fichier genere : {output}')
