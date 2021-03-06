# Generated by Django 3.2.6 on 2022-05-12 12:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0128_auto_20220510_0859'),
    ]

    operations = [
        migrations.AddField(
            model_name='etiquetaspalete',
            name='localizacao',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='etiquetaspalete',
            name='nota_fiscal',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='movpalete',
            name='palete',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portaria.paletecontrol'),
        ),
    ]
