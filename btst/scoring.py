"""Deterministic rule-based scoring, risk flags, and Top-5 selection for a next-day hold."""


def build_flags(candidate):
    """Concrete, human-readable risk flags for the overnight hold. Informational — never exclusion."""
    flags = []
    tech = candidate["technicals"]

    if candidate["rsi"] >= 80:
        flags.append(f"Overbought RSI {candidate['rsi']:.0f}")

    ext = tech.get("ext_above_sma20_pct")
    if ext is not None and ext > 15:
        flags.append(f"Extended +{ext:.0f}% above 20D avg")

    pe = candidate.get("pe")
    if pe is not None and pe < 0:
        flags.append("Loss-making (negative PE)")
    elif pe is not None and pe > 100:
        flags.append(f"Very high PE {pe:.0f}")

    event = candidate.get("next_event")
    if candidate.get("event_risk") and event:
        label = event["type"].replace("_", " ").title()
        flags.append(f"{label} in {event['days_away']}d — {event['direction']}")

    return flags


def score_candidate(candidate):
    """
    Rule-based composite for a 1-DAY (BTST) hold: probability/magnitude of a favorable
    move tomorrow. Equal-weight average of four 0..1 terms, then a mild fundamentals gate.

    ponytail: equal weights are a HEURISTIC, deliberately NOT fitted to historical returns
    (curve-fitting a 1-day edge overfits). Few, economically-justified terms only. Retune
    weights ONLY with forward-tested evidence, never by optimizing on past data.
    """
    def clamp01(x):
        return max(0.0, min(1.0, x))

    tech = candidate["technicals"]

    # 1. Proximity to 52W high: leadership → follow-through odds. At high=1.0, at -10% edge=0.0.
    proximity = clamp01(1 - abs(candidate["dist_52w_pct"]) / 10.0)
    # 2. Volume surge: real demand behind the move. 2x (filter floor)=0.0, >=8x=1.0.
    surge = tech.get("vol_surge")
    volume = clamp01((surge - 2) / 6.0) if surge else 0.5
    # 3. RSI health: 65..78 healthy=1.0; >78 decays to 0 by 92 (penalize blow-off that gaps down).
    rsi = candidate["rsi"]
    rsi_health = 1.0 if rsi <= 78 else clamp01(1 - (rsi - 78) / 14.0)
    # 4. Not overextended: at/below 20D mean=1.0, +20% above=0.0 (stretched moves revert overnight).
    ext = tech.get("ext_above_sma20_pct")
    not_extended = clamp01(1 - ext / 20.0) if ext is not None else 0.5

    composite = (proximity + volume + rsi_health + not_extended) / 4.0

    # Fundamentals = quality GATE, not a rank term (quarterly data can't time a 1-day move):
    # a mild haircut for losses / absurd valuation, never exclusion.
    pe = candidate.get("pe")
    gate = 1.0
    if pe is not None and pe < 0:
        gate = 0.85
    elif pe is not None and pe > 100:
        gate = 0.92

    return round(composite * gate * 100, 1)


def rank(candidates):
    """Attach flags + score to each candidate in place, sort, and return the rule-based Top 5.

    Sort order: score descending, then proximity to the 52W high as the tie-break.
    """
    for c in candidates:
        c["flags"] = build_flags(c)
        c["score"] = score_candidate(c)
    candidates.sort(key=lambda c: (-c["score"], abs(c["dist_52w_pct"])))
    return candidates[:5]


if __name__ == "__main__":
    base = {
        "rsi": 70, "pe": 20, "dist_52w_pct": -2.0,
        "technicals": {"vol_surge": 4.0, "ext_above_sma20_pct": 5.0},
        "next_event": None, "event_risk": False,
    }
    healthy = score_candidate(base)
    assert 0 <= healthy <= 100, healthy
    # A loss-making name gets a haircut vs an otherwise identical profitable one.
    loss = dict(base, pe=-5)
    assert score_candidate(loss) < healthy
    assert any("Loss-making" in f for f in build_flags(loss))
    # rank() sorts by score: a strong candidate outranks a blown-off, overextended one.
    weak = dict(base, rsi=90, technicals={"vol_surge": 2.0, "ext_above_sma20_pct": 25.0})
    top = rank([weak, base])
    assert top[0] is base and top[0]["score"] > top[1]["score"]
    print("scoring self-check OK")
