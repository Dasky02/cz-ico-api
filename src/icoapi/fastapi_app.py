from fastapi import FastAPI, HTTPException
from icoapi.validators import is_valid_ico, is_valid_dic
from icoapi.ares import fetch_ares
import httpx
from icoapi.vat import check_vat, VatServiceTimeout
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="CZ IČ/DIČ Validator", version="0.1.0")
@app.get("/")              # health-check
def root(): return {"status": "ok"}
@app.get("/validate_ico")
def v_ico(ico: str): return {"ico": ico, "valid": is_valid_ico(ico)}
@app.get("/validate_dic")
def v_dic(dic: str): return {"dic": dic, "valid": is_valid_dic(dic)}
@app.get("/lookup_ico", summary="Company lookup in ARES")
async def lookup(ico: str):
    """Return basic company data (ICO, name, address).
    400 → invalid ICO checksum
    404 → not found in ARES
    502 → ARES service unavailable / network error
    """
    if not is_valid_ico(ico):
        raise HTTPException(400, "Invalid IČO")

    try:
        data = await fetch_ares(ico)
    except httpx.HTTPError as exc:           # network / timeout to ARES
        logger.warning("ARES HTTP error for %s: %s", ico, exc)
        raise HTTPException(502, "ARES service unavailable")
    except Exception as exc:                 # XML parse etc.
        logger.error("ARES processing error for %s: %s", ico, exc)
        raise HTTPException(502, "ARES processing error")

    if not data:
        raise HTTPException(404, "Company not found in ARES")
    return data

@app.get("/check_vat", summary="Validate EU VAT (VIES)")
async def check_vat_endpoint(dic: str):
    # optional local CZ checksum first
    if dic.startswith("CZ") and not is_valid_dic(dic):
        raise HTTPException(400, "Invalid CZ DIČ")
    try:
        return await check_vat(dic)
    except VatServiceTimeout as e:
        # VIES did not respond in time → 504
        raise HTTPException(status_code=504, detail=str(e))
    except (httpx.HTTPError, ValueError) as e:
        # Other client / validation errors → 400
        raise HTTPException(status_code=400, detail=str(e))