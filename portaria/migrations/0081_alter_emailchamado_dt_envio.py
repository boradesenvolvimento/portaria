# Generated by Django 3.2.6 on 2022-01-18 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0080_alter_mailspj_data_pagamento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailchamado',
            name='dt_envio',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
