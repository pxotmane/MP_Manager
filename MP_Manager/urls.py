"""
URL configuration for MP_Manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Authentification
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    # logout: redirect to the login page after logout
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Password reset views
    path(
        "password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"
    ),
    # Password reset done view
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    # Password reset confirm view
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # Password reset complete view
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("", include("pages.urls")),  # Include the URLs from the 'pages' app
    path(
        "TR/", include("tresorerie.urls")
    ),  # Include the URLs from the 'tresorerie' app
    path("marche/", include("marche.urls")),  # Include the URLs from the 'marche' app
    # path('', include('login.urls')), # Include the URLs from the 'login' app
]
