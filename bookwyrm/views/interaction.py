""" boosts and favs """
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View

from bookwyrm import models
from .helpers import is_api_request


# pylint: disable= no-self-use
@method_decorator(login_required, name="dispatch")
class Favorite(View):
    """like a status"""

    def post(self, request, status_id):
        """create a like"""
        cache.delete(f"fav-{request.user.id}-{status_id}")
        status = models.Status.objects.get(id=status_id)
        try:
            models.Favorite.objects.create(status=status, user=request.user)
        except IntegrityError:
            # you already fav'ed that
            return HttpResponseBadRequest()

        if is_api_request(request):
            return HttpResponse()
        return redirect("/")


@method_decorator(login_required, name="dispatch")
class Unfavorite(View):
    """take back a fav"""

    def post(self, request, status_id):
        """unlike a status"""
        cache.delete(f"fav-{request.user.id}-{status_id}")
        status = models.Status.objects.get(id=status_id)
        try:
            favorite = models.Favorite.objects.get(status=status, user=request.user)
        except models.Favorite.DoesNotExist:
            # can't find that status, idk
            return HttpResponseNotFound()

        favorite.delete()
        if is_api_request(request):
            return HttpResponse()
        return redirect("/")


@method_decorator(login_required, name="dispatch")
class FollowGenre(View):
    """follow a genre"""

    def post(self, request, gen_pk):
        """follow a genre"""
        genre = models.Genre.objects.get(id=gen_pk)
        user = models.User.objects.get(id=request.user.id)
        user.followed_genres.add(genre)
        return redirect("genre-view", gen_pk=genre.id)


@method_decorator(login_required, name="dispatch")
class UnFollowGenre(View):
    """unfollow a genre"""

    # pylint: disable=invalid-name
    def post(self, request, pk):
        """unlike a status"""
        genre = models.Genre.objects.get(id=pk)
        user = models.User.objects.get(id=request.user.id)
        user.followed_genres.remove(genre)
        return redirect("genre-view", pk=genre.id)


@method_decorator(login_required, name="dispatch")
class Boost(View):
    """boost a status"""

    def post(self, request, status_id):
        """boost a status"""
        cache.delete(f"boost-{request.user.id}-{status_id}")
        status = models.Status.objects.get(id=status_id)
        # is it boostable?
        if not status.boostable:
            return HttpResponseBadRequest()

        if models.Boost.objects.filter(
            boosted_status=status, user=request.user
        ).exists():
            # you already boosted that.
            return redirect("/")

        models.Boost.objects.create(
            boosted_status=status,
            privacy=status.privacy,
            user=request.user,
        )
        if is_api_request(request):
            return HttpResponse()
        return redirect("/")


@method_decorator(login_required, name="dispatch")
class Unboost(View):
    """boost a status"""

    def post(self, request, status_id):
        """boost a status"""
        cache.delete(f"boost-{request.user.id}-{status_id}")
        status = models.Status.objects.get(id=status_id)
        boost = models.Boost.objects.filter(
            boosted_status=status, user=request.user
        ).first()

        boost.delete()
        if is_api_request(request):
            return HttpResponse()
        return redirect("/")
