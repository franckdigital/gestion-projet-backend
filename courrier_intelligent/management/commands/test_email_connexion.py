"""
Commande de test de connexion email (SMTP + IMAP)
Usage : python manage.py test_email_connexion
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Teste la connexion SMTP et IMAP de tous les comptes email"

    def handle(self, *args, **options):
        from courrier_intelligent.models import CompteEmail
        from courrier_intelligent.services import tester_connexion

        comptes = CompteEmail.objects.all()
        if not comptes.exists():
            self.stderr.write("Aucun compte email configure.")
            self.stderr.write("Lancez : python manage.py seed_comptes_email")
            return

        for compte in comptes:
            self.stdout.write(f"\nTest compte : {compte.adresse_email} ({compte.get_type_compte_display()})")
            self.stdout.write(f"  Nom : {compte.nom_affichage}")

            if not compte.mot_de_passe:
                self.stdout.write(self.style.WARNING("  Mot de passe non configure — test ignore"))
                continue

            resultat = tester_connexion(compte)

            smtp_ok = resultat.get('smtp', False)
            imap_ok = resultat.get('imap', False)

            self.stdout.write(
                f"  SMTP : " + (self.style.SUCCESS("OK") if smtp_ok else self.style.ERROR("ECHEC"))
            )
            self.stdout.write(
                f"  IMAP : " + (self.style.SUCCESS("OK") if imap_ok else self.style.ERROR("ECHEC"))
            )
            self.stdout.write(f"  Detail : {resultat.get('details', '')}")

            if not resultat.get('success'):
                self.stdout.write(self.style.WARNING(
                    "\n  Verifiez que :"
                    "\n  - L'acces IMAP est active dans Gmail (Parametres > Transfert et POP/IMAP)"
                    "\n  - L'App Password est correct (16 caracteres sans espaces)"
                    "\n  - La validation en 2 etapes est activee sur le compte Google"
                ))
