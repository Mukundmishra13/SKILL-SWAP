"""Matching and progress logic. Pure functions, no UI or database code.

A profile looks like:
    {"name": "Asha", "teaches": {"python": "Advanced"}, "wants": {"guitar": "Beginner"}}

The level on a "want" is the level the learner is aiming for, so a teacher
can only cover it if their own level is at least that high.
"""
from collections import defaultdict

LEVELS = ["Beginner", "Intermediate", "Advanced"]
RANK = {level: i for i, level in enumerate(LEVELS)}


def can_teach(teacher_level, wanted_level):
    return RANK[teacher_level] >= RANK[wanted_level]


def build_teacher_index(profiles):
    """skill -> [(user_id, level)] for everyone who teaches it.

    Built once in O(total skills). Lets us look up candidate partners per skill
    instead of comparing every user with every other user (O(n^2)).
    """
    index = defaultdict(list)
    for uid, p in profiles.items():
        for skill, level in p["teaches"].items():
            index[skill].append((uid, level))
    return index


def teachable(teacher, learner):
    """Skills `teacher` can teach `learner` at the level the learner wants."""
    return sorted(
        skill
        for skill, wanted in learner["wants"].items()
        if skill in teacher["teaches"] and can_teach(teacher["teaches"][skill], wanted)
    )


def find_matches(profiles, user_id, index=None):
    """Return (swaps, maybes) for one user.

    swaps  - two-way: both people can teach each other something.
    maybes - one-way: only one side benefits (lower priority).
    Each item: {"partner_id", "partner", "they_teach", "i_teach", "score"}.
    """
    index = index if index is not None else build_teacher_index(profiles)
    me = profiles[user_id]

    # Candidates who can teach me something, found via the index.
    candidates = set()
    for skill in me["wants"]:
        for uid, _ in index.get(skill, []):
            candidates.add(uid)
    # Also people who want something I teach (needed for one-way "maybe" matches).
    my_teach = set(me["teaches"])
    for uid, p in profiles.items():
        if my_teach & set(p["wants"]):
            candidates.add(uid)
    candidates.discard(user_id)

    swaps, maybes = [], []
    for uid in candidates:
        other = profiles[uid]
        they_teach = teachable(other, me)
        i_teach = teachable(me, other)
        if not they_teach and not i_teach:
            continue
        # Share of both people's wants that this pairing covers (0..1).
        wants_total = len(me["wants"]) + len(other["wants"])
        match = {
            "partner_id": uid,
            "partner": other["name"],
            "they_teach": they_teach,
            "i_teach": i_teach,
            "score": len(they_teach) + len(i_teach),
            "coverage": (len(they_teach) + len(i_teach)) / wants_total if wants_total else 0,
        }
        (swaps if they_teach and i_teach else maybes).append(match)

    key = lambda m: (-m["score"], m["partner"].lower())
    return sorted(swaps, key=key), sorted(maybes, key=key)


# ---------- progress ladder ----------

# (sessions needed, badge name, emoji)
BADGE_TIERS = [
    (1, "Newcomer", "🌱"),
    (3, "Bronze", "🥉"),
    (6, "Silver", "🥈"),
    (10, "Gold", "🥇"),
    (15, "Master", "🏆"),
]


def badge_for(count):
    """Return (current_badge or None, next_badge or None, progress 0..1 toward next)."""
    current, nxt = None, None
    for tier in BADGE_TIERS:
        if count >= tier[0]:
            current = tier
        else:
            nxt = tier
            break
    if nxt is None:
        return current, None, 1.0
    floor = current[0] if current else 0
    return current, nxt, (count - floor) / (nxt[0] - floor)


def skill_progress(sessions, user_id):
    """Per-skill ladder from completed sessions (teaching and learning both count).

    Returns a list of dicts sorted by most sessions first.
    """
    stats = defaultdict(lambda: {"taught": 0, "learned": 0, "minutes": 0})
    for s in sessions:
        if s["teacher_id"] == user_id:
            stats[s["skill"]]["taught"] += 1
        elif s["learner_id"] == user_id:
            stats[s["skill"]]["learned"] += 1
        else:
            continue
        stats[s["skill"]]["minutes"] += s["minutes"]

    out = []
    for skill, st in stats.items():
        total = st["taught"] + st["learned"]
        current, nxt, progress = badge_for(total)
        out.append({"skill": skill, "total": total, **st,
                    "badge": current, "next": nxt, "progress": progress})
    return sorted(out, key=lambda x: (-x["total"], x["skill"]))
