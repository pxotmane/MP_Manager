from django.urls import path
from . import views

# Add your URL patterns here from views.py
urlpatterns = [
    path('index', views.index, name='index'),
    path('tresorerie', views.tresorerie, name='tresorerie'),
    path('budget', views.budget, name='budget')
]