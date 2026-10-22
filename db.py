"""SQLite storage for users, skills and swap sessions."""
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).with_name("skillswap.db")
LEVELS = ["Beginner", "Intermediate", "Advanced"]


def connect(path=DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS skills (
            id      INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name    TEXT NOT NULL,             -- stored lowercase for matching
            kind    TEXT NOT NULL CHECK (kind IN ('teach', 'want')),
            level   TEXT NOT NULL CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
            UNIQUE (user_id, name, kind)
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY,
            teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            learner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            skill      TEXT NOT NULL,
            minutes    INTEGER NOT NULL DEFAULT 60,
            day        TEXT NOT NULL
        );
        """
    )
    return conn


# ---------- users ----------

def add_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (?)", (name.strip(),))
    conn.commit()
    return cur.lastrowid


def list_users(conn):
    return conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()


def delete_user(conn, user_id):
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()


# ---------- skills ----------

def set_skill(conn, user_id, name, kind, level):
    """Add a skill, or update its level if the user already has it."""
    conn.execute(
        """INSERT INTO skills (user_id, name, kind, level) VALUES (?, ?, ?, ?)
           ON CONFLICT (user_id, name, kind) DO UPDATE SET level = excluded.level""",
        (user_id, name.strip().lower(), kind, level),
    )
    conn.commit()


def remove_skill(conn, skill_id):
    conn.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
    conn.commit()


def skills_for(conn, user_id, kind):
    return conn.execute(
        "SELECT id, name, level FROM skills WHERE user_id = ? AND kind = ? ORDER BY name",
        (user_id, kind),
    ).fetchall()


def all_profiles(conn):
    """{user_id: {"name", "teaches": {skill: level}, "wants": {skill: level}}}"""
    profiles = {
        u["id"]: {"name": u["name"], "teaches": {}, "wants": {}} for u in list_users(conn)
    }
    for row in conn.execute("SELECT user_id, name, kind, level FROM skills"):
        key = "teaches" if row["kind"] == "teach" else "wants"
        profiles[row["user_id"]][key][row["name"]] = row["level"]
    return profiles


# ---------- sessions ----------

def log_session(conn, teacher_id, learner_id, skill, minutes=60, day=None):
    conn.execute(
        "INSERT INTO sessions (teacher_id, learner_id, skill, minutes, day) VALUES (?, ?, ?, ?, ?)",
        (teacher_id, learner_id, skill.strip().lower(), minutes, day or date.today().isoformat()),
    )
    conn.commit()


def sessions_for(conn, user_id):
    return conn.execute(
        """SELECT s.*, t.name AS teacher, l.name AS learner
           FROM sessions s
           JOIN users t ON t.id = s.teacher_id
           JOIN users l ON l.id = s.learner_id
           WHERE s.teacher_id = ? OR s.learner_id = ?
           ORDER BY s.day DESC, s.id DESC""",
        (user_id, user_id),
    ).fetchall()


def sessions_between(conn, a, b):
    return conn.execute(
        """SELECT s.*, t.name AS teacher, l.name AS learner
           FROM sessions s
           JOIN users t ON t.id = s.teacher_id
           JOIN users l ON l.id = s.learner_id
           WHERE (s.teacher_id = ? AND s.learner_id = ?) OR (s.teacher_id = ? AND s.learner_id = ?)
           ORDER BY s.day DESC, s.id DESC""",
        (a, b, b, a),
    ).fetchall()
