# Generated by Django 3.2.6 on 2021-09-20 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0010_auto_20210909_1713'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cadastro',
            name='filial',
        ),
        migrations.AlterField(
            model_name='cadastro',
            name='empresa',
            field=models.CharField(max_length=100),
        ),
    ]
