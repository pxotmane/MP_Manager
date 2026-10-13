from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from .models import OrdreRecette, SoldeOuvertureExercice, Tresorerie


MOIS_FR = (
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
)


def get_situation_mensuelle(exercice):
    """Retourne le solde d'ouverture et les mouvements encaissés/décaissés par mois."""
    solde = SoldeOuvertureExercice.objects.filter(exercice=exercice).first()
    recettes_par_mois = defaultdict(lambda: Decimal("0.00"))
    depenses_par_mois = defaultdict(lambda: Decimal("0.00"))

    recettes = (
        OrdreRecette.objects.filter(date_encaissement__year=exercice)
        .values("date_encaissement__month")
        .annotate(total=Sum("montant"))
    )
    for mouvement in recettes:
        recettes_par_mois[mouvement["date_encaissement__month"]] = (
            mouvement["total"] or Decimal("0.00")
        )

    depenses = (
        Tresorerie.objects.filter(date_decaissement__year=exercice)
        .values("date_decaissement__month")
        .annotate(total=Sum("montant"))
    )
    for mouvement in depenses:
        depenses_par_mois[mouvement["date_decaissement__month"]] = (
            mouvement["total"] or Decimal("0.00")
        )

    solde_courant = solde.montant if solde else None
    mois = []
    for numero in range(1, 13):
        recettes_mois = recettes_par_mois[numero]
        depenses_mois = depenses_par_mois[numero]
        solde_ouverture = solde_courant
        if solde_courant is not None:
            solde_courant += recettes_mois - depenses_mois
        mois.append(
            {
                "numero": numero,
                "nom": MOIS_FR[numero - 1],
                "date": date(exercice, numero, 1),
                "solde_ouverture": solde_ouverture,
                "recettes": recettes_mois,
                "depenses": depenses_mois,
                "solde_cloture": solde_courant,
            }
        )

    return {
        "solde_ouverture": solde,
        "mois": mois,
        "total_recettes": sum(recettes_par_mois.values(), Decimal("0.00")),
        "total_depenses": sum(depenses_par_mois.values(), Decimal("0.00")),
        "solde_cloture": solde_courant,
    }
