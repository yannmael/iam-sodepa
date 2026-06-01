"""Gestion des utilisateurs via Keycloak Admin API."""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.keycloak_client import keycloak
from core.decorators import role_required
from core.models import AuditLog


def _log(request, action, target='', details=''):
    operator = (request.user.get_full_name()
                or request.user.email
                or request.user.username)
    AuditLog.objects.create(
        action=action,
        operator=operator,
        target=target,
        details=details,
        ip_address=request.META.get('REMOTE_ADDR'),
    )


SODEPA_ROLES = ['USER', 'MANAGER', 'ADMIN', 'AUDITOR']


@login_required
@role_required('ADMIN', 'MANAGER')
def user_list(request):
    """Liste de tous les utilisateurs."""
    search = request.GET.get('q', '')
    try:
        users = keycloak.list_users(search=search)
        # Ajouter les rôles à chaque utilisateur
        for user in users:
            try:
                roles = keycloak.get_user_roles(user['id'])
                user['app_roles'] = [r['name'] for r in roles if r['name'] in SODEPA_ROLES]
            except Exception:
                user['app_roles'] = []
            try:
                sessions = keycloak.get_user_sessions(user['id'])
                user['session_count'] = len(sessions)
            except Exception:
                user['session_count'] = 0
    except Exception as e:
        messages.error(request, f"Erreur Keycloak : {e}")
        users = []

    return render(request, 'users/list.html', {
        'users': users,
        'search': search,
        'total': len(users),
    })


@login_required
@role_required('ADMIN')
def user_create(request):
    """Création d'un nouvel utilisateur."""
    if request.method == 'POST':
        try:
            user_id = keycloak.create_user(
                username=request.POST['username'],
                email=request.POST['email'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                password=request.POST['password'],
            )
            # Assigner le rôle sélectionné
            role = request.POST.get('role', 'USER')
            if role in SODEPA_ROLES:
                keycloak.assign_role(user_id, role)
            _log(request, 'USER_CREATE', request.POST['username'],
                 f"Rôle: {role} | Email: {request.POST['email']}")
            messages.success(request, f"Utilisateur {request.POST['username']} créé.")
            return redirect('user_list')
        except Exception as e:
            messages.error(request, f"Erreur : {e}")

    return render(request, 'users/create.html', {'roles': SODEPA_ROLES})


@login_required
@role_required('ADMIN')
def user_edit(request, user_id):
    """Modification d'un utilisateur."""
    try:
        user = keycloak.get_user(user_id)
        current_roles = [r['name'] for r in keycloak.get_user_roles(user_id)
                         if r['name'] in SODEPA_ROLES]
    except Exception as e:
        messages.error(request, f"Utilisateur introuvable : {e}")
        return redirect('user_list')

    if request.method == 'POST':
        try:
            keycloak.update_user(user_id,
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email'],
                enabled=request.POST.get('enabled') == 'true',
            )
            # Mettre à jour le rôle
            new_role = request.POST.get('role')
            if new_role and new_role in SODEPA_ROLES:
                for old_role in current_roles:
                    keycloak.remove_role(user_id, old_role)
                keycloak.assign_role(user_id, new_role)
            _log(request, 'USER_UPDATE', user.get('username', user_id),
                 f"Rôle: {new_role} | Email: {request.POST.get('email', '')}")
            messages.success(request, "Utilisateur mis à jour.")
            return redirect('user_list')
        except Exception as e:
            messages.error(request, f"Erreur : {e}")

    return render(request, 'users/edit.html', {
        'user': user,
        'current_roles': current_roles,
        'roles': SODEPA_ROLES,
    })


@login_required
@role_required('ADMIN')
def user_delete(request, user_id):
    """Suppression d'un utilisateur (confirmation requise)."""
    if request.method == 'POST':
        try:
            user = keycloak.get_user(user_id)
            username = user.get('username', user_id)
            keycloak.delete_user(user_id)
            _log(request, 'USER_DELETE', username)
            messages.success(request, "Utilisateur supprimé.")
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    return redirect('user_list')
