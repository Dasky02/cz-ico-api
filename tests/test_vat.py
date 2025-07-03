# tests/test_vat.py
import asyncio, pytest
from icoapi.vat import check_vat, VatServiceTimeout

@pytest.mark.asyncio
async def test_vat_ok():
    try:
        data = await asyncio.wait_for(check_vat("CZ27074358"), timeout=25)
    except VatServiceTimeout:          # VIES server pomalý → přeskoč
        pytest.skip("VIES timeout – skipping")
    assert data["valid"] is True