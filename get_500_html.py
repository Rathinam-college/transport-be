import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/transport/api/token/',
    data=json.dumps({'username':'admin','password':'admin123'}).encode('utf-8'),
    headers={'Content-Type':'application/json'}
)

try:
    res = urllib.request.urlopen(req)
    print("SUCCESS", res.status)
    print(res.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("STATUS CODE:", e.code)
    body = e.read().decode('utf-8', errors='ignore')
    print("=== ERROR HTML SNIPPET ===")
    print(body[:3000])
