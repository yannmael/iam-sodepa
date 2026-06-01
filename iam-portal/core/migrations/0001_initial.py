from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[
                    ('USER_CREATE', 'Création utilisateur'),
                    ('USER_UPDATE', 'Modification utilisateur'),
                    ('USER_DELETE', 'Suppression utilisateur'),
                    ('ROLE_ASSIGN', 'Attribution de rôle'),
                    ('ROLE_REMOVE', 'Retrait de rôle'),
                    ('APP_ACCESS', 'Accès application'),
                ], max_length=50)),
                ('operator', models.CharField(help_text="Username de l'admin ayant effectué l'action", max_length=150)),
                ('target', models.CharField(blank=True, help_text='Username ou ID de la cible', max_length=150)),
                ('details', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': "Log d'audit",
                'verbose_name_plural': "Logs d'audit",
                'ordering': ['-timestamp'],
            },
        ),
    ]
