# Generated by Django 3.2.6 on 2021-11-17 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0062_auto_20211117_0826'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='saldo',
            field=models.IntegerField(default='1'),
            preserve_default=False,
        ),
    ]
