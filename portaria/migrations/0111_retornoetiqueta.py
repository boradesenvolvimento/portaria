# Generated by Django 3.2.6 on 2022-03-22 11:38

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0110_auto_20220318_1142'),
    ]

    operations = [
        migrations.CreateModel(
            name='RetornoEtiqueta',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('nota_fiscal', models.CharField(max_length=15)),
                ('saida', models.DateField(default=django.utils.timezone.now)),
            ],
        ),
    ]