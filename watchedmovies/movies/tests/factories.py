import factory
from factory import Faker
from factory.django import DjangoModelFactory

from watchedmovies.movies.models import ViewDetails
from watchedmovies.users.tests.factories import ProfileFactory


class WatchedMovieFactory(DjangoModelFactory):
    adult = Faker("boolean")
    backdrop_path = Faker("file_path")
    genre_ids = factory.LazyFunction(lambda: str([Faker("pyint") for _ in range(3)]))
    original_language = Faker("language_code")
    original_title = Faker("sentence", nb_words=3)
    overview = Faker("text")
    popularity = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    poster_path = Faker("file_path")
    release_date = Faker("date")
    title = Faker("sentence", nb_words=6)
    video = Faker("boolean")
    vote_average = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    vote_count = Faker("pyint", min_value=1, max_value=100)

    class Meta:
        model = "movies.WatchedMovie"
        django_get_or_create = ["title"]


class ViewDetailFactory(DjangoModelFactory):
    watched_movie = factory.SubFactory(WatchedMovieFactory)
    profile = factory.SubFactory(ProfileFactory)
    rating = Faker("pyint", min_value=1, max_value=5)
    comment = Faker("text")
    language = Faker("random_element", elements=[lang[0] for lang in ViewDetails.LANGUAGE_CHOICES])
    place = Faker("random_element", elements=[place[0] for place in ViewDetails.PLACE_CHOICES])

    class Meta:
        model = "movies.ViewDetails"
        django_get_or_create = ["watched_movie", "profile"]
