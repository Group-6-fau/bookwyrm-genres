""" search views"""
import re

from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import Paginator
from django.db.models.functions import Greatest
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.views import View

from csp.decorators import csp_update

from bookwyrm import models
from bookwyrm.connectors import connector_manager
from bookwyrm.book_search import search, format_search_result, search_genre
from bookwyrm.settings import PAGE_LENGTH
from bookwyrm.utils import regex
from .helpers import is_api_request
from .helpers import handle_remote_webfinger


# pylint: disable= no-self-use
class Search(View):
    """search users or books"""

    @csp_update(IMG_SRC="*")
    def get(self, request):
        """that search bar up top"""

        search_type = request.GET.get("type")

        if is_api_request(request):
            return api_book_search(request, search_type)

        local_gens = list(models.Genre.objects.all())
        # ext_gens = connector_manager.get_external_genres()

        query = request.GET.get("q")
        genre_query = request.GET.get("genres")
        if not query and not genre_query:
            print("Exited because nothing was selected.")
            context = {}
            context["genre_tags"] = local_gens
            return TemplateResponse(request, "search/book.html", context)

        if query and not search_type:
            search_type = "user" if "@" in query else "book"

        endpoints = {
            "book": book_search,
            "user": user_search,
            "list": list_search,
            "genre": genre_search,
        }
        if not search_type in endpoints:
            search_type = "book"

        return endpoints[search_type](request)


def get_valid_genres(ext_gens, local_gens):
    # Note: I wasn't able to get this whole idea to work. For now, this remains unused.
    """We want to try to get genres from other instances that we don't have.
    Filters out genres we already have so there's no duplicates."""
    gen_exists = False
    final_list = local_gens
    for i in ext_gens:

        for gen in local_gens:
            if gen.name == i["results"].name:
                gen_exists = True
                break

        if gen_exists:
            gen_exists = False
            continue

        modified_name = i["results"].name + " -- External"

        final_list.append(
            models.Genre(
                id=get_ext_gen_id(i["results"].id),
                genre_name=modified_name,
                name=i["results"].name,
                description=i["results"].description,
            )
        )

    return final_list


def get_ext_gen_id(gen_url):
    """Try to get the genre ID from the url"""
    gen_last_url = gen_url[-3:]

    gen_id = ""

    for url_char in gen_last_url:
        if url_char.isdigit():
            gen_id = gen_id + url_char

    print(gen_id)
    return gen_id


def api_book_search(request, search_type):
    """Return books via API response"""
    if search_type == "genre":

        genre_list = request.GET.getlist("genres")
        button_selection = request.GET.get("search_buttons")
        # only return local book results via json so we don't cascade
        book_results = search_genre(genre_list, button_selection)

    else:

        query = request.GET.get("q")
        query = isbn_check(query)
        min_confidence = request.GET.get("min_confidence", 0)
        # only return local book results via json so we don't cascade
        book_results = search(query, min_confidence=min_confidence)

    return JsonResponse(
        [format_search_result(r) for r in book_results[:10]], safe=False
    )


def genre_search(request):
    """The main course.
    Look for books based on genres."""

    if is_api_request(request):
        return api_book_search(request, search_type="genre")

    genre_list = request.GET.getlist("genres")
    button_selection = request.GET.get("search_buttons")
    search_remote = request.GET.get("remote", False) and request.user.is_authenticated

    gen_query = request.GET.get("genres")
    query = request.GET.get("q")
    query = isbn_check(query)

    min_confidence = request.GET.get("min_confidence", 0)
    local_results = search_genre(genre_list, button_selection)

    paginated = Paginator(local_results, PAGE_LENGTH)
    page = paginated.get_page(request.GET.get("page"))
    data = {
        "genre_tags": models.Genre.objects.all(),
        "gen_query": gen_query,
        "gen_list": genre_list,
        "btn_select": button_selection,
        "query": query,
        "results": page,
        "remote": search_remote,
        "type": "genre",
        "page_range": paginated.get_elided_page_range(
            page.number, on_each_side=2, on_ends=1
        ),
    }

    if request.user.is_authenticated:
        print("Calling the remote results for genres.")
        data["remote_results"] = connector_manager.search_genre(
            genre_list, button_selection, min_confidence=min_confidence
        )
        data["remote"] = True
    return TemplateResponse(request, "search/book.html", data)


def book_search(request):
    """the real business is elsewhere"""
    query = request.GET.get("q")
    # check if query is isbn
    query = isbn_check(query)
    min_confidence = request.GET.get("min_confidence", 0)
    search_remote = request.GET.get("remote", False) and request.user.is_authenticated

    # try a local-only search
    local_results = search(query, min_confidence=min_confidence)
    paginated = Paginator(local_results, PAGE_LENGTH)
    page = paginated.get_page(request.GET.get("page"))
    data = {
        "genre_tags": models.Genre.objects.all(),
        "query": query,
        "results": page,
        "type": "book",
        "remote": search_remote,
        "page_range": paginated.get_elided_page_range(
            page.number, on_each_side=2, on_ends=1
        ),
    }
    # if a logged in user requested remote results or got no local results, try remote
    if request.user.is_authenticated and (not local_results or search_remote):
        data["remote_results"] = connector_manager.search(
            query, min_confidence=min_confidence
        )
        data["remote"] = True
    return TemplateResponse(request, "search/book.html", data)


def user_search(request):
    """cool kids members only user search"""
    viewer = request.user
    query = request.GET.get("q")
    query = query.strip()
    data = {"type": "user", "query": query}
    # logged out viewers can't search users
    if not viewer.is_authenticated:
        return TemplateResponse(request, "search/user.html", data)

    # use webfinger for mastodon style account@domain.com username to load the user if
    # they don't exist locally (handle_remote_webfinger will check the db)
    if re.match(regex.FULL_USERNAME, query):
        handle_remote_webfinger(query)

    results = (
        models.User.viewer_aware_objects(viewer)
        .annotate(
            similarity=Greatest(
                TrigramSimilarity("username", query),
                TrigramSimilarity("localname", query),
            )
        )
        .filter(
            similarity__gt=0.5,
        )
        .order_by("-similarity")
    )
    paginated = Paginator(results, PAGE_LENGTH)
    page = paginated.get_page(request.GET.get("page"))
    data["results"] = page
    data["page_range"] = paginated.get_elided_page_range(
        page.number, on_each_side=2, on_ends=1
    )
    return TemplateResponse(request, "search/user.html", data)


def list_search(request):
    """any relevent lists?"""
    query = request.GET.get("q")
    data = {"query": query, "type": "list"}
    results = (
        models.List.privacy_filter(
            request.user,
            privacy_levels=["public", "followers"],
        )
        .annotate(
            similarity=Greatest(
                TrigramSimilarity("name", query),
                TrigramSimilarity("description", query),
            )
        )
        .filter(
            similarity__gt=0.1,
        )
        .order_by("-similarity")
    )
    paginated = Paginator(results, PAGE_LENGTH)
    page = paginated.get_page(request.GET.get("page"))
    data["results"] = page
    data["page_range"] = paginated.get_elided_page_range(
        page.number, on_each_side=2, on_ends=1
    )
    return TemplateResponse(request, "search/list.html", data)


def isbn_check(query):
    """isbn10 or isbn13 check, if so remove separators"""
    if query:
        su_num = re.sub(r"(?<=\d)\D(?=\d|[xX])", "", query)
        if len(su_num) == 13 and su_num.isdecimal():
            # Multiply every other digit by  3
            # Add these numbers and the other digits
            product = sum(int(ch) for ch in su_num[::2]) + sum(
                int(ch) * 3 for ch in su_num[1::2]
            )
            if product % 10 == 0:
                return su_num
        elif (
            len(su_num) == 10
            and su_num[:-1].isdecimal()
            and (su_num[-1].isdecimal() or su_num[-1].lower() == "x")
        ):
            product = 0
            # Iterate through code_string
            for i in range(9):
                # for each character, multiply by a different decreasing number: 10 - x
                product = product + int(su_num[i]) * (10 - i)
            # Handle last character
            if su_num[9].lower() == "x":
                product += 10
            else:
                product += int(su_num[9])
            if product % 11 == 0:
                return su_num
    return query
