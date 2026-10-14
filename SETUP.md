# SkillSync AI - Setup & Operations Guide

SkillSync AI is an intelligent full-stack skill gap analyzer and market-driven career pathway generator built with **FastAPI**, **SQLAlchemy**, **PyMuPDF**, **Sentence-Transformers**, **React (Vite)**, and **Material UI**.

---

## 1. Prerequisites

- **Python**: 3.11+ or 3.12+ (tested on Python 3.12.10)
- **Node.js**: 18+ or 20+ (tested on Node v24.14.1 / Vite 5)
- **Git**

---

## 2. Environment Variables (.env)

Copy `.env.example` in the project root to `.env` (or configure system environment variables):

```bash
cp .env.example .env
```

### Documented Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `"SkillSync AI"` | Application display name. |
| `ENVIRONMENT` | `"development"` | Environment runtime (`development` / `production`). |
| `DEBUG` | `true` | FastAPI debug mode flag. |
| `PORT` | `8000` | Backend API server port. |
| `HOST` | `"0.0.0.0"` | Backend binding host. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of allowed frontend origins. |
| `DATABASE_URL` | `sqlite:///./skillsync.db` | SQLAlchemy DB connection string. Can be swapped for PostgreSQL: `postgresql+psycopg2://user:password@localhost:5432/skillsync_ai`. |
| `JWT_SECRET` | *(Random 32+ char secret)* | Secret key for signing HS256 authentication tokens. Generate with `openssl rand -hex 32`. |
| `JWT_ALGORITHM` | `HS256` | JWT signature algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Lifespan of JWT bearer access tokens in minutes. |
| `ADZUNA_APP_ID` | `your_adzuna_app_id_here` | Application ID for Adzuna Job Search API. |
| `ADZUNA_APP_KEY` | `your_adzuna_app_key_here` | Application Key for Adzuna Job Search API. |
| `ADZUNA_COUNTRY` | `us` | Default ISO country code for Adzuna job querying (e.g. `us`, `gb`). |
| `SEMANTIC_MODEL_NAME` | `all-MiniLM-L6-v2` | Pretrained sentence transformer model name from Hugging Face. |
| `SEMANTIC_SIMILARITY_THRESHOLD` | `0.65` | Cosine similarity threshold (0.0–1.0) above which resume sentences match job skills. |
| `UPLOAD_DIR` | `./uploads/resumes` | Filesystem directory where uploaded candidate resumes are stored. |
| `MAX_UPLOAD_SIZE_MB` | `5` | Maximum permitted file upload size in megabytes. |

---

## 3. Adzuna Credential Setup

The system fetches live market demand data from the Adzuna API or provides an automatic offline fixture fallback.

1. **Sign Up**: Register for a developer account at [developer.adzuna.com](https://developer.adzuna.com/).
2. **Obtain API Keys**: Create an application on the Adzuna developer portal to obtain your `APP_ID` and `APP_KEY`.
3. **Configure `.env`**:
   ```env
   ADZUNA_APP_ID="<your_app_id>"
   ADZUNA_APP_KEY="<your_app_key>"
   ADZUNA_COUNTRY="us"
   ```
4. **Offline Fixture Fallback**:
   If `ADZUNA_APP_ID` or `ADZUNA_APP_KEY` are unset, missing, or contain default placeholder values, the backend will **not fail**. Instead, it serves curated sample listings from `backend/app/taxonomy/sample_jobs.json` with `is_sample_data: True`. The frontend clearly shows a **"SAMPLE DATA — not live"** banner.

---

## 4. Semantic Model Download & Caching

The hybrid matcher uses `sentence-transformers/all-MiniLM-L6-v2` for dense vector embeddings:

- The model is loaded **once as a singleton at application startup** (`backend/app/services/semantic_matcher.py`) and warmed up inside the FastAPI lifespan handler (`backend/app/main.py`), preventing per-request overhead.
- Embeddings are computed with batching and cached in-memory with SHA-256 fingerprinting.

### Pre-downloading the Model
To cache the model locally before running the backend:

```bash
python -c "from transformers import AutoTokenizer, AutoModel; AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2'); AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2'); print('Model cached successfully.')"
```

The model weights (~90MB) will be stored in your Hugging Face cache directory (`~/.cache/huggingface/hub`).

---

## 5. Database Setup & Alembic Migrations

The database layer is abstracted using SQLAlchemy 2.0 ORM models and Alembic migrations.

### Running Migrations

From the `backend/` directory:

```bash
# Apply all existing migrations up to head:
alembic upgrade head
```

### Creating New Migrations
When adding or altering models:

```bash
alembic revision --autogenerate -m "describe schema changes"
alembic upgrade head
```

### Switching to PostgreSQL
1. Change `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL="postgresql+psycopg2://postgres:password@localhost:5432/skillsync_ai"
   ```
2. Install the PostgreSQL driver: `pip install psycopg2-binary`.
3. Run `alembic upgrade head`.

---

## 6. Running the Application

### Option A: Two Separate Terminals (Standard Development)

#### Terminal 1 — Backend (FastAPI + Uvicorn)
```powershell
cd "d:\S7 main project\ai_skill_match\backend"
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

#### Terminal 2 — Frontend (React + Vite)
```powershell
cd "d:\S7 main project\ai_skill_match\frontend"
npm install
npm run dev
```
- Web Application: `http://127.0.0.1:5173`

---

## 7. Feature Walkthrough & How to Use

1. **Authentication**:
   - Navigate to `http://127.0.0.1:5173/auth` to register or log in.
2. **Persistent Resume & Automatic Dashboard Restoration**:
   - Navigate to `http://127.0.0.1:5173/skill-gap`.
   - Upload your resume (`.pdf` or `.docx`). It is automatically parsed, its skills extracted, and set as your **Active Resume**.
   - If you log out and log back in (or refresh the app), your active resume, extracted skills, job recommendations, and analyses load automatically without re-uploading.
   - When you upload a replacement resume, it becomes active and your previous resume is preserved in the **Resume History** list.
3. **Personalized Job Recommendations**:
   - The **Recommended Jobs** tab queries live Adzuna listings relevant to your resume's top skills and ranks them by match percentage descending.
   - Each card displays your match % progress bar, green matched skill chips, gray missing skill chips, salary/location, and a direct "Apply on Adzuna" button.
4. **Role Skill Gap Analysis**:
   - Switch to the **Role Skill Gap Analysis** tab.
   - Enter your target role (e.g. `Developer`, `Python`, `Frontend`) to see an overall competency match %, matched skills with inline evidence, missing competencies with market demand % and project-defined priority badges (`High >= 70%`, `Medium 40-69%`, `Low < 40%`), and any items needing human review.
5. **Role Learning Roadmap**:
   - Switch to the **Learning Roadmap** tab (or click **Learning Roadmap** in the top navigation bar).
   - Enter your target role and click **Generate Roadmap**.
   - Missing and needs-review skills are deterministically ordered into a sequential learning roadmap by real market demand % (highest market opportunity first).
   - Renders as a vertical Material UI Stepper showing demand badges, priority chips, plain-language AI explanations, general learning resource suggestions (documentation, free platforms, project ideas), or an explicit `"AI explanation unavailable"` warning alert if LLM services are unreachable.

---

## 8. Running the Test Suites

### Backend Pytest Suite
```powershell
cd "d:\S7 main project\ai_skill_match\backend"
python -m pytest app/tests -v
```
- **Status**: 41 passed, 0 failed (100% pass rate)

### Frontend Vitest Suite
```powershell
cd "d:\S7 main project\ai_skill_match\frontend"
npm test
```
- **Status**: 26 passed across 6 test suites, 0 failed (100% pass rate)

### Frontend Production Build
```powershell
cd "d:\S7 main project\ai_skill_match\frontend"
npm run build
```
- **Result**: Successfully bundled modules into `dist/`.

---

## 9. Known Limitations & Architecture Notes

1. **Adzuna Live vs. Fixture Mode**:
   When Adzuna credentials are unset or free-tier rate limits are exceeded, the backend transparently falls back to curated sample fixtures from `backend/app/taxonomy/sample_jobs.json` with a visible `"SAMPLE DATA"` banner.
2. **Deterministic Roadmap Ordering**:
   Roadmap sequence steps are strictly ordered by real market demand percentage descending from the market demand service, ensuring that learning priorities are grounded in real job postings rather than arbitrary LLM output.
3. **LLM Provider & Safe Fallback**:
   Roadmap explanations use an optional LLM configuration (`GEMINI_API_KEY`, `OPENAI_API_KEY`, or `LLM_API_KEY`). If unconfigured or if a request times out, the backend gracefully falls back per-step with `"AI explanation unavailable"`, never blocking the response or fabricating unverified course lists.
4. **Database Dialect**:
   Configured for MySQL or SQLite via `DATABASE_URL` in `.env`. Resumes retain non-destructive history via `is_active` flags.


python -m uvicorn app.main:app --host 127.0.0.1 --port 8000