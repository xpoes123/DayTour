# Generated by Django 5.1.3 on 2024-11-10 13:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0006_alter_itinerary_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itinerary',
            name='locations',
        ),
        migrations.AddField(
            model_name='itinerary',
            name='locations',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
