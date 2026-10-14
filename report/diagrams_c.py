"""Diagrams C: ER diagram, context and level-1 DFDs, use-case diagram and the
two sequence diagrams (JWT authentication and front-end / back-end interaction)."""

from dstyle import (
    COLORS, INK, actor, arrow, box, diamond, elbow, new_ax, note, rect, save,
    store, wrap,
)
from matplotlib.patches import Ellipse, FancyArrowPatch, Rectangle


# ---------------------------------------------------------------------------
# helpers local to this module
# ---------------------------------------------------------------------------
def entity(ax, cx, cy, w, name, attrs, fs=6.3, header_h=3.2):
    """Database entity box with a coloured header and column table.

    attrs is a list of (tag, column, type) triples; the returned value is the
    box height so callers can anchor relationship lines on the true edges.
    """
    line_h = fs * 1.55 / 7.9
    h = header_h + len(attrs) * line_h + 1.6
    fc, ec = COLORS["data"]
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, facecolor="white",
                           edgecolor=ec, linewidth=1.3, zorder=3))
    ax.add_patch(Rectangle((cx - w / 2, cy + h / 2 - header_h), w, header_h,
                           facecolor=fc, edgecolor=ec, linewidth=1.3, zorder=4))
    ax.text(cx, cy + h / 2 - header_h / 2, name, ha="center", va="center",
            fontsize=fs + 1.1, fontweight="bold", color="#311B92", zorder=5)
    y = cy + h / 2 - header_h - 1.0
    for tag, col, typ in attrs:
        ax.text(cx - w / 2 + 1.0, y, tag, ha="left", va="top", fontsize=fs,
                family="monospace", color="#6A1B9A", fontweight="bold", zorder=5)
        ax.text(cx - w / 2 + 5.0, y, col, ha="left", va="top", fontsize=fs,
                family="monospace", color=INK, zorder=5)
        ax.text(cx - w / 2 + 15.0, y, typ, ha="left", va="top", fontsize=fs,
                family="monospace", color="#546E7A", zorder=5)
        y -= line_h
    return h


def rel(ax, p1, p2, card1="1", card2="N", fs=7.2, rad=0.0):
    """Relationship line with cardinality labels placed perpendicular to it."""
    arrow(ax, p1, p2, style="-", rad=rad)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    if abs(dx) >= abs(dy):
        o1, o2, ha = (0, 1.0), (0, 1.0), "center"
    else:
        o1, o2, ha = (1.4, 0), (1.4, 0), "left"
    for (px, py), (ox, oy), txt in ((p1, o1, card1), (p2, o2, card2)):
        ax.text(px + ox, py + oy, txt, ha=ha, va="center" if ha == "left" else "bottom",
                fontsize=fs, fontweight="bold", color="#B71C1C",
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"), zorder=8)


def sequence(lanes, messages, dy=4.0, fs=6.6, header_h=5.4, width_in=11.6,
             lane_pad=2.0, name="sequence.png"):
    """Minimal UML-style sequence diagram that sizes its own canvas.

    messages: list of (from_idx, to_idx, label, kind) where kind is 'call'
    (solid arrow), 'ret' (dashed return arrow) or 'self' (activation loop).
    """
    y_span = header_h + dy * (len(messages) + 2.8) + 2.0
    fig, ax = new_ax(width_in, width_in * y_span / 100.0)
    y_top = y_span - 1.0

    n = len(lanes)
    usable = 100.0 - 2 * lane_pad
    xs = [lane_pad + usable * (i + 0.5) / n for i in range(n)]
    lane_w = usable / n * 0.90

    y_bottom = y_top - header_h - dy * (len(messages) + 1.5)
    for x in xs:
        ax.plot([x, x], [y_top - header_h, y_bottom], color="#90A4AE", lw=0.9,
                ls=(0, (4, 3)), zorder=1)
    for x, label in zip(xs, lanes):
        box(ax, x, y_top - header_h / 2, lane_w, header_h, label, kind="ui",
            fs=fs, bold=True)

    ppu = getattr(ax, "_pt_per_unit", 7.2)
    y = y_top - header_h - dy * 0.9
    for a, b, label, kind in messages:
        color = COLORS["api"][1] if kind == "call" else "#78909C"
        if a == b:
            ax.add_patch(Rectangle((xs[a] + 0.4, y - dy * 0.66), 5.2, dy * 0.66,
                                   fill=False, edgecolor=color, lw=1.0, zorder=4))
            arrow(ax, (xs[a] + 5.6, y - dy * 0.66), (xs[a] + 0.2, y - dy * 0.66),
                  color=color, lw=1.0, ms=9)
            ax.text(xs[a] + 6.4, y - dy * 0.33, label, ha="left", va="center",
                    fontsize=fs, color=INK, zorder=6, linespacing=1.25)
        else:
            arrow(ax, (xs[a], y), (xs[b], y), color=color, lw=1.1, ms=10,
                  ls="-" if kind == "call" else (0, (5, 3)))
            mid = (xs[a] + xs[b]) / 2
            ax.text(mid, y + 0.8, wrap(label, abs(xs[b] - xs[a]) + 14, fs, ppu),
                    ha="center", va="bottom", fontsize=fs, color=INK, zorder=6,
                    linespacing=1.25)
        y -= dy
    return save(fig, name)


# ---------------------------------------------------------------------------
# Figure: entity relationship diagram
# ---------------------------------------------------------------------------
def fig_er():
    fig, ax = new_ax(11.8, 9.6)
    R1, R2 = 60.0, 20.0

    h_u = entity(ax, 17, R1, 28, "users", [
        ("PK", "id", "INTEGER"),
        ("UQ", "email", "VARCHAR(255)"),
        ("", "hashed_password", "VARCHAR(255)"),
        ("", "full_name", "VARCHAR(255)?"),
        ("", "is_active", "BOOLEAN"),
        ("", "is_superuser", "BOOLEAN"),
        ("", "created_at", "TIMESTAMPTZ"),
        ("", "updated_at", "TIMESTAMPTZ"),
    ])
    h_r = entity(ax, 50, R1, 28, "resumes", [
        ("PK", "id", "INTEGER"),
        ("FK", "user_id", "INT -> users.id"),
        ("", "filename", "VARCHAR(255)"),
        ("", "file_path", "VARCHAR(512)"),
        ("", "file_size_bytes", "INTEGER?"),
        ("", "file_type", "VARCHAR(50)?"),
        ("", "raw_text", "TEXT?"),
        ("", "parsed_json", "TEXT?"),
        ("IX", "is_active", "BOOLEAN"),
        ("", "created_at", "TIMESTAMPTZ"),
        ("", "updated_at", "TIMESTAMPTZ"),
    ])
    h_j = entity(ax, 83, R1, 28, "job_listings", [
        ("PK", "id", "INTEGER"),
        ("UQ", "external_id", "VARCHAR(255)?"),
        ("IX", "title", "VARCHAR(255)"),
        ("IX", "company", "VARCHAR(255)"),
        ("", "location", "VARCHAR(255)?"),
        ("", "country", "VARCHAR(50)?"),
        ("", "description", "TEXT"),
        ("", "salary_min", "FLOAT?"),
        ("", "salary_max", "FLOAT?"),
        ("", "url", "VARCHAR(1024)?"),
        ("", "source", "VARCHAR(100)"),
        ("", "posted_at", "TIMESTAMPTZ?"),
        ("", "created_at", "TIMESTAMPTZ"),
    ])
    h_sg = entity(ax, 17, R2, 28, "skill_gap_analyses", [
        ("PK", "id", "INTEGER"),
        ("FK", "user_id", "INT -> users.id"),
        ("FK", "resume_id", "INT -> resumes.id"),
        ("IX", "target_role", "VARCHAR(255)"),
        ("", "target_location", "VARCHAR(255)?"),
        ("", "total_listings_analyzed", "INTEGER"),
        ("", "data_source", "VARCHAR(100)"),
        ("", "is_sample_data", "BOOLEAN"),
        ("", "results_json", "TEXT"),
        ("", "created_at", "TIMESTAMPTZ"),
    ])
    h_es = entity(ax, 50, R2, 28, "extracted_skills", [
        ("PK", "id", "INTEGER"),
        ("FK", "resume_id", "INT -> resumes.id"),
        ("IX", "skill_name", "VARCHAR(100)"),
        ("IX", "canonical_name", "VARCHAR(100)?"),
        ("", "confidence_score", "FLOAT"),
        ("", "category", "VARCHAR(100)?"),
        ("", "years_experience", "FLOAT?"),
        ("", "created_at", "TIMESTAMPTZ"),
    ])
    h_js = entity(ax, 83, R2, 28, "job_skills", [
        ("PK", "id", "INTEGER"),
        ("FK", "job_listing_id", "INT -> job_listings.id"),
        ("IX", "skill_name", "VARCHAR(100)"),
        ("IX", "canonical_name", "VARCHAR(100)?"),
        ("", "importance_weight", "FLOAT"),
        ("", "is_required", "BOOLEAN"),
        ("UQ", "(listing_id,", "skill_name)"),
        ("", "created_at", "TIMESTAMPTZ"),
    ])

    rel(ax, (31.0, R1), (36.0, R1))
    rel(ax, (50.0, R1 - h_r / 2), (50.0, R2 + h_es / 2))
    rel(ax, (17.0, R1 - h_u / 2), (17.0, R2 + h_sg / 2))
    rel(ax, (42.0, R1 - h_r / 2), (25.0, R2 + h_sg / 2), rad=-0.10)
    rel(ax, (83.0, R1 - h_j / 2), (83.0, R2 + h_js / 2))

    note(ax, 50, 3.4, 96.0, 6.4,
         "Every foreign key uses ON DELETE CASCADE and each child collection uses cascade='all, delete-orphan',\n"
         "so deleting a user or a resume also removes its dependent rows. Alembic revisions 2e81ce75033c,\n"
         "8a3c9e12b4f1 and dd4ee4ad6d27 create the schema and add resumes.is_active and skill_gap_analyses.",
         fs=6.6)
    return save(fig, "fig_er_diagram.png")


# ---------------------------------------------------------------------------
# Figure: context (level 0) DFD
# ---------------------------------------------------------------------------
def fig_dfd0():
    fig, ax = new_ax(11.4, 6.4)
    box(ax, 50, 30, 34, 12, "0\nSkillSync AI — AI-driven employment\nand skill matching portal", kind="ai", fs=8.0, bold=True)

    box(ax, 12, 48, 20, 7, "Candidate /\nstudent", kind="ext", fs=7.4, bold=True)
    box(ax, 88, 48, 20, 7, "Adzuna Job\nSearch API", kind="ext", fs=7.4, bold=True)
    box(ax, 88, 10, 20, 7, "Optional LLM\nprovider", kind="ext", fs=7.4, bold=True)
    box(ax, 12, 10, 20, 7, "Relational store\n(SQLite / PostgreSQL)\nand resume file store", kind="store", fs=7.0)

    arrow(ax, (20, 44.5), (40, 36.5), label="credentials, resume file (PDF / DOCX),\ntarget role and location", fs=6.8, label_offset=(-2, 2.4), rad=0.05)
    arrow(ax, (40, 26.0), (20, 14.0), label="", rad=-0.05)
    arrow(ax, (33, 26.5), (16, 13.5), label="persists users, resumes, extracted\nskills and gap analyses", fs=6.8, label_offset=(-6, -1.0), rad=0.06)
    arrow(ax, (16, 13.5), (33, 24.0), label="", rad=-0.06)
    arrow(ax, (40, 33.0), (20, 44.5), label="JWT, extracted skills, ranked jobs,\ndemand %, gap report, roadmap", fs=6.8, label_offset=(6, 3.6), rad=-0.05)

    arrow(ax, (60, 35.0), (80, 45.0), label="search query (what / what_or / where)\nplus application credentials", fs=6.8, label_offset=(2, 3.2), rad=-0.05)
    arrow(ax, (80, 44.5), (62, 32.0), label="listing results, or an HTTP error\nthat triggers fixture fallback", fs=6.8, label_offset=(8, -1.2), rad=0.05)
    arrow(ax, (62, 26.0), (80, 13.0), label="scoped skill prompt over HTTPS", fs=6.8, label_offset=(2, 2.0), rad=-0.05)
    arrow(ax, (80, 12.0), (60, 24.5), label="JSON explanation, or nothing\nwhen the call fails or times out", fs=6.8, label_offset=(6, -2.4), rad=0.05)
    return save(fig, "fig_dfd_level0.png")


# ---------------------------------------------------------------------------
# Figure: level 1 DFD
# ---------------------------------------------------------------------------
def fig_dfd1():
    fig, ax = new_ax(12.0, 8.6)

    # external entities
    box(ax, 8, 66, 13, 6, "Candidate /\nstudent", kind="ext", fs=7.0, bold=True)
    box(ax, 8, 34, 13, 6, "Adzuna Job\nSearch API", kind="ext", fs=7.0, bold=True)
    box(ax, 8, 8, 13, 6, "Optional LLM\nprovider", kind="ext", fs=7.0, bold=True)

    # processes column A
    pa = [(30, 70, "1.0 Authenticate\nregister · login · /me"),
          (30, 60, "2.0 Ingest and parse\nresume (PDF / DOCX)"),
          (30, 50, "3.0 Extract and\nnormalise skills"),
          (30, 16, "9.0 Skill gap analysis\nand persistence"),
          (30, 6, "10.0 Roadmap sequencing\nand LLM guidance")]
    # processes column B
    pb = [(56, 60, "4.0 Retrieve job listings\nlive API or fixtures"),
          (56, 50, "5.0 Deduplicate and\nstore listings"),
          (56, 40, "6.0 Market demand\nanalysis"),
          (56, 28, "7.0 Hybrid skill\nmatching"),
          (56, 18, "8.0 Rank and recommend\njobs")]
    for cx, cy, label in pa + pb:
        box(ax, cx, cy, 21, 6.6, label, kind="service", fs=6.8)

    # stores column C
    stores = [(84, 72, "D1 users"), (84, 65, "D2 resumes"), (84, 58, "D3 extracted_skills"),
              (84, 51, "D4 job_listings"), (84, 44, "D5 job_skills"),
              (84, 37, "D6 skill_gap_analyses"), (84, 30, "D7 skills.json taxonomy"),
              (84, 23, "D8 sample_jobs.json fixtures")]
    for cx, cy, label in stores:
        store(ax, cx, cy, 24, 4.6, label, fs=6.6)

    # flows — candidate
    arrow(ax, (14.5, 68), (19.5, 70), label="credentials", fs=6.4, label_offset=(0, 1.2))
    arrow(ax, (19.5, 68.5), (14.5, 66.5), label="JWT", fs=6.4, label_offset=(0, -1.4))
    arrow(ax, (36.5, 70), (72, 72), label="", lw=0.9)
    arrow(ax, (14.5, 64), (21, 61), label="resume file", fs=6.4, label_offset=(-1, 1.4))
    arrow(ax, (36.5, 60), (72, 65), lw=0.9)
    arrow(ax, (36.5, 50), (72, 58), lw=0.9)
    arrow(ax, (72, 58), (36.5, 48.5), lw=0.9)
    arrow(ax, (72, 30), (36.5, 49.0), lw=0.9)
    # provider
    arrow(ax, (66.5, 60), (78, 45), label="", lw=0.9)
    arrow(ax, (78, 44), (66.5, 58.5), lw=0.9)
    arrow(ax, (45.5, 60), (66.5, 60), label="raw listings", fs=6.4, label_offset=(0, 1.2))
    arrow(ax, (56, 46.7), (56, 43.3), label="unique listings", fs=6.4, label_offset=(6.4, 0))
    arrow(ax, (56, 36.7), (56, 31.3), label="demand % per skill", fs=6.4, label_offset=(7.4, 0))
    arrow(ax, (56, 24.7), (56, 21.3), label="evaluated skills", fs=6.4, label_offset=(6.6, 0))
    arrow(ax, (45.5, 28), (40.5, 17.5), label="gap input", fs=6.4, label_offset=(-2.4, 0.8))
    arrow(ax, (30, 12.7), (30, 9.3), label="ordered gaps", fs=6.4, label_offset=(5.6, 0))
    arrow(ax, (72, 51), (62, 41.5), lw=0.9)
    arrow(ax, (72, 44), (64, 30.5), lw=0.9)
    arrow(ax, (72, 37), (40.5, 17.0), lw=0.9)
    arrow(ax, (66.5, 18), (72, 20), label="", lw=0.9)
    # adzuna + llm
    arrow(ax, (14.5, 36), (45.5, 58.5), label="HTTPS query + credentials", fs=6.4, label_offset=(-4, 1.6))
    arrow(ax, (45.5, 57.5), (14.5, 34.5), label="results / error", fs=6.4, label_offset=(-6, -1.8))
    arrow(ax, (40.5, 5.0), (14.5, 7.0), label="prompt", fs=6.4, label_offset=(0, -1.4))
    arrow(ax, (14.5, 9.5), (40.5, 7.2), label="JSON or nothing", fs=6.4, label_offset=(2, 1.4))
    # outputs to candidate
    arrow(ax, (45.5, 18), (78, 20), lw=0.9)
    ax.text(96.5, 12.0, "Outputs to the candidate:\nranked recommendations, demand table,\ngap report and ordered roadmap",
            ha="center", va="center", fontsize=6.6, color=INK,
            bbox=dict(boxstyle="round,pad=0.3", fc="#E3F2FD", ec="#1565C0", lw=0.9))
    arrow(ax, (88, 18), (93, 14.5), lw=0.9)
    return save(fig, "fig_dfd_level1.png")


# ---------------------------------------------------------------------------
# Figure: use case diagram
# ---------------------------------------------------------------------------
def fig_usecase():
    fig, ax = new_ax(11.6, 7.6)
    rect(ax, 20, 2, 56, 62, kind="band", lw=1.2, zorder=1)
    ax.text(48, 62.6, "SkillSync AI — system boundary", ha="center", va="bottom",
            fontsize=7.6, fontweight="bold", color=COLORS["band"][1])

    actor(ax, 8, 46, scale=1.1, label="Job seeker\n(student)")
    actor(ax, 91, 48, scale=1.0, label="Adzuna Job\nSearch API")
    actor(ax, 91, 16, scale=1.0, label="LLM provider")

    left = [(34, 58, "Register an account"),
            (34, 50, "Sign in / sign out"),
            (34, 42, "Upload a PDF or DOCX resume"),
            (34, 34, "Review resume history and\nactivate a past resume"),
            (34, 26, "Inspect extracted skills with\nevidence snippets"),
            (34, 18, "View market demand for a role"),
            (34, 10, "Request personalised job\nrecommendations")]
    right = [(62, 54, "Run role skill gap analysis"),
             (62, 44, "Generate the learning roadmap"),
             (62, 34, "Observe the SAMPLE DATA\nwarning banner"),
             (62, 24, "Filter results by location and\nminimum match"),
             (62, 14, "Open the posting on Adzuna")]
    for cx, cy, label in left + right:
        ax.add_patch(Ellipse((cx, cy), 24.0, 6.6, facecolor="#FFFFFF",
                             edgecolor="#1565C0", linewidth=1.1, zorder=3))
        ppu = getattr(ax, "_pt_per_unit", 7.2)
        ax.text(cx, cy, wrap(label, 22, 6.7, ppu), ha="center", va="center",
                fontsize=6.7, color=INK, zorder=4, linespacing=1.25)

    for cx, cy, _ in left:
        arrow(ax, (12.5, 46), (cx - 12.0, cy), style="-", lw=0.9, rad=0.04)
    for cx, cy, _ in right[:2]:
        arrow(ax, (cx + 12.0, cy), (87.5, 46), style="-", lw=0.9, rad=-0.04)
    arrow(ax, (62 + 12.0, 44), (87.5, 16), style="-", lw=0.9, rad=-0.06)

    for cy in (42, 34, 26, 18, 10):
        ax.add_patch(FancyArrowPatch((36, cy + 2.6), (35, 50 - 3.0),
                                     arrowstyle="-|>", mutation_scale=9, lw=0.9,
                                     color="#607D8B", linestyle=(0, (4, 3)), zorder=2))
    ax.text(24.5, 40.0, "«include»\nsign-in session", ha="center", va="center",
            fontsize=6.3, color="#607D8B", zorder=6)
    arrow(ax, (50, 44), (52, 54 - 3.2), style="-", lw=0.9)
    ax.text(56, 49.5, "«include»", ha="center", va="center", fontsize=6.3, color="#607D8B")
    return save(fig, "fig_usecase.png")


# ---------------------------------------------------------------------------
# Figure: JWT authentication sequence
# ---------------------------------------------------------------------------
def fig_jwt_sequence():
    lanes = ["React UI\n(AuthPage)", "Axios client\n(interceptor)", "FastAPI\n/api/auth",
             "AuthService", "UserRepository", "SQLite\n(users)"]
    msgs = [
        (0, 1, "submit registration or login form {email, password, full_name}", "call"),
        (1, 2, "POST /api/auth/register  or  POST /api/auth/login", "call"),
        (2, 3, "register(UserCreate) / authenticate(UserLogin)", "call"),
        (3, 4, "get_by_email(email) — duplicate e-mail raises HTTP 400", "call"),
        (4, 5, "INSERT user row with bcrypt-hashed password", "call"),
        (5, 4, "persisted User instance", "ret"),
        (3, 3, "verify_password() against the stored bcrypt hash;\ncreate_access_token(sub=user_id, exp = now + 60 min, HS256)", "self"),
        (3, 2, "Token {access_token, token_type='bearer', user}", "ret"),
        (2, 1, "HTTP 201 / 200 JSON body", "ret"),
        (1, 0, "localStorage.setItem('access_token', token)", "ret"),
        (0, 1, "any later request, e.g. GET /api/resumes/active", "call"),
        (1, 2, "Authorization: Bearer <token> attached by the interceptor", "call"),
        (2, 2, "get_current_user: jwt.decode(token, JWT_SECRET, ['HS256'])\nreads the sub claim; an inactive account raises HTTP 400", "self"),
        (2, 4, "get_by_id(int(sub))", "call"),
        (4, 2, "User instance, or 401 'Could not validate credentials'", "ret"),
        (2, 1, "request proceeds with the injected current_user", "ret"),
    ]
    return sequence(lanes, msgs, dy=4.1, fs=6.6, name="fig_jwt_sequence.png")


def fig_api_interaction():
    lanes = ["Job seeker", "SkillGapPage\n(React)", "AuthProvider +\nReact Query", "Axios client",
             "FastAPI routers", "Service layer", "SQLite /\nfile store"]
    msgs = [
        (0, 1, "open the application with a stored session", "call"),
        (1, 2, "resolve session and cached dashboard data", "call"),
        (2, 3, "GET /api/auth/me then GET /api/resumes/active", "call"),
        (3, 4, "Bearer token validated by get_current_user", "call"),
        (4, 6, "load active resume, extracted skills, latest analysis", "call"),
        (6, 4, "rows returned", "ret"),
        (4, 1, "ActiveResumeResponse {has_active_resume, resume, latest_analysis}", "ret"),
        (0, 1, "upload a new PDF or DOCX resume", "call"),
        (1, 3, "POST /api/resumes/upload (multipart/form-data)", "call"),
        (3, 5, "parse, extract and persist; previous resume deactivated", "call"),
        (5, 6, "resume row and extracted_skills rows committed; file saved", "call"),
        (5, 1, "201 ResumeUploadResponse with skills and provenance", "ret"),
        (1, 2, "invalidateQueries(['activeResume']) refreshes every tab", "call"),
        (1, 3, "GET /api/jobs/recommendations?resume_id=...", "call"),
        (3, 5, "JobMatcherService scores and ranks the listings", "call"),
        (5, 1, "ranked cards with matched / missing chips and is_sample_data", "ret"),
        (1, 3, "POST /api/skill-gap/analyze {resume_id, target_role}", "call"),
        (3, 5, "demand analysis, five-stage matching and persistence", "call"),
        (5, 1, "gap report with priorities and overall match percentage", "ret"),
        (1, 3, "GET /api/roadmap?resume_id=...&target_role=...", "call"),
        (3, 5, "demand-ordered steps with optional LLM guidance", "call"),
        (5, 1, "RoadmapResponse rendered as a vertical stepper", "ret"),
        (1, 1, "when is_sample_data is true the SampleDataBanner warning is shown", "self"),
    ]
    return sequence(lanes, msgs, dy=3.35, fs=6.3, name="fig_api_interaction.png")


if __name__ == "__main__":
    for fn in (fig_er, fig_dfd0, fig_dfd1, fig_usecase, fig_jwt_sequence, fig_api_interaction):
        print("wrote", fn())
