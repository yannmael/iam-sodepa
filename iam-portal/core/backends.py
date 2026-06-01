"""
Backend OIDC personnalisé.
Extrait les rôles Keycloak depuis le token et les stocke en session.
"""
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

APP_ROLES = ('ADMIN', 'MANAGER', 'USER', 'AUDITOR')


class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    """Étend le backend OIDC pour mapper les rôles Keycloak vers Django."""

    def get_or_create_user(self, access_token, id_token, payload):
        """Récupère/crée l'utilisateur et écrit ses rôles en session."""
        user = super().get_or_create_user(access_token, id_token, payload)
        if user and self.request:
            # payload = ID token décodé, contient realm_access si le mapper Keycloak est actif
            realm_access = payload.get('realm_access', {})
            roles = realm_access.get('roles', [])
            app_roles = [r for r in roles if r in APP_ROLES]
            self.request.session['user_roles'] = app_roles
        return user

    def create_user(self, claims):
        user = super().create_user(claims)
        self._sync_user_profile(user, claims)
        return user

    def update_user(self, user, claims):
        self._sync_user_profile(user, claims)
        return super().update_user(user, claims)

    def get_username(self, claims):
        """Utilise preferred_username Keycloak comme username Django."""
        return claims.get('preferred_username') or super().get_username(claims)

    def _sync_user_profile(self, user, claims):
        """Synchronise les attributs Django depuis les claims Keycloak."""
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.email = claims.get('email', '')
        realm_access = claims.get('realm_access', {})
        roles = realm_access.get('roles', [])
        # Élever les droits Django si rôle ADMIN
        if 'ADMIN' in roles:
            user.is_staff = True
        user.save()

    def get_userinfo(self, access_token, id_token, payload):
        """Fusionne le payload du token (realm_access) dans le userinfo."""
        info = super().get_userinfo(access_token, id_token, payload)
        # Keycloak met realm_access dans l'access token, pas toujours dans userinfo
        if payload:
            info.setdefault('realm_access', payload.get('realm_access', {}))
        return info
