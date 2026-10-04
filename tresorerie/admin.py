from django.contrib import admin
from .models import Tresorerie, BudgetExercice, OrdreRecette


@admin.register(Tresorerie)
class TresorerieAdmin(admin.ModelAdmin):
    list_display = ("op", "exercice", "budget", "nature", "montant")
    list_filter = ("exercice", "budget", "nature")
    search_fields = ("op", "beneficiaires")


@admin.register(BudgetExercice)
class BudgetExerciceAdmin(admin.ModelAdmin):
    list_display = (
        "exercice",
        "credit_exploitation",
        "credit_investissement",
        "total_credit",
        "updated_at",
    )
    search_fields = ("exercice", "observation")
    ordering = ("-exercice",)


@admin.register(OrdreRecette)
class OrdreRecetteAdmin(admin.ModelAdmin):
    list_display = (
        "num_ordre",
        "exercice",
        "date_decision",
        "num_decision",
        "debiteur",
        "nature",
        "budget",
        "montant",
        "date_encaissement",
        "etat",
    )
    list_filter = ("exercice", "nature", "budget", "etat")
    search_fields = ("num_ordre", "debiteur", "num_decision")
    ordering = ("-exercice", "num_ordre")
