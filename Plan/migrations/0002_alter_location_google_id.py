# Generated by Django 5.1.3 on 2024-11-10 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='google_id',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
