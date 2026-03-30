# ============================================================
# Studio Ciemme — Editor Visivo  v5.0  DEFINITIVO
# Fix: salvataggio garantito, upload senza loop, preview reale
# ============================================================

import streamlit as st
import requests
import base64
import os
import re
import time
import uuid
from datetime import datetime
from html import unescape
from typing import Any
from dotenv import load_dotenv

load_dotenv(override=True)

def get_env(key, default):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# Configuration environments
ENVS = {
    "Staging 🚀": {
        "url": get_env("STAGING_WP_URL", "https://staging.studiociemme.net"),
        "user": get_env("STAGING_WP_USER", "Marco"),
        "pass": get_env("STAGING_WP_APP_PASSWORD", "vtuS 60T7 pWMM 63zC 2Jwo PYfQ"),
        "api_base": "/?rest_route=/wp/v2",
        "api_test": "/?rest_route=/wp/v2/users/me"
    }
}

# Ensure env is in session state for global access
if "env" not in st.session_state:
    st.session_state.env = "Staging 🚀"

# Current config based on selection
_ce = ENVS.get(st.session_state.env, ENVS["Staging 🚀"])
WP_URL = _ce["url"]
WP_USER = _ce["user"]
WP_APP_PASSWORD = _ce["pass"]
API_BASE = f"{WP_URL}{_ce['api_base']}"
API_TEST = f"{WP_URL}{_ce['api_test']}"

IMG_TYPES = ["jpg", "jpeg", "png", "gif", "webp"]
MAX_IMG_MB = 5


# ============================================================
# WP API
# ============================================================
def _auth():
    return {"Authorization": f"Basic {base64.b64encode(f'{WP_USER}:{WP_APP_PASSWORD}'.encode()).decode()}"}

def _make_req(method, url, **kwargs):
    headers = kwargs.get("headers", {})
    
    wp_token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    headers["Authorization"] = f"Basic {wp_token}"
    
    kwargs["headers"] = headers

    # RIMOSSO: Il basic auth dello staging (auth) sovrascriveva l'header Authorization di WordPress
    # causando Errore 401 (Non Logged In) sulle API private.

    if method == "GET":
        return requests.get(url, **kwargs)
    elif method == "POST":
        return requests.post(url, **kwargs)
    elif method == "DELETE":
        return requests.delete(url, **kwargs)

def wp_read(ep, params=None):
    try:
        url = f"{API_BASE}/{ep}"
        r = _make_req("GET", url, params=params or {}, timeout=15)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def wp_write(ep, data):
    try:
        url = f"{API_BASE}/{ep}"
        headers = {**_auth(), "Content-Type": "application/json"}
        r = _make_req("POST", url, headers=headers, json=data, timeout=20)
        if r.status_code in [200, 201]:
            return True, r.json()
        try:
            msg = r.json().get("message", f"HTTP {r.status_code}")
        except Exception:
            msg = f"HTTP {r.status_code}: {r.text[:200]}"
        return False, msg
    except Exception as e:
        return False, str(e)

def wp_upload(fbytes, fname):
    for _ in range(3):
        try:
            url = f"{API_BASE}/media"
            headers = {**_auth(), "Content-Disposition": f'attachment; filename="{fname}"'}
            r = _make_req("POST", url, headers=headers, data=fbytes, timeout=30)
            if r.status_code in [200, 201]:
                return r.json().get("source_url")
        except Exception:
            pass
        time.sleep(0.5)
    return None

def wp_test():
    try:
        r = _make_req("GET", API_TEST, timeout=8)
        if r.status_code == 200:
            return True, "OK"
        elif r.status_code == 401 or r.status_code == 403:
            return False, f"Errore di Autenticazione (HTTP {r.status_code})"
        return False, f"Status Code {r.status_code}"
    except Exception as e:
        return False, str(e)


# ============================================================
# BLOCCHI
# ============================================================
def _bid() -> str:
    return str(uuid.uuid4())[:8] # type: ignore

def nb(tipo, contenuto="", **kw: Any):
    b: dict[str, Any] = {"id": _bid(), "tipo": tipo, "contenuto": contenuto}
    b.update(kw)
    return b

def _strip(h):
    return unescape(re.sub(r'<[^>]+>', '', h or '')).strip()


def html_to_blocks(html: str) -> list[dict[str, Any]]:
    if not html or not html.strip():
        return [nb("testo", "")]

    # Remove only Gutenberg comment wrappers
    text = re.sub(r'<!--\s*/?wp:[^>]*-->\n?', '', html).strip()

    # If it's a strongly structured page (Gutenberg layout, WPBakery columns, etc.)
    # preserve the entire content as a single HTML block so the visual preview and 
    # data format are totally unaffected.
    if re.search(r'<(div|section|article|header|footer|nav|aside|table|form|style|script)\b', text, re.IGNORECASE):
        return [nb("html", text)]

    blocks: list[dict[str, Any]] = []
    
    parts = re.split(r'(<(?:h[1-6]|figure|img|hr|iframe)[^>]*(?:>.*?</(?:h[1-6]|figure)>|/?>))',
                     text, flags=re.DOTALL | re.IGNORECASE)
                     
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        hm = re.match(r'<h([1-6])[^>]*>(.*?)</h\1>', part, flags=re.DOTALL | re.IGNORECASE)
        if hm:
            title_text = re.sub(r'<[^>]+>', '', hm.group(2)).strip()
            blocks.append(nb("titolo", title_text, heading_level=int(hm.group(1))))
            continue
            
        if re.match(r'<hr\b', part, flags=re.IGNORECASE):
            blocks.append(nb("separatore"))
            continue
            
        img = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', part, flags=re.IGNORECASE)
        if img:
            alt_m = re.search(r'alt=["\']([^"\']*)["\']', part, flags=re.IGNORECASE)
            style = {}
            w_m = re.search(r'width[:\s]*(\d+(?:px|%|em))', part, flags=re.IGNORECASE)
            if w_m:
                style["width"] = w_m.group(1)
            blocks.append(nb("immagine", "", image_url=img.group(1),
                             image_alt=alt_m.group(1) if alt_m else "", style=style))
            continue
            
        ifr = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', part, flags=re.IGNORECASE)
        if ifr:
            src = ifr.group(1)
            if "youtube" in src or "youtu.be" in src:
                blocks.append(nb("youtube", src))
            elif "google.com/maps" in src:
                blocks.append(nb("mappa", src))
            else:
                blocks.append(nb("html", part))
            continue
            
        # Testo standard: preserviamo eventuale markup semplice (<b>, <a>, <i>)
        # Se è avvolto in <p>, rimuoviamo il wrapper per evitare ridondanza in output
        p_match = re.fullmatch(r'<p[^>]*>(.*?)</p>', part, flags=re.DOTALL | re.IGNORECASE)
        if p_match:
            part = p_match.group(1).strip()
            
        if part:
            blocks.append(nb("testo", part))

    return blocks if blocks else [nb("testo", "")]


def blocks_to_html(blocks: list[dict[str, Any]]) -> str:
    out: list[str] = []
    for b in blocks:
        t = b["tipo"]
        c = b.get("contenuto", "").strip()
        s = b.get("style", {})

        if t == "titolo" and c:
            lv = b.get("heading_level", 2)
            align = s.get("alignment", "")
            style = f' style="text-align:{align};"' if align else ""
            out.append(f"<h{lv}{style}>{c}</h{lv}>")

        elif t == "testo" and c:
            align = s.get("alignment", "")
            style_str = f' style="text-align:{align};"' if align else ""
            for line in c.split('\n'):
                line = line.strip()
                if line:
                    if line.lower().startswith("<h") or line.lower().startswith("<p"):
                        out.append(line)
                    else:
                        out.append(f'<p{style_str}>{line}</p>')

        elif t == "immagine":
            u = b.get("image_url", "")
            a = b.get("image_alt", "")
            if u:
                w = s.get("width", "100%")
                align = s.get("alignment", "center")
                cap = f"<figcaption>{a}</figcaption>" if a else ""
                out.append(f'<figure style="text-align:{align};margin:1.5rem 0;">'
                           f'<img src="{u}" alt="{a}" style="width:{w};max-width:100%;height:auto;border-radius:8px;"/>'
                           f'{cap}</figure>')

        elif t == "bottone" and c:
            u = b.get("button_url", "#")
            align = s.get("alignment", "center")
            out.append(f'<div style="text-align:{align};margin:2rem 0;">'
                       f'<a href="{u}" style="display:inline-block;padding:14px 36px;'
                       f'background:#1B2A4A;color:#fff;text-decoration:none;'
                       f'border-radius:8px;font-weight:600;">{c}</a></div>')

        elif t == "separatore":
            out.append('<hr style="border:none;border-top:2px solid #E2E8F0;margin:2rem 0;"/>')

        elif t == "spaziatore":
            h = b.get("height", 40)
            out.append(f'<div style="height:{h}px;"></div>')

        elif t == "youtube" and c:
            vid = c
            ym = re.search(r'(?:youtube\.com/(?:watch\?v=|embed/)|youtu\.be/)([a-zA-Z0-9_-]+)', c)
            if ym:
                vid = ym.group(1)
            w = s.get("width", "560")
            out.append(f'<div style="text-align:center;margin:2rem 0;">'
                       f'<iframe width="{w}" height="315" src="https://www.youtube.com/embed/{vid}" '
                       f'frameborder="0" allowfullscreen style="max-width:100%;border-radius:8px;"></iframe></div>')

        elif t == "mappa" and c:
            out.append(f'<div style="margin:2rem 0;"><iframe src="{c}" width="100%" height="400" '
                       f'style="border:0;border-radius:8px;" allowfullscreen loading="lazy"></iframe></div>')

        elif t == "accordion":
            at = b.get("accordion_title", "")
            out.append(f'<details style="margin:1rem 0;border:1px solid #E2E8F0;border-radius:8px;padding:1rem;">'
                       f'<summary style="cursor:pointer;font-weight:600;color:#1B2A4A;">{at}</summary>'
                       f'<div style="margin-top:0.5rem;">{c}</div></details>')

        elif t == "html" and c:
            out.append(c)

    return "\n".join(out)


# ============================================================
# SYNC: leggi valori widget e aggiorna blocchi
# ============================================================
def sync_blocks_from_widgets():
    """Legge i valori correnti dei widget Streamlit e aggiorna i blocchi.
    DEVE essere chiamata PRIMA di blocks_to_html per il salvataggio."""
    blocks = st.session_state.get("blocks", [])
    for b in blocks:
        bid = b["id"]
        tipo = b["tipo"]
        s = b.setdefault("style", {})

        # Contenuto principale
        ckey = f"c{bid}"
        if ckey in st.session_state:
            b["contenuto"] = st.session_state[ckey]

        # Campi specifici per tipo
        if tipo == "immagine":
            akey = f"a{bid}"
            if akey in st.session_state:
                b["image_alt"] = st.session_state[akey]
            wkey = f"w{bid}"
            if wkey in st.session_state:
                s["width"] = st.session_state[wkey]
            alkey = f"al{bid}"
            if alkey in st.session_state:
                s["alignment"] = st.session_state[alkey]

        elif tipo == "bottone":
            ukey = f"bu{bid}"
            if ukey in st.session_state:
                b["button_url"] = st.session_state[ukey]

        elif tipo == "spaziatore":
            hkey = f"h{bid}"
            if hkey in st.session_state:
                b["height"] = st.session_state[hkey]

        elif tipo == "accordion":
            atkey = f"at{bid}"
            if atkey in st.session_state:
                b["accordion_title"] = st.session_state[atkey]

        elif tipo in ("testo", "titolo"):
            alkey = f"al{bid}"
            if alkey in st.session_state:
                s["alignment"] = st.session_state[alkey]

        elif tipo == "youtube":
            wkey = f"yw{bid}"
            if wkey in st.session_state:
                s["width"] = str(st.session_state[wkey])


# ============================================================
# INIT SESSION
# ============================================================
def init():
    for k, v in {
        "blocks": [], "item": None, "item_type": None, "item_title": "",
        "mode": "home", "saved": True, "msg": "", "msg_ok": True,
        "processed_uploads": set(), "debug_log": "", "env": "Staging 🚀"
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# APP
# ============================================================
st.set_page_config(page_title="Studio Ciemme - Editor", page_icon="✏️",
                   layout="wide", initial_sidebar_state="collapsed")
init()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .hdr{background:linear-gradient(135deg,#1B2A4A,#2C5282);padding:1rem 1.5rem;
         border-radius:12px;color:#fff;margin-bottom:1.5rem;
         display:flex;justify-content:space-between;align-items:center;}
    .hdr h2{color:#fff;margin:0;font-size:1.4rem;}
    .hdr .sub{color:rgba(255,255,255,.55);font-size:.82rem;margin:0;}
    .pill{font-size:.75rem;padding:.2rem .7rem;border-radius:20px;font-weight:600;}
    .pill-ok{background:#C6F6D5;color:#22543D;}
    .pill-dirty{background:#FEFCBF;color:#744210;}
    .pv{background:#fff;border:2px solid #E2E8F0;border-radius:12px;padding:2rem;
        font-family:'Inter',sans-serif;line-height:1.7;color:#2D3748;
        min-height:300px;max-height:700px;overflow-y:auto;}
    .pv h1{font-size:2rem;color:#1B2A4A;margin:0 0 .5rem;}
    .pv h2{font-size:1.5rem;color:#1B2A4A;margin:1.2rem 0 .5rem;}
    .pv h3{font-size:1.2rem;color:#2C5282;margin:1rem 0 .4rem;}
    .pv p{margin:.5rem 0;} .pv img{max-width:100%;height:auto;border-radius:8px;}
    .pv figure{text-align:center;margin:1.5rem 0;}
    .pv figcaption{font-size:.85rem;color:#718096;margin-top:.4rem;}
    .pv hr{border:none;border-top:2px solid #E2E8F0;margin:1.5rem 0;}
    .pv details{margin:1rem 0;border:1px solid #E2E8F0;border-radius:8px;padding:1rem;}
    .pv summary{cursor:pointer;font-weight:600;color:#1B2A4A;}
    .pv iframe{max-width:100%;border-radius:8px;}
    section[data-testid="stSidebar"]{display:none;}
    .debug-box{background:#1a1a2e;color:#0f0;padding:1rem;border-radius:8px;
               font-family:monospace;font-size:.75rem;max-height:200px;overflow-y:auto;
               margin:1rem 0; white-space:pre-wrap;}
</style>
""", unsafe_allow_html=True)

# Header
pill = ""
if st.session_state.mode in ["edit", "new"]:
    pill = ('<span class="pill pill-ok">Salvato</span>' if st.session_state.saved
            else '<span class="pill pill-dirty">Modifiche non salvate</span>')
st.markdown(f'<div class="hdr"><div><h2>Studio Ciemme</h2>'
            f'<p class="sub">Editor visivo del sito</p></div><div>{pill}</div></div>',
            unsafe_allow_html=True)

# ================================================================
# HOME
# ================================================================
if st.session_state.mode == "home":
    # Mostra ambiente corrente
    st.markdown(f"### 🌐 Connesso a: **{st.session_state.env}** ({WP_URL})")
    st.write("WP USER:", WP_USER)
    st.write("WP URL:", WP_URL)
    st.write("ENV USER RAW:", get_env("STAGING_WP_USER", "Marco default"))

    # Test Connection
    is_up, reason = wp_test()
    if not is_up:
        st.error(f"Il sito WordPress non è raggiungibile.")
        st.error(f"Dettaglio: {reason}")
        st.info("Verifica la tua connessione internet e le credenziali.")
        st.stop()

    if st.session_state.msg:
        (st.success if st.session_state.msg_ok else st.error)(st.session_state.msg)
        st.session_state.msg = ""

    st.markdown("## Cosa vuoi fare?")

    # Pagine
    st.markdown("### Pagine (Non Modificabili Visualmente)")
    pages = wp_read("pages", {"per_page": 50, "status": "any"}) or []
    SKIP = {"checkout", "cart", "my-account", "logout", "wishlist",
            "mijireh-secure-checkout", "sample-page", "test-page", "shortcodes", "screenshots"}
    ICONS = {"home": "🏠", "chi siamo": "👥", "about": "👥", "servizi": "💼",
             "app2do": "🚀", "contatti": "📞", "privacy": "🔒", "blog": "📰",
             "news": "📰", "notizie": "📰", "prodotti": "📦"}

    vis = [p for p in pages if p.get("slug", "") not in SKIP and p.get("status") != "trash"]
    if vis:
        cols = st.columns(min(len(vis), 4))
        for i, pg in enumerate(vis):
            title = _strip(pg["title"]["rendered"]) or pg["slug"]
            slug = pg.get("slug", "")
            icon = next((v for k, v in ICONS.items() if k in title.lower() or k in slug), "📄")
            with cols[i % min(len(vis), 4)]:
                if st.button(f"{icon} {title}", key=f"pg_{pg['id']}", use_container_width=True, disabled=True):
                    st.session_state.blocks = html_to_blocks(pg["content"]["rendered"])
                    st.session_state.item = {"id": pg["id"], "type": "pages", "title": title,
                                             "link": pg.get("link", "")}
                    st.session_state.item_type = "pagina"
                    st.session_state.item_title = title
                    st.session_state.saved = True
                    st.session_state.processed_uploads = set()
                    st.session_state.debug_log = ""
                    st.session_state.mode = "edit"
                    st.rerun()

    st.markdown("---")

    # News
    st.markdown("### News")
    if st.button("Scrivi nuova News", type="primary"):
        st.session_state.blocks = [nb("titolo", "", heading_level=2), nb("testo", "")]
        st.session_state.item = None
        st.session_state.item_type = "news"
        st.session_state.item_title = ""
        st.session_state.saved = True
        st.session_state.processed_uploads = set()
        st.session_state.debug_log = ""
        st.session_state.mode = "new"
        st.rerun()

    posts = wp_read("posts", {"per_page": 50, "status": "any"}) or []
    posts = [p for p in posts if p.get("status") != "trash"]
    
    if posts:
        st.markdown("#### Gestione Multipla")
        bc1, bc2 = st.columns([1, 4])
        with bc1:
            sel_all = st.checkbox("✔ Seleziona tutto", key="sa_news")
            # Forza l'aggiornamento diretto del session_state per i figli
            if st.session_state.get("last_sa_news") != sel_all:
                st.session_state.last_sa_news = sel_all
                for p in posts:
                    st.session_state[f"chk_{p['id']}"] = sel_all
        with bc2:
            if st.button("🗑️ Elimina selezionati", type="primary"):
                deleted = 0
                for p in posts:
                    if st.session_state.get(f"chk_{p['id']}"):
                        res = _make_req("DELETE", f"{API_BASE}/posts/{p['id']}?force=true")
                        if res and res.status_code in [200, 204]: deleted += 1
                if deleted > 0:
                    st.session_state.msg = f"{deleted} News eliminate!"
                    st.session_state.msg_ok = True
                st.rerun()

        st.markdown("---")

    for p in posts:
        title = _strip(p["title"]["rendered"]) or "Senza titolo"
        pid = p["id"]
        date = p.get("date", "")[:10]
        status = p.get("status", "")
        c1, c2, c3, c4 = st.columns([1, 5, 2, 2])
        with c1:
            st.checkbox("Seleziona", key=f"chk_{pid}", label_visibility="collapsed")
        with c2:
            st.write(f"**{title}** — {date} {'(bozza)' if status == 'draft' else ''}")
        with c3:
            if st.button("✏️ Modifica", key=f"ep_{pid}", use_container_width=True):
                st.session_state.blocks = html_to_blocks(p["content"]["rendered"])
                st.session_state.item = {"id": pid, "type": "posts", "title": title,
                                         "link": p.get("link", "")}
                st.session_state.item_type = "news"
                st.session_state.item_title = title
                st.session_state.saved = True
                st.session_state.processed_uploads = set()
                st.session_state.debug_log = ""
                st.session_state.mode = "edit"
                st.rerun()
        with c4:
            if st.button("🗑️ Elimina", key=f"dp_{pid}", use_container_width=True):
                res = _make_req("DELETE", f"{API_BASE}/posts/{pid}?force=true")
                if res and res.status_code in [200, 204]:
                    st.session_state.msg = "News eliminata!"
                    st.session_state.msg_ok = True
                else:
                    st.session_state.msg = "Errore durante l'eliminazione."
                    st.session_state.msg_ok = False
                st.rerun()


# ================================================================
# EDITOR
# ================================================================
elif st.session_state.mode in ["edit", "new"]:

    # Toolbar
    tb1, tb2, tb3 = st.columns([1, 4, 2])
    with tb1:
        if st.button("Indietro"):
            st.session_state.mode = "home"
            st.session_state.blocks = []
            st.session_state.item = None
            st.rerun()
    with tb2:
        kind = "Nuovo" if st.session_state.mode == "new" else "Modifica"
        st.markdown(f"### {kind} {st.session_state.item_type or ''}: {st.session_state.item_title or 'Nuovo'}")
    with tb3:
        btn_label = "Pubblica" if st.session_state.mode == "new" else "Salva sul sito"
        do_save = st.button(btn_label, type="primary", use_container_width=True)

    # Feedback
    if st.session_state.msg:
        (st.success if st.session_state.msg_ok else st.error)(st.session_state.msg)
        st.session_state.msg = ""

    st.markdown("---")

    # Titolo per nuovi
    if st.session_state.mode == "new":
        st.session_state.item_title = st.text_input(
            "Titolo", value=st.session_state.item_title,
            placeholder="Titolo articolo...", key="_title")

    # 3 colonne
    pal, edt, prev = st.columns([1, 2, 2], gap="medium")

    # ---- PALETTE ----
    with pal:
        st.markdown("#### Aggiungi")
        block_defs = [
            ("titolo", "Titolo", {"heading_level": 2}),
            ("testo", "Testo", {}),
            ("immagine", "Immagine", {"image_url": "", "image_alt": "", "style": {"width": "100%", "alignment": "center"}}),
            ("bottone", "Pulsante", {"button_url": "#"}),
            ("separatore", "Linea", {}),
            ("spaziatore", "Spazio", {"height": 40}),
            ("youtube", "YouTube", {}),
            ("mappa", "Mappa", {}),
            ("accordion", "Espandibile", {"accordion_title": "Titolo"}),
            ("html", "HTML", {}),
        ]
        for bt, label, defaults in block_defs:
            if st.button(label, key=f"add_{bt}", use_container_width=True):
                st.session_state.blocks.append(nb(bt, "", **defaults)) # type: ignore
                st.session_state.saved = False
                st.rerun()

    with edt:
        st.markdown("#### Contenuto")
        blocks = st.session_state.blocks
        action_type = ""
        action_idx = -1

        for idx, b in enumerate(blocks):
            bid = b["id"]
            tipo = b["tipo"]
            s = b.setdefault("style", {})

            # Header
            h1, h2, h3, h4 = st.columns([5, 1, 1, 1])
            with h1:
                st.markdown(f"**{b['tipo'].upper()}**")
                if st.button("X", key=f"x{bid}"):
                    action_type = "del"
                    action_idx = idx
                if idx > 0 and st.button("^", key=f"u{bid}"):
                    action_type = "up"
                    action_idx = idx
            with h2:
                if idx < len(blocks) - 1 and st.button("v", key=f"d{bid}"):
                    action_type = "down"
                    action_idx = idx
            with h3:
                pass # Placeholder for potential future buttons
            with h4:
                    action = ("del", idx)

            # Campi
            if tipo == "titolo":
                st.text_input("t", value=b["contenuto"], key=f"c{bid}",
                              placeholder="Titolo...", label_visibility="collapsed")
                st.selectbox("Allineamento", ["", "left", "center", "right"],
                             index=["", "left", "center", "right"].index(s.get("alignment", "")),
                             key=f"al{bid}", label_visibility="collapsed")

            elif tipo == "testo":
                st.text_area("t", value=b["contenuto"], key=f"c{bid}",
                             height=100, placeholder="Scrivi...", label_visibility="collapsed")
                st.selectbox("Allineamento", ["", "left", "center", "right"],
                             index=["", "left", "center", "right"].index(s.get("alignment", "")),
                             key=f"al{bid}", label_visibility="collapsed")

            elif tipo == "immagine":
                url = b.get("image_url", "")
                if url:
                    st.image(url, width=250)
                st.text_input("Didascalia", value=b.get("image_alt", ""),
                              key=f"a{bid}", placeholder="Descrizione...")
                ic1, ic2 = st.columns(2)
                with ic1:
                    st.text_input("Larghezza", value=s.get("width", "100%"),
                                  key=f"w{bid}", placeholder="100% o 300px")
                with ic2:
                    st.selectbox("Allineamento", ["center", "left", "right"],
                                 index=["center", "left", "right"].index(s.get("alignment", "center")),
                                 key=f"al{bid}")

                # Upload con anti-loop
                f = st.file_uploader("Scegli" if not url else "Cambia",
                                     type=IMG_TYPES, key=f"up_{bid}")
                if f is not None:
                    fid = f"{bid}_{f.name}_{f.size}"
                    if fid not in st.session_state.processed_uploads:
                        if f.size > MAX_IMG_MB * 1024 * 1024:
                            st.error(f"Max {MAX_IMG_MB}MB")
                        else:
                            with st.spinner("Caricamento..."):
                                new_url = wp_upload(f.read(), f.name)
                                if new_url:
                                    b["image_url"] = new_url
                                    if not b.get("image_alt"):
                                        b["image_alt"] = f.name.rsplit('.', 1)[0]
                                    st.session_state.processed_uploads.add(fid)
                                    st.session_state.saved = False
                                    st.rerun()
                                else:
                                    st.error("Upload fallito. Riprova.")

            elif tipo == "bottone":
                st.text_input("Testo", value=b["contenuto"], key=f"c{bid}",
                              placeholder="Testo pulsante...")
                st.text_input("Link", value=b.get("button_url", "#"), key=f"bu{bid}",
                              placeholder="https://...")

            elif tipo == "spaziatore":
                st.slider("Altezza px", 10, 200, b.get("height", 40), key=f"h{bid}")

            elif tipo == "youtube":
                st.text_input("URL YouTube", value=b["contenuto"], key=f"c{bid}",
                              placeholder="https://youtube.com/watch?v=...")

            elif tipo == "mappa":
                st.text_input("URL Embed Maps", value=b["contenuto"], key=f"c{bid}",
                              placeholder="Incolla embed...")

            elif tipo == "accordion":
                st.text_input("Titolo", value=b.get("accordion_title", ""), key=f"at{bid}")
                st.text_area("Contenuto", value=b["contenuto"], key=f"c{bid}", height=80)

            elif tipo == "html":
                b["contenuto"] = st.text_area("HTML", value=b["contenuto"], key=f"c{bid}", height=350)

            elif tipo == "separatore":
                st.markdown("<hr style='margin:.2rem 0;'>", unsafe_allow_html=True)

            st.markdown("---")

        if action_type == "del":
            blocks.pop(action_idx)
            st.session_state.saved = False
            st.rerun()
        elif action_type == "up":
            blocks[action_idx], blocks[action_idx - 1] = blocks[action_idx - 1], blocks[action_idx] # type: ignore
            st.session_state.saved = False
            st.rerun()

    # ---- PREVIEW ----
    with prev:
        st.markdown("#### Anteprima")
        # Sync prima di preview
        sync_blocks_from_widgets()
        html_out = blocks_to_html(st.session_state.blocks)
        title_show = st.session_state.item_title or "..."
        st.markdown(f"""
        <div class="pv">
            <h1>{title_show}</h1>
            <hr style="border:none;border-top:2px solid #E2E8F0;margin:.8rem 0 1.2rem;">
            {html_out if html_out.strip() else '<p style="color:#CBD5E0;">Aggiungi contenuto...</p>'}
        </div>
        """, unsafe_allow_html=True)

        # Pulsante per refresh manuale preview
        if st.button("Aggiorna anteprima", key="refresh_preview"):
            st.rerun()

    # ============================================================
    # SALVATAGGIO — IL CUORE DEL FIX
    # ============================================================
    if do_save:
        # 1. SYNC: leggi TUTTI i valori aggiornati dai widget
        sync_blocks_from_widgets()

        # 2. Genera HTML
        final_html = blocks_to_html(st.session_state.blocks)
        title = st.session_state.item_title
        debug = []
        debug.append(f"[{datetime.now().strftime('%H:%M:%S')}] SALVATAGGIO AVVIATO")
        debug.append(f"Modo: {st.session_state.mode}")
        debug.append(f"Titolo: {title}")
        debug.append(f"HTML generato ({len(final_html)} char):")
        debug.append(final_html[:300] + ("..." if len(final_html) > 300 else "")) # type: ignore

        if st.session_state.mode == "new":
            # NUOVO ARTICOLO
            if not title or not title.strip():
                st.session_state.msg = "Scrivi un titolo prima di pubblicare."
                st.session_state.msg_ok = False
                st.rerun()

            debug.append(f"\nCreazione post: POST {API_BASE}/posts")
            ok, result = wp_write("posts", {
                "title": title,
                "content": final_html,
                "status": "publish"
            })
            debug.append(f"Risultato: ok={ok}")

            if ok and isinstance(result, dict):
                new_id = result.get("id", "?")
                new_link = result.get("link", "")
                debug.append(f"Post creato! ID={new_id}, link={new_link}")
                st.session_state.msg = f"Articolo '{title}' pubblicato! Apri {new_link}"
                st.session_state.msg_ok = True
                st.session_state.saved = True
                st.session_state.mode = "home"
                st.session_state.blocks = []
            else:
                debug.append(f"ERRORE: {result}")
                st.session_state.msg = f"Errore: {result}"
                st.session_state.msg_ok = False

            st.session_state.debug_log = "\n".join(debug)
            st.rerun()

        else:
            # MODIFICA ESISTENTE
            item = st.session_state.item
            if not item:
                st.session_state.msg = "Errore: nessun elemento selezionato."
                st.session_state.msg_ok = False
                st.rerun()

            item_id = item["id"]
            item_ep = item["type"]  # "pages" o "posts"
            endpoint = f"{item_ep}/{item_id}"

            debug.append(f"\nModifica: POST {API_BASE}/{endpoint}")
            debug.append(f"Payload: title='{title}', content=({len(final_html)} char)")

            payload = {"content": final_html}
            if title:
                payload["title"] = title

            ok, result = wp_write(endpoint, payload)
            debug.append(f"Risultato: ok={ok}")

            if ok and isinstance(result, dict):
                mod_time = result.get("modified", "?")
                debug.append(f"Salvato! modified={mod_time}")

                # VERIFICA rileggendo
                verify = wp_read(endpoint)
                if verify:
                    saved_content = verify.get("content", {}).get("rendered", "")
                    debug.append(f"Verifica: contenuto letto ({len(saved_content)} char)")
                    debug.append(f"Prime 100 char: {saved_content[:100]}")

                link = item.get("link", "")
                st.session_state.msg = f"Salvato e pubblicato! Verifica su: {link}"
                st.session_state.msg_ok = True
                st.session_state.saved = True
            else:
                debug.append(f"ERRORE: {result}")
                st.session_state.msg = f"Errore nel salvataggio: {result}"
                st.session_state.msg_ok = False

            st.session_state.debug_log = "\n".join(debug)
            st.rerun()

    # ---- LOG DEBUG (visibile all'utente) ----
    if st.session_state.debug_log:
        with st.expander("Log tecnico ultimo salvataggio", expanded=False):
            st.markdown(f'<div class="debug-box">{st.session_state.debug_log}</div>',
                        unsafe_allow_html=True)
