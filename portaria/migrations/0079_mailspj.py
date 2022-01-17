# Generated by Django 3.2.6 on 2022-01-17 13:51

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0078_alter_funcpj_banco'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailsPJ',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('data_envio', models.DateTimeField(default=django.utils.timezone.now)),
                ('data_pagamento', models.DateTimeField()),
                ('mensagem', models.TextField()),
                ('funcionario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='portaria.funcpj')),
            ],
        ),
    ]
