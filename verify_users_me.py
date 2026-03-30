import requests
import base64

WP_URL = "https://staging.studiociemme.net"
WP_USER = "Marco"
WP_APP_PASSWORD = "vtuS 60T7 pWMM 63zC 2Jwo PYfQ"

staging_user = "info_5qownsi4"
staging_pass = "ES2Q!Fff1_7*803e"

wp_token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()

# 1. Test without basic auth
headers = {"Authorization": f"Basic {wp_token}"}
url1 = f"{WP_URL}/?rest_route=/wp/v2/users/me"

r1 = requests.get(url1, headers=headers)
print("Test 1 (No basic auth):", r1.status_code, r1.text[:200])

# 2. Test with basic auth
r2 = requests.get(url1, headers=headers, auth=(staging_user, staging_pass))
print("Test 2 (With basic auth):", r2.status_code, r2.text[:200])
