import requests
import base64

wp_token = base64.b64encode("Marco:vtuS 60T7 pWMM 63zC 2Jwo PYfQ".encode()).decode()
headers = {"Authorization": f"Basic {wp_token}"}
url = "https://info_5qownsi4:ES2Q%21Fff1_7%2A803e@staging.studiociemme.net/?rest_route=/wp/v2/posts&status=any&per_page=1"

print("Sending URL auth request...")
r = requests.get(url, headers=headers)
print(f"Status: {r.status_code}")
try:
    print(r.json()[:1])
except:
    print(r.text[:200])
