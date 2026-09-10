from django.urls import path
from . import views

urlpatterns = [
    # path("tableau", views.tresorerie_table, name="tresorerie_table"),
    path(
        "tresorerie",
        views.TresorerieListView.as_view(),
        name="tresorerie_table",
    ),
    path(
        "tresorerie/ajouter/",
        views.TresorerieCreateView.as_view(),
        name="tresorerie_add",
    ),
    path(
        "tresorerie/<int:pk>/modifier/",
        views.TresorerieUpdateView.as_view(),
        name="tresorerie_edit",
    ),
    path(
        "tresorerie/<int:pk>/supprimer/",
        views.TresorerieDeleteView.as_view(),
        name="tresorerie_delete",
    ),
]
