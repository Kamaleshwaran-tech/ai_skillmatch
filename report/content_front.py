"""Front matter content: title page data, certificate, declaration,
acknowledgement, abstract and list of abbreviations.

Institution-level lines are taken verbatim from the project brief where the
brief fixes them (student, guide, HOD, department, submission date). Lines that
must be preserved from the official example document but were not supplied are
emitted as clearly bracketed placeholders so that they can be replaced without
touching any other part of the report.
"""

TITLE_PAGE = {
    "logo": "assets/logo.png",          # replaced automatically if the file exists
    "institution_lines": [
        "[INSTITUTE NAME]",
        "[AFFILIATING UNIVERSITY]",
        "[CITY – PIN, STATE]",
    ],
    "report_label": "A MINI PROJECT REPORT",
    "title": "AI-DRIVEN EMPLOYMENT AND SKILL MATCHING PORTAL FOR YOUTH DEVELOPMENT",
    "subtitle": "(Application Name: SkillSync AI)",
    "purpose": ("Submitted in partial fulfilment of the requirements for the award of the degree of "
                "Bachelor of Engineering in Computer Science and Design"),
    "student": [("KAMALESHWARAN R", "7376231CD120")],
    "degree_line": "B.E. – COMPUTER SCIENCE AND DESIGN",
    "year_sem": "IV Year – VII Semester   |   Academic Year 2026 – 2027",
    "guide": ["Project Guide", "SATHIS KUMAR K", "Associate Professor",
              "Department of Information Technology"],
    "hod": ["Head of the Department", "Dr. VENKATESAN R", "Head of the Department"],
    "department": "DEPARTMENT OF COMPUTER SCIENCE AND DESIGN",
    "place_date": "Submitted on: 17.10.2026",
}

FRONT_BLOCKS = [
    ("titlepage", TITLE_PAGE),

    ("front_heading", "CERTIFICATE"),
    ("p", "This is to certify that the mini project report entitled “AI-Driven Employment and Skill "
          "Matching Portal for Youth Development” (application name: SkillSync AI) is a bonafide record "
          "of the mini project work carried out by KAMALESHWARAN R (Register Number 7376231CD120), a "
          "student of the IV year VII semester of the Bachelor of Engineering degree programme in "
          "Computer Science and Design, during the academic year 2026 – 2027. The work embodied in this "
          "report was performed under my supervision and guidance, and has not been submitted elsewhere "
          "for the award of any degree or diploma."),
    ("sig_two", {
        "left": ["SATHIS KUMAR K", "Associate Professor", "Department of Information Technology",
                 "Project Guide"],
        "right": ["Dr. VENKATESAN R", "Head of the Department", "Department of Computer Science and Design",
                  "Head of the Department"],
    }),
    ("p", "Place: [City]"),
    ("p", "Date: 17.10.2026"),

    ("front_heading", "DECLARATION"),
    ("p", "I, KAMALESHWARAN R (Register Number 7376231CD120), hereby declare that the mini project report "
          "entitled “AI-Driven Employment and Skill Matching Portal for Youth Development” submitted in "
          "partial fulfilment of the requirements for the award of the degree of Bachelor of Engineering "
          "in Computer Science and Design is a record of the original work carried out by me under the "
          "guidance of SATHIS KUMAR K, Associate Professor, Department of Information Technology. I further "
          "declare that the work reported in this document has not been submitted, in part or in full, to "
          "any other university or institution for the award of any degree, diploma or similar title. All "
          "sources of information and software used in the work have been duly acknowledged."),
    ("sig_one", {
        "lines": ["KAMALESHWARAN R", "Register Number 7376231CD120",
                  "B.E. Computer Science and Design, IV Year VII Semester"],
    }),
    ("p", "Place: [City]"),
    ("p", "Date: 17.10.2026"),

    ("front_heading", "ACKNOWLEDGEMENT"),
    ("p", "I express my sincere gratitude to my project guide, SATHIS KUMAR K, Associate Professor, "
          "Department of Information Technology, for the constant encouragement, technical direction and "
          "patient review that shaped this mini project from its first outline to its final form. His "
          "insistence on verifiable results and honest labelling of experimental data became the design "
          "principle of the entire system."),
    ("p", "I am deeply indebted to Dr. VENKATESAN R, Head of the Department, for providing the "
          "infrastructure, the laboratory environment and the administrative support without which this "
          "work could not have been completed within the semester."),
    ("p", "I thank the faculty members of the Department of Computer Science and Design for their "
          "constructive comments during the project reviews, and the authors and maintainers of the "
          "open-source libraries on which this portal stands — FastAPI, SQLAlchemy, PyMuPDF, python-docx, "
          "spaCy, Hugging Face Transformers, React and Material UI — whose documentation made a "
          "student-scale implementation of a machine-learning pipeline possible."),
    ("p", "Finally, I thank my family and friends for their patience and moral support throughout the "
          "academic year."),

    ("front_heading", "ABSTRACT"),
    ("p", "Graduating students choose their preparation topics from syllabi and anecdote, while employers "
          "state their requirements in vacancy descriptions that change every quarter. SkillSync AI is an "
          "AI-driven employment and skill-matching portal that closes this loop with measured, auditable "
          "evidence. The system accepts a resume in PDF or DOCX form, recovers its text with PyMuPDF or "
          "python-docx, rejects empty, corrupt and scanned documents with explicit explanations, and "
          "segments the recovered text into conventional resume sections."),
    ("p", "Technical skills are extracted against a curated taxonomy of fifty-six canonical skills in "
          "eleven categories, with alias normalisation, context guards against ambiguous abbreviations, "
          "rule-based confidence values and evidence snippets that retain the character offsets of every "
          "match. A pre-trained all-MiniLM-L6-v2 sentence encoder adds a semantic stage governed by a "
          "configurable cosine threshold, and a five-stage hybrid matcher decides, for each demanded "
          "skill, whether the candidate profile matches it, needs review or lacks it; a high similarity "
          "score alone can never produce a match without validating evidence."),
    ("p", "Vacancy listings are retrieved from the Adzuna job-search API when credentials are configured "
          "and otherwise from clearly labelled offline fixtures; listings are deduplicated by external "
          "identifier and by a normalised title–company–location fingerprint before per-skill market "
          "demand is computed as the share of unique listings, always reported together with its "
          "denominator. The portal then ranks vacancies by match percentage, produces a role-oriented gap "
          "report with demand-derived priorities and an overall competency percentage, persists every "
          "analysis, and generates a deterministic learning roadmap ordered by market demand, optionally "
          "enriched by a language model that degrades to an explicit unavailable notice rather than "
          "fabricating content."),
    ("p", "The implementation comprises a FastAPI back end with SQLAlchemy persistence and JWT "
          "authentication, and a React single-page front end with Material UI and TanStack Query. "
          "Verification combined forty-seven back-end test functions, twenty-seven front-end test cases "
          "and an execution of the extraction and demand services whose outputs are reported in this "
          "document. Because offline demonstration data is visibly labelled throughout, the portal remains "
          "honest about the provenance of every number it shows."),
    ("p", "Keywords: skill gap analysis, resume parsing, semantic similarity, sentence transformers, "
          "job recommendation, market demand analytics, learning roadmap, FastAPI, React."),

    ("front_heading", "LIST OF ABBREVIATIONS"),
    ("table", {
        "caption": None,
        "headers": ["Abbreviation", "Expansion"],
        "rows": [
            ["AI", "Artificial Intelligence"],
            ["API", "Application Programming Interface"],
            ["ASGI", "Asynchronous Server Gateway Interface"],
            ["AWS", "Amazon Web Services"],
            ["BERT", "Bidirectional Encoder Representations from Transformers"],
            ["CI/CD", "Continuous Integration / Continuous Delivery"],
            ["CORS", "Cross-Origin Resource Sharing"],
            ["CRUD", "Create, Read, Update, Delete"],
            ["CSS", "Cascading Style Sheets"],
            ["DFD", "Data Flow Diagram"],
            ["DOCX", "Office Open XML Wordprocessing Document"],
            ["ER", "Entity–Relationship"],
            ["ESCO", "European Skills, Competences, Qualifications and Occupations"],
            ["FASTAPI", "Modern Python web framework used for the back end"],
            ["GCP", "Google Cloud Platform"],
            ["HTML", "HyperText Markup Language"],
            ["HTTP / HTTPS", "HyperText Transfer Protocol (Secure)"],
            ["JSON", "JavaScript Object Notation"],
            ["JWT", "JSON Web Token"],
            ["LLM", "Large Language Model"],
            ["MUI", "Material UI component library"],
            ["NLP", "Natural Language Processing"],
            ["OCR", "Optical Character Recognition"],
            ["ORM", "Object–Relational Mapping"],
            ["PDF", "Portable Document Format"],
            ["PyMuPDF", "Python binding of the MuPDF document library"],
            ["REST", "Representational State Transfer"],
            ["SHA", "Secure Hash Algorithm"],
            ["SPA", "Single Page Application"],
            ["SQL", "Structured Query Language"],
            ["TF–IDF", "Term Frequency – Inverse Document Frequency"],
            ["UML", "Unified Modelling Language"],
            ["URL", "Uniform Resource Locator"],
            ["UUID", "Universally Unique Identifier"],
        ],
        "widths": [0.26, 0.74],
    }),
]
