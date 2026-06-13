from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ── couleurs stockées en tuples (r, g, b) ────────────────────────────────────
BLUE_DARK  = (0x1A, 0x37, 0x6C)
BLUE_MED   = (0x1F, 0x6F, 0xB8)
BLUE_LIGHT = (0xD6, 0xE4, 0xF7)
GREY_LIGHT = (0xF5, 0xF5, 0xF5)
WHITE      = (0xFF, 0xFF, 0xFF)
ORANGE     = (0xE8, 0x6C, 0x1E)


def rgb_hex(color: tuple) -> str:
    return f"{color[0]:02X}{color[1]:02X}{color[2]:02X}"


def to_rgb(color: tuple) -> RGBColor:
    return RGBColor(color[0], color[1], color[2])


def set_cell_bg(cell, color: tuple):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    hex_color = rgb_hex(color)
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex_color)
    tcPr.append(shd)


def set_cell_border(cell, **kwargs):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        val = kwargs.get(edge, {})
        if val:
            tag = OxmlElement(f'w:{edge}')
            for k, v in val.items():
                tag.set(qn(k), v)
            tcBorders.append(tag)
    tcPr.append(tcBorders)


def add_run(para, text, bold=False, italic=False, size=11,
            color=None, font='Calibri'):
    run = para.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = font
    if color:
        run.font.color.rgb = to_rgb(color)
    return run


def heading(doc, text, level=1, color=BLUE_DARK, size=14):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)
    add_run(p, text, bold=True, size=size, color=color)
    if level == 1:
        # ligne décorative sous le titre
        border = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'),   'single')
        bottom.set(qn('w:sz'),    '6')
        bottom.set(qn('w:space'), '4')
        bottom.set(qn('w:color'), rgb_hex(BLUE_MED))
        border.append(bottom)
        p._p.get_or_add_pPr().append(border)
    return p


def styled_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # En-têtes
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        set_cell_bg(cell, BLUE_DARK)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_run(p, h, bold=True, size=10, color=WHITE)

    # Données
    for r_idx, row_data in enumerate(rows):
        tr = table.rows[r_idx + 1]
        bg = GREY_LIGHT if r_idx % 2 == 0 else WHITE
        for c_idx, val in enumerate(row_data):
            cell = tr.cells[c_idx]
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_run(p, val, size=9.5)

    # Largeurs colonnes
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)

    doc.add_paragraph()
    return table


# ══════════════════════════════════════════════════════════════════════════════
doc = Document()

# ── Marges ───────────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE DE GARDE
# ══════════════════════════════════════════════════════════════════════════════
for _ in range(4):
    doc.add_paragraph()

title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run(title_p, 'OFFRE COMMERCIALE', bold=True, size=28, color=BLUE_DARK)

doc.add_paragraph()
sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run(sub_p, 'Plateforme ERP de Gestion de Projets & Administration',
        bold=True, size=16, color=BLUE_MED)

doc.add_paragraph()
doc.add_paragraph()

# Bandeau orange
banner = doc.add_paragraph()
banner.alignment = WD_ALIGN_PARAGRAPH.CENTER
shd = OxmlElement('w:pBdr')
for edge in ['top', 'bottom']:
    e = OxmlElement(f'w:{edge}')
    e.set(qn('w:val'),   'single')
    e.set(qn('w:sz'),    '12')
    e.set(qn('w:space'), '4')
    e.set(qn('w:color'), rgb_hex(ORANGE))
    shd.append(e)
banner._p.get_or_add_pPr().append(shd)
add_run(banner, 'Solution intégrée · 18 modules · Sécurité renforcée · IA embarquée',
        italic=True, size=12, color=ORANGE)

for _ in range(6):
    doc.add_paragraph()

# Infos de couverture
meta = [
    ('Référence', 'OC-2026-001'),
    ('Date',      '13 juin 2026'),
    ('Validité',  '30 jours'),
    ('Contact',   'franckalain.ai@gmail.com'),
]
for label, value in meta:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_run(p, f'{label} : ', bold=True, size=11, color=BLUE_DARK)
    add_run(p, value, size=11, color=BLUE_MED)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 1. PRÉSENTATION
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, '1.  PRÉSENTATION')
intro = doc.add_paragraph()
intro.paragraph_format.space_after = Pt(6)
add_run(intro,
    'Nous avons le plaisir de vous soumettre cette offre pour la mise en place d\'une '
    'plateforme ERP intégrée de gestion de projets et d\'administration, '
    'développée sur mesure pour répondre aux exigences des organisations publiques '
    'et privées gérant des portefeuilles de projets complexes.\n\n'
    'Cette solution couvre l\'intégralité du cycle de vie des projets : de la gouvernance '
    'stratégique jusqu\'au suivi-évaluation sur le terrain, en passant par la gestion '
    'financière, documentaire, RH et logistique.',
    size=11)

# ══════════════════════════════════════════════════════════════════════════════
# 2. MODULES FONCTIONNELS
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, '2.  MODULES FONCTIONNELS')

pillars = [
    ('PILIER 1 — Gestion des Programmes & Projets', [
        ('Gouvernance',         'Pilotage stratégique, comités de direction, tableaux de bord décisionnels'),
        ('Programmes & Projets','Création et suivi de portefeuille projets, jalons, livrables'),
        ('Planification',       'Gantt, affectation des ressources, budgets prévisionnels'),
        ('Exécution',           'Suivi des tâches, avancement, alertes automatiques'),
        ('Suivi & Évaluation',  'Indicateurs de performance (KPI), rapports de progression'),
    ]),
    ('PILIER 2 — Gestion Financière & Marchés', [
        ('Gestion Financière',  'Comptabilité analytique, décaissements, états financiers'),
        ('Marchés Publics',     'Appels d\'offres, dépouillement, contrats, suivi des marchés'),
        ('Partenaires & Bailleurs','Gestion des conventions, rapports bailleurs, tableaux de flux'),
    ]),
    ('PILIER 3 — Administration & Courrier', [
        ('Courrier Administratif','Réception, enregistrement, affectation, traçabilité complète'),
        ('Courrier Intelligent', 'Classement automatique, OCR, extraction de données par IA'),
        ('GED',                  'Gestion électronique de documents, coffre-fort numérique chiffré AES-256'),
    ]),
    ('PILIER 4 — Ressources Humaines & Terrain', [
        ('RH Projet',  'Agents, congés, absences, présences, organigramme'),
        ('Mobile Terrain','Application mobile, synchronisation hors-ligne'),
        ('Diligences', 'Suivi des diligences, assignation, commentaires, instructions'),
        ('Événements', 'Agenda institutionnel, réunions, compte-rendus'),
    ]),
    ('PILIER 5 — Technologies Avancées', [
        ('Intelligence Artificielle','Analyse prédictive, aide à la décision, chatbot intégré'),
        ('Business Intelligence',    'Tableaux de bord dynamiques, graphiques interactifs, exports'),
        ('SIG',                      'Cartographie des projets, suivi géospatial terrain'),
    ]),
    ('PILIER 6 — Transversal & Qualité', [
        ('Collaboration',     'Messagerie interne, partage de documents, espaces de travail'),
        ('Gestion de la Qualité','Normes, audits, non-conformités, plans d\'amélioration'),
        ('Logistique',        'Parc matériel, véhicules, stocks'),
        ('Capitalisation',    'Base de connaissances, leçons apprises, mémoire institutionnelle'),
    ]),
]

for pillar_title, modules in pillars:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(2)
    add_run(p, pillar_title, bold=True, size=11, color=BLUE_MED)
    styled_table(doc,
                 ['Module', 'Fonctionnalités clés'],
                 modules,
                 col_widths=[5, 12])

# ══════════════════════════════════════════════════════════════════════════════
# 3. ARCHITECTURE TECHNIQUE
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, '3.  ARCHITECTURE TECHNIQUE')
styled_table(doc,
    ['Composant', 'Technologie'],
    [
        ('Backend',              'Django 6 / Django REST Framework'),
        ('Base de données',      'PostgreSQL'),
        ('Authentification',     'JWT (tokens) + 2FA (TOTP)'),
        ('Tâches asynchrones',   'Celery + Redis'),
        ('Stockage fichiers',    'Django Storages (cloud-compatible)'),
        ('Sécurité documents',   'Chiffrement AES-256-GCM'),
        ('OCR & extraction',     'PyMuPDF + Tesseract'),
        ('Cartographie',         'SIG intégré'),
        ('Documentation API',    'OpenAPI / Swagger (drf-spectacular)'),
        ('Déploiement',          'Linux / Gunicorn / Nginx'),
    ],
    col_widths=[6, 11])

# ══════════════════════════════════════════════════════════════════════════════
# 4. POINTS FORTS
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, '4.  POINTS FORTS DE LA SOLUTION')
points = [
    ('Solution 100 % intégrée',    'Toutes les fonctions métier dans un seul système unifié.'),
    ('Interface API REST',          'Intégration facile avec les systèmes existants.'),
    ('Sécurité renforcée',          'Authentification double facteur, chiffrement AES-256 des documents sensibles.'),
    ('IA embarquée',               'Automatisation du traitement documentaire et aide à la décision.'),
    ('Mobile-first',               'Accès terrain depuis smartphone, même sans connexion internet.'),
    ('Tableaux de bord temps réel','Visibilité instantanée sur l\'ensemble du portefeuille projets.'),
    ('Conformité bailleurs',       'Rapports et indicateurs adaptés aux exigences des bailleurs internationaux.'),
]
for title, desc in points:
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    add_run(p, f'{title} : ', bold=True, size=11, color=BLUE_DARK)
    add_run(p, desc, size=11)

# ══════════════════════════════════════════════════════════════════════════════
# 5. PROPOSITION TARIFAIRE
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, '5.  PROPOSITION TARIFAIRE')
styled_table(doc,
    ['Prestation', 'Détail', 'Montant'],
    [
        ('Licence logicielle',        'Solution complète 18 modules',                        'Sur devis'),
        ('Déploiement & configuration','Installation, paramétrage, migration des données',   'Sur devis'),
        ('Formation',                 'Administrateurs + utilisateurs finaux (3 jours)',      'Sur devis'),
        ('Maintenance annuelle',      'Mises à jour, support technique, hébergement',        'Sur devis'),
        ('Développements spécifiques','Modules sur mesure selon besoins complémentaires',    'Sur devis'),
    ],
    col_widths=[5, 9, 3])

note = doc.add_paragraph()
add_run(note,
    'Un devis détaillé et personnalisé sera transmis après audit de vos besoins spécifiques.',
    italic=True, size=10, color=BLUE_MED)

# ══════════════════════════════════════════════════════════════════════════════
# 6. PLAN DE MISE EN ŒUVRE
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, '6.  PLAN DE MISE EN ŒUVRE')
styled_table(doc,
    ['Phase', 'Période', 'Activités'],
    [
        ('Phase 1 – Cadrage',      'Semaines 1–2',  'Audit des besoins, recueil des données existantes'),
        ('Phase 2 – Déploiement',  'Semaines 3–4',  'Infrastructure, configuration serveur et paramétrage'),
        ('Phase 3 – Migration',    'Semaines 5–6',  'Migration et validation des données'),
        ('Phase 4 – Formation',    'Semaines 7–8',  'Formation administrateurs et utilisateurs finaux'),
        ('Phase 5 – Recette',      'Semaine 9',     'Tests, corrections, validation client'),
        ('Phase 6 – Production',   'Semaine 10',    'Mise en production et suivi post-déploiement'),
    ],
    col_widths=[4.5, 3, 9.5])

# ══════════════════════════════════════════════════════════════════════════════
# 7. GARANTIES & SUPPORT
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, '7.  GARANTIES & SUPPORT')
styled_table(doc,
    ['Engagement', 'Valeur'],
    [
        ('Horaires support',           '5j/7 – 8h à 18h'),
        ('Délai réponse incidents critiques', '< 4 heures'),
        ('Mises à jour de sécurité',   'Incluses dans la maintenance'),
        ('Sauvegardes automatiques',   'Quotidiennes'),
        ('Disponibilité (SLA)',        '99,5 %'),
    ],
    col_widths=[8, 9])

# ══════════════════════════════════════════════════════════════════════════════
# 8. CONTACT
# ══════════════════════════════════════════════════════════════════════════════
heading(doc, '8.  CONTACT')
styled_table(doc,
    ['', ''],
    [
        ('Email',             'franckalain.ai@gmail.com'),
        ('Référence dossier', 'OC-2026-001'),
    ],
    col_widths=[5, 12])

doc.add_paragraph()
closing = doc.add_paragraph()
closing.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run(closing,
    'Cette offre est confidentielle et établie à l\'attention exclusive du destinataire.\n'
    'Validité : 30 jours à compter de la date d\'émission.',
    italic=True, size=10, color=BLUE_MED)

# ── Sauvegarde ────────────────────────────────────────────────────────────────
output = 'OFFRE_COMMERCIALE.docx'
doc.save(output)
print(f'OK  Fichier genere : {output}')
