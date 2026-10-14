"""Diagrams B: semantic embedding pipeline, hybrid matcher, job recommendation,
market demand, skill gap analysis, learning roadmap and data-source fallback."""

from dstyle import arrow, box, diamond, elbow, new_ax, note, rect, save, store, COLORS


# ---------------------------------------------------------------------------
# Figure: sentence-embedding pipeline used for semantic matching
# ---------------------------------------------------------------------------
def fig_semantic_embedding():
    fig, ax = new_ax(12.0, 4.4)
    ys, h = 24.0, 20.0
    w, gap = 15.4, 1.4
    x0 = 2.0
    items = [
        ("Skill phrases taken from the\nresume and from job\nrequirements, e.g. 'React',\n'ReactJS', 'built REST APIs'", "start"),
        ("AutoTokenizer from\nsentence-transformers/\nall-MiniLM-L6-v2 with padding\nand truncation at 128 tokens", "ai"),
        ("Transformer encoder forward\npass under torch.no_grad();\nthe model is a process-level\nsingleton warmed at start-up", "ai"),
        ("Mean pooling of token\nembeddings weighted by the\nattention mask yields one\n384-dimensional vector per text", "ai"),
        ("L2 normalisation of every\nvector (F.normalize, p=2) so\nthat a dot product equals the\ncosine similarity", "ai"),
        ("batch_compare() returns the\n[N, M] cosine matrix in one\nmatmul; vectors are cached per\nstring to skip re-encoding", "data"),
    ]
    for i, (label, kind) in enumerate(items):
        cx = x0 + w / 2 + i * (w + gap)
        box(ax, cx, ys, w, h, label, kind=kind, fs=6.5)
        if i:
            arrow(ax, (cx - w / 2 - gap, ys), (cx - w / 2, ys), ms=9)
    note(ax, 50.0, 7.0, 96.0, 7.5,
         "Cosine similarity between two normalised embeddings is their dot product, so a score of 1.0 means identical direction. The threshold "
         "SEMANTIC_SIMILARITY_THRESHOLD (default 0.65, configurable in .env) decides when a semantic hit is strong enough to proceed to evidence "
         "validation. Embeddings are cached in an in-memory dictionary keyed by the cleaned string.",
         fs=7.0)
    return save(fig, "fig_semantic_embedding.png")


# ---------------------------------------------------------------------------
# Figure: five-stage hybrid matching pipeline
# ---------------------------------------------------------------------------
def fig_hybrid_matcher():
    fig, ax = new_ax(11.6, 8.0)
    MX, MW = 40.0, 46.0
    OX, OW = 83.0, 28.0

    box(ax, MX, 62.0, MW, 5.0,
        "INPUT — one required skill (from a job listing or from market demand) evaluated\nagainst the candidate skill records extracted from the active resume",
        kind="start", fs=7.2, bold=True)
    arrow(ax, (MX, 59.5), (MX, 57.5))

    box(ax, MX, 55.0, MW, 5.0,
        "STAGE 1 — exact canonical match: a candidate canonical_name equals the required\ncanonical name, case-insensitively", kind="service", fs=7.2)
    box(ax, OX, 55.0, OW, 5.0,
        "matched · method 'exact'\nsimilarity 1.00 and the stored\nevidence snippet are returned", kind="api", fs=6.9)
    arrow(ax, (MX + MW / 2, 55.0), (OX - OW / 2, 55.0))
    arrow(ax, (MX, 52.5), (MX, 50.5), label="no exact match", fs=6.8)

    box(ax, MX, 48.0, MW, 5.0,
        "STAGE 2 — alias match: the candidate's matched_text or canonical name appears in\nthe required skill's alias list in skills.json", kind="service", fs=7.2)
    box(ax, OX, 48.0, OW, 5.0,
        "matched · method 'alias'\nsimilarity 0.98, e.g. 'JS' or\n'ECMAScript' satisfying JavaScript", kind="api", fs=6.9)
    arrow(ax, (MX + MW / 2, 48.0), (OX - OW / 2, 48.0))
    arrow(ax, (MX, 45.5), (MX, 43.75), label="no alias match", fs=6.8)

    box(ax, MX, 40.5, MW, 6.5,
        "STAGE 3 — semantic comparison: batch_compare() scores every candidate text against\nthe required skill and the best cosine score is kept; is that score at least\nSEMANTIC_SIMILARITY_THRESHOLD (default 0.65) ?", kind="ai", fs=7.2)
    elbow(ax, [(MX - MW / 2, 40.5), (10.0, 40.5), (10.0, 19.0), (MX - MW / 2, 19.0)],
          label="score below threshold", label_at=(10.0, 30.0))
    arrow(ax, (MX, 37.25), (MX, 35.25), label="score at or above threshold", fs=6.8)

    box(ax, MX, 31.0, MW, 8.5,
        "STAGE 4 — evidence validation: the required skill or one of its aliases must literally\noccur inside the evidence snippet of the best candidate. A general phrase such as\n'ReST APIs' may not validate a specific framework requirement such as FastAPI,\nDjango, Flask, Express.js or Spring Boot", kind="ai", fs=7.1)
    box(ax, OX, 32.5, OW, 6.0,
        "matched · method 'semantic'\nreturned with the cosine score\nand the validating sentence", kind="api", fs=6.9)
    arrow(ax, (MX + MW / 2, 32.5), (OX - OW / 2, 32.5), label="validated", fs=6.8)
    box(ax, OX, 25.0, OW, 6.5,
        "needs_review · the similarity met\nthe threshold but the evidence\ndoes not confirm the specific\ntechnology", kind="decision", fs=6.9)
    arrow(ax, (MX + MW / 2, 29.0), (OX - OW / 2, 26.5), label="not validated", fs=6.8, rad=0.06)

    box(ax, MX, 19.0, MW, 8.5,
        "STAGE 5 — otherwise: if the best similarity still exceeds 0.45 the requirement is\nflagged needs_review together with the related candidate skill that produced the\nmoderate score; if no candidate reaches 0.45 the requirement is reported missing",
        kind="service", fs=7.1)
    box(ax, OX, 17.5, OW, 5.0,
        "needs_review · moderate\nsimilarity, manual confirmation\nrequested", kind="decision", fs=6.9)
    arrow(ax, (MX + MW / 2, 20.5), (OX - OW / 2, 18.5), label="best score > 0.45", fs=6.8, rad=0.05)
    box(ax, OX, 10.0, OW, 5.0,
        "missing · method 'none',\nsimilarity 0.00, no candidate\ntext associated", kind="end", fs=6.9)
    arrow(ax, (MX + MW / 2, 16.0), (OX - OW / 2, 11.5), label="otherwise", fs=6.8, rad=0.08)

    note(ax, 36.0, 3.8, 68.0, 5.4,
         "Design invariant implemented in hybrid_matcher.py: a high similarity score alone can never produce a 'matched' verdict — "
         "stage 4 evidence validation must also pass. This prevents the encoder from silently promoting related concepts into claimed competencies.",
         fs=7.0)
    return save(fig, "fig_hybrid_matcher.png")


# ---------------------------------------------------------------------------
# Figure: job recommendation workflow
# ---------------------------------------------------------------------------
def fig_job_recommendation():
    fig, ax = new_ax(11.8, 8.0)
    c1, c2, c3 = 16.0, 49.0, 83.0
    w = 27.0

    box(ax, c1, 60.0, w, 5.5,
        "GET /api/jobs/recommendations with\nresume_id and optional location, limit\nand min_match; Bearer JWT attached", kind="api", fs=6.9)
    box(ax, c1, 52.5, w, 5.0,
        "Ownership verification — the resume\nmust belong to the authenticated user,\notherwise HTTP 403 Forbidden", kind="service", fs=6.9)
    box(ax, c1, 44.5, w, 6.0,
        "Candidate profile assembled from\nresume.extracted_skills; the first five\ncanonical skills become the search seed", kind="service", fs=6.9)
    arrow(ax, (c1, 57.25), (c1, 55.0))
    arrow(ax, (c1, 50.0), (c1, 47.5))
    elbow(ax, [(c1 + w / 2, 44.5), (32.5, 44.5), (32.5, 60.0), (c2 - w / 2, 60.0)])

    box(ax, c2, 60.0, w, 5.0,
        "Strategy A — what_or search with the\nfive seed skills, restricted to the\nit-jobs category", kind="service", fs=6.9)
    diamond(ax, c2, 52.0, 22.0, 5.5, "Listings\nreturned ?", fs=6.9)
    box(ax, c2, 44.5, w, 4.5,
        "Strategy B — what search using only\nthe strongest seed skill", kind="service", fs=6.9)
    diamond(ax, c2, 36.5, 22.0, 5.5, "Listings\nreturned ?", fs=6.9)
    box(ax, c2, 28.5, w, 6.0,
        "Strategy C — broad search still\nrestricted to it-jobs, so unrelated\nnon-technical jobs never appear", kind="service", fs=6.9)
    arrow(ax, (c2, 57.5), (c2, 54.75))
    arrow(ax, (c2, 49.25), (c2, 46.75), label="No", fs=6.8)
    arrow(ax, (c2, 42.25), (c2, 39.25))
    arrow(ax, (c2, 33.75), (c2, 31.5), label="No", fs=6.8)
    elbow(ax, [(c2 + w / 2, 28.5), (66.5, 28.5), (66.5, 60.0), (c3 - w / 2, 60.0)])

    box(ax, c3, 60.0, w, 8.0,
        "For every retrieved listing the\nSkillExtractor scans title + description;\nduplicate canonical requirements are\ncollapsed while order is preserved", kind="service", fs=6.9)
    diamond(ax, c3, 50.5, 22.0, 5.5, "At least one\nrequired skill ?", fs=6.9)
    box(ax, c3, 42.0, w, 7.0,
        "is_scorable = false and\nmatch_percentage = null; the card is\nstill displayed but always ranked\nbelow every scorable listing", kind="note", fs=6.9)
    box(ax, c3, 32.0, w, 7.5,
        "The HybridMatcher evaluates each\nrequirement against the candidate\nprofile, collecting matched_skills and\nmissing_skills lists", kind="ai", fs=6.9)
    box(ax, c3, 21.5, w, 6.5,
        "match_percentage = matched ÷ total\nrequired × 100 rounded to one decimal;\nthe optional min_match filter removes\nweaker listings", kind="service", fs=6.9)
    box(ax, c3, 11.5, w, 7.0,
        "Ranking: scorable listings first by\nmatch percentage descending, unscored\nlistings last; the first 'limit' entries\nare returned", kind="service", fs=6.9)
    box(ax, c3, 3.5, w, 6.0,
        "The response also carries is_sample_data,\nbanner_message and data_source so the\nfront end can raise the SAMPLE DATA\nwarning banner", kind="api", fs=6.9)
    arrow(ax, (c3, 56.0), (c3, 53.25))
    arrow(ax, (c3 + 11.0, 50.5), (c3 + w / 2, 45.5), label="No", fs=6.8, rad=0.05)
    arrow(ax, (c3, 47.75), (c3, 45.75), label="Yes", fs=6.8)
    arrow(ax, (c3, 38.5), (c3, 35.75))
    arrow(ax, (c3, 28.25), (c3, 24.75))
    arrow(ax, (c3, 18.25), (c3, 15.0))
    arrow(ax, (c3, 8.0), (c3, 6.5))

    return save(fig, "fig_job_recommendation.png")


# ---------------------------------------------------------------------------
# Figure: market demand analysis workflow
# ---------------------------------------------------------------------------
def fig_market_demand():
    fig, ax = new_ax(11.2, 7.6)
    MX, MW = 44.0, 54.0
    EX, EW = 86.0, 26.0

    box(ax, MX, 58.0, MW, 4.6,
        "GET /api/market-demand with role, location and limit (1–200) query parameters",
        kind="api", fs=7.3)
    arrow(ax, (MX, 55.7), (MX, 54.4))
    box(ax, MX, 51.5, MW, 5.4,
        "AdzunaJobProvider.search_jobs(query=role, location, results_per_page=limit) returns either\nlive Adzuna listings or the clearly labelled offline fixture set", kind="service", fs=7.2)
    arrow(ax, (MX, 48.8), (MX, 47.4))
    box(ax, MX, 43.5, MW, 6.8,
        "JobIngestionService.deduplicate_job_stream(): rule 1 rejects a repeated external listing id;\nrule 2 rejects a repeated fingerprint built from normalised title, company and location,\nwhere normalisation lower-cases and strips punctuation and extra whitespace", kind="service", fs=7.1)
    arrow(ax, (MX, 40.1), (MX, 38.6))
    diamond(ax, MX, 35.0, 30.0, 6.4, "Does at least one unique\nlisting survive deduplication ?", fs=7.0)
    box(ax, EX, 35.0, EW, 6.4,
        "status = insufficient_data with an\nexplanatory message; top_skills is\nreturned empty and no percentage\nis computed", kind="end", fs=6.8)
    arrow(ax, (MX + 15.0, 35.0), (EX - EW / 2, 35.0), label="No", fs=6.8)
    arrow(ax, (MX, 31.8), (MX, 30.2), label="Yes", fs=6.8)

    box(ax, MX, 26.0, MW, 6.6,
        "Each unique listing's title and description are scanned by the SkillExtractor; every\ncanonical skill found is mapped to the set of listing keys that contain it, so a skill\nrepeated inside one listing is counted only once for that listing", kind="service", fs=7.1)
    arrow(ax, (MX, 22.7), (MX, 21.2))
    box(ax, MX, 17.2, MW, 6.4,
        "demand_percentage = matching_listings_count ÷ total_unique_listings_analyzed × 100,\nrounded to two decimals. The denominator is returned alongside every percentage so\nthat no figure can be read without its population size", kind="ai", fs=7.1)
    arrow(ax, (MX, 14.0), (MX, 12.6))
    box(ax, MX, 9.6, MW, 4.6,
        "Skills are sorted by demand percentage descending and then alphabetically for a stable order",
        kind="service", fs=7.2)
    arrow(ax, (MX, 7.3), (MX, 6.0))
    box(ax, MX, 3.4, MW, 4.6,
        "MarketDemandResponse: total_unique_listings_analyzed, role_filter, location_filter, status,\nis_sample_data, banner_message and the ranked top_skills array", kind="api", fs=7.1)
    return save(fig, "fig_market_demand.png")


# ---------------------------------------------------------------------------
# Figure: skill gap analysis workflow
# ---------------------------------------------------------------------------
def fig_skill_gap():
    fig, ax = new_ax(11.4, 7.8)
    MX, MW = 50.0, 62.0

    box(ax, MX, 60.5, MW, 4.6,
        "POST /api/skill-gap/analyze with {resume_id, target_role, target_location, limit} and a Bearer token",
        kind="api", fs=7.2)
    arrow(ax, (MX, 58.2), (MX, 57.0))
    box(ax, MX, 54.6, MW, 4.4,
        "The resume is loaded and its owner compared with the authenticated user; a mismatch yields HTTP 403",
        kind="service", fs=7.2)
    arrow(ax, (MX, 52.4), (MX, 51.2))
    box(ax, MX, 48.6, MW, 4.8,
        "Candidate skill records (canonical name, matched text, category, evidence) are read from the resume",
        kind="service", fs=7.2)
    arrow(ax, (MX, 46.2), (MX, 45.0))
    box(ax, MX, 41.5, MW, 6.2,
        "MarketDemandService.analyze_market_demand(target_role, target_location, limit) supplies the\nin-demand skill list together with each skill's demand percentage and listing count",
        kind="service", fs=7.2)
    arrow(ax, (MX, 38.4), (MX, 37.0))
    box(ax, MX, 33.0, MW, 6.4,
        "Every demanded skill is evaluated against the candidate profile by the five-stage\nHybridMatcher, producing a status, a method and, where relevant, a similarity score",
        kind="ai", fs=7.2)
    arrow(ax, (MX, 29.8), (MX, 28.4))

    bx = [18.0, 50.0, 82.0]
    labels = [("matched — the candidate's resume\nsupports the demanded skill", "api"),
              ("needs_review — related evidence exists\nbut is not conclusive", "decision"),
              ("missing — no direct, alias or\nvalidated semantic match", "end")]
    for cx, (label, kind) in zip(bx, labels):
        box(ax, cx, 24.5, 28.0, 6.0, label, kind=kind, fs=6.9)
    arrow(ax, (MX - 18.0, 29.8), (18.0, 27.5), rad=-0.06)
    arrow(ax, (MX, 29.8), (50.0, 27.5))
    arrow(ax, (MX + 18.0, 29.8), (82.0, 27.5), rad=0.06)

    box(ax, MX, 15.5, MW, 6.6,
        "Each evaluated skill receives a priority from its market demand percentage —\nHigh at 70 % or above, Medium from 40 % to 69.9 %, Low below 40 %. These are\nproject-defined thresholds and are disclosed as such in every response",
        kind="service", fs=7.1)
    arrow(ax, (18.0, 21.5), (MX - 20.0, 18.0), rad=0.06)
    arrow(ax, (50.0, 21.5), (50.0, 18.8))
    arrow(ax, (82.0, 21.5), (MX + 20.0, 18.0), rad=-0.06)

    box(ax, MX, 7.0, MW, 6.8,
        "overall_match_percentage = matched ÷ total demanded skills × 100. The complete result is\npersisted as a SkillGapAnalysis row carrying results_json, data_source, is_sample_data and\nthe number of listings analysed, then returned with HTTP 201",
        kind="data", fs=7.1)
    arrow(ax, (MX, 12.2), (MX, 10.4))
    return save(fig, "fig_skill_gap.png")


# ---------------------------------------------------------------------------
# Figure: learning roadmap generation flow
# ---------------------------------------------------------------------------
def fig_roadmap():
    fig, ax = new_ax(11.4, 8.0)
    MX, MW = 50.0, 64.0

    box(ax, MX, 62.0, MW, 4.4,
        "GET /api/roadmap with resume_id, target_role and optional target_location and limit",
        kind="api", fs=7.2)
    arrow(ax, (MX, 59.8), (MX, 58.6))
    box(ax, MX, 55.6, MW, 5.4,
        "RoadmapService delegates to SkillGapService. Matching and market demand are never\nrecomputed — the freshly produced gap analysis is reused directly", kind="service", fs=7.2)
    arrow(ax, (MX, 52.9), (MX, 51.6))
    box(ax, MX, 47.2, MW, 7.4,
        "Missing and needs_review skills are merged and ordered deterministically:\n1) demand percentage descending, 2) matching listing count descending,\n3) 'missing' before 'needs_review' on ties, 4) skill name alphabetically",
        kind="service", fs=7.1)
    arrow(ax, (MX, 43.5), (MX, 42.2))
    box(ax, MX, 39.2, MW, 4.6,
        "Each ordered skill is assigned step_number 1..N, forming the learning sequence",
        kind="service", fs=7.2)
    arrow(ax, (MX, 36.9), (MX, 35.6))
    box(ax, MX, 30.6, MW, 8.6,
        "build_skill_prompt() writes a tightly scoped instruction asking the model for exactly three\nthings: a two-to-three sentence explanation, three general resource types (official\ndocumentation, one reputable free platform by name, one practice project) and a single\npractice-project idea. Invented course titles, URLs, instructor names, certifications and\ntime estimates are explicitly forbidden",
        kind="ai", fs=7.0)
    arrow(ax, (MX, 26.3), (MX, 24.8))
    diamond(ax, MX, 20.5, 40.0, 7.4,
            "Is an LLM key configured (GEMINI_API_KEY, OPENAI_API_KEY or LLM_API_KEY)\nand does the call return valid JSON within LLM_TIMEOUT_SECONDS ?", fs=6.9)

    box(ax, 24.0, 10.5, 34.0, 8.0,
        "The JSON reply is parsed after stripping\noptional code fences and validated; the step\ncarries ai_explanation_available = true with\nthe explanation, resource_suggestions and\npractice_project_idea", kind="ai", fs=6.9)
    box(ax, 76.0, 10.5, 34.0, 8.0,
        "The step is still returned with its real demand\npercentage and priority, but with\nai_explanation_available = false and the\nexplanation text 'AI explanation unavailable'.\nNo explanation is ever fabricated", kind="note", fs=6.9)
    arrow(ax, (MX - 20.0, 20.5), (24.0, 14.5), label="Yes", fs=6.9, rad=-0.06)
    arrow(ax, (MX + 20.0, 20.5), (76.0, 14.5), label="No / timeout", fs=6.9, rad=0.06)

    box(ax, MX, 2.8, MW, 5.2,
        "RoadmapResponse returns the ordered steps with demand data and priority, the matched\nskills, the priority thresholds, the resource disclaimer and the sample-data flag; the front\nend renders the sequence as a Material UI vertical stepper", kind="api", fs=7.0)
    arrow(ax, (24.0, 6.5), (MX - 16.0, 4.6), rad=0.05)
    arrow(ax, (76.0, 6.5), (MX + 16.0, 4.6), rad=-0.05)
    return save(fig, "fig_roadmap.png")


# ---------------------------------------------------------------------------
# Figure: live versus sample data fallback
# ---------------------------------------------------------------------------
def fig_data_source():
    fig, ax = new_ax(11.4, 6.6)
    MX = 33.0
    RX = 78.0

    box(ax, MX, 50.0, 46.0, 5.4,
        "A feature requests job listings — job recommendations,\nmarket demand or skill gap analysis", kind="start", fs=7.2, bold=True)
    arrow(ax, (MX, 47.3), (MX, 45.6))
    diamond(ax, MX, 41.0, 34.0, 7.4,
            "Are ADZUNA_APP_ID and ADZUNA_APP_KEY both present\nand different from the placeholder values ?", fs=6.9)
    box(ax, RX, 41.0, 32.0, 7.0,
        "The curated fixtures in sample_jobs.json are filtered by\nrole, what_or tokens and location; is_sample_data = true\nand the banner reads 'SAMPLE DATA — not live'",
        kind="store", fs=6.8)
    arrow(ax, (MX + 17.0, 41.0), (RX - 16.0, 41.0), label="No", fs=6.9)
    arrow(ax, (MX, 37.3), (MX, 35.4), label="Yes", fs=6.9)

    box(ax, MX, 32.0, 46.0, 5.6,
        "HTTPS GET api.adzuna.com/v1/api/jobs/{country}/search/{page}\nwith app_id and app_key, results_per_page capped at 50,\nhttpx client timeout of 8 seconds", kind="ext", fs=7.0)
    arrow(ax, (MX, 29.2), (MX, 27.4))
    diamond(ax, MX, 23.0, 30.0, 6.8, "Did the API answer\nwith HTTP 200 ?", fs=6.9)
    box(ax, RX, 23.0, 32.0, 7.0,
        "The fixtures are served instead and the banner states the\nconcrete cause — the HTTP status code returned, or the\nnetwork exception raised", kind="store", fs=6.8)
    arrow(ax, (MX + 15.0, 23.0), (RX - 16.0, 23.0), label="No / exception", fs=6.9)
    arrow(ax, (MX, 19.6), (MX, 17.8), label="Yes", fs=6.9)

    box(ax, MX, 14.4, 46.0, 5.6,
        "Live results are standardised into the JobListingOut shape with\nsource = adzuna_live; is_sample_data = false and\nbanner_message = null", kind="api", fs=7.0)

    box(ax, 50.0, 5.0, 76.0, 6.0,
        "Every response — search, recommendations, market demand, skill gap and roadmap — carries is_sample_data,\ndata_source and banner_message. The SampleDataBanner component renders its warning alert only when\nis_sample_data is true, so a demonstration run on fixtures can never be mistaken for live market data.",
        kind="ui", fs=7.0)
    arrow(ax, (MX, 11.6), (MX, 8.0))
    elbow(ax, [(RX - 16.0, 37.5), (60.0, 37.5), (60.0, 8.0)])
    elbow(ax, [(66.0, 19.5), (66.0, 8.0)])
    return save(fig, "fig_data_source.png")


if __name__ == "__main__":
    for fn in (fig_semantic_embedding, fig_hybrid_matcher, fig_job_recommendation,
               fig_market_demand, fig_skill_gap, fig_roadmap, fig_data_source):
        print("wrote", fn())
