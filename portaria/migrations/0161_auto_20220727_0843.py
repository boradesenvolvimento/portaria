# Generated by Django 3.2.6 on 2022-07-27 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0160_solicitacoescompras_anexo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitacoescompras',
            name='categoria',
            field=models.CharField(max_length=15),
        ),
        migrations.AlterField(
            model_name='solicitacoescompras',
            name='data',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='solicitacoescompras',
            name='status',
            field=models.CharField(max_length=15),
        ),
    ]
