# Generated by Django 3.2.6 on 2021-11-24 10:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0060_alter_emailmonitoramento_cc'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketMonitoramento',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('nome_tkt', models.CharField(max_length=100)),
                ('dt_abertura', models.DateField()),
                ('cliente', models.CharField(max_length=50)),
                ('responsavel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='emailmonitoramento',
            name='tkt_ref',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='portaria.ticketmonitoramento'),
            preserve_default=False,
        ),
    ]
