"""
Context processors — injecte les données globales dans tous les templates.
"""
from django.conf import settings


def user_roles(request):
    """Injecte les rôles et infos user dans tous les templates."""
    roles = []
    if request.user.is_authenticated:
        roles = request.session.get('user_roles', [])
    return {
        'user_roles': roles,
        'is_admin': 'ADMIN' in roles,
        'is_manager': 'MANAGER' in roles,
        'is_auditor': 'AUDITOR' in roles,
        'app_name': 'Portail IAM SODEPA',
    }
