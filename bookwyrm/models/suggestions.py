import re

from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import models, transaction
from django.db.models import Prefetch
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from bookwyrm.preview_images import generate_edition_preview_image_task
from bookwyrm.settings import (
    DOMAIN,
    DEFAULT_LANGUAGE,
    ENABLE_PREVIEW_IMAGES,
    ENABLE_THUMBNAIL_GENERATION,
)

from .book import Genre
from .activitypub_mixin import OrderedCollectionPageMixin, ObjectMixin
from .base_model import BookWyrmModel
from . import fields

# This will be a local class, always. Nothing to do with ActivityPub.
class MinimumVotesSetting(models.Model):
    minimum_votes = models.IntegerField(default=10)

    def __str__(self):
        return self.minimum_votes

class SuggestedGenre(models.Model):
    '''When users suggest a genre, it will create an instance of this class and begin counting votes.
       Restrictions on how many times a user can suggest a genre is still up for discussion.'''
    name = fields.CharField(max_length=40)
    description = fields.CharField(max_length=500)
    votes = fields.IntegerField(default = 1)
    
    def __str__(self):
        return self.name

    def autoApprove(self):
        '''If a certain category gets a certain number of votes, it will approve itself and create a new genre.'''
        if(self.votes > MinimumVotesSetting):
            genre = Genre.objects.create_genre(self.name, self.description)
            genre.save()
            self.delete()

class SuggestedBookGenre(models.Model):
    '''When users suggest a genre, it will create an instance of this class and begin counting votes.
       Restrictions on how many times a user can suggest a genre is still up for discussion.'''
    genre = models.ForeignKey("Genre", on_delete=models.CASCADE, null=False)
    votes = fields.IntegerField(default = 1)
    book = models.ForeignKey("Work", on_delete=models.CASCADE, null=False)
    
    def __str__(self):
        return self.name

    def autoApprove(self):
        '''If a certain category gets a certain number of votes, it will approve itself and create a new genre.'''
        if(self.votes > MinimumVotesSetting):
            self.book = Genre.objects.create_genre(self.name, self.description)
            genre.save()
            self.delete()