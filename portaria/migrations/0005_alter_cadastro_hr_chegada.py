# Generated by Django 3.2.6 on 2021-09-13 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0004_alter_cadastro_empresa'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cadastro',
            name='hr_chegada',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
