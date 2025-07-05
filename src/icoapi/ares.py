"""
ARES helper – implementace podle Katalogu veřejných služeb (08/2023)
Vrací dict {"ico", "name", "address"} nebo None.
"""

from __future__ import annotations
import httpx, xmltodict
from xml.parsers.expat import ExpatError
from typing import Any, Optional

# ───────────────────────── REST ─────────────────────────
REST_ROOT   = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"
REST_PATHS  = [                # zkoušíme v tomto pořadí
    "{root}/v3/ekonomicke-subjekty/{ico}",       # nový strom
    "{root}/ekonomicke-subjekty/{ico}",          # alias (bez /v3)
]
REST_SEARCH = [                # GET ?ico=...&size=1
    "{root}/v3/ekonomicke-subjekty",
    "{root}/ekonomicke-subjekty",
]

HEADERS_JSON = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "ico-api/0.1 (+https://github.com/your-repo)",
}

TIMEOUT = httpx.Timeout(10, connect=5)

# ───────────────────────── XML (legacy) ─────────────────
XML_BAS = "http://wwwinfo.mfcr.cz/cgi-bin/ares/darv_bas.cgi?ico={ico}&xml=1"
XML_ICO = "http://wwwinfo.mfcr.cz/cgi-bin/ares/darv_ico.cgi?ico={ico}&xml=1"

# =============== nízko-úrovňové pomocné funkce ==========
async def _get_json(url: str, params: dict | None = None) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS_JSON) as cli:
            r = await cli.get(url, params=params)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return None

async def _get_text(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cli:
            r = await cli.get(url, follow_redirects=True)
        r.raise_for_status()
        return r.text
    except httpx.HTTPError:
        return None

# ---------------- REST část ----------------
async def _fetch_rest(ico: str) -> Optional[dict]:
    # 1) detail {ico}
    for pattern in REST_PATHS:
        data = await _get_json(pattern.format(root=REST_ROOT, ico=ico))
        if data:
            break
    else:
        data = None

    # 2) fallback – GET search
    if not data:
        for search in REST_SEARCH:
            params = {"ico": ico, "size": 1}
            search_data = await _get_json(search.format(root=REST_ROOT), params)
            if not search_data:
                continue
            items = (
                search_data.get("ekonomickeSubjekty")
                or search_data.get("content")
                or (search_data if isinstance(search_data, list) else [])
            )
            if items:
                data = items[0]
                break

    if not data or not data.get("ico"):
        return None

    return {
        "ico":     data.get("ico"),
        "name":    data.get("obchodniJmeno", ""),
        "address": (data.get("sidlo") or {}).get("textovaAdresa", ""),
    }

# ---------------- XML fallback ----------------
def _scan(node: Any) -> Optional[dict]:
    if isinstance(node, dict):
        if node.get("ICO") and node.get("OF"):
            return node
        for v in node.values():
            out = _scan(v)
            if out:
                return out
    elif isinstance(node, list):
        for it in node:
            out = _scan(it)
            if out:
                return out
    return None

async def _fetch_xml(ico: str) -> Optional[dict]:
    xml = await _get_text(XML_BAS.format(ico=ico)) or await _get_text(XML_ICO.format(ico=ico))
    if not xml:
        return None
    try:
        data = xmltodict.parse(xml)
    except ExpatError:
        return None
    odp = data.get("Ares_odpovedi", {}).get("Odpoved", {})
    if odp.get("PZA") != "0":
        return None
    rec = _scan(odp)
    if not rec:
        return None
    return {
        "ico": rec.get("ICO"),
        "name": rec.get("OF"),
        "address": rec.get("AA", ""),
    }

# ---------------- veřejná funkce ----------------
async def fetch_ares(ico: str) -> Optional[dict]:
    return await _fetch_rest(ico) or await _fetch_xml(ico)