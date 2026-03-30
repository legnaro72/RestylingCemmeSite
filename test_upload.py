import requests
import base64
import os

WP_URL = "https://staging.studiociemme.net"
WP_USER = "Marco"
WP_APP_PASSWORD = "vtuS 60T7 pWMM 63zC 2Jwo PYfQ"

# Create a dummy 1x1 gif
fbytes = b"GIF89a\x01\x00\x01\x00\x80\xff\x00\xff\xff\xff\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
fname = "test_pixel.gif"
mime_type = "image/gif"

wp_token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
headers = {
    "Authorization": f"Basic {wp_token}", 
    "Content-Disposition": f'attachment; filename="{fname}"',
    "Content-Type": mime_type
}

url = f"{WP_URL}/?rest_route=/wp/v2/media"
r = requests.post(url, headers=headers, data=fbytes)
print("Status:", r.status_code)
print("Response:", r.text[:200])

if r.status_code == 201:
    print("Success URL:", r.json().get("source_url"))
