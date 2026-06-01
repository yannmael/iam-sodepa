"""
Service d'abstraction de l'API Admin Keycloak.
Toutes les interactions avec Keycloak Admin passent par cette classe.
"""
import time
import requests
from django.conf import settings


class KeycloakClient:
    """Client pour l'API Admin Keycloak avec gestion automatique du token."""

    def __init__(self):
        self.base_url = settings.KEYCLOAK_URL
        self.realm = settings.KEYCLOAK_REALM
        self.admin_client_id = settings.KEYCLOAK_ADMIN_CLIENT_ID
        self.admin_client_secret = settings.KEYCLOAK_ADMIN_CLIENT_SECRET
        self._token = None
        self._token_expiry = 0

    def get_admin_token(self):
        """Obtient un token Admin via client credentials. Renouvelle si expiré."""
        if self._token and time.time() < self._token_expiry - 30:
            return self._token

        url = f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"
        resp = requests.post(url, data={
            'grant_type': 'client_credentials',
            'client_id': self.admin_client_id,
            'client_secret': self.admin_client_secret,
        }, verify=False, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self._token = data['access_token']
        self._token_expiry = time.time() + data.get('expires_in', 300)
        return self._token

    def _headers(self):
        return {'Authorization': f'Bearer {self.get_admin_token()}',
                'Content-Type': 'application/json'}

    def _admin_url(self, path=''):
        return f"{self.base_url}/admin/realms/{self.realm}{path}"

    # ── Utilisateurs ──────────────────────────────────────────────────────────

    def list_users(self, search='', max=100):
        """Liste tous les utilisateurs du realm."""
        params = {'max': max}
        if search:
            params['search'] = search
        resp = requests.get(self._admin_url('/users'), headers=self._headers(),
                            params=params, verify=False, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_user(self, user_id):
        """Récupère un utilisateur par son ID."""
        resp = requests.get(self._admin_url(f'/users/{user_id}'),
                            headers=self._headers(), verify=False, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def create_user(self, username, email, first_name, last_name, password, enabled=True):
        """Crée un utilisateur dans Keycloak."""
        payload = {
            'username': username,
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
            'enabled': enabled,
            'credentials': [{'type': 'password', 'value': password, 'temporary': True}],
        }
        resp = requests.post(self._admin_url('/users'), headers=self._headers(),
                             json=payload, verify=False, timeout=10)
        resp.raise_for_status()
        # Keycloak retourne 201 avec Location header contenant l'ID
        location = resp.headers.get('Location', '')
        return location.split('/')[-1]

    def update_user(self, user_id, **kwargs):
        """Met à jour les attributs d'un utilisateur."""
        # Mapper les kwargs vers les champs Keycloak
        mapping = {
            'first_name': 'firstName',
            'last_name': 'lastName',
            'email': 'email',
            'enabled': 'enabled',
        }
        payload = {mapping.get(k, k): v for k, v in kwargs.items()}
        resp = requests.put(self._admin_url(f'/users/{user_id}'),
                            headers=self._headers(), json=payload,
                            verify=False, timeout=10)
        resp.raise_for_status()

    def delete_user(self, user_id):
        """Supprime un utilisateur."""
        resp = requests.delete(self._admin_url(f'/users/{user_id}'),
                               headers=self._headers(), verify=False, timeout=10)
        resp.raise_for_status()

    def reset_password(self, user_id, new_password, temporary=True):
        """Réinitialise le mot de passe d'un utilisateur."""
        payload = {'type': 'password', 'value': new_password, 'temporary': temporary}
        resp = requests.put(self._admin_url(f'/users/{user_id}/reset-password'),
                            headers=self._headers(), json=payload,
                            verify=False, timeout=10)
        resp.raise_for_status()

    # ── Rôles ─────────────────────────────────────────────────────────────────

    def list_realm_roles(self):
        """Liste tous les rôles du realm."""
        resp = requests.get(self._admin_url('/roles'), headers=self._headers(),
                            verify=False, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_user_roles(self, user_id):
        """Récupère les rôles realm d'un utilisateur."""
        resp = requests.get(
            self._admin_url(f'/users/{user_id}/role-mappings/realm'),
            headers=self._headers(), verify=False, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def assign_role(self, user_id, role_name):
        """Assigne un rôle realm à un utilisateur."""
        # D'abord récupérer l'objet rôle complet
        roles = self.list_realm_roles()
        role = next((r for r in roles if r['name'] == role_name), None)
        if not role:
            raise ValueError(f"Rôle '{role_name}' introuvable")
        resp = requests.post(
            self._admin_url(f'/users/{user_id}/role-mappings/realm'),
            headers=self._headers(), json=[role], verify=False, timeout=10)
        resp.raise_for_status()

    def remove_role(self, user_id, role_name):
        """Retire un rôle realm d'un utilisateur."""
        roles = self.list_realm_roles()
        role = next((r for r in roles if r['name'] == role_name), None)
        if not role:
            raise ValueError(f"Rôle '{role_name}' introuvable")
        resp = requests.delete(
            self._admin_url(f'/users/{user_id}/role-mappings/realm'),
            headers=self._headers(), json=[role], verify=False, timeout=10)
        resp.raise_for_status()

    def get_user_sessions(self, user_id):
        """Récupère les sessions actives d'un utilisateur."""
        resp = requests.get(
            self._admin_url(f'/users/{user_id}/sessions'),
            headers=self._headers(), verify=False, timeout=10)
        resp.raise_for_status()
        return resp.json()

    # ── Événements / Audit ───────────────────────────────────────────────────

    def get_events(self, event_type=None, user=None, client=None, max=100):
        """Récupère les événements d'authentification du realm."""
        params = {'max': max}
        if event_type:
            params['type'] = event_type
        if user:
            params['user'] = user
        if client:
            params['client'] = client
        resp = requests.get(self._admin_url('/events'), headers=self._headers(),
                            params=params, verify=False, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_admin_events(self, max=100):
        """Récupère les événements d'administration."""
        resp = requests.get(self._admin_url('/admin-events'),
                            headers=self._headers(),
                            params={'max': max}, verify=False, timeout=10)
        resp.raise_for_status()
        return resp.json()


# Instance singleton
keycloak = KeycloakClient()
