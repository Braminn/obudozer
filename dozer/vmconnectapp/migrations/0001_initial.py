# Generated by Django 4.2.14 on 2024-09-20 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Oss',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prettyName', models.CharField(max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Операционные системы',
                'verbose_name_plural': 'Операционные системы',
                'ordering': ('prettyName',),
            },
        ),
        migrations.CreateModel(
            name='Vms',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('powerState', models.CharField(max_length=50, null=True)),
                ('ipAdress', models.CharField(max_length=50, null=True)),
                ('toolsStatus', models.CharField(max_length=50, null=True)),
                ('vmtoolsdescription', models.CharField(max_length=50, null=True)),
                ('vmtoolsversionNumber', models.IntegerField(null=True)),
                ('prettyName', models.CharField(max_length=50, null=True)),
                ('familyName', models.CharField(max_length=50, null=True)),
                ('distroName', models.CharField(max_length=50, null=True)),
                ('distroVersion', models.CharField(max_length=50, null=True)),
                ('kernelVersion', models.CharField(max_length=50, null=True)),
                ('bitness', models.CharField(max_length=50, null=True)),
            ],
        ),
    ]
