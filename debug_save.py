"""
DEBUG PRECISO: simula ESATTAMENTE quello che fa l'app Streamlit
per trovare dove si rompe il salvataggio.
"""
import requests
import base64
import json
import time

WP_URL = "http://studiociemme-test.local"
WP_USER = "admin"
WP_APP_PASSWORD = "cNVMexHuaXssh1TyCsytYbvz"
API_BASE = f"{WP_URL}/wp-json/wp/v2"

def auth():
    c = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {c}"}


print("=" * 60)
print("A) MODIFICA ARTICOLO ESISTENTE")
print("=" * 60)

# 1. Leggi un post
r = requests.get(f"{API_BASE}/posts?status=any&per_page=1", headers=auth(), timeout=15)
if r.status_code != 200:
    print(f"ERRORE lettura post: {r.status_code} {r.text[:200]}")
else:
    posts = r.json()
    if not posts:
        print("Nessun post trovato, ne creo uno di test")
        r2 = requests.post(f"{API_BASE}/posts",
                           headers={**auth(), "Content-Type": "application/json"},
                           json={"title": "Post Test Debug", "content": "<p>Originale</p>", "status": "publish"},
                           timeout=15)
        post = r2.json()
    else:
        post = posts[0]

    post_id = post["id"]
    post_title = post["title"]["rendered"]
    old_content = post["content"]["rendered"]

    print(f"  Post: ID={post_id}, title='{post_title}'")
    print(f"  Contenuto attuale: {old_content[:150]}")

    # 2. Modifica con timestamp
    ts = time.strftime("%H:%M:%S")
    new_html = f"<h2>Modificato da debug</h2><p>Questo testo e' stato scritto dal debug alle {ts}</p>"

    print(f"\n  Invio nuovo contenuto:")
    print(f"  HTML: {new_html}")

    payload = {"content": new_html}
    print(f"  Payload JSON: {json.dumps(payload, indent=2)}")

    r3 = requests.post(
        f"{API_BASE}/posts/{post_id}",
        headers={**auth(), "Content-Type": "application/json"},
        json=payload,
        timeout=20
    )

    print(f"\n  Risposta HTTP: {r3.status_code}")
    if r3.status_code == 200:
        result = r3.json()
        print(f"  modified: {result.get('modified')}")
        saved_content = result["content"]["rendered"]
        print(f"  Contenuto dopo salvataggio: {saved_content[:200]}")

        # 3. Verifica rileggendo
        r4 = requests.get(f"{API_BASE}/posts/{post_id}", headers=auth(), timeout=15)
        verify = r4.json()
        verify_content = verify["content"]["rendered"]
        print(f"\n  VERIFICA (rilettura): {verify_content[:200]}")

        if ts in verify_content:
            print(f"\n  OK - il timestamp {ts} e' presente nel contenuto!")
        else:
            print(f"\n  ERRORE - timestamp non trovato nella verifica!")

        link = result.get("link", "")
        print(f"\n  Link frontend: {link}")
        print(f"  >> Apri questo link nel browser per verificare!")
    else:
        print(f"  ERRORE: {r3.text[:300]}")
        print(f"  Headers risposta: {dict(r3.headers)}")


print("\n")
print("=" * 60)
print("B) MODIFICA PAGINA ESISTENTE (Chi Siamo, ID=24)")
print("=" * 60)

# Leggi pagina
r5 = requests.get(f"{API_BASE}/pages/24", headers=auth(), timeout=15)
if r5.status_code == 200:
    page = r5.json()
    print(f"  Pagina: {page['title']['rendered']}")
    print(f"  Template: {page.get('template', 'default')}")
    print(f"  Contenuto attuale (primi 100): {page['content']['rendered'][:100]}")

    ts2 = time.strftime("%H:%M:%S")
    new_page_html = f"<h2>Studio Ciemme</h2><p>Contenuto modificato via API alle {ts2}</p><p>Se vedi questo testo nella pagina Chi Siamo del sito, il salvataggio API funziona correttamente.</p>"

    r6 = requests.post(
        f"{API_BASE}/pages/24",
        headers={**auth(), "Content-Type": "application/json"},
        json={"content": new_page_html},
        timeout=20
    )

    print(f"\n  Risposta HTTP: {r6.status_code}")
    if r6.status_code == 200:
        res = r6.json()
        print(f"  modified: {res.get('modified')}")
        print(f"  Contenuto salvato: {res['content']['rendered'][:200]}")

        # Verifica
        r7 = requests.get(f"{API_BASE}/pages/24", headers=auth(), timeout=15)
        v = r7.json()
        print(f"\n  VERIFICA: {v['content']['rendered'][:200]}")

        if ts2 in v['content']['rendered']:
            print(f"\n  OK - timestamp {ts2} trovato!")
        else:
            print(f"\n  ERRORE - timestamp non trovato!")

        print(f"\n  >> Apri http://studiociemme-test.local/chi-siamo/ per verificare")
    else:
        print(f"  ERRORE: {r6.text[:300]}")
else:
    print(f"  ERRORE lettura pagina: {r5.status_code}")


print("\n")
print("=" * 60)
print("FINE DEBUG")
print("=" * 60)
