""" using a bookwyrm instance as a source of book data """
from dataclasses import asdict, dataclass
from functools import reduce
import operator

from django.contrib.postgres.search import SearchRank, SearchQuery
from django.db.models import F, Q

from bookwyrm import models
from bookwyrm import connectors
from bookwyrm.settings import MEDIA_FULL_URL


# pylint: disable=arguments-differ
def search(query, min_confidence=0, filters=None, return_first=False):
    """search your local database"""
    filters = filters or []
    if not query:
        return []
    query = query.strip()

    results = None
    # first, try searching unique identifiers
    # unique identifiers never have spaces, title/author usually do
    if not " " in query:
        results = search_identifiers(query, *filters, return_first=return_first)

    # if there were no identifier results...
    if not results:
        # then try searching title/author
        results = search_title_author(
            query, min_confidence, *filters, return_first=return_first
        )
    return results


def search_genre(active_genres, search_active_option):
    """Get our genre list and put them on the page."""

    # Check if there's actually a genre selected.
    if len(active_genres):
        base_qs = models.Work.objects.all()
        results = []
        # AND Searching
        if search_active_option == "search_and":

            for gen in active_genres:
                results = base_qs.filter(genres__pk__contains=gen)
            results = get_first_edition_gen(results)
        # OR searching
        elif search_active_option == "search_or":

            results.extend(base_qs.filter(genres__pk__in=active_genres).distinct())
            results = get_first_edition_gen(results)
        # EXCLUDE searching
        elif search_active_option == "search_exclude":
            results = base_qs.exclude(genres__pk__in=active_genres)
            results = get_first_edition_gen(results)

    else:
        results = []

    return results


def get_first_edition_gen(results):
    """Get the default edition of our books."""
    list_result = []
    for work in results:
        # pylint: disable=broad-except
        try:
            list_result.append(work.default_edition)
        except Exception:
            # Ignore it if something went wrong somehow.
            # It shouldn't really matter.
            continue

    return list_result


def isbn_search(query):
    """search your local database"""
    if not query:
        return []
    # Up-case the ISBN string to ensure any 'X' check-digit is correct
    # If the ISBN has only 9 characters, prepend missing zero
    query = query.strip().upper().rjust(10, "0")
    filters = [{f: query} for f in ["isbn_10", "isbn_13"]]
    return models.Edition.objects.filter(
        reduce(operator.or_, (Q(**f) for f in filters))
    ).distinct()


def format_search_result(search_result):
    """convert a book object into a search result object"""
    cover = None
    if search_result.cover:
        cover = f"{MEDIA_FULL_URL}{search_result.cover}"

    return SearchResult(
        title=search_result.title,
        key=search_result.remote_id,
        author=search_result.author_text,
        year=search_result.published_date.year
        if search_result.published_date
        else None,
        cover=cover,
        confidence=search_result.rank if hasattr(search_result, "rank") else 1,
        connector="",
    ).json()


def search_identifiers(query, *filters, return_first=False):
    """tries remote_id, isbn; defined as dedupe fields on the model"""
    if connectors.maybe_isbn(query):
        # Oh did you think the 'S' in ISBN stood for 'standard'?
        normalized_isbn = query.strip().upper().rjust(10, "0")
        query = normalized_isbn
    # pylint: disable=W0212
    or_filters = [
        {f.name: query}
        for f in models.Edition._meta.get_fields()
        if hasattr(f, "deduplication_field") and f.deduplication_field
    ]
    results = models.Edition.objects.filter(
        *filters, reduce(operator.or_, (Q(**f) for f in or_filters))
    ).distinct()

    if return_first:
        return results.first()
    return results


def search_title_author(query, min_confidence, *filters, return_first=False):
    """searches for title and author"""
    query = SearchQuery(query, config="simple") | SearchQuery(query, config="english")
    results = (
        models.Edition.objects.filter(*filters, search_vector=query)
        .annotate(rank=SearchRank(F("search_vector"), query))
        .filter(rank__gt=min_confidence)
        .order_by("-rank")
    )

    # when there are multiple editions of the same work, pick the closest
    editions_of_work = results.values_list("parent_work__id", flat=True).distinct()

    # filter out multiple editions of the same work
    list_results = []
    for work_id in set(editions_of_work[:30]):
        result = (
            results.filter(parent_work=work_id)
            .order_by("-rank", "-edition_rank")
            .first()
        )

        if return_first:
            return result
        list_results.append(result)
    return list_results


@dataclass
class SearchResult:
    """standardized search result object"""

    title: str
    key: str
    connector: object
    # genres: str[str]
    view_link: str = None
    author: str = None
    year: str = None
    cover: str = None
    confidence: int = 1

    def __repr__(self):
        # pylint: disable=consider-using-f-string
        return "<SearchResult key={!r} title={!r} author={!r} confidence={!r}>".format(
            self.key, self.title, self.author, self.confidence
        )

    def json(self):
        """serialize a connector for json response"""
        serialized = asdict(self)
        del serialized["connector"]
        return serialized


@dataclass
class GenreResult:
    """How our genre will look like when requesting it from another instance."""

    # pylint: disable=invalid-name
    id: str
    genre_name: str
    description: str
    name: str
    type: str
    connector: object

    def __repr__(self):
        # pylint: disable=consider-using-f-string
        return "<GenreInfo id={!r} genre_name={!r} name={!r} description={!r}>".format(
            self.id, self.genre_name, self.name, self.description
        )

    def json(self):
        """serialize a connector for json response"""
        serialized = asdict(self)
        del serialized["connector"]
        return serialized
