# Generated by Django 3.2.16 on 2022-10-29 02:17

import bookwyrm.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0165_auto_20221028_2345'),
    ]

    operations = [
        migrations.AddField(
            model_name='genre',
            name='name',
            field=bookwyrm.models.fields.CharField(default=bookwyrm.models.fields.CharField(max_length=40), max_length=500),
        ),
    ]
