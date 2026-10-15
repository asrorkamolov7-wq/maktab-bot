"""Admin yuborgan matndan so'rovnoma tuzish (xatolar ro'yxati bilan)."""
from __future__ import annotations

import re

from .models import Question

MAX_QUESTIONS = 50
MAX_OPTIONS = 12
MAX_OPTION_LEN = 60
MIN_GRADE, MAX_GRADE = 5, 11

_QUESTION_RE = re.compile(r"^\d+\s*[.)]\s*(.+)$")
_GRADES_RE = re.compile(r"(\d+)(?:\s*[-–—]\s*(\d+))?")


def parse_grades(text: str) -> list[int]:
    """'9, 10, 11' yoki '5-8' yoki '5-6, 9' -> [..]"""
    grades: set[int] = set()
    for start, end in _GRADES_RE.findall(text):
        a = int(start)
        b = int(end) if end else a
        if a > b:
            a, b = b, a
        grades.update(range(a, b + 1))
    return sorted(grades)


def parse_survey_text(raw: str) -> tuple[str, list[int], list[Question], list[str]]:
    title = ""
    grades: list[int] = []
    questions: list[Question] = []
    errors: list[str] = []
    current: Question | None = None
    explicit_text = False  # joriy savolda [yozma] belgisi bormi

    def close_current() -> None:
        nonlocal current, explicit_text
        if current is None:
            return
        if explicit_text and current.options:
            errors.append(f"«{current.text[:40]}»: variantlar ham, [yozma] ham berilgan.")
        elif current.options:
            if len(current.options) < 2:
                errors.append(f"«{current.text[:40]}»: kamida 2 ta variant kerak.")
            if len(current.options) > MAX_OPTIONS:
                errors.append(f"«{current.text[:40]}»: variantlar {MAX_OPTIONS} tadan oshmasin.")
            current.type = "choice"
        else:
            current.type = "text"
        questions.append(current)
        current = None
        explicit_text = False

    for line in (ln.strip() for ln in raw.splitlines()):
        if not line:
            continue
        low = line.lower()
        if low.startswith(("sarlavha:", "title:")):
            title = line.split(":", 1)[1].strip()
        elif low.startswith(("sinflar:", "sinf:", "grades:")):
            grades = parse_grades(line.split(":", 1)[1])
        elif (m := _QUESTION_RE.match(line)):
            close_current()
            current = Question(text=m.group(1).strip())
        elif line[0] in "-•–":
            if current is None:
                errors.append(f"Variant savoldan oldin yozilgan: «{line[:40]}»")
                continue
            opt = line.lstrip("-•– ").strip()
            if not opt:
                continue
            if len(opt) > MAX_OPTION_LEN:
                errors.append(f"Variant juda uzun (>{MAX_OPTION_LEN}): «{opt[:30]}…»")
                continue
            current.options.append(opt)
        elif low == "[yozma]":
            if current is None:
                errors.append("[yozma] savoldan oldin yozilgan.")
            else:
                explicit_text = True
        else:
            errors.append(f"Tushunarsiz qator: «{line[:50]}»")
    close_current()

    if not title:
        errors.append("«Sarlavha:» qatori topilmadi.")
    elif len(title) > 200:
        errors.append("Sarlavha 200 belgidan oshmasin.")
    if not grades:
        errors.append("«Sinflar:» qatori topilmadi yoki bo'sh (masalan: Sinflar: 9-11).")
    elif any(g < MIN_GRADE or g > MAX_GRADE for g in grades):
        errors.append(f"Sinflar faqat {MIN_GRADE} dan {MAX_GRADE} gacha bo'lishi mumkin.")
    if not questions:
        errors.append("Kamida 1 ta savol kerak (masalan: «1. Savol matni»).")
    elif len(questions) > MAX_QUESTIONS:
        errors.append(f"Savollar {MAX_QUESTIONS} tadan oshmasin.")

    return title, grades, questions, errors
