"""Report body content — Chapters 6 to 10."""

CH6_10 = [
    # =======================================================================
    ("chapter", 6, "REQUIREMENT ANALYSIS"),
    ("h2", "6.1 Functional Requirements"),
    ("p", "The functional requirements were elicited from the intended user journey: create an account, "
          "deposit a resume, inspect what the system understood, ask for vacancies, ask for a gap report "
          "against a role, and ask for a learning sequence. Each requirement below is implemented by an "
          "endpoint and a service in the final system."),
    ("table", {
        "caption": "Functional requirements of SkillSync AI",
        "headers": ["ID", "Requirement", "Priority"],
        "rows": [
            ["FR-01", "The system shall allow a user to register with e-mail, password and optional full name, and shall reject duplicate e-mail addresses.", "Must"],
            ["FR-02", "The system shall authenticate users with e-mail and password and issue a time-limited signed JSON Web Token.", "Must"],
            ["FR-03", "The system shall restrict every resume, analysis and recommendation operation to the owner of the resource.", "Must"],
            ["FR-04", "The system shall accept resume uploads in PDF and DOCX format up to a configurable maximum size and reject other formats and oversized files with explanatory errors.", "Must"],
            ["FR-05", "The system shall recover readable text from uploaded documents, detect empty, corrupt and scanned image-only files, and explain each rejection.", "Must"],
            ["FR-06", "The system shall segment recovered text into standard resume sections and retain the section of every extracted skill.", "Should"],
            ["FR-07", "The system shall extract canonical technical skills with aliases, categories, confidence values and evidence snippets carrying character offsets.", "Must"],
            ["FR-08", "The system shall maintain a non-destructive resume history in which exactly one resume per user is active at any time.", "Must"],
            ["FR-09", "The system shall retrieve vacancy listings from the Adzuna API when credentials are configured, and otherwise serve clearly labelled offline fixtures.", "Must"],
            ["FR-10", "The system shall rank vacancies against the candidate profile by match percentage and report matched and missing skills for each listing.", "Must"],
            ["FR-11", "The system shall compute per-skill market demand over unique listings and return the denominator with every percentage.", "Must"],
            ["FR-12", "The system shall classify demanded skills as matched, missing or needing review and assign demand-derived priorities.", "Must"],
            ["FR-13", "The system shall persist each gap analysis and allow the owner to retrieve it later by identifier.", "Should"],
            ["FR-14", "The system shall generate an ordered learning roadmap whose step order is monotonic in market demand, with optional language-model explanations and a safe fallback.", "Must"],
            ["FR-15", "The interface shall display a warning banner whenever displayed market data originated from offline fixtures.", "Must"],
        ],
        "widths": [0.09, 0.79, 0.12],
    }),

    ("h2", "6.2 Non-Functional Requirements"),
    ("table", {
        "caption": "Non-functional requirements of SkillSync AI",
        "headers": ["ID", "Category", "Requirement"],
        "rows": [
            ["NFR-01", "Security", "Passwords shall be stored only as bcrypt hashes; tokens shall be signed with HS256 and expire after a configurable interval (default sixty minutes)."],
            ["NFR-02", "Security", "Credentials for external services shall be read from environment configuration and shall never appear in source code or responses."],
            ["NFR-03", "Performance", "The sentence encoder shall be instantiated once per process and warmed at start-up; repeated embeddings shall be served from an in-memory cache."],
            ["NFR-04", "Reliability", "Failure of the job API or of the language model shall degrade to a labelled fallback rather than abort the request."],
            ["NFR-05", "Integrity", "Uploaded files shall be removed again whenever parsing or persistence fails, so no orphan artefacts remain."],
            ["NFR-06", "Usability", "Every market-derived figure shall be shown together with its population size, and every offline-derived view shall carry an explicit banner."],
            ["NFR-07", "Maintainability", "Business rules shall reside in single-responsibility services, with repositories isolating database access and Pydantic schemas fixing the response contracts."],
            ["NFR-08", "Portability", "The persistence layer shall run on SQLite by default and on PostgreSQL through a connection-string change plus existing migrations."],
            ["NFR-09", "Testability", "Each analytical service shall accept injected providers and clients so that deterministic fixture-based tests can replace network calls."],
        ],
        "widths": [0.09, 0.15, 0.76],
    }),

    ("h2", "6.3 Hardware Requirements"),
    ("table", {
        "caption": "Minimum and recommended development hardware",
        "headers": ["Component", "Minimum", "Recommended"],
        "rows": [
            ["Processor", "Dual-core x86-64, 2.0 GHz", "Quad-core or better, 3.0 GHz"],
            ["Memory", "8 GB RAM", "16 GB RAM (encoder plus browser plus servers)"],
            ["Storage", "2 GB free for dependencies and model weights", "10 GB solid-state"],
            ["Network", "Broadband for dependency and model download", "Broadband with stable DNS for API calls"],
            ["Display", "1366 × 768", "1920 × 1080"],
        ],
        "widths": [0.22, 0.36, 0.42],
    }),

    ("h2", "6.4 Software Requirements"),
    ("table", {
        "caption": "Software environment used to build and run the system",
        "headers": ["Layer", "Technology", "Role in the project"],
        "rows": [
            ["Runtime", "Python 3.11 or 3.12", "Backend interpreter"],
            ["Runtime", "Node.js 18 or newer", "Frontend toolchain and test runner"],
            ["Framework", "FastAPI with Uvicorn", "Asynchronous HTTP service and ASGI server"],
            ["Validation", "Pydantic v2 and pydantic-settings", "Request and response contracts; environment configuration"],
            ["Persistence", "SQLAlchemy 2.0 with Alembic", "ORM models and schema migrations"],
            ["Documents", "PyMuPDF and python-docx", "PDF and DOCX text recovery"],
            ["NLP", "spaCy blank English pipeline with sentencizer", "Sentence and token boundary segmentation during extraction"],
            ["Semantic", "Transformers and PyTorch, all-MiniLM-L6-v2", "Dense sentence embeddings and cosine similarity"],
            ["Numeric", "NumPy and Torch tensors", "Vector operations in the similarity stage"],
            ["Interface", "React 18, Vite 5, Material UI 5", "Single-page application and component library"],
            ["State", "TanStack React Query and Axios", "Server-state caching and HTTP client with token interceptor"],
            ["Testing", "pytest with httpx TestClient; Vitest with Testing Library", "Backend and frontend verification"],
        ],
        "widths": [0.16, 0.36, 0.48],
    }),

    ("h2", "6.5 Actors and Use Cases"),
    ("p", "The system recognises a single human actor, the job seeker, and two external system actors: the "
          "Adzuna job-search service and an optional language-model provider. The human actor's goals are "
          "captured by the use cases of Figure 6.1. All use cases below the session boundary include "
          "successful sign-in, because every resume-scoped operation is resolved through the authenticated "
          "user identity."),
    ("fig", {"key": "usecase", "caption": "Use-case view of SkillSync AI with its human and system actors",
             "width": 0.95}),

    # =======================================================================
    ("chapter", 7, "SYSTEM DESIGN"),
    ("h2", "7.1 Design Philosophy"),
    ("p", "The design follows a layered, service-oriented structure. Routers own only transport concerns: "
          "they validate input, resolve the authenticated user and delegate. Services own the business "
          "rules and may be composed, as the roadmap service composes the gap service and the gap service "
          "composes the market-demand and hybrid-matching services. Repositories own SQL access, so "
          "services never write queries against models directly except for narrow reads. Pydantic schemas "
          "fix the outward contract of every endpoint, which makes the interface self-documenting through "
          "the generated OpenAPI schema. This separation is what allows the analytical core to be tested "
          "with injected fixtures instead of live network services."),

    ("h2", "7.2 Module Decomposition"),
    ("p", "Figure 7.1 decomposes the system into its three subsystems and their principal modules. The "
          "front-end subsystem contains the routed pages, the reusable components, the service modules that "
          "wrap HTTP calls, and the state layer formed by the authentication context and the React Query "
          "cache. The back-end subsystem contains the route packages, the dependency providers, the "
          "service layer, the repositories, the ORM models with their schemas, and the core configuration "
          "and security modules. The third subsystem groups every durable or external artefact: the "
          "relational store, the upload directory, the taxonomy and fixture files, the encoder weights and "
          "the two external services."),
    ("fig", {"key": "modules", "caption": "Module decomposition of the SkillSync AI system", "width": 0.95}),

    ("h2", "7.3 Data-Flow Design"),
    ("p", "At the highest level of abstraction the portal is a single process exchanging flows with two "
          "external services and with its own durable stores, as shown in the context diagram of Figure "
          "7.2. The candidate supplies credentials, a resume document and analysis parameters, and receives "
          "a token, extracted skills, ranked vacancies, demand figures, gap reports and roadmaps."),
    ("fig", {"key": "dfd0", "caption": "Context diagram (level-0 data flow) of SkillSync AI", "width": 0.95}),
    ("p", "Decomposing the single process yields the level-1 diagram of Figure 7.3. Ten processes are "
          "identified. Authentication guards the session; ingestion and parsing recover document text; "
          "extraction and normalisation produce canonical skills; retrieval obtains listings either live or "
          "from fixtures; deduplication and storage persist unique listings together with their skills; "
          "market-demand analysis computes shares; hybrid matching evaluates requirements; ranking produces "
          "recommendations; gap analysis classifies and persists; and roadmap sequencing orders the "
          "residual skills. Eight data stores participate, of which two are read-only reference files."),
    ("fig", {"key": "dfd1", "caption": "Level-1 data-flow diagram of SkillSync AI", "width": 1.0}),

    ("h2", "7.4 Resume Ingestion Design"),
    ("p", "The ingestion pipeline is designed as a sequence of validated stages, each of which either "
          "advances the document or terminates the request with a specific, human-readable HTTP error. "
          "Figure 7.4 shows the complete flow including the exception lane. Two design decisions deserve "
          "emphasis. First, the file is written to disk before parsing and deleted again if any later stage "
          "fails, so the file store never diverges from the database. Second, the parser distinguishes a "
          "scanned document from an empty one by checking whether pages carry images while yielding less "
          "than fifty characters of text, and reports the two situations with different messages."),
    ("fig", {"key": "resume_flow", "caption": "Resume ingestion data flow with validation gates and the exception lane",
             "width": 0.86}),

    ("h2", "7.5 Skill Extraction and Normalisation Design"),
    ("p", "Extraction is designed as a two-phase process. In the preparation phase the taxonomy file is "
          "loaded once and indexed twice: canonical names map to their definitions and every alias maps to "
          "its canonical owner, while every regular-expression pattern of every skill is compiled with "
          "case-insensitivity so that scanning costs nothing beyond a single pass per pattern. In the "
          "scanning phase each section block is swept by every compiled pattern; each hit yields the "
          "matched text, its character span and an evidence snippet of sixty characters on either side. The "
          "hit then passes two gates — canonical resolution and context validation — before receiving a "
          "confidence value. Duplicates of the same canonical skill are collapsed by retaining the "
          "highest-confidence record. Figure 7.5 presents the workflow."),
    ("fig", {"key": "skill_extraction", "caption": "Skill extraction and normalisation workflow with validation gates",
             "width": 0.98}),

    ("h2", "7.6 Semantic and Hybrid Matching Design"),
    ("p", "The semantic stage is designed around a single process-level encoder instance. Texts are "
          "tokenised with padding and truncation at one hundred and twenty-eight tokens, pushed through the "
          "six-layer transformer under gradient-free inference, mean-pooled with the attention mask and "
          "L2-normalised, after which cosine similarity reduces to a dot product. Candidate and requirement "
          "sets are compared in one matrix multiplication, and every encoded string is cached so repeated "
          "analyses do not re-encode stable skill names. Figure 7.6 summarises this pipeline."),
    ("fig", {"key": "semantic_embedding", "caption": "Sentence-embedding pipeline used for semantic skill comparison",
             "width": 0.98}),
    ("p", "Semantic scores are consumed by the five-stage hybrid pipeline of Figure 7.7. Exact canonical "
          "equality is tested first, then alias membership, then the semantic threshold, then evidence "
          "validation, and finally a residual band. The ordering is deliberate: cheap and certain tests "
          "short-circuit expensive and probabilistic ones, and no probabilistic signal can produce a "
          "positive verdict without surviving the evidence gate."),
    ("fig", {"key": "hybrid_matcher", "caption": "Five-stage hybrid matching decision pipeline", "width": 0.92}),

    ("h2", "7.7 Job Recommendation Design"),
    ("p", "Recommendation is designed as a three-strategy retrieval followed by per-listing scoring. The "
          "retrieval strategies widen the net only as far as necessary: a disjunctive search over the five "
          "strongest resume skills, then a search on the single strongest skill, then a broad search "
          "confined to the information-technology category so that unrelated occupations never enter the "
          "result set. Each retrieved listing is scanned for required skills, and every requirement is "
          "evaluated against the candidate profile by the hybrid matcher. Listings that yield no "
          "requirements are retained but marked unscorable and ranked beneath every scorable listing. "
          "Figure 7.8 shows the workflow."),
    ("fig", {"key": "job_recommendation", "caption": "Job recommendation retrieval, scoring and ranking workflow",
             "width": 0.95}),

    ("h2", "7.8 Market Demand, Skill Gap and Roadmap Design"),
    ("p", "Market demand is designed as a deduplicate-then-count pipeline (Figure 7.9). Only after "
          "duplication is removed does the denominator become meaningful; the design therefore fixes the "
          "unique-listing count before any skill is counted, and returns that count with every percentage."),
    ("fig", {"key": "market_demand", "caption": "Market demand analysis workflow with two-level deduplication",
             "width": 0.92}),
    ("p", "The gap analysis (Figure 7.10) reuses the demand list as its requirement set: each demanded "
          "skill is evaluated against the candidate profile, bucketed into matched, needs-review or "
          "missing, tagged with a priority band derived from its demand share, and the aggregate is "
          "persisted so that the same analysis can be re-opened without recomputation."),
    ("fig", {"key": "skill_gap", "caption": "Skill gap analysis workflow with priority assignment and persistence",
             "width": 0.92}),
    ("p", "The roadmap (Figure 7.11) is designed to add information without disturbing the analysis: it "
          "delegates to the gap service, orders the residual skills by a four-key deterministic sort, and "
          "then optionally decorates each step with language-model guidance produced under a prompt that "
          "forbids invented resources. The fallback path returns the same ordered steps with an explicit "
          "unavailable marker, so the educational value of the ordering never depends on the model."),
    ("fig", {"key": "roadmap", "caption": "Learning roadmap generation flow with the language-model fallback path",
             "width": 0.92}),

    ("h2", "7.9 Data-Provenance Design for Live and Sample Data"),
    ("p", "Because every downstream number inherits the quality of the listing source, the provider is "
          "designed as a single decision point used by all consumers. Credentials are inspected first; a "
          "live call is attempted only when they are present and non-placeholder; and every outcome — "
          "live success, non-200 response, network exception or absent credentials — is returned with an "
          "explicit flag, a source label and a banner message that names the concrete cause. Figure 7.12 "
          "shows the decision structure, and Figure 7.13 shows how the flag reaches the interface."),
    ("fig", {"key": "data_source", "caption": "Live-versus-sample decision structure inside the job provider",
             "width": 0.92}),

    # =======================================================================
    ("chapter", 8, "METHODOLOGY"),
    ("h2", "8.1 Development Methodology"),
    ("p", "The project followed an incremental, test-first methodology. Each analytical capability was "
          "delivered as an isolated service with an injected-dependency constructor, accompanied by "
          "deterministic tests built on in-memory fixtures before the next capability was layered on top. "
          "This ordering meant that the hybrid matcher could be validated against adversarial examples long "
          "before any user interface existed, and that later stages inherited already-proven components. "
          "The front end was developed against the same contracts, with component tests asserting the "
          "rendering of match badges, skill chips and the sample-data banner."),

    ("h2", "8.2 Document Text Recovery Method"),
    ("p", "For PDF input the document is opened with PyMuPDF and each page contributes the string returned "
          "by its text extraction routine; page images are counted separately to support scanned-document "
          "detection. For DOCX input the paragraph collection is read in document order and every table "
          "cell is appended when its text is not already present, which preserves tabular skill matrices "
          "that many resumes use. The concatenated text is then segmented by scanning lines against a "
          "heading vocabulary covering skills, competencies, technologies, experience, education, "
          "projects, certifications, summary and objective; lines before the first recognised heading are "
          "retained under a general section so that no text is discarded."),

    ("h2", "8.3 Taxonomy Construction and Normalisation Method"),
    ("p", "The taxonomy was constructed by enumerating the technologies that recur in entry-level and "
          "mid-level information-technology vacancies and organising them into eleven categories: "
          "programming languages, front end, back end, databases, cloud, DevOps, data science, machine "
          "learning, natural language processing, testing and version control. Each of the fifty-six "
          "canonical entries carries alias spellings, boundary-sensitive patterns and, where the token is "
          "ambiguous, a context requirement listing words that must appear near a hit for it to be "
          "accepted. Normalisation resolves a raw mention through the alias index; if that fails, a "
          "punctuation-insensitive comparison against condensed aliases catches spaced or hyphenated "
          "spellings; and mentions of context-guarded tokens without supporting context are dropped."),

    ("h2", "8.4 Semantic Similarity Method"),
    ("p", "Each skill phrase is embedded by the pre-trained all-MiniLM-L6-v2 encoder. Token embeddings are "
          "mean-pooled under the attention mask and the resulting vector is L2-normalised. Because both "
          "vectors are unit length, the cosine similarity between phrases a and b reduces to their inner "
          "product:"),
    ("eq", "sim(a, b) = E(a) · E(b)  /  ( ‖E(a)‖ · ‖E(b)‖ )  =  E(a) · E(b)", 1),
    ("p", "A candidate phrase is considered semantically related to a requirement when its similarity "
          "reaches the configured threshold, whose default value is zero point six five and which is read "
          "from the environment configuration so that it can be tightened or relaxed without code changes. "
          "Batch comparison of N candidates against M requirements is performed as a single matrix "
          "product of the two embedding matrices."),

    ("h2", "8.5 Hybrid Decision Method"),
    ("p", "The evaluation of one requirement against a candidate profile proceeds through five ordered "
          "stages. Stage one accepts an exact canonical equality and reports similarity one. Stage two "
          "accepts membership of the candidate's raw or canonical text in the requirement's alias list and "
          "reports similarity zero point nine eight. Stage three computes the best semantic score; if it is "
          "below the threshold the evaluation skips to stage five. Stage four validates evidence: the "
          "requirement or one of its aliases must occur as a whole word inside the evidence snippet of the "
          "winning candidate, and a conceptual phrase such as a generic web-service term may not validate a "
          "specific framework requirement. Passing stage four yields a matched verdict carrying the cosine "
          "score; failing it yields needs-review. Stage five assigns needs-review when the best score "
          "exceeds zero point four five, and missing otherwise."),

    ("h2", "8.6 Listing Deduplication Method"),
    ("p", "Two rules are applied in order to each incoming listing and against both the current batch and "
          "the persisted store. Rule one discards a listing whose external identifier has already been "
          "seen. Rule two discards a listing whose content fingerprint has already been seen, where the "
          "fingerprint is the concatenation of the normalised title, company and location:"),
    ("eq", "f = norm(title) | norm(company) | norm(location)", 2),
    ("p", "The normalisation lower-cases the string, removes every non-word character and collapses "
          "whitespace runs, so re-postings that differ only in punctuation or spacing are recognised as "
          "duplicates even when the source assigns them different identifiers."),

    ("h2", "8.7 Market Demand Estimation Method"),
    ("p", "After deduplication, the unique listing set L is fixed and each listing is scanned once. For a "
          "skill s the matching count is the cardinality of the set of listings in which s was extracted, "
          "so repeated mentions inside a single listing cannot inflate the figure. The demand percentage is "
          "then:"),
    ("eq", "D(s) = | { l ∈ L : s ∈ skills(l) } |  /  |L|  × 100", 3),
    ("p", "rounded to two decimal places, with |L| returned alongside. If |L| is zero the analysis reports "
          "an insufficient-data status with an explanatory message instead of emitting percentages over an "
          "empty population. Results are sorted by descending demand and then alphabetically for "
          "stability."),

    ("h2", "8.8 Vacancy Match and Overall Competency Method"),
    ("p", "For a scorable listing j with requirement set R(j), the match percentage is the share of "
          "requirements evaluated as matched:"),
    ("eq", "M(j) = | { r ∈ R(j) : status(r) = matched } |  /  |R(j)|  × 100", 4),
    ("p", "rounded to one decimal place. For a gap analysis against a demanded set S, the overall "
          "competency measure is the share of demanded skills that matched:"),
    ("eq", "O = | { s ∈ S : status(s) = matched } |  /  |S|  × 100", 5),
    ("p", "Priorities are assigned from demand using the project-defined bands: High at seventy percent or "
          "above, Medium from forty to sixty-nine point nine percent, and Low below forty percent. These "
          "bands are declared to be project conventions and are transmitted to the client inside every "
          "response so that they are never mistaken for industry standards."),

    ("h2", "8.9 Roadmap Sequencing Method"),
    ("p", "The residual skills — those classified missing or needing review — are ordered by a "
          "four-component sort key that makes the sequence fully deterministic:"),
    ("eq", "K(s) = ( −D(s),  −count(s),  rank(status),  lower(name) )", 6),
    ("p", "where rank places missing before needs-review on exact ties. Step numbers are then assigned "
          "sequentially from one, so two executions over the same data always produce the same plan. Each "
          "step is independently enriched by the language model when one is configured; a failure, timeout "
          "or missing configuration affects only the explanation fields of that step and never the "
          "ordering."),

    ("h2", "8.10 Fallback and Labelling Method"),
    ("p", "Three independent fallbacks were designed. The provider fallback substitutes filtered fixtures "
          "when credentials are absent or the live call fails, tagging the response as sample data with a "
          "banner that names the cause. The language-model fallback substitutes the literal notice that no "
          "explanation is available, with a boolean flag set to false, whenever the model cannot be reached "
          "or its reply cannot be parsed. The interface fallback renders the warning banner only when the "
          "sample flag is true, and suppresses it entirely for live data. Together these ensure that a "
          "demonstration environment remains fully usable while remaining visibly distinct from a live "
          "deployment."),

    # =======================================================================
    ("chapter", 9, "SYSTEM ARCHITECTURE"),
    ("h2", "9.1 Layered Architecture"),
    ("p", "Figure 9.1 presents the four-layer architecture. The presentation layer is a React single-page "
          "application served by the Vite development server, which also proxies every /api path to the "
          "back end so that the browser never addresses another origin during development. The API layer is "
          "the FastAPI application hosted by Uvicorn, exposing seven route groups plus health endpoints "
          "and applying CORS, bearer-token extraction and Pydantic validation as cross-cutting behaviour. "
          "The service layer contains the twelve services that implement authentication, parsing, "
          "extraction, normalisation, semantic and hybrid matching, listing retrieval, ingestion, demand "
          "analysis, gap analysis and roadmap generation. The bottom layer holds the relational store, the "
          "upload directory, the reference files, the cached encoder weights and the two external "
          "services."),
    ("fig", {"key": "architecture", "caption": "Four-layer architecture of the SkillSync AI portal", "width": 1.0}),

    ("h2", "9.2 Request Lifecycle and Tier Interaction"),
    ("p", "Figure 9.2 traces the interaction between the two tiers for the principal user journey. A stored "
          "session is first revalidated through the identity endpoint and the active-resume endpoint, which "
          "restores the dashboard without re-upload. A new upload is parsed, extracted and persisted in a "
          "single transaction and answered with the provenance-bearing skill list. The three analytical "
          "views then issue their requests, each of which traverses the router, the authentication "
          "dependency, the composed services and the persistence layer before returning a contract-validated "
          "payload."),
    ("fig", {"key": "api_interaction", "caption": "Front-end and back-end interaction sequence for the principal user journey",
             "width": 1.0, "page": True}),

    ("h2", "9.3 Authentication Architecture"),
    ("p", "Authentication is implemented with the OAuth2 password-bearer scheme. Registration hashes the "
          "password with bcrypt before insertion and immediately issues a token; login verifies the hash "
          "and issues a token; every protected route resolves the caller through a dependency that decodes "
          "the token with the configured secret and algorithm, converts the subject claim to a user "
          "identifier, loads the user and confirms that the account is active. Figure 9.3 shows the "
          "complete sequence including the failure semantics."),
    ("fig", {"key": "jwt_sequence", "caption": "JSON Web Token issuance and validation sequence", "width": 1.0, "page": True}),

    ("h2", "9.4 Configuration Architecture"),
    ("p", "All deployment variation is expressed through environment variables consumed by a single "
          "settings object. The object validates and normalises the CORS origin list, selects the database "
          "dialect from the connection string, and exposes the JWT, Adzuna, semantic-model, language-model "
          "and upload parameters with documented defaults. Because services read the settings object rather "
          "than the environment directly, tests can monkey-patch individual values — for example to force "
          "the fixture path — without touching process state."),
    ("table", {
        "caption": "Principal configuration variables and their defaults",
        "headers": ["Variable", "Default", "Effect"],
        "rows": [
            ["DATABASE_URL", "sqlite:///./skillsync.db", "Selects SQLite or PostgreSQL and the pooling behaviour"],
            ["JWT_SECRET / JWT_ALGORITHM", "development secret / HS256", "Signing key and algorithm for access tokens"],
            ["ACCESS_TOKEN_EXPIRE_MINUTES", "60", "Token lifetime"],
            ["CORS_ORIGINS", "localhost:5173 and 127.0.0.1:5173", "Permitted browser origins"],
            ["ADZUNA_APP_ID / ADZUNA_APP_KEY / ADZUNA_COUNTRY", "empty / empty / us", "Live market data credentials and default country"],
            ["SEMANTIC_MODEL_NAME", "all-MiniLM-L6-v2", "Sentence encoder identifier"],
            ["SEMANTIC_SIMILARITY_THRESHOLD", "0.65", "Cosine cut-off for the semantic stage"],
            ["LLM_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY", "empty", "Optional roadmap explanation provider"],
            ["LLM_TIMEOUT_SECONDS", "8.0", "Hard limit for a language-model call"],
            ["UPLOAD_DIR / MAX_UPLOAD_SIZE_MB", "./uploads/resumes / 5", "Resume storage location and size cap"],
        ],
        "widths": [0.34, 0.26, 0.40],
    }),

    ("h2", "9.5 Runtime Topology"),
    ("table", {
        "caption": "Processes and addresses of a development deployment",
        "headers": ["Process", "Command", "Address", "Purpose"],
        "rows": [
            ["Back end", "uvicorn app.main:app", "http://127.0.0.1:8000", "REST API, OpenAPI docs at /docs"],
            ["Front end", "npm run dev (Vite)", "http://127.0.0.1:5173", "Single-page application; proxies /api to the back end"],
            ["Database", "embedded (SQLite) or server (PostgreSQL)", "file or 5432", "Relational store"],
            ["Encoder", "in-process singleton", "n/a", "Loaded once inside the back-end process at start-up"],
        ],
        "widths": [0.14, 0.30, 0.26, 0.30],
    }),

    # =======================================================================
    ("chapter", 10, "DATABASE DESIGN"),
    ("h2", "10.1 Persistence Strategy"),
    ("p", "The relational schema is expressed as SQLAlchemy declarative models and evolved through Alembic "
          "migrations, so the same code base targets the embedded SQLite database used during development "
          "and a PostgreSQL server used in production. Connection arguments are chosen per dialect: SQLite "
          "receives the thread-sharing flag required by a multi-threaded server, while PostgreSQL receives "
          "a pooled configuration with pre-ping health checks. Every table carries creation and update "
          "timestamps, and every child collection is declared with cascade deletion so that ownership "
          "removal is complete."),

    ("h2", "10.2 Entity-Relationship Model"),
    ("p", "Figure 10.1 shows the six entities and their relationships. A user owns many resumes and many "
          "gap analyses; a resume owns many extracted skills and many gap analyses; and a job listing owns "
          "many job skills. The gap analysis therefore sits at the intersection of user and resume, "
          "recording the target role, the analysed population, the provenance of the data and the complete "
          "result document."),
    ("fig", {"key": "er", "caption": "Entity-relationship diagram of the SkillSync AI schema", "width": 1.0, "page": True}),

    ("h2", "10.3 Table Specifications"),
    ("table", {
        "caption": "users — authenticated accounts",
        "headers": ["Column", "Type", "Constraints and notes"],
        "rows": [
            ["id", "INTEGER", "Primary key, auto-increment"],
            ["email", "VARCHAR(255)", "Unique, indexed, stored lower-cased and trimmed"],
            ["hashed_password", "VARCHAR(255)", "bcrypt digest; plain password never stored"],
            ["full_name", "VARCHAR(255)", "Nullable display name"],
            ["is_active", "BOOLEAN", "Inactive accounts are refused at token resolution"],
            ["is_superuser", "BOOLEAN", "Reserved privilege flag used by ownership checks"],
            ["created_at / updated_at", "TIMESTAMPTZ", "Managed automatically"],
        ],
        "widths": [0.26, 0.20, 0.54],
    }),
    ("table", {
        "caption": "resumes — uploaded documents and recovered text",
        "headers": ["Column", "Type", "Constraints and notes"],
        "rows": [
            ["id", "INTEGER", "Primary key"],
            ["user_id", "INTEGER", "Foreign key to users.id, cascade delete, indexed"],
            ["filename / file_path", "VARCHAR(255) / VARCHAR(512)", "Original name and on-disk path with UUID prefix"],
            ["file_size_bytes / file_type", "INTEGER / VARCHAR(50)", "Nullable size and extension"],
            ["raw_text", "TEXT", "Full recovered text used for re-extraction"],
            ["parsed_json", "TEXT", "Serialised section segmentation"],
            ["is_active", "BOOLEAN", "Indexed; exactly one true row per user is maintained"],
            ["created_at / updated_at", "TIMESTAMPTZ", "Used to order the history list"],
        ],
        "widths": [0.26, 0.24, 0.50],
    }),
    ("table", {
        "caption": "extracted_skills — provenance-bearing skill records",
        "headers": ["Column", "Type", "Constraints and notes"],
        "rows": [
            ["id", "INTEGER", "Primary key"],
            ["resume_id", "INTEGER", "Foreign key to resumes.id, cascade delete, indexed"],
            ["skill_name", "VARCHAR(100)", "The matched surface text, indexed"],
            ["canonical_name", "VARCHAR(100)", "Taxonomy canonical owner, indexed"],
            ["confidence_score", "FLOAT", "1.00 exact, 0.95 alias, 0.90 context, plus section bonus"],
            ["category", "VARCHAR(100)", "Taxonomy category of the canonical skill"],
            ["years_experience", "FLOAT", "Reserved for future duration extraction"],
            ["created_at", "TIMESTAMPTZ", "Insertion time"],
        ],
        "widths": [0.26, 0.20, 0.54],
    }),
    ("table", {
        "caption": "job_listings and job_skills — market corpus",
        "headers": ["Column", "Type", "Constraints and notes"],
        "rows": [
            ["id", "INTEGER", "Primary key of job_listings"],
            ["external_id", "VARCHAR(255)", "Unique, indexed; first deduplication key"],
            ["title / company", "VARCHAR(255)", "Indexed; inputs of the content fingerprint"],
            ["location / country", "VARCHAR(255) / VARCHAR(50)", "Geographic attributes"],
            ["description", "TEXT", "Scanned for required skills"],
            ["salary_min / salary_max", "FLOAT", "Nullable; formatted for display"],
            ["url / source / posted_at", "VARCHAR(1024) / VARCHAR(100) / TIMESTAMPTZ", "Provenance of the listing"],
            ["job_skills.skill_name / canonical_name", "VARCHAR(100)", "Indexed requirement tokens"],
            ["job_skills.importance_weight", "FLOAT", "Confidence carried from extraction"],
            ["job_skills (job_listing_id, skill_name)", "—", "Composite unique constraint uq_job_listing_skill"],
        ],
        "widths": [0.34, 0.26, 0.40],
    }),
    ("table", {
        "caption": "skill_gap_analyses — persisted analyses",
        "headers": ["Column", "Type", "Constraints and notes"],
        "rows": [
            ["id", "INTEGER", "Primary key, used to re-open an analysis"],
            ["user_id / resume_id", "INTEGER", "Foreign keys to users.id and resumes.id, cascade"],
            ["target_role / target_location", "VARCHAR(255)", "Analysis parameters, role indexed"],
            ["total_listings_analyzed", "INTEGER", "The denominator behind every percentage"],
            ["data_source", "VARCHAR(100)", "Adzuna Live API or Adzuna Sample Fixtures"],
            ["is_sample_data", "BOOLEAN", "Provenance flag mirrored to the interface"],
            ["results_json", "TEXT", "Complete result document including matched, missing and review lists"],
            ["created_at", "TIMESTAMPTZ", "Analysis timestamp"],
        ],
        "widths": [0.30, 0.18, 0.52],
    }),

    ("h2", "10.4 Indexing and Integrity Decisions"),
    ("bullets", [
        "Unique indexes on users.email and job_listings.external_id enforce identity and the first "
        "deduplication rule at the database level.",
        "A composite unique constraint on (job_listing_id, skill_name) prevents a listing from accumulating "
        "duplicate requirement rows.",
        "Indexes on the foreign keys and on is_active support the ownership filters and the active-resume "
        "lookup that every analytical request performs.",
        "Cascade deletion is declared both in the schema and in the ORM relationships, so a removed user "
        "leaves no orphan resumes, skills or analyses.",
        "The complete gap result is stored as a JSON document rather than normalised child tables, because "
        "it is written once and read whole; the scalar columns that users filter or sort by are promoted to "
        "real columns.",
    ]),

    ("h2", "10.5 Migration History"),
    ("table", {
        "caption": "Alembic migration revisions applied to build the schema",
        "headers": ["Revision", "Purpose"],
        "rows": [
            ["2e81ce75033c", "Creates users, resumes, extracted_skills, job_listings and job_skills with indexes and constraints"],
            ["8a3c9e12b4f1", "Adds the resumes.is_active column supporting non-destructive resume history"],
            ["dd4ee4ad6d27", "Adds the skill_gap_analyses table for persisted gap results"],
        ],
        "widths": [0.24, 0.76],
    }),
]
