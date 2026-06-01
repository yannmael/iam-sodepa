"""Dashboard d'audit — logs Keycloak + actions portail."""
import csv
from datetime import datetime, timezone
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from core.keycloak_client import keycloak
from core.decorators import role_required
from core.models import AuditLog


@login_required
@role_required('ADMIN', 'AUDITOR')
def audit_dashboard(request):
    """Tableau de bord d'audit avec filtres."""
    event_type = request.GET.get('type', '')
    user_filter = request.GET.get('user', '')
    app_filter = request.GET.get('app', '')
    source = request.GET.get('source', 'all')  # all | keycloak | portal

    # ── Events Keycloak ──────────────────────────────────────────────────────
    keycloak_events = []
    if source in ('all', 'keycloak'):
        try:
            raw = keycloak.get_events(
                event_type=event_type or None,
                user=user_filter or None,
                client=app_filter or None,
                max=200,
            )
            user_map = {
                ev['userId']: ev['details']['username']
                for ev in raw
                if ev.get('userId') and ev.get('details', {}).get('username')
            }
            for ev in raw:
                ts = datetime.fromtimestamp(ev['time'] / 1000, tz=timezone.utc) if 'time' in ev else None
                username = (ev.get('details', {}).get('username')
                            or user_map.get(ev.get('userId', ''), ''))
                keycloak_events.append({
                    'source': 'keycloak',
                    'type': ev.get('type', '—'),
                    'display_user': username or ev.get('userId', '?'),
                    'display_initials': (username[:2] if username else ev.get('userId', '??')[:2]).upper(),
                    'time_formatted': ts.strftime('%d/%m/%Y %H:%M:%S') if ts else '—',
                    'ts': ts,
                    'ip': ev.get('ipAddress', '—'),
                    'app': ev.get('clientId', '—'),
                    'details': '',
                })
        except Exception as e:
            pass

    # ── Logs portail (Django DB) ─────────────────────────────────────────────
    portal_events = []
    if source in ('all', 'portal'):
        qs = AuditLog.objects.all()
        if user_filter:
            qs = qs.filter(operator__icontains=user_filter) | qs.filter(target__icontains=user_filter)
        if event_type and event_type in dict(AuditLog.ACTION_CHOICES):
            qs = qs.filter(action=event_type)
        for log in qs[:200]:
            portal_events.append({
                'source': 'portal',
                'type': log.action,
                'display_user': log.operator,
                'display_initials': log.operator[:2].upper(),
                'time_formatted': log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                'ts': log.timestamp,
                'ip': log.ip_address or '—',
                'app': f'→ {log.target}' if log.target else '—',
                'details': log.details,
            })

    # Fusionner et trier par date décroissante
    all_events = sorted(
        keycloak_events + portal_events,
        key=lambda e: e['ts'] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    event_types = ['LOGIN', 'LOGIN_ERROR', 'LOGOUT', 'CODE_TO_TOKEN',
                   'USER_CREATE', 'USER_UPDATE', 'USER_DELETE']

    # Liste des applications connues pour les chips de filtre
    from django.conf import settings
    known_apps = [{'id': a['id'], 'name': a['name'], 'icon': a['icon']}
                  for a in settings.IAM_APPLICATIONS]

    return render(request, 'audit/dashboard.html', {
        'events': all_events,
        'event_types': event_types,
        'selected_type': event_type,
        'user_filter': user_filter,
        'app_filter': app_filter,
        'source': source,
        'known_apps': known_apps,
        'total': len(all_events),
    })


@login_required
@role_required('ADMIN', 'AUDITOR')
def export_csv(request):
    """Export des logs d'audit au format CSV (Keycloak + portail)."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="audit_sodepa_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
    )
    response.write('﻿')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Date/Heure', 'Source', 'Type', 'Opérateur', 'Cible/App', 'IP', 'Détails'])

    for log in AuditLog.objects.all():
        writer.writerow([
            log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            'Portail',
            log.action,
            log.operator,
            log.target,
            log.ip_address or '',
            log.details,
        ])

    for ev in keycloak.get_events(max=1000):
        ts = datetime.fromtimestamp(ev.get('time', 0) / 1000).strftime('%d/%m/%Y %H:%M:%S')
        writer.writerow([
            ts, 'Keycloak', ev.get('type', ''),
            ev.get('details', {}).get('username', ev.get('userId', '')),
            ev.get('clientId', ''),
            ev.get('ipAddress', ''),
            '',
        ])

    return response
