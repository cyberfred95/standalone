#!/usr/bin/env python
"""
Script to create a Django superuser programmatically.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Superuser credentials
username = 'admin'
email = 'admin@lexamt.fr'
password = 'AdminLara2025!'

# Check if superuser already exists
if User.objects.filter(username=username).exists():
    print(f'Superuser "{username}" already exists.')
    user = User.objects.get(username=username)
    # Update password
    user.set_password(password)
    user.save()
    print(f'Password updated for user "{username}"')
else:
    # Create superuser
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f'Superuser "{username}" created successfully!')

print(f'\nCredentials:')
print(f'  Username: {username}')
print(f'  Email: {email}')
print(f'  Password: {password}')
print(f'\nAdmin URL: http://127.0.0.1:8001/lara-django/admin/')
print(f'       or: https://api.portail.lexamt.fr/lara-django/admin/')
