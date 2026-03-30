import urllib.request
import base64
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Credenziali Base Auth per il server web hostato
auth_string = "info_5qownsi4:ES2Q!Fff1_7*803e"
auth_base64 = base64.b64encode(auth_string.encode()).decode()

def test_endpoint(ep):
    url = f"https://staging.studiociemme.net/wp-json/wp/v2/{ep}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth_base64}")
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode())
            print(f"{ep} len: {len(data)}")
            if len(data) > 0:
                print(f"Primo {ep}: {data[0]['title']['rendered']}")
    except Exception as e:
        print(f"Errore {ep}: {e}")

test_endpoint("posts")
test_endpoint("news")
