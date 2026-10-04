"""Filtres de template : affichage des « pills » (badges) Budget / Nature.

Ces filtres centralisent la correspondance valeur métier -> couleur, afin de ne
pas dupliquer de logique de présentation dans les templates (utilisables aussi
par la page « Marchés »).

Choix de design : les pills ne portent AUCUNE icône (registre administratif) ;
la pastille de couleur est ajoutée en CSS via `.badge-matte::before`.
"""

from django import template

register = template.Library()

# Budget : la COULEUR dépend du type (EXP/INV), le REMPLISSAGE de la source
# (RAM = pastel « matte », BUDGET = aplat « matte »).
_BUDGET_BADGES = {
    "RAM EXP": "badge-matte-green",
    "RAM INV": "badge-matte-blue",
    "BUDGET EXP": "badge-matte-green-solid",
    "BUDGET INV": "badge-matte-blue-solid",
    "EXPLOITATION": "badge-matte-green-solid",
    "INVESTISSEMENT": "badge-matte-blue-solid",
}

_NATURE_BADGES = {
    "MARCHE": "badge-matte-blue",
    "BON COMMANDE": "badge-matte-green",
    "CONVENTION": "badge-matte-teal",
    "HEURES_SUPP": "badge-matte-indigo",
    "INDEMNITE DEPLACEMENT": "badge-matte-cyan",
    "FRAIS AUTORISATION": "badge-matte-amber",
    "INSERSTION": "badge-matte-slate",
    "ALIMENTATION DE LA TRESORERIE": "badge-matte-blue",
    "RECETTES CONFISCATION": "badge-matte-indigo",
    "PENALITES DE RETARD": "badge-matte-amber",
    "REJET DE LA TGR": "badge-matte-red",
}

_ETAT_RECETTE_BADGES = {
    "ETABLI": "badge-matte-green",
    "NON ETABLI": "badge-matte-amber",
}

_DEFAULT_BADGE = "badge-matte-slate"


@register.filter
def budget_badge(value):
    """Classe CSS de la pill du champ « budget »."""
    return _BUDGET_BADGES.get(value or "", _DEFAULT_BADGE)


@register.filter
def nature_badge(value):
    """Classe CSS de la pill du champ « nature »."""
    return _NATURE_BADGES.get(value or "", _DEFAULT_BADGE)


@register.filter
def etat_recette_badge(value):
    """Classe CSS de la pill du champ « etat » d'une recette."""
    return _ETAT_RECETTE_BADGES.get(value or "", _DEFAULT_BADGE)


@register.filter
def format_montant(value):
    """Formate un montant monétaire en dirhams (ex: 1 250 450,00)."""
    if value is None or value == "":
        return "-"
    try:
        val = float(value)
        if val == 0:
            return "0,00"
        return f"{val:,.2f}".replace(",", " ").replace(".", ",")
    except (ValueError, TypeError):
        return value
