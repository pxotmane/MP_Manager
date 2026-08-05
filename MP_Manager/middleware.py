from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    Middleware qui exige la connexion pour toutes les pages,
    sauf pour les URLs explicites (comme la page de login).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Liste des URLs accessibles sans connexion (ex: login, assets statiques)
        exempt_urls = [
            reverse('login'),
            # Ajoutez ici d'autres URLs publiques si besoin (ex: reverse('signup'))
        ]

        if not request.user.is_authenticated and request.path not in exempt_urls:
            # Empêche aussi la boucle si l'URL statique/media est demandée
            if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
                return redirect(f"{reverse('login')}?next={request.path}")

        response = self.get_response(request)
        return response