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
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Actor
        fields = ["id", "first_name", "last_name", "full_name"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )
    actors = ActorSerializer(many=True, read_only=True)
    genres_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Genre.objects.all(),
        source="genres"
    )
    actors_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Actor.objects.all(),
        source="actors"
    )

    class Meta:
        model = Movie
        fields = [
            "id", "title", "description", "duration",
            "genres", "actors", "genres_ids", "actors_ids"
        ]

    def create(self, validated_data):
        genres = validated_data.pop("genres", [])
        actors = validated_data.pop("actors", [])
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
    class Meta:
        model = CinemaHall
        fields = ["id", "name", "rows", "seats_in_row", "capacity"]


class MovieSessionSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    movie_id = serializers.PrimaryKeyRelatedField(
        source="movie", queryset=Movie.objects.all(), write_only=True
    )
    cinema_hall = CinemaHallSerializer(read_only=True)
    cinema_hall_id = serializers.PrimaryKeyRelatedField(
        source="cinema_hall",
        queryset=CinemaHall.objects.all(),
        write_only=True
    )

    class Meta:
        model = MovieSession
        fields = [
            "id", "show_time", "movie", "movie_id",
            "cinema_hall", "cinema_hall_id"
        ]


class TicketSerializer(serializers.ModelSerializer):
    movie_session = MovieSessionSerializer(read_only=True)
    movie_session_id = serializers.PrimaryKeyRelatedField(
        source="movie_session",
        queryset=MovieSession.objects.all(),
        write_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            "id", "movie_session", "movie_session_id",
            "row", "seat"
        ]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    tickets = TicketSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = [
            "id", "created_at", "user", "tickets"
        ]

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(user=self.context["request"].user,
                                     **validated_data)
        for ticket_data in tickets_data:
            ticket_data["order"] = order
            Ticket.objects.create(**ticket_data)
        return order


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
