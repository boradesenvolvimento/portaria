# Generated by Django 3.2.6 on 2022-09-12 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0174_alter_movpalete_palete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bipagempalete',
            name='filial',
            field=models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('25', 'GVR'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE'), ('40', 'FMA')], max_length=3),
        ),
        migrations.AlterField(
            model_name='estoquesolicitacoes',
            name='filial',
            field=models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('25', 'GVR'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE'), ('40', 'FMA')], max_length=3),
        ),
        migrations.AlterField(
            model_name='etiquetasdocumento',
            name='garagem',
            field=models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('25', 'GVR'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE'), ('40', 'FMA')], max_length=3),
        ),
        migrations.AlterField(
            model_name='etiquetaspalete',
            name='filial',
            field=models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('25', 'GVR'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE'), ('40', 'FMA')], max_length=3),
        ),
        migrations.AlterField(
            model_name='registraterceirizados',
            name='filial',
            field=models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('25', 'GVR'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE'), ('40', 'FMA')], max_length=3),
        ),
        migrations.AlterField(
            model_name='solicitacoescompras',
            name='filial',
            field=models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('25', 'GVR'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE'), ('40', 'FMA')], max_length=3),
        ),
        migrations.AlterField(
            model_name='ticketchamado',
            name='filial',
            field=models.CharField(blank=True, choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('25', 'GVR'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE'), ('40', 'FMA')], max_length=3, null=True),
        ),
    ]