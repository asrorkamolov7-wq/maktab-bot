"""Sozlamalar: barcha maxfiy ma'lumotlar muhit o'zgaruvchilaridan olinadi."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    db_path: str
    port: int
    grade_letters: tuple[str, ...]
    broadcast_delay: float = 0.05  # Telegram limiti: ~30 xabar/soniya


def _parse_ids(raw: str) -> frozenset[int]:
    ids: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            raise RuntimeError(f"ADMIN_IDS ichida noto'g'ri qiymat: {part!r}") from None
    return frozenset(ids)


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan.")

    # ADMIN_ID (eski nom) ham qabul qilinadi
    admin_ids = _parse_ids(os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID", ""))
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS muhit o'zgaruvchisi o'rnatilmagan.")

    letters = tuple(
        x.strip().upper()
        for x in os.getenv("GRADE_LETTERS", "A,B,V,G,D").split(",")
        if x.strip()
    )
    return Settings(
        bot_token=token,
        admin_ids=admin_ids,
        db_path=os.getenv("DB_PATH", "data/school_bot.db"),
        port=int(os.getenv("PORT", "10000")),
        grade_letters=letters or ("A", "B", "V", "G", "D"),
    )
