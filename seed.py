"""Demo data so the app isn't empty on first run. Run directly to reset:  python seed.py"""
import db

DEMO = {
    "Mukund": {"teach": {"python": "Advanced", "dsa": "Intermediate"},
               "want": {"guitar": "Beginner", "ui design": "Intermediate"}},
    "Ananya": {"teach": {"guitar": "Advanced", "photography": "Intermediate"},
               "want": {"python": "Intermediate"}},
    "Rahul":  {"teach": {"ui design": "Advanced", "figma": "Advanced"},
               "want": {"dsa": "Beginner", "public speaking": "Beginner"}},
    "Sneha":  {"teach": {"guitar": "Intermediate", "public speaking": "Advanced"},
               "want": {"photography": "Beginner"}},
    "Kabir":  {"teach": {"python": "Beginner", "cooking": "Advanced"},
               "want": {"guitar": "Intermediate", "dsa": "Advanced"}},
    "Priya":  {"teach": {"photography": "Advanced", "dsa": "Advanced"},
               "want": {"figma": "Beginner", "cooking": "Beginner"}},
}

SESSIONS = [  # (teacher, learner, skill, minutes, day)
    ("Mukund", "Ananya", "python", 60, "2026-10-12"),
    ("Ananya", "Mukund", "guitar", 45, "2026-10-13"),
    ("Mukund", "Ananya", "python", 60, "2026-10-16"),
    ("Rahul", "Mukund", "ui design", 90, "2026-10-17"),
    ("Mukund", "Rahul", "dsa", 60, "2026-10-18"),
    ("Mukund", "Ananya", "python", 60, "2026-10-20"),
]


def seed(conn):
    ids = {}
    for name, skills in DEMO.items():
        ids[name] = db.add_user(conn, name)
        for kind in ("teach", "want"):
            for skill, level in skills[kind].items():
                db.set_skill(conn, ids[name], skill, kind, level)
    for teacher, learner, skill, minutes, day in SESSIONS:
        db.log_session(conn, ids[teacher], ids[learner], skill, minutes, day)


if __name__ == "__main__":
    db.DB_PATH.unlink(missing_ok=True)
    seed(db.connect())
    print("Database reset with demo data.")
