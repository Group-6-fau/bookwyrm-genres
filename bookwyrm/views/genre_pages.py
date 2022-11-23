"""View for an individual genre's page.
   Also contains JSON information."""
from django.shortcuts import render
from django.views.generic import (
    DetailView,
)

from bookwyrm.views.helpers import is_api_request
from bookwyrm.activitypub import ActivitypubResponse
from bookwyrm.models.book import Genre, Work


class GenreDetailView(DetailView):
    template_name = "genre/genre_detail_page.html"
    model = Genre

    def post(self, request):
        """Get the genres the user has selected."""

        # buttonSelection = request.POST.get("search_buttons")
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        """info about a genre"""
        if is_api_request(request):

            return ActivitypubResponse(super().get_object().to_activity())

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """We can get some sample books."""
        context = super().get_context_data(**kwargs)
        context["demo_books"] = Work.objects.filter(genres=self.get_object())[:4]
        return context
