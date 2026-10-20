import os
import sys
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from django.test import RequestFactory
from rathinam.urls import urlpatterns
from django.urls import resolve

factory = RequestFactory()
request = factory.post('/transport/api/token/', data={'username': 'admin', 'password': 'admin123'}, content_type='application/json')

try:
    match = resolve('/transport/api/token/')
    print("Resolved view:", match.func)
    response = match.func(request)
    print("Response status:", response.status_code)
    if hasattr(response, 'content'):
        print("Response content snippet:", response.content[:500])
except Exception as e:
    print("=== EXCEPTION TRACEBACK ===")
    traceback.print_exc()
