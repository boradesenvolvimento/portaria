# Generated by Django 3.2.6 on 2021-10-29 11:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0037_auto_20211028_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='checklistfrota',
            name='autor',
            field=models.ForeignKey(default='1', on_delete=django.db.models.deletion.PROTECT, to='auth.user'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='manutencaofrota',
            name='autor',
            field=models.ForeignKey(default='1', on_delete=django.db.models.deletion.PROTECT, to='auth.user'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='paletecontrol',
            name='autor',
            field=models.ForeignKey(default='1', on_delete=django.db.models.deletion.PROTECT, to='auth.user'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='status',
            field=models.CharField(choices=[('ANDAMENTO', 'ANDAMENTO'), ('PENDENTE', 'PENDENTE'), ('CONCLUIDO', 'CONCLUIDO')], max_length=30),
        ),
    ]
