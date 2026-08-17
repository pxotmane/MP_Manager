from django.db import models


class Tresorerie(models.Model):
    """Feuille Excel TRESORERIE -- suivi d'un ordre de paiement (OP) jusqu'au décaissement."""

    class TypeBudget(models.TextChoices):
        RAM_EXP = "RAM EXP", "RAM Exploitation"
        RAM_INV = "RAM INV", "RAM Investissement"
        BUDGET_EXP = "BUDGET EXP", "Budget Exploitation"
        BUDGET_INV = "BUDGET INV", "Budget Investissement"

    class Nature(models.TextChoices):
        MARCHE = "MARCHE", "Marché"
        HRS_SUPP = "HEURES_SUPP", "Heures supplémentaires"
        BN_CMD = "BON COMMANDE", "Bon de commande"
        CNV = "CONVENTION", "Convention"
        FR_AUTO = "FRAIS AUTORISATION", "Frais autorisations"
        INSER = "INSERSTION", "Insertion"
        IND_DPL = "INDEMNITE DEPLACEMENT", "Indemnité de déplacement"
        # AUTRE = "AUTRE", "Autre"  # Liste incomplète dans la source ("Marché, Heures supp...") -- à compléter.

    op = models.PositiveIntegerField(verbose_name="Numéro d'OP")
    ov = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Numéro d'OV",
        help_text="Renseigné l'ordre de virement.",
    )
    exercice = models.PositiveSmallIntegerField(verbose_name="Exercice d'origine")
    budget = models.CharField(
        max_length=10, choices=TypeBudget.choices, verbose_name="RAM ou Budget"
    )
    ligne_budgetaire = models.CharField(
        max_length=50,
        verbose_name="Ligne budgétaire",
        help_text="Exemple : 980.912.32.31",
    )
    code = models.PositiveIntegerField(
        verbose_name="Code CGNC",
        help_text=(
            "Code du plan comptable CGNC. À vérifier : envisager une ForeignKey vers "
            "votre modèle de plan comptable (app accounting) plutôt qu'un entier brut, "
            "pour garantir la cohérence avec votre plan comptable."
        ),
    )
    nature = models.CharField(
        max_length=50, choices=Nature.choices, verbose_name="Nature"
    )
    # 1. Le menu déroulant pour les Marchés (Relation)
    marche = models.ForeignKey(
        "marche.FicheMarche",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Numéro de marché",
    )

    # 2. Le champ texte pour les Bons de commande, Conventions, etc.
    reference_document = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Référence",
        help_text="N° Bons de commande, n°Conventions, etc. (hors Marchés, heures supp, indemnités).",
    )
    beneficiaires = models.CharField(max_length=255, verbose_name="Bénéficiaires")
    montant = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant de décompte"
    )
    date_rejet = models.DateField(null=True, blank=True, verbose_name="Date de rejet")
    num_rejet = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Numéro de rejet"
    )
    date_visa = models.DateField(null=True, blank=True, verbose_name="Date de visa")
    date_decaissement = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de décaissement",
        help_text="Décaissement sur compte TGR.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trésorerie"
        verbose_name_plural = "Trésorerie"
        ordering = ["-exercice", "-op"]
        constraints = [
            models.UniqueConstraint(
                fields=["op", "exercice"], name="unique_op_exercice"
            ),
        ]
        indexes = [
            models.Index(fields=["exercice", "op"]),
            models.Index(fields=["ligne_budgetaire"]),
        ]

    def __str__(self):
        return f"OP {self.op}/{self.exercice} - {self.beneficiaires}"
