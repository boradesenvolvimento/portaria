# Generated by Django 3.2.6 on 2021-11-12 15:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0059_auto_20211112_1541'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paletecontrol',
            name='mov_palete_fk',
        ),
    ]
