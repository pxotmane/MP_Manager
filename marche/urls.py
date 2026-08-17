from django.urls import path
from . import views

urlpatterns = [
    # path('fiche_marche', views.marche_table, name='fiche_marche'),
    path("tableau_marche", views.marche_table, name="tableau_marche"),
]
