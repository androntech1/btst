"""ScanX (Dhan) universe fetch + the server-side momentum query."""
import requests

SCANX_URL = "https://ow-scanx-analytics.dhan.co/customscan/v2/fetchdt"

SCANX_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://scanx.trade",
}


# The momentum filter runs SERVER-SIDE inside this query, not in Python: NSE equity segment,
# Volume >= 2x the 10-day average volume, positive open action (Open > BcOpen), positive
# close action (Ltp > BcClose), and RSI(14) >= 65. Change the screen here.
SCANX_PAYLOAD = {
    "data": {
        "count": 100,
        "sort": "Mcap",
        "sorder": "desc",
        "fields": [
            "DispSym",
            "Ltp",
            "Pchange",
            "PPerchange",
            "Volume",
            "Pe",
            "Mcap",
            "Open",
            "BcOpen",
            "BcClose",
            "DayRSI14CurrentCandle",
            "Sym",
        ],
        "pgno": 1,
        "query": {
            "logic_op": "AND",
            "params": [
                {
                    "field": "Exch",
                    "op": "eq",
                    "val": "NSE",
                },
                {
                    "field": "Volume",
                    "op": "gte",
                    "field2": "DaySMA10VolMul_2",
                    "val": "",
                },
                {
                    "field": "Open",
                    "op": "gt",
                    "field2": "BcOpen",
                    "val": "",
                },
                {
                    "field": "Ltp",
                    "op": "gt",
                    "field2": "BcClose",
                    "val": "",
                },
                {
                    "field": "DayRSI14CurrentCandle",
                    "op": "gte",
                    "val": "65",
                },
                {
                    "field": "OgInst",
                    "op": "eq",
                    "val": "ES",
                },
                {
                    "field": "Volume",
                    "op": "gte",
                    "val": "0",
                },
            ],
        },
    }
}


def fetch_universe():
    """POST the momentum query to ScanX; return ``(headers_list, rows, raw_response)``.

    ``raw_response`` is the untouched JSON (saved verbatim for audit); rows are never mutated
    downstream, so no defensive copy is needed.
    """
    response = requests.post(SCANX_URL, headers=SCANX_HEADERS, json=SCANX_PAYLOAD, timeout=60)
    if not response.ok:
        raise RuntimeError(f"ScanX API request failed (HTTP {response.status_code}):\n{response.text}")

    raw = response.json()
    if "headers" not in raw or "data" not in raw:
        raise RuntimeError("ScanX response missing required 'headers' or 'data' fields.")

    return raw["headers"], raw["data"], raw
