# Generated by Django 3.2.6 on 2022-01-17 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0077_auto_20220114_1615'),
    ]

    operations = [
        migrations.AlterField(
            model_name='funcpj',
            name='banco',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
