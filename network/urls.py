from django.urls import path

from network import views

urlpatterns = [
    path("nodes", views.NodeListCreateView.as_view(), name="node-list-create"),
    path("nodes/<int:pk>", views.NodeDetailView.as_view(), name="node-detail"),
    path("edges", views.EdgeListCreateView.as_view(), name="edge-list-create"),
    path("edges/<int:pk>", views.EdgeDetailView.as_view(), name="edge-detail"),
    path("routes/shortest", views.ShortestRouteView.as_view(), name="route-shortest"),
    path("routes/history", views.RouteHistoryView.as_view(), name="route-history"),
]
