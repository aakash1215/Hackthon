"""Rate-pack loader and resolver.

A rate pack is a JSON file with a validity window, provenance and a
verification status. The resolver never invents a rate: if the context is
incomplete or the date is outside every pack's window it returns an error code.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from pathlib import Path

RATE_PACK_DIR = Path(__file__).resolve().parent.parent / "rate_packs"

CATEGORIES = ("unskilled", "semi_skilled", "skilled", "highly_skilled")


@dataclass(frozen=True)
class RatePack:
    pack_id: str
    sphere: str
    state: str | None
    employment_sn: int | None
    effective_from: date
    effective_to: date
    unit: str
    rates: dict
    daily_divisor: int
    normal_hours: int
    ot_multiplier: int
    conversion_status: str
    source: dict
    sha256: str
    raw: dict

    def covers(self, d: date) -> bool:
        return self.effective_from <= d <= self.effective_to

    def provenance(self) -> dict:
        return {
            "pack_id": self.pack_id,
            "notification_no": self.source.get("notification_no"),
            "notification_date": self.source.get("date"),
            "issuer": self.source.get("issuer"),
            "documents": self.source.get("documents", []),
            "verification_status": self.source.get("verification_status"),
            "valid_from": self.effective_from.isoformat(),
            "valid_to": self.effective_to.isoformat(),
            "unit": self.unit,
            "daily_divisor": self.daily_divisor,
            "normal_hours": self.normal_hours,
            "conversion_status": self.conversion_status,
            "pack_sha256": self.sha256,
        }


@dataclass(frozen=True)
class RateContext:
    """Everything needed to pick a rate. Each item must be confirmed by the worker."""
    sphere: str | None          # 'state' | 'central' | 'unknown' | None
    state: str | None           # e.g. 'Maharashtra'
    employment_sn: int | None   # scheduled employment serial no. (11 = construction)
    category: str | None        # one of CATEGORIES
    zone: str | None            # 'I'|'II'|'III' (state) or 'A'|'B'|'C' (central)
    zone_confirmed: bool = True
    piece_rated: bool = False


@dataclass(frozen=True)
class ResolvedRate:
    daily_min: Fraction
    pack: RatePack
    category_used: str
    zone: str
    components: dict


class RateError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


def _load_pack(path: Path) -> RatePack:
    data = path.read_bytes()
    raw = json.loads(data.decode("utf-8"))
    conv = raw.get("conversion", {})
    return RatePack(
        pack_id=raw["pack_id"],
        sphere=raw["sphere"],
        state=raw.get("state"),
        employment_sn=(raw.get("employment") or {}).get("sn"),
        effective_from=date.fromisoformat(raw["effective_from"]),
        effective_to=date.fromisoformat(raw["effective_to"]),
        unit=raw["unit"],
        rates=raw["rates"],
        daily_divisor=int(conv.get("daily_divisor", 26)),
        normal_hours=int(conv.get("normal_hours", 8)),
        ot_multiplier=int(conv.get("ot_multiplier", 2)),
        conversion_status=conv.get("status", "UNKNOWN"),
        source=raw.get("source", {}),
        sha256=hashlib.sha256(data).hexdigest(),
        raw=raw,
    )


def load_packs(directory: Path = RATE_PACK_DIR) -> list[RatePack]:
    return [_load_pack(p) for p in sorted(directory.glob("*.json"))]


def check_context(ctx: RateContext) -> None:
    """Raise the first blocking error for an incomplete rate context."""
    if ctx.piece_rated:
        raise RateError("PIECE_RATE_UNSUPPORTED")
    if ctx.sphere not in ("state", "central"):
        raise RateError("SPHERE_UNKNOWN")
    if ctx.category not in CATEGORIES:
        raise RateError("CATEGORY_UNKNOWN")
    if not ctx.zone or not ctx.zone_confirmed:
        raise RateError("ZONE_UNCONFIRMED")


def resolve(ctx: RateContext, d: date, packs: list[RatePack]) -> ResolvedRate:
    check_context(ctx)
    candidates = [
        p for p in packs
        if p.sphere == ctx.sphere
        and (ctx.sphere == "central" or p.state == ctx.state)
        and (ctx.employment_sn is None or p.employment_sn in (None, ctx.employment_sn))
    ]
    if not candidates:
        raise RateError("RATE_NOT_FOUND", f"no pack for sphere={ctx.sphere} state={ctx.state}")
    in_window = [p for p in candidates if p.covers(d)]
    if not in_window:
        raise RateError("RATE_OUT_OF_WINDOW", f"{d.isoformat()} outside every pack window")
    pack = max(in_window, key=lambda p: p.effective_from)

    category = ctx.category
    table = pack.rates.get(category)
    if table == "same_as_skilled":
        category = "skilled"
        table = pack.rates.get("skilled")
    if not isinstance(table, dict) or ctx.zone not in table:
        raise RateError("RATE_NOT_FOUND", f"no rate for {ctx.category}/{ctx.zone} in {pack.pack_id}")

    row = table[ctx.zone]
    total = Fraction(row[-1])
    components = dict(zip(pack.raw.get("rate_tuple", []), row))
    if pack.unit == "INR_per_month":
        daily = total / pack.daily_divisor
    elif pack.unit == "INR_per_day":
        daily = total
    else:
        raise RateError("RATE_NOT_FOUND", f"unsupported unit {pack.unit}")
    return ResolvedRate(daily_min=daily, pack=pack, category_used=category, zone=ctx.zone,
                        components=components)
