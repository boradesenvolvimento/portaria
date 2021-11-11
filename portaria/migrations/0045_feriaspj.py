# Generated by Django 3.2.6 on 2021-11-08 12:58

from django.db import migrations, models
import django.db.models.deletion
import portaria.models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0044_auto_20211105_0912'),
    ]

    operations = [
        migrations.CreateModel(
            name='feriaspj',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('ultimas_ferias_ini', models.DateField()),
                ('ultimas_ferias_fim', models.DateField()),
                ('periodo', models.CharField(max_length=2, validators=[portaria.models.only_int])),
                ('valor_pagar', models.FloatField()),
                ('quitado', models.BooleanField()),
                ('alerta_venc_enviado', models.BooleanField()),
                ('funcionario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='portaria.funcpj')),
            ],
        ),
    ]
