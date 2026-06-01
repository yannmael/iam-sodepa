"""
Point d'entrée WSGI pour le portail IAM SODEPA.
Déploiement : gunicorn iam_portal.wsgi:application
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iam_portal.settings')

application = get_wsgi_application()
