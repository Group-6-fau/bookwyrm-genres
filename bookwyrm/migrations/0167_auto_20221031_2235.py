# Generated by Django 3.2.16 on 2022-10-31 22:35

import bookwyrm.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bookwyrm", "0166_genre_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="genre",
            name="genre_name",
            field=bookwyrm.models.fields.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name="genre",
            name="name",
            field=bookwyrm.models.fields.CharField(
                default=bookwyrm.models.fields.CharField(max_length=500), max_length=500
            ),
        ),
    ]
