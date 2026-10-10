"""Generate the synthetic data for the tutorial.

Everything here is fake (Faker, fixed seeds). The data carries the traps the
tutorial relies on:

- raw_events: timestamps are UTC, the warehouse session is not (profiles.yml).
  Activity peaks in European hours, so a session-local date shifts a large
  share of each day's events into the previous day; the last day comes up short.
- raw_events: mobile clients replay events — same event_id ingested twice.
- support_tickets: free-text complaints with PII (names, emails, phones, IBANs,
  card numbers) plus decoys that look like PII but aren't (order ids, epoch
  millis, internal addresses, local numbers, dates, amounts).
- corpus/*.jsonl: the same generator with labelled PII spans, for scoring
  the masking filter in act 3.

Run:  uv run python data/generate.py
"""

from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker

ROOT = Path(__file__).resolve().parent.parent
START = datetime(2026, 10, 1, tzinfo=timezone.utc)
DAYS = 14
USERS = 1500
EVENTS_PER_DAY = 2200
REPLAY_RATE = 0.03

# UTC hour weights: European users plus some APAC traffic, so 00–07 UTC is busy.
HOUR_WEIGHTS = [6, 5, 5, 7, 10, 13, 14, 9, 9, 8, 7, 7, 8, 8, 8, 9, 10, 11, 11, 10, 8, 6, 4, 3]
EVENT_TYPES = ["app_open", "view_instrument", "add_watchlist", "place_order", "deposit", "close_position"]
PLATFORMS = ["ios", "android", "web"]

INTERNAL_DOMAIN = "corp.example"
LOCALES = ["de_DE", "de_AT", "de_CH"]


def gen_events(rng: random.Random) -> list[dict]:
    rows = []
    n = 0
    for d in range(DAYS):
        day = START + timedelta(days=d)
        for _ in range(int(EVENTS_PER_DAY * rng.uniform(0.9, 1.1))):
            hour = rng.choices(range(24), weights=HOUR_WEIGHTS)[0]
            ts = day + timedelta(hours=hour, minutes=rng.randrange(60), seconds=rng.randrange(60))
            n += 1
            platform = rng.choice(PLATFORMS)
            row = {
                "event_id": f"ev_{n:07d}",
                "user_id": rng.randint(1, USERS),
                "event_type": rng.choice(EVENT_TYPES),
                "platform": platform,
                "event_ts": ts.strftime("%Y-%m-%d %H:%M:%S+00"),
                "ingested_at": (ts + timedelta(seconds=rng.randint(1, 90))).strftime("%Y-%m-%d %H:%M:%S+00"),
            }
            rows.append(row)
            if platform != "web" and rng.random() < REPLAY_RATE:
                replay = dict(row)
                replay["ingested_at"] = (ts + timedelta(minutes=rng.randint(5, 240))).strftime("%Y-%m-%d %H:%M:%S+00")
                rows.append(replay)
    rows.sort(key=lambda r: r["ingested_at"])
    return rows


# --- support tickets with PII --------------------------------------------------


class Text:
    """Builds a string and records labelled spans as pieces are appended."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.spans: list[dict] = []
        self.pos = 0

    def add(self, s: str, label: str | None = None) -> "Text":
        if label:
            self.spans.append({"start": self.pos, "end": self.pos + len(s), "type": label})
        self.parts.append(s)
        self.pos += len(s)
        return self

    def value(self) -> str:
        return "".join(self.parts)


def intl_phone(fake: Faker, rng: random.Random) -> str:
    cc = rng.choice(["+49", "+43", "+41"])
    digits = "".join(str(rng.randint(0, 9)) for _ in range(rng.randint(9, 11)))
    style = rng.choice(["space", "dash", "plain"])
    if style == "space":
        return f"{cc} {digits[:3]} {digits[3:7]} {digits[7:]}"
    if style == "dash":
        return f"{cc}-{digits[:3]}-{digits[3:]}"
    return f"{cc}{digits}"


def luhn_ok(digits: str) -> bool:
    total, dbl = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if dbl:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
        dbl = not dbl
    return total % 10 == 0


def order_id(rng: random.Random) -> str:
    """16 digits that deliberately fail Luhn — looks like a card, isn't."""
    while True:
        s = "".join(str(rng.randint(0, 9)) for _ in range(16))
        if not luhn_ok(s):
            return s


def decoy(fake: Faker, rng: random.Random) -> str:
    kind = rng.choice(["order", "epoch", "internal", "local", "date", "amount"])
    if kind == "order":
        return f"order {order_id(rng)}"
    if kind == "epoch":
        return f"ref {rng.randint(1_759_000_000_000, 1_761_000_000_000)}"
    if kind == "internal":
        return f"{fake.first_name().lower()}.{fake.last_name().lower()}@{INTERNAL_DOMAIN}"
    if kind == "local":
        return f"0{rng.randint(100, 999)} {rng.randint(100000, 9999999)}"
    if kind == "date":
        return (START + timedelta(days=rng.randint(-30, 13))).strftime("%Y-%m-%d")
    return f"{rng.randint(50, 9000):,}.{rng.randint(0, 99):02d} EUR".replace(",", " ")


TEMPLATES = [
    # each template: list of (literal | (pii_kind) | ("decoy",))
    ["Hi, this is ", ("PERSON",), ". My withdrawal is still pending, see ", ("decoy",), ". Please call me on ", ("PHONE",), "."],
    ["I was charged twice on card ", ("CARD",), " for ", ("decoy",), ". Contact me at ", ("EMAIL",), "."],
    ["Please send the refund to ", ("IBAN",), ". Account holder: ", ("PERSON",), "."],
    ["Your agent ", ("decoy_internal",), " promised a callback on ", ("decoy",), ". Nobody called. Reach me at ", ("EMAIL",), "."],
    ["App crashes when I open the chart, ", ("decoy",), ". Not urgent."],
    ["Deposit failed again. Card ", ("CARD",), ", tried ", ("decoy",), ". My number is ", ("PHONE",), ", ", ("PERSON",), "."],
    ["", ("PERSON",), " here. Why was my position closed? Ticket from ", ("decoy",), " was ignored."],
    ["Spread on DAX was too wide yesterday. Call the office ", ("decoy_local",), " if you need details."],
    ["Change my email to ", ("EMAIL",), " and the payout account to ", ("IBAN",), "."],
    ["Verification documents uploaded twice, ", ("decoy",), ". Please confirm. ", ("PERSON",), ", ", ("PHONE",), "."],
]


def render(fake: Faker, rng: random.Random, template: list) -> Text:
    t = Text()
    for piece in template:
        if isinstance(piece, str):
            t.add(piece)
            continue
        kind = piece[0]
        if kind == "PERSON":
            t.add(fake.name(), "PERSON")
        elif kind == "EMAIL":
            t.add(fake.email(), "EMAIL")
        elif kind == "PHONE":
            t.add(intl_phone(fake, rng), "PHONE")
        elif kind == "IBAN":
            t.add(fake.iban(), "IBAN")
        elif kind == "CARD":
            t.add(fake.credit_card_number(card_type=rng.choice(["visa16", "mastercard"])), "CARD")
        elif kind == "decoy_internal":
            t.add(f"{fake.first_name().lower()}.{fake.last_name().lower()}@{INTERNAL_DOMAIN}")
        elif kind == "decoy_local":
            t.add(f"0{rng.randint(100, 999)} {rng.randint(100000, 9999999)}")
        elif kind == "decoy":
            t.add(decoy(fake, rng))
    return t


def gen_texts(seed: int, n: int) -> list[Text]:
    rng = random.Random(seed)
    fakers = {loc: Faker(loc) for loc in LOCALES}
    for i, f in enumerate(fakers.values()):
        f.seed_instance(seed + i)
    out = []
    for _ in range(n):
        fake = fakers[rng.choice(LOCALES)]
        out.append(render(fake, rng, rng.choice(TEMPLATES)))
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_corpus(path: Path, texts: list[Text]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for t in texts:
            f.write(json.dumps({"text": t.value(), "spans": t.spans}, ensure_ascii=False) + "\n")


def main() -> None:
    rng = random.Random(42)
    write_csv(ROOT / "seeds" / "raw_events.csv", gen_events(rng))

    tickets = []
    for i, t in enumerate(gen_texts(seed=7, n=400), start=1):
        created = START + timedelta(days=rng.randrange(DAYS), hours=rng.randrange(24), minutes=rng.randrange(60))
        tickets.append({
            "ticket_id": f"tk_{i:05d}",
            "customer_id": rng.randint(1, USERS),
            "channel": rng.choice(["email", "chat", "phone_note"]),
            "created_at": created.strftime("%Y-%m-%d %H:%M:%S+00"),
            "body": t.value(),
        })
    write_csv(ROOT / "seeds" / "support_tickets.csv", tickets)

    write_corpus(ROOT / "corpus" / "public.jsonl", gen_texts(seed=101, n=200))
    write_corpus(ROOT / "corpus" / "hidden.jsonl", gen_texts(seed=202, n=500))
    print("seeds/raw_events.csv, seeds/support_tickets.csv, corpus/public.jsonl, corpus/hidden.jsonl")


if __name__ == "__main__":
    main()
