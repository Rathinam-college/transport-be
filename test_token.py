import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rathinam.settings')
django.setup()

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.post('/transport/api/token/', {'username': 'admin', 'password': 'admin123'}, format='json')
view = TokenObtainPairView.as_view()

try:
    response = view(request)
    print("STATUS CODE:", response.status_code)
    print("DATA:", response.data)
except Exception as e:
    print("EXCEPTION RAISED DURING TOKEN OBTAIN:")
    traceback.print_exc()
