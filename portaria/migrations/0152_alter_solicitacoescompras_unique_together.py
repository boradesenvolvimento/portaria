# Generated by Django 3.2.6 on 2022-07-01 09:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0151_auto_20220630_1238'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='solicitacoescompras',
            unique_together={('filial', 'nr_solic')},
        ),
    ]
