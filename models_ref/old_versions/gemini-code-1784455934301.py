from django.db import models

# ==========================================
# CHOICES DEFINITIONS
# ==========================================

BUDGET_CHOICES = [
    ('RAM', 'RAM'),
    ('BUDGET', 'Budget'),
]

NATURE_CHOICES = [
    ('MARCHE', 'Marché'),
    ('HEURES_SUPP', 'Heures supplémentaires'),
    # Ajoutez d'autres options si nécessaire
]

TYPE_BUDGET_EXE_CHOICES = [
    ('RAM_EXPLOIT', 'RAM exploit'),
    ('BUD_EXPLOIT', 'Bud exploit'),
    # Ajoutez d'autres options si nécessaire
]

TYPE_BUDGET_MARCHE_CHOICES = [
    ('INV', 'Investissement (INV)'),
    ('EXP', 'Exploitation (EXP)'),
]

MODE_PASSATION_CHOICES = [
    ('AO', "Appel d'offre"),
    ('CONCOURS', 'Concours'),
    # Ajoutez d'autres options si nécessaire
]


# ==========================================
# DJANGO MODELS
# ==========================================

class Tresorerie(models.Model):
    op = models.IntegerField(verbose_name="Numéro d'OP", blank=True, null=True)
    ov = models.CharField(max_length=50, verbose_name="Numéro d'OV", blank=True, null=True)
    exercice = models.IntegerField(verbose_name="Exercice d'origine", blank=True, null=True)
    budget = models.CharField(
        max_length=20, 
        choices=BUDGET_CHOICES, 
        verbose_name="RAM ou Budget", 
        blank=True, 
        null=True
    )
    ligne_budgetaire = models.CharField(max_length=100, verbose_name="Ligne budgétaire (ex: 980.912.32.31)", blank=True, null=True)
    code = models.IntegerField(verbose_name="Code CGNC", blank=True, null=True)
    nature = models.CharField(
        max_length=50, 
        choices=NATURE_CHOICES, 
        verbose_name="Nature", 
        blank=True, 
        null=True
    )
    beneficiaires = models.CharField(max_length=255, verbose_name="Nom de bénéficiaires", blank=True, null=True)
    montant = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Montant de décompte", blank=True, null=True)
    date_rejet = models.DateField(verbose_name="Date de rejet", blank=True, null=True)
    num_rejet = models.IntegerField(verbose_name="Numéro de rejet", blank=True, null=True)
    date_visa = models.DateField(verbose_name="Date de visa", blank=True, null=True)
    date_decaissement = models.DateField(verbose_name="Date décaissement sur compte TGR", blank=True, null=True)

    def __str__(self):
        return f"OP {self.op} - {self.beneficiaires}"


class DepGid(models.Model):
    montant = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Montant d'OP", blank=True, null=True)
    beneficiaire = models.CharField(max_length=255, verbose_name="Nom de bénéficiaire", blank=True, null=True)
    lf_depense = models.IntegerField(verbose_name="Année d'engagement de dépense", blank=True, null=True)
    num_depense = models.IntegerField(verbose_name="Numéro de dépense", blank=True, null=True)
    type_depense = models.CharField(max_length=100, verbose_name="Type de dépense (SUB, CONV, MARCHE...)", blank=True, null=True)
    etat = models.CharField(max_length=100, verbose_name="État (Transmis, Contrôlée...)", blank=True, null=True)

    def __str__(self):
        return f"Dépense N° {self.num_depense} - {self.beneficiaire}"


class ExeBud(models.Model):
    num_op = models.IntegerField(verbose_name="Numéro d'OP", blank=True, null=True)
    montant = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Montant d'OP", blank=True, null=True)
    exercice_paiement = models.IntegerField(verbose_name="Année en cours (Exercice de paiement)", blank=True, null=True)
    exercice_origine = models.IntegerField(verbose_name="Année d'engagement (Exercice d'origine)", blank=True, null=True)
    type_budget = models.CharField(
        max_length=50, 
        choices=TYPE_BUDGET_EXE_CHOICES, 
        verbose_name="Type de budget", 
        blank=True, 
        null=True
    )
    ligne_budgetaire = models.CharField(max_length=255, verbose_name="Nom de la ligne budgétaire", blank=True, null=True)
    imputation_budgetaire = models.CharField(max_length=100, verbose_name="Code budgétaire (Imputation)", blank=True, null=True)
    beneficiaire = models.CharField(max_length=255, verbose_name="Nom de bénéficiaire", blank=True, null=True)
    date_validation_tp = models.DateField(verbose_name="Date de visa (Validation de TP)", blank=True, null=True)

    def __str__(self):
        return f"ExeBud OP {self.num_op} ({self.exercice_paiement})"


class FicheMarche(models.Model):
    num_marche = models.CharField(max_length=100, unique=True, verbose_name="Numéro de marché")
    type_budget = models.CharField(
        max_length=10, 
        choices=TYPE_BUDGET_MARCHE_CHOICES, 
        verbose_name="INV ou EXP", 
        blank=True, 
        null=True
    )
    impu_bud = models.CharField(max_length=100, verbose_name="Imputation budgétaire (ex: 980.912.50.53)", blank=True, null=True)
    objet = models.TextField(verbose_name="Objet du marché", blank=True, null=True)
    titulaire = models.CharField(max_length=255, verbose_name="Le titulaire du marché", blank=True, null=True)
    mode_passation = models.CharField(
        max_length=100, 
        choices=MODE_PASSATION_CHOICES, 
        verbose_name="Mode de passation", 
        blank=True, 
        null=True
    )
    rib = models.CharField(max_length=24, verbose_name="Le RIB", blank=True, null=True)
    dom_bancaire = models.CharField(max_length=255, verbose_name="La banque domicile du compte", blank=True, null=True)
    nantis = models.BooleanField(default=False, verbose_name="Nantis (OUI/NON)")
    date_notif_appro = models.DateField(verbose_name="Date de la notification d'approbation", blank=True, null=True)
    delai_execution = models.IntegerField(verbose_name="Le délai d'exécution du marché en mois", blank=True, null=True)
    
    # Données financières du Marché
    montant_ht = models.DecimalField(max_digits=17, decimal_places=2, verbose_name="Le montant du marché hors taxe", blank=True, null=True)
    tva = models.DecimalField(max_digits=17, decimal_places=2, verbose_name="La TVA calculée sur le montant hors taxe", blank=True, null=True)
    rabais = models.DecimalField(max_digits=17, decimal_places=2, verbose_name="Le Rabais proposé par le titulaire", blank=True, null=True)
    majoration = models.DecimalField(max_digits=17, decimal_places=2, verbose_name="La majoration proposée par le titulaire", blank=True, null=True)
    montant_ttc = models.DecimalField(max_digits=17, decimal_places=2, verbose_name="Le montant du marché TTC", blank=True, null=True)
    avenant = models.DecimalField(max_digits=17, decimal_places=2, verbose_name="Avenant sur le marché", blank=True, null=True)
    montant_global_ttc = models.DecimalField(max_digits=17, decimal_places=2, verbose_name="Montant global du marché TTC", blank=True, null=True)
    
    # Cautions & Garanties
    caution_provisoire = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Le cautionnement provisoire", blank=True, null=True)
    caution_definitive = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Le cautionnement définitif", blank=True, null=True)
    retenue_garantie = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="La retenue de garantie", blank=True, null=True)
    
    # Statuts
    marche_solde = models.BooleanField(default=False, verbose_name="Marché soldé (OUI/NON)")
    marche_resilie = models.BooleanField(default=False, verbose_name="Marché résilié (OUI/NON)")
    info_supp = models.TextField(verbose_name="Des informations supplémentaires", blank=True, null=True)

    def __str__(self):
        return f"Marché N° {self.num_marche} - {self.titulaire}"


class Nantissement(models.Model):
    marche = models.ForeignKey(
        FicheMarche, 
        on_delete=models.CASCADE, 
        to_field='num_marche',
        related_name='nantissements',
        verbose_name="Marché faisant l'objet du nantissement"
    )
    num_acte = models.CharField(max_length=100, verbose_name="Numéro de l'acte de nantissement", blank=True, null=True)
    date_nant = models.DateField(verbose_name="Date de nantissement", blank=True, null=True)
    mtt_nant = models.DecimalField(max_digits=17, decimal_places=2, verbose_name="Montant objet de nantissement", blank=True, null=True)
    entit_nant = models.CharField(max_length=255, verbose_name="Entité qui nantis le marché", blank=True, null=True)
    rib = models.CharField(max_length=24, verbose_name="RIB de l'entité de nantissement", blank=True, null=True)
    dom_banc = models.CharField(max_length=255, verbose_name="Domicile de compte de nantissement", blank=True, null=True)

    def __str__(self):
        return f"Nantissement Acte {self.num_acte} - Marché {self.marche.num_marche}"