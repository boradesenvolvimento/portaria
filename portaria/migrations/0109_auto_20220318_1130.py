# Generated by Django 3.2.6 on 2022-03-18 11:30

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0108_bipagemetiqueta_etiquetasromaneio'),
    ]

    operations = [
        migrations.AddField(
            model_name='bipagemetiqueta',
            name='pub_date',
            field=models.DateField(default='0001-01-01', verbose_name=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='etiquetasromaneio',
            name='pub_date',
            field=models.DateField(default='0001-01-01', verbose_name=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='etiquetasromaneio',
            name='tp_doc',
            field=models.CharField(choices=[('4', 'ROMANEIO'), ('58', 'MDFE')], max_length=3),
        ),
    ]
