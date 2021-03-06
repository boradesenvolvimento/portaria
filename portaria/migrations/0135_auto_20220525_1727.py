# Generated by Django 3.2.6 on 2022-05-25 17:27

from django.db import migrations, models
import portaria.models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0134_registraterceirizados'),
    ]

    operations = [
        migrations.CreateModel(
            name='FornecedorTerceirizados',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('razao_social', models.CharField(max_length=200)),
                ('cnpj', models.CharField(max_length=14, validators=[portaria.models.only_int])),
                ('valor_p_funcionario', models.FloatField()),
            ],
        ),
        migrations.AddField(
            model_name='registraterceirizados',
            name='filial',
            field=models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE'), ('40', 'FMA')], default=1, max_length=3),
            preserve_default=False,
        ),
    ]
