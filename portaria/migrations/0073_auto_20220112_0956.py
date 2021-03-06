# Generated by Django 3.2.6 on 2022-01-12 09:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0072_checklistfrota_placacarreta2'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailmonitoramento',
            old_name='ult_rest_dt',
            new_name='ult_resp_dt',
        ),
        migrations.CreateModel(
            name='TicketChamado',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('solicitante', models.CharField(max_length=100)),
                ('servico', models.CharField(choices=[('DESENVOLVIMENTO', 'DESENVOLVIMENTO'), ('TI', 'TI'), ('PRAXIO', 'PRAXIO'), ('MANUTENCAO', 'MANUTENCAO')], max_length=15)),
                ('nome_tkt', models.CharField(max_length=150)),
                ('dt_abertura', models.DateTimeField(default=django.utils.timezone.now)),
                ('filial', models.CharField(choices=[('SPO', 'SPO'), ('REC', 'REC'), ('SSA', 'SSA'), ('FOR', 'FOR'), ('MCZ', 'MCZ'), ('NAT', 'NAT'), ('JPA', 'JPA'), ('AJU', 'AJU'), ('VDC', 'VDC'), ('MG', 'MG'), ('CTG', 'CTG'), ('TCO', 'TCO'), ('UDI', 'UDI'), ('TNA', 'TNA'), ('VIX', 'VIX')], max_length=3)),
                ('departamento', models.CharField(choices=[('DIRETORIA', 'DIRETORIA'), ('FATURAMENTO', 'FATURAMENTO'), ('FINANCEIRO', 'FINANCEIRO'), ('RH', 'RH'), ('FISCAL', 'FISCAL'), ('MONITORAMENTO', 'MONITORAMENTO'), ('OPERACIONAL', 'OPERACIONAL'), ('FROTA', 'FROTA'), ('EXPEDICAO', 'EXPEDICAO'), ('COMERCIAL', 'COMERCIAL'), ('JURIDICO', 'JURIDICO'), ('DESENVOLVIMENTO', 'DESENVOLVIMENTO'), ('TI', 'TI'), ('FILIAIS', 'FILIAIS')], max_length=15)),
                ('status', models.CharField(choices=[('ABERTO', 'ABERTO'), ('ANDAMENTO', 'ANDAMENTO'), ('CONCLUIDO', 'CONCLUIDO'), ('CANCELADO', 'CANCELADO')], max_length=9)),
                ('msg_id', models.CharField(max_length=100, unique=True)),
                ('responsavel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EmailChamado',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('assunto', models.CharField(max_length=100)),
                ('mensagem', models.TextField()),
                ('cc', models.CharField(blank=True, max_length=1000, null=True)),
                ('dt_envio', models.DateField()),
                ('email_id', models.CharField(max_length=100, unique=True)),
                ('ult_resp', models.TextField(blank=True, null=True)),
                ('ult_resp_dt', models.DateField(blank=True, null=True)),
                ('ult_resp_html', models.TextField(blank=True, null=True)),
                ('tkt_ref', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='portaria.ticketchamado')),
            ],
        ),
    ]
