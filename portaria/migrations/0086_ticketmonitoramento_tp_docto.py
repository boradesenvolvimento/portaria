# Generated by Django 3.2.6 on 2022-01-26 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0085_auto_20220125_1116'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketmonitoramento',
            name='tp_docto',
            field=models.CharField(choices=[(57, 'CTE'), (8, 'NFS')], default=8, max_length=3),
            preserve_default=False,
        ),
    ]