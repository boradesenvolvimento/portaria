# Generated by Django 3.2.6 on 2022-05-02 15:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('portaria', '0122_auto_20220502_1450'),
    ]

    operations = [
        migrations.AlterField(
            model_name='justificativaentrega',
            name='autor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
