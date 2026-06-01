# Portail IAM SODEPA

Interface de gouvernance IAM — Django 4.2 + Keycloak OIDC

## Démarrage rapide

```bash
# 1. Environnement virtuel
python3 -m venv venv && source venv/bin/activate

# 2. Dépendances
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env
# Éditer .env avec vos valeurs Keycloak

# 4. Base de données
python manage.py migrate

# 5. Lancement
python manage.py runserver 0.0.0.0:8000
```

## Ajouter une application au SI

Dans `iam_portal/settings.py`, ajouter un dict dans `IAM_APPLICATIONS` :

```python
{
    "id": "mon-app",           # identifiant unique slug
    "name": "Mon Application",
    "description": "Description courte",
    "url": "https://mon-app.sodepa.local",
    "icon": "🖥️",              # emoji ou caractère
    "color": "#6366f1",        # couleur hex de la carte
    "category": "Métier",      # catégorie dans le launcher
    "roles": ["USER", "MANAGER", "ADMIN"],  # rôles autorisés
    "sso": True,               # True = badge SSO affiché
},
```

## Configuration Keycloak requise

1. Créer client `portail-iam` (OIDC, confidential)
   - Redirect URIs : `https://portail.sodepa.local/oidc/callback/`
   - Scopes : `openid email profile`

2. Créer client `portail-iam-admin` (service account)
   - Service account roles : `realm-management > manage-users, view-users, manage-realm`

3. Ajouter mapper `realm roles` → claim `realm_access` dans le token

## Rôles supportés
| Rôle | Accès |
|------|-------|
| ADMIN | Tout (users, audit, launcher complet) |
| MANAGER | Users (lecture), launcher filtré |
| AUDITOR | Audit uniquement + launcher |
| USER | Launcher filtré uniquement |
