# Generated by Django 3.2.6 on 2022-03-04 08:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0091_cadastro_notas'),
    ]

    operations = [
        migrations.CreateModel(
            name='RomXML',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('dt_emissao', models.DateTimeField()),
                ('nota_fiscal', models.IntegerField()),
                ('remetente', models.CharField(max_length=200)),
                ('destinatario', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='SkuRefXML',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('codigo', models.IntegerField()),
                ('desc_prod', models.CharField(max_length=200)),
                ('tp_un', models.CharField(max_length=10)),
                ('qnt_un', models.IntegerField()),
                ('xmlref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portaria.romxml')),
            ],
        ),
    ]
