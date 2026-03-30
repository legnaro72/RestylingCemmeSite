import requests

url = "https://staging.studiociemme.net/?rest_route=/wp/v2/posts"
r = requests.get(url, params={"status": "any"}, auth=("info_5qownsi4", "ES2Q!Fff1_7*803e"))
print("Status:", r.status_code)
print("Response:", r.text[:200])
