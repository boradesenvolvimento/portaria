# Generated by Django 3.2.6 on 2021-11-12 14:52

from django.db import migrations, models
import portaria.models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0056_auto_20211112_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='funcpj',
            name='cpf_cnpj',
            field=models.CharField(max_length=14, validators=[portaria.models.only_int]),
        ),
        migrations.AlterField(
            model_name='motorista',
            name='CPF',
            field=models.CharField(max_length=11, validators=[portaria.models.only_int]),
        ),
    ]
