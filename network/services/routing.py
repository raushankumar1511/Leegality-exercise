from collections import defaultdict

from network.models import Edge, RouteQuery
from network.services.graph import dijkstra


def build_graph():
    """Adjacency list from the edges table: {node: [(neighbour, latency), ...]}.
    Edges are bidirectional so each edge is added in both directions."""
    graph = defaultdict(list)
    for source, destination, latency in Edge.objects.values_list("source__name", "destination__name", "latency"):
        graph[source].append((destination, latency))
        graph[destination].append((source, latency))
    return graph


def find_shortest_route(source, destination):
    """Run dijkstra on the current graph and save the result in history.
    Returns None when there is no path."""
    result = dijkstra(build_graph(), source, destination)
    if result is None:
        return None

    total_latency, path = result
    RouteQuery.objects.create(source=source, destination=destination, total_latency=total_latency, path=path)
    return {"total_latency": total_latency, "path": path}
