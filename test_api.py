"""Test diretto delle API WordPress per debug del salvataggio."""
import requests
import base64
import json

WP_URL = "http://studiociemme-test.local"
WP_USER = "admin"
WP_APP_PASSWORD = "cNVMexHuaXssh1TyCsytYbvz"
API_BASE = f"{WP_URL}/wp-json/wp/v2"

def auth():
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

print("=" * 60)
print("TEST 1: Connessione base a WordPress")
print("=" * 60)
try:
    r = requests.get(f"{WP_URL}/wp-json/", timeout=10)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Nome sito: {data.get('name', 'N/A')}")
        print(f"  URL: {data.get('url', 'N/A')}")
    else:
        print(f"  ERRORE: {r.text[:300]}")
except Exception as e:
    print(f"  ERRORE CONNESSIONE: {e}")

print()
print("=" * 60)
print("TEST 2: Autenticazione (lettura post privati)")
print("=" * 60)
try:
    r = requests.get(f"{API_BASE}/posts?status=any&per_page=1", headers=auth(), timeout=10)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        posts = r.json()
        if posts:
            print(f"  Post trovato: {posts[0]['title']['rendered']}")
        print("  ✅ Autenticazione OK")
    else:
        print(f"  ❌ ERRORE AUTH: {r.text[:300]}")
except Exception as e:
    print(f"  ERRORE: {e}")

print()
print("=" * 60)
print("TEST 3: Elenco pagine")
print("=" * 60)
try:
    r = requests.get(f"{API_BASE}/pages?per_page=50&status=any", headers=auth(), timeout=10)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        pages = r.json()
        print(f"  Pagine trovate: {len(pages)}")
        for p in pages:
            print(f"    ID={p['id']} | slug={p['slug']} | status={p['status']} | title={p['title']['rendered'][:40]}")
    else:
        print(f"  ERRORE: {r.text[:300]}")
except Exception as e:
    print(f"  ERRORE: {e}")

print()
print("=" * 60)
print("TEST 4: SCRITTURA - Creo post di test")
print("=" * 60)
try:
    data = {
        "title": "__TEST_API_SCRITTURA__",
        "content": "<p>Questo è un test di scrittura API.</p>",
        "status": "draft"
    }
    r = requests.post(
        f"{API_BASE}/posts",
        headers={**auth(), "Content-Type": "application/json"},
        json=data,
        timeout=15
    )
    print(f"  Status: {r.status_code}")
    print(f"  Headers risposta: {dict(r.headers)}")
    if r.status_code in [200, 201]:
        result = r.json()
        test_id = result.get("id")
        print(f"  ✅ Post creato! ID={test_id}")
        print(f"  Link: {result.get('link', 'N/A')}")

        # Cancella il post di test
        r2 = requests.delete(f"{API_BASE}/posts/{test_id}?force=true", headers=auth(), timeout=10)
        print(f"  Cleanup: {r2.status_code}")
    else:
        print(f"  ❌ ERRORE SCRITTURA:")
        print(f"  Body: {r.text[:500]}")
        print(f"  Headers: {dict(r.headers)}")
except Exception as e:
    print(f"  ERRORE: {e}")

print()
print("=" * 60)
print("TEST 5: MODIFICA PAGINA - Aggiorno una pagina esistente")
print("=" * 60)
try:
    # Prendi la prima pagina
    r = requests.get(f"{API_BASE}/pages?per_page=1&status=any", headers=auth(), timeout=10)
    if r.status_code == 200 and r.json():
        page = r.json()[0]
        page_id = page["id"]
        page_title = page["title"]["rendered"]
        old_content = page["content"]["rendered"][:100]
        print(f"  Pagina target: ID={page_id} | {page_title}")
        print(f"  Contenuto attuale (primi 100 char): {old_content}")

        # Aggiorna con un marcatore timestamp
        test_marker = f"<!-- API_TEST_{int(__import__('time').time())} -->"
        new_content = page["content"]["rendered"] + test_marker

        r2 = requests.post(
            f"{API_BASE}/pages/{page_id}",
            headers={**auth(), "Content-Type": "application/json"},
            json={"content": new_content},
            timeout=15
        )
        print(f"  Status aggiornamento: {r2.status_code}")
        if r2.status_code == 200:
            updated = r2.json()
            print(f"  ✅ Pagina aggiornata!")
            print(f"  Modified: {updated.get('modified', 'N/A')}")
            # Verifica che il marker sia nel contenuto
            if test_marker in updated["content"]["rendered"]:
                print(f"  ✅ Contenuto verificato - il marker è presente!")
            else:
                print(f"  ⚠️ Marker non trovato nel contenuto restituito")

            # Ripristina contenuto originale
            requests.post(
                f"{API_BASE}/pages/{page_id}",
                headers={**auth(), "Content-Type": "application/json"},
                json={"content": page["content"]["rendered"]},
                timeout=15
            )
            print(f"  Contenuto originale ripristinato")
        else:
            print(f"  ❌ ERRORE MODIFICA:")
            print(f"  {r2.text[:500]}")
    else:
        print(f"  Nessuna pagina trovata per il test")
except Exception as e:
    print(f"  ERRORE: {e}")

print()
print("=" * 60)
print("FINE TEST")
print("=" * 60)
