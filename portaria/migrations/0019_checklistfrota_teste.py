# Generated by Django 3.2.6 on 2021-10-14 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0018_nfservicopj_data_emissao'),
    ]

    operations = [
        migrations.AddField(
            model_name='checklistfrota',
            name='teste',
            field=models.BooleanField(default='1'),
            preserve_default=False,
        ),
    ]
