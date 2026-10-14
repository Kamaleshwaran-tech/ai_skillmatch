"""Diagrams A: system architecture, module decomposition, resume ingestion,
skill extraction and normalisation."""

from dstyle import (
    arrow, band, box, diamond, elbow, new_ax, note, rect, save, store, COLORS,
)


# ---------------------------------------------------------------------------
# Figure: Overall system architecture
# ---------------------------------------------------------------------------
def fig_architecture():
    fig, ax = new_ax(11.6, 8.3)

    band_x, band_w = 1.5, 97.0

    # ---- Layer 1: Presentation -------------------------------------------
    band(ax, band_x, 56.0, band_w, 12.6,
         "PRESENTATION LAYER  —  React 18 · Vite 5 · Material UI 5 · TanStack React Query")
    pages = [
        ("Home Page\nbackend health + module cards", "ui"),
        ("Auth Page\nregister / login form", "ui"),
        ("Skill Gap Page\ntabs: Jobs · Gap · Roadmap", "ui"),
        ("Market Demand Page\nrole and location filters", "ui"),
        ("Learning Roadmap Page\nMUI vertical stepper", "ui"),
    ]
    xs = [12.0, 31.0, 50.0, 69.0, 88.0]
    for (label, kind), cx in zip(pages, xs):
        box(ax, cx, 62.9, 17.6, 5.0, label, kind=kind, fs=7.0)
    infra = [
        "Axios client +\nBearer interceptor",
        "React Query cache\n(staleTime 5 min)",
        "React Router v6\nclient-side routes",
        "MUI theme +\nSampleDataBanner",
        "Vite dev proxy\n/api → 127.0.0.1:8000",
    ]
    for label, cx in zip(infra, xs):
        box(ax, cx, 58.1, 17.6, 4.1, label, kind="note", fs=6.7)

    # ---- Layer 2: API -----------------------------------------------------
    band(ax, band_x, 41.5, band_w, 12.0,
         "API LAYER  —  FastAPI · Uvicorn (ASGI) · Pydantic v2 request / response contracts")
    routers = ["/api/auth", "/api/resumes", "/api/jobs", "/api/market-demand",
               "/api/skill-gap", "/api/roadmap", "/api/health"]
    rxs = [8.6, 22.4, 36.2, 50.0, 63.8, 77.6, 91.4]
    for label, cx in zip(routers, rxs):
        box(ax, cx, 48.4, 12.6, 4.4, label, kind="api", fs=6.9)
    cross = [
        "CORSMiddleware\n(allow_origins from .env)",
        "OAuth2PasswordBearer →\nget_current_user dependency",
        "response_model validation\nand OpenAPI /docs schema",
        "Lifespan handler: DB ping +\nsemantic model warm-up",
    ]
    cxs = [13.85, 37.95, 62.05, 86.15]
    for label, cx in zip(cross, cxs):
        box(ax, cx, 43.8, 22.5, 4.1, label, kind="note", fs=6.7)

    # ---- Layer 3: Services ------------------------------------------------
    band(ax, band_x, 21.0, band_w, 18.0,
         "APPLICATION / SERVICE LAYER  —  business logic, document processing and AI-NLP components")
    rows = [
        (33.6, [("AuthService\nregister · login", "service"),
                ("ResumeParserService\nPyMuPDF · python-docx", "service"),
                ("SkillExtractor\nregex + spaCy sentencizer", "service"),
                ("SkillNormalizer\nalias → canonical", "service")]),
        (28.5, [("SemanticMatcher\nall-MiniLM-L6-v2", "ai"),
                ("HybridMatcher\nfive-stage pipeline", "ai"),
                ("JobMatcherService\nscore and rank", "service"),
                ("AdzunaJobProvider\nlive + fixture fallback", "service")]),
        (23.4, [("JobIngestionService\ntwo-level deduplication", "service"),
                ("MarketDemandService\ndemand percentage", "service"),
                ("SkillGapService\npriority + persistence", "service"),
                ("RoadmapService\ndemand-ordered steps", "service")]),
    ]
    for cy, items in rows:
        for (label, kind), cx in zip(items, cxs):
            box(ax, cx, cy, 22.5, 4.4, label, kind=kind, fs=6.9)

    # ---- Layer 4: Data and external ---------------------------------------
    band(ax, band_x, 2.0, band_w, 17.0,
         "DATA, STORAGE AND EXTERNAL SERVICE LAYER")
    d1 = [("SQLAlchemy 2.0 ORM\nUserRepository · ResumeRepository", "data"),
          ("SQLite by default\nPostgreSQL-ready via DATABASE_URL", "data"),
          ("Resume file store\n./uploads/resumes", "data"),
          ("Hugging Face model cache\nall-MiniLM-L6-v2 weights", "data")]
    for (label, kind), cx in zip(d1, cxs):
        box(ax, cx, 13.5, 22.5, 5.0, label, kind=kind, fs=6.9)
    d2 = [("skills.json taxonomy\n56 skills · 11 categories", "store"),
          ("sample_jobs.json\nlabelled offline fixtures", "store"),
          ("Adzuna Job Search API\napi.adzuna.com (external)", "ext"),
          ("Optional LLM provider\nGemini / OpenAI-compatible", "ext")]
    for (label, kind), cx in zip(d2, cxs):
        if kind == "store":
            store(ax, cx, 6.5, 22.5, 5.0, label, fs=6.9)
        else:
            box(ax, cx, 6.5, 22.5, 5.0, label, kind=kind, fs=6.9)

    # ---- Inter-layer connectors -------------------------------------------
    for cx in (25.0, 50.0, 75.0):
        arrow(ax, (cx, 56.0), (cx, 53.5))
        arrow(ax, (cx, 41.5), (cx, 39.0))
        arrow(ax, (cx, 21.0), (cx, 19.0))
    ax.text(50.0, 54.75, "HTTP / JSON and multipart form-data, Bearer JWT in the Authorization header",
            ha="center", va="center", fontsize=6.8, color=COLORS["api"][1],
            bbox=dict(boxstyle="round,pad=0.20", fc="white", ec="none", alpha=0.92), zorder=8)
    ax.text(50.0, 40.25, "Dependency-injected service calls inside a scoped SQLAlchemy session",
            ha="center", va="center", fontsize=6.8, color=COLORS["service"][1],
            bbox=dict(boxstyle="round,pad=0.20", fc="white", ec="none", alpha=0.92), zorder=8)
    ax.text(50.0, 20.0, "ORM reads and writes, local file access, model inference and outbound HTTPS",
            ha="center", va="center", fontsize=6.8, color=COLORS["data"][1],
            bbox=dict(boxstyle="round,pad=0.20", fc="white", ec="none", alpha=0.92), zorder=8)

    return save(fig, "fig_architecture.png")


# ---------------------------------------------------------------------------
# Figure: Module decomposition
# ---------------------------------------------------------------------------
def fig_modules():
    fig, ax = new_ax(11.6, 7.2)

    box(ax, 9.0, 31.5, 15.0, 7.0, "SkillSync AI\nmini-project system", kind="start", fs=7.6, bold=True)

    groups = [
        (54.2, "Frontend\nReact + Vite", "ui", [
            (60.5, "Pages: Home, Auth, SkillGap,\nMarketDemand, Roadmap, NotFound"),
            (56.3, "Components: Navbar, Footer,\nSampleDataBanner, RecommendedJobCard,\nLearningRoadmapView"),
            (52.1, "Services: authService, skillGapService,\nhealthService over a shared Axios client"),
            (47.9, "State: AuthProvider context +\nReact Query cache"),
        ]),
        (30.4, "Backend\nFastAPI", "api", [
            (43.0, "api/routes: auth, resumes, jobs,\nmarket_demand, skill_gap, roadmap"),
            (38.8, "api/deps: OAuth2 bearer extraction\nand get_current_user"),
            (34.6, "services: parsing, extraction,\nnormalisation, semantic and hybrid matching"),
            (30.4, "services: job provider, ingestion,\nmarket demand, skill gap, roadmap"),
            (26.2, "repositories: UserRepository,\nResumeRepository"),
            (22.0, "models + schemas: ORM entities and\nPydantic response contracts"),
            (17.8, "core: config (pydantic-settings) and\nsecurity (bcrypt, JWT)"),
        ]),
        (8.0, "Data and\nexternal", "data", [
            (14.2, "SQLite / PostgreSQL through\nSQLAlchemy and Alembic migrations"),
            (11.1, "Local resume upload directory"),
            (8.0, "skills.json taxonomy and\nsample_jobs.json fixtures"),
            (4.9, "all-MiniLM-L6-v2 sentence\nencoder weights"),
            (1.8, "Adzuna API and optional\nLLM provider"),
        ]),
    ]

    for gy, glabel, gkind, children in groups:
        box(ax, 34.0, gy, 19.0, 6.4, glabel, kind=gkind, fs=7.8, bold=True)
        arrow(ax, (16.5, 31.5), (24.5, gy), rad=0.0 if abs(gy - 31.5) < 0.1 else (-0.12 if gy > 31.5 else 0.12))
        for cy, label in children:
            box(ax, 74.0, cy, 44.0, 2.9, label, kind="note", fs=6.6, align="center")
            arrow(ax, (43.5, gy), (52.0, cy), rad=0.0 if abs(cy - gy) < 0.6 else (0.06 if cy > gy else -0.06),
                  lw=0.9, ms=8)

    return save(fig, "fig_modules.png")


# ---------------------------------------------------------------------------
# Figure: Resume ingestion data flow
# ---------------------------------------------------------------------------
def fig_resume_flow():
    fig, ax = new_ax(11.0, 10.2)
    MX, MW = 32.0, 44.0   # main processing lane
    EX, EW = 79.5, 31.0   # exception lane

    rect(ax, 62.5, 1.5, 36.0, 88.0, kind="note", lw=0.9, ls=(0, (4, 2)), zorder=0)
    ax.text(80.5, 88.6, "EXCEPTION AND CLEAN-UP PATHS", ha="center", va="top",
            fontsize=7.2, fontweight="bold", color="#B71C1C", zorder=2)

    # ---- main lane -------------------------------------------------------
    box(ax, MX, 88.0, MW, 4.2,
        "START — candidate selects a resume file (.pdf or .docx) on the Skill Gap page",
        kind="start", fs=7.2, bold=True)
    arrow(ax, (MX, 85.9), (MX, 85.2))

    box(ax, MX, 82.6, MW, 5.2,
        "React wraps the file in a FormData payload; the Axios request interceptor\nattaches the stored access token as a Bearer Authorization header",
        kind="ui", fs=7.2)
    arrow(ax, (MX, 80.0), (MX, 79.8))

    box(ax, MX, 77.2, MW, 5.2,
        "The Vite dev proxy forwards the multipart POST /api/resumes/upload\nto Uvicorn, which serves the FastAPI application on port 8000",
        kind="api", fs=7.2)
    arrow(ax, (MX, 74.6), (MX, 74.2))

    diamond(ax, MX, 71.0, 30.0, 6.4, "Is the file extension one of\n.pdf, .docx or .doc ?", fs=7.0)
    box(ax, EX, 71.0, EW, 4.4,
        "HTTP 400 Bad Request —\nunsupported file format", kind="end", fs=7.0)
    arrow(ax, (MX + 15.0, 71.0), (EX - EW / 2, 71.0), label="No", fs=6.8)
    arrow(ax, (MX, 67.8), (MX, 66.6), label="Yes", fs=6.8)

    diamond(ax, MX, 63.4, 30.0, 6.4, "Is the file size within\nMAX_UPLOAD_SIZE_MB (5 MB) ?", fs=7.0)
    box(ax, EX, 63.4, EW, 4.4,
        "HTTP 413 Payload Too Large —\nupload exceeds the configured limit", kind="end", fs=7.0)
    arrow(ax, (MX + 15.0, 63.4), (EX - EW / 2, 63.4), label="No", fs=6.8)
    arrow(ax, (MX, 60.2), (MX, 59.8), label="Yes", fs=6.8)

    box(ax, MX, 57.6, MW, 4.4,
        "Persist the bytes to UPLOAD_DIR under a collision-free name\n<uuid4().hex>_<original filename>", kind="service", fs=7.2)
    arrow(ax, (MX, 55.4), (MX, 54.6))

    box(ax, MX, 52.6, MW, 4.0,
        "ResumeParserService.parse_file(saved_path, filename)",
        kind="service", fs=7.4, bold=True)
    arrow(ax, (MX, 50.6), (MX, 49.4))

    diamond(ax, MX, 46.6, 24.0, 5.6, "Document format ?", fs=7.0)
    box(ax, 17.0, 39.0, 26.0, 6.8,
        "PDF branch — PyMuPDF\npage.get_text('text') for every page;\npage.get_images(full=True) records\nwhether any page carries images",
        kind="service", fs=6.6)
    box(ax, 48.0, 39.0, 26.0, 6.8,
        "DOCX branch — python-docx\nevery non-empty paragraph plus the\ntext of all cells in all tables,\nappended without duplication",
        kind="service", fs=6.6)
    arrow(ax, (MX - 12.0, 46.6), (17.0, 42.4), rad=-0.10)
    arrow(ax, (MX + 12.0, 46.6), (48.0, 42.4), rad=0.10)

    box(ax, MX, 31.0, MW, 5.6,
        "Join the page or paragraph text into raw_text, then _segment_sections() splits it\nat Skills, Experience, Education, Projects, Certifications, Summary and\nObjective headings",
        kind="service", fs=7.0)
    arrow(ax, (17.0, 35.6), (MX - 13.0, 33.0), rad=0.08)
    arrow(ax, (48.0, 35.6), (MX + 8.0, 33.6), rad=-0.06)

    diamond(ax, MX, 24.0, 30.0, 6.0, "Is the extracted text at least\n50 characters long ?", fs=7.0)
    arrow(ax, (MX, 28.2), (MX, 27.0))
    box(ax, EX, 24.6, EW, 7.4,
        "HTTP 422 Unprocessable Entity —\nreported as a scanned or image-only PDF\nwhen images are present, otherwise as\ninsufficient readable text", kind="end", fs=6.7)
    arrow(ax, (MX + 15.0, 24.0), (EX - EW / 2, 24.6), label="No", fs=6.8, rad=0.06)

    box(ax, MX, 17.4, MW, 5.2,
        "SkillExtractor.extract_skills(raw_text, sections) returns canonical skills with\nmatched text, evidence snippet, category and confidence",
        kind="ai", fs=7.0)
    arrow(ax, (MX, 21.0), (MX, 20.0), label="Yes", fs=6.8)

    box(ax, MX, 12.2, MW, 4.6,
        "ResumeRepository.create_resume_with_skills() deactivates the previously active\nresume, inserts the resume row and its extracted_skills rows, then commits",
        kind="data", fs=7.0)
    arrow(ax, (MX, 14.8), (MX, 14.5))

    box(ax, MX, 7.4, MW, 4.6,
        "HTTP 201 Created — ResumeUploadResponse carrying id, filename, is_active,\nreplaced_previous, extracted_skills_count and the full skills array",
        kind="api", fs=7.0)
    arrow(ax, (MX, 9.9), (MX, 9.7))

    box(ax, MX, 2.6, MW, 4.2,
        "END — React Query invalidates the activeResume query; the UI renders skill chips,\nthe resume history list and the active badge",
        kind="end", fs=7.0, bold=True)
    arrow(ax, (MX, 5.1), (MX, 4.7))

    # ---- exception lane extras -------------------------------------------
    box(ax, EX, 13.0, EW, 7.6,
        "Any HTTPException or unexpected error removes the\njust-written file from UPLOAD_DIR before the error is\nre-raised, so a failed upload never leaves an orphan\nfile on disk", kind="note", fs=6.8)
    box(ax, EX, 4.6, EW, 6.0,
        "Rejected uploads never reach the database: no resume\nrow and no extracted_skills rows are created, and the\npreviously active resume stays active", kind="note", fs=6.8)

    return save(fig, "fig_resume_flow.png")


# ---------------------------------------------------------------------------
# Figure: Skill extraction and normalisation workflow
# ---------------------------------------------------------------------------
def fig_skill_extraction():
    fig, ax = new_ax(11.6, 7.8)

    # Row 0 — taxonomy preparation
    store(ax, 15.0, 60.0, 26.0, 8.0,
          "skills.json taxonomy\n56 canonical skills in 11 categories,\neach with aliases, regex patterns\nand context flags", fs=6.9)
    box(ax, 50.0, 60.0, 28.0, 8.0,
        "SkillNormalizer._build_lookup_indices()\ncanonical_map: lowercase canonical → definition\nalias_to_canonical: lowercase alias → canonical",
        kind="service", fs=6.9)
    box(ax, 84.0, 60.0, 26.0, 8.0,
        "SkillExtractor._compile_patterns()\nre.compile(pattern, re.IGNORECASE) for\nevery pattern; invalid patterns are logged\nand skipped", kind="service", fs=6.9)
    arrow(ax, (28.0, 60.0), (36.0, 60.0))
    arrow(ax, (64.0, 60.0), (71.0, 60.0))

    # Row 1 — scanning
    box(ax, 15.0, 47.5, 26.0, 7.0,
        "Resume raw_text and the section\nblocks produced by\n_segment_sections()", kind="start", fs=6.9)
    box(ax, 50.0, 47.5, 28.0, 7.0,
        "For each section block and each compiled\npattern, regex.finditer() locates every\nmention of the skill", kind="service", fs=6.9)
    box(ax, 84.0, 47.5, 26.0, 7.0,
        "Record matched_text with its start_char\nand end_char, and build an evidence\nsnippet spanning 60 characters on either\nside", kind="service", fs=6.9)
    arrow(ax, (28.0, 47.5), (36.0, 47.5))
    arrow(ax, (64.0, 47.5), (71.0, 47.5))
    arrow(ax, (84.0, 56.0), (84.0, 51.0), rad=0.0)

    # Row 2 — validation gates (right to left)
    diamond(ax, 82.0, 34.5, 28.0, 8.0,
            "Does the mention resolve to a\ncanonical taxonomy skill through the\nalias index or a punctuation-insensitive\ncomparison ?", fs=6.6)
    arrow(ax, (84.0, 44.0), (83.0, 38.5))
    box(ax, 82.0, 24.5, 28.0, 4.6,
        "Discard the match — it is outside the\ncontrolled vocabulary", kind="end", fs=6.8)
    arrow(ax, (82.0, 30.5), (82.0, 26.8), label="No", fs=6.8)

    diamond(ax, 45.0, 34.5, 30.0, 8.0,
            "Are the context and acronym guards\nsatisfied for ambiguous tokens such as\nsingle-letter 'C' or the acronym 'ML' ?", fs=6.6)
    arrow(ax, (68.0, 34.5), (60.0, 34.5), label="Yes", fs=6.8)
    box(ax, 45.0, 24.5, 30.0, 4.6,
        "Discard as a probable false positive\n(no supporting technical context nearby)", kind="end", fs=6.8)
    arrow(ax, (45.0, 30.5), (45.0, 26.8), label="No", fs=6.8)

    box(ax, 12.5, 34.5, 21.0, 9.0,
        "Assign a confidence score\n1.00 exact canonical text\n0.95 ordinary alias match\n0.90 context-dependent match\n+0.05 when found inside a\nSkills or Technologies section",
        kind="ai", fs=6.6)
    arrow(ax, (30.0, 34.5), (23.0, 34.5), label="Yes", fs=6.8)

    # Row 3 — output
    box(ax, 40.0, 14.0, 52.0, 9.0,
        "Deduplicate by canonical name, retaining the highest-confidence record across all\nsections, and emit the provenance object: canonical_name, matched_text, category,\nextraction_method = 'taxonomy_regex_spacy', evidence_snippet, confidence and\nposition {start_char, end_char, section}",
        kind="data", fs=7.0)
    elbow(ax, [(12.5, 30.0), (12.5, 14.0), (14.0, 14.0)])
    store(ax, 82.0, 4.0, 26.0, 6.0,
          "Persisted as extracted_skills\nrows linked to the resume", fs=6.9)
    elbow(ax, [(66.0, 14.0), (82.0, 14.0), (82.0, 7.0)])

    note(ax, 22.0, 5.0, 34.0, 8.0,
         "Aliases collapse surface variants onto one canonical skill, for example 'JS' and\n'ECMAScript' to JavaScript, 'ReactJS' to React and 'Postgre SQL' to PostgreSQL.\nBecause the evidence snippet and character offsets are retained, every extracted\nskill can be traced back to the exact sentence of the resume that produced it.",
         fs=6.8, title="Provenance and alias handling")

    return save(fig, "fig_skill_extraction.png")


if __name__ == "__main__":
    for fn in (fig_architecture, fig_modules, fig_resume_flow, fig_skill_extraction):
        print("wrote", fn())
