# Generated by Django 3.2.6 on 2022-05-25 15:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0132_produtossolicitacoes_solicitacoescompras'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitacoescompras',
            name='departamento',
            field=models.CharField(blank=True, choices=[('DIRETORIA', 'DIRETORIA'), ('FATURAMENTO', 'FATURAMENTO'), ('FINANCEIRO', 'FINANCEIRO'), ('RH', 'RH'), ('FISCAL', 'FISCAL'), ('MONITORAMENTO', 'MONITORAMENTO'), ('OPERACIONAL', 'OPERACIONAL'), ('FROTA', 'FROTA'), ('EXPEDICAO', 'EXPEDICAO'), ('COMERCIAL', 'COMERCIAL'), ('JURIDICO', 'JURIDICO'), ('DESENVOLVIMENTO', 'DESENVOLVIMENTO'), ('TI', 'TI'), ('FILIAIS', 'FILIAIS')], max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='solicitacoescompras',
            name='responsavel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='responsavelcompras', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='solicitacoescompras',
            name='autor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='autorcompras', to=settings.AUTH_USER_MODEL),
        ),
    ]
