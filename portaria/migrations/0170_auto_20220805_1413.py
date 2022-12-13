# Generated by Django 3.2.6 on 2022-08-05 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0169_auto_20220803_0850'),
    ]

    operations = [
        migrations.AddField(
            model_name='romxml',
            name='bairro',
            field=models.CharField(default='N/A', max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='romxml',
            name='cep',
            field=models.CharField(default='N/A', max_length=8),
            preserve_default=False,
        ),
    ]