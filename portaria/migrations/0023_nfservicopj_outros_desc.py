# Generated by Django 3.2.6 on 2021-10-19 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0022_funcpj_tipo_contrato'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfservicopj',
            name='outros_desc',
            field=models.IntegerField(default='1'),
            preserve_default=False,
        ),
    ]
