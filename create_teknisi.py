import os
import django
import sys

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

try:
    user, created = User.objects.get_or_create(username='teknisi', defaults={'email': 'teknisi@gadgetcare.com'})
    user.set_password('teknisi123')
    user.first_name = 'Rasya'
    user.last_name = 'Mahendra'
    user.save()

    profile, p_created = UserProfile.objects.get_or_create(user=user)
    profile.role = 'teknisi'
    profile.save()

    print("Success: teknisi@gadgetcare.com / teknisi123")
except Exception as e:
    print(f"Error: {e}")
