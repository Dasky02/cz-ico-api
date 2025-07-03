from fastapi import FastAPI, HTTPException
from icoapi.validators import is_valid_ico, is_valid_dic
from icoapi.ares import fetch_ares
import httpx
from icoapi.vat import check_vat, VatServiceTimeout
app = FastAPI(title="CZ IČ/DIČ Validator", version="0.1.0")
@app.get("/")              # health-check
def root(): return {"status": "ok"}
@app.get("/validate_ico")
def v_ico(ico: str): return {"ico": ico, "valid": is_valid_ico(ico)}
@app.get("/validate_dic")
def v_dic(dic: str): return {"dic": dic, "valid": is_valid_dic(dic)}
@app.get("/lookup_ico")
async def lookup(ico: str):
    if not is_valid_ico(ico):
        raise HTTPException(400, "Invalid IČO")
    data = await fetch_ares(ico)
    if not data:
        raise HTTPException(404, "Company not found")
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