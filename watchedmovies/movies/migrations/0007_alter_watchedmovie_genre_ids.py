# Generated by Django 5.1 on 2024-09-06 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0006_alter_watchedmovie_overview_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="watchedmovie",
            name="genre_ids",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
