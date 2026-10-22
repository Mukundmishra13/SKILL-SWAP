# Skill Swap Matchmaking

A peer-to-peer alternative to formal mentorship: people list what they can **teach** and
what they want to **learn**, and the app pairs up people who can **teach each other**.

Built with **Python + [Flet](https://flet.dev)** (Flutter UI in Python) and **SQLite**.

## Features

| Requirement | Where |
|---|---|
| Skill profiles: teach / want lists, each tagged Beginner / Intermediate / Advanced | **Profile** tab |
| Bidirectional matching (A teaches what B wants **and** vice versa) | **Matches** tab → "Perfect swaps" |
| Progress ladder: log completed sessions, level up badges per skill | **Log** + **Dashboard** tabs |
| Bonus: one-way "maybe" matches as a lower-priority list | **Matches** tab → "Maybe" |
| Bonus: session history per pair | "History" button on each match card |

Badge tiers per skill (teaching and learning sessions both count):
Newcomer (1) → Bronze (3) → Silver (6) → Gold (10) → Master (15).

## Run it

```bash
pip install -r requirements.txt
python app.py              # desktop window
python test_matching.py    # unit tests for the matching logic
python seed.py             # reset the database to demo data
```

On first launch the database (`skillswap.db`) is filled with 6 demo users so you can try
matching straight away. Use the **Signed in as** dropdown to switch between users, or the
add-user button to create your own.

## Project structure

```
app.py            Flet UI: Profile, Matches, Log, Dashboard screens
matching.py       Pure matching + badge logic (no UI, no DB) - easy to test
db.py             SQLite schema and queries
seed.py           Demo data
test_matching.py  Unit tests
```

---

## Write-up: the matching approach

### Rules
- A user's **want** level is the level they want to reach, so a teacher only counts if
  `teacher_level >= wanted_level` (an Advanced Python teacher can help someone who wants
  Intermediate Python, but a Beginner can't).
- `teachable(X, Y)` = the skills Y wants that X can teach at a high enough level.
- **Swap (two-way)**: `teachable(A, B)` and `teachable(B, A)` are both non-empty.
- **Maybe (one-way)**: exactly one of them is non-empty.
- Matches are ranked by `score = number of skills exchanged in both directions`, so
  partners who can swap several skills come first.

### Naive approach: O(n²)
Compare every user with every other user. With `n` users and `k` skills each that is
`O(n² · k)`. Fine for 50 students, too slow for 50,000.

### What the app does: an inverted index
`build_teacher_index()` builds one map, `skill -> [(user, level), ...]`, in a single pass
over all skills (`O(n · k)`).

To find matches for user A:
1. For each skill A **wants**, look up the index to get only the people who **teach** it.
   These are the only possible two-way partners.
2. For each such candidate, check whether they want something A teaches (a set lookup).

So the cost per user depends on **how many people share A's skills**, not on the total
number of users. Unrelated users are never touched.

### Scaling further
| Users | Approach |
|---|---|
| Hundreds | Current approach, recomputed on demand (instant). |
| Tens of thousands | Same index, but as a **database index** on `skills(name, kind)` so candidate lookup is a SQL query instead of loading all profiles into memory. |
| Millions | Precompute matches in a background job when a profile changes (only the users who share the changed skill need updating), cache results, and paginate. Normalise skill names (e.g. "py" / "Python 3" → `python`) with a fixed skill catalogue so matching isn't broken by typos. |

### Progress ladder
Each logged session is stored as `(teacher, learner, skill, minutes, day)`. Badges are
computed from these rows (not stored), so they can't drift out of sync with history:
per skill, `total = taught + learned`, mapped onto the tier table, with a progress bar
toward the next tier.
