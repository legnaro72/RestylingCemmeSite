import requests
import base64

WP_URL = "https://staging.studiociemme.net"
WP_USER = "Marco"
WP_APP_PASSWORD = "vtuS 60T7 pWMM 63zC 2Jwo PYfQ"

staging_user = "info_5qownsi4"
staging_pass = "ES2Q!Fff1_7*803e"

wp_token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
headers = {"Authorization": f"Basic {wp_token}"}
auth = (staging_user, staging_pass)

# Test 1: /?rest_route=/
url1 = f"{WP_URL}/?rest_route=/wp/v2/posts"
r1 = requests.get(url1, headers=headers, auth=auth)
print("Test 1: /?rest_route=/wp/v2/posts")
print("Status Code:", r1.status_code)
if r1.status_code == 200:
    print("Success: loaded", len(r1.json()), "posts")
else:
    print("Response:", r1.text[:200])
print("-" * 50)

# Test 2: /wp-json/wp/v2/
url2 = f"{WP_URL}/wp-json/wp/v2/posts"
r2 = requests.get(url2, headers=headers, auth=auth)
print("Test 2: /wp-json/wp/v2/posts")
print("Status Code:", r2.status_code)
if r2.status_code == 200:
    print("Success: loaded", len(r2.json()), "posts")
else:
    print("Response:", r2.text[:200])
