from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ged', '0001_initial'),
    ]

    operations = [
        # Clé AES-256 wrappée dans BoiteArchive
        migrations.AddField(
            model_name='boitearchive',
            name='cle_chiffrement',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Clé AES-256 wrappée (base64). Générée automatiquement si chiffree=True.',
            ),
            preserve_default=False,
        ),
        # Fichier chiffré dans DocumentArchive
        migrations.AddField(
            model_name='documentarchive',
            name='fichier_chiffre',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='ged/coffre/%Y/%m/',
                help_text='Copie chiffrée AES-256-GCM du fichier (coffre-fort numérique).',
            ),
        ),
    ]
