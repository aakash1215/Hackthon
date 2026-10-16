"""Corroboration level per confirmed workday (BUILD_PLAN §6). Pure and deterministic.

Signals:
  SELF          the worker's confirmed entry (always present)
  PHOTO         a photo taken on that date
  GPS_AT_SITE   an entry or photo fix taken on that date, within 300 m of the site point, accuracy <= 100 m
  COWORKER      a confirmed, consented co-worker confirmation covers the date
  THEKEDAR_ACK  a worker-confirmed thekedar statement (recording or Telegram) that acknowledges the days
Flag:
  THEKEDAR_DISPUTES  the thekedar disputes the days or counts fewer days; shown, never hidden

Levels: L1 worker's record · L2 + on-site evidence (PHOTO or GPS_AT_SITE) · L3 + another person
(COWORKER or THEKEDAR_ACK). "How much of this day is backed by more than the worker's word: not a legal score."

A fix or photo only counts for the date it was taken on: a note recorded the next morning about
"yesterday" says nothing about where the worker was yesterday.
"""
from __future__ import annotations

import math

SITE_RADIUS_M = 300
MAX_ACCURACY_M = 100
ACK_INTENTS = {"acknowledges", "promise_to_pay"}
DISPUTE_INTENTS = {"disputes_days"}

LEVEL_LABEL = {
    1: {"en": "Worker's record", "hi": "अपना रिकॉर्ड"},
    2: {"en": "+ on-site evidence", "hi": "+ साइट पर सबूत"},
    3: {"en": "+ another person", "hi": "+ दूसरे व्यक्ति से"},
}
DISCLAIMER = {
    "en": "How much of this day is backed by more than the worker's word: not a legal score.",
    "hi": "यह दिन आपकी बात के अलावा और किन चीज़ों से जुड़ा है — यह क़ानूनी स्कोर नहीं है।",
}


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres (haversine)."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def at_site(fix: dict, site: dict | None) -> bool:
    if not site or site.get("lat") is None or site.get("lon") is None:
        return False
    if fix.get("lat") is None or fix.get("lon") is None:
        return False
    acc = fix.get("acc")
    if acc is None or acc > MAX_ACCURACY_M:
        return False
    return distance_m(fix["lat"], fix["lon"], site["lat"], site["lon"]) <= SITE_RADIUS_M


def thekedar_window(days: list[str], rec_day: str) -> list[str]:
    """The days a thekedar statement speaks about: confirmed days in the same month, up to the statement date."""
    return [d for d in days if d[:7] == rec_day[:7] and d <= rec_day]


def compute_levels(
    days: list[str],
    *,
    site: dict | None = None,
    photos: list[dict] | None = None,
    fixes: list[dict] | None = None,
    coworker: list[dict] | None = None,
    thekedar: list[dict] | None = None,
) -> dict[str, dict]:
    """Return {day: {level, label, signals, flags, refs}} for each confirmed workday date (ISO).

    photos/fixes: [{day, lat, lon, acc, ref}]  (day = date the photo/fix was taken)
    coworker:     [{dates: [iso...], name, ref}]  (confirmed + consented only)
    thekedar:     [{rec_day, days_counted, intent, ref}]  (worker-confirmed statements only)
    """
    out: dict[str, dict] = {d: {"signals": ["SELF"], "flags": [], "refs": {}} for d in sorted(set(days))}

    def add(day: str, signal: str, ref: str | None) -> None:
        o = out.get(day)
        if o is None:
            return
        if signal not in o["signals"] and signal not in o["flags"]:
            (o["flags"] if signal == "THEKEDAR_DISPUTES" else o["signals"]).append(signal)
        if ref:
            o["refs"].setdefault(signal, []).append(ref)

    for p in photos or []:
        add(p["day"], "PHOTO", p.get("ref"))
        if at_site(p, site):
            add(p["day"], "GPS_AT_SITE", p.get("ref"))
    for f in fixes or []:
        if at_site(f, site):
            add(f["day"], "GPS_AT_SITE", f.get("ref"))
    for c in coworker or []:
        for d in c.get("dates") or []:
            add(d, "COWORKER", c.get("ref"))
    all_days = list(out)
    for t in thekedar or []:
        window = thekedar_window(all_days, t["rec_day"])
        if not window:
            continue
        n = t.get("days_counted")
        intent = t.get("intent")
        if intent in DISPUTE_INTENTS or (n is not None and n < len(window)):
            signal = "THEKEDAR_DISPUTES"
        elif intent in ACK_INTENTS or (n is not None and n >= len(window)):
            signal = "THEKEDAR_ACK"
        else:
            continue
        for d in window:
            add(d, signal, t.get("ref"))

    for o in out.values():
        s = set(o["signals"])
        level = 3 if s & {"COWORKER", "THEKEDAR_ACK"} else 2 if s & {"PHOTO", "GPS_AT_SITE"} else 1
        o["level"] = level
        o["label"] = LEVEL_LABEL[level]
    return out
