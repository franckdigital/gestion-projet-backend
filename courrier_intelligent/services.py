"""
Service email : envoi SMTP + synchronisation IMAP/POP3
Auto-detection des serveurs en fonction du domaine de l'expediteur.
Supporte : Gmail, Outlook/Hotmail, Yahoo, Office 365, serveurs custom.
"""
import imaplib
import poplib
import smtplib
import email as email_lib
import ssl
import logging
from datetime import datetime, timezone
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from django.utils import timezone as dj_tz

logger = logging.getLogger(__name__)

# ─── Fournisseurs connus (auto-detection par domaine) ─────────────────────────

SMTP_PROVIDERS = {
    # Google
    'gmail.com':         {'host': 'smtp.gmail.com',            'port': 587, 'tls': True},
    'googlemail.com':    {'host': 'smtp.gmail.com',            'port': 587, 'tls': True},
    'google.com':        {'host': 'smtp.gmail.com',            'port': 587, 'tls': True},
    # Microsoft
    'outlook.com':       {'host': 'smtp-mail.outlook.com',     'port': 587, 'tls': True},
    'hotmail.com':       {'host': 'smtp-mail.outlook.com',     'port': 587, 'tls': True},
    'hotmail.fr':        {'host': 'smtp-mail.outlook.com',     'port': 587, 'tls': True},
    'live.com':          {'host': 'smtp-mail.outlook.com',     'port': 587, 'tls': True},
    'live.fr':           {'host': 'smtp-mail.outlook.com',     'port': 587, 'tls': True},
    'msn.com':           {'host': 'smtp-mail.outlook.com',     'port': 587, 'tls': True},
    # Yahoo
    'yahoo.com':         {'host': 'smtp.mail.yahoo.com',       'port': 587, 'tls': True},
    'yahoo.fr':          {'host': 'smtp.mail.yahoo.fr',        'port': 587, 'tls': True},
    # Zoho
    'zoho.com':          {'host': 'smtp.zoho.com',             'port': 587, 'tls': True},
    # Hostinger (email pro / domaine personnalise)
    'hostinger.com':     {'host': 'smtp.hostinger.com',        'port': 587, 'tls': True},
    'numerix.digital':   {'host': 'smtp.hostinger.com',        'port': 587, 'tls': True},
    # OVH / mutualisé
    'ovh.net':           {'host': 'ssl0.ovh.net',              'port': 465, 'tls': False, 'ssl': True},
    'ovh.com':           {'host': 'ssl0.ovh.net',              'port': 465, 'tls': False, 'ssl': True},
    # Infomaniak
    'infomaniak.com':    {'host': 'mail.infomaniak.com',       'port': 587, 'tls': True},
    # Office 365 custom domain
    '_office365':        {'host': 'smtp.office365.com',        'port': 587, 'tls': True},
}

IMAP_PROVIDERS = {
    'gmail.com':         {'host': 'imap.gmail.com',            'port': 993, 'ssl': True},
    'googlemail.com':    {'host': 'imap.gmail.com',            'port': 993, 'ssl': True},
    'google.com':        {'host': 'imap.gmail.com',            'port': 993, 'ssl': True},
    'outlook.com':       {'host': 'outlook.office365.com',     'port': 993, 'ssl': True},
    'hotmail.com':       {'host': 'outlook.office365.com',     'port': 993, 'ssl': True},
    'hotmail.fr':        {'host': 'outlook.office365.com',     'port': 993, 'ssl': True},
    'live.com':          {'host': 'outlook.office365.com',     'port': 993, 'ssl': True},
    'live.fr':           {'host': 'outlook.office365.com',     'port': 993, 'ssl': True},
    'yahoo.com':         {'host': 'imap.mail.yahoo.com',       'port': 993, 'ssl': True},
    'yahoo.fr':          {'host': 'imap.mail.yahoo.fr',        'port': 993, 'ssl': True},
    'zoho.com':          {'host': 'imap.zoho.com',             'port': 993, 'ssl': True},
    # Hostinger (email pro / domaine personnalise)
    'hostinger.com':     {'host': 'imap.hostinger.com',        'port': 993, 'ssl': True},
    'numerix.digital':   {'host': 'imap.hostinger.com',        'port': 993, 'ssl': True},
    # OVH
    'ovh.net':           {'host': 'ssl0.ovh.net',              'port': 993, 'ssl': True},
    'ovh.com':           {'host': 'ssl0.ovh.net',              'port': 993, 'ssl': True},
    # Infomaniak
    'infomaniak.com':    {'host': 'mail.infomaniak.com',       'port': 993, 'ssl': True},
    '_office365':        {'host': 'outlook.office365.com',     'port': 993, 'ssl': True},
}

POP3_PROVIDERS = {
    'gmail.com':         {'host': 'pop.gmail.com',             'port': 995, 'ssl': True},
    'googlemail.com':    {'host': 'pop.gmail.com',             'port': 995, 'ssl': True},
    'outlook.com':       {'host': 'outlook.office365.com',     'port': 995, 'ssl': True},
    'hotmail.com':       {'host': 'outlook.office365.com',     'port': 995, 'ssl': True},
    'yahoo.com':         {'host': 'pop.mail.yahoo.com',        'port': 995, 'ssl': True},
    # Hostinger
    'hostinger.com':     {'host': 'pop.hostinger.com',         'port': 995, 'ssl': True},
    'numerix.digital':   {'host': 'pop.hostinger.com',         'port': 995, 'ssl': True},
    # OVH
    'ovh.net':           {'host': 'ssl0.ovh.net',              'port': 995, 'ssl': True},
    '_office365':        {'host': 'outlook.office365.com',     'port': 995, 'ssl': True},
}


def _get_domain(email_address: str) -> str:
    """Extrait le domaine d'une adresse email."""
    if not email_address or '@' not in email_address:
        return ''
    return email_address.split('@')[-1].lower().strip()


def detect_smtp_config(email_address: str) -> dict:
    """
    Auto-detecte la configuration SMTP selon le domaine de l'adresse.
    Retourne un dict {host, port, tls, ssl} ou {} si inconnu.
    """
    domain = _get_domain(email_address)
    if domain in SMTP_PROVIDERS:
        return SMTP_PROVIDERS[domain]
    # Domaines Office 365 custom (organisation.com utilisant Microsoft 365)
    # On ne peut pas detecter automatiquement, on retourne la config par defaut O365
    return {}


def detect_imap_config(email_address: str) -> dict:
    domain = _get_domain(email_address)
    return IMAP_PROVIDERS.get(domain, {})


def detect_pop3_config(email_address: str) -> dict:
    domain = _get_domain(email_address)
    return POP3_PROVIDERS.get(domain, {})


def get_server_config_for_compte(compte) -> dict:
    """
    Construit la config complete pour un CompteEmail.
    Priorite : champs renseignes dans le modele > auto-detection.

    Convention du modele :
      ssl_sortant=False  → STARTTLS (port 587, standard Gmail/Outlook)
      ssl_sortant=True   → SSL direct (port 465, OVH, certains serveurs)
    """
    smtp_auto = detect_smtp_config(compte.adresse_email)
    imap_auto = detect_imap_config(compte.adresse_email)

    # Si serveur manuel renseigne : ssl_sortant=False → STARTTLS, True → SSL direct
    # Si auto-detecte : utiliser la config du fournisseur
    if compte.serveur_sortant:
        smtp_tls = not compte.ssl_sortant   # False(STARTTLS)→tls=True, True(SSL)→tls=False
        smtp_ssl = compte.ssl_sortant        # False(STARTTLS)→ssl=False, True(SSL)→ssl=True
    else:
        smtp_tls = smtp_auto.get('tls', True)
        smtp_ssl = smtp_auto.get('ssl', False)

    # Pour port 587 sans SSL direct : forcer STARTTLS
    smtp_port = compte.port_sortant or smtp_auto.get('port', 587)
    if smtp_port == 587:
        smtp_tls = True
        smtp_ssl = False
    elif smtp_port == 465:
        smtp_tls = False
        smtp_ssl = True

    return {
        'smtp_host':   compte.serveur_sortant  or smtp_auto.get('host', ''),
        'smtp_port':   smtp_port,
        'smtp_tls':    smtp_tls,
        'smtp_ssl':    smtp_ssl,
        'imap_host':   compte.serveur_entrant  or imap_auto.get('host', ''),
        'imap_port':   compte.port_entrant      or imap_auto.get('port', 993),
        'imap_ssl':    compte.ssl_entrant if compte.serveur_entrant else imap_auto.get('ssl', True),
        'identifiant': compte.identifiant       or compte.adresse_email,
        'password':    getattr(compte, 'mot_de_passe', '') or '',
    }


# ─── SERVICE SMTP (envoi) ─────────────────────────────────────────────────────

class SmtpSender:
    """Envoie un email via SMTP avec la configuration du CompteEmail."""

    def __init__(self, compte):
        self.compte = compte
        self.cfg = get_server_config_for_compte(compte)

    def _build_message(self, email_obj) -> MIMEMultipart:
        """Construit le message MIME depuis un objet Email Django."""
        from email.utils import make_msgid
        msg = MIMEMultipart('alternative')
        msg['Subject'] = email_obj.sujet or ''
        msg['From']    = f"{email_obj.expediteur} <{email_obj.expediteur_email}>" if email_obj.expediteur else email_obj.expediteur_email
        destinataires = email_obj.destinataires or []
        msg['To']      = ', '.join(destinataires) if isinstance(destinataires, list) else destinataires

        cc = email_obj.destinataires_cc or []
        if cc:
            msg['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc

        # Message-ID persistant pour permettre le threading côté client
        if not email_obj.message_id:
            domain = email_obj.expediteur_email.split('@')[-1] if '@' in (email_obj.expediteur_email or '') else 'erp.local'
            email_obj.message_id = make_msgid(domain=domain)
            email_obj.save(update_fields=['message_id'])
        msg['Message-ID'] = email_obj.message_id

        # En-têtes de threading si c'est une réponse
        if email_obj.en_reponse_a and email_obj.en_reponse_a.message_id:
            parent_mid = email_obj.en_reponse_a.message_id
            msg['In-Reply-To'] = parent_mid
            msg['References']  = parent_mid

        if email_obj.corps_texte:
            msg.attach(MIMEText(email_obj.corps_texte, 'plain', 'utf-8'))
        if email_obj.corps_html:
            msg.attach(MIMEText(email_obj.corps_html, 'html', 'utf-8'))

        # Pièces jointes
        for pj in email_obj.pieces_jointes.all():
            if pj.fichier:
                try:
                    part = MIMEBase('application', 'octet-stream')
                    pj.fichier.seek(0)
                    part.set_payload(pj.fichier.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{pj.nom_fichier}"')
                    msg.attach(part)
                except Exception as e:
                    logger.warning(f"PJ ignorée ({pj.nom_fichier}) : {e}")

        return msg

    def send(self, email_obj) -> dict:
        """
        Envoie l'email. Retourne {'success': True/False, 'message': str}.
        """
        cfg = self.cfg
        if not cfg['smtp_host']:
            return {'success': False, 'message': 'Serveur SMTP non configuré.'}
        if not cfg['password']:
            return {'success': False, 'message': 'Mot de passe non renseigné pour ce compte.'}

        try:
            msg = self._build_message(email_obj)
            all_recipients = list(email_obj.destinataires or [])
            all_recipients += list(email_obj.destinataires_cc or [])
            all_recipients += list(email_obj.destinataires_cci or [])

            if cfg.get('smtp_ssl'):
                # SSL direct (port 465)
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(cfg['smtp_host'], cfg['smtp_port'], context=context) as server:
                    server.login(cfg['identifiant'], cfg['password'])
                    server.sendmail(email_obj.expediteur_email, all_recipients, msg.as_string())
            else:
                # STARTTLS (port 587)
                with smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=30) as server:
                    server.ehlo()
                    if cfg.get('smtp_tls', True):
                        server.starttls()
                        server.ehlo()
                    server.login(cfg['identifiant'], cfg['password'])
                    server.sendmail(email_obj.expediteur_email, all_recipients, msg.as_string())

            logger.info(f"Email envoyé : {email_obj.sujet} → {all_recipients}")
            return {'success': True, 'message': 'Email envoyé avec succès.'}

        except smtplib.SMTPAuthenticationError:
            return {'success': False, 'message': 'Authentification SMTP échouée. Vérifiez identifiant/mot de passe.'}
        except smtplib.SMTPConnectError:
            return {'success': False, 'message': f'Connexion SMTP impossible ({cfg["smtp_host"]}:{cfg["smtp_port"]}).'}
        except Exception as e:
            logger.error(f"Erreur envoi email : {e}")
            return {'success': False, 'message': str(e)}


# ─── SERVICE IMAP (synchronisation) ──────────────────────────────────────────

class ImapSyncService:
    """Synchronise les emails entrants depuis un serveur IMAP."""

    def __init__(self, compte):
        self.compte = compte
        self.cfg = get_server_config_for_compte(compte)

    def _decode_header_value(self, value) -> str:
        if not value:
            return ''
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result.append(part.decode(charset or 'utf-8', errors='replace'))
                except Exception:
                    result.append(part.decode('latin-1', errors='replace'))
            else:
                result.append(str(part))
        return ' '.join(result)

    def _extract_body(self, msg) -> tuple[str, str, list]:
        """Retourne (texte_plain, html, pieces_jointes).
        pieces_jointes = liste de dicts {nom, type_mime, data: bytes}
        """
        plain, html, attachments = '', '', []
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                cd = str(part.get('Content-Disposition', ''))
                filename_raw = part.get_filename()
                filename = self._decode_header_value(filename_raw) if filename_raw else None

                if filename or 'attachment' in cd:
                    try:
                        data = part.get_payload(decode=True)
                        if data:
                            attachments.append({
                                'nom': filename or 'fichier',
                                'type_mime': ct,
                                'data': data,
                            })
                    except Exception:
                        pass
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    charset = part.get_content_charset() or 'utf-8'
                    text = payload.decode(charset, errors='replace')
                    if ct == 'text/plain' and not plain:
                        plain = text
                    elif ct == 'text/html' and not html:
                        html = text
                except Exception:
                    pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                content = payload.decode(charset, errors='replace') if payload else ''
                if msg.get_content_type() == 'text/html':
                    html = content
                else:
                    plain = content
            except Exception:
                pass
        return plain, html, attachments

    def _parse_date(self, date_str) -> datetime:
        if not date_str:
            return dj_tz.now()
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return dj_tz.now()

    def sync(self, mailbox='INBOX', limit=50) -> dict:
        """
        Synchronise les emails non lus depuis IMAP.
        Retourne {'success': bool, 'nb_new': int, 'message': str}.
        """
        from .models import Email as EmailModel
        cfg = self.cfg

        if not cfg['imap_host']:
            return {'success': False, 'nb_new': 0, 'message': 'Serveur IMAP non configuré.'}
        if not cfg['password']:
            return {'success': False, 'nb_new': 0, 'message': 'Mot de passe manquant.'}

        nb_new = 0
        try:
            if cfg['imap_ssl']:
                M = imaplib.IMAP4_SSL(cfg['imap_host'], cfg['imap_port'])
            else:
                M = imaplib.IMAP4(cfg['imap_host'], cfg['imap_port'])
                M.starttls()

            M.login(cfg['identifiant'], cfg['password'])
            M.select(mailbox)

            # Chercher les non lus
            _, data = M.search(None, 'UNSEEN')
            ids = data[0].split() if data[0] else []
            ids = ids[-limit:]  # Limiter aux N derniers

            for uid in ids:
                _, msg_data = M.fetch(uid, '(RFC822)')
                raw = msg_data[0][1] if msg_data and msg_data[0] else None
                if not raw:
                    continue

                msg = email_lib.message_from_bytes(raw)
                sujet      = self._decode_header_value(msg.get('Subject', ''))
                from_raw   = self._decode_header_value(msg.get('From', ''))
                msg_id     = msg.get('Message-ID', '').strip()
                in_reply_to= msg.get('In-Reply-To', '').strip().strip('<>').strip()
                references = msg.get('References', '').strip()
                date_str   = msg.get('Date', '')
                plain, html, pj_list = self._extract_body(msg)

                # Extraire email expéditeur
                exp_email, exp_nom = '', ''
                if '<' in from_raw and '>' in from_raw:
                    exp_nom   = from_raw.split('<')[0].strip().strip('"')
                    exp_email = from_raw.split('<')[1].rstrip('>')
                else:
                    exp_email = from_raw.strip()

                date_reception = self._parse_date(date_str)

                # Eviter les doublons
                if msg_id and EmailModel.objects.filter(message_id=msg_id).exists():
                    continue

                # Liaison au fil de discussion via In-Reply-To / References
                import uuid as _uuid
                en_reponse_a = None
                thread_id = ''

                ref_ids = []
                if in_reply_to:
                    ref_ids.append(in_reply_to)
                if references:
                    ref_ids += [r.strip().strip('<>') for r in references.split() if r.strip()]

                for ref_id in ref_ids:
                    parent = EmailModel.objects.filter(message_id__icontains=ref_id).first()
                    if parent:
                        en_reponse_a = parent
                        thread_id = parent.thread_id or ''
                        if not thread_id:
                            thread_id = str(_uuid.uuid4())
                            parent.thread_id = thread_id
                            parent.save(update_fields=['thread_id'])
                        break

                email_obj = EmailModel.objects.create(
                    compte=self.compte,
                    direction='entrant',
                    message_id=msg_id or '',
                    sujet=sujet or '(Sans objet)',
                    corps_texte=plain,
                    corps_html=html,
                    expediteur=exp_nom,
                    expediteur_email=exp_email,
                    destinataires=[self.compte.adresse_email],
                    date_reception=date_reception,
                    en_reponse_a=en_reponse_a,
                    thread_id=thread_id,
                    statut='non_lu',
                    est_lu=False,
                    priorite='normale',
                    cree_par=self.compte.utilisateur,
                )

                # Sauvegarder les pièces jointes
                for pj in pj_list:
                    try:
                        from django.core.files.base import ContentFile
                        from .models import PieceJointeEmail
                        pj_obj = PieceJointeEmail(
                            email=email_obj,
                            nom_fichier=pj['nom'],
                            type_mime=pj['type_mime'],
                            taille=len(pj['data']),
                        )
                        pj_obj.fichier.save(pj['nom'], ContentFile(pj['data']), save=True)
                    except Exception as pj_err:
                        logger.warning(f"PJ ignorée ({pj.get('nom')}) : {pj_err}")

                nb_new += 1
                # Marquer comme lu sur le serveur
                M.store(uid, '+FLAGS', '\\Seen')

            M.logout()

            # Mettre à jour derniere_synchro
            self.compte.derniere_synchro = dj_tz.now()
            self.compte.statut = 'actif'
            self.compte.save(update_fields=['derniere_synchro', 'statut'])

            return {'success': True, 'nb_new': nb_new, 'message': f'{nb_new} nouveau(x) email(s) importé(s).'}

        except imaplib.IMAP4.error as e:
            self.compte.statut = 'erreur'
            self.compte.save(update_fields=['statut'])
            return {'success': False, 'nb_new': 0, 'message': f'Erreur IMAP : {e}'}
        except ConnectionRefusedError:
            return {'success': False, 'nb_new': 0, 'message': f'Connexion refusée ({cfg["imap_host"]}:{cfg["imap_port"]}).'}
        except Exception as e:
            logger.error(f"Erreur sync IMAP : {e}")
            return {'success': False, 'nb_new': 0, 'message': str(e)}


# ─── SERVICE POP3 (synchronisation) ──────────────────────────────────────────

class Pop3SyncService:
    """Synchronise les emails entrants depuis un serveur POP3."""

    def __init__(self, compte):
        self.compte = compte
        self.cfg = get_server_config_for_compte(compte)

    def sync(self, limit=50) -> dict:
        from .models import Email as EmailModel
        cfg = self.cfg
        pop_cfg = detect_pop3_config(self.compte.adresse_email)

        pop_host = cfg['imap_host'] or pop_cfg.get('host', '')
        pop_port = pop_cfg.get('port', 995)
        pop_ssl  = pop_cfg.get('ssl', True)

        if not pop_host:
            return {'success': False, 'nb_new': 0, 'message': 'Serveur POP3 non configuré.'}
        if not cfg['password']:
            return {'success': False, 'nb_new': 0, 'message': 'Mot de passe manquant.'}

        nb_new = 0
        try:
            if pop_ssl:
                M = poplib.POP3_SSL(pop_host, pop_port)
            else:
                M = poplib.POP3(pop_host, pop_port)

            M.user(cfg['identifiant'])
            M.pass_(cfg['password'])

            nb_total = len(M.list()[1])
            start = max(1, nb_total - limit + 1)

            for i in range(start, nb_total + 1):
                raw_lines = M.retr(i)[1]
                raw_bytes = b'\n'.join(raw_lines)
                msg = email_lib.message_from_bytes(raw_bytes)

                msg_id = msg.get('Message-ID', '').strip()
                if msg_id and EmailModel.objects.filter(message_id=msg_id).exists():
                    continue

                from email.header import decode_header as dh

                def dh_str(v):
                    if not v:
                        return ''
                    parts = dh(v)
                    res = []
                    for part, cs in parts:
                        if isinstance(part, bytes):
                            res.append(part.decode(cs or 'utf-8', errors='replace'))
                        else:
                            res.append(str(part))
                    return ' '.join(res)

                sujet     = dh_str(msg.get('Subject', ''))
                from_raw  = dh_str(msg.get('From', ''))
                exp_email, exp_nom = '', ''
                if '<' in from_raw:
                    exp_nom   = from_raw.split('<')[0].strip().strip('"')
                    exp_email = from_raw.split('<')[1].rstrip('>')
                else:
                    exp_email = from_raw.strip()

                plain = ''
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain':
                            try:
                                plain = part.get_payload(decode=True).decode(
                                    part.get_content_charset() or 'utf-8', errors='replace')
                                break
                            except Exception:
                                pass
                else:
                    try:
                        plain = msg.get_payload(decode=True).decode(
                            msg.get_content_charset() or 'utf-8', errors='replace') or ''
                    except Exception:
                        pass

                EmailModel.objects.create(
                    compte=self.compte,
                    direction='entrant',
                    message_id=msg_id or '',
                    sujet=sujet or '(Sans objet)',
                    corps_texte=plain,
                    expediteur=exp_nom,
                    expediteur_email=exp_email,
                    destinataires=[self.compte.adresse_email],
                    date_reception=dj_tz.now(),
                    statut='non_lu',
                    est_lu=False,
                    priorite='normale',
                    cree_par=self.compte.utilisateur,
                )
                nb_new += 1

            M.quit()
            self.compte.derniere_synchro = dj_tz.now()
            self.compte.statut = 'actif'
            self.compte.save(update_fields=['derniere_synchro', 'statut'])

            return {'success': True, 'nb_new': nb_new, 'message': f'{nb_new} email(s) importé(s) via POP3.'}

        except poplib.error_proto as e:
            self.compte.statut = 'erreur'
            self.compte.save(update_fields=['statut'])
            return {'success': False, 'nb_new': 0, 'message': f'Erreur POP3 : {e}'}
        except Exception as e:
            logger.error(f"Erreur sync POP3 : {e}")
            return {'success': False, 'nb_new': 0, 'message': str(e)}


# ─── Fonction utilitaire principale ──────────────────────────────────────────

def sync_compte(compte) -> dict:
    """
    Lance la synchronisation adaptee au type de compte.
    Retourne le resultat de la synchronisation.
    """
    if compte.type_compte == 'pop3':
        service = Pop3SyncService(compte)
        return service.sync()
    else:
        # imap, gmail, outlook → tous utilisent IMAP
        service = ImapSyncService(compte)
        return service.sync()


def envoyer_email(compte, email_obj) -> dict:
    """
    Envoie un email via SMTP depuis le compte donne.
    """
    sender = SmtpSender(compte)
    return sender.send(email_obj)


def tester_connexion(compte) -> dict:
    """
    Teste la connexion SMTP et IMAP du compte.
    Retourne {'smtp': bool, 'imap': bool, 'details': str}.
    """
    cfg = get_server_config_for_compte(compte)
    smtp_ok, imap_ok = False, False
    details = []

    # Test SMTP
    if cfg['smtp_host'] and cfg['password']:
        try:
            if cfg.get('smtp_ssl'):
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(cfg['smtp_host'], cfg['smtp_port'], context=ctx, timeout=10) as s:
                    s.login(cfg['identifiant'], cfg['password'])
                    smtp_ok = True
            else:
                with smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'], timeout=10) as s:
                    s.ehlo()
                    if cfg.get('smtp_tls'):
                        s.starttls()
                        s.ehlo()
                    s.login(cfg['identifiant'], cfg['password'])
                    smtp_ok = True
            details.append(f"SMTP ({cfg['smtp_host']}:{cfg['smtp_port']}) : OK")
        except Exception as e:
            details.append(f"SMTP : ERREUR — {e}")
    else:
        details.append("SMTP : non configure (host ou password manquant)")

    # Test IMAP
    if cfg['imap_host'] and cfg['password']:
        try:
            if cfg['imap_ssl']:
                M = imaplib.IMAP4_SSL(cfg['imap_host'], cfg['imap_port'])
            else:
                M = imaplib.IMAP4(cfg['imap_host'], cfg['imap_port'])
            M.login(cfg['identifiant'], cfg['password'])
            M.logout()
            imap_ok = True
            details.append(f"IMAP ({cfg['imap_host']}:{cfg['imap_port']}) : OK")
        except Exception as e:
            details.append(f"IMAP : ERREUR — {e}")
    else:
        details.append("IMAP : non configure (host ou password manquant)")

    return {
        'smtp': smtp_ok,
        'imap': imap_ok,
        'success': smtp_ok or imap_ok,
        'details': ' | '.join(details),
    }
