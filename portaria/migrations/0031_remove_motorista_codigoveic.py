# Generated by Django 3.2.6 on 2021-10-25 11:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0030_auto_20211022_1636'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='motorista',
            name='codigoveic',
        ),
    ]