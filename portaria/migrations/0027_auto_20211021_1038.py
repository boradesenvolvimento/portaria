# Generated by Django 3.2.6 on 2021-10-21 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0026_auto_20211021_1007'),
    ]

    operations = [
        migrations.RenameField(
            model_name='funcpj',
            old_name='cnpj',
            new_name='cpf_cnpj',
        ),
        migrations.RenameField(
            model_name='nfservicopj',
            old_name='adiantamento',
            new_name='cred_convenio',
        ),
        migrations.RenameField(
            model_name='nfservicopj',
            old_name='ajuda_custo',
            new_name='desc_convenio',
        ),
        migrations.RenameField(
            model_name='nfservicopj',
            old_name='convenio',
            new_name='faculdade',
        ),
        migrations.RenameField(
            model_name='nfservicopj',
            old_name='premios_faculdade',
            new_name='outros_cred',
        ),
        migrations.RemoveField(
            model_name='funcpj',
            name='cpf',
        ),
        migrations.AddField(
            model_name='funcpj',
            name='adiantamento',
            field=models.IntegerField(default='1'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='funcpj',
            name='ajuda_custo',
            field=models.IntegerField(default='1'),
            preserve_default=False,
        ),
    ]