# Generated by Django 3.2.6 on 2021-10-22 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0028_auto_20211021_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cadastro',
            name='hr_chegada',
            field=models.DateTimeField(blank=True),
        ),
    ]
