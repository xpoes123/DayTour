# Generated by Django 5.1.3 on 2024-11-10 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0005_itinerary_reviewed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itinerary',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
