import heapq

# float addition gives things like 23.400000000000002, so round the total
DECIMAL_PLACES = 6


def dijkstra(graph, source, destination):
    """Shortest path from source to destination using Dijkstra.
    Returns (total_latency, path) or None if there is no path."""
    if source == destination:
        return 0.0, [source]

    distances = {source: 0.0}
    previous = {}
    visited = set()
    heap = [(0.0, source)]

    while heap:
        distance, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)

        if node == destination:
            return round(distance, DECIMAL_PLACES), build_path(previous, source, destination)

        for neighbour, latency in graph.get(node, []):
            new_distance = distance + latency
            if new_distance < distances.get(neighbour, float("inf")):
                distances[neighbour] = new_distance
                previous[neighbour] = node
                heapq.heappush(heap, (new_distance, neighbour))

    return None


def build_path(previous, source, destination):
    """Go back from destination to source using the previous map."""
    path = [destination]
    while path[-1] != source:
        path.append(previous[path[-1]])
    return path[::-1]
