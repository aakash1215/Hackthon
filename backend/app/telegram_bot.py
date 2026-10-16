"""Telegram thekedar agent (BUILD_PLAN §7): a stand-in for WhatsApp, whose Business API is paid.

- python-telegram-bot 21.x, long polling, started from the FastAPI lifespan only if TELEGRAM_BOT_TOKEN is set.
- Linking only through the worker's invite link (/start <token>), then a language pick, then the intro notice.
- Every message in or out is saved and hashed with Telegram's server timestamp and logged on the chain.
- Outbound text only from fixed templates (tg_policy.py) filled by code; at most 5 bot messages per chat per day.
- Outbound goes through an outbox: with no internet the messages wait as `pending` and go out when the
  connection is back. The bot never blocks the app; if Telegram is down the app degrades, it never crashes.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import logging
import secrets
import uuid
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import asr, db, events, extract
from .config import settings
from .tg_policy import DAILY_LIMIT, LANGS, decide, hostile_guard, render

log = logging.getLogger("apna_hisaab.telegram")
router = APIRouter()


# --- small helpers -------------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now().astimezone().date().isoformat()


def _utc_iso(dt: datetime | None) -> str:
    dt = dt or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def local_day(utc_iso: str | None) -> str | None:
    """Telegram time (UTC) → the worker's local calendar date."""
    if not utc_iso:
        return None
    try:
        return datetime.fromisoformat(utc_iso).astimezone().date().isoformat()
    except ValueError:
        return None


def _sha(obj) -> str:
    return hashlib.sha256(events.canonical(obj)).hexdigest()


def inr(v) -> str:
    """'9539.38' → '9,539' (rounded half up, Indian digit grouping). Display only."""
    n = int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    s, neg = str(abs(n)), n < 0
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        s = ",".join([head, *parts, tail]) if head else ",".join([*parts, tail])
    return ("-" if neg else "") + s


MONTHS = {"hi": ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
          "mr": ["जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून", "जुलै", "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"],
          "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}


def _day_text(iso: str, lang: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS.get(lang, MONTHS['hi'])[d.month - 1]}"


def _row(c, sql: str, args=()) -> dict | None:
    r = c.execute(sql, args).fetchone()
    return dict(r) if r else None


# --- links ---------------------------------------------------------------------------------------

def active_link(c, worker_id: str) -> dict | None:
    return _row(c, "SELECT * FROM tg_links WHERE worker_id=? AND linked_at IS NOT NULL "
                   "ORDER BY linked_at DESC LIMIT 1", (worker_id,))


def link_by_chat(c, chat_id: int) -> dict | None:
    return _row(c, "SELECT * FROM tg_links WHERE chat_id=? AND linked_at IS NOT NULL "
                   "ORDER BY linked_at DESC LIMIT 1", (chat_id,))


def _names(c, worker_id: str) -> tuple[str, str, str]:
    w = _row(c, "SELECT display_name FROM workers WHERE id=?", (worker_id,)) or {}
    site = _row(c, "SELECT name FROM sites WHERE worker_id=? ORDER BY created_at LIMIT 1", (worker_id,)) or {}
    tk = _row(c, "SELECT name FROM parties WHERE worker_id=? AND role IN ('contractor','mukadam','subcontractor') "
                 "AND name IS NOT NULL ORDER BY rowid DESC LIMIT 1", (worker_id,)) or {}
    return w.get("display_name") or "कामगार", site.get("name") or "साइट", tk.get("name") or "ठेकेदार"


def start_link(token: str, chat_id: int, user_id: int | None, username: str | None) -> dict | None:
    """/start <token>: bind the chat to the invite. Unknown or already-used tokens are ignored (no reply)."""
    with db.write() as c:
        link = _row(c, "SELECT * FROM tg_links WHERE invite_token=?", (token,))
        if not link or (link["chat_id"] is not None and link["chat_id"] != chat_id):
            return None
        c.execute("UPDATE tg_links SET chat_id=?, tg_user_id=?, tg_username=? WHERE id=?",
                  (chat_id, user_id, username, link["id"]))
        return {**link, "chat_id": chat_id, "tg_user_id": user_id, "tg_username": username}


def choose_lang(chat_id: int, lang: str) -> dict | None:
    """Language picked → linked; the intro notice is queued as the first message in that language."""
    if lang not in LANGS:
        return None
    with db.write() as c:
        link = _row(c, "SELECT * FROM tg_links WHERE chat_id=? ORDER BY rowid DESC LIMIT 1", (chat_id,))
        if not link or link["linked_at"]:
            return None  # already linked: a second tap changes nothing
        now = _now()
        c.execute("UPDATE tg_links SET lang=?, linked_at=? WHERE id=?", (lang, now, link["id"]))
        link = {**link, "lang": lang, "linked_at": now}
        events.append(c, "TG_LINKED", {"link_id": link["id"], "chat_id": chat_id, "tg_user_id": link["tg_user_id"],
                                       "lang": lang}, link["worker_id"])
        worker, _, _ = _names(c, link["worker_id"])
        _queue(c, link, "INTRO", {"worker": worker}, force=True)
        return link


# --- outbox ----------------------------------------------------------------------------------------

class OutboxError(Exception):
    def __init__(self, code: str, link: dict | None = None, template_id: str | None = None):
        super().__init__(code)
        self.code, self.link, self.template_id = code, link, template_id


def note_refused(e: OutboxError) -> None:
    """Log a message the outbox refused (after the failed transaction rolled back)."""
    if e.code == "DAILY_LIMIT" and e.link:
        with db.write() as c:
            events.append(c, "TG_RATE_LIMITED", {"chat_id": e.link["chat_id"], "template_id": e.template_id},
                          e.link["worker_id"])


def _sent_today(c, chat_id: int) -> int:
    return c.execute("SELECT COUNT(*) FROM tg_messages WHERE chat_id=? AND direction='out' "
                     "AND status IN ('pending','sent') AND substr(created_at,1,10)=?", (chat_id, _today())).fetchone()[0]


def _queue(c, link: dict, template_id: str, vals: dict, *, force: bool = False) -> dict:
    """Render a fixed template and put it in the outbox. Raises OutboxError(PAUSED|DAILY_LIMIT|NOT_LINKED)."""
    if not link or link.get("chat_id") is None:
        raise OutboxError("NOT_LINKED")
    if link.get("paused") and not force:
        raise OutboxError("PAUSED")
    if _sent_today(c, link["chat_id"]) >= DAILY_LIMIT and not force:
        raise OutboxError("DAILY_LIMIT", link, template_id)
    text = render(template_id, link.get("lang") or "hi", **vals)
    rid = uuid.uuid4().hex[:12]
    c.execute("INSERT INTO tg_messages (id, worker_id, chat_id, direction, text, template_id, created_at, status) "
              "VALUES (?,?,?, 'out', ?,?,?, 'pending')", (rid, link["worker_id"], link["chat_id"], text, template_id, _now()))
    return {"id": rid, "text": text, "template_id": template_id}


def pending_out() -> list[dict]:
    with db.read() as c:
        return [dict(r) for r in c.execute("SELECT * FROM tg_messages WHERE direction='out' AND status='pending' "
                                           "ORDER BY created_at, rowid")]


def mark_sent(row_id: str, tg_message_id: int, tg_date: str) -> None:
    with db.write() as c:
        r = _row(c, "SELECT * FROM tg_messages WHERE id=?", (row_id,))
        sha = _sha({"chat_id": r["chat_id"], "direction": "out", "tg_message_id": tg_message_id, "tg_date": tg_date,
                    "text": r["text"], "template_id": r["template_id"]})
        c.execute("UPDATE tg_messages SET status='sent', tg_message_id=?, tg_date=?, sha256=? WHERE id=?",
                  (tg_message_id, tg_date, sha, row_id))
        events.append(c, "TG_MESSAGE_OUT", {"tg_row": row_id, "chat_id": r["chat_id"], "tg_message_id": tg_message_id,
                                            "tg_date": tg_date, "template_id": r["template_id"], "sha256": sha},
                      r["worker_id"])


def mark_failed(row_id: str, code: str) -> None:
    with db.write() as c:
        c.execute("UPDATE tg_messages SET status='failed', classification=? WHERE id=?",
                  (json.dumps({"error": code}), row_id))


# --- numbers for the templates (ledger + wage engine; code only) -------------------------------------

def _balance(worker_id: str, upto: str) -> str | None:
    from .api import hisaab

    res = hisaab(worker_id, upto[:8] + "01", upto)
    return inr(res["totals"]["claim_estimate"]) if res.get("ok") and res.get("totals") else None


def _ledger_rows(c, worker_id: str, d_from: str, d_to: str) -> list[dict]:
    from .api import _confirmed

    return _confirmed(c, worker_id, d_from, d_to)


def day_vals(worker_id: str, day: str, lang: str) -> dict | None:
    with db.read() as c:
        worker, site, _ = _names(c, worker_id)
        rows = _ledger_rows(c, worker_id, day, day)
    wd = next((r for r in rows if r["kind"] == "workday" and (r["confirmed"] or {}).get("worked") != "no"), None)
    if not wd:
        return None
    cf = wd["confirmed"]
    paid = sum(int((r["confirmed"] or {}).get("amount_paid") or 0) for r in rows if r["kind"] == "payment")
    return {"date": _day_text(day, lang), "worker": worker, "site": site, "start": cf.get("start_time"),
            "end": cf.get("end_time"), "paid_today": inr(paid), "balance": _balance(worker_id, day)}


def summary_vals(worker_id: str, lang: str) -> dict:
    today = _today()
    with db.read() as c:
        worker, _, _ = _names(c, worker_id)
        rows = _ledger_rows(c, worker_id, today[:8] + "01", today)
    days = sorted((r for r in rows if r["kind"] == "workday" and r["day"]), key=lambda r: r["day"])
    lines = [f"{_day_text(r['day'], lang)}: {r['confirmed'].get('start_time')}–{r['confirmed'].get('end_time')}"
             for r in days[-31:]]
    paid = sum(int((r["confirmed"] or {}).get("amount_paid") or 0) for r in rows if r["kind"] == "payment")
    period = f"{_day_text(today[:8] + '01', lang)}–{_day_text(today, lang)}"
    return {"worker": worker, "period": period, "lines": "\n".join(lines) or "—", "days": len(days),
            "paid": inr(paid), "balance": _balance(worker_id, today)}


def month_days(worker_id: str) -> int:
    today = _today()
    with db.read() as c:
        rows = _ledger_rows(c, worker_id, today[:8] + "01", today)
    return len({r["day"] for r in rows if r["kind"] == "workday" and r["day"]})


def queue_template(worker_id: str, template_id: str, *, auto: bool = False) -> dict:
    """Worker-triggered (SUMMARY, REQUEST_WRITTEN_HISAAB) or automatic (DAILY_UPDATE) message."""
    with db.read() as c:
        link = active_link(c, worker_id)
    if not link:
        raise OutboxError("NOT_LINKED")
    lang = link.get("lang") or "hi"
    vals = summary_vals(worker_id, lang) if template_id == "SUMMARY" else {}
    with db.write() as c:
        link = active_link(c, worker_id)
        return _queue(c, link, template_id, vals)


def on_entry_confirmed(worker_id: str, kind: str, confirmed: dict) -> None:
    """Hook from /confirm: DAILY_UPDATE for a workday, PAYMENT_ACK for a payment (if auto_daily and not paused)."""
    if not settings.telegram_configured:
        return
    try:
        with db.read() as c:
            link = active_link(c, worker_id)
        if not link or not link["auto_daily"] or link["paused"]:
            return
        lang = link.get("lang") or "hi"
        if kind == "workday" and confirmed.get("work_date") and confirmed.get("worked") != "no":
            day = confirmed["work_date"]
            vals = day_vals(worker_id, day, lang)
            if not vals:
                return
            tpl = "DAILY_UPDATE" if day == _today() else "DAY_UPDATE"
        elif kind == "payment" and confirmed.get("amount_paid") is not None:
            tpl = "PAYMENT_ACK"
            vals = {"amount": inr(confirmed["amount_paid"]),
                    "balance": _balance(worker_id, confirmed.get("payment_date") or _today())}
        else:
            return
        with db.write() as c:
            _queue(c, active_link(c, worker_id), tpl, vals)
        RUNTIME.kick()
    except OutboxError as e:
        note_refused(e)
        log.info("telegram update not queued: %s", e.code)
    except Exception:  # noqa: BLE001 — Telegram must never break a confirm
        log.exception("telegram hook failed")


# --- inbound ---------------------------------------------------------------------------------------

def save_inbound(link: dict, tg_message_id: int, tg_date: str, text: str | None = None,
                 voice: bytes | None = None) -> dict:
    """Save and hash first (text or original OGG bytes), with Telegram's server timestamp."""
    rid = uuid.uuid4().hex[:12]
    voice_path = voice_sha = None
    if voice is not None:
        voice_sha = hashlib.sha256(voice).hexdigest()
        rel = Path("media") / "tg" / f"{rid}.ogg"
        (settings.data_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (settings.data_dir / rel).write_bytes(voice)
        voice_path = rel.as_posix()
    sha = _sha({"chat_id": link["chat_id"], "direction": "in", "tg_message_id": tg_message_id, "tg_date": tg_date,
                "text": text, "voice_sha256": voice_sha})
    with db.write() as c:
        c.execute("INSERT INTO tg_messages (id, worker_id, chat_id, direction, tg_message_id, tg_date, text, voice_path, "
                  "voice_sha256, sha256, created_at, status) VALUES (?,?,?, 'in', ?,?,?,?,?,?,?, 'received')",
                  (rid, link["worker_id"], link["chat_id"], tg_message_id, tg_date, text, voice_path, voice_sha, sha,
                   _now()))
        events.append(c, "TG_MESSAGE_IN", {"tg_row": rid, "chat_id": link["chat_id"], "tg_message_id": tg_message_id,
                                           "tg_date": tg_date, "sha256": sha, "voice_sha256": voice_sha},
                      link["worker_id"])
    return {"id": rid, "sha256": sha, "voice_path": voice_path}


def classify_and_act(row_id: str) -> dict:
    """Slow part (ASR for voice, LLM classification), then the fixed reply policy. Run in a thread."""
    from .api import _ground_reply

    with db.read() as c:
        m = _row(c, "SELECT * FROM tg_messages WHERE id=?", (row_id,))
        link = link_by_chat(c, m["chat_id"])
    transcript = None
    if m["voice_path"]:
        src = settings.data_dir / m["voice_path"]
        try:
            asr_res = asr.transcribe_wav(asr.to_wav16k(src, src.with_suffix(".16k.wav")), "auto")
            transcript = asr_res["text"]
        except asr.ASRUnavailable as e:
            log.warning("voice ASR failed: %s", e)
    text = m["text"] or transcript or ""
    guard = hostile_guard(text)
    reply = {"intent": None, "confidence": None, "amount": {"value": None}, "date": {"value": None},
             "days": {"value": None}}
    llm_error = None
    if guard:
        reply.update(intent="hostile", confidence="high")
    elif text.strip():
        try:
            reply = _ground_reply(extract.extract_reply(text, timeout=120), text)
        except extract.LLMUnavailable as e:
            llm_error = e.args[0]  # cut line: log as evidence, alert the worker, no reply
    amount = reply["amount"]["value"]
    date_text = reply["date"]["evidence"] if reply["date"].get("value") else None
    days = reply["days"]["value"]
    d = decide(reply["intent"], reply["confidence"], amount=amount, date_text=date_text, guard_hit=guard)
    classification = {"intent": reply["intent"], "confidence": reply["confidence"], "amount": amount,
                      "date_text": date_text, "days": days, "guard": guard, "llm_error": llm_error,
                      "decision": {"template_id": d.template_id, "inbox": d.inbox_kind, "pause": d.pause}}
    out = refused = None
    with db.write() as c:
        c.execute("UPDATE tg_messages SET transcript=?, classification=? WHERE id=?",
                  (transcript, json.dumps(classification, ensure_ascii=False), row_id))
        wid = m["worker_id"]
        if d.pause:
            c.execute("UPDATE tg_links SET paused=1 WHERE id=?", (link["id"],))
            link = {**link, "paused": 1}
            events.append(c, "TG_HOSTILE_STOP", {"tg_row": row_id, "sha256": m["sha256"], "guard": guard}, wid)
        if d.inbox_kind:
            c.execute("INSERT INTO inbox (id, worker_id, tg_message_row, kind, text, intent, confidence, amount, "
                      "date_text, days, tg_date, message_sha256, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (uuid.uuid4().hex[:12], wid, row_id, d.inbox_kind, text, reply["intent"], reply["confidence"],
                       amount, date_text, days, m["tg_date"], m["sha256"], _now()))
        if d.template_id:
            worker, _, _ = _names(c, wid)
            vals = {"worker": worker, "amount": inr(amount) if amount is not None else None, "date": date_text}
            if d.template_id == "NOTED_DISPUTE":
                vals["days"] = None  # filled below (needs its own read)
            if d.template_id == "SUMMARY":
                vals = None
            try:
                if vals is not None and d.template_id != "NOTED_DISPUTE":
                    out = _queue(c, link, d.template_id, vals)
            except OutboxError as e:
                classification["not_sent"] = e.code
                refused = e
    # templates that need ledger/engine numbers are built outside the write lock
    if d.template_id in ("SUMMARY", "NOTED_DISPUTE"):
        lang = link.get("lang") or "hi"
        vals = summary_vals(m["worker_id"], lang) if d.template_id == "SUMMARY" else None
        if d.template_id == "NOTED_DISPUTE":
            with db.read() as c:
                worker, _, _ = _names(c, m["worker_id"])
            vals = {"worker": worker, "days": month_days(m["worker_id"])}
        try:
            with db.write() as c:
                out = _queue(c, link_by_chat(c, m["chat_id"]), d.template_id, vals)
        except OutboxError as e:
            classification["not_sent"] = e.code
            refused = e
    if refused:
        note_refused(refused)
    return {"decision": d, "classification": classification, "reply": out}


# --- runtime (long polling inside the FastAPI event loop) ----------------------------------------------

class Runtime:
    def __init__(self) -> None:
        self.app = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self.running = False
        self.last_error: str | None = None
        self._wake: asyncio.Event | None = None
        self._task: asyncio.Task | None = None

    def kick(self) -> None:
        """Ask the loop to flush the outbox now (callable from any thread)."""
        if self.loop and self._wake:
            self.loop.call_soon_threadsafe(self._wake.set)

    def start(self) -> None:
        self.loop = asyncio.get_running_loop()
        self._wake = asyncio.Event()
        self._task = asyncio.create_task(self._supervise())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        await self._shutdown()

    async def _supervise(self) -> None:
        """Start polling; if Telegram/internet is down, keep retrying. Flush the outbox every few seconds."""
        while True:
            try:
                if not self.running:
                    await self._start_app()
                await self.flush()
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 — offline: pause and retry, never crash the hub
                self.last_error = type(e).__name__
                log.warning("telegram offline/paused: %s", e)
                await self._shutdown()
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=10 if self.running else 30)
            except asyncio.TimeoutError:
                pass
            self._wake.clear()

    async def _start_app(self) -> None:
        from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

        builder = Application.builder().token(settings.telegram_bot_token)
        if settings.telegram_proxy:
            builder = builder.proxy(settings.telegram_proxy).get_updates_proxy(settings.telegram_proxy)
        app = builder.build()
        app.add_handler(CommandHandler("start", self._on_start))
        app.add_handler(CallbackQueryHandler(self._on_lang, pattern=r"^lang:"))
        app.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.VOICE, self._on_message))
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=["message", "callback_query"])
        self.app, self.running, self.last_error = app, True, None
        log.info("telegram bot polling as @%s", settings.telegram_bot_username)

    async def _shutdown(self) -> None:
        app, self.app, self.running = self.app, None, False
        if not app:
            return
        for step in (lambda: app.updater.stop(), app.stop, app.shutdown):
            try:
                await step()
            except Exception:  # noqa: BLE001
                pass

    async def flush(self) -> None:
        if not self.running or not self.app:
            return
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.error import BadRequest, Forbidden

        for m in pending_out():
            markup = None
            if m["template_id"] == "LANG_ASK":
                markup = InlineKeyboardMarkup([[InlineKeyboardButton("हिंदी", callback_data="lang:hi"),
                                                InlineKeyboardButton("मराठी", callback_data="lang:mr"),
                                                InlineKeyboardButton("English", callback_data="lang:en")]])
            try:
                sent = await self.app.bot.send_message(chat_id=m["chat_id"], text=m["text"], reply_markup=markup)
            except (Forbidden, BadRequest) as e:  # blocked the bot / bad chat: will not succeed on retry
                mark_failed(m["id"], type(e).__name__)
                continue
            mark_sent(m["id"], sent.message_id, _utc_iso(sent.date))

    # handlers ---------------------------------------------------------------------------------------
    async def _on_start(self, update, context) -> None:
        msg = update.effective_message
        token = context.args[0] if context.args else None
        if not token:
            return  # no invite: the bot stays silent
        link = start_link(token, msg.chat_id, update.effective_user.id if update.effective_user else None,
                          update.effective_user.username if update.effective_user else None)
        if not link:
            return
        with db.write() as c:
            worker, _, _ = _names(c, link["worker_id"])
            _queue(c, link, "LANG_ASK", {"worker": worker}, force=True)
        await self.flush()

    async def _on_lang(self, update, context) -> None:
        q = update.callback_query
        await q.answer()
        choose_lang(q.message.chat_id, q.data.split(":", 1)[1])
        await self.flush()

    async def _on_message(self, update, context) -> None:
        msg = update.effective_message
        with db.read() as c:
            link = link_by_chat(c, msg.chat_id)
        if not link:
            return  # only linked chats are recorded
        voice = None
        if msg.voice:
            f = await msg.voice.get_file()
            voice = bytes(await f.download_as_bytearray())
        row = save_inbound(link, msg.message_id, _utc_iso(msg.date), text=msg.text, voice=voice)
        await asyncio.to_thread(classify_and_act, row["id"])
        await self.flush()


RUNTIME = Runtime()


# --- API --------------------------------------------------------------------------------------------

class InviteIn(BaseModel):
    worker_id: str


def _link_public(link: dict | None) -> dict | None:
    if not link:
        return None
    return {"linked": bool(link.get("linked_at")), "tg_username": link.get("tg_username"), "lang": link.get("lang"),
            "linked_at": link.get("linked_at"), "auto_daily": bool(link.get("auto_daily")),
            "paused": bool(link.get("paused")), "invite_url": _invite_url(link["invite_token"])}


def _invite_url(token: str) -> str:
    return f"https://t.me/{settings.telegram_bot_username}?start={token}"


@router.get("/api/telegram/status")
def tg_status(worker_id: str):
    with db.read() as c:
        link = active_link(c, worker_id) or _row(c, "SELECT * FROM tg_links WHERE worker_id=? ORDER BY rowid DESC "
                                                    "LIMIT 1", (worker_id,))
    return {"configured": settings.telegram_configured, "running": RUNTIME.running,
            "bot_username": settings.telegram_bot_username or None, "last_error": RUNTIME.last_error,
            "link": _link_public(link)}


@router.post("/api/telegram/invite")
def tg_invite(body: InviteIn):
    if not (settings.telegram_configured and settings.telegram_bot_username):
        raise HTTPException(409, "TELEGRAM_NOT_CONFIGURED")
    with db.write() as c:
        if not _row(c, "SELECT id FROM workers WHERE id=?", (body.worker_id,)):
            raise HTTPException(404, "WORKER_NOT_FOUND")
        link = _row(c, "SELECT * FROM tg_links WHERE worker_id=? AND chat_id IS NULL ORDER BY rowid DESC LIMIT 1",
                    (body.worker_id,))
        if not link:
            party = _row(c, "SELECT id FROM parties WHERE worker_id=? AND role IN ('contractor','mukadam',"
                            "'subcontractor') ORDER BY rowid DESC LIMIT 1", (body.worker_id,))
            link = {"id": uuid.uuid4().hex[:12], "invite_token": secrets.token_urlsafe(12)}
            c.execute("INSERT INTO tg_links (id, worker_id, party_id, invite_token) VALUES (?,?,?,?)",
                      (link["id"], body.worker_id, party["id"] if party else None, link["invite_token"]))
            events.append(c, "TG_INVITE_CREATED", {"link_id": link["id"]}, body.worker_id)
        worker, _, _ = _names(c, body.worker_id)
    url = _invite_url(link["invite_token"])
    return {"invite_url": url, "token": link["invite_token"], "qr_png": _qr(url), "bot_username": settings.telegram_bot_username,
            "share_text": f"नमस्ते, यह {worker} का 'अपना हिसाब' है। काम और पैसे का हिसाब यहाँ मिलेगा: {url}"}


def _qr(url: str) -> str:
    import qrcode

    img = qrcode.make(url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


class SettingsIn(BaseModel):
    worker_id: str
    auto_daily: bool | None = None
    paused: bool | None = None


@router.post("/api/telegram/settings")
def tg_settings(body: SettingsIn):
    with db.write() as c:
        link = active_link(c, body.worker_id)
        if not link:
            raise HTTPException(409, "NOT_LINKED")
        if body.auto_daily is not None:
            c.execute("UPDATE tg_links SET auto_daily=? WHERE id=?", (int(body.auto_daily), link["id"]))
        if body.paused is not None:
            c.execute("UPDATE tg_links SET paused=? WHERE id=?", (int(body.paused), link["id"]))
        events.append(c, "TG_SETTINGS", {"link_id": link["id"], "auto_daily": body.auto_daily, "paused": body.paused},
                      body.worker_id)
        link = active_link(c, body.worker_id)
    return _link_public(link)


class SendIn(BaseModel):
    worker_id: str
    template: Literal["SUMMARY", "REQUEST_WRITTEN_HISAAB"]


@router.post("/api/telegram/send")
def tg_send(body: SendIn):
    try:
        out = queue_template(body.worker_id, body.template)
    except OutboxError as e:
        note_refused(e)
        raise HTTPException(429 if e.code == "DAILY_LIMIT" else 409, e.code) from e
    RUNTIME.kick()
    return {"queued": True, **out}


@router.get("/api/telegram/messages")
def tg_messages(worker_id: str):
    with db.read() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM tg_messages WHERE worker_id=? ORDER BY created_at, rowid",
                                           (worker_id,))]
    items = []
    for r in rows:
        cl = json.loads(r["classification"]) if r["classification"] else {}
        items.append({"id": r["id"], "direction": r["direction"], "text": r["text"], "transcript": r["transcript"],
                      "tg_date": r["tg_date"], "template_id": r["template_id"], "intent": cl.get("intent"),
                      "status": r["status"], "sha256": r["sha256"]})
    return {"items": items}


@router.get("/api/inbox")
def inbox(worker_id: str):
    with db.read() as c:
        _, _, tk = _names(c, worker_id)
        rows = [dict(r) for r in c.execute("SELECT * FROM inbox WHERE worker_id=? ORDER BY created_at DESC, rowid DESC",
                                           (worker_id,))]
    return {"items": [{**r, "thekedar_name": tk} for r in rows]}


class InboxAction(BaseModel):
    action: Literal["confirm", "deny", "dismiss", "seen"]
    amount: int | None = None
    due_date: str | None = None
    remind: bool = False


@router.post("/api/inbox/{item_id}")
def inbox_action(item_id: str, body: InboxAction):
    with db.write() as c:
        it = _row(c, "SELECT * FROM inbox WHERE id=?", (item_id,))
        if not it:
            raise HTTPException(404, "NOT_FOUND")
        status = {"confirm": "confirmed", "deny": "denied", "dismiss": "dismissed", "seen": "seen"}[body.action]
        promise_id = None
        if body.action == "confirm" and it["kind"] == "promise":
            if body.amount is None or not 0 < body.amount <= 10_000_000:
                raise HTTPException(422, "AMOUNT_REQUIRED")  # the worker confirms the number, not the model
            due = None
            if body.due_date:
                try:
                    due = date.fromisoformat(body.due_date).isoformat()
                except ValueError as e:
                    raise HTTPException(422, "BAD_DATE") from e
            promise_id = uuid.uuid4().hex[:12]
            c.execute("INSERT INTO promises (id, worker_id, source, source_ref, amount, due_date, date_status, confirmed, "
                      "reminder_at, created_at) VALUES (?,?, 'telegram', ?,?,?,?,1,?,?)",
                      (promise_id, it["worker_id"], it["message_sha256"], body.amount, due,
                       "worker_confirmed" if due else None, f"{due}T09:00:00" if (due and body.remind) else None, _now()))
            events.append(c, "PROMISE_LOGGED", {"promise_id": promise_id, "source": "telegram", "amount": body.amount,
                                                "due": due, "message_sha256": it["message_sha256"],
                                                "tg_date": it["tg_date"]}, it["worker_id"])
        elif body.action in ("confirm", "deny") and it["kind"] == "partial_payment":
            events.append(c, "TG_CLAIM_CONFIRMED" if body.action == "confirm" else "TG_CLAIM_DENIED",
                          {"inbox_id": item_id, "amount": it["amount"], "message_sha256": it["message_sha256"]},
                          it["worker_id"])
        else:
            events.append(c, "INBOX_RESOLVED", {"inbox_id": item_id, "kind": it["kind"], "status": status},
                          it["worker_id"])
        c.execute("UPDATE inbox SET status=?, promise_id=?, resolved_at=? WHERE id=?",
                  (status, promise_id, _now(), item_id))
        head = events.head(c)
    return {"id": item_id, "status": status, "promise_id": promise_id, "chain_head": head}


@router.get("/api/promises")
def promises(worker_id: str):
    with db.read() as c:
        return {"items": [dict(r) for r in c.execute("SELECT * FROM promises WHERE worker_id=? ORDER BY created_at DESC",
                                                     (worker_id,))]}
