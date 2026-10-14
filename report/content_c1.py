"""Report body content — Chapters 1 to 5.

All technical statements in this module were derived from the SkillSync AI
source tree (backend/app and frontend/src) so that the report describes the
implemented system rather than an idealised version of it.
"""

CH1_5 = [
    # =======================================================================
    ("chapter", 1, "INTRODUCTION"),
    ("h2", "1.1 Background of the Study"),
    ("p", "The information technology labour market expands and re-composes itself faster than any "
          "academic curriculum can be revised. Frameworks, cloud services and tooling that were peripheral "
          "five years ago are now listed as mandatory requirements in a large share of entry-level "
          "vacancies, while several technologies that still appear in university syllabi have receded from "
          "industrial practice. A graduating student therefore faces a dual uncertainty: it is difficult to "
          "know which competencies the market currently rewards, and it is equally difficult to measure the "
          "distance between the competencies one already possesses and the competencies a target role "
          "demands. Career guidance in most institutions remains conversational and qualitative, and "
          "commercial job portals optimise for listing volume rather than for the developmental needs of "
          "the candidate."),
    ("p", "At the same time, the technical ingredients required to close this gap have matured considerably. "
          "Lightweight transformer encoders make sentence-level semantic comparison inexpensive enough to run "
          "on an ordinary development machine; public job-search application programming interfaces expose "
          "structured vacancy data at scale [25]; and modern asynchronous web frameworks allow a small team to "
          "serve a machine-learning pipeline behind a conventional REST interface [15]. SkillSync AI is a mini "
          "project that assembles these ingredients into a single coherent portal: it reads a candidate "
          "resume, understands the skills written in it, compares them with the skills that current "
          "vacancies actually request, and converts the difference into an ordered, market-justified "
          "learning plan."),
    ("p", "The application is deliberately built around evidence. Every skill reported to the user is "
          "accompanied by the fragment of the resume from which it was read; every market percentage is "
          "returned together with the number of unique vacancies that produced it; and every figure derived "
          "from offline demonstration data is labelled as such in the application interface. This design "
          "stance, carried through the entire implementation, is what distinguishes the portal from systems "
          "that present algorithmic output as though it were verified truth."),

    ("h2", "1.2 Motivation"),
    ("p", "Three observations motivated the project. First, students routinely prepare for interviews using "
          "syllabus-derived checklists that bear little relation to vacancy descriptions, so preparation "
          "effort is frequently spent on low-demand topics. Second, keyword-only matching, as used by many "
          "applicant tracking systems, rejects candidates whose resumes express a competency with different "
          "wording, and it also promotes candidates whose resumes merely mention a technology without "
          "demonstrating it. Third, freely available market data is voluminous but unstructured; converting "
          "it into a comparable, per-skill demand signal requires careful deduplication and normalisation "
          "that most student-level tools omit entirely."),
    ("p", "SkillSync AI responds to each observation with a concrete mechanism. Market grounding is obtained "
          "by analysing unique vacancy listings and reporting the proportion of them that mention each "
          "skill. Wording sensitivity is addressed by combining a controlled skill taxonomy with alias "
          "normalisation and a sentence-embedding similarity stage. Over-claiming is suppressed by an "
          "evidence-validation rule that refuses to accept semantic similarity alone as proof of a "
          "competency. Together these mechanisms form the analytical core of the portal."),

    ("h2", "1.3 Scope of the Project"),
    ("p", "The project covers the full path from an uploaded resume document to a rendered learning "
          "roadmap. In concrete terms the implemented scope comprises: authenticated user accounts; "
          "upload, parsing and history management of PDF and DOCX resumes; taxonomy-driven skill extraction "
          "with alias normalisation and evidence provenance; semantic similarity matching with a "
          "pre-trained MiniLM encoder; retrieval of job listings from the Adzuna job-search API together "
          "with a clearly labelled offline fixture fallback; hybrid scoring and ranking of vacancies "
          "against a candidate profile; per-skill market demand percentages computed over deduplicated "
          "listings; role-oriented skill-gap analysis with demand-derived priorities; and deterministic "
          "generation of a sequenced learning roadmap with optional language-model explanations."),
    ("p", "The project does not attempt to train any machine-learning model, does not perform optical "
          "character recognition on scanned documents, does not crawl job boards directly, and does not "
          "maintain a live course catalogue. These exclusions are intentional: they keep the mini project "
          "within a verifiable boundary in which every displayed number can be traced to a computation in "
          "the source code."),

    ("h2", "1.4 Organisation of the Report"),
    ("p", "The remainder of the report is organised as follows. Chapter 2 surveys the literature on resume "
          "parsing, recruitment recommendation, semantic similarity and labour-market analytics, and "
          "identifies the gap that the project addresses. Chapter 3 states the problem formally and Chapter "
          "4 enumerates the objectives together with their traceability to implemented features. Chapter 5 "
          "contrasts existing approaches with the proposed system. Chapter 6 analyses functional and "
          "non-functional requirements. Chapter 7 presents the system design, including data-flow and "
          "workflow diagrams. Chapter 8 describes the methodology adopted for each analytical stage. "
          "Chapter 9 details the system architecture, Chapter 10 the database design, and Chapter 11 the "
          "implementation of both tiers. Chapter 12 documents the testing strategy and test cases, Chapter "
          "13 discusses the results obtained during validation, and Chapters 14 and 15 conclude the report "
          "and outline future enhancements."),

    # =======================================================================
    ("chapter", 2, "LITERATURE SURVEY"),
    ("h2", "2.1 Overview"),
    ("p", "The proposed portal sits at the intersection of four research and engineering streams: automated "
          "parsing of curriculum vitae documents, recommender systems applied to recruitment, semantic "
          "textual similarity using dense sentence embeddings, and labour-market intelligence derived from "
          "vacancy corpora [9]. This chapter reviews representative work in each stream, compares the approaches "
          "in a summary table, and isolates the specific deficiency that SkillSync AI is designed to "
          "remedy."),

    ("h2", "2.2 Automated Resume Parsing and Skill Extraction"),
    ("p", "Early approaches to resume understanding treated the document as a bag of keywords and relied on "
          "string matching against a fixed dictionary. Such systems are inexpensive but brittle: they fail "
          "on abbreviations, on concatenated spellings and on homographs such as the single letter used for "
          "a programming language. Structured extraction pipelines improved on this by first recovering the "
          "document text and then applying section detection and named-entity recognition. Section-aware "
          "parsing materially raises the precision of skill detection because the same token carries a "
          "different meaning inside a skills list than inside narrative prose, which is why the present "
          "implementation records the originating section of every hit [6]. More recent work replaces hand-written dictionaries with sequence-labelling "
          "models, at the cost of requiring annotated resume corpora that are rarely available to small "
          "projects and that drift as technology names change."),
    ("p", "The present project adopts a middle path that is well suited to a mini project: a curated "
          "taxonomy of fifty-six canonical technology skills across eleven categories [7], each with explicit "
          "alias lists and boundary-sensitive regular expressions, combined with section segmentation and a "
          "context-guard stage that rejects ambiguous abbreviations lacking technical context. This yields "
          "deterministic, auditable extraction without any annotated training data, while retaining "
          "provenance in the form of character offsets and evidence snippets."),

    ("h2", "2.3 Recommender Systems in Recruitment"),
    ("p", "Job recommendation has been studied both as a content-based filtering problem and as a "
          "collaborative filtering problem [2]. Content-based systems compare the term profile of a candidate "
          "with the term profile of a vacancy, typically using cosine similarity over tf-idf vectors; they "
          "are transparent and cold-start friendly but ignore wording variation. Collaborative approaches "
          "exploit the behaviour of many applicants and employers and can surface non-obvious matches, yet "
          "they require large interaction logs and offer little explanation, which is unacceptable in a "
          "career-guidance context where a student must understand why a vacancy was suggested. Hybrid "
          "recruiters combine lexical, semantic and behavioural signals, and several industrial systems "
          "rank vacancies by the fraction of stated requirements that a profile satisfies, exactly the "
          "interpretation adopted by the recommendation module of this project."),

    ("h2", "2.4 Semantic Textual Similarity with Sentence Embeddings"),
    ("p", "The release of Sentence-BERT established that a siamese transformer encoder can map sentences "
          "into a space in which cosine distance correlates with human semantic judgement, making "
          "similarity search practical at scale [3]. The encoder family descends from the transformer "
          "architecture [10] and its bidirectional pre-training [11]; the all-MiniLM-L6-v2 configuration "
          "[4], distributed through the sentence-transformers library [26] and the public model hub [27], "
          "offers a favourable accuracy-to-cost ratio, producing three-hundred-and-"
          "eighty-four dimensional embeddings from a six-layer transformer [5]. Subsequent studies applied such "
          "encoders to skill normalisation, to occupation matching against taxonomies such as ESCO [8], and to "
          "resume-to-job similarity ranking. A recurring caution in this literature is that high embedding "
          "similarity between two phrases does not entail that a person claiming one phrase possesses the "
          "other competency; relatedness and possession are different relations. The hybrid matcher of this "
          "project operationalises that caution as an explicit evidence-validation stage."),

    ("h2", "2.5 Skill-Gap Analysis and Labour-Market Intelligence"),
    ("p", "Labour-market analytics research treats vacancy postings as a sensor network for skill demand. "
          "Standard practice is to parse postings, map free-text mentions onto a controlled vocabulary [7], and "
          "report the frequency of each skill, often as a share of the analysed postings. Two "
          "methodological hazards are repeatedly noted. The first is duplication: the same vacancy appears "
          "through several channels or is re-posted, inflating frequencies unless listings are deduplicated "
          "by identifier and by content fingerprint. The second is denominator opacity: a percentage "
          "reported without the population it was computed over cannot be interpreted or reproduced. "
          "Skill-gap tools then subtract the candidate profile from the demand profile and prioritise the "
          "residual; several authors weight the residual by market frequency so that learning effort "
          "follows employment relevance, which is precisely the ordering rule implemented in the roadmap "
          "generator of this project."),

    ("h2", "2.6 Application Frameworks for Data-Intensive Portals"),
    ("p", "On the engineering side, asynchronous Python frameworks such as FastAPI [15] provide automatic request "
          "and response validation through Pydantic models, dependency injection for cross-cutting concerns "
          "such as authentication, and machine-readable OpenAPI documentation at no extra cost. On the "
          "client side, component-based libraries such as React [19], combined with a server-state cache such as "
          "TanStack Query [20], allow a portal whose data changes with every analysis run to remain responsive "
          "without manual cache invalidation logic. Material UI [21] supplies an accessible, themeable component "
          "set that shortens the interface development cycle. These choices are adopted throughout the "
          "implementation described in later chapters."),

    ("h2", "2.7 Comparative Summary of Surveyed Approaches"),
    ("table", {
        "caption": "Comparison of approaches reviewed in the literature survey",
        "headers": ["Approach family", "Representative idea", "Strength", "Limitation addressed by this project"],
        "rows": [
            ["Keyword dictionary matching", "String search of resume text against a fixed term list",
             "Simple and fast", "Fails on aliases and homographs; no provenance"],
            ["Section-aware NER extraction", "Detect resume sections, then label skill entities",
             "Higher precision", "Needs annotated corpora that drift over time"],
            ["Collaborative filtering", "Rank by behaviour of similar users",
             "Captures latent preference", "Cold start; no explanation for the candidate"],
            ["Content-based tf-idf ranking", "Cosine similarity of term vectors",
             "Transparent scoring", "Insensitive to paraphrase and synonyms"],
            ["Sentence-embedding similarity", "Cosine similarity of dense vectors",
             "Robust to wording variation", "Relatedness mistaken for possession of a skill"],
            ["Vacancy frequency analytics", "Skill share across parsed postings",
             "Market-grounded priorities", "Inflated by duplicates; opaque denominators"],
            ["Proposed hybrid pipeline", "Taxonomy + alias + semantic + evidence stages, deduplicated demand",
             "Auditable, market-grounded, evidence-backed", "Not applicable — this project"],
        ],
        "widths": [0.20, 0.26, 0.20, 0.34],
    }),

    ("h2", "2.8 Research Gap"),
    ("p", "The surveyed systems each solve one fragment of the problem. Parsing research does not connect "
          "extracted skills to live market demand; recommendation research rarely explains a match in terms "
          "a student can verify; embedding-based matchers do not guard against treating relatedness as "
          "competence; and market analytics tools seldom expose the denominator or the deduplication rules "
          "behind their percentages. No reviewed student-scale system combines all four concerns behind a "
          "single authenticated portal with explicit labelling of offline demonstration data. SkillSync AI "
          "is positioned exactly in this gap."),

    # =======================================================================
    ("chapter", 3, "PROBLEM STATEMENT"),
    ("h2", "3.1 The Problem"),
    ("p", "A student or early-career job seeker possesses a resume document and a target role, but has no "
          "reliable, verifiable means of answering three questions: which of the skills demanded by the "
          "current market for that role does the resume already demonstrate; which demanded skills are "
          "absent or unproven; and in what order should the absent skills be learned so that effort is "
          "spent where employment return is greatest. Manual answers to these questions are slow and "
          "anecdotal, while automated answers offered by existing tools are typically unexplained, "
          "untraceable to the source document, or computed over duplicated and unlabelled vacancy data."),

    ("h2", "3.2 Formal Statement"),
    ("p", "Let R be the text recovered from a candidate resume document, T a controlled skill taxonomy, L a "
          "set of unique vacancy listings relevant to a target role, and D(s) the share of listings in L "
          "that mention skill s. The problem is to compute, for each demanded skill s, a status in "
          "{matched, needs review, missing} justified by evidence drawn from R, to aggregate these statuses "
          "into an overall competency measure, and to produce a total order over the non-matched skills "
          "that is monotonic in D(s). The computation must remain interpretable: every status must cite the "
          "evidence or the similarity score that produced it, and every D(s) must be reported together with "
          "|L|."),

    ("h2", "3.3 Key Challenges"),
    ("bullets", [
        "Resume documents arrive in heterogeneous layouts; text recovery must detect empty, corrupt and "
        "scanned image-only files and explain the rejection rather than fail silently.",
        "Technology names appear as abbreviations, concatenations and brand variants, so surface forms must "
        "be normalised onto canonical skills without introducing false positives from ambiguous tokens.",
        "Semantic similarity alone cannot distinguish a related concept from a possessed competency, so a "
        "guard is required between a high similarity score and a positive match verdict.",
        "Vacancy feeds contain re-posted and mirrored listings; demand percentages computed without "
        "deduplication are inflated and misleading.",
        "External job APIs may be unconfigured, rate limited or unreachable; the system must degrade to "
        "clearly labelled offline data without ever presenting it as live market data.",
        "Optional language-model assistance must never block the response nor fabricate courses, URLs or "
        "certifications when the model is unavailable.",
    ]),

    # =======================================================================
    ("chapter", 4, "OBJECTIVES"),
    ("h2", "4.1 Primary Objective"),
    ("p", "The primary objective of the project is to design and implement an AI-driven employment and "
          "skill-matching portal, named SkillSync AI, that converts a candidate resume into a personalised, "
          "market-grounded view of employability: extracted and evidenced skills, ranked vacancy "
          "recommendations, quantified skill gaps against a target role, and a demand-ordered learning "
          "roadmap."),

    ("h2", "4.2 Specific Objectives"),
    ("nums", [
        "To implement secure registration and login with JSON Web Token based session handling and "
        "user-scoped data protection.",
        "To implement resume ingestion for PDF and DOCX documents with robust text recovery, scanned-file "
        "detection, section segmentation and non-destructive resume history.",
        "To extract technical skills through a controlled taxonomy with alias normalisation, context "
        "guards, confidence scores and evidence snippets carrying character-level positions.",
        "To add a semantic matching stage based on the pre-trained all-MiniLM-L6-v2 sentence encoder with a "
        "configurable cosine similarity threshold and an evidence-validation guard.",
        "To retrieve vacancy listings from the Adzuna job-search API when credentials are configured, and to "
        "fall back transparently to clearly labelled offline fixtures otherwise.",
        "To score and rank vacancies against the candidate profile using hybrid matching, reporting matched "
        "and missing skills and a match percentage for every scorable listing.",
        "To compute per-skill market demand as the share of unique analysed listings, with two-level "
        "deduplication and an always-present denominator.",
        "To perform role-oriented skill-gap analysis that classifies demanded skills as matched, missing or "
        "needing review, assigns demand-derived priorities and persists the analysis for later retrieval.",
        "To generate a deterministic learning roadmap that orders the residual skills by market demand and "
        "enriches each step with optional, safely-degrading language-model guidance.",
        "To present all of the above through a responsive React interface that visibly distinguishes live "
        "market data from sample data.",
    ]),

    ("h2", "4.3 Traceability of Objectives to Implemented Modules"),
    ("table", {
        "caption": "Mapping of specific objectives to implemented system modules",
        "headers": ["Objective", "Implemented module", "Principal artefacts"],
        "rows": [
            ["1", "core.security, api.deps, services.auth_service", "bcrypt hashing; HS256 tokens; get_current_user dependency"],
            ["2", "services.resume_parser, repositories.resume_repository", "PyMuPDF and python-docx extraction; is_active history"],
            ["3", "services.skill_extractor, services.skill_normalizer, taxonomy/skills.json", "56-skill taxonomy; alias index; evidence snippets"],
            ["4", "services.semantic_matcher, services.hybrid_matcher", "MiniLM embeddings; five-stage decision pipeline"],
            ["5", "services.job_provider_adzuna, taxonomy/sample_jobs.json", "live Adzuna client; labelled fixture fallback"],
            ["6", "services.job_matcher, routes.jobs", "match percentage; ranking; matched and missing chips"],
            ["7", "services.job_ingestion, services.market_demand_service", "external-id and fingerprint deduplication; demand share"],
            ["8", "services.skill_gap_service, models.skill_gap", "priority bands; persisted SkillGapAnalysis rows"],
            ["9", "services.roadmap_service", "demand-ordered steps; LLM guidance with safe fallback"],
            ["10", "frontend pages and SampleDataBanner", "tabs, cards, steppers and the sample-data warning"],
        ],
        "widths": [0.10, 0.40, 0.50],
    }),

    # =======================================================================
    ("chapter", 5, "EXISTING SYSTEM AND PROPOSED SYSTEM"),
    ("h2", "5.1 The Existing System"),
    ("p", "In the prevailing practice, a student seeking direction relies on three instruments. The first is "
          "the general-purpose job board, which returns listings for a keyword query in recency or "
          "sponsorship order and offers no comparison between the listing requirements and the student "
          "profile. The second is the applicant tracking system used by employers, which performs keyword "
          "screening optimised for rejection rather than for guidance and gives the rejected candidate no "
          "feedback. The third is informal mentorship, in which a senior practitioner compares the resume "
          "against personal experience of the market; this advice is valuable but unrepeatable, "
          "unscalable and frequently stale."),

    ("h2", "5.2 Limitations of the Existing System"),
    ("bullets", [
        "Keyword screening treats wording variation as absence of a skill, penalising well-qualified "
        "candidates who phrase a competency differently.",
        "Job boards present listings without relating them to the candidate, so the student must mentally "
        "diff every description against their own resume.",
        "No feedback loop exists: a rejected applicant learns neither which requirement failed nor how "
        "important that requirement is in the wider market.",
        "Market intuition obtained from mentors decays quickly and cannot be audited or reproduced.",
        "None of the three instruments quantify demand, so learning priorities are set by anecdote rather "
        "than by measured vacancy frequency.",
    ]),

    ("h2", "5.3 The Proposed System"),
    ("p", "SkillSync AI replaces the anecdotal loop with a measured one. The candidate uploads a resume "
          "once; the portal recovers its text, segments it into sections and extracts canonical skills "
          "together with the sentence that evidenced each one. When the candidate names a target role, the "
          "portal analyses unique vacancies for that role, computes how frequently each skill appears, and "
          "evaluates every demanded skill against the candidate profile through the five-stage hybrid "
          "matcher. The outcome is presented in three coordinated views: ranked vacancy recommendations "
          "with matched and missing skill chips, a gap report with demand-derived priorities and an overall "
          "competency percentage, and a sequential learning roadmap whose ordering follows measured market "
          "demand. Whenever the market data originates from offline fixtures rather than the live API, a "
          "persistent banner states so, preserving the honesty of every downstream number."),

    ("h2", "5.4 Advantages of the Proposed System"),
    ("bullets", [
        "Wording tolerance: alias normalisation and semantic similarity let 'JS', 'ECMAScript' or "
        "'ReactJS' satisfy the corresponding canonical requirement.",
        "Evidence discipline: a similarity score alone never yields a match; the validating sentence must "
        "contain the required technology or one of its aliases.",
        "Market grounding: priorities and roadmap order derive from measured demand over deduplicated "
        "listings, with the denominator always displayed.",
        "Traceability: extracted skills carry character offsets and snippets, and gap analyses are "
        "persisted so any earlier result can be re-opened.",
        "Graceful degradation: missing Adzuna credentials, API failures and LLM outages each produce a "
        "clearly labelled, non-blocking fallback instead of an error page or a fabricated answer.",
        "User isolation: every resume and analysis is scoped to its owner and protected by bearer-token "
        "authentication.",
    ]),

    ("h2", "5.5 Feasibility Study"),
    ("h3", "5.5.1 Technical Feasibility"),
    ("p", "All required capabilities are available as mature open-source components: FastAPI and Uvicorn "
          "for the asynchronous service tier, SQLAlchemy with Alembic for persistence, PyMuPDF and "
          "python-docx for document text recovery, the Hugging Face Transformers library for the MiniLM "
          "encoder, and React with Material UI and TanStack Query for the interface. The encoder is small "
          "enough to run on CPU within acceptable latency, and it is loaded once at process start-up, so no "
          "specialised hardware is needed."),
    ("h3", "5.5.2 Operational Feasibility"),
    ("p", "The portal is operated as two conventional processes, a Uvicorn server and a Vite development "
          "server, configured entirely through environment variables. An operator can switch databases, "
          "enable live market data or enable language-model guidance by editing a single configuration "
          "file, and every degraded mode is self-announcing in the user interface, which keeps operational "
          "risk low."),
    ("h3", "5.5.3 Economic and Schedule Feasibility"),
    ("p", "The project uses only free-tier external services and open-source software, so its marginal cost "
          "is limited to development time. The modular service layout allowed the analytical stages to be "
          "built and tested independently in sequence, which fitted the mini-project schedule without "
          "parallel staffing."),
]
