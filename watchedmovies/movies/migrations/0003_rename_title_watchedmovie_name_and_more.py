# Generated by Django 5.1 on 2024-09-05 18:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0002_remove_watchedmovie_unique_original_title_release_date"),
    ]

    operations = [
        migrations.RenameField(
            model_name="watchedmovie",
            old_name="title",
            new_name="name",
        ),
        migrations.RenameField(
            model_name="watchedmovie",
            old_name="original_title",
            new_name="original_name",
        ),
    ]
