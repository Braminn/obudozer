# Generated by Django 4.2.14 on 2024-11-24 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vmconnectapp', '0007_alter_oss_options_vms_owner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
    ]
