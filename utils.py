from __future__ import annotations

import re
from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import User


def esc(text: str | None) -> str:
    """Foydalanuvchi matnini HTML uchun xavfsiz qilish."""
    return escape(text or "", quote=False)


def user_link(user: User) -> str:
    return f'<a href="tg://user?id={user.id}">{esc(user.full_name)}</a>'


def progress_bar(done: int, total: int, width: int = 10) -> str:
    filled = round(width * done / total) if total else 0
    return "▰" * filled + "▱" * (width - filled)


def grade_key(grade: str) -> tuple[int, str]:
    """'10-B' -> (10, 'B') — sinflarni to'g'ri tartiblash uchun."""
    m = re.match(r"(\d+)\s*-?\s*(\w*)", grade)
    return (int(m.group(1)), m.group(2)) if m else (99, grade)
