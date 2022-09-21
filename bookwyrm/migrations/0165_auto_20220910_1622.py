# Generated by Django 3.2.15 on 2022-09-10 16:22

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0164_auto_20220910_1559'),
    ]

    operations = [
        migrations.AddField(
            model_name='genrenotification',
            name='read',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='genrenotification',
            name='related_users',
            field=models.ManyToManyField(null=True, related_name='notifications_to', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterIndexTogether(
            name='genrenotification',
            index_together=set(),
        ),
        migrations.RemoveField(
            model_name='genrenotification',
            name='to_user',
        ),
        migrations.RemoveField(
            model_name='genrenotification',
            name='unread',
        ),
    ]
