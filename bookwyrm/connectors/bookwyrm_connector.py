""" using another bookwyrm instance as a source of book data """
from bookwyrm import activitypub, models
from bookwyrm.book_search import SearchResult, GenreResult
from .abstract_connector import AbstractMinimalConnector


class Connector(AbstractMinimalConnector):
    """this is basically just for search"""

    def get_or_create_book(self, remote_id):
        return activitypub.resolve_remote_id(remote_id, model=models.Edition)

    def parse_search_data(self, data, min_confidence):
        for search_result in data:
            print("Parsing book from Bookwyrm Connector")
            search_result["connector"] = self
            yield SearchResult(**search_result)

    def parse_genre_data(self, data):
        """Parse the data we got from a genre json."""
        data["connector"] = self
        data["type"] = "Genre"
        # I forgot why I did this. Surely this isn't a problem.
        del data["@context"]

        return GenreResult(**data)
        # for gen in data:
        #    #gen["connector"] = self
        #    print(gen)
        #    yield GenreResult(**gen)

    def parse_isbn_search_data(self, data):
        for search_result in data:
            search_result["connector"] = self
            yield SearchResult(**search_result)
