"""All the views that lets us modify genres."""
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DeleteView,
)

from bookwyrm.models.book import Genre
from bookwyrm.forms import GenreForm


class ManageGenreHome(ListView):
    """Get a list of all of our genres in the admin page."""

    paginate_by = 15
    template_name = "settings/genres/genre_manage_home.html"
    model = Genre
    ordering = ["genre_name"]


class ModifyGenre(UpdateView):
    """Separate page for modifying each genre in admin page."""

    template_name = "settings/genres/genre_mod.html"
    model = Genre
    form_class = GenreForm
    success_url = reverse_lazy("settings-genres")


class CreateGenre(CreateView):
    """Page for creating a new genre."""

    template_name = "settings/genres/genre_add.html"
    model = Genre
    form_class = GenreForm
    success_url = reverse_lazy("settings-genres")


class RemoveGenre(DeleteView):
    "Page for removing a genre."

    template_name = "settings/genres/genre_delete.html"
    model = Genre
    success_url = reverse_lazy("settings-genres")
