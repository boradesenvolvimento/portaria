# Generated by Django 3.2.6 on 2022-03-17 14:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0107_auto_20220317_0925'),
    ]

    operations = [
        migrations.CreateModel(
            name='EtiquetasRomaneio',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('garagem', models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE')], max_length=3)),
                ('tp_doc', models.CharField(choices=[('8', 'NFS'), ('57', 'CTE')], max_length=3)),
                ('nr_doc', models.CharField(max_length=20)),
                ('nota', models.CharField(max_length=10)),
                ('volume', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='BipagemEtiqueta',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('cod_barras', models.CharField(max_length=20)),
                ('nota', models.CharField(max_length=10)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('rom_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portaria.etiquetasromaneio')),
            ],
        ),
    ]
