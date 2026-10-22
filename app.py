"""Skill Swap Matchmaking - Flet UI.  Run:  python app.py"""
import sqlite3

import flet as ft

import db
import matching
import seed

LEVEL_COLORS = {
    "Beginner": ft.Colors.GREEN_400,
    "Intermediate": ft.Colors.AMBER_400,
    "Advanced": ft.Colors.DEEP_ORANGE_400,
}

BADGE_COLORS = {
    "Newcomer": ft.Colors.LIGHT_GREEN_400,
    "Bronze": ft.Colors.BROWN_300,
    "Silver": ft.Colors.BLUE_GREY_200,
    "Gold": ft.Colors.AMBER_400,
    "Master": ft.Colors.PURPLE_300,
}


def badge_icon(name, size=36):
    color = BADGE_COLORS.get(name, ft.Colors.OUTLINE)
    return ft.Icon(ft.Icons.WORKSPACE_PREMIUM if name else ft.Icons.LOCK_OUTLINE,
                   color=color, size=size)


def level_chip(level):
    return ft.Container(
        ft.Text(level, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
        bgcolor=LEVEL_COLORS[level], border_radius=12,
        padding=ft.padding.symmetric(2, 8),
    )


def skill_tag(skill):
    return ft.Container(
        ft.Text(skill.title(), size=12),
        border=ft.border.all(1, ft.Colors.OUTLINE), border_radius=12,
        padding=ft.padding.symmetric(3, 10),
    )


def section_title(text, icon):
    return ft.Row([ft.Icon(icon, color=ft.Colors.PRIMARY),
                   ft.Text(text, size=18, weight=ft.FontWeight.BOLD)])


def main(page: ft.Page):
    conn = db.connect()
    if not db.list_users(conn):
        seed.seed(conn)

    page.title = "Skill Swap"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.DEEP_ORANGE)
    page.window.width, page.window.height = 900, 780
    page.padding = 0

    state = {"user": None, "log_partner": None}

    def toast(msg):
        page.open(ft.SnackBar(ft.Text(msg)))

    # ---------------- header: current user ----------------

    user_dd = ft.Dropdown(label="Signed in as", width=220, dense=True)

    def refresh_users(select_id=None):
        users = db.list_users(conn)
        user_dd.options = [ft.dropdown.Option(str(u["id"]), u["name"]) for u in users]
        if select_id is not None:
            state["user"] = select_id
        elif state["user"] not in {u["id"] for u in users}:
            state["user"] = users[0]["id"] if users else None
        user_dd.value = str(state["user"]) if state["user"] else None

    def on_user_change(e):
        state["user"] = int(user_dd.value)
        render()

    user_dd.on_change = on_user_change

    def open_add_user(_):
        name = ft.TextField(label="Name", autofocus=True)

        def save(_):
            if not name.value.strip():
                name.error_text = "Enter a name"
                page.update()
                return
            try:
                uid = db.add_user(conn, name.value)
            except sqlite3.IntegrityError:
                name.error_text = "That name is taken"
                page.update()
                return
            page.close(dlg)
            refresh_users(uid)
            nav.selected_index = 0
            render()
            toast(f"Welcome, {name.value.strip()}! Add your skills.")

        name.on_submit = save
        dlg = ft.AlertDialog(
            title=ft.Text("New user"), content=name,
            actions=[ft.TextButton("Cancel", on_click=lambda _: page.close(dlg)),
                     ft.FilledButton("Create", on_click=save)],
        )
        page.open(dlg)

    header = ft.Container(
        ft.Row([
            ft.Row([ft.Icon(ft.Icons.SWAP_HORIZONTAL_CIRCLE, size=30, color=ft.Colors.PRIMARY),
                    ft.Text("Skill Swap", size=24, weight=ft.FontWeight.BOLD)]),
            ft.Row([user_dd,
                    ft.IconButton(ft.Icons.PERSON_ADD, tooltip="New user", on_click=open_add_user)]),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(12, 20), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
    )

    # ---------------- 1. Profile ----------------

    def skill_list_editor(kind, title, icon):
        uid = state["user"]
        rows = [
            ft.Row([
                ft.Text(s["name"].title(), expand=True, size=15),
                level_chip(s["level"]),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, tooltip="Remove",
                              on_click=lambda _, sid=s["id"]: (db.remove_skill(conn, sid), render())),
            ])
            for s in db.skills_for(conn, uid, kind)
        ] or [ft.Text("Nothing yet.", italic=True, color=ft.Colors.ON_SURFACE_VARIANT)]

        name = ft.TextField(label="Skill", expand=True, dense=True)
        level = ft.Dropdown(width=150, dense=True, value="Beginner",
                            options=[ft.dropdown.Option(l) for l in matching.LEVELS])

        def add(_):
            if not name.value.strip():
                name.error_text = "Required"
                page.update()
                return
            db.set_skill(conn, uid, name.value, kind, level.value)
            render()

        name.on_submit = add
        return ft.Card(ft.Container(ft.Column([
            section_title(title, icon),
            *rows,
            ft.Divider(),
            ft.Row([name, level, ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=add, tooltip="Add")]),
        ]), padding=16))

    def profile_view():
        return ft.Column([
            ft.Text("Your skill profile", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("For skills you want, pick the level you're aiming for. "
                    "A partner must teach at that level or higher.",
                    color=ft.Colors.ON_SURFACE_VARIANT),
            skill_list_editor("teach", "I can teach", ft.Icons.SCHOOL),
            skill_list_editor("want", "I want to learn", ft.Icons.LIGHTBULB),
        ], scroll=ft.ScrollMode.AUTO, spacing=12)

    # ---------------- 2. Matches ----------------

    def open_history(partner_id, partner_name):
        rows = db.sessions_between(conn, state["user"], partner_id)
        items = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.HISTORY_EDU),
                title=ft.Text(f"{r['teacher']} taught {r['learner']}: {r['skill'].title()}"),
                subtitle=ft.Text(f"{r['day']} · {r['minutes']} min"),
            ) for r in rows
        ] or [ft.Text("No sessions together yet.")]
        dlg = ft.AlertDialog(
            title=ft.Text(f"History with {partner_name}"),
            content=ft.Column(items, tight=True, scroll=ft.ScrollMode.AUTO, height=300, width=420),
            actions=[ft.TextButton("Close", on_click=lambda _: page.close(dlg))],
        )
        page.open(dlg)

    def go_log(partner_id):
        state["log_partner"] = partner_id
        nav.selected_index = 2
        render()

    def match_card(m, two_way):
        def line(label, skills):
            return ft.Row([ft.Text(label, width=130, color=ft.Colors.ON_SURFACE_VARIANT),
                           *(map(skill_tag, skills) if skills else [ft.Text("—")])], wrap=True)

        return ft.Card(ft.Container(ft.Column([
            ft.Row([
                ft.CircleAvatar(content=ft.Text(m["partner"][0])),
                ft.Text(m["partner"], size=17, weight=ft.FontWeight.BOLD, expand=True),
                ft.Container(
                    ft.Text("SWAP" if two_way else "ONE-WAY", size=11,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    bgcolor=ft.Colors.GREEN_400 if two_way else ft.Colors.BLUE_GREY_300,
                    border_radius=12, padding=ft.padding.symmetric(2, 8)),
            ]),
            line("They teach you", m["they_teach"]),
            line("You teach them", m["i_teach"]),
            ft.Row([
                ft.TextButton("History", icon=ft.Icons.HISTORY,
                              on_click=lambda _: open_history(m["partner_id"], m["partner"])),
                ft.FilledTonalButton("Log session", icon=ft.Icons.ADD_TASK,
                                     on_click=lambda _: go_log(m["partner_id"])),
            ], alignment=ft.MainAxisAlignment.END),
        ]), padding=16), opacity=1 if two_way else 0.85)

    def matches_view():
        profiles = db.all_profiles(conn)
        swaps, maybes = matching.find_matches(profiles, state["user"])
        empty = ft.Text("No matches yet. Add more skills to your profile.", italic=True,
                        color=ft.Colors.ON_SURFACE_VARIANT)
        return ft.Column([
            section_title(f"Perfect swaps ({len(swaps)})", ft.Icons.SYNC_ALT),
            ft.Text("You both have something the other wants.", color=ft.Colors.ON_SURFACE_VARIANT),
            *([match_card(m, True) for m in swaps] or [empty]),
            ft.Divider(height=30),
            section_title(f"Maybe ({len(maybes)})", ft.Icons.ARROW_FORWARD),
            ft.Text("One-way: only one of you can teach the other. Lower priority.",
                    color=ft.Colors.ON_SURFACE_VARIANT),
            *([match_card(m, False) for m in maybes] or [ft.Text("None.", italic=True)]),
        ], scroll=ft.ScrollMode.AUTO, spacing=10)

    # ---------------- 3. Log session ----------------

    def log_view():
        uid = state["user"]
        profiles = db.all_profiles(conn)
        me = profiles[uid]
        partners = [(pid, p["name"]) for pid, p in profiles.items() if pid != uid]

        partner_dd = ft.Dropdown(label="Partner", width=260,
                                 options=[ft.dropdown.Option(str(pid), n) for pid, n in partners])
        role = ft.RadioGroup(ft.Row([ft.Radio(value="taught", label="I taught"),
                                     ft.Radio(value="learned", label="I learned")]), value="taught")
        skill_dd = ft.Dropdown(label="Skill", width=260)
        minutes = ft.TextField(label="Minutes", value="60", width=120,
                               keyboard_type=ft.KeyboardType.NUMBER)
        hint = ft.Text("", color=ft.Colors.ON_SURFACE_VARIANT, size=12)

        def update_skills(_=None):
            skill_dd.options, skill_dd.value = [], None
            if partner_dd.value:
                other = profiles[int(partner_dd.value)]
                skills = (matching.teachable(me, other) if role.value == "taught"
                          else matching.teachable(other, me))
                skill_dd.options = [ft.dropdown.Option(s, s.title()) for s in skills]
                skill_dd.value = skills[0] if skills else None
                hint.value = ("" if skills else
                              "No matching skill in this direction. Check both profiles.")
            page.update()

        partner_dd.on_change = update_skills
        role.on_change = update_skills
        if state["log_partner"] in profiles and state["log_partner"] != uid:
            partner_dd.value = str(state["log_partner"])
            state["log_partner"] = None
            # fill skills once the view is mounted
            other = profiles[int(partner_dd.value)]
            skills = matching.teachable(me, other) or matching.teachable(other, me)
            if not matching.teachable(me, other):
                role.value = "learned"
            skill_dd.options = [ft.dropdown.Option(s, s.title()) for s in skills]
            skill_dd.value = skills[0] if skills else None

        def save(_):
            if not partner_dd.value or not skill_dd.value:
                toast("Pick a partner and a skill.")
                return
            try:
                mins = int(minutes.value)
                assert 0 < mins <= 600
            except (ValueError, AssertionError):
                minutes.error_text = "1-600"
                page.update()
                return
            pid = int(partner_dd.value)
            teacher, learner = (uid, pid) if role.value == "taught" else (pid, uid)
            db.log_session(conn, teacher, learner, skill_dd.value, mins)
            toast("Session logged! Check your Dashboard for progress.")
            render()

        recent = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.NORTH_EAST if r["teacher_id"] == uid else ft.Icons.SOUTH_WEST),
                title=ft.Text(f"{'Taught' if r['teacher_id'] == uid else 'Learned'} "
                              f"{r['skill'].title()} "
                              f"{'to' if r['teacher_id'] == uid else 'from'} "
                              f"{r['learner'] if r['teacher_id'] == uid else r['teacher']}"),
                subtitle=ft.Text(f"{r['day']} · {r['minutes']} min"),
                dense=True,
            ) for r in db.sessions_for(conn, uid)[:10]
        ] or [ft.Text("No sessions yet.", italic=True)]

        return ft.Column([
            ft.Text("Log a completed swap session", size=22, weight=ft.FontWeight.BOLD),
            ft.Card(ft.Container(ft.Column([
                partner_dd, role, skill_dd, hint, minutes,
                ft.FilledButton("Save session", icon=ft.Icons.CHECK, on_click=save),
            ], spacing=12), padding=16)),
            section_title("Recent sessions", ft.Icons.HISTORY),
            *recent,
        ], scroll=ft.ScrollMode.AUTO, spacing=12)

    # ---------------- 4. Dashboard / progress ladder ----------------

    def stat(label, value, icon):
        return ft.Card(ft.Container(ft.Column([
            ft.Icon(icon, color=ft.Colors.PRIMARY),
            ft.Text(str(value), size=26, weight=ft.FontWeight.BOLD),
            ft.Text(label, color=ft.Colors.ON_SURFACE_VARIANT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=14, width=150))

    def ladder_card(p):
        badge = p["badge"]
        if p["next"]:
            needed = p["next"][0] - p["total"]
            nxt = f"{needed} more to {p['next'][1]}"
        else:
            nxt = "Top tier reached!"
        name = badge[1] if badge else None
        return ft.Card(ft.Container(ft.Row([
            badge_icon(name, 40),
            ft.Column([
                ft.Row([ft.Text(p["skill"].title(), size=17, weight=ft.FontWeight.BOLD),
                        ft.Text(name or "", color=BADGE_COLORS.get(name))]),
                ft.ProgressBar(value=p["progress"], height=8, border_radius=4,
                               color=BADGE_COLORS.get(p["next"][1] if p["next"] else name)),
                ft.Text(f"{p['taught']} taught · {p['learned']} learned · {p['minutes']} min  —  {nxt}",
                        size=12, color=ft.Colors.ON_SURFACE_VARIANT),
            ], expand=True, spacing=6),
        ], spacing=16), padding=16))

    def dashboard_view():
        uid = state["user"]
        sessions = db.sessions_for(conn, uid)
        progress = matching.skill_progress(sessions, uid)
        taught = sum(1 for s in sessions if s["teacher_id"] == uid)
        hours = sum(s["minutes"] for s in sessions) / 60
        partners = {s["learner_id"] if s["teacher_id"] == uid else s["teacher_id"] for s in sessions}

        legend = ft.Row([
            ft.Row([badge_icon(name, 16),
                    ft.Text(f"{name} ({n}+)", size=12, color=ft.Colors.ON_SURFACE_VARIANT)],
                   spacing=2, tight=True)
            for n, name, _ in matching.BADGE_TIERS
        ], wrap=True, spacing=14)

        return ft.Column([
            ft.Text(f"{db.all_profiles(conn)[uid]['name']}'s progress ladder",
                    size=22, weight=ft.FontWeight.BOLD),
            ft.Row([
                stat("Sessions", len(sessions), ft.Icons.EVENT_AVAILABLE),
                stat("Taught", taught, ft.Icons.NORTH_EAST),
                stat("Learned", len(sessions) - taught, ft.Icons.SOUTH_WEST),
                stat("Hours", f"{hours:.1f}", ft.Icons.TIMER),
                stat("Partners", len(partners), ft.Icons.GROUP),
            ], wrap=True),
            section_title("Skill badges", ft.Icons.MILITARY_TECH),
            legend,
            *([ladder_card(p) for p in progress]
              or [ft.Text("Log a session to earn your first badge.", italic=True)]),
        ], scroll=ft.ScrollMode.AUTO, spacing=12)

    # ---------------- layout & navigation ----------------

    views = [profile_view, matches_view, log_view, dashboard_view]
    body = ft.Container(expand=True, padding=20)

    def render(_=None):
        refresh_users()
        if state["user"] is None:
            body.content = ft.Column([ft.Text("Create a user to get started."),
                                      ft.FilledButton("New user", on_click=open_add_user)])
        else:
            body.content = views[nav.selected_index]()
        page.update()

    nav = ft.NavigationBar(
        selected_index=0, on_change=render,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE,
                                        selected_icon=ft.Icons.PERSON, label="Profile"),
            ft.NavigationBarDestination(icon=ft.Icons.SYNC_ALT, label="Matches"),
            ft.NavigationBarDestination(icon=ft.Icons.ADD_TASK, label="Log"),
            ft.NavigationBarDestination(icon=ft.Icons.LEADERBOARD_OUTLINED,
                                        selected_icon=ft.Icons.LEADERBOARD, label="Dashboard"),
        ],
    )

    page.navigation_bar = nav
    page.add(ft.Column([header, body], expand=True, spacing=0))
    render()


if __name__ == "__main__":
    ft.app(target=main)
