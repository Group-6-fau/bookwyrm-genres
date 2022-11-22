"""Form for making a suggestion. Genre suggestion specifically."""
from django import forms
from django.utils.translation import gettext_lazy as _

from bookwyrm import models
from .custom_form import StyledForm


class SuggestionForm(StyledForm):
    """Form to suggest a genre."""
    class Meta:
        """Only a couple of fields we want."""
        model = models.SuggestedGenre

        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"aria-describedby": "desc_name"}),
            "description": forms.Textarea(
                attrs={
                    "aria-describedby": "desc_desc",
                    "class": "textarea",
                    "cols": "40",
                }
            ),
        }
