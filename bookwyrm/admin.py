""" models that will show up in django admin for superuser """
from django.contrib import admin
from bookwyrm import models

admin.site.register(models.User)
admin.site.register(models.FederatedServer)
admin.site.register(models.Connector)
admin.site.register(models.book.Genre)
admin.site.register(models.suggestions.SuggestedGenre)
admin.site.register(models.suggestions.SuggestedBookGenre)
admin.site.register(models.suggestions.MinimumVotesSetting)
admin.site.register(models.Author)
