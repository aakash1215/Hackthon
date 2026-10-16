"""Deterministic normalizer for Hindi, Marathi and Hinglish text (Handoff §10.5).

Pure functions, no model calls. Matching runs on the original string, so every `span`
is an exact substring of the input. Only the lookup keys are normalised (nukta,
chandrabindu, Devanagari digits, case).

Coverage: Hindi cardinals 0–99, Marathi 0–50 and round tens. Other compounds fall through
to the LLM reader, and the reconciler then shows the field as amber/red.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta

_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_TOKEN = re.compile(r"\d[\d,]*(?::\d{2})?|[ऀ-ॣ०-ॿ]+|[A-Za-z]+|₹")


def key(s: str) -> str:
    """Lookup key: drop nukta, chandrabindu -> anusvara, Devanagari digits -> ASCII, lowercase."""
    s = unicodedata.normalize("NFD", s).replace("़", "").replace("ँ", "ं")
    return unicodedata.normalize("NFC", s).translate(_DIGITS).lower()


def _table(text: str) -> dict[str, int]:
    parts = text.split()
    return {key(w): int(n) for w, n in zip(parts[::2], parts[1::2])}


_HI = _table(
    "शून्य 0 एक 1 दो 2 तीन 3 चार 4 पांच 5 छह 6 सात 7 आठ 8 नौ 9 दस 10 ग्यारह 11 बारह 12 "
    "तेरह 13 चौदह 14 पंद्रह 15 सोलह 16 सत्रह 17 अठारह 18 उन्नीस 19 बीस 20 इक्कीस 21 बाईस 22 "
    "तेईस 23 चौबीस 24 पच्चीस 25 छब्बीस 26 सत्ताईस 27 अट्ठाईस 28 उनतीस 29 तीस 30 इकतीस 31 "
    "बत्तीस 32 तैंतीस 33 चौंतीस 34 पैंतीस 35 छत्तीस 36 सैंतीस 37 अड़तीस 38 उनतालीस 39 चालीस 40 "
    "इकतालीस 41 बयालीस 42 तैंतालीस 43 चवालीस 44 पैंतालीस 45 छियालीस 46 सैंतालीस 47 अड़तालीस 48 "
    "उनचास 49 पचास 50 इक्यावन 51 बावन 52 तिरेपन 53 चौवन 54 पचपन 55 छप्पन 56 सत्तावन 57 "
    "अट्ठावन 58 उनसठ 59 साठ 60 इकसठ 61 बासठ 62 तिरसठ 63 चौंसठ 64 पैंसठ 65 छियासठ 66 सड़सठ 67 "
    "अड़सठ 68 उनहत्तर 69 सत्तर 70 इकहत्तर 71 बहत्तर 72 तिहत्तर 73 चौहत्तर 74 पचहत्तर 75 छिहत्तर 76 "
    "सतहत्तर 77 अठहत्तर 78 उन्यासी 79 अस्सी 80 इक्यासी 81 बयासी 82 तिरासी 83 चौरासी 84 पचासी 85 "
    "छियासी 86 सतासी 87 अट्ठासी 88 नवासी 89 नब्बे 90 इक्यानवे 91 बानवे 92 तिरानवे 93 चौरानवे 94 "
    "पचानवे 95 छियानवे 96 सत्तानवे 97 अट्ठानवे 98 निन्यानवे 99"
)
_MR = _table(
    "शून्य 0 एक 1 दोन 2 तीन 3 चार 4 पाच 5 सहा 6 सात 7 आठ 8 नऊ 9 दहा 10 अकरा 11 बारा 12 "
    "तेरा 13 चौदा 14 पंधरा 15 सोळा 16 सतरा 17 अठरा 18 एकोणीस 19 वीस 20 एकवीस 21 बावीस 22 "
    "तेवीस 23 चोवीस 24 पंचवीस 25 सव्वीस 26 सत्तावीस 27 अठ्ठावीस 28 एकोणतीस 29 तीस 30 एकतीस 31 "
    "बत्तीस 32 तेहतीस 33 चौतीस 34 पस्तीस 35 छत्तीस 36 सदतीस 37 अडतीस 38 एकोणचाळीस 39 चाळीस 40 "
    "एक्केचाळीस 41 बेचाळीस 42 त्रेचाळीस 43 चव्वेचाळीस 44 पंचेचाळीस 45 सेहेचाळीस 46 सत्तेचाळीस 47 "
    "अठ्ठेचाळीस 48 एकोणपन्नास 49 पन्नास 50 साठ 60 सत्तर 70 ऐंशी 80 नव्वद 90"
)
_NUM = {**_MR, **_HI}
_MULT_HUNDRED = {key(w) for w in ("सौ", "सो", "शंभर", "शंबर")}
_MULT_THOUSAND = {key("हजार")}
_CURRENCY = {key(w) for w in ("रुपये", "रुपए", "रुपया", "रु", "रू", "rs", "₹")}
_PART = {
    key(w): p
    for p, words in {
        "am": ("सुबह", "सवेरे", "सकाळी", "सकाळ"),
        "noon": ("दोपहर", "दुपारी", "दुपार"),
        "pm": ("शाम", "संध्याकाळी", "संध्याकाळ", "सायंकाळी", "सायंकाळ"),
        "night": ("रात", "रात्री", "रात्र"),
    }.items()
    for w in words
}
_MOD = {
    key("सवा"): 0.25, key("सव्वा"): 0.25,
    key("साढ़े"): 0.5, key("साढे"): 0.5, key("साडे"): 0.5,
    key("पौने"): -0.25, key("पावणे"): -0.25,
}
_ABS = {key("डेढ़"): 1.5, key("डेढ"): 1.5, key("दीड"): 1.5, key("ढाई"): 2.5, key("अडीच"): 2.5}
_TIME_WORDS = {key(w) for w in ("बजे", "बजकर", "वाजता", "वाजले", "वाजून", "वाजत")}
_CONNECT = {key(w) for w in ("से", "ते", "पासून")}
_DAY_WORD = {key(w) for w in ("तारीख", "तारखेला", "तारखेस")}


@dataclass(frozen=True)
class _Tok:
    text: str
    start: int
    end: int
    k: str


def _tokens(s: str) -> list[_Tok]:
    return [_Tok(m.group(), m.start(), m.end(), key(m.group())) for m in _TOKEN.finditer(s)]


def _num(k: str) -> float | None:
    """A single numeric token: digits, 'H:MM', or a Hindi/Marathi cardinal."""
    k2 = k.replace(",", "")
    if re.fullmatch(r"\d+", k2):
        return float(int(k2))
    m = re.fullmatch(r"(\d+):(\d{2})", k2)
    if m:
        return int(m[1]) + int(m[2]) / 60
    return float(_NUM[k]) if k in _NUM else None


def _hour(h: float, part: str | None) -> tuple[int, int]:
    hour = int(h)
    minute = round((h - hour) * 60)
    if minute == 60:
        hour, minute = hour + 1, 0
    if part == "am":
        hour = 0 if hour == 12 else hour
    elif part == "noon":
        hour = hour + 12 if 1 <= hour <= 4 else hour
    elif part == "pm":
        hour = hour + 12 if hour < 12 else hour
    elif part == "night":
        if 8 <= hour <= 11:
            hour += 12
        elif hour == 12:
            hour = 0
    return hour % 24, minute


def _fmt(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def _mention(text: str, toks: list[_Tok], s: int, i: int, hval: float, part: str | None) -> dict:
    hh, mm = _hour(hval, part)
    if part is not None:
        status = "stated"
    elif 1 <= int(hval) <= 6:
        # A bare hour of 1–6 is almost always an afternoon or evening shift, but the worker must check it.
        hh, status = (hh + 12) % 24, "ambiguous"
    elif 7 <= int(hval) <= 11:
        status = "inferred"  # taken as morning
    else:
        status = "stated"
    return {"value": _fmt(hh, mm), "status": status, "span": text[toks[s].start:toks[i].end]}


def _resolve_end(start: str, end_h: int, text: str, span: str) -> dict:
    """Bare end hour ('7' in '9 से 7'): choose 7:00 or 19:00 so the shift lasts 1–16 h. Always inferred."""
    sh, sm = (int(x) for x in start.split(":"))
    cands = [end_h, end_h + 12] if 1 <= end_h <= 11 else [end_h]
    for c in cands:
        diff = (c * 60) - (sh * 60 + sm)
        if 60 <= diff <= 16 * 60:
            return {"value": _fmt(c, 0), "status": "inferred", "span": span}
    return {"value": _fmt(cands[0], 0), "status": "inferred", "span": span}


def _times(text: str) -> list[dict]:
    """Time mentions in order of appearance. Each is {value 'HH:MM', status, span}."""
    toks = _tokens(text)
    n = len(toks)
    found: list[tuple[int, dict]] = []  # (token index, mention)
    covered: set[int] = set()

    # 1. Hour + time word: [part] [modifier] hour (बजे|वाजता|...)
    for i, t in enumerate(toks):
        if t.k not in _TIME_WORDS or i < 1:
            continue
        j = i - 1
        if toks[j].k in _ABS:
            hval, s = _ABS[toks[j].k], j
        else:
            hval = _num(toks[j].k)
            if hval is None or j in covered:
                continue
            s = j
            if s - 1 >= 0 and toks[s - 1].k in _MOD:
                hval, s = hval + _MOD[toks[s - 1].k], s - 1
        part = None
        if s - 1 >= 0 and toks[s - 1].k in _PART:
            part, s = _PART[toks[s - 1].k], s - 1
        m = _mention(text, toks, s, i, hval, part)
        # "9 से 7 बजे": a bare start hour before the connector makes this mention the range end.
        if part is None and s - 2 >= 0 and toks[s - 1].k in _CONNECT and _num(toks[s - 2].k) is not None                 and toks[s - 2].k not in _TIME_WORDS:
            s_part = _PART.get(toks[s - 3].k) if s - 3 >= 0 else None
            start = _mention(text, toks, s - 2, s - 2, _num(toks[s - 2].k), s_part)
            if s_part is not None:
                start["status"] = "stated"
            found.append((s - 2, start))
            covered.update({s - 2, s - 1})
            m = _resolve_end(start["value"], int(hval), text, text[toks[s].start:toks[i].end])
        found.append((s, m))
        covered.update(range(s, i + 1))

    # 2. Bare range without a time word: "9 से 7". Skipped when a time word follows the second number.
    for idx in range(n - 2):
        if idx in covered or idx + 1 in covered or idx + 2 in covered:
            continue
        a, c, b = toks[idx], toks[idx + 1], toks[idx + 2]
        if c.k not in _CONNECT or _num(a.k) is None or _num(b.k) is None:
            continue
        if a.k in _TIME_WORDS or b.k in _TIME_WORDS or (idx + 3 < n and toks[idx + 3].k in _TIME_WORDS):
            continue
        a_part = _PART.get(toks[idx - 1].k) if idx >= 1 else None
        start = _mention(text, toks, idx, idx, _num(a.k), a_part)
        if a_part is not None:
            start["status"] = "stated"
        found.append((idx, start))
        found.append((idx + 2, _resolve_end(start["value"], int(_num(b.k)), text, text[a.start:b.end])))
        covered.update({idx, idx + 1, idx + 2})

    found.sort(key=lambda p: p[0])
    return [m for _, m in found]


def _money_value(keys: list[str]) -> int | None:
    total, cur = 0, 0
    if not keys:
        return None
    for k in keys:
        if k.replace(",", "").isdigit():
            cur += int(k.replace(",", ""))
        elif k in _NUM:
            cur += _NUM[k]
        elif k in _MULT_HUNDRED:
            cur = (cur or 1) * 100
        elif k in _MULT_THOUSAND:
            total += (cur or 1) * 1000
            cur = 0
        elif k.endswith(key("शे")) and key(k[:-2]) in _NUM:  # fused hundreds: पाचशे = 500
            cur += _NUM[key(k[:-2])] * 100
        else:
            return None
    return total + cur


def _is_numeric(k: str) -> bool:
    return k.replace(",", "").isdigit() or k in _NUM or k in _MULT_HUNDRED or k in _MULT_THOUSAND or (
        k.endswith(key("शे")) and key(k[:-2]) in _NUM
    )


def _money(text: str) -> list[dict]:
    """Amounts followed (or, for '₹ 500' / 'रु 500', preceded) by a rupee word."""
    toks = _tokens(text)
    out: list[dict] = []
    for c, t in enumerate(toks):
        if t.k not in _CURRENCY:
            continue
        back: list[_Tok] = []
        j = c - 1
        while j >= 0 and _is_numeric(toks[j].k):
            back.insert(0, toks[j])
            j -= 1
        run, span = back, None
        if run:
            span = text[run[0].start:t.end]
        else:
            fwd: list[_Tok] = []
            j = c + 1
            while j < len(toks) and _is_numeric(toks[j].k):
                fwd.append(toks[j])
                j += 1
            run = fwd
            if run:
                span = text[t.start:run[-1].end]
        if not run:
            continue
        value = _money_value([r.k for r in run])
        if value is not None:
            out.append({"value": value, "status": "stated", "span": span})
    return out


def _dates(text: str, rec: date) -> list[dict]:
    toks = _tokens(text)
    out: list[dict] = []
    for idx, t in enumerate(toks):
        if t.k == key("आज"):
            out.append({"value": rec.isoformat(), "status": "stated", "span": t.text})
        elif t.k == key("काल"):  # Marathi 'काल' = yesterday
            out.append({"value": (rec - timedelta(days=1)).isoformat(), "status": "stated", "span": t.text})
        elif t.k == key("कल"):  # Hindi 'कल' = yesterday or tomorrow
            out.append({"value": (rec - timedelta(days=1)).isoformat(), "status": "ambiguous", "span": t.text})
        elif t.k in (key("परसों"), key("परवा")):
            out.append({"value": (rec - timedelta(days=2)).isoformat(), "status": "ambiguous", "span": t.text})
        elif t.k in _DAY_WORD and idx >= 1:
            n = _num(toks[idx - 1].k)
            if n is None or not 1 <= n <= 31:
                continue
            day = int(n)
            try:
                d = date(rec.year, rec.month, day) if rec.day >= day else _prev_month_day(rec, day)
            except ValueError:
                continue
            out.append({"value": d.isoformat(), "status": "inferred", "span": text[toks[idx - 1].start:t.end]})
    return out


def _prev_month_day(rec: date, day: int) -> date:
    first = date(rec.year, rec.month, 1)
    prev_last = first - timedelta(days=1)
    return date(prev_last.year, prev_last.month, day)


def normalize(text: str, rec: date) -> dict:
    """Candidate fields for a transcript. Keys: work_date/payment_date, start_time, end_time, amount_paid."""
    out: dict[str, dict] = {}
    dates = _dates(text, rec)
    if dates:
        out["work_date"] = dates[0]
        out["payment_date"] = dict(dates[0])
    times = _times(text)
    if times:
        out["start_time"] = times[0]
    if len(times) >= 2:
        out["end_time"] = times[1]
    amounts = _money(text)
    if amounts:
        out["amount_paid"] = amounts[0]
    return out


# --- Canonical parsing of LLM values, so they can be compared with normalizer values ---

def parse_clock(value) -> str | None:
    if value in (None, ""):
        return None
    s = str(value).strip()
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?\s*[Mm]\.?", s)
    if m:
        h, mi = int(m[1]), int(m[2] or 0)
        if m[3].lower() == "p" and h < 12:
            h += 12
        if m[3].lower() == "a" and h == 12:
            h = 0
        return _fmt(h, mi) if h < 24 and mi < 60 else None
    m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", s)
    if m and int(m[1]) < 24 and int(m[2]) < 60:
        return _fmt(int(m[1]), int(m[2]))
    times = _times(s)
    return times[0]["value"] if times else None


def parse_money(value) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value)
    m = re.search(r"\d[\d,]*", key(s))
    if m:
        return int(m.group().replace(",", ""))
    nums = [t.k for t in _tokens(s) if _is_numeric(t.k)]
    return _money_value(nums)


def parse_date(value, rec: date) -> str | None:
    if value in (None, ""):
        return None
    s = str(value)
    m = re.search(r"\d{4}-\d{2}-\d{2}", s)
    if m:
        try:
            return date.fromisoformat(m.group()).isoformat()
        except ValueError:
            return None
    dates = _dates(s, rec)
    return dates[0]["value"] if dates else None
