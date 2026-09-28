from django.views.generic import DetailView, ListView

from .models import FicheMarche


class FicheMarcheListView(ListView):
    """Liste des marchés -- page « tableau_marche ».

    `avec_statut_nantissement()` annote `nantissement_existe` via un EXISTS :
    le statut de nantissement de TOUS les marchés est calculé en une seule
    requête, au lieu d'une requête par ligne (N+1) avec la propriété
    `est_nanti`. L'ordre par défaut du modèle (date de notification
    décroissante, puis n° de marché) est conservé.
    """

    model = FicheMarche
    template_name = "marche/tableau_marche.html"
    context_object_name = "marches"
    queryset = FicheMarche.objects.avec_statut_nantissement()


class FicheMarcheDetailView(DetailView):
    """Fiche détaillée en lecture seule d'un marché (bouton « Actions »)."""

    model = FicheMarche
    template_name = "marche/fiche_marche.html"
    context_object_name = "marche"

    def get_queryset(self):
        # Préchargement des documents liés : la fiche affiche nantissements et
        # pénalités, sans requête supplémentaire par marché.
        return FicheMarche.objects.avec_statut_nantissement().prefetch_related(
            "nantissements", "penalites"
        )
