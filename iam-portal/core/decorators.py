"""Décorateurs de contrôle d'accès basés sur les rôles Keycloak."""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """Restreint l'accès aux utilisateurs ayant au moins un des rôles spécifiés."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            user_roles = request.session.get('user_roles', [])
            if not any(r in user_roles for r in roles):
                messages.error(request, "Accès refusé : droits insuffisants.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
