# -*- coding: utf-8 -*-
"""
Modèles Django -- app "treasury"
Générés à partir de MODELS_TABLES.xlsx (feuilles : TRESORERIE, DEP_GID, EXE_BUD)

Hypothèses à valider avec Otmane :
- RIB : absent de ces 3 feuilles (présent dans FICHE_MARCHE / NANTISSEMENT,
  voir procurement/models.py) -- traitement expliqué là-bas.
- Champs "MULTI CHOICE" : les choix ci-dessous reprennent les exemples donnés
  dans le fichier Excel (souvent suivis de "...", donc incomplets). À compléter.
- Placement d'application : ces 3 modèles sont proposés dans l'app "treasury" ;
  à ajuster si vous les préférez dans "accounting" (ils concernent l'exécution
  budgétaire / l'engagement de dépense, en amont du paiement).
"""
from django.db import models


class Tresorerie(models.Model):
    """Feuille Excel TRESORERIE -- suivi d'un ordre de paiement (OP) jusqu'au décaissement."""

    class TypeBudget(models.TextChoices):
        RAM = "RAM", "RAM"
        BUDGET = "BUDGET", "Budget"

    class Nature(models.TextChoices):
        MARCHE = "MARCHE", "Marché"
        HEURES_SUPP = "HEURES_SUPP", "Heures supplémentaires"
        AUTRE = "AUTRE", "Autre"  # Liste incomplète dans la source ("Marché, Heures supp...") -- à compléter.

    op = models.PositiveIntegerField(verbose_name="Numéro d'OP")
    ov = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Numéro d'OV",
        help_text="Renseigné une fois l'ordre de virement émis.",
    )
    exercice = models.PositiveSmallIntegerField(verbose_name="Exercice d'origine")
    budget = models.CharField(max_length=10, choices=TypeBudget.choices, verbose_name="RAM ou Budget")
    ligne_budgetaire = models.CharField(
        max_length=50, verbose_name="Ligne budgétaire", help_text="Exemple : 980.912.32.31"
    )
    code = models.PositiveIntegerField(
        verbose_name="Code CGNC",
        help_text=(
            "Code du plan comptable CGNC. À vérifier : envisager une ForeignKey vers "
            "votre modèle de plan comptable (app accounting) plutôt qu'un entier brut, "
            "pour garantir la cohérence avec votre plan comptable."
        ),
    )
    nature = models.CharField(max_length=20, choices=Nature.choices, verbose_name="Nature")
    beneficiaires = models.CharField(max_length=255, verbose_name="Bénéficiaires")
    montant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant de décompte")
    date_rejet = models.DateField(null=True, blank=True, verbose_name="Date de rejet")
    num_rejet = models.PositiveIntegerField(null=True, blank=True, verbose_name="Numéro de rejet")
    date_visa = models.DateField(null=True, blank=True, verbose_name="Date de visa")
    date_decaissement = models.DateField(
        null=True, blank=True, verbose_name="Date de décaissement", help_text="Décaissement sur compte TGR."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trésorerie (OP)"
        verbose_name_plural = "Trésorerie (OP)"
        ordering = ["-exercice", "-op"]
        constraints = [
            models.UniqueConstraint(fields=["op", "exercice"], name="unique_op_exercice"),
        ]
        indexes = [
            models.Index(fields=["exercice", "op"]),
            models.Index(fields=["ligne_budgetaire"]),
        ]

    def __str__(self):
        return f"OP {self.op}/{self.exercice} - {self.beneficiaires}"


class DepenseGid(models.Model):
    """Feuille Excel DEP_GID -- dépense suivie via le système GID."""

    class TypeDepense(models.TextChoices):
        SUBVENTION = "SUB", "Subvention"
        CONVENTION = "CONV", "Convention"
        MARCHE = "MARCHE", "Marché"
        AUTRE = "AUTRE", "Autre"  # Liste incomplète dans la source -- à compléter.

    class Etat(models.TextChoices):
        TRANSMIS = "TRANSMIS", "Transmis"
        CONTROLE = "CONTROLE", "Contrôlé"
        VALIDE = "VALIDE", "Validé"
        REJETE = "REJETE", "Rejeté"
        # Liste illustrative -- la source ne montre que "Transmis..., Contrôlée...". À confirmer.

    montant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant d'OP")
    beneficiaire = models.CharField(max_length=255, verbose_name="Bénéficiaire")
    lf_depense = models.PositiveSmallIntegerField(verbose_name="Année d'engagement (Loi de finances)")
    num_depense = models.PositiveIntegerField(verbose_name="Numéro de dépense")
    type_depense = models.CharField(max_length=10, choices=TypeDepense.choices, verbose_name="Type de dépense")
    etat = models.CharField(max_length=15, choices=Etat.choices, verbose_name="État")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dépense (GID)"
        verbose_name_plural = "Dépenses (GID)"
        ordering = ["-lf_depense", "-num_depense"]
        constraints = [
            models.UniqueConstraint(fields=["num_depense", "lf_depense"], name="unique_depense_lf"),
        ]

    def __str__(self):
        return f"Dépense {self.num_depense}/{self.lf_depense} - {self.beneficiaire}"


class ExecutionBudgetaire(models.Model):
    """Feuille Excel EXE_BUD -- exécution budgétaire d'un OP."""

    class TypeBudget(models.TextChoices):
        RAM_EXPLOIT = "RAM_EXPLOIT", "RAM exploitation"
        BUDGET_EXPLOIT = "BUDGET_EXPLOIT", "Budget exploitation"
        RAM_INVEST = "RAM_INVEST", "RAM investissement"
        BUDGET_INVEST = "BUDGET_INVEST", "Budget investissement"
        # Source : "RAM exploit, Bud exploit....." -- complété par symétrie avec INV/EXP
        # de FICHE_MARCHE. À confirmer.

    num_op = models.PositiveIntegerField(verbose_name="Numéro d'OP")
    montant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant d'OP")
    exercice_paiement = models.PositiveSmallIntegerField(verbose_name="Exercice de paiement")
    exercice_origine = models.PositiveSmallIntegerField(verbose_name="Exercice d'origine (engagement)")
    type_budget = models.CharField(max_length=20, choices=TypeBudget.choices, verbose_name="Type de budget")
    ligne_budgetaire = models.CharField(max_length=255, verbose_name="Ligne budgétaire")
    imputation_budgetaire = models.CharField(max_length=50, verbose_name="Imputation budgétaire")
    beneficiaire = models.CharField(max_length=255, verbose_name="Bénéficiaire")
    date_validation_tp = models.DateField(null=True, blank=True, verbose_name="Date de validation du TP (visa)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Exécution budgétaire"
        verbose_name_plural = "Exécutions budgétaires"
        ordering = ["-exercice_paiement", "-num_op"]
        indexes = [
            models.Index(fields=["exercice_paiement", "num_op"]),
        ]

    def __str__(self):
        return f"OP {self.num_op} - exécution {self.exercice_origine}/{self.exercice_paiement}"
