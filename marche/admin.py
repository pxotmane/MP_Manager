from django.contrib import admin
from .models import FicheMarche, Nantissement, Penalite
# Register your models here.
@admin.register(FicheMarche)
class FicheMarcheAdmin(admin.ModelAdmin):
    list_display = ('num_marche', 'objet', 'titulaire', 'montant_global_ttc')
    search_fields = ('num_marche','titulaire')
    list_filter = ('exercice_budgetaire', 'type_marche')

@admin.register(Nantissement)
class NantissementAdmin(admin.ModelAdmin):
    list_display = ('num_acte', 'mtt_nant', 'entite_nant')
    search_fields = ('num_acte','entite_nant')
    list_filter = ('entite_nant', 'date_nant')

@admin.register(Penalite)
class PenaliteAdmin(admin.ModelAdmin):
    list_display = ('num_penalite', 'mtt_penalite', 'date_penalite')
    search_fields = ('num_penalite',)
    list_filter = ('num_penalite', 'mtt_penalite')
