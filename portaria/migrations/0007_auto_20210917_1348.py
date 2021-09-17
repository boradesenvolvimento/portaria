# Generated by Django 3.2.6 on 2021-09-17 16:48

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0006_alter_cadastro_hr_chegada'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cadastro',
            name='hr_chegada',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='cadastro',
            name='placa',
            field=models.CharField(max_length=7),
        ),
        migrations.AlterField(
            model_name='cadastro',
            name='tipo_viagem',
            field=models.CharField(choices=[('COLETA', 'COLETA'), ('ENTREGA', 'ENTREGA'), ('TRANSF', 'TRANSF')], max_length=10),
        ),
    ]
