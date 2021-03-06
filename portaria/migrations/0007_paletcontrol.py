# Generated by Django 3.2.6 on 2021-09-24 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0006_rename_tipo_func_cadastro_tipo_mot'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaletControl',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('loc_atual', models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TNA'), ('24', 'VIX')], max_length=3)),
                ('ultima_viagem', models.DateField()),
                ('origem', models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TNA'), ('24', 'VIX')], max_length=3)),
                ('destino', models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TNA'), ('24', 'VIX')], max_length=3)),
                ('placa_veic', models.CharField(max_length=7)),
            ],
        ),
    ]
