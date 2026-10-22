"""Skill Swap Matchmaking - Flet UI.  Run:  python app.py"""
import sqlite3

import flet as ft

import db
import matching
import seed

# ---------------- design tokens ----------------

BG = "#0D0F14"
SURFACE = "#141821"
CARD = "#1A1F2A"
BORDER = "#272D3A"
TEXT = "#E8ECF3"
MUTED = "#8E97A8"
ORANGE = "#FF7A18"
PINK = "#FF3D77"
TEAL = "#2DD4BF"

LEVEL_COLORS = {"Beginner": "#4ADE80", "Intermediate": "#FBBF24", "Advanced": "#FB7185"}
BADGE_COLORS = {
    "Newcomer": "#86EFAC",
    "Bronze": "#D6A27A",
    "Silver": "#CBD5E1",
    "Gold": "#FACC15",
    "Master": "#C084FC",
}
AVATAR_GRADIENTS = [
    ("#FF7A18", "#FF3D77"), ("#2DD4BF", "#3B82F6"), ("#A78BFA", "#EC4899"),
    ("#FBBF24", "#F97316"), ("#34D399", "#059669"), ("#60A5FA", "#8B5CF6"),
]

FIELD = dict(border_radius=12, border_color=BORDER, focused_border_color=ORANGE,
             filled=True, fill_color=SURFACE, text_size=14)
EASE = ft.Animation(180, ft.AnimationCurve.EASE_OUT)


# ---------------- small components ----------------

def tint(color, opacity=0.14):
    return ft.Colors.with_opacity(opacity, color)


def gradient(c1=ORANGE, c2=PINK):
    return ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
                             colors=[c1, c2])


def txt(value, size=14, weight=None, color=TEXT, **kw):
    return ft.Text(value, size=size, weight=weight, color=color, **kw)


def bold(value, size=16, color=TEXT, **kw):
    return txt(value, size, ft.FontWeight.BOLD, color, **kw)


def card(content, padding=20, hover=False, **kw):
    c = ft.Container(content, bgcolor=CARD, border_radius=18, padding=padding,
                     border=ft.border.all(1, BORDER), **kw)
    if hover:
        c.animate, c.animate_scale = EASE, EASE

        def on_hover(e):
            on = e.data == "true"
            c.scale = 1.015 if on else 1
            c.border = ft.border.all(1, tint(ORANGE, 0.55) if on else BORDER)
            c.update()

        c.on_hover = on_hover
    return c


def avatar(name, size=44, ring=False):
    c1, c2 = AVATAR_GRADIENTS[sum(map(ord, name)) % len(AVATAR_GRADIENTS)]
    return ft.Container(
        bold(name[:1].upper(), size * 0.42, "white"),
        width=size, height=size, border_radius=size / 2, gradient=gradient(c1, c2),
        alignment=ft.alignment.center,
        border=ft.border.all(3, ft.Colors.with_opacity(0.8, "white")) if ring else None,
    )


def icon_badge(icon, color, size=40):
    return ft.Container(ft.Icon(icon, color=color, size=size * 0.5), width=size, height=size,
                        border_radius=size * 0.3, bgcolor=tint(color, 0.16),
                        alignment=ft.alignment.center)


def pill(text, color, dot=None, sub=None, on_delete=None, size=13):
    items = []
    if dot:
        items.append(ft.Container(width=8, height=8, border_radius=4, bgcolor=dot))
    items.append(txt(text, size, ft.FontWeight.W_600, color))
    if sub:
        items.append(txt(sub, size - 2, color=MUTED))
    if on_delete:
        items.append(ft.Container(ft.Icon(ft.Icons.CLOSE_ROUNDED, size=14, color=MUTED),
                                  on_click=on_delete, border_radius=10, padding=2,
                                  tooltip="Remove"))
    return ft.Container(ft.Row(items, spacing=6, tight=True), bgcolor=tint(color, 0.12),
                        border=ft.border.all(1, tint(color, 0.35)), border_radius=20,
                        padding=ft.padding.symmetric(6, 12))


def primary_button(text, icon, on_click, small=False):
    return ft.Container(
        ft.Row([ft.Icon(icon, color="white", size=16 if small else 18),
                txt(text, 13 if small else 14, ft.FontWeight.W_600, "white")],
               tight=True, spacing=8),
        gradient=gradient(), border_radius=12, on_click=on_click, ink=True,
        padding=ft.padding.symmetric(9 if small else 13, 16 if small else 22),
        shadow=ft.BoxShadow(blur_radius=16, color=tint(PINK, 0.3), offset=ft.Offset(0, 5)),
    )


def ghost_button(text, icon, on_click):
    return ft.TextButton(text, icon=icon, on_click=on_click,
                         style=ft.ButtonStyle(color=MUTED, shape=ft.RoundedRectangleBorder(radius=12)))


def page_header(title, subtitle):
    return ft.Column([bold(title, 26), txt(subtitle, 14, color=MUTED)], spacing=4)


def section_header(title, icon, color=ORANGE, count=None, subtitle=None):
    row = [icon_badge(icon, color, 34), bold(title, 18)]
    if count is not None:
        row.append(pill(str(count), color, size=12))
    col = [ft.Row(row, spacing=12)]
    if subtitle:
        col.append(txt(subtitle, 13, color=MUTED))
    return ft.Column(col, spacing=6)


def empty_state(icon, title, subtitle):
    return card(ft.Column([
        icon_badge(icon, MUTED, 56), bold(title, 16),
        txt(subtitle, 13, color=MUTED, text_align=ft.TextAlign.CENTER),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), padding=32)


def progress_bar(value, color):
    return ft.ProgressBar(value=value, color=color, bgcolor=BORDER, height=7, border_radius=4)


# ---------------- app ----------------

def main(page: ft.Page):
    conn = db.connect()
    if not db.list_users(conn):
        seed.seed(conn)

    page.title = "Skill Swap"
    page.fonts = {"Poppins": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf"}
    theme = ft.Theme(font_family="Poppins", color_scheme_seed=ORANGE,
                     color_scheme=ft.ColorScheme(primary=ORANGE, surface=SURFACE))
    page.theme = page.dark_theme = theme
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.window.width, page.window.height = 1180, 800
    page.window.min_width, page.window.min_height = 820, 600

    state = {"user": None, "log_partner": None}

    def toast(msg, icon=ft.Icons.CHECK_CIRCLE, color=TEAL):
        page.open(ft.SnackBar(
            ft.Row([ft.Icon(icon, color=color), txt(msg)], spacing=10),
            bgcolor=CARD, behavior=ft.SnackBarBehavior.FLOATING, width=420,
            shape=ft.RoundedRectangleBorder(radius=14)))

    # ---------------- top bar: current user ----------------

    user_dd = ft.Dropdown(label="Signed in as", width=210, dense=True, **FIELD)
    greeting_name = bold("", 22)

    def refresh_users(select_id=None):
        users = db.list_users(conn)
        user_dd.options = [ft.dropdown.Option(str(u["id"]), u["name"]) for u in users]
        if select_id is not None:
            state["user"] = select_id
        elif state["user"] not in {u["id"] for u in users}:
            state["user"] = users[0]["id"] if users else None
        user_dd.value = str(state["user"]) if state["user"] else None
        greeting_name.value = next((u["name"] for u in users if u["id"] == state["user"]), "")

    def on_user_change(_):
        state["user"] = int(user_dd.value)
        render()

    user_dd.on_change = on_user_change

    def open_add_user(_):
        name = ft.TextField(label="Your name", autofocus=True, **FIELD)

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
            rail.selected_index = 0
            render()
            toast(f"Welcome, {name.value.strip()}! Add your skills to find matches.")

        name.on_submit = save
        dlg = ft.AlertDialog(
            bgcolor=CARD, shape=ft.RoundedRectangleBorder(radius=20),
            title=ft.Row([icon_badge(ft.Icons.PERSON_ADD_ALT_1, ORANGE, 38), bold("Join Skill Swap", 18)]),
            content=ft.Container(name, width=340),
            actions=[ghost_button("Cancel", None, lambda _: page.close(dlg)),
                     primary_button("Create", ft.Icons.ARROW_FORWARD, save, small=True)],
        )
        page.open(dlg)

    top_bar = ft.Row([
        ft.Column([txt("Welcome back,", 13, color=MUTED), greeting_name], spacing=0),
        ft.Row([
            user_dd,
            ft.IconButton(ft.Icons.PERSON_ADD_ALT_1, tooltip="New user", on_click=open_add_user,
                          icon_color=TEXT, bgcolor=CARD,
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12),
                                               side=ft.BorderSide(1, BORDER))),
        ], spacing=10),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # ---------------- 1. Profile ----------------

    def hero_stat(value, label):
        return ft.Container(ft.Column([
            bold(str(value), 24, "white"),
            txt(label, 12, color=ft.Colors.with_opacity(0.85, "white")),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.with_opacity(0.16, "white"), border_radius=16,
            padding=ft.padding.symmetric(10, 18), width=104)

    def skill_editor(kind, title, subtitle, icon, color):
        uid = state["user"]
        skills = db.skills_for(conn, uid, kind)
        chips = ft.Row([
            pill(s["name"].title(), TEXT, dot=LEVEL_COLORS[s["level"]], sub=s["level"],
                 on_delete=lambda _, sid=s["id"]: (db.remove_skill(conn, sid), render()))
            for s in skills
        ], wrap=True, spacing=8, run_spacing=8) if skills else txt(
            "Nothing here yet. Add your first skill below.", 13, color=MUTED, italic=True)

        name = ft.TextField(hint_text="e.g. Python, Guitar, Figma", expand=True, dense=True, **FIELD)
        level = ft.Dropdown(width=165, dense=True, value="Beginner", **FIELD,
                            options=[ft.dropdown.Option(l) for l in matching.LEVELS])

        def add(_):
            if not name.value.strip():
                name.error_text = "Type a skill"
                page.update()
                return
            db.set_skill(conn, uid, name.value, kind, level.value)
            toast(f"Added {name.value.strip().title()}")
            render()

        name.on_submit = add
        add_btn = ft.Container(ft.Icon(ft.Icons.ADD_ROUNDED, color="white"), width=44, height=44,
                               border_radius=12, gradient=gradient(), on_click=add,
                               alignment=ft.alignment.center, tooltip="Add skill")
        return card(ft.Column([
            ft.Row([icon_badge(icon, color), ft.Column([bold(title, 17), txt(subtitle, 12, color=MUTED)],
                                                       spacing=0)], spacing=12),
            ft.Container(chips, padding=ft.padding.symmetric(6, 0)),
            ft.Divider(color=BORDER, height=1),
            ft.Row([name, level, add_btn], spacing=10),
        ], spacing=14), col={"md": 6})

    def profile_view():
        uid = state["user"]
        profiles = db.all_profiles(conn)
        me = profiles[uid]
        swaps, _ = matching.find_matches(profiles, uid)

        hero = ft.Container(ft.Row([
            avatar(me["name"], 76, ring=True),
            ft.Column([
                txt("YOUR SKILL PROFILE", 11, ft.FontWeight.BOLD, ft.Colors.with_opacity(0.8, "white")),
                bold(me["name"], 28, "white"),
                txt("Teach what you know. Learn what you don't.", 14,
                    color=ft.Colors.with_opacity(0.9, "white")),
            ], spacing=2, expand=True),
            ft.Row([hero_stat(len(me["teaches"]), "Teaching"),
                    hero_stat(len(me["wants"]), "Learning"),
                    hero_stat(len(swaps), "Swaps")], spacing=10),
        ], spacing=22), gradient=gradient("#FF7A18", "#D9306B"), border_radius=24,
            padding=ft.padding.symmetric(26, 28),
            shadow=ft.BoxShadow(blur_radius=30, color=tint(PINK, 0.25), offset=ft.Offset(0, 10)))

        legend = ft.Row([txt("Levels", 12, color=MUTED)] + [
            ft.Row([ft.Container(width=8, height=8, border_radius=4, bgcolor=c), txt(l, 12, color=MUTED)],
                   spacing=6, tight=True) for l, c in LEVEL_COLORS.items()
        ] + [txt("·  For skills you want, pick the level you're aiming for. "
                 "Partners must teach at that level or higher.", 12, color=MUTED)],
            spacing=16, wrap=True)

        return ft.Column([
            hero,
            legend,
            ft.ResponsiveRow([
                skill_editor("teach", "I can teach", "Skills you'll share with others",
                             ft.Icons.SCHOOL_ROUNDED, ORANGE),
                skill_editor("want", "I want to learn", "Skills you're looking for",
                             ft.Icons.LIGHTBULB_ROUNDED, TEAL),
            ], spacing=18, run_spacing=18),
        ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)

    # ---------------- 2. Matches ----------------

    def open_history(partner_id, partner_name):
        rows = db.sessions_between(conn, state["user"], partner_id)
        items = [timeline_item(r, state["user"]) for r in rows] or [
            txt("No sessions together yet.", color=MUTED)]
        dlg = ft.AlertDialog(
            bgcolor=CARD, shape=ft.RoundedRectangleBorder(radius=20),
            title=ft.Row([avatar(partner_name, 40), ft.Column([
                bold(f"You & {partner_name}", 18), txt(f"{len(rows)} sessions together", 12, color=MUTED)],
                spacing=0)], spacing=12),
            content=ft.Column(items, tight=True, scroll=ft.ScrollMode.AUTO, height=320, width=440,
                              spacing=4),
            actions=[ghost_button("Close", None, lambda _: page.close(dlg))],
        )
        page.open(dlg)

    def go_log(partner_id):
        state["log_partner"] = partner_id
        rail.selected_index = 2
        render()

    def match_card(m, two_way):
        def line(label, skills, color):
            return ft.Column([
                txt(label.upper(), 11, ft.FontWeight.BOLD, MUTED),
                ft.Row([pill(s.title(), color) for s in skills], wrap=True, spacing=6, run_spacing=6)
                if skills else txt("Nothing in this direction", 13, color=MUTED, italic=True),
            ], spacing=8)

        pct = round(m["coverage"] * 100)
        accent = TEAL if two_way else MUTED
        return card(ft.Column([
            ft.Row([
                avatar(m["partner"], 48),
                ft.Column([bold(m["partner"], 17),
                           txt("Two-way match" if two_way else "One-way match", 12, color=MUTED)],
                          spacing=0, expand=True),
                pill("SWAP" if two_way else "MAYBE", TEAL if two_way else MUTED, size=11),
            ], spacing=12),
            ft.Column([
                ft.Row([txt("Match strength", 12, color=MUTED), txt(f"{pct}%", 12, ft.FontWeight.BOLD, accent)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                progress_bar(m["coverage"], accent),
            ], spacing=6),
            line("They can teach you", m["they_teach"], TEAL),
            line("You can teach them", m["i_teach"], ORANGE),
            ft.Row([
                ghost_button("History", ft.Icons.HISTORY_ROUNDED,
                             lambda _: open_history(m["partner_id"], m["partner"])),
                primary_button("Log session", ft.Icons.ADD_TASK_ROUNDED,
                               lambda _: go_log(m["partner_id"]), small=True),
            ], alignment=ft.MainAxisAlignment.END, spacing=8),
        ], spacing=16), hover=True, col={"md": 6}, opacity=1 if two_way else 0.9)

    def matches_view():
        profiles = db.all_profiles(conn)
        swaps, maybes = matching.find_matches(profiles, state["user"])
        return ft.Column([
            page_header("Your matches", "People who can teach you, and learn from you."),
            section_header("Perfect swaps", ft.Icons.SYNC_ALT_ROUNDED, TEAL, len(swaps),
                           "You both have something the other wants."),
            ft.ResponsiveRow([match_card(m, True) for m in swaps], spacing=18, run_spacing=18)
            if swaps else empty_state(ft.Icons.PERSON_SEARCH_ROUNDED, "No perfect swaps yet",
                                      "Add more skills you can teach or want to learn."),
            ft.Container(height=6),
            section_header("Maybe", ft.Icons.ARROW_FORWARD_ROUNDED, MUTED, len(maybes),
                           "One-way: only one of you can teach the other. Lower priority."),
            ft.ResponsiveRow([match_card(m, False) for m in maybes], spacing=18, run_spacing=18)
            if maybes else txt("None right now.", 13, color=MUTED, italic=True),
        ], spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)

    # ---------------- 3. Log session ----------------

    def timeline_item(r, uid):
        taught = r["teacher_id"] == uid
        color = ORANGE if taught else TEAL
        other = r["learner"] if taught else r["teacher"]
        return ft.Container(ft.Row([
            icon_badge(ft.Icons.NORTH_EAST_ROUNDED if taught else ft.Icons.SOUTH_WEST_ROUNDED, color, 38),
            ft.Column([
                ft.Row([txt("Taught" if taught else "Learned", 14, ft.FontWeight.W_600),
                        pill(r["skill"].title(), color, size=12),
                        txt("to" if taught else "from", 14, color=MUTED),
                        txt(other, 14, ft.FontWeight.W_600)], spacing=6, wrap=True),
                txt(f"{r['day']}  ·  {r['minutes']} min", 12, color=MUTED),
            ], spacing=4, expand=True),
        ], spacing=14), padding=ft.padding.symmetric(10, 4),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER)))

    def log_view():
        uid = state["user"]
        profiles = db.all_profiles(conn)
        me = profiles[uid]
        partners = sorted(((pid, p["name"]) for pid, p in profiles.items() if pid != uid),
                          key=lambda x: x[1])

        partner_dd = ft.Dropdown(label="Partner", width=330, **FIELD,
                                 options=[ft.dropdown.Option(str(pid), n) for pid, n in partners])
        role = ft.SegmentedButton(
            selected={"taught"}, allow_empty_selection=False, allow_multiple_selection=False,
            segments=[ft.Segment("taught", label=ft.Text("I taught"),
                                 icon=ft.Icon(ft.Icons.NORTH_EAST_ROUNDED)),
                      ft.Segment("learned", label=ft.Text("I learned"),
                                 icon=ft.Icon(ft.Icons.SOUTH_WEST_ROUNDED))])
        skill_dd = ft.Dropdown(label="Skill", width=330, **FIELD)
        minutes_label = txt("60 min", 14, ft.FontWeight.BOLD, ORANGE)
        minutes = ft.Slider(min=15, max=180, divisions=11, value=60, label="{value} min",
                            active_color=ORANGE, inactive_color=BORDER)
        hint = txt("", 12, color=PINK)

        def current_role():
            return next(iter(role.selected))

        def fill_skills():
            skill_dd.options, skill_dd.value, hint.value = [], None, ""
            if partner_dd.value:
                other = profiles[int(partner_dd.value)]
                skills = (matching.teachable(me, other) if current_role() == "taught"
                          else matching.teachable(other, me))
                skill_dd.options = [ft.dropdown.Option(s, s.title()) for s in skills]
                skill_dd.value = skills[0] if skills else None
                if not skills:
                    hint.value = "No matching skill in this direction. Try switching the role."

        def on_change(_):
            fill_skills()
            page.update()

        def on_minutes(_):
            minutes_label.value = f"{int(minutes.value)} min"
            minutes_label.update()

        partner_dd.on_change = role.on_change = on_change
        minutes.on_change = on_minutes

        if state["log_partner"] in profiles and state["log_partner"] != uid:
            partner_dd.value = str(state["log_partner"])
            if not matching.teachable(me, profiles[state["log_partner"]]):
                role.selected = {"learned"}
            state["log_partner"] = None
            fill_skills()

        def save(_):
            if not partner_dd.value or not skill_dd.value:
                toast("Pick a partner and a skill first.", ft.Icons.INFO_ROUNDED, PINK)
                return
            pid = int(partner_dd.value)
            teacher, learner = (uid, pid) if current_role() == "taught" else (pid, uid)
            db.log_session(conn, teacher, learner, skill_dd.value, int(minutes.value))
            toast("Session logged! Your progress ladder has been updated.")
            render()

        form = card(ft.Column([
            section_header("New session", ft.Icons.ADD_TASK_ROUNDED, ORANGE),
            partner_dd,
            ft.Column([txt("What happened?", 12, color=MUTED), role], spacing=6),
            skill_dd,
            hint,
            ft.Column([ft.Row([txt("Duration", 12, color=MUTED), minutes_label],
                              alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=330),
                       ft.Container(minutes, width=330, margin=ft.margin.only(left=-12))], spacing=0),
            primary_button("Save session", ft.Icons.CHECK_ROUNDED, save),
        ], spacing=16), padding=24, col={"lg": 5})

        sessions = db.sessions_for(conn, uid)
        history = card(ft.Column([
            section_header("Recent sessions", ft.Icons.HISTORY_ROUNDED, TEAL, len(sessions)),
            ft.Column([timeline_item(r, uid) for r in sessions[:12]], spacing=0)
            if sessions else txt("No sessions yet. Log your first one!", 13, color=MUTED, italic=True),
        ], spacing=12), padding=24, col={"lg": 7})

        return ft.Column([
            page_header("Log a session", "Finished a swap? Record it to level up your badges."),
            ft.ResponsiveRow([form, history], spacing=18, run_spacing=18),
        ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)

    # ---------------- 4. Dashboard / progress ladder ----------------

    def stat_tile(icon, value, label, color):
        return card(ft.Column([
            icon_badge(icon, color, 42),
            bold(str(value), 28),
            txt(label, 12, color=MUTED),
        ], spacing=6), padding=18, col={"xs": 5, "lg": 2})

    def badge_card(p):
        name = p["badge"][1] if p["badge"] else None
        color = BADGE_COLORS.get(name, MUTED)
        if p["next"]:
            nxt = f"{p['next'][0] - p['total']} more to {p['next'][1]}"
            bar_color = BADGE_COLORS[p["next"][1]]
        else:
            nxt, bar_color = "Top tier reached!", color
        return card(ft.Row([
            ft.Container(ft.Icon(ft.Icons.WORKSPACE_PREMIUM_ROUNDED, color=color, size=38),
                         width=66, height=66, border_radius=33, bgcolor=tint(color, 0.14),
                         border=ft.border.all(2, tint(color, 0.5)), alignment=ft.alignment.center),
            ft.Column([
                ft.Row([bold(p["skill"].title(), 17), pill(name or "Locked", color, size=11)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                progress_bar(p["progress"], bar_color),
                ft.Row([txt(f"{p['taught']} taught · {p['learned']} learned · {p['minutes']} min",
                            12, color=MUTED),
                        txt(nxt, 12, ft.FontWeight.W_600, bar_color)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            ], spacing=10, expand=True),
        ], spacing=18), hover=True, col={"md": 6})

    def dashboard_view():
        uid = state["user"]
        sessions = db.sessions_for(conn, uid)
        progress = matching.skill_progress(sessions, uid)
        taught = sum(1 for s in sessions if s["teacher_id"] == uid)
        hours = sum(s["minutes"] for s in sessions) / 60
        partners = {s["learner_id"] if s["teacher_id"] == uid else s["teacher_id"] for s in sessions}

        legend = ft.Row([
            pill(f"{name} {n}+", BADGE_COLORS[name], dot=BADGE_COLORS[name], size=12)
            for n, name, _ in matching.BADGE_TIERS
        ], wrap=True, spacing=8, run_spacing=8)

        return ft.Column([
            page_header("Progress ladder", "Every session you teach or learn moves you up."),
            ft.ResponsiveRow([
                stat_tile(ft.Icons.EVENT_AVAILABLE_ROUNDED, len(sessions), "Sessions", ORANGE),
                stat_tile(ft.Icons.NORTH_EAST_ROUNDED, taught, "Taught", PINK),
                stat_tile(ft.Icons.SOUTH_WEST_ROUNDED, len(sessions) - taught, "Learned", TEAL),
                stat_tile(ft.Icons.TIMER_ROUNDED, f"{hours:.1f}", "Hours", "#FBBF24"),
                stat_tile(ft.Icons.GROUP_ROUNDED, len(partners), "Partners", "#A78BFA"),
            ], columns=10, spacing=14, run_spacing=14),
            ft.Row([section_header("Skill badges", ft.Icons.MILITARY_TECH_ROUNDED, "#FACC15"), legend],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True, run_spacing=10),
            ft.ResponsiveRow([badge_card(p) for p in progress], spacing=18, run_spacing=18)
            if progress else empty_state(ft.Icons.WORKSPACE_PREMIUM_ROUNDED, "No badges yet",
                                         "Log your first session to earn the Newcomer badge."),
        ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)

    # ---------------- layout & navigation ----------------

    views = [profile_view, matches_view, log_view, dashboard_view]
    body = ft.Container(expand=True, alignment=ft.alignment.top_left,
                        animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT))

    def render(e=None):
        refresh_users()
        if state["user"] is None:
            body.content = ft.Column([empty_state(ft.Icons.PERSON_ADD_ALT_1, "Welcome to Skill Swap",
                                                  "Create a user to get started."),
                                      primary_button("New user", ft.Icons.ADD, open_add_user)],
                                     horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            body.content = views[rail.selected_index]()
        # Fade in when switching tabs.
        if e is not None and e.control is rail:
            body.opacity = 0
            page.update()
            body.opacity = 1
        page.update()

    logo = ft.Column([
        ft.Container(ft.Icon(ft.Icons.SWAP_HORIZ_ROUNDED, color="white", size=28), width=50, height=50,
                     border_radius=16, gradient=gradient(), alignment=ft.alignment.center,
                     shadow=ft.BoxShadow(blur_radius=18, color=tint(PINK, 0.35), offset=ft.Offset(0, 6))),
        txt("SkillSwap", 12, ft.FontWeight.BOLD),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)

    rail = ft.NavigationRail(
        selected_index=0, on_change=render, bgcolor=SURFACE, min_width=96,
        label_type=ft.NavigationRailLabelType.ALL, group_alignment=-0.8,
        indicator_color=tint(ORANGE, 0.22),
        leading=ft.Container(logo, padding=ft.padding.only(top=22, bottom=26)),
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
                                         selected_icon=ft.Icons.PERSON_ROUNDED, label="Profile"),
            ft.NavigationRailDestination(icon=ft.Icons.SYNC_ALT_ROUNDED,
                                         selected_icon=ft.Icons.SYNC_ALT_ROUNDED, label="Matches"),
            ft.NavigationRailDestination(icon=ft.Icons.ADD_TASK_OUTLINED,
                                         selected_icon=ft.Icons.ADD_TASK_ROUNDED, label="Log"),
            ft.NavigationRailDestination(icon=ft.Icons.LEADERBOARD_OUTLINED,
                                         selected_icon=ft.Icons.LEADERBOARD_ROUNDED, label="Progress"),
        ],
    )

    page.add(ft.Row([
        rail,
        ft.VerticalDivider(width=1, color=BORDER),
        ft.Container(ft.Column([top_bar, body], spacing=22, expand=True),
                     expand=True, padding=ft.padding.only(left=32, right=32, top=24, bottom=12)),
    ], expand=True, spacing=0))
    render()


if __name__ == "__main__":
    ft.app(target=main)
