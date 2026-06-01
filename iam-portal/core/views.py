"""Vues principales : home, dashboard, app launcher."""
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from core.keycloak_client import keycloak


def home(request):
    """Page d'accueil / landing. Redirige si déjà connecté."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """Tableau de bord principal."""
    # Récupérer les rôles depuis la session
    user_roles = request.session.get('user_roles', [])

    # Stats rapides pour le dashboard
    stats = {}
    if 'ADMIN' in user_roles or 'MANAGER' in user_roles:
        try:
            users = keycloak.list_users(max=1000)
            stats['total_users'] = len(users)
            stats['active_users'] = sum(1 for u in users if u.get('enabled'))
        except Exception:
            stats['total_users'] = '—'
            stats['active_users'] = '—'

    # Apps accessibles à cet utilisateur
    apps = _get_user_apps(user_roles)
    stats['total_apps'] = len(apps)

    # Derniers événements (aperçu)
    recent_events = []
    if 'ADMIN' in user_roles or 'AUDITOR' in user_roles:
        try:
            recent_events = keycloak.get_events(max=5)
            user_map = {
                ev['userId']: ev['details']['username']
                for ev in recent_events
                if ev.get('userId') and ev.get('details', {}).get('username')
            }
            for ev in recent_events:
                if 'time' in ev:
                    ev['time_formatted'] = datetime.fromtimestamp(
                        ev['time'] / 1000).strftime('%d/%m/%Y %H:%M:%S')
                username = (ev.get('details', {}).get('username')
                            or user_map.get(ev.get('userId', ''), ''))
                ev['display_user'] = username or ev.get('userId', '?')
                ev['display_initials'] = (username[:2] if username else ev.get('userId', '??')[:2]).upper()
        except Exception as e:
            messages.error(request, f"Impossible de charger les événements : {e}")

    context = {
        'stats': stats,
        'apps': apps[:6],  # 6 apps max sur le dashboard
        'recent_events': recent_events,
        'user_roles': user_roles,
    }
    return render(request, 'dashboard.html', context)


@login_required
def launcher(request):
    """Page App Launcher — toutes les applications accessibles."""
    user_roles = request.session.get('user_roles', [])
    apps = _get_user_apps(user_roles)

    # Grouper par catégorie
    categories = {}
    for app in apps:
        cat = app.get('category', 'Autres')
        categories.setdefault(cat, []).append(app)

    return render(request, 'launcher.html', {
        'categories': categories,
        'apps': apps,
        'user_roles': user_roles,
    })


@login_required
def app_launch(request, app_id):
    """Lance une application via SSO Keycloak ou redirection directe."""
    user_roles = request.session.get('user_roles', [])
    apps = settings.IAM_APPLICATIONS
    app = next((a for a in apps if a['id'] == app_id), None)

    if not app:
        messages.error(request, "Application introuvable.")
        return redirect('launcher')

    if not any(r in user_roles for r in app.get('roles', [])):
        messages.error(request, "Accès refusé : droits insuffisants.")
        return redirect('launcher')

    # SSO : rediriger vers l'URL de login OIDC de l'application (pas Keycloak directement)
    # L'app génère son propre state → échange le code → pas d'erreur state mismatch
    target_url = app.get('sso_login_url') or app['url']
    return redirect(target_url)


def _get_user_apps(user_roles):
    """Filtre les applications selon les rôles de l'utilisateur."""
    all_apps = settings.IAM_APPLICATIONS
    if not user_roles:
        return []
    return [
        app for app in all_apps
        if any(role in user_roles for role in app.get('roles', []))
    ]
