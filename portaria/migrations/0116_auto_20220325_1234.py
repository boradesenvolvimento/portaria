# Generated by Django 3.2.6 on 2022-03-25 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0115_alter_etiquetaspalete_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='etiquetaspalete',
            name='bip_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='etiquetaspalete',
            name='bipado',
            field=models.BooleanField(default=False),
        ),
    ]
