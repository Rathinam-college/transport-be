import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from django.contrib.auth.models import User

def create_or_reset_superuser(username='admin', password='adminpassword'):
    try:
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        
        status = "Created new" if created else "Updated existing"
        print(f"SUCCESS: {status} superuser account!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to set superuser: {e}")
        return False

if __name__ == '__main__':
    user_arg = sys.argv[1] if len(sys.argv) > 1 else 'admin'
    pass_arg = sys.argv[2] if len(sys.argv) > 2 else 'admin123'
    create_or_reset_superuser(user_arg, pass_arg)
