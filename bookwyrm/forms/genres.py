"""Our form for letting us modify genres."""
from django import forms

from bookwyrm import models
from .custom_form import StyledForm


class GenreForm(StyledForm):
    """Form for modifying an existing genre. Can be seen in the admin page."""

    class Meta:
        """Only the name and description can be modified."""

        model = models.Genre

        fields = ("genre_name", "description")

        widgets = {
            "genre_name": forms.TextInput(attrs={"aria-describedby": "desc_name"}),
            "genre_description": forms.Textarea(
                attrs={
                    "aria-describedby": "desc_desc",
                    "class": "textarea",
                    "cols": "40",
                }
            ),
        }
