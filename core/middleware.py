# from django.shortcuts import redirect
# from django.urls import reverse


# class LoginRequiredMiddleware:
#     """
#     Middleware qui exige la connexion pour toutes les pages,
#     sauf pour les URLs explicites (comme la page de login).
#     """

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Liste des URLs accessibles sans connexion (ex: login, assets statiques)
#         exempt_urls = [
#             reverse("login"),
#             # Ajoutez ici d'autres URLs publiques si besoin (ex: reverse('signup'))
#         ]

#         if not request.user.is_authenticated and request.path not in exempt_urls:
#             # Empêche aussi la boucle si l'URL statique/media est demandée
#             if not request.path.startswith("/static/") and not request.path.startswith(
#                 "/media/"
#             ):
#                 return redirect(f"{reverse('login')}?next={request.path}")

#         response = self.get_response(request)
#         return response


from django.shortcuts import redirect
from django.urls import reverse

# class LoginRequiredMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # 1. On laisse passer la requête si l'utilisateur est connecté
#         if request.user.is_authenticated:
#             return self.get_response(request)

#         # 2. Si non connecté, on vérifie si l'URL demandée fait partie des exceptions
#         path = request.path
#         if (
#             path == reverse("login")
#             or path.startswith("/password_reset/")
#             or path.startswith("/reset/")
#             or path.startswith("/static/")
#             or path.startswith("/media/")
#         ):
#             # C'est une URL publique, on laisse passer
#             return self.get_response(request)

#         # 3. Sinon, on bloque et on renvoie vers le login
#         return redirect(f"{reverse('login')}?next={path}")


from django.conf import settings
# [AUDIT PHASE 1] Import pour valider que l'URL 'next' appartient bien à notre site (évite l'Open Redirect)
from django.utils.http import url_has_allowed_host_and_scheme

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        # [AUDIT PHASE 1] Ciblage EXACT des URLs publiques pour éviter de laisser passer de fausses routes (ex: /login_bypass/)
        public_paths = {reverse("login"), "/password_reset/", "/reset/"}
        
        # Et les préfixes stricts pour les fichiers statiques/média
        public_prefixes = ["/static/", "/media/"]

        if request.path in public_paths or any(request.path.startswith(p) for p in public_prefixes):
            return self.get_response(request)

        # Sinon, on bloque et on redirige vers le login avec validation de ?next=
        # [AUDIT PHASE 1] Vérification stricte du paramètre next_url (fallback sur "/" si l'URL est invalide)
        next_url = request.path if url_has_allowed_host_and_scheme(
            url=request.path, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ) else "/"
        
        # [AUDIT PHASE 1] Redirection propre en utilisant reverse('login') pour éviter le problème d'URL relative
        return redirect(f"{reverse('login')}?next={next_url}")
