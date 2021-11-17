# Generated by Django 3.2.6 on 2021-11-12 15:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import portaria.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0057_auto_20211112_1452'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('razao_social', models.CharField(max_length=100)),
                ('cnpj', models.CharField(max_length=14, validators=[portaria.models.only_int])),
            ],
        ),
        migrations.RemoveField(
            model_name='paletecontrol',
            name='destino',
        ),
        migrations.RemoveField(
            model_name='paletecontrol',
            name='origem',
        ),
        migrations.RemoveField(
            model_name='paletecontrol',
            name='placa_veic',
        ),
        migrations.RemoveField(
            model_name='paletecontrol',
            name='ultima_viagem',
        ),
        migrations.AddField(
            model_name='paletecontrol',
            name='tp_palete',
            field=models.CharField(choices=[('CHEP', 'CHEP'), ('PBR', 'PBR')], default='1', max_length=4),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='MovPalete',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('data_ult_mov', models.DateField(default=django.utils.timezone.now)),
                ('origem', models.CharField(choices=[('SPO', 'SPO'), ('REC', 'REC'), ('SSA', 'SSA'), ('FOR', 'FOR'), ('MCZ', 'MCZ'), ('NAT', 'NAT'), ('JPA', 'JPA'), ('AJU', 'AJU'), ('VDC', 'VDC'), ('MG', 'MG'), ('CTG', 'CTG'), ('TCO', 'TCO'), ('UDI', 'UDI'), ('TNA', 'TNA'), ('VIX', 'VIX')], max_length=3)),
                ('destino', models.CharField(choices=[('SPO', 'SPO'), ('REC', 'REC'), ('SSA', 'SSA'), ('FOR', 'FOR'), ('MCZ', 'MCZ'), ('NAT', 'NAT'), ('JPA', 'JPA'), ('AJU', 'AJU'), ('VDC', 'VDC'), ('MG', 'MG'), ('CTG', 'CTG'), ('TCO', 'TCO'), ('UDI', 'UDI'), ('TNA', 'TNA'), ('VIX', 'VIX')], max_length=3)),
                ('placa_veic', models.CharField(max_length=7)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('palete', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='portaria.paletecontrol')),
            ],
        ),
    ]
