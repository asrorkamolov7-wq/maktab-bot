"""Oddiy ma'lumot modellari."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_NUMBERING_RE = re.compile(r"^\s*\d+\s*[.)]\s*")


def clean_question_text(text: str) -> str:
    """'1. Savol' -> 'Savol' (raqamlash botning o'zida qo'yiladi)."""
    return _NUMBERING_RE.sub("", text).strip()


@dataclass
class Question:
    text: str
    type: str = "text"  # "text" yoki "choice"
    options: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Question":
        return cls(
            text=clean_question_text(d.get("question") or d.get("text") or ""),
            type=d.get("type", "text"),
            options=list(d.get("options") or []),
        )

    def to_dict(self) -> dict:
        return {"type": self.type, "question": self.text, "options": self.options}


@dataclass
class Survey:
    id: str
    title: str
    grades: list[int]
    questions: list[Question]
    is_active: bool = True
    created_at: str = ""
