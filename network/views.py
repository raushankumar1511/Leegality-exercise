from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from network.models import Edge, Node, RouteQuery
from network.serializers import (
    EdgeSerializer,
    NodeSerializer,
    RouteHistoryQuerySerializer,
    RouteHistorySerializer,
    ShortestRouteRequestSerializer,
    ShortestRouteResponseSerializer,
)
from network.services.routing import find_shortest_route


class NodeListCreateView(APIView):
    """List all nodes or add a new node."""

    def get(self, request):
        nodes = Node.objects.all()
        return Response(NodeSerializer(nodes, many=True).data)

    def post(self, request):
        serializer = NodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        node = serializer.save()
        return Response(NodeSerializer(node).data, status=status.HTTP_201_CREATED)


class NodeDetailView(APIView):
    """Delete a node. Not allowed while the node still has edges."""

    def delete(self, request, pk):
        node = Node.objects.filter(pk=pk).first()
        if node is None:
            raise NotFound(f"Node with id {pk} not found.")

        if Edge.objects.filter(Q(source=node) | Q(destination=node)).exists():
            return Response(
                {"error": f"Node '{node}' has edges connected to it. Delete those edges first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        node.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EdgeListCreateView(APIView):
    """List all edges or add a new edge between two existing nodes."""

    def get(self, request):
        edges = Edge.objects.select_related("source", "destination")
        return Response(EdgeSerializer(edges, many=True).data)

    def post(self, request):
        serializer = EdgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EdgeDetailView(APIView):
    """Delete an edge."""

    def delete(self, request, pk):
        deleted, _ = Edge.objects.filter(pk=pk).delete()
        if not deleted:
            raise NotFound(f"Edge with id {pk} not found.")
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShortestRouteView(APIView):
    """Find the lowest latency path between two nodes.
    Returns 404 if the destination can't be reached from the source."""

    def post(self, request):
        serializer = ShortestRouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = serializer.validated_data["source"]
        destination = serializer.validated_data["destination"]

        route = find_shortest_route(source, destination)
        if route is None:
            return Response(
                {"error": f"No path exists between {source} and {destination}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ShortestRouteResponseSerializer(route).data)


class RouteHistoryView(APIView):
    """Past route queries, newest first.
    Supports source, destination, limit, date_from and date_to filters."""

    def get(self, request):
        params = RouteHistoryQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        filters = params.validated_data

        queries = RouteQuery.objects.all()
        if "source" in filters:
            queries = queries.filter(source=filters["source"])
        if "destination" in filters:
            queries = queries.filter(destination=filters["destination"])
        if "date_from" in filters:
            queries = queries.filter(created_at__gte=filters["date_from"])
        if "date_to" in filters:
            queries = queries.filter(created_at__lte=filters["date_to"])
        if "limit" in filters:
            queries = queries[: filters["limit"]]

        return Response(RouteHistorySerializer(queries, many=True).data)
