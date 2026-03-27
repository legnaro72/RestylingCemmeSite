"""Test: verifica quale template usa ogni pagina e se the_content funziona."""
import requests
import base64

WP_URL = "http://studiociemme-test.local"
WP_USER = "admin"
WP_APP_PASSWORD = "cNVMexHuaXssh1TyCsytYbvz"
API_BASE = f"{WP_URL}/wp-json/wp/v2"

def auth():
    return {"Authorization": f"Basic {base64.b64encode(f'{WP_USER}:{WP_APP_PASSWORD}'.encode()).decode()}"}

# Test: modifica una pagina e verifica sul frontend
r = requests.get(f"{API_BASE}/pages?per_page=50&status=any", headers=auth(), timeout=15)
pages = r.json()

print("PAGINE E TEMPLATE:")
for p in pages:
    pid = p["id"]
    title = p["title"]["rendered"]
    slug = p["slug"]
    template = p.get("template", "(nessuno)")
    content_len = len(p.get("content", {}).get("rendered", ""))
    print(f"  ID={pid:6d} | template={template:30s} | content_len={content_len:5d} | slug={slug}")

# Test scrittura su "Chi Siamo" (ID=24) che usa the_content()
print("\n" + "="*60)
print("TEST SCRITTURA SU CHI SIAMO (ID=24)")
print("="*60)
test_content = "<p><strong>TEST STREAMLIT</strong> - Se vedi questo testo sulla pagina, il salvataggio funziona!</p>"

r2 = requests.post(
    f"{API_BASE}/pages/24",
    headers={**auth(), "Content-Type": "application/json"},
    json={"content": test_content},
    timeout=15
)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    result = r2.json()
    print(f"Modified: {result.get('modified')}")
    saved = result.get("content", {}).get("rendered", "")
    print(f"Content salvato: {saved[:200]}")
    print(">> Ora apri http://studiociemme-test.local/chi-siamo/ nel browser!")
else:
    print(f"ERRORE: {r2.text[:300]}")
