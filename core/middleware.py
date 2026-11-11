from django.shortcuts import redirect
from django.urls import reverse
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
