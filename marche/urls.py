from django.urls import path
from . import views

urlpatterns = [
    # Liste des marchés (page principale « Marchés » de la navbar).
    path(
        "tableau_marche",
        views.FicheMarcheListView.as_view(),
        name="tableau_marche",
    ),
    # Fiche détaillée en lecture seule d'un marché (colonne « Actions »).
    path(
        "marche/<int:pk>/",
        views.FicheMarcheDetailView.as_view(),
        name="fiche_marche",
    ),
]
