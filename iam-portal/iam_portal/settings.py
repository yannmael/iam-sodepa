import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-changez-en-prod')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

WSGI_APPLICATION = 'iam_portal.wsgi.application'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mozilla_django_oidc',
    'crispy_forms',
    'crispy_bootstrap5',
    'core',
    'users',
    'audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mozilla_django_oidc.middleware.SessionRefresh',
]

ROOT_URLCONF = 'iam_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_roles',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Keycloak OIDC
KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://keycloak.sodepa.local:8080')
KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', 'sodepa')
KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID', 'portail-iam')
KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET', '')
KEYCLOAK_ADMIN_CLIENT_ID = os.getenv('KEYCLOAK_ADMIN_CLIENT_ID', 'portail-iam-admin')
KEYCLOAK_ADMIN_CLIENT_SECRET = os.getenv('KEYCLOAK_ADMIN_CLIENT_SECRET', '')

_BASE = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect"
OIDC_RP_CLIENT_ID = KEYCLOAK_CLIENT_ID
OIDC_RP_CLIENT_SECRET = KEYCLOAK_CLIENT_SECRET
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{_BASE}/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{_BASE}/token"
OIDC_OP_USER_ENDPOINT = f"{_BASE}/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{_BASE}/certs"
OIDC_OP_LOGOUT_ENDPOINT = f"{_BASE}/logout"
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_STORE_ACCESS_TOKEN = True
OIDC_STORE_ID_TOKEN = True
OIDC_AUTHENTICATION_CALLBACK_URL = 'oidc_authentication_callback'
# Désactiver la vérification SSL en développement (Keycloak HTTP local)
OIDC_VERIFY_SSL = os.getenv('OIDC_VERIFY_SSL', 'False') == 'True'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/oidc/authenticate/'
# Scopes OIDC — roles Keycloak inclus via le mapper "realm roles"
OIDC_RP_SCOPES = 'openid email profile'

AUTHENTICATION_BACKENDS = [
    'core.backends.KeycloakOIDCBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Applications du SI — MODIFIER ICI pour ajouter vos apps
IAM_APPLICATIONS = [
    {
        "id": "mycow",
        "name": "MyCow",
        "description": "Application métier d'élevage SODEPA",
        "url": "https://mycow.sodepa.local",
        "icon": "🐄",
        "color": "#10b981",
        "category": "Métier",
        "roles": ["USER", "MANAGER", "ADMIN"],
        "sso": True,
        "sso_client_id": "mycow",  # Client ID dans Keycloak
    },
    {
        "id": "aws",
        "name": "AWS Console",
        "description": "Services Cloud Amazon Web Services",
        "url": "https://sodepa.awsapps.com/start",
        "icon": "☁️",
        "color": "#f59e0b",
        "category": "Cloud",
        "roles": ["ADMIN", "MANAGER"],
        "sso": False,  # AWS utilise son propre fédération, pas OIDC Keycloak
    },
    {
        "id": "nextcloud",
        "name": "Nextcloud",
        "description": "Gestion documentaire et collaboration",
        "url": "https://nextcloud.sodepa.local",
        "icon": "📁",
        "color": "#3b82f6",
        "category": "Collaboration",
        "roles": ["USER", "MANAGER", "ADMIN", "AUDITOR"],
        "sso": True,
        "sso_client_id": "nextcloud",
        # URL de login OIDC Nextcloud — remplacer {id} par l'ID du provider (occ user_oidc:provider --list)
        "sso_login_url": "https://nextcloud.sodepa.local/index.php/apps/user_oidc/login/1",
    },
]

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Inclure le dossier static/ uniquement s'il existe (évite crash WhiteNoise en CI)
_STATIC_DIR = BASE_DIR / 'static'
STATICFILES_DIRS = [_STATIC_DIR] if _STATIC_DIR.exists() else []
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True

SESSION_COOKIE_AGE = 28800  # 8 heures
SESSION_SAVE_EVERY_REQUEST = True
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')

# Tolérance décalage horloge entre Django et Keycloak (en secondes)
OIDC_LEEWAY = 60
