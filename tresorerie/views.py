from django.shortcuts import render
from .models import Tresorerie

# Create your views here.
# Call the template created in the templates folder to display the table of the Tresorerie model
def tresorerie_table(request): 
    tresorerie_list = Tresorerie.objects.all()
    return render(request, 'tr_tableau/tresorerie_table.html', {'tresorerie_list': tresorerie_list})
    # Just comment for one object:
    # return render(request, 'tr_tableau/tresorerie_table.html', {'tresorerie': tresorerie_list[0]})
    #OR
    # return render(request, 'tr_tableau/tresorerie_table.html', {'tresorerie': Tresorerie.objects.first()})
    #OR
    # return render(request, 'tr_tableau/tresorerie_table.html', {'tresorerie': Tresorerie.objects.get(id=1)}) this which i want