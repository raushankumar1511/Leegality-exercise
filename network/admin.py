from django.contrib import admin

from network.models import Edge, Node, RouteQuery


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_at"]
    search_fields = ["name"]


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ["id", "source", "destination", "latency", "created_at"]
    list_select_related = ["source", "destination"]


@admin.register(RouteQuery)
class RouteQueryAdmin(admin.ModelAdmin):
    list_display = ["id", "source", "destination", "total_latency", "created_at"]
    list_filter = ["created_at"]
