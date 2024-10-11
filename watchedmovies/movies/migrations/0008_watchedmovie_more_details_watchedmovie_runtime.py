# Generated by Django 5.1 on 2024-10-11 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0007_alter_watchedmovie_genre_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="watchedmovie",
            name="more_details",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="watchedmovie",
            name="runtime",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
