# Generated by Django 3.2.6 on 2021-11-10 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0048_auto_20211108_1736'),
    ]

    operations = [
        migrations.RenameField(
            model_name='feriaspj',
            old_name='proximas_ferias',
            new_name='vencimento',
        ),
        migrations.AddField(
            model_name='feriaspj',
            name='agendamento',
            field=models.DateField(blank=True, null=True),
        ),
    ]
