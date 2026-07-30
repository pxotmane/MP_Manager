from decimal import Decimal
from django.core.validators import RegexValidator
from django.db import models


# --- Validators ---
rib_validator = RegexValidator(
    regex=r"^\d{24}$",
    message="Un RIB marocain comporte exactement 24 chiffres.",
)


# --- Base Mixin / Abstract Model ---
class TimeStampedModel(models.Model):
    """Classe abstraite fournissant l'horodatage automatique."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        abstract = True


# --- Main Models ---
class FicheMarche(TimeStampedModel):
    """Fiche administrative et financière d'un marché public."""

    class TypeBudget(models.TextChoices):
        INV = "INV", "Investissement"
        EXP = "EXP", "Exploitation"

    class ModePassation(models.TextChoices):
        APPEL_OFFRES_OUVERT = "AOO", "Appel d'offres ouvert"
        APPEL_OFFRES_OUVERT_SIMPLIFIE = "AOS", "Appel d'offres ouvert simplifié"
        APPEL_OFFRES_AVEC_PRESELECTION = "AOP", "Appel d'offres avec présélection"
        APPEL_OFFRES_NATIONAL = "AON", "Appel d'offres national"
        APPEL_OFFRES_INTERNATIONAL = "AOI", "Appel d'offres international"
        APPEL_OFFRES_RESTREINT = "AOR", "Appel d'offres restreint"
        CONCOURS = "CONCOURS", "Concours"
        PROCEDURE_NEGOCIEE = "NEGOCIEE", "Procédure négociée"

    class TypesMarche(models.TextChoices):
        MARCHE_CADRE = "MARCHE_CADRE", "Marché cadre"
        MARCHE_RECONDUCTIBLE = "MARCHE_RECONDUCTIBLE", "Marché reconductible"
        MARCHE_ALLOTIS = "MARCHE_ALLOTIS", "Marché alloti"
        MARCHE_CONCEP_REALISATION = "MARCHE_CONCEP_REALISATION", "Marché conception-réalisation"
        MARCHE_TRANCHES_CONDITIONNELLES = "MARCHE_TRANCHES_CONDITIONNELLES", "Marché à tranches conditionnelles"
        DIALOGUE_COMPETITIF = "DIALOGUE_COMPETITIF", "Dialogue compétitif"
        OFFRE_SPONTANEE = "OFFRE_SPONTANEE", "Offre spontanée"

    # Identification & Classification
    num_marche = models.CharField(max_length=50, unique=True, verbose_name="Numéro de marché")
    type_budget = models.CharField(max_length=5, choices=TypeBudget.choices, verbose_name="Type de budget")
    imputation_budgetaire = models.CharField(
        max_length=50, verbose_name="Imputation budgétaire", help_text="Exemple : 980.912.50.53"
    )
    objet = models.TextField(verbose_name="Objet du marché")
    titulaire = models.CharField(max_length=255, verbose_name="Titulaire du marché")
    mode_passation = models.CharField(
        max_length=10, choices=ModePassation.choices, verbose_name="Mode de passation"
    )
    type_marche = models.CharField(
        max_length=150, choices=TypesMarche.choices, verbose_name="Type de marché"
    )
    exercice_budgetaire = models.PositiveIntegerField(verbose_name="Exercice budgétaire")

    # Coordonnées bancaires
    rib = models.CharField(
        max_length=24,
        validators=[rib_validator],
        verbose_name="RIB",
        help_text="24 chiffres. Stocké en CharField pour préserver les zéros initiaux.",
    )
    dom_bancaire = models.CharField(max_length=255, verbose_name="Domiciliation bancaire")

    # Dates & Délais
    date_notif_appro = models.DateField(null=True, blank=True, verbose_name="Date de notification d'approbation")
    delai_execution = models.PositiveIntegerField(verbose_name="Délai d'exécution (mois)")

    # Éléments financiers
    montant_ht = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant HT")
    tva = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name="TVA (%)")
    rabais = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Rabais (%)")
    majoration = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Majoration (%)")
    
    montant_ttc = models.DecimalField(
        max_digits=14, decimal_places=2, editable=False, default=Decimal("0.00"), verbose_name="Montant TTC"
    )
    avenant = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), verbose_name="Montant des avenants")
    montant_global_ttc = models.DecimalField(
        max_digits=14, decimal_places=2, editable=False, default=Decimal("0.00"), verbose_name="Montant global TTC"
    )

    # Cautions & Garanties
    caution_provisoire = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Caution provisoire"
    )
    caution_definitive = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Caution définitive"
    )
    retenue_garantie = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"), verbose_name="Retenue de garantie (%)"
    )

    # États du marché
    marche_solde = models.BooleanField(default=False, verbose_name="Marché soldé")
    marche_resilie = models.BooleanField(default=False, verbose_name="Marché résilié")
    info_supp = models.TextField(blank=True, verbose_name="Informations supplémentaires")

    class Meta:
        verbose_name = "Fiche marché"
        verbose_name_plural = "Fiches marché"
        ordering = ["-date_notif_appro", "num_marche"]

    def __str__(self):
        return f"Marché n° {self.num_marche} - {self.titulaire}"

    @property
    def is_nanti(self) -> bool:
        """Vérifie dynamiquement si le marché fait l'objet d'un nantissement."""
        return self.nantissements.exists()

    def calculate_totals(self):
        """Calcule avec précision les montants TTC et Global TTC."""
        ht = self.montant_ht or Decimal("0.00")
        tva_rate = (self.tva or Decimal("0.00")) / Decimal("100")
        rabais_rate = (self.rabais or Decimal("0.00")) / Decimal("100")
        majoration_rate = (self.majoration or Decimal("0.00")) / Decimal("100")

        # Calcul : HT * (1 + TVA) * (1 - Rabais) * (1 + Majoration)
        ttc = ht * (Decimal("1.00") + tva_rate) * (Decimal("1.00") - rabais_rate) * (Decimal("1.00") + majoration_rate)
        self.montant_ttc = round(ttc, 2)
        self.montant_global_ttc = round(self.montant_ttc + (self.avenant or Decimal("0.00")), 2)

    def save(self, *args, **kwargs):
        """Recalcule automatiquement les montants avant sauvegarde."""
        self.calculate_totals()
        super().save(*args, **kwargs)


class Nantissement(TimeStampedModel):
    """Acte de nantissement adossé à un marché."""

    marche = models.ForeignKey(
        FicheMarche, on_delete=models.PROTECT, related_name="nantissements", verbose_name="Marché concerné"
    )
    num_acte = models.CharField(max_length=50, verbose_name="Numéro de l'acte")
    date_nant = models.DateField(verbose_name="Date de nantissement")
    mtt_nant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant nanti")
    entite_nant = models.CharField(
        max_length=255, verbose_name="Organisme bénéficiaire", help_text="Banque / Établissement financier"
    )
    rib = models.CharField(max_length=24, validators=[rib_validator], verbose_name="RIB de l'organisme")
    dom_banc = models.CharField(max_length=255, verbose_name="Domiciliation bancaire")

    class Meta:
        verbose_name = "Nantissement"
        verbose_name_plural = "Nantissements"
        ordering = ["-date_nant"]

    def __str__(self):
        return f"Nantissement n° {self.num_acte} - Marché {self.marche.num_marche}"


class Penalite(TimeStampedModel):
    """Pénalité financière appliquée à un marché."""

    marche = models.ForeignKey(
        FicheMarche, on_delete=models.PROTECT, related_name="penalites", verbose_name="Marché concerné"
    )
    num_penalite = models.CharField(max_length=50, verbose_name="Numéro de la pénalité")
    date_penalite = models.DateField(verbose_name="Date d'application")
    mtt_penalite = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant de la pénalité")
    motif_penalite = models.TextField(verbose_name="Motif")

    class Meta:
        verbose_name = "Pénalité"
        verbose_name_plural = "Pénalités"
        ordering = ["-date_penalite"]

    def __str__(self):
        return f"Pénalité n° {self.num_penalite} - Marché {self.marche.num_marche}"