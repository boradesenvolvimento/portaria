# Generated by Django 3.2.6 on 2021-09-24 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0007_paletcontrol'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='paletcontrol',
            options={'verbose_name': 'PaletControl', 'verbose_name_plural': 'PaletControl'},
        ),
        migrations.AlterField(
            model_name='cadastro',
            name='garagem',
            field=models.CharField(choices=[('SPO', 'SPO'), ('REC', 'REC'), ('SSA', 'SSA'), ('FOR', 'FOR'), ('MCZ', 'MCZ'), ('NAT', 'NAT'), ('JPA', 'JPA'), ('AJU', 'AJU'), ('VDC', 'VDC'), ('MG', 'MG'), ('CTG', 'CTG'), ('TCO', 'TCO'), ('UDI', 'UDI'), ('TNA', 'TNA'), ('VIX', 'VIX')], max_length=5),
        ),
        migrations.AlterField(
            model_name='paletcontrol',
            name='destino',
            field=models.CharField(choices=[('SPO', 'SPO'), ('REC', 'REC'), ('SSA', 'SSA'), ('FOR', 'FOR'), ('MCZ', 'MCZ'), ('NAT', 'NAT'), ('JPA', 'JPA'), ('AJU', 'AJU'), ('VDC', 'VDC'), ('MG', 'MG'), ('CTG', 'CTG'), ('TCO', 'TCO'), ('UDI', 'UDI'), ('TNA', 'TNA'), ('VIX', 'VIX')], max_length=3),
        ),
        migrations.AlterField(
            model_name='paletcontrol',
            name='loc_atual',
            field=models.CharField(choices=[('SPO', 'SPO'), ('REC', 'REC'), ('SSA', 'SSA'), ('FOR', 'FOR'), ('MCZ', 'MCZ'), ('NAT', 'NAT'), ('JPA', 'JPA'), ('AJU', 'AJU'), ('VDC', 'VDC'), ('MG', 'MG'), ('CTG', 'CTG'), ('TCO', 'TCO'), ('UDI', 'UDI'), ('TNA', 'TNA'), ('VIX', 'VIX')], max_length=3),
        ),
        migrations.AlterField(
            model_name='paletcontrol',
            name='origem',
            field=models.CharField(choices=[('SPO', 'SPO'), ('REC', 'REC'), ('SSA', 'SSA'), ('FOR', 'FOR'), ('MCZ', 'MCZ'), ('NAT', 'NAT'), ('JPA', 'JPA'), ('AJU', 'AJU'), ('VDC', 'VDC'), ('MG', 'MG'), ('CTG', 'CTG'), ('TCO', 'TCO'), ('UDI', 'UDI'), ('TNA', 'TNA'), ('VIX', 'VIX')], max_length=3),
        ),
    ]
