"""Report body content — Chapters 11 to 15, references and appendices.

The results tables in Chapter 13 are generated from report/observed_outputs.json,
which was produced by executing the project's own services; Appendix A is
generated from backend/app/taxonomy/skills.json.
"""

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_OBS = json.load(open(os.path.join(_HERE, "observed_outputs.json")))
_TAX = json.load(open(os.path.join(_HERE, "..", "backend", "app", "taxonomy", "skills.json")))

_skills = _OBS["resume"]["skills"]
_mkt = _OBS["market"]

# --- Table 13.2: every extracted skill -------------------------------------
_rows_skills = [
    [str(i + 1), s["canonical_name"], s["matched_text"], s["category"],
     f"{s['confidence']:.2f}", s["section"]]
    for i, s in enumerate(_skills)
]

# --- Table 13.3: demand ranking (top rows, remainder summarised) -----------
_top = _mkt["top_skills"][:14]
_rows_demand = [
    [str(i + 1), s["skill_name"], s["category"], str(s["matching_listings_count"]),
     str(s["total_listings_analyzed"]), f"{s['demand_percentage']:.2f}"]
    for i, s in enumerate(_top)
]

# --- Appendix A: taxonomy by category --------------------------------------
_cat_order = _TAX["categories"]
_rows_tax = []
for cat in _cat_order:
    names = [s["canonical_name"] for s in _TAX["skills"] if s["category"] == cat]
    _rows_tax.append([cat.replace("_", " "), str(len(names)), ", ".join(names)])


CH11_END = [
    # =======================================================================
    ("chapter", 11, "IMPLEMENTATION"),
    ("h2", "11.1 Back-End Organisation"),
    ("p", "The back end is a Python package named app, organised so that each concern has exactly one "
          "home. The api package holds the routers and the dependency providers; the services package "
          "holds the twelve business components; the repositories package isolates SQL access; the models "
          "and schemas packages define the persistence entities and the wire contracts; the core package "
          "contains configuration and security primitives; and the taxonomy directory carries the two "
          "reference files, skills.json and sample_jobs.json. The extract below shows the package layout "
          "as implemented."),
    ("code", {"caption": "Back-end package layout", "text": (
        "backend/app/\n"
        "├── api/            routes: auth, resumes, jobs, market_demand, skill_gap, roadmap\n"
        "│   └── deps.py     OAuth2PasswordBearer scheme, get_current_user, superuser check\n"
        "├── core/           config.py (pydantic-settings), security.py (bcrypt, JWT)\n"
        "├── db/             base.py (DeclarativeBase, timestamps), session.py (engine, get_db)\n"
        "├── models/         User, Resume, ExtractedSkill, JobListing, JobSkill, SkillGapAnalysis\n"
        "├── repositories/   user_repository.py, resume_repository.py\n"
        "├── schemas/        auth, resume, jobs, roadmap, skill_gap response contracts\n"
        "├── services/       auth, resume_parser, skill_extractor, skill_normalizer,\n"
        "│                 semantic_matcher, hybrid_matcher, job_provider, job_provider_adzuna,\n"
        "│                 job_ingestion, job_matcher, market_demand_service, skill_gap_service,\n"
        "│                 roadmap_service\n"
        "├── taxonomy/       skills.json (56 skills, 11 categories), sample_jobs.json (8 fixtures)\n"
        "└── tests/          eight pytest modules, 47 test functions")}),

    ("h2", "11.2 Security Implementation"),
    ("p", "Passwords are hashed with bcrypt through a passlib CryptContext, and tokens are signed with the "
          "HS256 algorithm using the configured secret [12], [13]. Token resolution is implemented once as a "
          "FastAPI dependency so that every protected route inherits identical semantics: decode, read the "
          "subject claim, load the user, confirm the account is active [14]. The essential excerpt is "
          "reproduced below."),
    ("code", {"caption": "Token creation and resolution (extract from core/security.py and api/deps.py)", "text": (
        "def create_access_token(subject, expires_delta=None, extra_claims=None):\n"
        "    if expires_delta:\n"
        "        expire = datetime.now(timezone.utc) + expires_delta\n"
        "    else:\n"
        "        expire = datetime.now(timezone.utc) + timedelta(\n"
        "            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)\n"
        "    to_encode = {\"sub\": subject, \"exp\": expire}\n"
        "    ...\n"
        "    return jwt.encode(to_encode, settings.JWT_SECRET,\n"
        "                      algorithm=settings.JWT_ALGORITHM)\n"
        "\n"
        "def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):\n"
        "    payload = jwt.decode(token, settings.JWT_SECRET,\n"
        "                         algorithms=[settings.JWT_ALGORITHM])\n"
        "    user_id = int(payload.get(\"sub\"))          # 401 when absent or malformed\n"
        "    user = UserRepository(db).get_by_id(user_id)  # 401 when unknown\n"
        "    if not user.is_active:                        # 400 when deactivated\n"
        "        raise HTTPException(400, \"Inactive user account\")\n"
        "    return user")}),

    ("h2", "11.3 Document Processing Implementation"),
    ("p", "The parser distinguishes three failure modes that naive implementations conflate: a zero-byte "
          "file, a file whose text layer is shorter than fifty characters although pages carry images, and "
          "a file that is simply too short. Each raises a different HTTP status with a different message, "
          "which the interface displays verbatim [23], [24]."),
    ("code", {"caption": "Scanned-document detection (extract from services/resume_parser.py)", "text": (
        "MIN_TEXT_LENGTH_THRESHOLD = 50\n"
        "...\n"
        "if len(combined_text) < cls.MIN_TEXT_LENGTH_THRESHOLD:\n"
        "    if has_images:\n"
        "        raise HTTPException(status_code=422, detail=(\n"
        "            \"The PDF appears to be a scanned document or image-only file. ...\"))\n"
        "    else:\n"
        "        raise HTTPException(status_code=422, detail=(\n"
        "            \"The PDF contains insufficient readable text ...\"))")}),

    ("h2", "11.4 Extraction and Normalisation Implementation"),
    ("p", "Extraction compiles every taxonomy pattern once at construction time and then sweeps each "
          "section block. Confidence is assigned by explicit rules rather than learned weights, which keeps "
          "the behaviour explainable: an exact canonical mention scores one, an ordinary alias scores zero "
          "point nine five, a mention that required a context guard scores zero point nine zero, and any "
          "mention found inside a skills or technologies section receives a bonus of zero point zero five "
          "capped at one [6]."),
    ("code", {"caption": "Confidence assignment (extract from services/skill_extractor.py)", "text": (
        "confidence = 0.95\n"
        "if matched_raw.lower() == canonical_name.lower():\n"
        "    confidence = 1.0\n"
        "elif skill_def.get(\"requires_context\") or \\\n"
        "        skill_def.get(\"requires_context_for_acronym\"):\n"
        "    confidence = 0.90\n"
        "if \"skill\" in section_name.lower() or \"technolog\" in section_name.lower():\n"
        "    confidence = min(1.0, confidence + 0.05)")}),

    ("h2", "11.5 Semantic Matching Implementation"),
    ("p", "The encoder is wrapped in a singleton that the FastAPI lifespan handler warms at start-up, so the "
          "first user request does not pay for model loading. Mean pooling follows the standard recipe for "
          "this model family: token embeddings are weighted by the attention mask, summed and divided by "
          "the clamped mask total, after which L2 normalisation makes the dot product equal to cosine "
          "similarity [26], [27]."),
    ("code", {"caption": "Mean pooling and normalisation (extract from services/semantic_matcher.py)", "text": (
        "def _mean_pooling(self, model_output, attention_mask):\n"
        "    token_embeddings = model_output[0]\n"
        "    input_mask_expanded = (attention_mask.unsqueeze(-1)\n"
        "                           .expand(token_embeddings.size()).float())\n"
        "    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)\n"
        "    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)\n"
        "    return sum_embeddings / sum_mask\n"
        "...\n"
        "normalized = F.normalize(sentence_embeddings, p=2, dim=1)")}),

    ("h2", "11.6 Evidence-Validation Implementation"),
    ("p", "The guard that separates relatedness from possession is a compact rule with an explicit "
          "adversarial list: a general architectural phrase present in the evidence may not validate a "
          "specific framework requirement. This single rule is the difference between a portal that "
          "flatters the candidate and one that informs them."),
    ("code", {"caption": "Adversarial evidence guard (extract from services/hybrid_matcher.py)", "text": (
        "if cand_in_evidence:\n"
        "    if clean_cand in [\"rest api\", \"rest apis\", \"restful api\", \"apis\",\n"
        "                      \"web services\", \"backend\"] and \\\n"
        "       clean_req in [\"fastapi\", \"django\", \"flask\", \"express.js\",\n"
        "                     \"spring boot\"]:\n"
        "        return False")}),

    ("h2", "11.7 Provider Fallback Implementation"),
    ("p", "The Adzuna client checks credentials before any network activity and treats the placeholder "
          "values shipped in the example configuration as absent, so a freshly cloned repository degrades "
          "gracefully instead of failing [25]. Non-200 responses and transport exceptions are converted "
          "into the same fixture path with a banner that names the concrete cause."),
    ("code", {"caption": "Credential gate (extract from services/job_provider_adzuna.py)", "text": (
        "if not app_id or not app_key or app_id == \"your_adzuna_app_id_here\":\n"
        "    return self._filter_sample_fixtures(query, location, page,\n"
        "                                        results_per_page, category, what_or)")}),

    ("h2", "11.8 Demand and Deduplication Implementation"),
    ("p", "Demand is computed over a set of listing keys per skill, which makes repeated mentions inside "
          "one listing count once, and the percentage is rounded to two decimals while the denominator "
          "travels with every row."),
    ("code", {"caption": "Demand percentage (extract from services/market_demand_service.py)", "text": (
        "matching_count = len(matching_job_set)\n"
        "demand_pct = round((matching_count / total_unique_listings) * 100, 2)\n"
        "skills_ranked.append({\"skill_name\": c_name, ..., \n"
        "                      \"matching_listings_count\": matching_count,\n"
        "                      \"total_listings_analyzed\": total_unique_listings,\n"
        "                      \"demand_percentage\": demand_pct})")}),

    ("h2", "11.9 Roadmap Sequencing Implementation"),
    ("p", "The ordering key implements the four-component rule of Section 8.9 verbatim, which is what makes "
          "two runs over identical data produce identical plans."),
    ("code", {"caption": "Deterministic ordering key (extract from services/roadmap_service.py)", "text": (
        "combined.sort(key=lambda x: (\n"
        "    -float(x.get(\"demand_percentage\", 0.0)),\n"
        "    -int(x.get(\"matching_listings_count\", 0)),\n"
        "    0 if x.get(\"status\") == \"missing\" else 1,\n"
        "    str(x.get(\"skill\", \"\")).lower()))")}),

    ("h2", "11.10 Front-End Implementation"),
    ("p", "The interface is a React application whose HTTP layer is a single Axios instance. A request "
          "interceptor attaches the stored bearer token to every call, so no page component needs to know "
          "that authentication exists [19], [22]. The sample-data banner is a component that renders "
          "nothing unless the payload flag is true, which is the mechanism that keeps offline "
          "demonstrations honest [21]."),
    ("code", {"caption": "Token interceptor and provenance banner (extracts from the front end)", "text": (
        "// src/api/client.js\n"
        "apiClient.interceptors.request.use((config) => {\n"
        "  const token = localStorage.getItem('access_token');\n"
        "  if (token) { config.headers.Authorization = `Bearer ${token}`; }\n"
        "  return config;\n"
        "});\n"
        "\n"
        "// src/components/SampleDataBanner.jsx\n"
        "export const SampleDataBanner = ({ isSampleData, message }) => {\n"
        "  if (!isSampleData) return null;\n"
        "  return (<Alert severity=\"warning\" ...>\n"
        "    {message || 'SAMPLE DATA — not live (Adzuna credentials not configured'\n"
        "            + ' or live API offline)'}\n"
        "  </Alert>);\n"
        "};")}),

    ("h2", "11.11 User Interface"),
    ("p", "The interface comprises five routed pages. The home page shows the portal identity, the live "
          "back-end health state polled every thirty seconds, and four module cards. The authentication "
          "page hosts the registration and login forms. The market-demand page exposes role and location "
          "filters together with the ranked demand table. The skill-gap page is the working surface: it "
          "contains the upload control, the resume history list and three tabs for recommendations, gap "
          "analysis and the roadmap. The roadmap page repeats the generator as a standalone route. The "
          "figures below show the principal screens as implemented."),
    ("fig", {"key": "shot_login", "kind": "screenshot", "width": 0.92,
             "caption": "Authentication screen with the registration and login forms"}),
    ("fig", {"key": "shot_upload", "kind": "screenshot", "width": 0.92,
             "caption": "Resume upload control with resume history on the Skill Gap page"}),
    ("fig", {"key": "shot_skills", "kind": "screenshot", "width": 0.92,
             "caption": "Skills extracted from the active resume with categories and evidence"}),
    ("fig", {"key": "shot_jobs", "kind": "screenshot", "width": 0.92,
             "caption": "Recommended jobs ranked by match percentage with matched and missing chips"}),
    ("fig", {"key": "shot_demand", "kind": "screenshot", "width": 0.92,
             "caption": "Market demand view showing per-skill percentages and the analysed denominator"}),
    ("fig", {"key": "shot_gap", "kind": "screenshot", "width": 0.92,
             "caption": "Role skill-gap report with priorities, evidence and overall match percentage"}),
    ("fig", {"key": "shot_roadmap", "kind": "screenshot", "width": 0.92,
             "caption": "Learning roadmap rendered as a vertical stepper ordered by market demand"}),

    # =======================================================================
    ("chapter", 12, "TESTING"),
    ("h2", "12.1 Testing Strategy"),
    ("p", "Verification was performed at three levels. Service-level unit tests exercise each analytical "
          "component with injected fixtures so that network calls are replaced by deterministic data. "
          "API-level tests drive the FastAPI application through an HTTP test client against a temporary "
          "database, asserting status codes, ownership enforcement and response shapes. Component-level "
          "front-end tests render React components with representative payloads and assert on the produced "
          "document. The back-end suites are executed with pytest [28]; the front-end suites with Vitest "
          "and Testing Library [29], [30]."),

    ("h2", "12.2 Back-End Test Suites"),
    ("table", {
        "caption": "Back-end pytest modules and their coverage",
        "headers": ["Module", "Tests", "Principal coverage"],
        "rows": [
            ["test_auth", "5", "Registration success; duplicate e-mail rejection; login with /me; wrong password 401; request without token 401"],
            ["test_health", "3", "/api/health, the /health alias and the root endpoint"],
            ["test_resumes", "12", "PDF and DOCX parsing; empty-file and scanned-file rejection; alias resolution (JS, PostgreSQL, Node, ML); false-positive suppression for 'C'; upload–skills–delete flow; empty active response; second upload deactivating the first; active-resume correctness; cross-user ownership isolation"],
            ["test_semantic_matcher", "8", "Singleton and batched encoding; embedding cache reuse; hybrid exact match; hybrid alias match; alias from raw mention; clean semantic match with evidence; adversarial REST-versus-FastAPI case; high score alone never matching"],
            ["test_job_matcher", "6", "Match-score arithmetic on fixtures; ranking order with min_match; ownership enforcement; fallback when credentials are absent; 404 for an unknown resume; non-zero match for a realistic profile"],
            ["test_market_demand", "7", "Deduplication by external id; deduplication by normalised composite key; demand arithmetic on fixtures; insufficient-data state; /jobs/search sample banner; /market-demand contract; unknown role insufficiency"],
            ["test_skill_gap", "2", "Analysis creation, retrieval by identifier and cross-user denial; failure on an unknown resume"],
            ["test_roadmap", "4", "Deterministic demand ordering; endpoint ordering with a mocked language model; ownership enforcement; fallback on language-model failure and timeout"],
        ],
        "widths": [0.18, 0.08, 0.74],
    }),
    ("p", "In total the back-end package contains forty-seven test functions. The project documentation "
          "records that the suite was executed with a fully passing result during development."),

    ("h2", "12.3 Front-End Test Suites"),
    ("table", {
        "caption": "Front-end Vitest suites and their coverage",
        "headers": ["Suite", "Cases", "Assertions"],
        "rows": [
            ["Footer", "1", "Brand name and copyright line are rendered"],
            ["LearningRoadmapView", "3", "Overall match, matched chips, ordered steps and the AI fallback notice; fully-matched empty state; loading indicator"],
            ["RecommendedJobCard", "5", "Title, company, location and salary; prominent match badge; matched and missing chips; apply link opening in a new tab with rel=noopener; unscored card shows an N/A badge"],
            ["SampleDataBanner", "3", "Banner shown when the flag is true; default message when none supplied; nothing rendered when the flag is false"],
            ["authService", "4", "Token persisted on register and login; /auth/me retrieval; token removal on logout"],
            ["skillGapService", "11", "One case per service function verifying method, path, parameters and multipart encoding"],
        ],
        "widths": [0.22, 0.08, 0.70],
    }),
    ("p", "The six suites contain twenty-seven cases in total, and the production build of the front end "
          "was verified to bundle without errors."),

    ("h2", "12.4 Functional Test Cases"),
    ("p", "Table 12.3 restates the principal functional validations in conventional test-case form. The "
          "actual results are those asserted by the automated suites named in the final column."),
    ("table", {
        "caption": "Functional test cases with expected and actual outcomes",
        "headers": ["ID", "Test input / action", "Expected result", "Actual result", "Status"],
        "rows": [
            ["TC-01", "Register with a new e-mail and a six-character password", "201 with access token and user object", "Token issued; user persisted with bcrypt hash", "Pass"],
            ["TC-02", "Register again with the same e-mail", "400 duplicate e-mail", "400 with explanatory detail", "Pass"],
            ["TC-03", "Login with a wrong password", "401 unauthorised", "401 'Incorrect email or password.'", "Pass"],
            ["TC-04", "Call /api/resumes without a token", "401 unauthorised", "401 with WWW-Authenticate header", "Pass"],
            ["TC-05", "Upload a one-page text PDF resume", "201 with parsed text and skills", "201; skills returned with evidence and confidence", "Pass"],
            ["TC-06", "Upload a DOCX resume containing a skills table", "201; table cells included", "Table text appended and skills extracted", "Pass"],
            ["TC-07", "Upload a zero-byte file", "400 empty-file error", "400 'completely empty (0 bytes)'", "Pass"],
            ["TC-08", "Upload an image-only scanned PDF", "422 scanned-document error", "422 with scanned-document explanation", "Pass"],
            ["TC-09", "Upload a second resume", "New resume active, first retained in history", "is_active moved; history contains both", "Pass"],
            ["TC-10", "Read another user's resume skills", "403 forbidden", "403 on ownership mismatch", "Pass"],
            ["TC-11", "Text containing 'JS' and 'ReactJS'", "Canonical JavaScript and React", "Aliases resolved to canonical names", "Pass"],
            ["TC-12", "Text containing the bare letter 'C' without context", "No C skill extracted", "Mention rejected by the context guard", "Pass"],
            ["TC-13", "Candidate 'built REST APIs' against requirement FastAPI", "needs_review, not matched", "needs_review with evidence explanation", "Pass"],
            ["TC-14", "Recommendations with Adzuna credentials unset", "Fixture results with sample banner", "is_sample_data true and banner message set", "Pass"],
            ["TC-15", "Feed a duplicated listing stream to ingestion", "Duplicates filtered by id and fingerprint", "Both rules removed the duplicates", "Pass"],
            ["TC-16", "Demand analysis over an empty result set", "insufficient_data status, empty skills", "Status and message returned, no percentages", "Pass"],
            ["TC-17", "Analyse a gap for a role and re-open it by id", "Identical persisted result", "Retrieved document matches the original", "Pass"],
            ["TC-18", "Generate a roadmap twice over the same data", "Identical step order", "Ordering deterministic across runs", "Pass"],
            ["TC-19", "Generate a roadmap with the language model unreachable", "Steps returned with unavailable notice", "ai_explanation_available false; notice text set", "Pass"],
            ["TC-20", "Render a job card with a null match percentage", "Unscored badge, ranked last", "N/A badge rendered; ranking places it below scorable cards", "Pass"],
        ],
        "widths": [0.07, 0.27, 0.22, 0.30, 0.08],
    }),

    ("h2", "12.5 Adversarial and Boundary Testing"),
    ("p", "Two adversarial families were tested explicitly because they are the failure modes that "
          "discredit matching systems. The first is semantic over-reach, in which a resume phrase that is "
          "merely related to a requirement must not satisfy it; the suite asserts that a REST-oriented "
          "resume does not acquire FastAPI, and that a high cosine score without validating evidence never "
          "produces a matched verdict. The second is lexical over-reach, in which short or ambiguous tokens "
          "match inside unrelated words; the suite asserts that a bare 'C' and substring accidents are "
          "suppressed. Boundary testing additionally covers the fifty-character text threshold, the "
          "five-megabyte upload ceiling, empty result sets and unknown identifiers."),

    # =======================================================================
    ("chapter", 13, "RESULTS AND DISCUSSION"),
    ("h2", "13.1 Demonstration Configuration"),
    ("p", "All quantitative results reported in this chapter were produced by executing the implemented "
          "services inside the development environment with Adzuna credentials unset and no language-model "
          "key configured. Consequently the market corpus is the offline fixture set shipped with the "
          "repository, and every figure below is a sample-mode figure; the application itself labels such "
          "output with the SAMPLE DATA banner, and the same labelling applies to this discussion. No "
          "classification accuracy is reported anywhere in this chapter, because the system is not a "
          "classifier: its outputs are extracted facts, computed shares and ordered plans, each of which is "
          "validated by construction and by the automated suites rather than by a held-out label set."),

    ("h2", "13.2 Resume Ingestion and Extraction Results"),
    ("p", "The repository's sample resume was parsed and extracted. The document recovered "
          f"{_OBS['resume']['metadata']['char_count']} characters from "
          f"{_OBS['resume']['metadata']['page_count']} page with no embedded images, and the segmenter "
          "identified the sections listed in Table 13.1. Extraction produced "
          f"{len(_skills)} canonical skills, of which "
          f"{sum(1 for s in _skills if s['confidence'] == 1.0)} scored the maximum confidence and one, "
          "REST API, scored 0.95 because it was matched through the surface form 'RESTful' inside the "
          "experience section rather than inside the skills list."),
    ("table", {
        "caption": "Parsing outcome for the sample resume",
        "headers": ["Attribute", "Value"],
        "rows": [
            ["File", _OBS["resume"]["file"]],
            ["Recovered characters", str(_OBS["resume"]["metadata"]["char_count"])],
            ["Pages", str(_OBS["resume"]["metadata"]["page_count"])],
            ["Embedded images", str(_OBS["resume"]["metadata"]["has_images"])],
            ["Detected sections", " → ".join(_OBS["resume"]["sections"])],
            ["Canonical skills extracted", str(len(_skills))],
            ["Distinct categories represented", str(len({s["category"] for s in _skills}))],
        ],
        "widths": [0.34, 0.66],
    }),
    ("table", {
        "caption": "Skills extracted from the sample resume with provenance",
        "headers": ["#", "Canonical skill", "Matched text", "Category", "Confidence", "Section"],
        "rows": _rows_skills,
        "widths": [0.045, 0.20, 0.15, 0.235, 0.145, 0.225],
    }),
    ("p", "Two observations merit discussion. First, the evidence snippets returned with every skill make "
          "the extraction auditable: a reviewer can confirm in one glance that Docker was read from the "
          "cloud and DevOps line rather than inferred. Second, the single sub-maximal confidence is "
          "informative rather than defective; it records that the mention was narrative rather than "
          "declarative, and the value propagates into the job-skill importance weight when the same text "
          "is treated as a requirement."),

    ("h2", "13.3 Market Demand Results"),
    ("p", "The fixture corpus contains eight listings. Deduplication left all eight unique, and re-feeding "
          "the corpus twice yielded eight unique listings and eight filtered duplicates, confirming that "
          "both deduplication rules behave as specified. Demand was then computed over the eight-listing "
          "population; thirty-two distinct canonical skills were observed, of which the fourteen highest "
          "are listed in Table 13.3. Because the denominator is eight, each percentage is an exact "
          "multiple of twelve and a half, which also illustrates why the denominator must accompany the "
          "percentage: a share of fifty percent over eight listings is a much weaker signal than the same "
          "share over eight thousand."),
    ("table", {
        "caption": "Market demand computed over the offline fixture corpus (denominator 8 unique listings)",
        "headers": ["Rank", "Skill", "Category", "Listings", "Denominator", "Demand %"],
        "rows": _rows_demand,
        "widths": [0.08, 0.26, 0.26, 0.12, 0.14, 0.14],
    }),
    ("p", "Under the project's priority bands the two leading skills at fifty percent fall in the Medium "
          "band, while the remainder of the fixture corpus falls in the Low band; a live corpus of "
          "hundreds of listings would distribute across all three bands. This is precisely the behaviour "
          "the design intends: priorities are a function of measured demand, not of a fixed table."),
    ("table", {
        "caption": "Deduplication experiment on the fixture corpus",
        "headers": ["Feed", "Received", "Unique retained", "Duplicates filtered"],
        "rows": [
            ["Single pass of the corpus", str(_mkt["received"]), str(_mkt["unique"]), str(_mkt["duplicates"])],
            ["Corpus concatenated with itself", str(_mkt["received"] * 2), str(_mkt["doubled_feed_unique"]),
             str(_mkt["doubled_feed_duplicates"])],
        ],
        "widths": [0.40, 0.18, 0.21, 0.21],
    }),

    ("h2", "13.4 Behavioural Results of Matching, Gap and Roadmap Stages"),
    ("p", "The behaviour of the stages that depend on the semantic encoder and on persistence was validated "
          "through the automated suites, since those components cannot be exercised without the model "
          "weights and a database. The suites confirm that exact and alias matches short-circuit before "
          "any embedding is computed, that a clean semantic match above the threshold is accepted only "
          "with validating evidence, that the adversarial REST-versus-FastAPI case is routed to "
          "needs-review, that recommendations rank scorable listings by descending match percentage with "
          "unscorable listings last, that gap analyses persist and re-open identically, and that roadmap "
          "order is invariant across repeated runs and survives language-model failure."),

    ("h2", "13.5 Validation Summary"),
    ("table", {
        "caption": "Summary of validation performed per capability",
        "headers": ["Capability", "Validation method", "Outcome"],
        "rows": [
            ["Authentication and ownership", "API tests with two users and missing tokens", "All denial paths returned the specified status codes"],
            ["Resume ingestion", "Service and API tests over generated PDF and DOCX files", "Text recovered; empty, corrupt and scanned inputs rejected with distinct messages"],
            ["Skill extraction", "Service tests plus the execution reported in Section 13.2", "24 canonical skills with evidence; aliases resolved; false positives suppressed"],
            ["Semantic and hybrid matching", "Unit tests including adversarial pairs", "Five-stage order and the evidence invariant held in every case"],
            ["Listing retrieval and fallback", "API tests with monkey-patched credentials", "Fixture path taken with correct banner whenever live access was unavailable"],
            ["Deduplication and demand", "Service tests plus the execution reported in Section 13.3", "Both rules filtered duplicates; percentages carried their denominator"],
            ["Gap analysis", "API tests with persistence and cross-user denial", "Analyses stored and re-opened identically"],
            ["Roadmap generation", "Service and API tests with mocked and failing language models", "Ordering deterministic; fallback notice emitted without blocking"],
            ["Interface rendering", "Component tests across six suites", "Badges, chips, steppers and the provenance banner render as specified"],
        ],
        "widths": [0.24, 0.36, 0.40],
    }),

    ("h2", "13.6 Discussion of Limitations"),
    ("bullets", [
        "The offline fixture corpus is small by construction; it demonstrates the arithmetic and the "
        "labelling, but it is not a market measurement and is never presented as one.",
        "Scanned and image-only resumes are detected and explained but not read, since optical character "
        "recognition is outside the project scope.",
        "The taxonomy is curated manually; a technology absent from it cannot be extracted, which bounds "
        "recall by design in exchange for precision and auditability.",
        "A single general-purpose encoder is used; domain-adapted embeddings could raise semantic quality "
        "at the cost of the training effort the mini project deliberately avoids.",
        "Priority bands are project conventions; they are disclosed in every response so that users do not "
        "mistake them for industry standards.",
    ]),

    # =======================================================================
    ("chapter", 14, "CONCLUSION"),
    ("p", "The project set out to replace anecdotal career guidance with a measured, auditable pipeline, "
          "and the implemented system achieves that within the declared scope. A resume deposited once "
          "becomes a structured, evidenced profile; a target role becomes a demand-weighted requirement "
          "set; and the difference between the two becomes a ranked vacancy list, a prioritised gap report "
          "and a deterministic learning sequence. Every stage was built to answer the question a sceptical "
          "student would ask: the extraction cites its sentence, the percentage cites its denominator, the "
          "match cites its evidence, and the data source cites itself."),
    ("p", "Three engineering decisions proved decisive. The five-stage matcher with its evidence gate "
          "prevented the most seductive failure of embedding-based systems, namely treating relatedness as "
          "competence. The deduplicate-then-count discipline made the demand figures meaningful at any "
          "corpus size. And the uniform provenance flag for live versus sample data allowed the entire "
          "application to remain fully demonstrable without ever misrepresenting its inputs. Together with "
          "a layered architecture and an extensive automated suite, these decisions give the mini project a "
          "foundation that can absorb the enhancements outlined in the next chapter without redesign."),

    # =======================================================================
    ("chapter", 15, "FUTURE ENHANCEMENTS"),
    ("bullets", [
        "Add an optical character recognition stage so that scanned resumes can be read instead of merely "
        "rejected, preserving the existing explanation path as its fallback.",
        "Map the internal taxonomy onto a public occupational vocabulary such as ESCO so that demand can be "
        "compared across countries and sectors [8].",
        "Persist demand snapshots with timestamps and visualise their drift, turning the portal into a "
        "longitudinal labour-market instrument.",
        "Introduce domain-adapted sentence embeddings fine-tuned on skill phrases, evaluated against a "
        "labelled synonym set, to refine the semantic stage beyond the general-purpose encoder.",
        "Cache market-demand results per role and location with a bounded lifetime to reduce repeated "
        "provider calls during a session.",
        "Extend the roadmap with prerequisite awareness, so that a step depending on another skill is "
        "ordered after its prerequisite even when its demand is higher.",
        "Provide an employer-side ingestion path that accepts structured vacancy submissions in addition to "
        "the external API.",
        "Ship the PostgreSQL configuration with containerised deployment and automated migration on "
        "start-up, completing the production-readiness path already prepared in the connection layer.",
    ]),

    # =======================================================================
    ("refs", [
        "World Economic Forum, The Future of Jobs Report 2025. Geneva: World Economic Forum, 2025.",
        "F. Ricci, L. Rokach and B. Shapira, Eds., Recommender Systems Handbook, 3rd ed. Cham: Springer, 2022.",
        "N. Reimers and I. Gurevych, 'Sentence-BERT: Sentence embeddings using siamese BERT-networks,' in Proc. Conf. Empirical Methods Natural Language Processing (EMNLP-IJCNLP), 2019, pp. 4228–4238.",
        "W. Wang et al., 'MiniLM: Deep self-attention distillation for task-agnostic compression of pre-trained transformers,' in Proc. Advances in Neural Information Processing Systems (NeurIPS), 2020.",
        "T. Wolf et al., 'Transformers: State-of-the-art natural language processing,' in Proc. Conf. Empirical Methods Natural Language Processing: System Demonstrations, 2020, pp. 38–45.",
        "M. Honnibal and I. Montani, 'spaCy 2: Natural language understanding with Bloom embeddings, convolutional neural networks and incremental parsing,' 2017.",
        "Lightcast, 'Lightcast Open Skills: skills taxonomy documentation,' Lightcast Inc., 2024.",
        "European Commission, 'ESCO v1.1: European Skills, Competences, Qualifications and Occupations,' Publications Office of the European Union, 2022.",
        "LinkedIn, 'Global Skills Report 2024,' LinkedIn Corporation, 2024.",
        "A. Vaswani et al., 'Attention is all you need,' in Proc. Advances in Neural Information Processing Systems (NeurIPS), 2017, pp. 5998–6008.",
        "J. Devlin, M.-W. Chang, K. Lee and K. Toutanova, 'BERT: Pre-training of deep bidirectional transformers for language understanding,' in Proc. NAACL-HLT, 2019, pp. 4171–4186.",
        "M. Jones, J. Bradley and N. Sakimura, 'JSON Web Token (JWT),' IETF RFC 7519, 2015.",
        "N. Provos and D. Mazières, 'A future-adaptable password scheme,' in Proc. USENIX Annual Technical Conference, 1999.",
        "M. Jones and D. Hardt, 'The OAuth 2.0 authorization framework: Bearer token usage,' IETF RFC 6750, 2012.",
        "S. Ramírez, 'FastAPI documentation,' 2024. [Online]. Available: https://fastapi.tiangolo.com",
        "Pydantic Software, 'Pydantic v2 documentation,' 2024. [Online]. Available: https://docs.pydantic.dev",
        "SQLAlchemy authors, 'SQLAlchemy 2.0 documentation,' 2024. [Online]. Available: https://docs.sqlalchemy.org",
        "M. Bayer, 'Alembic documentation,' 2024. [Online]. Available: https://alembic.sqlalchemy.org",
        "Meta Platforms, 'React documentation,' 2024. [Online]. Available: https://react.dev",
        "TanStack, 'TanStack Query v5 documentation,' 2024. [Online]. Available: https://tanstack.com/query",
        "MUI SE, 'Material UI documentation,' 2024. [Online]. Available: https://mui.com",
        "E. You and Vite contributors, 'Vite documentation,' 2024. [Online]. Available: https://vitejs.dev",
        "Artifex Software, 'PyMuPDF documentation,' 2024. [Online]. Available: https://pymupdf.readthedocs.io",
        "python-docx authors, 'python-docx documentation,' 2024. [Online]. Available: https://python-docx.readthedocs.io",
        "Adzuna, 'Adzuna developer API documentation,' 2024. [Online]. Available: https://developer.adzuna.com",
        "N. Reimers and I. Gurevych, 'sentence-transformers: sentence and text embedding library,' 2020. [Online]. Available: https://sbert.net",
        "Hugging Face, 'all-MiniLM-L6-v2 model card,' Hugging Face Model Hub, 2024. [Online]. Available: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
        "pytest developers, 'pytest documentation,' 2024. [Online]. Available: https://docs.pytest.org",
        "Vitest team, 'Vitest documentation,' 2024. [Online]. Available: https://vitest.dev",
        "Testing Library authors, 'Testing Library documentation,' 2024. [Online]. Available: https://testing-library.com",
        "Google DeepMind, 'Gemini API documentation,' 2025. [Online]. Available: https://ai.google.dev",
        "OpenAI, 'OpenAI API documentation,' 2025. [Online]. Available: https://platform.openai.com/docs",
    ]),

    # =======================================================================
    ("chapter", "A", "SKILL TAXONOMY"),
    ("p", "The taxonomy file skills.json defines fifty-six canonical skills distributed over eleven "
          "categories. Each entry additionally carries alias spellings, boundary-sensitive regular "
          "expressions and, for ambiguous tokens, context keyword requirements. Table A.1 lists the "
          "canonical members of every category."),
    ("table", {
        "caption": "Canonical skills per taxonomy category",
        "headers": ["Category", "Count", "Canonical skills"],
        "rows": _rows_tax,
        "widths": [0.20, 0.08, 0.72],
    }),

    ("chapter", "B", "APPLICATION PROGRAMMING INTERFACE"),
    ("p", "Table B.1 enumerates the complete HTTP surface of the back end. Endpoints marked bearer resolve "
          "the caller through the token dependency before any service is invoked."),
    ("table", {
        "caption": "REST endpoints of SkillSync AI",
        "headers": ["Method and path", "Auth", "Purpose"],
        "rows": [
            ["POST /api/auth/register", "public", "Create an account and receive an initial token"],
            ["POST /api/auth/login", "public", "Verify credentials and receive a token"],
            ["GET /api/auth/me", "bearer", "Return the authenticated user"],
            ["GET /api/resumes", "bearer", "List the caller's resume history"],
            ["GET /api/resumes/active", "bearer", "Return the active resume, its skills and latest analysis"],
            ["POST /api/resumes/upload", "bearer", "Upload, parse, extract and activate a resume"],
            ["POST /api/resumes/{id}/activate", "bearer", "Promote a historical resume to active"],
            ["GET /api/resumes/{id}/skills", "bearer", "Return extracted skills of one resume"],
            ["DELETE /api/resumes/{id}", "bearer", "Delete a resume, its skills and its file"],
            ["GET /api/jobs/search", "public", "Search listings with role and location filters"],
            ["GET /api/jobs/recommendations", "bearer", "Rank listings against a resume"],
            ["GET /api/market-demand", "public", "Demand percentages with denominator"],
            ["POST /api/skill-gap/analyze", "bearer", "Run and persist a gap analysis"],
            ["GET /api/skill-gap/{analysis_id}", "bearer", "Re-open a persisted analysis"],
            ["GET /api/roadmap", "bearer", "Generate the demand-ordered learning roadmap"],
            ["GET /api/health, GET /health, GET /", "public", "Operational readiness and service banner"],
        ],
        "widths": [0.34, 0.10, 0.56],
    }),

    ("chapter", "C", "EVIDENCE EXAMPLES"),
    ("p", "The following evidence snippets are reproduced verbatim from the extraction run reported in "
          "Section 13.2, truncated only where indicated by an ellipsis, to illustrate the provenance that "
          "accompanies every extracted skill."),
    ("table", {
        "caption": "Evidence snippets for selected extracted skills",
        "headers": ["Canonical skill", "Section", "Evidence snippet"],
        "rows": [
            [s["canonical_name"], s["section"], s["evidence_snippet"]]
            for s in _skills if s["canonical_name"] in
            ("FastAPI", "PostgreSQL", "REST API", "Kubernetes", "Material UI")
        ],
        "widths": [0.16, 0.18, 0.66],
    }),

    ("chapter", "D", "REPRODUCTION PROCEDURE"),
    ("p", "The results of Chapter 13 can be reproduced from a clean clone with the commands below. The "
          "market figures require no external credentials because the fixture path is taken automatically "
          "when the Adzuna variables are unset."),
    ("code", {"caption": "Reproducing the reported outputs", "text": (
        "# back end\n"
        "cd backend\n"
        "pip install -r requirements.txt\n"
        "python -m alembic upgrade head\n"
        "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000\n"
        "python -m pytest app/tests -v\n"
        "\n"
        "# front end\n"
        "cd frontend\n"
        "npm install\n"
        "npm run dev\n"
        "npm test\n"
        "\n"
        "# observed extraction and demand figures\n"
        "python - <<'PY'\n"
        "from app.services.resume_parser import ResumeParserService\n"
        "from app.services.skill_extractor import SkillExtractor\n"
        "from app.services.market_demand_service import MarketDemandService\n"
        "p = ResumeParserService.parse_file('test_candidate_resume.pdf', 'r.pdf')\n"
        "print(SkillExtractor().extract_skills(p['raw_text'], sections=p['sections']))\n"
        "print(MarketDemandService().analyze_market_demand(role='', location=''))\n"
        "PY")}),
]
