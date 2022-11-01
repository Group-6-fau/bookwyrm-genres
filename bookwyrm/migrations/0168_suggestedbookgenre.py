# Generated by Django 3.2.16 on 2022-11-01 01:44

import bookwyrm.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0167_minimumvotessetting'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuggestedBookGenre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('votes', bookwyrm.models.fields.IntegerField(default=1)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bookwyrm.work')),
                ('genre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bookwyrm.genre')),
            ],
        ),
    ]
