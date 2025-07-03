import httpx, xmltodict, asyncio # type: ignore
URL = "https://wwwinfo.mfcr.cz/cgi-bin/ares/darv_bas.cgi?ico={ico}&xml=1"
async def fetch_ares(ico: str) -> dict | None:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(URL.format(ico=ico))
        r.raise_for_status()
    data = xmltodict.parse(r.text)
    try:
        rec = data["Ares_odpovedi"]["Odpoved"]["VBAS"]
        return {"ico": rec["ICO"], "name": rec["OF"], "address": rec.get("AA", "")}
    except KeyError:
        return None
