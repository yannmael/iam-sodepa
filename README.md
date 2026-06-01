# Portail IAM SODEPA — Documentation Technique

> Portail de gestion des identités et des accès (IAM) développé pour la SODEPA.  
> Authentification centralisée via Keycloak (OpenID Connect), contrôle d'accès par rôles, journal d'audit.

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture](#2-architecture)
3. [Stack technique](#3-stack-technique)
4. [Structure du projet](#4-structure-du-projet)
5. [Prérequis](#5-prérequis)
6. [Installation et configuration](#6-installation-et-configuration)
7. [Configuration Keycloak](#7-configuration-keycloak)
8. [Variables d'environnement](#8-variables-denvironnement)
9. [Flux d'authentification OIDC](#9-flux-dauthentification-oidc)
10. [Contrôle d'accès par rôles (RBAC)](#10-contrôle-daccès-par-rôles-rbac)
11. [Modèles de données](#11-modèles-de-données)
12. [API et endpoints](#12-api-et-endpoints)
13. [Composants backend](#13-composants-backend)
14. [Templates et design system](#14-templates-et-design-system)
15. [Système d'audit](#15-système-daudit)
16. [Intégration des applications SSO](#16-intégration-des-applications-sso)
17. [Déploiement](#17-déploiement)
18. [Sécurité et conformité](#18-sécurité-et-conformité)

---

## 1. Vue d'ensemble

Le Portail IAM SODEPA est une application web Django qui centralise :

- **L'authentification SSO** de tous les utilisateurs via Keycloak (OpenID Connect)
- **Le contrôle d'accès** basé sur des rôles définis dans Keycloak
- **Le lanceur d'applications** : accès en un clic aux applications du SI via SSO
- **La gestion des utilisateurs** : création, modification, désactivation via l'API Admin Keycloak
- **L'audit complet** : journalisation des événements Keycloak et des actions administratives du portail

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Navigateur utilisateur                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
          ┌──────────────▼──────────────┐
          │      Portail IAM Django      │
          │    (192.168.56.50:8000)      │
          │                             │
          │  ┌─────────┐ ┌───────────┐  │
          │  │  core   │ │   users   │  │
          │  │  audit  │ │ templates │  │
          └──┴────┬────┴─┴─────┬─────┘──┘
                  │             │
        OIDC/REST │             │ Admin API
                  ▼             ▼
          ┌───────────────────────────┐
          │         Keycloak          │
          │  keycloak.sodepa.local    │
          │        :8080              │
          │                           │
          │  Realm : sodepa           │
          │  Clients : portail-iam    │
          │            portail-iam-admin│
          │            nextcloud      │
          └─────────────┬─────────────┘
                        │ SSO (OIDC)
            ┌───────────┼───────────┐
            ▼           ▼           ▼
        MyCow       Nextcloud    AWS Console
```

### Flux de données

```
Utilisateur → Portail → Keycloak (auth) → Token JWT → Session Django
                  ↓
            App Launcher → redirect vers app → Keycloak (SSO) → App connectée
                  ↓
            Admin API → Keycloak Admin → CRUD utilisateurs
                  ↓
            AuditLog → SQLite (actions portail) + Keycloak Events API
```

---

## 3. Stack technique

| Composant | Technologie | Version |
|---|---|---|
| Backend | Python / Django | 4.2 |
| Authentification | mozilla-django-oidc | 4.x |
| Identity Provider | Keycloak | 21+ |
| Base de données | SQLite (dev) / PostgreSQL (prod) |  |
| Fichiers statiques | WhiteNoise | 6.x |
| Frontend | HTML/CSS vanilla + SVG inline | — |
| Typographie | Roboto + Roboto Mono (Google Fonts) | — |
| Déploiement | Gunicorn + Nginx (prod) | — |

---

## 4. Structure du projet

```
iam-portal/
├── manage.py
├── .env                          # Variables d'environnement (non versionné)
├── requirements.txt
│
├── iam_portal/                   # Configuration Django principale
│   ├── settings.py               # Paramètres : DB, OIDC, apps, sécurité
│   ├── urls.py                   # Routage principal
│   └── wsgi.py
│
├── core/                         # Module central
│   ├── backends.py               # Backend OIDC personnalisé (rôles Keycloak → session)
│   ├── context_processors.py     # Injection globale : user_roles, is_admin, etc.
│   ├── decorators.py             # @role_required(*roles)
│   ├── keycloak_client.py        # Client API Admin Keycloak (singleton)
│   ├── models.py                 # AuditLog : journal des actions portail
│   ├── urls.py                   # Routes : home, dashboard, launcher, app_launch
│   └── views.py                  # Vues : home, dashboard, launcher, app_launch
│
├── users/                        # Module gestion des utilisateurs
│   ├── urls.py                   # Routes CRUD utilisateurs
│   └── views.py                  # Vues : list, create, edit, delete
│
├── audit/                        # Module journal d'audit
│   ├── urls.py                   # Routes : dashboard, export CSV
│   └── views.py                  # Fusion events Keycloak + logs portail
│
└── templates/                    # Templates HTML
    ├── base.html                 # Layout minimal (head + blocks)
    ├── home.html                 # Page de connexion
    ├── dashboard.html            # Tableau de bord
    ├── launcher.html             # Lanceur d'applications
    ├── users/
    │   ├── list.html
    │   ├── create.html
    │   └── edit.html
    └── audit/
        └── dashboard.html
```

---

## 5. Prérequis

### Logiciels requis

- Python 3.10+
- Keycloak 21+ (accessible sur le réseau)
- Git

### Keycloak — Clients nécessaires

| Client ID | Usage | Type |
|---|---|---|
| `portail-iam` | Authentification utilisateurs (OIDC) | Confidential |
| `portail-iam-admin` | API Admin (gestion utilisateurs) | Service Account |

---

## 6. Installation et configuration

### 6.1 Cloner le projet

```bash
git clone https://github.com/yannmael/iam-sodepa.git
cd iam-sodepa/iam-portal
```

### 6.2 Environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6.3 Variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos valeurs (voir section 8)
nano .env
```

### 6.4 Base de données

```bash
python manage.py migrate
```

### 6.5 Lancement en développement

```bash
python manage.py runserver 0.0.0.0:8000
```

---

## 7. Configuration Keycloak

### 7.1 Client `portail-iam` (authentification utilisateurs)

| Paramètre | Valeur |
|---|---|
| Client ID | `portail-iam` |
| Client authentication | ON (Confidential) |
| Valid redirect URIs | `http://<IP>:8000/oidc/callback/*` |
| Web origins | `http://<IP>:8000` |

**Mappers requis :**
- `realm roles` → type `User Realm Role` → Token Claim Name : `realm_access`

### 7.2 Client `portail-iam-admin` (API Admin)

| Paramètre | Valeur |
|---|---|
| Client ID | `portail-iam-admin` |
| Service accounts enabled | ON |

**Rôles Service Account (realm-management) :**
- `manage-users`
- `view-users`
- `view-events`

### 7.3 Rôles du realm `sodepa`

| Rôle | Description | Accès portail |
|---|---|---|
| `ADMIN` | Administrateur complet | Toutes les pages |
| `MANAGER` | Gestionnaire | Dashboard, Utilisateurs |
| `USER` | Utilisateur standard | Dashboard, Applications |
| `AUDITOR` | Auditeur | Dashboard, Audit |

### 7.4 Journalisation des événements

`Realm Settings → Events → User events settings` :
- Save events : **ON**
- Expiration : **90 Days**
- Types sauvegardés : `Login`, `Login error`, `Logout`, `Code to token`, `Update password`, `Register`

---

## 8. Variables d'environnement

Fichier `.env` à la racine du projet Django :

```env
# Django
SECRET_KEY=votre-clé-secrète-longue-et-aléatoire
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.56.50
CSRF_TRUSTED_ORIGINS=http://192.168.56.50:8000

# Keycloak
KEYCLOAK_URL=http://keycloak.sodepa.local:8080
KEYCLOAK_REALM=sodepa

# Client OIDC (authentification utilisateurs)
KEYCLOAK_CLIENT_ID=portail-iam
KEYCLOAK_CLIENT_SECRET=<secret-depuis-keycloak-credentials>

# Client Admin (API gestion utilisateurs)
KEYCLOAK_ADMIN_CLIENT_ID=portail-iam-admin
KEYCLOAK_ADMIN_CLIENT_SECRET=<secret-depuis-keycloak-credentials>

# SSL (False en dev HTTP, True en prod HTTPS)
OIDC_VERIFY_SSL=False
```

---

## 9. Flux d'authentification OIDC

### 9.1 Connexion au portail

```
1. Utilisateur → GET /
2. Portail → redirect vers /oidc/authenticate/
3. Browser → redirect vers Keycloak /realms/sodepa/protocol/openid-connect/auth
4. Keycloak → formulaire de login (+ MFA si configuré)
5. Keycloak → redirect vers /oidc/callback/?code=XXX&state=YYY
6. Portail → échange code contre token (POST /token)
7. KeycloakOIDCBackend.get_or_create_user()
   → extrait realm_access.roles du JWT
   → stocke les rôles dans request.session['user_roles']
   → crée/met à jour le User Django
8. Portail → redirect vers /dashboard/
```

### 9.2 Backend OIDC personnalisé (`core/backends.py`)

Le backend étend `OIDCAuthenticationBackend` avec :

| Méthode | Rôle |
|---|---|
| `get_username(claims)` | Utilise `preferred_username` Keycloak comme username Django |
| `get_or_create_user()` | Extrait les rôles du JWT et les stocke en session |
| `_sync_user_profile()` | Synchronise `first_name`, `last_name`, `email`, `is_staff` |
| `get_userinfo()` | Fusionne `realm_access` depuis l'access token dans le userinfo |

### 9.3 Lancement d'application SSO (`core/views.py → app_launch`)

```
Utilisateur clique "Accéder" sur MyCow
→ GET /launch/mycow/
→ Vérification rôles utilisateur
→ redirect vers sso_login_url (ex: https://mycow.sodepa.local/oidc/login)
→ L'application déclenche son propre flux OIDC vers Keycloak
→ Keycloak utilise la session existante → SSO transparent
→ Utilisateur connecté à MyCow sans re-saisir ses identifiants
```

> **Important** : le portail redirige toujours vers l'URL OIDC de l'application (SP-initiated),
> jamais directement vers Keycloak. Cela évite les erreurs de state mismatch.

---

## 10. Contrôle d'accès par rôles (RBAC)

### 10.1 Décorateur `@role_required` (`core/decorators.py`)

```python
@login_required
@role_required('ADMIN', 'MANAGER')
def user_list(request):
    ...
```

Vérifie que `request.session['user_roles']` contient au moins un des rôles requis. Redirige vers le dashboard avec un message d'erreur si non autorisé.

### 10.2 Context processor (`core/context_processors.py`)

Injecté dans tous les templates via `settings.TEMPLATES` :

```python
# Disponible dans tous les templates
{{ user_roles }}    # liste : ['ADMIN', 'USER']
{{ is_admin }}      # booléen
{{ is_manager }}    # booléen
{{ is_auditor }}    # booléen
```

### 10.3 Matrice d'accès

| Page / Action | ADMIN | MANAGER | USER | AUDITOR |
|---|:---:|:---:|:---:|:---:|
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| App Launcher | ✓ | ✓ | ✓ | ✓ |
| Gestion utilisateurs | ✓ | ✓ | — | — |
| Créer/modifier/supprimer user | ✓ | — | — | — |
| Journal d'audit | ✓ | — | — | ✓ |
| Export CSV audit | ✓ | — | — | ✓ |

---

## 11. Modèles de données

### 11.1 `AuditLog` (`core/models.py`)

Trace locale des actions administratives effectuées via le portail.

| Champ | Type | Description |
|---|---|---|
| `action` | CharField | `USER_CREATE`, `USER_UPDATE`, `USER_DELETE`, `ROLE_ASSIGN`, `ROLE_REMOVE`, `APP_ACCESS` |
| `operator` | CharField | Nom complet ou email de l'administrateur |
| `target` | CharField | Username ou ID de l'utilisateur cible |
| `details` | TextField | Informations complémentaires (rôle assigné, email, etc.) |
| `ip_address` | GenericIPAddressField | IP source de l'action |
| `timestamp` | DateTimeField | Horodatage automatique (auto_now_add) |

> Les événements Keycloak (LOGIN, LOGOUT, etc.) sont récupérés via l'API Admin et ne sont pas stockés localement.

---

## 12. API et endpoints

### 12.1 Routes Django

| URL | Nom | Vue | Accès |
|---|---|---|---|
| `/` | `home` | `core.views.home` | Public |
| `/dashboard/` | `dashboard` | `core.views.dashboard` | Authentifié |
| `/launcher/` | `launcher` | `core.views.launcher` | Authentifié |
| `/launch/<app_id>/` | `app_launch` | `core.views.app_launch` | Authentifié |
| `/users/` | `user_list` | `users.views.user_list` | ADMIN, MANAGER |
| `/users/creer/` | `user_create` | `users.views.user_create` | ADMIN |
| `/users/<id>/modifier/` | `user_edit` | `users.views.user_edit` | ADMIN |
| `/users/<id>/supprimer/` | `user_delete` | `users.views.user_delete` | ADMIN |
| `/audit/` | `audit_dashboard` | `audit.views.audit_dashboard` | ADMIN, AUDITOR |
| `/audit/export/` | `audit_export` | `audit.views.export_csv` | ADMIN, AUDITOR |
| `/oidc/authenticate/` | `oidc_authentication_init` | mozilla-django-oidc | Public |
| `/oidc/callback/` | `oidc_authentication_callback` | mozilla-django-oidc | Public |
| `/oidc/logout/` | `oidc_logout` | mozilla-django-oidc | POST requis |

### 12.2 Paramètres de filtre — Page Audit

| Paramètre GET | Valeurs | Description |
|---|---|---|
| `source` | `all`, `keycloak`, `portal` | Filtrer par source |
| `type` | `LOGIN`, `LOGOUT`, `USER_CREATE`, etc. | Filtrer par type d'événement |
| `user` | string | Filtrer par nom d'utilisateur |
| `app` | `nextcloud`, `mycow`, etc. | Filtrer par application (Keycloak clientId) |

---

## 13. Composants backend

### 13.1 `KeycloakClient` (`core/keycloak_client.py`)

Singleton (`keycloak = KeycloakClient()`) — client pour l'API Admin Keycloak avec gestion automatique du token (client credentials grant, renouvellement avant expiration).

| Méthode | Description |
|---|---|
| `get_admin_token()` | Obtient/renouvelle le token d'administration |
| `list_users(search, max)` | Liste les utilisateurs du realm |
| `get_user(user_id)` | Récupère un utilisateur par ID |
| `create_user(...)` | Crée un utilisateur avec mot de passe temporaire |
| `update_user(user_id, **kwargs)` | Met à jour les attributs d'un utilisateur |
| `delete_user(user_id)` | Supprime un utilisateur |
| `get_user_roles(user_id)` | Récupère les rôles realm d'un utilisateur |
| `get_user_sessions(user_id)` | Récupère les sessions actives d'un utilisateur |
| `assign_role(user_id, role_name)` | Assigne un rôle realm |
| `remove_role(user_id, role_name)` | Retire un rôle realm |
| `get_events(type, user, client, max)` | Récupère les événements d'authentification |
| `get_admin_events(max)` | Récupère les événements d'administration |

### 13.2 Applications déclarées (`settings.IAM_APPLICATIONS`)

Chaque application est un dictionnaire avec les clés :

```python
{
    "id": str,           # Identifiant unique
    "name": str,         # Nom affiché
    "description": str,  # Description courte
    "url": str,          # URL de l'application
    "icon": str,         # Emoji ou caractère
    "color": str,        # Couleur hex pour l'UI
    "category": str,     # Catégorie (Métier, Cloud, Collaboration...)
    "roles": list,       # Rôles autorisés à accéder
    "sso": bool,         # SSO Keycloak activé
    "sso_client_id": str,    # Client ID Keycloak (optionnel)
    "sso_login_url": str,    # URL OIDC login SP (optionnel, remplace url)
}
```

---

## 14. Templates et design system

### 14.1 Architecture des templates

`base.html` est un layout minimal (head + `{% block extra_head %}` + `{% block content %}`).  
Chaque template enfant inclut sa propre sidebar avec navigation et bouton de déconnexion.

### 14.2 Design system

| Variable CSS | Valeur | Usage |
|---|---|---|
| `--navy` | `#0A1828` | Sidebar, titres principaux |
| `--teal` | `#178582` | Accent, boutons primaires, éléments actifs |
| `--gold` | `#BFA181` | Badges de rôle |
| `--bg` | `#f2f5f9` | Fond de page |
| `--white` | `#ffffff` | Cartes, topbar |
| `--text` | `#1a2940` | Texte principal |
| `--muted` | `#6b7a99` | Texte secondaire, labels |
| `--border` | `#e4e9f2` | Bordures |

**Typographie** : `Roboto` (corps) + `Roboto Mono` (valeurs numériques, badges événements)

### 14.3 Variables de contexte disponibles dans tous les templates

Fournies par le context processor `core.context_processors.user_roles` :

```
user_roles   → list des rôles Keycloak de l'utilisateur connecté
is_admin     → bool
is_manager   → bool
is_auditor   → bool
app_name     → "Portail IAM SODEPA"
```

---

## 15. Système d'audit

L'audit est alimenté par deux sources fusionnées et triées par date :

### 15.1 Events Keycloak (authentification)

Récupérés via `GET /admin/realms/{realm}/events` avec filtres optionnels (`type`, `user`, `client`).

Champs clés : `type`, `userId`, `ipAddress`, `time` (epoch ms), `details.username`, `clientId`

### 15.2 Logs portail Django (actions admin)

Écrits dans `AuditLog` à chaque action CRUD via la fonction `_log()` dans `users/views.py`.

```python
_log(request, 'USER_CREATE', target='jean.dupont', details='Rôle: USER | Email: ...')
```

### 15.3 Export CSV

`GET /audit/export/` → fichier CSV UTF-8 BOM (compatible Excel) avec colonnes :  
`Date/Heure | Source | Type | Opérateur | Cible/App | IP | Détails`

---

## 16. Intégration des applications SSO

### Ajouter une nouvelle application

1. **Dans Keycloak** : créer un nouveau client OIDC avec `Valid redirect URIs` pointant vers l'app
2. **Dans `settings.py`** : ajouter l'entrée dans `IAM_APPLICATIONS`
3. **Dans l'application** : configurer le provider OIDC avec les endpoints Keycloak

### Exemple — Nextcloud

```python
{
    "id": "nextcloud",
    "name": "Nextcloud",
    "url": "https://nextcloud.sodepa.local",
    "icon": "📁",
    "color": "#3b82f6",
    "category": "Collaboration",
    "roles": ["USER", "MANAGER", "ADMIN", "AUDITOR"],
    "sso": True,
    "sso_client_id": "nextcloud",
    "sso_login_url": "https://nextcloud.sodepa.local/index.php/apps/user_oidc/login/1",
}
```

> L'ID dans `sso_login_url` (`/login/1`) correspond à l'ID du provider OIDC dans la table  
> `oc_user_oidc_providers` de Nextcloud.

---

## 17. Déploiement

### 17.1 Variables à changer pour la production

```env
DEBUG=False
SECRET_KEY=<clé-cryptographiquement-aléatoire-64-chars>
ALLOWED_HOSTS=portail.sodepa.cm
CSRF_TRUSTED_ORIGINS=https://portail.sodepa.cm
OIDC_VERIFY_SSL=True
```

### 17.2 Base de données PostgreSQL (recommandé en prod)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'iam_portal',
        'USER': 'iam_user',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',
    }
}
```

### 17.3 Gunicorn + Nginx

```bash
# Gunicorn
gunicorn iam_portal.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 4 \
  --timeout 60
```

```nginx
# Nginx
server {
    listen 443 ssl;
    server_name portail.sodepa.cm;

    location /static/ {
        alias /opt/iam-portal/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 17.4 Collecte des fichiers statiques

```bash
python manage.py collectstatic --noinput
```

---

## 18. Sécurité et conformité

### 18.1 Mesures implémentées

| Mesure | Implémentation |
|---|---|
| Authentification SSO | OpenID Connect via Keycloak |
| Sessions sécurisées | `SESSION_COOKIE_AGE = 28800` (8h), `SESSION_SAVE_EVERY_REQUEST = True` |
| Protection CSRF | Django middleware + token dans tous les formulaires POST |
| Contrôle d'accès | RBAC via `@role_required` + vérification session |
| Déconnexion Keycloak | POST vers `oidc_logout` → end session Keycloak |
| Audit trail | Logs Keycloak + AuditLog Django |
| Tolérance décalage horloge | `OIDC_LEEWAY = 60` secondes |

### 18.2 Conformité ISO 27001 / NIST

| Contrôle | Standard | Implémentation |
|---|---|---|
| Journalisation des accès | ISO 27001 A.12.4 / NIST AU-2 | Events Keycloak (Login, Logout, Erreurs) |
| Traçabilité des actions admin | ISO 27001 A.12.4.3 | AuditLog Django + Admin events Keycloak |
| Gestion des identités | ISO 27001 A.9 | Keycloak realm + rôles RBAC |
| Authentification forte | NIST SP 800-63 | MFA via Keycloak (TOTP configurable) |
| Rétention des logs | ISO 27001 A.12.4.1 | 90 jours minimum (configurable Keycloak) |
| Séparation des privilèges | ISO 27001 A.9.2 | 4 rôles distincts (ADMIN/MANAGER/USER/AUDITOR) |

### 18.3 Points d'attention

- Ne jamais commiter le fichier `.env` (contient les secrets Keycloak)
- En production, utiliser HTTPS pour Keycloak et le portail
- Activer `OIDC_VERIFY_SSL=True` en production
- Changer le `SECRET_KEY` Django en production
- Limiter `ALLOWED_HOSTS` au domaine de production uniquement

---

## Auteur

Développé pour la **SODEPA** — Direction des Systèmes d'Information  
Dépôt : [github.com/yannmael/iam-sodepa](https://github.com/yannmael/iam-sodepa)
