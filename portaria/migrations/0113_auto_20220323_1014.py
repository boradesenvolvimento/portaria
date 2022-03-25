# Generated by Django 3.2.6 on 2022-03-23 10:14

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0112_alter_retornoetiqueta_nota_fiscal'),
    ]

    operations = [
        migrations.CreateModel(
            name='EtiquetasDocumento',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('garagem', models.CharField(choices=[('1', 'SPO'), ('2', 'REC'), ('3', 'SSA'), ('4', 'FOR'), ('5', 'MCZ'), ('6', 'NAT'), ('7', 'JPA'), ('8', 'AJU'), ('9', 'VDC'), ('10', 'MG'), ('20', 'CTG'), ('21', 'TCO'), ('22', 'UDI'), ('23', 'TMA'), ('24', 'VIX'), ('30', 'BMA'), ('31', 'BPE'), ('32', 'BEL'), ('33', 'BPB'), ('34', 'SLZ'), ('35', 'BAL'), ('36', 'THE')], max_length=3)),
                ('tp_doc', models.CharField(choices=[('8', 'NFS'), ('57', 'CTE')], max_length=3)),
                ('nr_doc', models.CharField(max_length=20)),
                ('nota', models.CharField(max_length=10)),
                ('volume', models.PositiveSmallIntegerField()),
                ('pub_date', models.DateField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.RemoveField(
            model_name='bipagemetiqueta',
            name='rom_ref',
        ),
        migrations.DeleteModel(
            name='EtiquetasRomaneio',
        ),
        migrations.AddField(
            model_name='bipagemetiqueta',
            name='doc_ref',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='portaria.etiquetasdocumento'),
            preserve_default=False,
        ),
    ]