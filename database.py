"""SQLite (aiosqlite) bilan ishlash. Bitta umumiy ulanish, WAL rejimi."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import aiosqlite

from .models import Question, Survey
from .texts import DEFAULT_SURVEYS

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS users (
    user_id    INTEGER PRIMARY KEY,
    full_name  TEXT,
    username   TEXT,
    is_blocked INTEGER NOT NULL DEFAULT 0,
    joined_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS surveys (
    id             TEXT PRIMARY KEY,
    title          TEXT NOT NULL,
    grades_json    TEXT NOT NULL,
    questions_json TEXT NOT NULL,
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submissions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id  TEXT NOT NULL REFERENCES surveys(id),
    user_id    INTEGER NOT NULL,
    full_name  TEXT NOT NULL,
    grade      TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (survey_id, user_id)
);

CREATE TABLE IF NOT EXISTS submission_answers (
    submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    q_idx         INTEGER NOT NULL,
    question      TEXT NOT NULL,
    answer        TEXT NOT NULL,
    PRIMARY KEY (submission_id, q_idx)
);

CREATE TABLE IF NOT EXISTS feedback_map (
    admin_id     INTEGER NOT NULL,
    admin_msg_id INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    user_name    TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (admin_id, admin_msg_id)
);

CREATE INDEX IF NOT EXISTS idx_submissions_user ON submissions(user_id);
"""


def _row_to_survey(row: aiosqlite.Row) -> Survey:
    return Survey(
        id=row["id"],
        title=row["title"],
        grades=json.loads(row["grades_json"]),
        questions=[Question.from_dict(q) for q in json.loads(row["questions_json"])],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"] or "",
    )


class Database:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn
        self._write_lock = asyncio.Lock()

    # ---------- hayot sikli ----------
    @classmethod
    async def connect(cls, path: str) -> "Database":
        folder = os.path.dirname(os.path.abspath(path))
        os.makedirs(folder, exist_ok=True)
        conn = await aiosqlite.connect(path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        db = cls(conn)
        await db._init_schema()
        return db

    async def close(self) -> None:
        await self._conn.close()

    async def _init_schema(self) -> None:
        async with self._write_lock:
            await self._conn.executescript(SCHEMA)
            await self._migrate_legacy()
            await self._seed_defaults()
            await self._conn.commit()

    async def _migrate_legacy(self) -> None:
        """Eski versiyadagi `custom_surveys` jadvalidagi so'rovnomalarni ko'chirish."""
        async with self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='custom_surveys'"
        ) as cur:
            if await cur.fetchone() is None:
                return
        await self._conn.execute(
            """INSERT OR IGNORE INTO surveys (id, title, grades_json, questions_json, created_at)
               SELECT id, title, grades_json, questions_json, created_at FROM custom_surveys"""
        )
        await self._conn.execute(
            "INSERT OR IGNORE INTO meta (key, value) VALUES ('defaults_seeded', '1')"
        )
        logger.info("Eski so'rovnomalar yangi jadvalga ko'chirildi.")

    async def _seed_defaults(self) -> None:
        """Boshlang'ich so'rovnomalar faqat BIR marta qo'shiladi (o'chirilsa qaytmaydi)."""
        async with self._conn.execute(
            "SELECT value FROM meta WHERE key='defaults_seeded'"
        ) as cur:
            if await cur.fetchone():
                return
        for s in DEFAULT_SURVEYS:
            await self._conn.execute(
                "INSERT OR IGNORE INTO surveys (id, title, grades_json, questions_json) VALUES (?,?,?,?)",
                (s["id"], s["title"], json.dumps(s["grades"]), json.dumps(s["questions"], ensure_ascii=False)),
            )
        await self._conn.execute("INSERT INTO meta (key, value) VALUES ('defaults_seeded', '1')")

    async def _execute(self, sql: str, params: tuple | list = ()) -> int:
        async with self._write_lock:
            cur = await self._conn.execute(sql, params)
            await self._conn.commit()
            return cur.rowcount

    async def _fetchall(self, sql: str, params: tuple | list = ()) -> list[aiosqlite.Row]:
        async with self._conn.execute(sql, params) as cur:
            return list(await cur.fetchall())

    async def _fetchone(self, sql: str, params: tuple | list = ()) -> aiosqlite.Row | None:
        async with self._conn.execute(sql, params) as cur:
            return await cur.fetchone()

    # ---------- foydalanuvchilar ----------
    async def upsert_user(self, user_id: int, full_name: str, username: str | None) -> None:
        await self._execute(
            """INSERT INTO users (user_id, full_name, username) VALUES (?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET
                   full_name = excluded.full_name,
                   username  = excluded.username,
                   is_blocked = 0,
                   last_seen = CURRENT_TIMESTAMP""",
            (user_id, full_name, username or ""),
        )

    async def get_broadcast_ids(self) -> list[int]:
        rows = await self._fetchall("SELECT user_id FROM users WHERE is_blocked = 0")
        return [r["user_id"] for r in rows]

    async def mark_blocked(self, user_id: int) -> None:
        await self._execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))

    async def user_exists(self, user_id: int) -> bool:
        return await self._fetchone("SELECT 1 FROM users WHERE user_id = ?", (user_id,)) is not None

    # ---------- so'rovnomalar ----------
    async def list_surveys(self, only_active: bool = False) -> list[Survey]:
        sql = "SELECT * FROM surveys"
        if only_active:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY created_at, rowid"
        return [_row_to_survey(r) for r in await self._fetchall(sql)]

    async def get_survey(self, survey_id: str) -> Survey | None:
        row = await self._fetchone("SELECT * FROM surveys WHERE id = ?", (survey_id,))
        return _row_to_survey(row) if row else None

    async def add_survey(self, survey_id: str, title: str, grades: list[int], questions: list[Question]) -> None:
        await self._execute(
            "INSERT INTO surveys (id, title, grades_json, questions_json) VALUES (?,?,?,?)",
            (
                survey_id,
                title,
                json.dumps(grades),
                json.dumps([q.to_dict() for q in questions], ensure_ascii=False),
            ),
        )

    async def set_survey_active(self, survey_id: str, active: bool) -> None:
        await self._execute("UPDATE surveys SET is_active = ? WHERE id = ?", (int(active), survey_id))

    async def count_submissions(self, survey_id: str) -> int:
        row = await self._fetchone("SELECT COUNT(*) AS c FROM submissions WHERE survey_id = ?", (survey_id,))
        return int(row["c"]) if row else 0

    async def delete_survey(self, survey_id: str) -> bool:
        """Faqat javoblari yo'q so'rovnomani o'chiradi."""
        async with self._write_lock:
            row = await (await self._conn.execute(
                "SELECT COUNT(*) FROM submissions WHERE survey_id = ?", (survey_id,)
            )).fetchone()
            if row and row[0] > 0:
                return False
            cur = await self._conn.execute("DELETE FROM surveys WHERE id = ?", (survey_id,))
            await self._conn.commit()
            return cur.rowcount > 0

    async def surveys_for_grade(self, grade: int, user_id: int) -> tuple[list[Survey], bool]:
        """(hali to'ldirilmagan faol so'rovnomalar, sinf uchun faol so'rovnoma umuman bormi)"""
        active = [s for s in await self.list_surveys(only_active=True) if grade in s.grades]
        rows = await self._fetchall("SELECT survey_id FROM submissions WHERE user_id = ?", (user_id,))
        done = {r["survey_id"] for r in rows}
        return [s for s in active if s.id not in done], bool(active)

    async def has_active_surveys(self) -> bool:
        row = await self._fetchone("SELECT 1 FROM surveys WHERE is_active = 1 LIMIT 1")
        return row is not None

    # ---------- javoblar ----------
    async def save_submission(
        self,
        survey: Survey,
        user_id: int,
        full_name: str,
        grade: str,
        answers: list[str],
    ) -> bool:
        """Barcha javoblarni bitta tranzaksiyada saqlaydi. Takroriy bo'lsa False."""
        async with self._write_lock:
            try:
                cur = await self._conn.execute(
                    "INSERT INTO submissions (survey_id, user_id, full_name, grade) VALUES (?,?,?,?)",
                    (survey.id, user_id, full_name, grade),
                )
                sub_id = cur.lastrowid
                await self._conn.executemany(
                    "INSERT INTO submission_answers (submission_id, q_idx, question, answer) VALUES (?,?,?,?)",
                    [(sub_id, i, survey.questions[i].text, a) for i, a in enumerate(answers)],
                )
                await self._conn.commit()
                return True
            except aiosqlite.IntegrityError:
                await self._conn.rollback()
                return False
            except Exception:
                await self._conn.rollback()
                raise

    # ---------- murojaatlar ----------
    async def link_feedback(self, admin_id: int, admin_msg_id: int, user_id: int, user_name: str) -> None:
        await self._execute(
            "INSERT OR REPLACE INTO feedback_map (admin_id, admin_msg_id, user_id, user_name) VALUES (?,?,?,?)",
            (admin_id, admin_msg_id, user_id, user_name),
        )

    async def get_feedback_target(self, admin_id: int, admin_msg_id: int) -> tuple[int, str] | None:
        row = await self._fetchone(
            "SELECT user_id, user_name FROM feedback_map WHERE admin_id = ? AND admin_msg_id = ?",
            (admin_id, admin_msg_id),
        )
        return (row["user_id"], row["user_name"] or "") if row else None

    # ---------- statistika va eksport ----------
    async def stats(self) -> dict[str, Any]:
        total = (await self._fetchone("SELECT COUNT(*) AS c FROM users"))["c"]
        blocked = (await self._fetchone("SELECT COUNT(*) AS c FROM users WHERE is_blocked = 1"))["c"]
        per_survey = await self._fetchall(
            """SELECT s.id, s.title, s.is_active, COUNT(sub.id) AS c
               FROM surveys s LEFT JOIN submissions sub ON sub.survey_id = s.id
               GROUP BY s.id ORDER BY s.created_at, s.rowid"""
        )
        per_grade = await self._fetchall(
            "SELECT survey_id, grade, COUNT(*) AS c FROM submissions GROUP BY survey_id, grade"
        )
        return {
            "users": total,
            "blocked": blocked,
            "surveys": [dict(r) for r in per_survey],
            "grades": [dict(r) for r in per_grade],
        }

    async def export_data(self) -> list[dict[str, Any]]:
        """Excel uchun: har bir so'rovnoma bo'yicha javob bergan o'quvchilar."""
        result: list[dict[str, Any]] = []
        for survey in await self.list_surveys():
            subs = await self._fetchall(
                """SELECT sub.id, sub.user_id, sub.full_name, sub.grade, sub.created_at,
                          COALESCE(u.username, '') AS username
                   FROM submissions sub LEFT JOIN users u ON u.user_id = sub.user_id
                   WHERE sub.survey_id = ? ORDER BY sub.id""",
                (survey.id,),
            )
            if not subs:
                continue
            ans_rows = await self._fetchall(
                """SELECT a.submission_id, a.q_idx, a.answer
                   FROM submission_answers a JOIN submissions s ON s.id = a.submission_id
                   WHERE s.survey_id = ?""",
                (survey.id,),
            )
            by_sub: dict[int, dict[int, str]] = {}
            for r in ans_rows:
                by_sub.setdefault(r["submission_id"], {})[r["q_idx"]] = r["answer"]
            result.append(
                {
                    "survey": survey,
                    "submissions": [
                        {
                            "user_id": s["user_id"],
                            "username": s["username"],
                            "full_name": s["full_name"],
                            "grade": s["grade"],
                            "created_at": s["created_at"],
                            "answers": [by_sub.get(s["id"], {}).get(i, "") for i in range(len(survey.questions))],
                        }
                        for s in subs
                    ],
                }
            )
        return result
