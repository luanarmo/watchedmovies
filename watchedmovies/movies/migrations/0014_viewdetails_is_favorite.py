from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0013_alter_watchedmovie_popularity"),
    ]

    operations = [
        migrations.AddField(
            model_name="viewdetails",
            name="is_favorite",
            field=models.BooleanField(default=False),
        ),
    ]
