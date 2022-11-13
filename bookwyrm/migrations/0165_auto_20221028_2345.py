# Generated by Django 3.2.16 on 2022-10-28 23:45

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0164_merge_0159_auto_20220924_0634_0163_genre_remote_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='genre',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='genre',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
