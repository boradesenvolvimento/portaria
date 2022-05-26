# Generated by Django 3.2.6 on 2022-05-25 16:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import portaria.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0133_auto_20220525_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistraTerceirizados',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('fornecedor', models.CharField(max_length=150)),
                ('nome_funcionario', models.CharField(max_length=100)),
                ('rg', models.CharField(max_length=15)),
                ('cpf', models.CharField(max_length=11, validators=[portaria.models.only_int])),
                ('data', models.DateTimeField(default=django.utils.timezone.now)),
                ('valor', models.FloatField()),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]