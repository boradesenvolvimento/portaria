# Generated by Django 3.2.6 on 2022-05-26 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0136_solicitacoesentradas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitacoesentradas',
            name='file1',
            field=models.FileField(blank=True, null=True, upload_to='cpr/%Y/%m/%d'),
        ),
        migrations.AlterField(
            model_name='solicitacoesentradas',
            name='file2',
            field=models.FileField(blank=True, null=True, upload_to='cpr/%Y/%m/%d'),
        ),
        migrations.AlterField(
            model_name='solicitacoesentradas',
            name='file3',
            field=models.FileField(blank=True, null=True, upload_to='cpr/%Y/%m/%d'),
        ),
    ]
