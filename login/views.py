from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from .forms import LoginForm

class LoginUser(LoginView):
    form_class = LoginForm
    template_name = "login/login.html"
    redirect_authenticated_user = True


class LogoutUser(LogoutView):
    pass

# Create your views here.
