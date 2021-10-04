# Generated by Django 3.2.6 on 2021-09-28 14:09

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0008_auto_20210924_1121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Motorista',
            fields=[
                ('codigomot', models.BigAutoField(primary_key=True, serialize=False)),
                ('codigoveic', models.IntegerField()),
                ('empresa', models.IntegerField(default=1)),
                ('filial', models.IntegerField(default=1)),
                ('nome', models.CharField(max_length=100)),
                ('RG', models.CharField(max_length=20)),
                ('CPF', models.CharField(max_length=11)),
                ('telefone', models.IntegerField(validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(11)])),
                ('endereco', models.CharField(max_length=100)),
                ('bairro', models.CharField(max_length=100)),
                ('cidade', models.CharField(max_length=20)),
                ('UF', models.CharField(max_length=2)),
                ('cep', models.IntegerField(validators=[django.core.validators.MinValueValidator(8), django.core.validators.MaxValueValidator(8)])),
                ('data_nasc', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Veiculos',
            fields=[
                ('codigoveic', models.BigAutoField(primary_key=True, serialize=False)),
                ('codigotpveic', models.CharField(choices=[(1, 'VAN_PASSAGEIROS'), (2, 'CAMINHAO'), (3, 'CAVALO'), (4, 'CARRETA'), (5, 'VUC'), (6, 'BITRUCK'), (7, 'TOCO'), (8, '3/4'), (9, 'TRUCK'), (10, 'VEICULO_APOIO'), (11, 'PASSAGEIRO'), (12, 'PASSAGEIRO_AUTOMOVEL')], max_length=5)),
                ('empresa', models.IntegerField(default=1)),
                ('filial', models.IntegerField(default=1)),
                ('garagem', models.IntegerField(default=1)),
                ('prefixoveic', models.CharField(max_length=7)),
                ('condicaoveic', models.CharField(max_length=20)),
                ('capacidadetanqueveic', models.CharField(max_length=20)),
                ('kmatualveic', models.IntegerField()),
                ('obsveic', models.CharField(max_length=30)),
                ('renavanveic', models.CharField(max_length=11)),
                ('modeloveic', models.CharField(max_length=20)),
                ('codmotorista', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='portaria.motorista')),
            ],
        ),
    ]