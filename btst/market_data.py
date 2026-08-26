"""Market-data enrichment: 52-week-high proximity gate + daily technicals + events.

This is the only module that touches pandas / yfinance. It returns market-only candidate
dicts (prices, technicals, events); scoring adds flags/score on top.
"""
from datetime import datetime

import pandas as pd
import yfinance as yf


def compute_technicals(hist, ltp, live_volume):
    """
    Daily technicals derived from the 1y history already fetched for the 52W filter
    (no extra network call). Classic pivot/R1/S1 (last completed session), 20D mean +
    overextension %, ATR%, and volume surge vs the prior 10-day average.
    Every field degrades to None on short/dirty history — the run never depends on it.
    """
    out = {
        "pivot": None, "r1": None, "s1": None, "sma20": None,
        "ext_above_sma20_pct": None, "atr_pct": None, "vol_surge": None,
    }
    try:
        close, high, low, vol = hist["Close"], hist["High"], hist["Low"], hist["Volume"]
        if len(close.dropna()) < 20:
            return out

        # Classic pivots use the last COMPLETED session — drop today's forming candle if present.
        comp = hist
        try:
            if hist.index[-1].date() == datetime.now().date():
                comp = hist.iloc[:-1]
        except Exception:
            pass
        ph, pl, pc = float(comp["High"].iloc[-1]), float(comp["Low"].iloc[-1]), float(comp["Close"].iloc[-1])
        pivot = (ph + pl + pc) / 3.0
        out["pivot"], out["r1"], out["s1"] = round(pivot, 2), round(2 * pivot - pl, 2), round(2 * pivot - ph, 2)

        sma20 = float(close.tail(20).mean())
        out["sma20"] = round(sma20, 2)
        if sma20:
            out["ext_above_sma20_pct"] = round((ltp - sma20) / sma20 * 100, 2)

        prev_close = close.shift()
        tr = pd.concat([(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        atr = float(tr.dropna().tail(14).mean())
        if ltp:
            out["atr_pct"] = round(atr / ltp * 100, 2)

        # Volume surge: live ScanX volume vs the prior 10 sessions (exclude today's partial row).
        avg10 = float(vol.tail(11).iloc[:-1].mean()) if len(vol) >= 11 else float(vol.mean())
        if avg10 and live_volume:
            out["vol_surge"] = round(float(live_volume) / avg10, 2)
    except Exception:
        return out
    return out


def get_next_event(ticker):
    """
    Nearest upcoming ex-dividend / earnings date via yfinance, with gap DIRECTION.
    Best-effort and flag-only: yfinance NSE forward-event data is spotty, so on any gap we
    return None and the stock simply carries no event flag. We exclude nothing on events.
    """
    try:
        cal = ticker.calendar or {}
    except Exception:
        return None
    if not isinstance(cal, dict):
        return None

    today = datetime.now().date()
    raw_events = []
    exd = cal.get("Ex-Dividend Date")
    if exd:
        raw_events.append(("ex_dividend", exd, "gaps down (long forgoes the dividend)"))
    earn = cal.get("Earnings Date")
    for d in (earn if isinstance(earn, list) else [earn] if earn else []):
        raw_events.append(("earnings", d, "two-sided (results volatility)"))

    best = None
    for etype, d, direction in raw_events:
        try:
            days = (d - today).days
        except Exception:
            continue
        if days < 0:
            continue
        if best is None or days < best["days_away"]:
            best = {"type": etype, "date": d.isoformat(), "days_away": days, "direction": direction}
    return best


def _to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def enrich_candidates(headers_list, rows):
    """
    Keep only ScanX rows whose LTP is within 10% of their 52-week high, and attach daily
    technicals + the nearest event. Returns market-only candidate dicts (no flags/score).
    Any per-stock failure skips that stock; the run still produces a Top 5.
    """
    try:
        sym_idx = headers_list.index("Sym")
        ltp_idx = headers_list.index("Ltp")
    except ValueError as e:
        raise RuntimeError(f"Required ScanX field missing: {e}")

    candidates = []
    print(f"\nProcessing {len(rows)} stocks and evaluating 52-week highs via yfinance...")

    for row in rows:
        try:
            sym = str(row[sym_idx]).strip()
            ltp = float(row[ltp_idx])
        except (ValueError, TypeError, IndexError) as e:
            print(f"Skipping malformed row: {e}")
            continue

        rec = dict(zip(headers_list, row))

        try:
            ticker = yf.Ticker(f"{sym}.NS")
            hist = ticker.history(period="1y", auto_adjust=False)

            if hist.empty:
                print(f"No historical data for {sym}")
                continue

            high_series = hist["High"].dropna()
            if high_series.empty:
                print(f"No High series for {sym}")
                continue

            wk52_high = float(high_series.max())

            # FILTER: LTP within 10% of 52-week high
            if ltp < (0.90 * wk52_high):
                continue

            dist_pct = round(((ltp - wk52_high) / wk52_high) * 100, 2)

            # Enrichment (all best-effort; a failure here must not drop the candidate).
            volume = _to_float(rec.get("Volume"))
            technicals = compute_technicals(hist, ltp, volume)
            event = get_next_event(ticker)

            candidate = {
                "symbol": sym,
                "name": str(rec.get("DispSym") or sym).strip(),
                "ltp": ltp,
                "change": _to_float(rec.get("Pchange")),
                "pct_change": _to_float(rec.get("PPerchange")),
                "volume": volume,
                "rsi": _to_float(rec.get("DayRSI14CurrentCandle")) or 0.0,
                "pe": _to_float(rec.get("Pe")),
                "mcap_cr": _to_float(rec.get("Mcap")),
                "open": _to_float(rec.get("Open")),
                "bc_open": _to_float(rec.get("BcOpen")),
                "bc_close": _to_float(rec.get("BcClose")),
                "wk52_high": round(wk52_high, 2),
                "dist_52w_pct": dist_pct,
                "technicals": technicals,
                "next_event": event,
                "event_risk": bool(event and event["days_away"] <= 2),
                "catalyst": "",  # AI fills this per-pick; empty for the rule-based baseline
            }
            candidates.append(candidate)

            print(f"  [PASS] {sym:<12} | LTP: {ltp:>8.2f} | Dist52W: {dist_pct:>6.2f}%")
        except Exception as e:
            print(f"Skipping {sym} due to error: {e}")

    print(f"\n52-Week High filter complete: {len(candidates)} of {len(rows)} stocks passed.")
    return candidates
