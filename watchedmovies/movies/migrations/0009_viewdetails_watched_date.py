# Generated by Django 5.1 on 2024-11-04 01:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0008_watchedmovie_more_details_watchedmovie_runtime"),
    ]

    operations = [
        migrations.AddField(
            model_name="viewdetails",
            name="watched_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]