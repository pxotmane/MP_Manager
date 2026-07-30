from django.urls import path
from . import views

urlpatterns = [
    path('tableau', views.tresorerie_table, name='tresorerie_table'),
]   
