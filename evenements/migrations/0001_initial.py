import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('programmes_projets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Evenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('titre', models.CharField(max_length=300)),
                ('type_evenement', models.CharField(choices=[('atelier','Atelier'),('seminaire','Séminaire'),('formation','Formation'),('conference','Conférence'),('forum','Forum'),('mission','Mission'),('reunion','Réunion'),('autre','Autre')], max_length=15)),
                ('statut', models.CharField(choices=[('planifie','Planifié'),('confirme','Confirmé'),('en_cours','En cours'),('termine','Terminé'),('annule','Annulé'),('reporte','Reporté')], default='planifie', max_length=15)),
                ('description', models.TextField(blank=True)),
                ('date_debut', models.DateTimeField()),
                ('date_fin', models.DateTimeField()),
                ('lieu', models.CharField(blank=True, max_length=300)),
                ('lieu_details', models.TextField(blank=True)),
                ('budget_prevu', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('budget_realise', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('nombre_participants_prevu', models.IntegerField(default=0)),
                ('objectifs', models.TextField(blank=True)),
                ('ordre_du_jour', models.TextField(blank=True)),
                ('resultats_attendus', models.TextField(blank=True)),
                ('compte_rendu', models.TextField(blank=True)),
                ('avec_inscription', models.BooleanField(default=False)),
                ('avec_presence_qr', models.BooleanField(default=False)),
                ('avec_evaluation', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evv_crees', to=settings.AUTH_USER_MODEL)),
                ('organisateur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evv_organises', to=settings.AUTH_USER_MODEL)),
                ('programme', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evv_evenements', to='programmes_projets.programme')),
                ('projet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evv_evenements', to='programmes_projets.projet')),
            ],
            options={'verbose_name': 'Événement', 'ordering': ['-date_debut']},
        ),
        migrations.CreateModel(
            name='ParticipantEvenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nom', models.CharField(blank=True, max_length=200)),
                ('prenom', models.CharField(blank=True, max_length=200)),
                ('email', models.EmailField(blank=True)),
                ('organisation', models.CharField(blank=True, max_length=200)),
                ('fonction', models.CharField(blank=True, max_length=200)),
                ('telephone', models.CharField(blank=True, max_length=20)),
                ('statut', models.CharField(choices=[('invite','Invité'),('confirme','Confirmé'),('present','Présent'),('absent','Absent'),('annule','Annulé')], default='invite', max_length=15)),
                ('date_confirmation', models.DateTimeField(blank=True, null=True)),
                ('date_presence', models.DateTimeField(blank=True, null=True)),
                ('qr_code', models.CharField(blank=True, max_length=100)),
                ('note_evaluation', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('commentaire_evaluation', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('evenement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='evenements.evenement')),
                ('utilisateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evv_participations', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Participant', 'ordering': ['nom', 'prenom'], 'unique_together': {('evenement', 'email')}},
        ),
        migrations.CreateModel(
            name='DepenseEvenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('categorie', models.CharField(choices=[('location_salle','Location salle'),('restauration','Restauration'),('transport','Transport'),('materiel','Matériel'),('communication','Communication'),('honoraires','Honoraires'),('autre','Autre')], max_length=20)),
                ('description', models.CharField(max_length=300)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=15)),
                ('fournisseur', models.CharField(blank=True, max_length=200)),
                ('date_depense', models.DateField()),
                ('facture_ref', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('evenement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='depenses', to='evenements.evenement')),
                ('saisi_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Dépense événement', 'ordering': ['-date_depense']},
        ),
    ]
