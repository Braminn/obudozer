# Generated by Django 4.2.14 on 2024-11-17 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vmconnectapp', '0006_vms_cms'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='oss',
            options={'ordering': ('prettyName',), 'verbose_name': 'Операционные системы', 'verbose_name_plural': 'Операционная система'},
        ),
        migrations.AddField(
            model_name='vms',
            name='owner',
            field=models.CharField(max_length=150, null=True),
        ),
    ]
