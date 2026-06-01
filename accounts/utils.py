import re
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


PASSWORD_REGEX = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&+\-_#])[A-Za-z\d@$!%*?&+\-_#]{8,}$'
)


def validate_password_strength(password):
    errors = []
    if len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères.")
    if not re.search(r'[A-Z]', password):
        errors.append("Le mot de passe doit contenir au moins une majuscule.")
    if not re.search(r'[a-z]', password):
        errors.append("Le mot de passe doit contenir au moins une minuscule.")
    if not re.search(r'\d', password):
        errors.append("Le mot de passe doit contenir au moins un chiffre.")
    if not re.search(r'[@$!%*?&+\-_#]', password):
        errors.append("Le mot de passe doit contenir au moins un caractère spécial (@$!%*?&+-_#).")
    return errors


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def send_otp_email(user, otp_code):
    subject = f"[ERP Projets] Code de vérification : {otp_code.code}"
    message = (
        f"Bonjour {user.get_full_name()},\n\n"
        f"Votre code de vérification est : {otp_code.code}\n\n"
        f"Ce code est valide pendant 10 minutes.\n\n"
        f"Si vous n'avez pas initié cette connexion, ignorez ce message."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@erp-projets.ci'),
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_password_reset_email(user, reset_token, base_url='http://localhost:5173'):
    reset_url = f"{base_url}/reset-password/{reset_token.token}"
    subject = "[ERP Projets] Réinitialisation de votre mot de passe"
    message = (
        f"Bonjour {user.get_full_name()},\n\n"
        f"Vous avez demandé une réinitialisation de mot de passe.\n\n"
        f"Cliquez sur le lien suivant pour réinitialiser votre mot de passe :\n{reset_url}\n\n"
        f"Ce lien est valide pendant 2 heures.\n\n"
        f"Si vous n'avez pas effectué cette demande, ignorez ce message."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@erp-projets.ci'),
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_account_locked_email(user):
    subject = "[ERP Projets] Compte temporairement verrouillé"
    message = (
        f"Bonjour {user.get_full_name()},\n\n"
        f"Votre compte a été temporairement verrouillé suite à plusieurs tentatives de connexion échouées.\n\n"
        f"Il sera automatiquement déverrouillé après 30 minutes.\n\n"
        f"Si vous n'êtes pas à l'origine de ces tentatives, contactez votre administrateur."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@erp-projets.ci'),
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_new_login_notification(user, ip, user_agent):
    subject = "[ERP Projets] Nouvelle connexion détectée"
    message = (
        f"Bonjour {user.get_full_name()},\n\n"
        f"Une nouvelle connexion a été détectée sur votre compte.\n\n"
        f"Adresse IP : {ip}\n"
        f"Navigateur : {user_agent[:100]}\n\n"
        f"Si ce n'est pas vous, changez votre mot de passe immédiatement."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@erp-projets.ci'),
        recipient_list=[user.email],
        fail_silently=True,
    )
