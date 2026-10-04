from django.contrib import admin
from .models import Tresorerie, BudgetExercice


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
