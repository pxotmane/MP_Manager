from django.contrib import admin
from .models import FicheMarche, Nantissement, Penalite
# Register your models here.
@admin.register(FicheMarche)
class FicheMarcheAdmin(admin.ModelAdmin):
    list_display = ('num_marche', 'objet', 'titulaire','montant_global_ttc')
    search_fields = ('num_marche','titulaire')
    list_filter = ('exercice_budgetaire', 'type_marche')