# Generated by Django 3.2.6 on 2022-03-11 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0103_auto_20220311_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manutencaofrota',
            name='socorro',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='servjoinmanu',
            name='feito',
            field=models.BooleanField(null=True),
        ),
    ]
