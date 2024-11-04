# Generated by Django 5.1 on 2024-11-04 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0009_viewdetails_watched_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="viewdetails",
            name="language",
            field=models.CharField(
                blank=True,
                choices=[
                    ("en", "English"),
                    ("es", "Spanish"),
                    ("fr", "French"),
                    ("de", "German"),
                    ("it", "Italian"),
                    ("pt", "Portuguese"),
                    ("ru", "Russian"),
                    ("ja", "Japanese"),
                    ("zh", "Chinese"),
                    ("ko", "Korean"),
                    ("ar", "Arabic"),
                    ("hi", "Hindi"),
                    ("other", "Other"),
                ],
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="viewdetails",
            name="place",
            field=models.CharField(
                blank=True,
                choices=[
                    ("cinema", "Movie Theater"),
                    ("home", "Home"),
                    ("friend", "Friend's House"),
                    ("other", "Other"),
                ],
                max_length=255,
            ),
        ),
    ]
