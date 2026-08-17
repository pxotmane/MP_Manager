from django.contrib import admin
from .models import Tresorerie


@admin.register(Tresorerie)
class TresorerieAdmin(admin.ModelAdmin):
    list_display = ("op", "exercice", "budget", "nature", "montant")
    list_filter = ("exercice", "budget", "nature")
    search_fields = ("op", "beneficiaires")
