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
            name='NonConformite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('reference', models.CharField(blank=True, max_length=30, unique=True)),
                ('titre', models.CharField(max_length=300)),
                ('description', models.TextField()),
                ('type_nc', models.CharField(choices=[('processus','Processus'),('produit','Produit'),('service','Service'),('documentation','Documentation'),('ressources','Ressources'),('autre','Autre')], max_length=20)),
                ('gravite', models.CharField(choices=[('mineure','Mineure'),('majeure','Majeure'),('critique','Critique')], default='mineure', max_length=10)),
                ('statut', models.CharField(choices=[('ouverte','Ouverte'),('en_traitement','En traitement'),('cloturee','Clôturée'),('verifiee','Vérifiée')], default='ouverte', max_length=15)),
                ('date_detection', models.DateField()),
                ('date_echeance', models.DateField(blank=True, null=True)),
                ('date_cloture', models.DateField(blank=True, null=True)),
                ('cause_racine', models.TextField(blank=True)),
                ('impact', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('detecte_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nc_detectees', to=settings.AUTH_USER_MODEL)),
                ('programme', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programmes_projets.programme')),
                ('projet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programmes_projets.projet')),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nc_responsable', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Non-conformité', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ActionQualite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('type_action', models.CharField(choices=[('corrective','Action Corrective'),('preventive','Action Préventive'),('amelioration',"Action d'Amélioration")], max_length=15)),
                ('titre', models.CharField(max_length=300)),
                ('description', models.TextField()),
                ('statut', models.CharField(choices=[('planifiee','Planifiée'),('en_cours','En cours'),('realisee','Réalisée'),('verifiee','Vérifiée'),('cloturee','Clôturée')], default='planifiee', max_length=15)),
                ('date_prevue', models.DateField(blank=True, null=True)),
                ('date_realisation', models.DateField(blank=True, null=True)),
                ('resultat', models.TextField(blank=True)),
                ('efficace', models.BooleanField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions_qualite_creees', to=settings.AUTH_USER_MODEL)),
                ('non_conformite', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions', to='gestion_qualite.nonconformite')),
                ('responsable', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions_qualite', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Action qualité', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='AuditInterne',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('reference', models.CharField(blank=True, max_length=30, unique=True)),
                ('titre', models.CharField(max_length=300)),
                ('type_audit', models.CharField(choices=[('processus','Audit processus'),('systeme','Audit système'),('produit','Audit produit'),('conformite','Audit conformité')], max_length=15)),
                ('statut', models.CharField(choices=[('planifie','Planifié'),('en_cours','En cours'),('termine','Terminé'),('cloture','Clôturé')], default='planifie', max_length=10)),
                ('date_planifiee', models.DateField()),
                ('date_realisation', models.DateField(blank=True, null=True)),
                ('perimetre', models.TextField(blank=True)),
                ('criteres', models.TextField(blank=True)),
                ('nb_nc_majeures', models.IntegerField(default=0)),
                ('nb_nc_mineures', models.IntegerField(default=0)),
                ('nb_observations', models.IntegerField(default=0)),
                ('rapport', models.TextField(blank=True)),
                ('conclusions', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('auditeur_principal', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audits_conduits', to=settings.AUTH_USER_MODEL)),
                ('programme', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programmes_projets.programme')),
                ('projet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='programmes_projets.projet')),
            ],
            options={'verbose_name': 'Audit interne', 'ordering': ['-date_planifiee']},
        ),
        migrations.CreateModel(
            name='IndicateurQualite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('intitule', models.CharField(max_length=300)),
                ('description', models.TextField(blank=True)),
                ('unite', models.CharField(max_length=50)),
                ('valeur_cible', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('valeur_actuelle', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('frequence_mesure', models.CharField(choices=[('mensuelle','Mensuelle'),('trimestrielle','Trimestrielle'),('semestrielle','Semestrielle'),('annuelle','Annuelle')], default='mensuelle', max_length=15)),
                ('actif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Indicateur qualité', 'ordering': ['code']},
        ),
    ]
