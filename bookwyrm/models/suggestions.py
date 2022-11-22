"""Models for anything related to suggestion. Either suggesting
   a genre for a book or a genre itself."""
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


from .book import Genre, Edition
from .user import User
from . import fields

# This will be a local class, always. Nothing to do with ActivityPub.
class MinimumVotesSetting(models.Model):
    minimum_genre_votes = models.IntegerField(default=10)
    minimum_book_votes = models.IntegerField(default=10)


class SuggestedGenre(models.Model):
    """When users suggest a genre, it will create an instance of this class and begin counting votes.
    Restrictions on how many times a user can suggest a genre is still up for discussion."""

    name = fields.CharField(max_length=40)
    description = fields.CharField(max_length=500)
    votes = fields.IntegerField(default=1)
    users = models.ManyToManyField(User, blank=False)

    def __str__(self):
        return self.name

    def auto_approve(self):
        """If a certain category gets a certain number of votes, it will approve itself and create a new genre."""
        minimum_votes = MinimumVotesSetting.objects.get(id=1)

        if self.votes >= minimum_votes.minimum_genre_votes:
            genre = Genre.objects.create_genre(self.name, self.description)
            genre.save()
            self.delete()


class SuggestedBookGenre(models.Model):
    """When users suggest a genre, it will create an instance of this class and begin counting votes.
    Restrictions on how many times a user can suggest a genre is still up for discussion."""

    genre = models.ForeignKey("Genre", on_delete=models.CASCADE, null=False)
    votes = fields.IntegerField(default=1)
    book = models.ForeignKey("Work", on_delete=models.CASCADE, null=False)
    users = models.ManyToManyField(User, blank=False)

    def auto_approve(self):
        """If a certain category gets a certain number of votes, it will approve itself and create a new genre."""
        minimum_votes = MinimumVotesSetting.objects.get(id=1)

        if self.votes >= minimum_votes.minimum_book_votes:
            self.book.genres.add(self.genre)
            editions = Edition.objects.filter(Q(parent_work=self.book))
            for edition in editions:
                edition.genres.add(self.genre)
            self.delete()
