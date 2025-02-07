from rest_framework import serializers
from django.contrib.auth import get_user_model
from cinema.models import (
    Genre, Actor, Movie,
    CinemaHall, MovieSession,
    Ticket, Order
)

User = get_user_model()


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class ActorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Actor
        fields = ["id", "first_name", "last_name", "full_name"]


class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    genres_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Genre.objects.all(),
        source="genres",
        required=True
    )
    actors_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Actor.objects.all(),
        source="actors",
        required=True
    )

    class Meta:
        model = Movie
        fields = [
            "id", "title", "description", "duration",
            "genres", "actors", "genres_ids", "actors_ids"
        ]

    def validate_duration(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Duration must be a positive integer.")
        return value

    def create(self, validated_data):
        genres = validated_data.pop("genres")
        actors = validated_data.pop("actors")
        movie = Movie.objects.create(**validated_data)
        movie.genres.set(genres)
        movie.actors.set(actors)
        return movie

    def update(self, instance, validated_data):
        genres = validated_data.pop("genres", None)
        actors = validated_data.pop("actors", None)
        instance = super().update(instance, validated_data)
        if genres is not None:
            instance.genres.set(genres)
        if actors is not None:
            instance.actors.set(actors)
        return instance


class CinemaHallSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = CinemaHall
        fields = ["id", "name", "rows", "seats_in_row", "capacity"]


class MovieSessionSerializer(serializers.ModelSerializer):
    movie = serializers.StringRelatedField()
    cinema_hall = serializers.StringRelatedField()
    cinema_hall_capacity = serializers.IntegerField(
        source="cinema_hall.capacity", read_only=True
    )
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    cinema_hall_name = serializers.CharField(
        source="cinema_hall.name", read_only=True)
    movie_id = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(), write_only=True, source="movie"
    )
    cinema_hall_id = serializers.PrimaryKeyRelatedField(
        queryset=CinemaHall.objects.all(),
        write_only=True, source="cinema_hall"
    )

    class Meta:
        model = MovieSession
        fields = [
            "id", "show_time", "movie", "cinema_hall",
            "movie_id", "cinema_hall_id", "movie_title",
            "cinema_hall_name", "cinema_hall_capacity"
        ]

    def create(self, validated_data):
        return MovieSession.objects.create(**validated_data)
