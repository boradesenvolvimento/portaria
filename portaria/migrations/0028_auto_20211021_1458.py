# Generated by Django 3.2.6 on 2021-10-21 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0027_auto_20211021_1038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='funcpj',
            name='adiantamento',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='funcpj',
            name='ajuda_custo',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='funcpj',
            name='salario',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='nfservicopj',
            name='cred_convenio',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='nfservicopj',
            name='desc_convenio',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='nfservicopj',
            name='faculdade',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='nfservicopj',
            name='outros_cred',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='nfservicopj',
            name='outros_desc',
            field=models.FloatField(),
        ),
    ]
