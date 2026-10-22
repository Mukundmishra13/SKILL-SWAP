"""Run with:  python -m pytest -q   (or just: python test_matching.py)"""
from matching import badge_for, find_matches, skill_progress

PROFILES = {
    1: {"name": "Asha", "teaches": {"python": "Advanced"}, "wants": {"guitar": "Beginner"}},
    2: {"name": "Ben", "teaches": {"guitar": "Intermediate"}, "wants": {"python": "Intermediate"}},
    3: {"name": "Chen", "teaches": {"guitar": "Advanced"}, "wants": {"cooking": "Beginner"}},
    4: {"name": "Dev", "teaches": {"python": "Beginner"}, "wants": {"guitar": "Beginner"}},
}


def test_two_way_swap():
    swaps, _ = find_matches(PROFILES, 1)
    assert [m["partner"] for m in swaps] == ["Ben"]
    assert swaps[0]["they_teach"] == ["guitar"] and swaps[0]["i_teach"] == ["python"]


def test_coverage():
    swaps, _ = find_matches(PROFILES, 1)
    # Asha wants 1 skill, Ben wants 1; both are covered -> 100%.
    assert swaps[0]["coverage"] == 1.0


def test_one_way_is_maybe_not_swap():
    _, maybes = find_matches(PROFILES, 1)
    # Chen can teach Asha guitar, but Asha has nothing Chen wants.
    assert "Chen" in [m["partner"] for m in maybes]


def test_level_too_low_does_not_match():
    # Dev teaches Python at Beginner; Ben wants Intermediate -> Dev can't teach Ben.
    # Ben can still teach Dev guitar, so it's only a one-way "maybe".
    swaps, maybes = find_matches(PROFILES, 2)
    assert "Dev" not in [m["partner"] for m in swaps]
    dev = next(m for m in maybes if m["partner"] == "Dev")
    assert dev["they_teach"] == [] and dev["i_teach"] == ["guitar"]


def test_never_matches_self():
    swaps, maybes = find_matches(PROFILES, 1)
    assert 1 not in [m["partner_id"] for m in swaps + maybes]


def test_badges():
    assert badge_for(0)[0] is None
    assert badge_for(3)[0][1] == "Bronze"
    current, nxt, progress = badge_for(4)
    assert nxt[1] == "Silver" and abs(progress - 1 / 3) < 1e-9
    assert badge_for(99)[1] is None


def test_skill_progress_counts_both_roles():
    sessions = [
        {"teacher_id": 1, "learner_id": 2, "skill": "python", "minutes": 60},
        {"teacher_id": 2, "learner_id": 1, "skill": "guitar", "minutes": 30},
        {"teacher_id": 1, "learner_id": 2, "skill": "python", "minutes": 60},
    ]
    prog = {p["skill"]: p for p in skill_progress(sessions, 1)}
    assert prog["python"]["taught"] == 2 and prog["guitar"]["learned"] == 1


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
