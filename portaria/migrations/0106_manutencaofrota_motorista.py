# Generated by Django 3.2.6 on 2022-03-11 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0105_auto_20220311_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='manutencaofrota',
            name='motorista',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
