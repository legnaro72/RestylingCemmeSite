import requests
import base64

# Prova a caricare solo i post PUBBLICATI (senza status=any) per vedere se il 400 sparisce
wp_token = base64.b64encode("Marco:vtuS 60T7 pWMM 63zC 2Jwo PYfQ".encode()).decode()
headers = {"Authorization": f"Basic {wp_token}"}

# Rimuovo status=any per testare se è l'auth di WP che fallisce o il parametro
url = "https://staging.studiociemme.net/?rest_route=/wp/v2/posts&per_page=1"
auth = ("info_5qownsi4", "ES2Q!Fff1_7*803e")

print("Test Post Pubblicati (Senza status=any)...")
r = requests.get(url, headers=headers, auth=auth)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:200]}")
