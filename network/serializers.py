import math
from datetime import datetime, time, timezone

from django.db.models import Q
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import serializers

from network.models import Edge, Node, RouteQuery


class NodeSerializer(serializers.ModelSerializer):
    # declared manually so the duplicate error message comes from validate_name
    name = serializers.CharField(max_length=100)

    class Meta:
        model = Node
        fields = ["id", "name"]

    def validate_name(self, value):
        if Node.objects.filter(name=value).exists():
            raise serializers.ValidationError(f"A node named '{value}' already exists.")
        return value


class EdgeSerializer(serializers.ModelSerializer):
    """Source and destination are sent and returned as node names instead of ids."""

    source = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Node.objects.all(),
        error_messages={"does_not_exist": "Node '{value}' does not exist."},
    )
    destination = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Node.objects.all(),
        error_messages={"does_not_exist": "Node '{value}' does not exist."},
    )

    class Meta:
        model = Edge
        fields = ["id", "source", "destination", "latency"]

    def validate_latency(self, value):
        if not math.isfinite(value) or value <= 0:
            raise serializers.ValidationError("Latency must be a number greater than 0.")
        return value

    def validate(self, attrs):
        source = attrs["source"]
        destination = attrs["destination"]

        if source == destination:
            raise serializers.ValidationError({"destination": "Source and destination must be different nodes."})

        # edges are bidirectional, so check both A-B and B-A
        same_pair = Q(source=source, destination=destination) | Q(source=destination, destination=source)
        if Edge.objects.filter(same_pair).exists():
            raise serializers.ValidationError(
                {"destination": f"An edge between '{source}' and '{destination}' already exists."}
            )

        return attrs


def get_node(name):
    """Return the node with this name, or raise a validation error if it doesn't exist."""
    node = Node.objects.filter(name=name).first()
    if node is None:
        raise serializers.ValidationError(f"Node '{name}' does not exist.")
    return node


class ShortestRouteRequestSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=100)
    destination = serializers.CharField(max_length=100)

    def validate_source(self, value):
        return get_node(value).name

    def validate_destination(self, value):
        return get_node(value).name


class ShortestRouteResponseSerializer(serializers.Serializer):
    total_latency = serializers.FloatField()
    path = serializers.ListField(child=serializers.CharField())


class RouteHistorySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)

    class Meta:
        model = RouteQuery
        fields = ["id", "source", "destination", "total_latency", "path", "created_at"]


class RouteHistoryQuerySerializer(serializers.Serializer):
    """Query params for history. Dates can be 2026-02-20 or 2026-02-20T14:32:00Z."""

    source = serializers.CharField(max_length=100, required=False)
    destination = serializers.CharField(max_length=100, required=False)
    limit = serializers.IntegerField(min_value=1, required=False)
    date_from = serializers.CharField(required=False)
    date_to = serializers.CharField(required=False)

    def validate_date_from(self, value):
        return to_datetime(value)

    def validate_date_to(self, value):
        # date_to=2026-02-20 should include the whole day
        return to_datetime(value, end_of_day=True)

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({"date_from": "date_from must be earlier than or equal to date_to."})
        return attrs


def to_datetime(value, end_of_day=False):
    """Parse a date or datetime string into a UTC aware datetime."""
    try:
        result = parse_datetime(value)
        if result is None:
            day = parse_date(value)
            if day:
                result = datetime.combine(day, time.max if end_of_day else time.min)
    except ValueError:  # e.g. 2026-02-30
        result = None

    if result is None:
        raise serializers.ValidationError("Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ format.")

    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result
