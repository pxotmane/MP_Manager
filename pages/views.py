from django.shortcuts import render
# from django.http import HttpResponse

# # Create your views here.
# def index(request):
#     return HttpResponse("Hello, World!")

# def tresorerie(request):
#     return HttpResponse("C'est la page de trésorerie.")

def index(request):
    context = {
        'title': 'Tableau de bord',
        'elements': ['Element 1', 'Element 2', 'Element 3'],
    }
    return render(request, 'pages/index.html', context)

def tresorerie(request):
    context = {
        'title': 'Gestion de la trésorerie',
    }
    return render(request, 'pages/tresorerie.html', context)

def budget(request):
    context = {
        'title': 'Budget',
    }
    return render(request, 'pages/budget.html', context)

