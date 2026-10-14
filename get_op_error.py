import urllib.request
import urllib.error
import json
import re

req = urllib.request.Request(
    'http://127.0.0.1:8000/transport/api/token/',
    data=json.dumps({'username':'admin','password':'admin123'}).encode('utf-8'),
    headers={'Content-Type':'application/json'}
)

try:
    res = urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='ignore')
    match = re.search(r'<th>Exception Value:</th>\s*<td><pre>(.*?)</pre>', body, re.DOTALL)
    if match:
        print("EXACT OPERATIONAL ERROR:")
        print(match.group(1))
    else:
        # Search for exception type and value
        print("EXCEPTIONS SEARCH:")
        for m in re.finditer(r'<pre class="exception_value">(.*?)</pre>', body, re.DOTALL):
            print(m.group(1))
        # Print first part of body with exception info
        h1 = re.search(r'<h1>(.*?)</h1>', body, re.DOTALL)
        if h1:
            print("H1:", h1.group(1))
        pre = re.search(r'<pre>(.*?)</pre>', body, re.DOTALL)
        if pre:
            print("PRE:", pre.group(1))
