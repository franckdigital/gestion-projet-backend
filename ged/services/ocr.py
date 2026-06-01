"""
Service OCR — extraction de texte multi-format.

Hiérarchie des backends par type :
  PDF      → PyMuPDF (texte natif) puis pdf2image+Tesseract (PDF scanné)
  Images   → pytesseract (PNG/JPEG/BMP/TIFF/GIF/WEBP)
  Word     → python-docx (.docx) + fallback extraction binaire (.doc)
  Excel    → openpyxl (.xlsx/.xls)
  Texte    → décodage UTF-8/latin-1 (.txt/.csv/.md/.log)
  Autres   → non supporté, retourne chaîne vide sans erreur fatale
"""
import io
import os
import logging

logger = logging.getLogger(__name__)


def extraire_texte(fichier_field) -> dict:
    """
    Extrait le texte d'un fichier Django FieldFile.

    Returns:
        {
            'texte': str,
            'nb_pages': int,
            'methode': str,
            'erreur': str | None,
        }
    """
    if not fichier_field:
        return _vide('aucun_fichier', 'Aucun fichier associé')

    nom = getattr(fichier_field, 'name', '') or ''
    ext = os.path.splitext(nom)[1].lstrip('.').lower()

    try:
        fichier_field.seek(0)
        contenu = fichier_field.read()
        fichier_field.seek(0)
    except Exception as e:
        return _vide('lecture_erreur', str(e))

    if not contenu:
        return _vide('fichier_vide', 'Le fichier est vide')

    if ext == 'pdf':
        return _pdf(contenu)
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif', 'gif', 'webp'):
        return _image(contenu)
    if ext == 'docx':
        return _docx(contenu)
    if ext == 'doc':
        return _doc_binaire(contenu)
    if ext in ('xlsx', 'xls'):
        return _excel(contenu)
    if ext in ('txt', 'csv', 'md', 'rst', 'log', 'xml', 'json', 'html', 'htm'):
        return _texte_brut(contenu)

    return _vide('format_non_supporte', f'Format .{ext} non pris en charge')


# ─── backends ────────────────────────────────────────────────────────────────

def _pdf(contenu: bytes) -> dict:
    # Tentative 1 : extraction texte natif via PyMuPDF
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=contenu, filetype='pdf')
        pages = []
        for page in doc:
            t = page.get_text('text').strip()
            if t:
                pages.append(t)
        doc.close()
        if pages:
            return {'texte': '\n\n'.join(pages), 'nb_pages': len(pages), 'methode': 'pymupdf', 'erreur': None}
        # PDF scanné sans texte natif → fallback Tesseract
        logger.debug('PyMuPDF: PDF sans texte natif, tentative OCR image')
    except ImportError:
        logger.warning('PyMuPDF (fitz) non installé — pip install PyMuPDF')
    except Exception as e:
        logger.warning('PyMuPDF erreur: %s', e)

    # Tentative 2 : PDF scanné via pdf2image + Tesseract
    return _pdf_ocr(contenu)


def _pdf_ocr(contenu: bytes) -> dict:
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
        images = convert_from_bytes(contenu, dpi=200)
        textes = []
        for img in images:
            t = pytesseract.image_to_string(img, lang='fra+eng').strip()
            if t:
                textes.append(t)
        return {
            'texte': '\n\n'.join(textes),
            'nb_pages': len(images),
            'methode': 'tesseract_pdf',
            'erreur': None,
        }
    except ImportError:
        return _vide('indisponible', 'PyMuPDF et pdf2image/pytesseract non installés')
    except Exception as e:
        return _vide('tesseract_pdf_erreur', str(e))


def _image(contenu: bytes) -> dict:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(contenu))
        texte = pytesseract.image_to_string(img, lang='fra+eng').strip()
        return {'texte': texte, 'nb_pages': 1, 'methode': 'tesseract', 'erreur': None}
    except ImportError:
        return _vide('indisponible', 'pytesseract non installé — pip install pytesseract + Tesseract-OCR')
    except Exception as e:
        return _vide('tesseract_erreur', str(e))


def _docx(contenu: bytes) -> dict:
    try:
        import docx
        doc = docx.Document(io.BytesIO(contenu))
        lignes = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        lignes.append(cell.text.strip())
        return {'texte': '\n'.join(lignes), 'nb_pages': 1, 'methode': 'python_docx', 'erreur': None}
    except ImportError:
        return _vide('indisponible', 'python-docx non installé — pip install python-docx')
    except Exception as e:
        return _vide('docx_erreur', str(e))


def _doc_binaire(contenu: bytes) -> dict:
    # .doc ancien format binaire — extraction basique sans antiword
    try:
        texte = contenu.decode('latin-1', errors='ignore')
        # Filtrer les caractères imprimables
        lignes = [l for l in texte.splitlines() if l.strip() and l.isprintable()]
        extrait = ' '.join(lignes)[:5000]
        return {'texte': extrait, 'nb_pages': 1, 'methode': 'doc_binaire_brut', 'erreur': 'Extraction partielle (.doc binaire)'}
    except Exception as e:
        return _vide('doc_binaire_erreur', str(e))


def _excel(contenu: bytes) -> dict:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(contenu), read_only=True, data_only=True)
        lignes = []
        for sheet in wb.worksheets:
            lignes.append(f'[Feuille : {sheet.title}]')
            for row in sheet.iter_rows(values_only=True):
                cellules = [str(c) for c in row if c is not None]
                if cellules:
                    lignes.append(' | '.join(cellules))
        wb.close()
        return {'texte': '\n'.join(lignes), 'nb_pages': len(wb.sheetnames), 'methode': 'openpyxl', 'erreur': None}
    except Exception as e:
        return _vide('excel_erreur', str(e))


def _texte_brut(contenu: bytes) -> dict:
    for enc in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
        try:
            texte = contenu.decode(enc)
            return {'texte': texte, 'nb_pages': 1, 'methode': 'texte_brut', 'erreur': None}
        except UnicodeDecodeError:
            continue
    return _vide('encodage_inconnu', 'Encodage de caractères non reconnu')


def _vide(methode: str, erreur: str) -> dict:
    return {'texte': '', 'nb_pages': 0, 'methode': methode, 'erreur': erreur}
