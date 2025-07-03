import asyncio, datetime
from functools import lru_cache

from zeep import AsyncClient, helpers
from zeep.transports import AsyncTransport
import httpx

WSDL = "https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl"
TIMEOUT = 20  # s

# ───────────────────────────────────────────────────────────────
class VatServiceTimeout(Exception):
    """Raised when VIES does not respond within TIMEOUT seconds."""
# ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=128)                   # jednoduchá 1h cache
def _get_client() -> AsyncClient:
    return AsyncClient(
        WSDL,
        transport=AsyncTransport(
            client=httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT))
        ),
    )

async def check_vat(dic: str) -> dict:
    if len(dic) < 4:
        raise ValueError("DIČ too short")

    country, number = dic[:2], dic[2:]
    client = _get_client()

    try:
        resp = await client.service.checkVat(
            countryCode=country,
            vatNumber=number,
        )
    except httpx.ReadTimeout as exc:
        # převeď na naši doménovou výjimku
        raise VatServiceTimeout(f"VIES timeout ({TIMEOUT}s)") from exc

    data = helpers.serialize_object(resp)
    return {
        "dic":          dic,
        "valid":        data["valid"],
        "trader_name":  data.get("name") or None,
        "country_code": data["countryCode"],
        "request_date": data["requestDate"].strftime("%Y-%m-%d"),
    }

# CLI quick test
if __name__ == "__main__":
    print(asyncio.run(check_vat("CZ27074358")))