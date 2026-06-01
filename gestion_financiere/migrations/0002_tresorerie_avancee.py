import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_financiere', '0001_initial'),
        ('programmes_projets', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── CompteBancaire ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='CompteBancaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('code', models.CharField(blank=True, max_length=20)),
                ('intitule', models.CharField(max_length=200)),
                ('type_compte', models.CharField(
                    choices=[
                        ('courant', 'Compte courant'),
                        ('epargne', 'Compte épargne'),
                        ('projet', 'Compte projet dédié'),
                        ('transit', 'Compte de transit'),
                    ],
                    default='courant', max_length=15,
                )),
                ('banque', models.CharField(max_length=200)),
                ('numero_compte', models.CharField(blank=True, max_length=50)),
                ('rib', models.CharField(blank=True, max_length=100, verbose_name='RIB/IBAN')),
                ('devise', models.CharField(
                    choices=[
                        ('XOF', 'Franc CFA (XOF)'), ('EUR', 'Euro (EUR)'),
                        ('USD', 'Dollar US (USD)'), ('GBP', 'Livre Sterling (GBP)'),
                        ('CHF', 'Franc Suisse (CHF)'),
                    ],
                    default='XOF', max_length=5,
                )),
                ('solde_initial', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('solde_actuel', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('date_ouverture', models.DateField(blank=True, null=True)),
                ('actif', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('programme', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='comptes_bancaires',
                    to='programmes_projets.programme',
                )),
                ('projet', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='comptes_bancaires',
                    to='programmes_projets.projet',
                )),
                ('responsable', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='comptes_bancaires_geres',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'Compte bancaire', 'ordering': ['banque', 'intitule']},
        ),

        # ── MouvementBancaire ────────────────────────────────────────────────
        migrations.CreateModel(
            name='MouvementBancaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('date_operation', models.DateField()),
                ('date_valeur', models.DateField(blank=True, null=True)),
                ('type_mouvement', models.CharField(
                    choices=[('credit', 'Crédit (entrée)'), ('debit', 'Débit (sortie)')],
                    max_length=10,
                )),
                ('libelle', models.CharField(max_length=300)),
                ('montant', models.DecimalField(
                    decimal_places=2, max_digits=15,
                    validators=[django.core.validators.MinValueValidator(0)],
                )),
                ('solde_apres', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('reference_externe', models.CharField(blank=True, max_length=100)),
                ('rapproche', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('compte', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mouvements',
                    to='gestion_financiere.comptebancaire',
                )),
                ('convention', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mouvements_bancaires',
                    to='gestion_financiere.convention',
                )),
                ('depense', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mouvements_bancaires',
                    to='gestion_financiere.depense',
                )),
                ('saisi_par', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mouvements_bancaires_saisis',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'Mouvement bancaire', 'ordering': ['-date_operation', '-created_at']},
        ),

        # ── RapprochementBancaire ────────────────────────────────────────────
        migrations.CreateModel(
            name='RapprochementBancaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('periode_debut', models.DateField()),
                ('periode_fin', models.DateField()),
                ('solde_releve', models.DecimalField(
                    decimal_places=2, max_digits=20,
                    help_text='Solde figurant sur le relevé bancaire officiel.',
                )),
                ('solde_comptable', models.DecimalField(
                    decimal_places=2, default=0, max_digits=20,
                    help_text="Solde calculé dans l'ERP à la date de fin de période.",
                )),
                ('ecart', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('nb_mouvements_rapproches', models.IntegerField(default=0)),
                ('nb_mouvements_non_rapproches', models.IntegerField(default=0)),
                ('statut', models.CharField(
                    choices=[
                        ('en_cours', 'En cours'),
                        ('valide', 'Validé'),
                        ('cloture', 'Clôturé'),
                    ],
                    default='en_cours', max_length=15,
                )),
                ('observations', models.TextField(blank=True)),
                ('date_validation', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('compte', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rapprochements',
                    to='gestion_financiere.comptebancaire',
                )),
                ('effectue_par', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='rapprochements_effectues',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('valide_par', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='rapprochements_valides',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'Rapprochement bancaire', 'ordering': ['-periode_fin']},
        ),
    ]
