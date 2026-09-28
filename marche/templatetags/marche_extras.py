"""Filtres de template de l'app « Marché » : pills (badges) du tableau.

Mêmes principes que `tresorerie/templatetags/ui_extras.py` (design commun,
vocabulaire d'icônes Bootstrap `bi-*`) :
  - la correspondance valeur métier -> couleur vit ici, pas dans les templates ;
  - les pills ne portent AUCUNE icône (registre administratif) : la pastille
    de couleur est ajoutée en CSS via `.badge-matte::before` ;
  - toute valeur inconnue retombe sur la couleur neutre `badge-matte-slate`,
    pour qu'une valeur de choix ajoutée plus tard reste affichable.
"""

from django import template

register = template.Library()

# Budget : la couleur dépend du type (INV = investissement, EXP = exploitation).
_TYPE_BUDGET_BADGES = {
    "INV": "badge-matte-blue",
    "EXP": "badge-matte-green",
}

# Mode de passation : large ouvert -> couleur neutre ; proceeding != couleur.
_MODE_PASSATION_BADGES = {
    "AOO": "badge-matte-blue",
    "AOS": "badge-matte-cyan",
    "AOP": "badge-matte-indigo",
    "AON": "badge-matte-teal",
    "AOI": "badge-matte-green",
    "AOR": "badge-matte-amber",
    "CONCOURS": "badge-matte-indigo",
    "NEGOCIEE": "badge-matte-slate",
}

# Type de marché : on alterne les teintes mates pour distinguer visuellement
# les grandes families de procédures.
_TYPE_MARCHE_BADGES = {
    "MARCHE_CADRE": "badge-matte-blue",
    "MARCHE_RECONDUCTIBLE": "badge-matte-teal",
    "MARCHE_ALLOTIS": "badge-matte-cyan",
    "MARCHE_CONCEP_REALISATION": "badge-matte-indigo",
    "MARCHE_TRANCHES_CONDITIONNELLES": "badge-matte-amber",
    "DIALOGUE_COMPETITIF": "badge-matte-green",
    "OFFRE_SPONTANEE": "badge-matte-slate",
}

# Statut du marché : un marché résilié est « fermé » (rouge), un marché soldé est
# « terminé » (vert), sinon le marché est en cours (orange). L'ordre importe :
# un marché résilié ET soldé s'affiche « Résilié ».
_STATUTS = (
    ("marche_resilie", "Résilié", "badge-matte-red"),
    ("marche_solde", "Soldé", "badge-matte-green"),
)
_STATUT_DEFAUT = ("En cours", "badge-matte-amber")

# Nantissement : le statut vient de l'annotation `nantissement_existe` (calculée
# en base par FicheMarche.objects.avec_statut_nantissement()).
_NANTISSEMENT = {
    True: ("Nanti", "badge-matte-teal"),
    False: ("Non nanti", "badge-matte-slate"),
}

_DEFAULT_BADGE = "badge-matte-slate"


def _lookup(mapping, value):
    """Clé absente / None -> couleur neutre, plutôt qu'une classe vide."""
    return mapping.get(value, _DEFAULT_BADGE)


@register.filter
def type_budget_badge(value):
    """Classe CSS de la pill du champ « type_budget » (INV / EXP)."""
    return _lookup(_TYPE_BUDGET_BADGES, value)


@register.filter
def mode_passation_badge(value):
    """Classe CSS de la pill du champ « mode_passation »."""
    return _lookup(_MODE_PASSATION_BADGES, value)


@register.filter
def type_marche_badge(value):
    """Classe CSS de la pill du champ « type_marche »."""
    return _lookup(_TYPE_MARCHE_BADGES, value)


def _statut(marche):
    """(libellé, classe CSS) du statut global d'un marché.

    Prend l'OBJET et non un champ, car le statut combine deux booléens
    (`marche_resilie` / `marche_solde`) : le template ne peut pas les
    combiner seul, et on ne peut pas ajouter de méthode au modèle sans
    accord. Les attributs sont lus via getattr pour rester tolérant.
    """
    for attribut, libelle, classe in _STATUTS:
        if getattr(marche, attribut, False):
            return libelle, classe
    return _STATUT_DEFAUT


# Le libellé et la classe sont exposés séparément (et non en tuple) car
# `{% with %}` n'accepte qu'une affectation à la fois dans un template.
@register.filter
def statut_libelle(marche):
    """Libellé de la pill de statut : « Résilié », « Soldé » ou « En cours »."""
    return _statut(marche)[0]


@register.filter
def statut_badge(marche):
    """Classe CSS de la pill de statut."""
    return _statut(marche)[1]


def _nantissement(nantissement_existe):
    """(libellé, classe CSS) de la pill de nantissement.

    Attend l'annotation `nantissement_existe` du queryset, et non l'objet :
    c'est elle qui évite une requête par ligne.
    """
    return _NANTISSEMENT[bool(nantissement_existe)]


@register.filter
def nantissement_libelle(nantissement_existe):
    """Libellé de la pill : « Nanti » ou « Non nanti »."""
    return _nantissement(nantissement_existe)[0]


@register.filter
def nantissement_badge(nantissement_existe):
    """Classe CSS de la pill de nantissement."""
    return _nantissement(nantissement_existe)[1]