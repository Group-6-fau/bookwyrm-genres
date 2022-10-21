""" class views for login/register views """
import time

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters

from bookwyrm import forms, models
from bookwyrm.settings import DOMAIN
from bookwyrm.views.helpers import set_language


# pylint: disable=no-self-use
class Login(View):
    """authenticate an existing user"""

    def get(self, request, confirmed=None):
        """login page"""
        if request.user.is_authenticated:
            return redirect("/")
        # send user to the login page
        data = {
            "show_confirmed_email": confirmed,
            "login_form": forms.LoginForm(),
            "register_form": forms.RegisterForm(),
        }
        return TemplateResponse(request, "landing/login.html", data)

    # pylint: disable=too-many-return-statements
    @sensitive_variables("password")
    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request):
        """authentication action"""
        if request.user.is_authenticated:
            return redirect("/")
        login_form = forms.LoginForm(request.POST)

        localname = login_form.data.get("localname")

        if "@" in localname:  # looks like an email address to me
            try:
                username = models.User.objects.get(email=localname).username
            except models.User.DoesNotExist:  # maybe it's a full username?
                username = localname
        else:
            username = f"{localname}@{DOMAIN}"
        password = login_form.data.get("password")

        # perform authentication
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # if 2fa is set, don't log them in until they enter the right code
            if user.two_factor_auth:
                request.session["2fa_user"] = user.username
                request.session["2fa_auth_time"] = time.time()
                return redirect("login-with-2fa")

            # otherwise, successful login
            login(request, user)
            user.update_active_date()
            if request.POST.get("first_login"):
                return set_language(user, redirect("get-started-profile"))

            if user.two_factor_auth is None:
                # set to false so this page doesn't pop up again
                user.two_factor_auth = False
                user.save(broadcast=False, update_fields=["two_factor_auth"])

                # show the 2fa prompt page
                return set_language(user, redirect("prompt-2fa"))

            return set_language(user, redirect("/"))

        # maybe the user is pending email confirmation
        if models.User.objects.filter(
            username=username, is_active=False, deactivation_reason="pending"
        ).exists():
            return redirect("confirm-email")

        # login errors
        login_form.non_field_errors = _("Username or password are incorrect")
        register_form = forms.RegisterForm()
        data = {"login_form": login_form, "register_form": register_form}
        return TemplateResponse(request, "landing/login.html", data)


@method_decorator(login_required, name="dispatch")
class Logout(View):
    """log out"""

    def post(self, request):
        """done with this place! outa here!"""
        logout(request)
        return redirect("/")
