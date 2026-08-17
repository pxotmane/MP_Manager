from django.shortcuts import render
from .models import FicheMarche, Nantissement, Penalite


# Create your views here.
def marche_table(request):
    # # Fetch all FicheMarche objects from the database
    marches = FicheMarche.objects.all()

    # # Pass the fetched data to the template
    # context = {
    #     'marches': marches,
    # }

    return render(request, "marche/tableau_marche.html", {"marches": marches})
