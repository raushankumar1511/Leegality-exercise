from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Greatest, Least


class Node(models.Model):
    """A server in the network."""

    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Edge(models.Model):
    """Bidirectional link between two nodes. A - B can be used both ways,
    so B - A is the same edge and can't be added again."""

    source = models.ForeignKey(Node, on_delete=models.PROTECT, related_name="outgoing_edges")
    destination = models.ForeignKey(Node, on_delete=models.PROTECT, related_name="incoming_edges")
    latency = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        # serializer already checks these, constraints are just a safety net at DB level
        constraints = [
            # same pair of nodes in any order counts as a duplicate (A-B and B-A)
            models.UniqueConstraint(
                Least("source", "destination"),
                Greatest("source", "destination"),
                name="unique_edge_node_pair",
            ),
            models.CheckConstraint(condition=Q(latency__gt=0), name="edge_latency_positive"),
            models.CheckConstraint(condition=~Q(source=F("destination")), name="edge_no_self_loop"),
        ]

    def __str__(self):
        return f"{self.source} - {self.destination} ({self.latency})"


class RouteQuery(models.Model):
    """History of successful shortest route queries.
    Node names are stored as plain text so history stays even if a node is deleted."""

    source = models.CharField(max_length=100, db_index=True)
    destination = models.CharField(max_length=100, db_index=True)
    total_latency = models.FloatField()
    path = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name_plural = "route queries"

    def __str__(self):
        return f"{self.source} -> {self.destination} ({self.total_latency})"
