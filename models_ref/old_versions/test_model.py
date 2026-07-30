from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Sum, DecimalField, Case, When, Value
from decimal import Decimal

rib_validator = RegexValidator(
    regex=r"^\d{24}$",
    message="Un RIB marocain comporte exactement 24 chiffres.",
)


class FicheMarche(models.Model):
    """Feuille Excel FICHE_MARCHE -- fiche administrative et financière d'un marché."""

    class TypeBudget(models.TextChoices):
        INV = "INV", "Investissement"
        EXP = "EXP", "Exploitation"

    class ModePassation(models.TextChoices):
        APPEL_OFFRES_OUVERT = "AOO", "Appel d'offres ouvert"
        APPEL_OFFRES_OUVERT_SIMPLIFIE = "AOS", "Appel d'offres ouvert simplifié"
        APPEL_OFFRES_AVEC_PRESELECTION = "AOP", "Appel d'offres avec présélection"
        APPEL_OFFRES_NATIONAL= "AON", "Appel d'offres national"
        APPEL_OFFRES_INTERNATIONAL = "AOI", "Appel d'offres international"
        APPEL_OFFRES_RESTREINT = "AOR", "Appel d'offres restreint"
        CONCOURS = "CONCOURS", "Concours"
        PROCEDURE_NEGOCIEE = "NEGOCIEE", "Procédure négociée"

    class TypesMarche(models.TextChoices):
        MARCHE_CADRE = "MARCHE_CADRE", "Marché cadre"
        MARCHE_RECONDUCTIBLE = "MARCHE_RECONDUCTIBLE", "Marché reconductible"
        MARCHE_ALLOTIS="MARCHE_ALLOTIS", "Marché allotis"
        MARCHE_CONCEP_REALISATION = "MARCHE_CONCEP_REALISATION", "Marché conception-réalisation"
        MARCHE_TRANCHES_CONDITIONNELLES = "MARCHE_TRANCHES_CONDITIONNELLES", "Marché à tranches conditionnelles"
        DIALOGUE_COMPETITIF = "DIALOGUE_COMPETITIF", "Dialogue compétitif"
        OFFRE_SPONTANEE = "OFFRE_SPONTANEE", "Offre spontanée"

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
    rib = models.CharField(
        max_length=24,
        validators=[rib_validator],
        verbose_name="RIB",
        help_text=(
            "24 chiffres. Stocké en CharField (et non INT comme indiqué dans le fichier "
            "source) pour préserver les zéros non significatifs et éviter un dépassement "
            "de capacité d'un champ entier."
        ),
    )
    dom_bancaire = models.CharField(max_length=255, verbose_name="Domiciliation bancaire")
    nantis = models.BooleanField(
        default=False,
        verbose_name="Nanti",
        help_text=(
            "Envisager de calculer ce champ à partir de la relation nantissements "
            "(self.nantissements.exists()) plutôt que de le stocker, pour éviter une "
            "désynchronisation."
        ),
    )
    date_notif_appro = models.DateField(null=True, blank=True, verbose_name="Date de notification d'approbation")
    delai_execution = models.PositiveIntegerField(verbose_name="Délai d'exécution (mois)")
    montant_ht = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant hors taxe")
    tva = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="TVA")
    rabais = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Rabais",
        help_text=(
            "En pourcentage"
        )
    )
    majoration = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Majoration", help_text="En pourcentage")
    montant_ttc = models.GeneratedField(
        expression=F("montant_ht") * (1 + F("tva") / 100) * (1 - F("rabais") / 100) * (1 + F("majoration") / 100),
        verbose_name="Montant TTC",
        output_field=models.DecimalField(max_digits=14, decimal_places=2),
        db_persist=True,
        help_text="Montant TTC calculé à partir du montant HT, de la TVA, du rabais et de la majoration.",
    )
    avenant = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Montant des avenants")
    montant_global_ttc = models.GeneratedField(
        expression=models.F("montant_ttc") + models.F("avenant"), 
        verbose_name="Montant global TTC",
        output_field=models.DecimalField(max_digits=14, decimal_places=2),
        db_persist=True,
        help_text="Montant TTC + avenant, en cas de modification par avenant.",
    )
    # montant_global_ttc = models.DecimalField(
    #     max_digits=14,
    #     decimal_places=2,
    #     verbose_name="Montant global TTC",
    #     help_text="Généralement montant_ttc + avenant -- à recalculer/valider en conséquence.",
    # )
    caution_provisoire = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Caution provisoire"
    )
    caution_definitive = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, verbose_name="Caution définitive"
    )
    retenue_garantie = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, default=0, verbose_name="Retenue de garantie"
    )
    marche_solde = models.BooleanField(default=False, verbose_name="Marché soldé")
    marche_resilie = models.BooleanField(default=False, verbose_name="Marché résilié")
    info_supp = models.TextField(blank=True, verbose_name="Informations supplémentaires")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fiche marché"
        verbose_name_plural = "Fiches marché"
        ordering = ["-date_notif_appro", "num_marche"]

    def __str__(self):
        return f"{self.num_marche} - {self.titulaire} - {self.montant_global_ttc} DH"

class Nantissement(models.Model):
    """
    Feuille Excel NANTISSEMENT -- nantissement (gage bancaire) adossé à un marché.

    NUM_MCH était typé "CHAR FIELD" dans le fichier source, mais désigne en réalité
    le marché concerné : converti ici en ForeignKey vers FicheMarche plutôt qu'en
    champ texte dupliqué.
    """

    marche = models.ForeignKey(
        FicheMarche, on_delete=models.PROTECT, related_name="nantissements", verbose_name="Marché"
    )
    # i want to select num_marche from FicheMarche model as a multiple choice and store it in this field 
    # num_marche = models.CharField(max_length=50, verbose_name="Numéro de marché")
    num_acte = models.CharField(max_length=50, verbose_name="Numéro de l'acte de nantissement")
    date_nant = models.DateField(verbose_name="Date de nantissement")
    mtt_nant = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant nanti")
    entite_nant = models.CharField(
        max_length=255,
        verbose_name="Entité bénéficiaire du nantissement",
        help_text=(
            "Interprété comme la banque en faveur de laquelle le nantissement est "
            "constitué (cohérent avec RIB/domiciliation ci-dessous) plutôt que le "
            "titulaire du marché -- à confirmer."
        ),
    )
    rib = models.CharField(max_length=24, validators=[rib_validator], verbose_name="RIB")
    dom_banc = models.CharField(max_length=255, verbose_name="Domiciliation bancaire")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nantissement"
        verbose_name_plural = "Nantissements"
        ordering = ["-date_nant"]

    def __str__(self):
        return f"Nantissement {self.num_acte} - Marché {self.marche.num_marche}"

class Penalite(models.Model):
    """
    Feuille Excel PENALITE -- pénalités financières liées à un marché.

    NUM_MCH était typé "CHAR FIELD" dans le fichier source, mais désigne en réalité
    le marché concerné : converti ici en ForeignKey vers FicheMarche plutôt qu'en
    champ texte dupliqué.
    """

    marche = models.ForeignKey(
        FicheMarche, on_delete=models.PROTECT, related_name="penalites", verbose_name="Marché"
    )
    # num_marche = models.CharField(max_length=50, verbose_name="Numéro de marché")
    num_penalite = models.CharField(max_length=50, verbose_name="Numéro de la pénalité")
    date_penalite = models.DateField(verbose_name="Date de la pénalité")
    mtt_penalite = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Montant de la pénalité")
    motif_penalite = models.TextField(verbose_name="Motif de la pénalité")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pénalité"
        verbose_name_plural = "Pénalités"
        ordering = ["-date_penalite"]

    def __str__(self):
        return f"Pénalité {self.num_penalite} - Marché {self.marche.num_marche}"


# for testing if github work 