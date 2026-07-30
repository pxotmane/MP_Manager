
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Exists, F, OuterRef

class HorodatageMixin(models.Model):
    """Ajoute les champs de traçabilité created_at / updated_at."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        abstract = True


class DocumentLieAuMarche(HorodatageMixin):
    """
    Base abstraite pour tout modèle rattaché à un FicheMarche.

    Factorise la ForeignKey commune à Nantissement et Penalite.
    related_name="%(class)ss" donne automatiquement "nantissements" pour
    Nantissement et "penalites" pour Penalite (interpolation Django standard
    pour les classes abstraites, cf. doc "Abstract related name").
    """

    marche = models.ForeignKey(
        "FicheMarche", on_delete=models.PROTECT, related_name="%(class)ss", verbose_name="Marché"
    )

    class Meta:
        abstract = True




