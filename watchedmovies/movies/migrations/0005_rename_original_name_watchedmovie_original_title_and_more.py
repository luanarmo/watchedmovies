# Generated by Django 5.1 on 2024-09-05 18:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0004_rename_release_date_watchedmovie_first_air_date"),
    ]

    operations = [
        migrations.RenameField(
            model_name="watchedmovie",
            old_name="original_name",
            new_name="original_title",
        ),
        migrations.RenameField(
            model_name="watchedmovie",
            old_name="first_air_date",
            new_name="release_date",
        ),
        migrations.RenameField(
            model_name="watchedmovie",
            old_name="name",
            new_name="title",
        ),
    ]
