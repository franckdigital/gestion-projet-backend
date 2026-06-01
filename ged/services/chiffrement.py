"""
Service de chiffrement AES-256-GCM pour le coffre-fort numérique.

Architecture de clés :
  - Chaque BoiteArchive chiffrée possède une clé AES-256 unique (cle_document).
  - Cette clé est elle-même chiffrée par une clé maître dérivée du SECRET_KEY Django
    via PBKDF2-HMAC-SHA256 (key wrapping).
  - La clé wrappée est stockée en base64 dans BoiteArchive.cle_chiffrement.
  - Les fichiers sont chiffrés avec AES-256-GCM (authentifié, nonce unique par fichier).

Format du payload chiffré stocké en fichier :
  [ nonce (12 octets) | tag (16 octets inclus dans ciphertext GCM) | ciphertext ]
"""
import os
import base64
import hashlib
import secrets
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Nombre d'itérations PBKDF2 pour dériver la clé maître
_PBKDF2_ITERATIONS = 260_000
_SALT_MASTER = b'ged-coffre-fort-numerique-v1'  # sel statique pour dérivation maître


def _master_key() -> bytes:
    """Clé maître 256 bits dérivée du SECRET_KEY Django. Stable pour toute l'appli."""
    return hashlib.pbkdf2_hmac(
        'sha256',
        settings.SECRET_KEY.encode('utf-8'),
        _SALT_MASTER,
        iterations=_PBKDF2_ITERATIONS,
        dklen=32,
    )


def _aesgcm(cle: bytes):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return AESGCM(cle)


# ─── Gestion des clés de boîte ───────────────────────────────────────────────

def generer_cle_boite() -> str:
    """
    Génère une clé AES-256 aléatoire pour une BoiteArchive et la retourne
    chiffrée (wrappée) par la clé maître, encodée en base64.

    Format du blob : nonce(12) + ciphertext_de_la_cle_brute(32+16)
    """
    cle_brute = secrets.token_bytes(32)          # Clé AES-256 du document
    nonce = secrets.token_bytes(12)               # Nonce GCM 96 bits
    cle_chiffree = _aesgcm(_master_key()).encrypt(nonce, cle_brute, None)
    payload = nonce + cle_chiffree               # 12 + 48 = 60 octets
    return base64.b64encode(payload).decode('ascii')


def _recuperer_cle_boite(cle_b64: str) -> bytes:
    """Déchiffre et retourne la clé AES-256 brute d'une BoiteArchive."""
    try:
        payload = base64.b64decode(cle_b64)
        nonce = payload[:12]
        cle_chiffree = payload[12:]
        return _aesgcm(_master_key()).decrypt(nonce, cle_chiffree, None)
    except Exception as e:
        raise ValueError(f'Impossible de récupérer la clé de chiffrement : {e}') from e


# ─── Chiffrement / Déchiffrement de fichiers ─────────────────────────────────

def chiffrer_fichier(cle_boite_b64: str, contenu: bytes) -> bytes:
    """
    Chiffre le contenu d'un fichier avec AES-256-GCM.

    Returns:
        Payload = nonce(12) + ciphertext_avec_tag_GCM
    """
    cle = _recuperer_cle_boite(cle_boite_b64)
    nonce = secrets.token_bytes(12)
    chiffre = _aesgcm(cle).encrypt(nonce, contenu, None)
    return nonce + chiffre  # nonce en tête pour le déchiffrement


def dechiffrer_fichier(cle_boite_b64: str, payload_chiffre: bytes) -> bytes:
    """
    Déchiffre un payload produit par `chiffrer_fichier`.

    Raises:
        ValueError si le payload est invalide ou corrompu (intégrité GCM échouée).
    """
    if len(payload_chiffre) < 28:  # 12 nonce + 16 tag minimum
        raise ValueError('Payload chiffré trop court')
    cle = _recuperer_cle_boite(cle_boite_b64)
    nonce = payload_chiffre[:12]
    chiffre = payload_chiffre[12:]
    try:
        return _aesgcm(cle).decrypt(nonce, chiffre, None)
    except Exception as e:
        raise ValueError(f'Déchiffrement échoué — intégrité compromise : {e}') from e


# ─── Utilitaires ─────────────────────────────────────────────────────────────

def empreinte_sha256(contenu: bytes) -> str:
    """SHA-256 du contenu en clair (calculé avant chiffrement)."""
    return hashlib.sha256(contenu).hexdigest()
