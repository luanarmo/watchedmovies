# Generated by Django 4.2.9 on 2024-07-02 20:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False, verbose_name="email verified"),
        ),
    ]
