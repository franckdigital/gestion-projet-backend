"""
Seed : Emails et etiquettes de demonstration -- Module Courrier Intelligent
Reproduit le scenario exact signale par le client :
  - Un email "lien reunion OSC Touba" noye dans un fil "TDR Enabel-GIZ"
  - La meme information correctement envoyee en fil independant

Usage : python manage.py seed_courrier
Prerequis : seed_lot1 (superuser)
"""
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

NOW = timezone.now()


def dt(days=0, hours=0):
    return NOW - timedelta(days=days, hours=hours)


class Command(BaseCommand):
    help = "Cree les emails et etiquettes de demonstration"

    def handle(self, *args, **options):
        from accounts.models import User
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stderr.write("Aucun superuser -- lancez d'abord seed_lot1")
            return

        with transaction.atomic():
            etiquettes = self._seed_etiquettes(admin)
            self._seed_emails(admin, etiquettes)

        self.stdout.write(self.style.SUCCESS(
            "\nSeed courrier intelligent termine avec succes !"
        ))

    # --- Etiquettes -----------------------------------------------------------

    def _seed_etiquettes(self, admin):
        from courrier_intelligent.models import EtiquetteEmail

        etiq_data = [
            ("Reunion",       "#7c3aed"),
            ("Urgent",        "#dc2626"),
            ("Partenaires",   "#0ea5e9"),
            ("Rapport",       "#059669"),
            ("En attente",    "#f59e0b"),
            ("Formation",     "#6d28d9"),
            ("Finance",       "#c2410c"),
            ("Info",          "#64748b"),
            ("OSC Terrain",   "#15803d"),
            ("Interne",       "#6366f1"),
        ]

        created_etiq = {}
        for nom, couleur in etiq_data:
            etiq, created = EtiquetteEmail.objects.get_or_create(
                nom=nom, utilisateur=admin,
                defaults={"couleur": couleur}
            )
            created_etiq[nom] = etiq
            status = "Creee" if created else "Existante"
            self.stdout.write(f"  [Etiquette] {status} -- {nom} ({couleur})")

        return created_etiq

    # --- Emails ---------------------------------------------------------------

    def _seed_emails(self, admin, etiq):
        """
        Scenarios crees :
        A) Le probleme client : fil "TDR Enabel-GIZ" (11 emails)
           dont 1 email "lien reunion OSC" noye dedans (probleme)
        B) La solution : meme info en fil independant (correct)
        C) Emails independants varies (rapports, finances, partenaires)
        D) Un fil de reponse legitime (rapport mensuel)
        """
        from courrier_intelligent.models import Email

        # A) Scenario probleme : fil TDR Enabel-GIZ ----------------------------
        thread_tdr = "THREAD-TDR-ENABEL-GIZ-" + uuid.uuid4().hex[:8]

        tdr_emails = [
            # 1 -- Email initial (entrant)
            dict(
                direction="entrant", sujet="TDR Atelier Enabel - GIZ",
                expediteur="Dr. Moussa Diallo", expediteur_email="m.diallo@enabel.be",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Bonjour,\n\n"
                    "Veuillez trouver ci-joint les TDR de l'atelier de coordination "
                    "Enabel-GIZ prevu pour le mois prochain.\n\n"
                    "Merci de nous confirmer votre participation avant le 15 courant.\n\n"
                    "Cordialement,\nDr. Moussa Diallo\nEnabel Cote d'Ivoire"
                ),
                priorite="normale", statut="lu", est_lu=True,
                date_reception=dt(days=25), score_urgence=20,
            ),
            # 2 -- Reponse (sortant)
            dict(
                direction="sortant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Adjoua KONAN", expediteur_email="coordination@ong-demo.ci",
                destinataires=["m.diallo@enabel.be"],
                corps_texte=(
                    "Bonjour Dr. Diallo,\n\n"
                    "Merci pour l'envoi des TDR. Nous confirmons notre participation.\n\n"
                    "Nous vous ferons parvenir la liste des participants d'ici vendredi.\n\n"
                    "Bien cordialement,\nAdjoua KONAN\nCoordinatrice de Projet"
                ),
                priorite="normale", statut="repondu", est_lu=True,
                date_reception=dt(days=24), score_urgence=10,
            ),
            # 3 -- Retour confirmation (entrant)
            dict(
                direction="entrant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Dr. Moussa Diallo", expediteur_email="m.diallo@enabel.be",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Merci pour votre confirmation. Programme de l'atelier :\n\n"
                    "J1 : Presentation des resultats 2024\n"
                    "J2 : Planification 2025\n"
                    "J3 : Visite terrain\n\n"
                    "Hotel : Sofitel Abidjan -- Salle : Ivoire A"
                ),
                priorite="normale", statut="lu", est_lu=True,
                date_reception=dt(days=22), score_urgence=15,
            ),
            # 4 -- Demande liste participants (entrant)
            dict(
                direction="entrant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Secretariat GIZ", expediteur_email="secretariat@giz.de",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Bonjour,\n\n"
                    "Nous attendons toujours la liste des participants de votre organisation.\n"
                    "Merci de nous la transmettre en urgence.\n\nCordialement"
                ),
                priorite="haute", statut="lu", est_lu=True,
                date_reception=dt(days=20), score_urgence=60,
            ),
            # 5 -- Envoi liste (sortant)
            dict(
                direction="sortant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Adjoua KONAN", expediteur_email="coordination@ong-demo.ci",
                destinataires=["secretariat@giz.de", "m.diallo@enabel.be"],
                corps_texte=(
                    "Bonjour,\n\nCi-joint la liste des 4 participants :\n"
                    "1. Adjoua KONAN -- Coordinatrice\n"
                    "2. Ibrahima TRAORE -- Expert S&E\n"
                    "3. Fatoumata BAMBA -- Finance\n"
                    "4. Kouassi YAPI -- Logistique\n\nBien cordialement"
                ),
                priorite="normale", statut="repondu", est_lu=True,
                date_reception=dt(days=19), score_urgence=20,
            ),
            # 6 -- Confirmation hotel (entrant)
            dict(
                direction="entrant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Dr. Moussa Diallo", expediteur_email="m.diallo@enabel.be",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Parfait. Les chambres sont reservees au nom de votre organisation.\n"
                    "Check-in le dimanche 19h, petit-dejeuner inclus.\n\nA bientot"
                ),
                priorite="normale", statut="lu", est_lu=True,
                date_reception=dt(days=17), score_urgence=10,
            ),
            # 7 -- Demande remboursement transport (sortant)
            dict(
                direction="sortant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Fatoumata BAMBA", expediteur_email="f.bamba@ong-demo.ci",
                destinataires=["m.diallo@enabel.be"],
                corps_texte=(
                    "Bonjour,\n\n"
                    "Pourriez-vous confirmer les modalites de remboursement des frais de transport ?\n\n"
                    "Merci d'avance"
                ),
                priorite="normale", statut="repondu", est_lu=True,
                date_reception=dt(days=15), score_urgence=25,
            ),
            # 8 -- Reponse remboursement (entrant)
            dict(
                direction="entrant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Dr. Moussa Diallo", expediteur_email="m.diallo@enabel.be",
                destinataires=["f.bamba@ong-demo.ci"],
                corps_texte=(
                    "Le transport est pris en charge par Enabel sur presentation de factures.\n"
                    "Plafond : 50 000 FCFA par personne aller-retour."
                ),
                priorite="normale", statut="lu", est_lu=True,
                date_reception=dt(days=14), score_urgence=15,
            ),
            # 9 -- Modification programme (entrant)
            dict(
                direction="entrant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Secretariat GIZ", expediteur_email="secretariat@giz.de",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "MODIFICATION : La salle passe de Ivoire A a Ivoire B.\n"
                    "L'horaire du J2 est decale de 9h a 10h. Merci de noter ce changement."
                ),
                priorite="haute", statut="lu", est_lu=True,
                date_reception=dt(days=10), score_urgence=50,
            ),
            # 10 -- Accuse reception modification (sortant)
            dict(
                direction="sortant", sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Adjoua KONAN", expediteur_email="coordination@ong-demo.ci",
                destinataires=["secretariat@giz.de"],
                corps_texte="Bien note. Merci pour l'information.",
                priorite="normale", statut="repondu", est_lu=True,
                date_reception=dt(days=10, hours=2), score_urgence=5,
            ),
            # [PROBLEME] 11 -- Email reunion OSC noye dans le fil TDR
            dict(
                direction="sortant",
                sujet="Re: TDR Atelier Enabel - GIZ",
                expediteur="Adjoua KONAN", expediteur_email="coordination@ong-demo.ci",
                destinataires=["osc.touba@gmail.com", "osc.sanpedro@gmail.com"],
                corps_texte=(
                    "Bonjour,\n\n"
                    "Je vous transmets le lien pour notre seance de travail de demain :\n"
                    ">> https://meet.google.com/abc-defg-hij\n\n"
                    "Date : Vendredi 10 janvier a 14h30\n"
                    "Ordre du jour :\n"
                    "  1. Point sur les activites OSC Touba\n"
                    "  2. Plan d'action OSC San Pedro\n"
                    "  3. Divers\n\n"
                    "[PROBLEME SIGNALE PAR LE CLIENT]\n"
                    "Cet email a ete envoye en reponse au fil TDR Enabel-GIZ.\n"
                    "Il devrait etre un email independant avec son propre sujet.\n\n"
                    "Bien cordialement,\nAdjoua KONAN"
                ),
                priorite="haute", statut="repondu", est_lu=True,
                date_reception=dt(days=8), score_urgence=75,
                traite_par_ia=True,
                resume_ia=(
                    "[ALERTE IA] Cet email traite d'un sujet DIFFERENT du fil de discussion : "
                    "lien de reunion OSC Touba/San Pedro, sans rapport avec le TDR Enabel-GIZ. "
                    "Recommandation : aurait du etre envoye en email independant."
                ),
                categorie_ia="Reunion / Lien visioconference",
            ),
        ]

        tdr_objs = []
        for i, data in enumerate(tdr_emails):
            data["thread_id"] = thread_tdr
            email, created = Email.objects.get_or_create(
                sujet=data["sujet"],
                expediteur_email=data["expediteur_email"],
                thread_id=thread_tdr,
                date_reception=data["date_reception"],
                defaults={**data, "cree_par": admin},
            )
            if created and i > 0 and tdr_objs:
                email.en_reponse_a = tdr_objs[i - 1]
                email.save(update_fields=["en_reponse_a"])
            tdr_objs.append(email)
            if created:
                self.stdout.write(f"  [Fil TDR #{i + 1}] {email.sujet[:55]}")

        # Assigner etiquettes au fil TDR
        if tdr_objs:
            etiq["Partenaires"].emails.add(tdr_objs[0])
            etiq["Formation"].emails.add(tdr_objs[0])
        if len(tdr_objs) >= 11:
            etiq["Reunion"].emails.add(tdr_objs[10])
            etiq["Urgent"].emails.add(tdr_objs[10])
            etiq["OSC Terrain"].emails.add(tdr_objs[10])

        self.stdout.write(
            f"  [Fil TDR] {len(tdr_objs)} emails (thread={thread_tdr[:30]})"
        )

        # B) LA SOLUTION : meme info en email independant ----------------------
        thread_osc = "THREAD-REUNION-OSC-" + uuid.uuid4().hex[:8]
        email_correct, created = Email.objects.get_or_create(
            sujet="Lien reunion OSC Touba / San Pedro -- Vendredi 10 janvier",
            expediteur_email="coordination@ong-demo.ci",
            defaults=dict(
                direction="sortant",
                expediteur="Adjoua KONAN",
                destinataires=["osc.touba@gmail.com", "osc.sanpedro@gmail.com"],
                destinataires_cc=["direction@ong-demo.ci"],
                corps_texte=(
                    "Bonjour,\n\n"
                    "Lien pour notre seance de travail de vendredi :\n"
                    "Lien Meet : https://meet.google.com/abc-defg-hij\n"
                    "Date : Vendredi 10 janvier 2025 a 14h30\n"
                    "Duree prevue : 2 heures\n\n"
                    "Ordre du jour :\n"
                    "  1. Point de situation OSC Touba (30 min)\n"
                    "  2. Plan d'action OSC San Pedro (30 min)\n"
                    "  3. Prochaines etapes et calendrier (30 min)\n"
                    "  4. Divers\n\n"
                    "[FIL INDEPENDANT] Cet email est envoye avec son propre sujet "
                    "et peut etre retrouve facilement via l'etiquette 'Reunion' ou 'OSC Terrain'.\n\n"
                    "Bien cordialement,\nAdjoua KONAN -- Coordinatrice de Projet"
                ),
                priorite="haute", statut="repondu", est_lu=True,
                date_reception=dt(days=8, hours=1),
                thread_id=thread_osc,
                score_urgence=70,
                cree_par=admin,
            )
        )
        if created:
            etiq["Reunion"].emails.add(email_correct)
            etiq["Urgent"].emails.add(email_correct)
            etiq["OSC Terrain"].emails.add(email_correct)
            etiq["Partenaires"].emails.add(email_correct)
            self.stdout.write(
                f"  [Fil independant CORRECT] {email_correct.sujet}"
            )

        # C) Emails independants varies ----------------------------------------
        independants = [
            dict(
                direction="entrant",
                sujet="Rapport mensuel novembre 2024 -- ONG-DEMO",
                expediteur="Direction Programmes",
                expediteur_email="programmes@ong-demo.ci",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Bonjour,\n\nVeuillez trouver ci-joint le rapport mensuel de novembre 2024.\n"
                    "Points saillants :\n"
                    "- Taux d'execution budgetaire : 78%\n"
                    "- Activites realisees : 12/15\n"
                    "- Indicateurs atteints : 8/10\n\n"
                    "Le rapport complet est disponible sur le serveur."
                ),
                priorite="normale", statut="lu", est_lu=True,
                date_reception=dt(days=30),
                thread_id="THREAD-RAPPORT-NOV-" + uuid.uuid4().hex[:8],
                score_urgence=20, cree_par=admin,
                etiquettes_noms=["Rapport", "Info"],
            ),
            dict(
                direction="entrant",
                sujet="Demande de justificatifs -- Avance de fonds mission Bouake",
                expediteur="Service Comptabilite",
                expediteur_email="compta@ong-demo.ci",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Bonjour,\n\nSuite a la mission de terrain a Bouake (15-18 janvier),\n"
                    "merci de nous faire parvenir les justificatifs suivants :\n"
                    "- Recus carburant\n- Factures hebergement\n- Bordereau de mission signe\n\n"
                    "Delai : 5 jours ouvrables.\n\nMerci"
                ),
                priorite="haute", statut="non_lu", est_lu=False,
                date_reception=dt(days=3),
                thread_id="THREAD-JUSTIF-BOUAKE-" + uuid.uuid4().hex[:8],
                score_urgence=65, cree_par=admin,
                etiquettes_noms=["Finance", "Urgent", "En attente"],
            ),
            dict(
                direction="entrant",
                sujet="Invitation -- Comite de pilotage PRCC -- 25 janvier 2025",
                expediteur="Dr. Moussa Diallo",
                expediteur_email="m.diallo@enabel.be",
                destinataires=["coordination@ong-demo.ci", "direction@ong-demo.ci"],
                corps_texte=(
                    "Madame, Monsieur,\n\n"
                    "Nous avons l'honneur de vous inviter au Comite de Pilotage PRCC "
                    "le samedi 25 janvier 2025 a 9h00 au siege d'Enabel.\n\n"
                    "Programme :\n"
                    "  09h00 - Accueil\n"
                    "  09h30 - Bilan 2024\n"
                    "  11h00 - Plan de travail 2025\n"
                    "  12h30 - Dejeuner de travail\n"
                    "  14h00 - Questions diverses\n\n"
                    "Merci de confirmer votre presence avant le 20 janvier.\n\n"
                    "Bien cordialement,\nDr. Moussa Diallo"
                ),
                priorite="haute", statut="non_lu", est_lu=False,
                date_reception=dt(days=5),
                thread_id="THREAD-COPIL-PRCC-" + uuid.uuid4().hex[:8],
                score_urgence=80, cree_par=admin,
                etiquettes_noms=["Reunion", "Urgent", "Partenaires"],
            ),
            dict(
                direction="sortant",
                sujet="Transmission rapport trimestriel Q4 2024 -- PRCC",
                expediteur="Adjoua KONAN",
                expediteur_email="coordination@ong-demo.ci",
                destinataires=["m.diallo@enabel.be", "secretariat@giz.de"],
                destinataires_cc=["direction@ong-demo.ci"],
                corps_texte=(
                    "Monsieur, Madame,\n\n"
                    "Veuillez trouver ci-joint le rapport trimestriel Q4 2024 du programme PRCC.\n\n"
                    "Faits marquants :\n"
                    "[OK] Formation de 450 beneficiaires (cible 400)\n"
                    "[OK] 3 infrastructures rehabilitees\n"
                    "[ATTENTION] Activite 2.3 reportee au Q1 2025 (raisons climatiques)\n\n"
                    "Nous restons disponibles pour toute question.\n\nBien cordialement"
                ),
                priorite="normale", statut="repondu", est_lu=True,
                date_reception=dt(days=15),
                thread_id="THREAD-RAPPORT-Q4-" + uuid.uuid4().hex[:8],
                score_urgence=30, cree_par=admin,
                etiquettes_noms=["Rapport", "Partenaires"],
            ),
            dict(
                direction="entrant",
                sujet="Formation ODK Collect -- convocation agents terrain",
                expediteur="Ibrahima TRAORE",
                expediteur_email="i.traore@consultant.ci",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Bonjour,\n\n"
                    "Convocation pour la formation ODK Collect prevue les 20-22 janvier 2025.\n\n"
                    "Participants : 15 agents terrain\n"
                    "Lieu : Salle de conference ONG-DEMO, Abidjan\n"
                    "Materiel requis : tablettes chargees, connexion WiFi\n\n"
                    "Merci de confirmer la disponibilite de la salle.\n\nCordialement"
                ),
                priorite="normale", statut="lu", est_lu=True,
                date_reception=dt(days=12),
                thread_id="THREAD-FORM-ODK-" + uuid.uuid4().hex[:8],
                score_urgence=40, cree_par=admin,
                etiquettes_noms=["Formation", "OSC Terrain"],
            ),
            dict(
                direction="entrant",
                sujet="URGENT -- Blocage deblocage fonds programme decembre",
                expediteur="PNUD Finance",
                expediteur_email="finance.pnud@undp.org",
                destinataires=["direction@ong-demo.ci", "f.bamba@ong-demo.ci"],
                corps_texte=(
                    "URGENT\n\n"
                    "Le deblocage des fonds de decembre est suspendu en raison d'une anomalie "
                    "dans le rapport financier S2 transmis le 15 decembre.\n\n"
                    "Documents requis en urgence :\n"
                    "1. Rapport narratif corrige\n"
                    "2. Pieces justificatives des depenses > 500 000 FCFA\n"
                    "3. Certification du commissaire aux comptes\n\n"
                    "Delai absolu : 48h\n\nCordialement"
                ),
                priorite="haute", statut="non_lu", est_lu=False,
                date_reception=dt(hours=6),
                thread_id="THREAD-FONDS-PNUD-" + uuid.uuid4().hex[:8],
                score_urgence=95, cree_par=admin,
                etiquettes_noms=["Finance", "Urgent", "Partenaires"],
            ),
            dict(
                direction="sortant",
                sujet="Point hebdomadaire equipe -- semaine 3 janvier 2025",
                expediteur="Adjoua KONAN",
                expediteur_email="coordination@ong-demo.ci",
                destinataires=["equipe@ong-demo.ci"],
                corps_texte=(
                    "Equipe,\n\nVoici le point de la semaine :\n\n"
                    "Fait cette semaine :\n"
                    "  - Atelier Enabel-GIZ finalise\n"
                    "  - Rapport Q4 transmis aux bailleurs\n"
                    "  - Reunion OSC Touba/San Pedro (voir compte-rendu)\n\n"
                    "A faire semaine prochaine :\n"
                    "  - Formation ODK Collect (20-22/01)\n"
                    "  - COPIL PRCC (25/01)\n"
                    "  - Deblocage fonds PNUD -- dossier urgent\n\n"
                    "Bonne semaine a tous,\nAdjoua"
                ),
                priorite="normale", statut="repondu", est_lu=True,
                date_reception=dt(days=2),
                thread_id="THREAD-POINT-HEBDO-" + uuid.uuid4().hex[:8],
                score_urgence=15, cree_par=admin,
                etiquettes_noms=["Interne", "Info"],
            ),
        ]

        for mail_data in independants:
            etiq_noms = mail_data.pop("etiquettes_noms", [])
            email, created = Email.objects.get_or_create(
                sujet=mail_data["sujet"],
                expediteur_email=mail_data["expediteur_email"],
                defaults=mail_data,
            )
            if created:
                for nom in etiq_noms:
                    if nom in etiq:
                        etiq[nom].emails.add(email)
                label = email.sujet[:55] + ("..." if len(email.sujet) > 55 else "")
                self.stdout.write(f"  [Email] {label} (urgence={email.score_urgence})")
            else:
                self.stdout.write(f"  [Email] Existant -- {email.sujet[:50]}")

        # D) Fil de reponse legitime : rapport mensuel -------------------------
        thread_rapport = "THREAD-RAPPORT-DEC-" + uuid.uuid4().hex[:8]

        rapport_init, cr1 = Email.objects.get_or_create(
            sujet="Rapport mensuel decembre 2024 -- en attente validation",
            expediteur_email="i.traore@consultant.ci",
            defaults=dict(
                direction="entrant",
                expediteur="Ibrahima TRAORE",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Bonjour,\n\n"
                    "Veuillez trouver en piece jointe le rapport mensuel de decembre 2024.\n"
                    "Merci de valider avant transmission aux bailleurs.\n\nCordialement"
                ),
                priorite="normale", statut="lu", est_lu=True,
                date_reception=dt(days=7),
                thread_id=thread_rapport,
                score_urgence=35, cree_par=admin,
            )
        )
        if cr1:
            etiq["Rapport"].emails.add(rapport_init)
            etiq["En attente"].emails.add(rapport_init)
            self.stdout.write(f"  [Fil Rapport] 1/3 -- {rapport_init.sujet[:50]}")

        rapport_reponse, cr2 = Email.objects.get_or_create(
            sujet="Re: Rapport mensuel decembre 2024 -- en attente validation",
            expediteur_email="coordination@ong-demo.ci",
            defaults=dict(
                direction="sortant",
                expediteur="Adjoua KONAN",
                destinataires=["i.traore@consultant.ci"],
                corps_texte=(
                    "Ibrahima,\n\nRapport bien recu. Commentaires :\n"
                    "- Section 3.2 : preciser les indicateurs atteints vs cibles\n"
                    "- Annexe B : joindre les fiches de presence des formations\n\n"
                    "Merci de corriger et renvoyer d'ici jeudi.\n\nCordialement"
                ),
                priorite="normale", statut="repondu", est_lu=True,
                date_reception=dt(days=6),
                en_reponse_a=rapport_init,
                thread_id=thread_rapport,
                score_urgence=30, cree_par=admin,
            )
        )
        if cr2:
            etiq["Rapport"].emails.add(rapport_reponse)
            self.stdout.write(f"  [Fil Rapport] 2/3 -- {rapport_reponse.sujet[:50]}")

        rapport_final, cr3 = Email.objects.get_or_create(
            sujet="Re: Rapport mensuel decembre 2024 -- en attente validation",
            expediteur_email="i.traore@consultant.ci",
            date_reception=dt(days=5),
            defaults=dict(
                direction="entrant",
                expediteur="Ibrahima TRAORE",
                destinataires=["coordination@ong-demo.ci"],
                corps_texte=(
                    "Bonjour,\n\nRapport corrige en piece jointe. Corrections :\n"
                    "[OK] Section 3.2 mise a jour avec tableaux indicateurs\n"
                    "[OK] Annexe B : fiches de presence ajoutees (12 fiches)\n\n"
                    "Merci pour vos retours.\n\nCordialement"
                ),
                priorite="normale", statut="non_lu", est_lu=False,
                en_reponse_a=rapport_reponse,
                thread_id=thread_rapport,
                score_urgence=25, cree_par=admin,
            )
        )
        if cr3:
            etiq["Rapport"].emails.add(rapport_final)
            etiq["En attente"].emails.add(rapport_final)
            self.stdout.write(f"  [Fil Rapport] 3/3 (non lu) -- {rapport_final.sujet[:50]}")

        total = Email.objects.count()
        total_etiq = sum(e.emails.count() for e in etiq.values())
        self.stdout.write("")
        self.stdout.write(f"  Total emails en base       : {total}")
        self.stdout.write(f"  Associations etiquettes    : {total_etiq}")
