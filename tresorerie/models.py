from decimal import Decimal
from django.db import models
from core.coreFcn import HorodatageMixin


class BudgetExercice(HorodatageMixin):
    """Crédits budgétaires annuels par exercice (Exploitation et Investissement)."""

    exercice = models.PositiveSmallIntegerField(
        unique=True,
        verbose_name="Exercice budgétaire",
        help_text="Année budgétaire (ex: 2026, 2025...)",
    )
    credit_exploitation = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Crédit Exploitation",
        help_text="Crédit budgétaire alloué en dirhams (Exploitation)",
    )
    credit_investissement = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Crédit Investissement",
        help_text="Crédit budgétaire alloué en dirhams (Investissement)",
    )
    observation = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Observation / Notes",
    )

    class Meta:
        verbose_name = "Budget par Exercice"
        verbose_name_plural = "Budgets par Exercice"
        ordering = ["-exercice"]

    @property
    def total_credit(self):
        return (self.credit_exploitation or Decimal("0.00")) + (
            self.credit_investissement or Decimal("0.00")
        )

    def __str__(self):
        return f"Budget {self.exercice} — Total: {self.total_credit} DH"


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


class OrdreRecette(HorodatageMixin):
    """Ordre de recette dans la trésorerie."""

    class Nature(models.TextChoices):
        ALIMENTATION = "ALIMENTATION DE LA TRESORERIE", "Alimentation de la trésorerie"
        CONFISCATION = "RECETTES CONFISCATION", "Recettes confiscation"
        PENALITES = "PENALITES DE RETARD", "Pénalités de retard"
        REJET_TGR = "REJET DE LA TGR", "Rejet de la TGR"

    class TypeBudget(models.TextChoices):
        EXPLOITATION = "EXPLOITATION", "Exploitation"
        INVESTISSEMENT = "INVESTISSEMENT", "Investissement"

    class Etat(models.TextChoices):
        NON_ETABLI = "NON ETABLI", "Non établi"
        ETABLI = "ETABLI", "Établi"

    exercice = models.PositiveSmallIntegerField(
        verbose_name="Exercice budgétaire",
        help_text="Année de l'exercice (ex: 2026)",
    )
    num_ordre = models.PositiveIntegerField(
        verbose_name="N° d'ordre de recette",
    )
    date_decision = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de décision",
    )
    num_decision = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="N° de décision",
    )
    debiteur = models.CharField(
        max_length=255,
        verbose_name="Débiteur",
    )
    nature = models.CharField(
        max_length=50,
        choices=Nature.choices,
        verbose_name="Nature",
    )
    budget = models.CharField(
        max_length=20,
        choices=TypeBudget.choices,
        verbose_name="Budget",
    )
    date_encaissement = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'encaissement",
    )
    montant = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Montant (DH)",
    )
    etat = models.CharField(
        max_length=20,
        choices=Etat.choices,
        default=Etat.NON_ETABLI,
        verbose_name="État",
    )
    observation = models.TextField(
        blank=True,
        verbose_name="Observation / Notes",
    )

    class Meta:
        verbose_name = "Ordre de Recette"
        verbose_name_plural = "Ordres de Recette"
        ordering = ["-exercice", "num_ordre"]
        indexes = [
            models.Index(fields=["exercice", "num_ordre"]),
        ]

    def __str__(self):
        return f"OR N°{self.num_ordre}/{self.exercice} - {self.debiteur} ({self.montant} DH)"
