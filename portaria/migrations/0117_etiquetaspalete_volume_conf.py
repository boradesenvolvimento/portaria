# Generated by Django 3.2.6 on 2022-03-25 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0116_auto_20220325_1234'),
    ]

    operations = [
        migrations.AddField(
            model_name='etiquetaspalete',
            name='volume_conf',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
