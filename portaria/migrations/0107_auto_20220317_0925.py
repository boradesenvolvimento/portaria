# Generated by Django 3.2.6 on 2022-03-17 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0106_manutencaofrota_motorista'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='checklistfrota',
            name='obs',
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='obs_carreta',
            field=models.TextField(blank=True, verbose_name='Obs Carreta'),
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='obs_cavalo',
            field=models.TextField(blank=True, verbose_name='Obs Cavalo'),
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_25',
            field=models.BooleanField(default=1, verbose_name='Parabrisa em boas condições?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_26',
            field=models.BooleanField(default=1, verbose_name='Ar condicionado funcionando?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_27',
            field=models.BooleanField(default=1, verbose_name='Pintura do cavalo em boas condições?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_28',
            field=models.BooleanField(default=1, verbose_name='Extintor em boas condições?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_29',
            field=models.BooleanField(default=1, verbose_name='Pneus dianteiros em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_30',
            field=models.BooleanField(default=1, verbose_name='Pneus tração em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_31',
            field=models.BooleanField(default=1, verbose_name='Pneus traseiros em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_32',
            field=models.BooleanField(default=1, verbose_name='Lubrificação está em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_33',
            field=models.BooleanField(default=1, verbose_name='Alinhamento está em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p2_34',
            field=models.BooleanField(default=1, verbose_name='Balanceamento está em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_10',
            field=models.BooleanField(default=1, verbose_name='Plotagem em boas condições?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_11',
            field=models.BooleanField(default=1, verbose_name='Amortecedores em boas condições?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_12',
            field=models.BooleanField(default=1, verbose_name='A carreta está lavada?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_13',
            field=models.BooleanField(default=1, verbose_name='Pneus dianteiros em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_14',
            field=models.BooleanField(default=1, verbose_name='Pneus tração em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_15',
            field=models.BooleanField(default=1, verbose_name='Pneus traseiros em bom estado?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_16',
            field=models.BooleanField(default=1, verbose_name='Lubrificação em boas condições?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_17',
            field=models.BooleanField(default=1, verbose_name='Alinhamento em boas condições?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_18',
            field=models.BooleanField(default=1, verbose_name='Balanceamento em boas condições?'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checklistfrota',
            name='p3_19',
            field=models.BooleanField(default=1, verbose_name='Carreta tem divisória?'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_12',
            field=models.BooleanField(verbose_name='Bateria em boas condições?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_13',
            field=models.BooleanField(verbose_name='Freio de emergência funcionando?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_14',
            field=models.BooleanField(verbose_name='Alarme sonoro da ré funcionando?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_15',
            field=models.BooleanField(verbose_name='Existe vazamentos de óleo de motor?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_16',
            field=models.BooleanField(verbose_name='Existe vazamentos de ar?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_17',
            field=models.BooleanField(verbose_name='Existe vazamento de óleo hidráulico?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_18',
            field=models.BooleanField(verbose_name='Existe vazamento de água no radiador?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_19',
            field=models.BooleanField(verbose_name='As mangueiras estão em boas condições?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_20',
            field=models.BooleanField(verbose_name='Lonas de freio em boas condições?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_21',
            field=models.BooleanField(verbose_name='Amortecedor em boas condições?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_22',
            field=models.BooleanField(verbose_name='A suspensão está em boas condições?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_23',
            field=models.BooleanField(verbose_name='O carro está limpo e higienizado?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p2_24',
            field=models.BooleanField(verbose_name='Limpador de parabrisa funcionando ?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_1',
            field=models.BooleanField(verbose_name='Luzes de advertência das laterais funcionando?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_2',
            field=models.BooleanField(verbose_name='Estepes em bom estado?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_3',
            field=models.BooleanField(verbose_name='Thermoking está em boas condições?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_4',
            field=models.BooleanField(verbose_name='Carroceria, assoalho e baú em boas condições?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_5',
            field=models.BooleanField(verbose_name='Luz de freio funcionando?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_6',
            field=models.BooleanField(verbose_name='Luz de ré funcionando ?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_7',
            field=models.BooleanField(verbose_name='Luzes da lanterna traseira direita funciona?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_8',
            field=models.BooleanField(verbose_name='Luzes da lanterna traseira esquerda funciona?'),
        ),
        migrations.AlterField(
            model_name='checklistfrota',
            name='p3_9',
            field=models.BooleanField(verbose_name='Veículo plotado?'),
        ),
    ]
