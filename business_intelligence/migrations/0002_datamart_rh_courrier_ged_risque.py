import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_intelligence', '0001_initial'),
        ('programmes_projets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatamartRH',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('annee', models.IntegerField()),
                ('mois', models.IntegerField(null=True, blank=True)),
                ('nb_agents', models.IntegerField(default=0)),
                ('nb_consultants', models.IntegerField(default=0)),
                ('nb_missions', models.IntegerField(default=0)),
                ('nb_contrats_actifs', models.IntegerField(default=0)),
                ('cout_total_rh', models.DecimalField(max_digits=20, decimal_places=2, default=0)),
                ('taux_occupation_moyen', models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('zone_geographique', models.CharField(max_length=200, blank=True)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('programme', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE,
                                                related_name='datamart_rh', to='programmes_projets.programme')),
                ('projet', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL,
                                             related_name='datamart_rh', to='programmes_projets.projet')),
            ],
            options={
                'verbose_name': 'Datamart RH',
                'ordering': ['-annee', '-mois'],
                'unique_together': {('programme', 'projet', 'annee', 'mois')},
            },
        ),
        migrations.CreateModel(
            name='DatamartCourrier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('annee', models.IntegerField()),
                ('mois', models.IntegerField()),
                ('trimestre', models.IntegerField()),
                ('nb_courriers_entrants', models.IntegerField(default=0)),
                ('nb_courriers_sortants', models.IntegerField(default=0)),
                ('nb_courriers_internes', models.IntegerField(default=0)),
                ('nb_en_attente', models.IntegerField(default=0)),
                ('nb_traites', models.IntegerField(default=0)),
                ('delai_traitement_moyen', models.DecimalField(max_digits=8, decimal_places=2, default=0)),
                ('direction', models.CharField(max_length=200, blank=True)),
                ('type_dominant', models.CharField(max_length=50, blank=True)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Datamart Courrier',
                'ordering': ['-annee', '-mois'],
                'unique_together': {('annee', 'mois', 'direction')},
            },
        ),
        migrations.CreateModel(
            name='DatamartGED',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('annee', models.IntegerField()),
                ('mois', models.IntegerField()),
                ('nb_documents', models.IntegerField(default=0)),
                ('nb_valides', models.IntegerField(default=0)),
                ('nb_en_attente', models.IntegerField(default=0)),
                ('taille_totale_mo', models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ('type_dominant', models.CharField(max_length=50, blank=True)),
                ('nb_telechargements', models.IntegerField(default=0)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('programme', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL,
                                                related_name='datamart_ged', to='programmes_projets.programme')),
            ],
            options={
                'verbose_name': 'Datamart GED',
                'ordering': ['-annee', '-mois'],
                'unique_together': {('annee', 'mois', 'programme')},
            },
        ),
        migrations.CreateModel(
            name='DatamartRisque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('annee', models.IntegerField()),
                ('trimestre', models.IntegerField(null=True, blank=True)),
                ('nb_risques_total', models.IntegerField(default=0)),
                ('nb_critiques', models.IntegerField(default=0)),
                ('nb_eleves', models.IntegerField(default=0)),
                ('nb_moderes', models.IntegerField(default=0)),
                ('nb_faibles', models.IntegerField(default=0)),
                ('nb_maitrise', models.IntegerField(default=0)),
                ('nb_nouveaux', models.IntegerField(default=0)),
                ('score_risque_moyen', models.DecimalField(max_digits=5, decimal_places=2, default=0)),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('programme', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL,
                                                related_name='datamart_risques', to='programmes_projets.programme')),
                ('projet', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL,
                                             related_name='datamart_risques', to='programmes_projets.projet')),
            ],
            options={
                'verbose_name': 'Datamart Risque',
                'ordering': ['-annee', '-trimestre'],
                'unique_together': {('annee', 'trimestre', 'programme', 'projet')},
            },
        ),
    ]
