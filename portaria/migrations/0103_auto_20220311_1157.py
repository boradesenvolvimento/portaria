# Generated by Django 3.2.6 on 2022-03-11 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0102_cadastro_kilometragem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='manutencaofrota',
            name='tp_servico',
        ),
        migrations.AddField(
            model_name='servjoinmanu',
            name='feito',
            field=models.BooleanField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='dt_entrada',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='filial',
            field=models.CharField(blank=True, choices=[('SPO', 'SPO'), ('VDC', 'VDC')], max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='km_atual',
            field=models.IntegerField(blank=True, null=True, verbose_name='Kilometragem atual'),
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='local_manu',
            field=models.CharField(blank=True, choices=[('I', 'INTERNO'), ('E', 'EXTERNO')], max_length=1, null=True, verbose_name='Local manutenção'),
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='observacao',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='prev_entrega',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='status',
            field=models.CharField(blank=True, choices=[('ANDAMENTO', 'ANDAMENTO'), ('PENDENTE', 'PENDENTE'), ('CONCLUIDO', 'CONCLUIDO')], max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='manutencaofrota',
            name='tp_manutencao',
            field=models.CharField(blank=True, choices=[('PREVENTIVA', 'PREVENTIVA'), ('CORRETIVA', 'CORRETIVA')], max_length=10, null=True, verbose_name='Tipo manutenção'),
        ),
    ]
