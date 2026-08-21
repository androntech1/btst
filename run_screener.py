from datetime import datetime
import json
import copy
import requests
import yfinance as yf

# 1. API Endpoint and Payload
url = "https://ow-scanx-analytics.dhan.co/customscan/v2/fetchdt"
api_headers = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://scanx.trade",
}
payload = {
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
                {"field": "Exch", "op": "eq", "val": "NSE"},
                {
                    "field": "Volume",
                    "op": "gte",
                    "field2": "DaySMA10VolMul_2",
                    "val": "",
                },
                {"field": "Open", "op": "gt", "field2": "BcOpen", "val": ""},
                {"field": "Ltp", "op": "gt", "field2": "BcClose", "val": ""},
                {"field": "DayRSI14CurrentCandle", "op": "gte", "val": "65"},
                {"field": "OgInst", "op": "eq", "val": "ES"},
                {"field": "Volume", "op": "gte", "val": "0"},
            ],
        },
    }
}

print("Fetching data from ScanX API...")
response = requests.post(url, headers=api_headers, json=payload)
raw_data = response.json()

# Preserve a deep copy of the raw original response
original_data = copy.deepcopy(raw_data)

headers_list = raw_data["headers"]
rows = raw_data["data"]

# Add new column headers for the 52-week high metrics to the filtered data schema
filtered_headers = list(headers_list)
filtered_headers.extend(["Calculated52WkHigh", "DistFrom52WkHighPct"])

sym_idx = headers_list.index("Sym")
ltp_idx = headers_list.index("Ltp")

filtered_rows = []
filtered_symbols = []

print(f"Processing {len(rows)} stocks and checking 52-week highs via yfinance...")
for row in rows:
  sym = row[sym_idx]
  ltp = row[ltp_idx]
  ticker_symbol = f"{sym}.NS"

  try:
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="1y")

    if not hist.empty:
      wk52_high = hist["High"].max()

      # Filter Rule: Stock must be within 10% of its 52-week high
      if ltp >= (0.90 * wk52_high):
        dist_pct = round(((ltp - wk52_high) / wk52_high) * 100, 2)

        # Create a new row with the calculated fields appended
        new_row = list(row)
        new_row.append(round(wk52_high, 2))
        new_row.append(dist_pct)
        filtered_rows.append(new_row)
        filtered_symbols.append(sym)
  except Exception as e:
    print(f"Skipping {sym} due to error: {e}")

# Build structured filtered response object
filtered_data = copy.deepcopy(raw_data)
filtered_data["headers"] = filtered_headers
filtered_data["data"] = filtered_rows
filtered_data["tot_rec"] = len(filtered_rows)

# Create the master output dictionary combining all three requested segments
master_output = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "original_scanx_results": original_data,
    "filtered_52w_results": filtered_data,
    "filtered_symbols": filtered_symbols,
}

# Generate filename with today's date
today_date = datetime.now().strftime("%Y-%m-%d")
filename = f"data_{today_date}.json"

with open(filename, "w") as f:
  json.dump(master_output, f, indent=4)

print(
    f"Successfully saved master JSON file ({filename}) with original data,"
    f" filtered data, and {len(filtered_symbols)} symbols."
)
