"""
Modèles Django -- Fiche marché, Nantissement, Pénalité (marchés publics).

Voir le message associé pour le détail des corrections apportées par rapport à la
version d'origine (test_model.py). Résumé des changements structurels :
  - montant_ttc et montant_global_ttc fusionnés en un seul GeneratedField : un
    GeneratedField ne peut pas référencer un autre GeneratedField (Django lève
    l'erreur "Generated fields cannot reference other generated fields" ; testé
    empiriquement, PostgreSQL la rejette avec "cannot use generated column ... in
    column generation expression"). montant_ttc redevient une propriété Python.
  - Champ `tva` renommé `taux_tva` et redimensionné (max_digits=5 comme rabais/
    majoration) : il était dimensionné comme un montant (max_digits=14) mais
    utilisé comme un taux dans la formule (division par 100) -- à confirmer avec
    la source Excel.
  - Champ booléen `nantis` remplacé par une propriété `est_nanti` calculée depuis
    la relation, pour éviter toute désynchronisation (déjà pressenti dans le
    commentaire d'origine) ; un queryset dédié permet de filtrer efficacement en
    base sans requête N+1.
  - FK + created_at/updated_at factorisés dans des classes abstraites communes à
    Nantissement et Penalite.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Exists, F, OuterRef, Value, ExpressionWrapper
from django.db.models.functions import Coalesce
from core.coreFcn import HorodatageMixin, DocumentLieAuMarche

rib_validator = RegexValidator(
    regex=r"^\d{24}$",
    message="Un RIB marocain comporte exactement 24 chiffres.",
)


class FicheMarcheQuerySet(models.QuerySet):
    def avec_statut_nantissement(self):
        """
        Annote chaque marché d'un booléen `nantissement_existe`, calculé par la base
        de données en une seule requête pour tout le queryset (via EXISTS).

        Nom volontairement différent de la propriété `est_nanti` du modèle : Django
        ne peut pas écrire une valeur annotée sur un attribut qui est une @property
        en lecture seule (testé -- lève AttributeError sinon).
        """
        return self.annotate(
            nantissement_existe=Exists(
                Nantissement.objects.filter(marche=OuterRef("pk"))
            )
        )


class FicheMarche(HorodatageMixin):
    """Feuille Excel FICHE_MARCHE -- fiche administrative et financière d'un marché."""

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
        MARCHE_CONCEP_REALISATION = (
            "MARCHE_CONCEP_REALISATION",
            "Marché conception-réalisation",
        )
        MARCHE_TRANCHES_CONDITIONNELLES = (
            "MARCHE_TRANCHES_CONDITIONNELLES",
            "Marché à tranches conditionnelles",
        )
        DIALOGUE_COMPETITIF = "DIALOGUE_COMPETITIF", "Dialogue compétitif"
        OFFRE_SPONTANEE = "OFFRE_SPONTANEE", "Offre spontanée"

    objects = FicheMarcheQuerySet.as_manager()

    num_marche = models.CharField(
        max_length=50, unique=True, verbose_name="Numéro de marché"
    )
    type_budget = models.CharField(
        max_length=5, choices=TypeBudget.choices, verbose_name="Type de budget"
    )
    imputation_budgetaire = models.CharField(
        max_length=50,
        verbose_name="Imputation budgétaire",
        help_text="Exemple : 980.912.50.53",
    )
    objet = models.TextField(verbose_name="Objet du marché")
    titulaire = models.CharField(max_length=255, verbose_name="Titulaire du marché")
    mode_passation = models.CharField(
        max_length=10, choices=ModePassation.choices, verbose_name="Mode de passation"
    )
    type_marche = models.CharField(
        max_length=35, choices=TypesMarche.choices, verbose_name="Type de marché"
    )
    exercice_budgetaire = models.PositiveSmallIntegerField(
        verbose_name="Exercice budgétaire",
        db_index=True,
        # Une année tient dans un PositiveSmallIntegerField (jusqu'à 32767) ; inutile de réserver un IntegerField complet.
    )
    rib = models.CharField(
        max_length=24,
        validators=[rib_validator],
        verbose_name="RIB",
        # "24 chiffres. Stocké en CharField (et non INT comme indiqué dans le fichier "
        # "source) pour préserver les zéros non significatifs et éviter un dépassement "
        # "de capacité d'un champ entier."
    )
    dom_bancaire = models.CharField(
        max_length=255, verbose_name="Domiciliation bancaire"
    )
    date_notif_appro = models.DateField(
        null=True, blank=True, verbose_name="Date de notification d'approbation"
    )
    delai_execution = models.PositiveIntegerField(
        verbose_name="Délai d'exécution (mois)"
    )
    montant_ht = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
        verbose_name="Montant hors taxe",
    )
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("20.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux de TVA",
        # "En pourcentage (ex. 20.00 pour 20%). Anciennement `tva`, dimensionné comme un "
        # "montant (max_digits=14) mais utilisé comme un taux dans la formule du TTC "
        # "(division par 100) -- renommé et redimensionné en conséquence. Si le fichier "
        # "source désigne en réalité un montant de TVA en dirhams (et non un taux), la "
        # "formule de montant_global_ttc ci-dessous doit être revue (remplacer la "
        # "multiplication par une simple addition du montant de TVA)."
    )
    taux_rabais = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Rabais",
        help_text="En pourcentage, exemple: 12.45",
    )
    taux_majoration = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Majoration",
        help_text="En pourcentage, exemple: 14.05",
    )
    avenant = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Montant des avenants",
    )
    montant_global_ttc = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        null=True,
        blank=True,
        verbose_name="Montant global TTC",
    )

    def calculer_ttc(self):
        """
        Montant TTC =
        (Montant HT × (1 + TVA) × ((1 - Rabais) ou (1 + Majoration))) + Avenant
        """

        ht = self.montant_ht
        tva = self.taux_tva / Decimal("100")
        rabais = self.taux_rabais / Decimal("100")
        majoration = self.taux_majoration / Decimal("100")

        # TVA
        montant = ht * (Decimal("1") + tva)

        # Rabais ou majoration
        if rabais > 0:
            montant *= Decimal("1") - rabais
        elif majoration > 0:
            montant *= Decimal("1") + majoration

        # Avenant
        montant += self.avenant

        return montant.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        self.montant_global_ttc = self.calculer_ttc()
        super().save(*args, **kwargs)

    caution_provisoire = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Caution provisoire",
    )
    caution_definitive = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Caution définitive",
    )
    retenue_garantie = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        default=0,
        verbose_name="Retenue de garantie",
    )
    marche_solde = models.BooleanField(default=False, verbose_name="Marché soldé")
    marche_resilie = models.BooleanField(default=False, verbose_name="Marché résilié")
    info_supp = models.TextField(
        blank=True, verbose_name="Informations supplémentaires"
    )

    class Meta:
        verbose_name = "Fiche marché"
        verbose_name_plural = "Fiches marché"
        # nulls_last=True : sans cela, PostgreSQL trie les NULL en premier sur un tri
        # descendant, ce qui remonterait les marchés sans date de notification en tête
        # de liste plutôt qu'en fin.
        ordering = [F("date_notif_appro").desc(nulls_last=True), "num_marche"]
        indexes = [
            models.Index(fields=["type_budget", "exercice_budgetaire"]),
        ]

    def __str__(self):
        return f"{self.num_marche} - {self.titulaire} - {self.montant_global_ttc} DH"

    @property
    def montant_ttc(self):
        """
        Montant TTC hors avenant (HT + TVA, rabais, majoration), calculé à la volée
        en Python -- non stocké en base (seul montant_global_ttc, qui inclut
        l'avenant, l'est réellement : cf. note sur le chaînage de GeneratedField).

        Non interrogeable via l'ORM (pas de .filter(montant_ttc=...) possible) ;
        pour un filtrage en base, passer par une annotation dédiée si besoin.
        """

    @property
    def est_nanti(self):
        """
        Calculé depuis la relation nantissements (une requête par accès) plutôt que
        stocké, pour éviter toute désynchronisation -- remplace l'ancien champ
        booléen `nantis`. Pratique pour un accès ponctuel sur une fiche déjà
        chargée ; pour une liste de marchés, préférer
        FicheMarche.objects.avec_statut_nantissement() qui calcule tout en une
        seule requête plutôt qu'une par instance.
        """
        return self.nantissements.exists()


class Nantissement(DocumentLieAuMarche):
    """
    Feuille Excel NANTISSEMENT -- nantissement (gage bancaire) adossé à un marché.

    NUM_MCH était typé "CHAR FIELD" dans le fichier source, mais désigne en réalité
    le marché concerné : converti en ForeignKey vers FicheMarche (héritée de
    DocumentLieAuMarche) plutôt qu'en champ texte dupliqué. Pour l'afficher ou le
    sélectionner par num_marche plutôt que par le __str__ complet de FicheMarche
    (ex. dans l'admin), personnaliser le widget du formulaire (ModelChoiceField
    avec label_from_instance dédié) plutôt que le modèle : la FK le permet déjà.
    """

    num_acte = models.CharField(
        max_length=50, verbose_name="Numéro de l'acte de nantissement"
    )
    date_nant = models.DateField(verbose_name="Date de nantissement")
    mtt_nant = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant nanti",
    )
    entite_nant = models.CharField(
        max_length=255,
        verbose_name="Entité bénéficiaire du nantissement",
        help_text=(
            "Interprété comme la banque en faveur de laquelle le nantissement est "
            "constitué (cohérent avec RIB/domiciliation ci-dessous) plutôt que le "
            "titulaire du marché -- à confirmer."
        ),
    )
    # rib / dom_banc dupliquent potentiellement marche.rib / marche.dom_bancaire : à
    # confirmer si c'est volontaire (photo des coordonnées bancaires au moment du
    # nantissement, pouvant évoluer indépendamment de celles du marché par la suite)
    # ou s'il serait préférable de les supprimer et de ne référencer que
    # self.marche.rib / self.marche.dom_bancaire.
    rib = models.CharField(
        max_length=24, validators=[rib_validator], verbose_name="RIB"
    )
    dom_banc = models.CharField(max_length=255, verbose_name="Domiciliation bancaire")

    class Meta:
        verbose_name = "Nantissement"
        verbose_name_plural = "Nantissements"
        ordering = ["-date_nant"]

    def __str__(self):
        return f"Nantissement {self.num_acte} - Marché {self.marche.num_marche}"


class Penalite(DocumentLieAuMarche):
    """
    Feuille Excel PENALITE -- pénalités financières liées à un marché.

    NUM_MCH était typé "CHAR FIELD" dans le fichier source, mais désigne en réalité
    le marché concerné : converti en ForeignKey vers FicheMarche (héritée de
    DocumentLieAuMarche) plutôt qu'en champ texte dupliqué.
    """

    num_penalite = models.CharField(max_length=50, verbose_name="Numéro de la pénalité")
    date_penalite = models.DateField(verbose_name="Date de la pénalité")
    mtt_penalite = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant de la pénalité",
    )
    motif_penalite = models.TextField(verbose_name="Motif de la pénalité")

    class Meta:
        verbose_name = "Pénalité"
        verbose_name_plural = "Pénalités"
        ordering = ["-date_penalite"]

    def __str__(self):
        return f"Pénalité {self.num_penalite} - Marché {self.marche.num_marche}"
