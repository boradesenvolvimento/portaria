# Generated by Django 3.2.6 on 2021-11-08 16:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0046_auto_20211108_1306'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feriaspj',
            name='valor_pagar',
        ),
    ]