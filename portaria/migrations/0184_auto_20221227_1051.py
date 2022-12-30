# Generated by Django 3.2.6 on 2022-12-27 10:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0183_alter_estoqueitens_desc'),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('desc', models.CharField(max_length=100)),
            ],
        ),
        migrations.RemoveField(
            model_name='estoqueitens',
            name='desc',
        ),
        migrations.RemoveField(
            model_name='estoqueitens',
            name='quantidade',
        ),
        migrations.RemoveField(
            model_name='estoqueitens',
            name='tamanho',
        ),
        migrations.RemoveField(
            model_name='estoqueitens',
            name='tipo',
        ),
        migrations.AddField(
            model_name='estoqueitens',
            name='grupo',
            field=models.CharField(default='camisetas', max_length=100),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Tamanho',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('tam', models.CharField(max_length=5)),
                ('quantidade', models.PositiveSmallIntegerField()),
                ('item', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='portaria.item')),
            ],
        ),
        migrations.AddField(
            model_name='item',
            name='estoque',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='portaria.estoqueitens'),
        ),
    ]
