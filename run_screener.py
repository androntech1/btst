from datetime import datetime
import json
import requests
import yfinance as yf

# 1. API Endpoint and Payload (matches your original curl)
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
data = response.json()

headers_list = data["headers"]
rows = data["data"]

# Add new column headers for the 52-week high metrics
headers_list.extend(["Calculated52WkHigh", "DistFrom52WkHighPct"])

sym_idx = headers_list.index("Sym")
ltp_idx = headers_list.index("Ltp")

filtered_rows = []

print(f"Processing {len(rows)} stocks and checking 52-week highs via yfinance...")
for row in rows:
  sym = row[sym_idx]
  ltp = row[ltp_idx]
  ticker_symbol = f"{sym}.NS"  # Yahoo Finance NSE format

  try:
    # Fetch 1 year of history to find true 52-week high
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="1y")

    if not hist.empty:
      wk52_high = hist["High"].max()

      # Filter Rule: Stock must be within 10% of its 52-week high (LTP >= 90% of high)
      if ltp >= (0.90 * wk52_high):
        dist_pct = round(((ltp - wk52_high) / wk52_high) * 100, 2)

        # Append new objects/values to the row matching the new headers
        row.append(round(wk52_high, 2))
        row.append(dist_pct)
        filtered_rows.append(row)
  except Exception as e:
    print(f"Skipping {sym} due to error: {e}")

# Update JSON response structure with filtered data
data["data"] = filtered_rows
data["tot_rec"] = len(filtered_rows)

# Generate filename with today's date
today_date = datetime.now().strftime("%Y-%m-%d")
filename = f"data_{today_date}.json"

with open(filename, "w") as f:
  json.dump(data, f, indent=4)

print(
    f"Successfully saved {len(filtered_rows)} matching stocks to {filename}"
)
