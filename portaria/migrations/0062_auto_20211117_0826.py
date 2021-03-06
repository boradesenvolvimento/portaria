# Generated by Django 3.2.6 on 2021-11-17 08:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0061_cliente_intex'),
    ]

    operations = [
        migrations.AddField(
            model_name='paletecontrol',
            name='posse_bora',
            field=models.BooleanField(default=1),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='intex',
            field=models.CharField(choices=[('INTERNO', 'INTERNO'), ('CLIENTE', 'CLIENTE')], max_length=7),
        ),
        migrations.AlterField(
            model_name='paletecontrol',
            name='empresa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portaria.cliente'),
        ),
    ]
