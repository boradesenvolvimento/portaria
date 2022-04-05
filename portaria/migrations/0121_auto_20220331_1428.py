# Generated by Django 3.2.6 on 2022-03-31 14:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0120_etiquetaspalete_autor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='etiquetaspalete',
            name='bip_date',
        ),
        migrations.RemoveField(
            model_name='etiquetaspalete',
            name='bipado',
        ),
        migrations.RemoveField(
            model_name='etiquetaspalete',
            name='manifesto',
        ),
        migrations.RemoveField(
            model_name='etiquetaspalete',
            name='volume_conf',
        ),
        migrations.AlterField(
            model_name='skurefxml',
            name='codigo',
            field=models.CharField(max_length=30),
        ),
        migrations.CreateModel(
            name='BipagemPalete',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('filial', models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE')], max_length=3)),
                ('bip_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('cod_barras', models.CharField(max_length=20)),
                ('volume_conf', models.IntegerField(blank=True, null=True)),
                ('manifesto', models.IntegerField(blank=True, null=True)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('etq_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portaria.etiquetaspalete')),
            ],
        ),
    ]