"""
Tâches Celery — Module Courrier Intelligent
  - sync_tous_comptes  : synchronise IMAP/POP3 de tous les comptes actifs (toutes les 5 min)
  - sync_compte_email  : synchronise un compte spécifique (déclenché à la demande)
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name='courrier_intelligent.sync_tous_comptes')
def sync_tous_comptes(self):
    """Synchronise tous les comptes email actifs (IMAP + POP3)."""
    from .models import CompteEmail
    from .services import sync_compte

    comptes = CompteEmail.objects.filter(statut__in=['actif', 'erreur'])
    total_new = 0
    errors = []

    for compte in comptes:
        try:
            result = sync_compte(compte)
            nb = result.get('nb_new', 0)
            total_new += nb
            if nb:
                logger.info(f"[SYNC] {compte.adresse_email} : {nb} nouveau(x) email(s)")
        except Exception as exc:
            logger.error(f"[SYNC] Erreur {compte.adresse_email} : {exc}")
            errors.append(str(exc))

    logger.info(f"[SYNC] Terminé — {total_new} email(s) importé(s) sur {comptes.count()} compte(s)")
    return {'nb_new': total_new, 'errors': errors}


@shared_task(bind=True, max_retries=2, default_retry_delay=30, name='courrier_intelligent.sync_compte_email')
def sync_compte_email(self, compte_id):
    """Synchronise un compte email spécifique."""
    from .models import CompteEmail
    from .services import sync_compte

    try:
        compte = CompteEmail.objects.get(id=compte_id)
        result = sync_compte(compte)
        logger.info(f"[SYNC] {compte.adresse_email} : {result}")
        return result
    except CompteEmail.DoesNotExist:
        logger.error(f"[SYNC] Compte {compte_id} introuvable")
        return {'success': False, 'message': 'Compte introuvable'}
    except Exception as exc:
        logger.error(f"[SYNC] Erreur compte {compte_id} : {exc}")
        raise self.retry(exc=exc)
