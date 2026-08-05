from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# from django.http import HttpResponse

# # Create your views here.
# def index(request):
#     return HttpResponse("Hello, World!")

# def tresorerie(request):
#     return HttpResponse("C'est la page de trésorerie.")

@login_required
def index(request):
    context = {
        'title': 'Tableau de bord',
        'elements': ['Element 1', 'Element 2', 'Element 3'],
    }
    return render(request, 'pages/index.html', context)

@login_required
def tresorerie(request):
    context = {
        'title': 'Gestion de la trésorerie',
    }
    return render(request, 'pages/tresorerie.html', context)

@login_required
def budget(request):
    context = {
        'title': 'Budget',
    }
    return render(request, 'pages/budget.html', context)

