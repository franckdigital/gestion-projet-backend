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
            name='Diligence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('reference', models.CharField(blank=True, max_length=30, unique=True)),
                ('titre', models.CharField(max_length=300)),
                ('description', models.TextField(blank=True)),
                ('type_source', models.CharField(choices=[('courrier','Courrier'),('reunion','Réunion'),('decision','Décision'),('note','Note'),('instruction_dg','Instruction DG'),('rapport','Rapport'),('autre','Autre')], default='instruction_dg', max_length=20)),
                ('priorite', models.CharField(choices=[('urgente','Urgente'),('haute','Haute'),('normale','Normale'),('faible','Faible')], default='normale', max_length=10)),
                ('statut', models.CharField(choices=[('ouverte','Ouverte'),('affectee','Affectée'),('en_cours','En cours'),('en_attente_controle','En attente de contrôle'),('cloturee','Clôturée'),('annulee','Annulée')], default='ouverte', max_length=25)),
                ('date_echeance', models.DateField(blank=True, null=True)),
                ('date_cloture', models.DateField(blank=True, null=True)),
                ('taux_avancement', models.IntegerField(default=0)),
                ('source_reference', models.CharField(blank=True, max_length=200)),
                ('instructions', models.TextField(blank=True)),
                ('resultat', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diligences_creees', to=settings.AUTH_USER_MODEL)),
                ('emetteur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diligences_emises', to=settings.AUTH_USER_MODEL)),
                ('programme', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diligences', to='programmes_projets.programme')),
                ('projet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diligences', to='programmes_projets.projet')),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dlg_assignees', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Diligence', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SuiviDiligence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('date_suivi', models.DateField()),
                ('avancement', models.IntegerField(default=0)),
                ('observations', models.TextField()),
                ('actions_realisees', models.TextField(blank=True)),
                ('prochaines_etapes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('auteur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='suivis_diligences', to=settings.AUTH_USER_MODEL)),
                ('diligence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suivis', to='diligences.diligence')),
            ],
            options={'verbose_name': 'Suivi diligence', 'ordering': ['-date_suivi']},
        ),
        migrations.CreateModel(
            name='RelanceDiligence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('message', models.TextField()),
                ('date_relance', models.DateTimeField(auto_now_add=True)),
                ('diligence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relances', to='diligences.diligence')),
                ('emetteur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Relance diligence', 'ordering': ['-date_relance']},
        ),
    ]
