# Network Route Optimization API

REST API to manage a network of servers (nodes) and the links between them (edges), and to find the
shortest route between two servers based on latency. Every successful route query is saved in a history table.

Tech stack: Django 5.2, Django REST Framework, PostgreSQL 16 (Docker).

## Project structure

```
config/                  Django project settings and root urls
network/
    models.py            Node, Edge, RouteQuery
    serializers.py       request validation and response serializers
    views.py             APIViews
    urls.py
    exceptions.py        custom exception handler for error responses
    services/
        graph.py         Dijkstra's algorithm
        routing.py       builds the graph from DB, runs dijkstra, saves history
docker-compose.yml       PostgreSQL for local development
```

## Setup

Requirements: Python 3.12+, Docker

```bash
cp .env.example .env            # and set DJANGO_SECRET_KEY

docker compose up -d            # starts postgres on port 5433

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Postgres runs on port 5433 instead of 5432 so it doesn't conflict with a locally installed Postgres.
You can change it with `DB_PORT` in `.env`.

## APIs

No authentication. All request and response bodies are JSON.

Errors are returned in this format:

```json
{"error": "Node with id 5 not found."}
```

Validation errors (400) return the field wise errors in `details`:

```json
{"error": "Validation Error", "details": {"latency": ["Latency must be a number greater than 0."]}}
```
### POST /nodes

```json
{"name": "ServerA"}
```
- 201: `{"id": 1, "name": "ServerA"}`
- 400: name missing or duplicate

### POST /edges

```json
{"source": "ServerA", "destination": "ServerB", "latency": 12.5}
```
- 201: `{"id": 1, "source": "ServerA", "destination": "ServerB", "latency": 12.5}`
- 400: source/destination missing, latency <= 0, duplicate edge (in either direction), node not found, source same as destination

### POST /routes/shortest

```json
{"source": "ServerA", "destination": "ServerD"}
```
- 200: `{"total_latency": 23.4, "path": ["ServerA", "ServerB", "ServerD"]}`
- 404: `{"error": "No path exists between ServerA and ServerD"}`
- 400: invalid or non-existent nodes

### GET /routes/history

Optional query params:

- `source`, `destination` - filter by node name
- `limit` - max number of records
- `date_from`, `date_to` - filter by `created_at`, accepts `2026-02-20` or `2026-02-20T14:32:00Z`.
  If `date_to` is just a date, the whole day is included.

Example: `/routes/history?source=ServerA&limit=10&date_from=2026-02-20`

```json
[
  {
    "id": 1,
    "source": "ServerA",
    "destination": "ServerD",
    "total_latency": 23.4,
    "path": ["ServerA", "ServerB", "ServerD"],
    "created_at": "2026-02-20T14:32:00Z"
  }
]
```

### Other APIs

- `GET /nodes` - list all nodes
- `GET /edges` - list all edges
- `DELETE /nodes/{id}` - delete a node. Returns 400 if the node still has edges, they need to be deleted first
- `DELETE /edges/{id}` - delete an edge

Both DELETE APIs return 204 on success and 404 if the id doesn't exist.

## Assumptions

- Edges are bidirectional. An edge between A and B can be used both ways, so adding B -> A when A -> B
  already exists is a duplicate. This is also enforced at DB level with a unique constraint on the node pair.
- Shortest path is calculated with Dijkstra's algorithm. This works because latency is always > 0.
- `total_latency` is rounded to 6 decimal places to avoid float values like `23.400000000000002`.
- If source and destination are the same node, the response is `{"total_latency": 0.0, "path": ["ServerA"]}`.
- Only successful route queries are stored in history. History keeps node names instead of foreign keys,
  so it isn't lost when a node is deleted.
- History is sorted newest first, so `limit` returns the latest records.
- A node can't be deleted while it has edges (as source or destination). This is also enforced at DB level with `on_delete=PROTECT`.
- Node names are case sensitive.
