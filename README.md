# Devil's Advocate Panel

**Pitch your idea. Get grilled by AI investors who won't go easy on you.**

A Streamlit app that puts your business pitch, product plan, or proposal in front of a
panel of three AI personas — a skeptical VC, a hard-nosed financial analyst, and a market
realist — who interrogate it across multiple rounds, react to how you defend it, and
deliver a severity-ranked verdict with specific fixes at the end. You can download the
full transcript and verdict as a PDF.

---

## Why this project

Most "AI feedback on your pitch" tools are polite. They hedge, they compliment, they give
you a balanced list of pros and cons. That's not useful when the actual value of a pitch
review is finding the questions a real investor would ask that you don't have a good
answer for yet.

This project is built around a different premise: the AI panel is adversarial by design.
It's not trying to be fair — it's trying to find the weakest point in your pitch and push
on it, the way a skeptical room actually would. You can tune how hard it pushes (from
constructive to openly merciless), but even at the gentlest setting, it's still trying to
catch you out, not cheer you on. The panel can also check your pitch against real data —
your actual GitHub activity, your actual spreadsheet model — instead of just reasoning
against text you typed, so it can catch a gap between what you claimed and what's real.

---

## How it works (user flow)

1. **Sign in** — Google OAuth (via Supabase Auth) or email/password.
2. **(Optional) Connect accounts** — GitHub and Google Sheets, so the panel can check
   your claims against real data instead of just your pitch text. Stripe and Notion are
   supported in the code but currently run in mock mode (see [Connectors](#connectors)).
3. **Submit your pitch** and pick an intensity level: **Light**, **Normal**, **Heavy**,
   or **No Mercy**. Higher intensity means less benefit of the doubt, more aggressive
   follow-ups, and harsher severity scoring in the final verdict.
4. **Get grilled**, one persona at a time — VC, then Financial Analyst, then Market
   Realist. For each turn you see:
   - The persona's **reasoning trace**, streamed in live, showing genuine analysis (not
     performed sarcasm — that's saved for the actual question)
   - The persona's **question/challenge**, in-character and sarcastic, scaled to your
     chosen intensity
   - A box to **reply**, after which that specific persona reacts to what you said —
     either resolving the objection or pushing further (up to 3 rounds per persona)
5. **Read the verdict** — a list of weaknesses, ranked by severity (1–5, calibrated by
   your intensity level), each with a specific fix.
6. **Download the PDF** — the full transcript (every round, every persona, every reply)
   plus the verdict, as a document you can keep or share.
7. **Revisit past sessions** from Pitch History any time — the transcript and verdict are
   saved, and the PDF regenerates on demand.

---

## Tech stack, and why

| Piece | Choice | Why |
|---|---|---|
| Frontend | **Streamlit** | Fast to build a real interactive app in pure Python — no separate frontend codebase needed for a project this scoped |
| Orchestration | **LangGraph** | The grilling loop is fundamentally a cycle (persona asks → user replies → persona reacts → repeat), not a linear chain. LangGraph models this as a graph with conditional edges and native human-in-the-loop pausing (`interrupt()`/`Command(resume=...)`), which maps directly onto "wait for the founder's reply before continuing" |
| LLMs | **Gemini 2.5 Flash (primary) → xAI Grok → Groq**, in a retry-then-fallback chain | Three free/low-cost providers chained for resilience against rate limits. Grok was the original first choice specifically for its tone (it's noticeably better at genuine sarcasm/roasting than more measured models), but currently sits second in the chain while its account is unfunded — flip `LLM_PROVIDER_ORDER` in `.env` to restore it to primary once funded |
| Live market search | **Tavily** | Lets the Market Realist persona check "does this actually exist / how did comparable products do" against the live web, not just static knowledge |
| RAG | **Supabase `pgvector`** | A static curated corpus of SaaS/marketplace benchmarks and startup failure post-mortems, retrieved via cosine similarity, grounds the Financial Analyst's challenges in real numbers instead of generic critique |
| Database / Auth / Storage | **Supabase** | Postgres + pgvector + Auth (Google OAuth + email/password) + Row Level Security in one managed service — no separate auth provider or vector DB needed |
| Connectors | **GitHub API, Google Sheets API** (OAuth-gated, per-user) | Lets specific personas fact-check specific claims against a founder's real accounts: GitHub commit activity for "we've built this," a real spreadsheet model for "the math behind our numbers" |
| PDF export | **ReportLab** | Generates the downloadable transcript + verdict document |

### Why an adversarial fallback chain, not just one model

All three LLM providers have free or low-cost tiers with real rate limits. Rather than
the app breaking mid-session when one provider is temporarily unavailable, each call
retries once on the same model, then moves to the next model in the chain — and once a
session falls back off its primary, it sticks with whatever's working rather than
re-probing the primary on every subsequent turn (avoiding repeatedly wasting calls
against an exhausted daily quota). Fallback only triggers on transient errors (rate
limits, timeouts) — a genuine auth/billing problem is surfaced as a real error instead of
silently masked by switching providers.

---

## System design

```
┌────────────────────────── Streamlit (frontend/app.py) ───────────────────────┐
│ Login (Supabase Auth: Google OAuth + email/password, 100% client-side)       │
│  → Connect Accounts (Calls backend OAuth authorize-url & token exchange)     │
│  → Pitch Submission (Calls POST /api/sessions)                                │
│  → Live Interrogation (Calls POST /api/sessions/{id}/reply & next-turn)       │
│  → Verdict Report (Calls GET /api/sessions/{id}/verdict & PDF download)      │
│  → Pitch History (Calls GET /api/sessions)                                   │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ HTTP + Bearer JWT (frontend/api_client.py)
                                        ▼
┌─────────────────────────── FastAPI (backend/main.py) ─────────────────────────┐
│ Auth: backend/deps.py (verifies Supabase JWT using admin client)              │
│ Routers: /api/sessions, /api/verdicts, /api/pdf, /api/connections             │
│ LangGraph compilation once on startup: app.state.graph                        │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
┌────────────────────────────── LangGraph (core/graph.py) ──────────────────────┐
│  State: pitch_text, intensity, connected_providers, transcript,              │
│         per-persona round/resolved tracking, llm_calls_made                  │
│                                                                                │
│   vc_node ──► router ──► [interrupt: wait for reply] ──► vc_node (reacts)     │
│                  │                                                            │
│                  ▼ (once resolved / round cap hit)                           │
│              analyst_node ──► ... ──► realist_node ──► ... ──► verdict_node  │
│                                                                                │
│  Tools attached per persona, gated by what's connected:                      │
│   VC:       GitHub (real activity check)                                     │
│   Analyst:  Google Sheets (real model), Stripe (mock), pgvector RAG          │
│   Realist:  Notion (mock), Tavily live search                                │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌────────────────┐    ┌────────────────────┐    ┌──────────────────────┐
│ Gemini / Grok /  │    │ GitHub & Sheets     │    │      Supabase          │
│ Groq (fallback   │    │ APIs, Tavily search │    │ Auth, Postgres,        │
│ chain)           │    │                     │    │ pgvector, RLS-scoped   │
└────────────────┘    └────────────────────┘    │ sessions/transcripts/  │
                                                    │ verdicts/connections   │
                                                    └──────────────────────┘
```

### Key design decisions

- **Sequential, not parallel, personas** — one persona grills at a time, each reacting
  specifically to what the founder just said to *them*. This keeps "the panel reacts to
  your response" meaningful rather than three unrelated challenges landing at once.
- **Round cap, tracked independently per persona** — up to 3 rounds each; a persona can
  resolve early if satisfied, another can run the full cap, and the whole panel routes to
  verdict once every persona is either resolved or capped (or a 12-call session budget is
  hit, as a hard cost ceiling).
- **Sarcasm lives in the question, not the reasoning** — each persona's visible thinking
  trace is genuine analysis; the sarcastic, in-character tone is layered on only in the
  spoken challenge that follows it, so the reasoning stays useful as actual reasoning.
- **No tool attached when a connector isn't connected**, rather than falling back to
  fabricated mock data — an unconnected persona reasons off the pitch text alone.
- **PDFs regenerate on demand** from the stored transcript/verdict rather than being
  stored as files — simpler than managing a storage bucket for something this size.

---

## Project structure

```
app.py                  Entry point, routing, sidebar nav, OAuth callback handling
core/
  state.py              LangGraph state schema, round/budget constants
  prompts.py            Persona identities + intensity-scaled tone blocks
  llm.py                Fallback chain (Gemini/Grok/Groq), reasoning extraction
  graph.py              Persona nodes, router, verdict node, graph assembly
  tools.py              Tool-attachment logic (gated by connected providers)
connectors/
  oauth.py              OAuth authorize-URL building + code exchange
  github_tools.py        Real GitHub API tool
  sheets_tools.py        Real Google Sheets API tool
db/
  client.py             Supabase client setup
  schema.sql             Table definitions + RLS policies
  connections.py         user_connections CRUD
  rag.py                  pgvector similarity search
ui/
  auth.py                Login/signup/logout (Google OAuth + email/password)
  connections.py          Connect Accounts screen
  pitch.py                Pitch Submission screen
  session.py              Live Interrogation screen
  verdict.py              Verdict Report screen
  history.py              Pitch History screen
  components.py           Theme tokens, custom CSS, shared UI pieces
export/
  pdf.py                  Transcript + verdict PDF generation
seed_corpus.py           Populates the pgvector benchmark corpus
test_all.py              Smoke test: imports + PDF generation
.env.example             Template for all required environment variables
```

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd devils-advocate-panel
python -m venv venv
# Windows: venv\Scripts\Activate.ps1   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in:

```
# LLM providers
GOOGLE_API_KEY=          # from aistudio.google.com — also used for embeddings
XAI_API_KEY=              # from console.x.ai (needs credits to actually respond)
GROQ_API_KEY=              # free, from console.groq.com
LLM_PROVIDER_ORDER=       # optional, e.g. "xai,google_genai,groq" — defaults to Gemini-first

# Live market search
TAVILY_API_KEY=            # free tier, from tavily.com

# Environment & Service URLs (Two-Process Architecture)
APP_BASE_URL=http://localhost:8501
BACKEND_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:8501

# Supabase
SUPABASE_URL=
SUPABASE_KEY=               # anon/publishable key
SUPABASE_SERVICE_KEY=       # service_role/secret key — backend only, never expose

# OAuth connectors (leave blank to use mock mode)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GOOGLE_OAUTH_CLIENT_ID=      # separate from the Google login client below
GOOGLE_OAUTH_CLIENT_SECRET=
STRIPE_CLIENT_ID=            # left blank in this build — see Connectors below
STRIPE_CLIENT_SECRET=
NOTION_CLIENT_ID=            # left blank in this build
NOTION_CLIENT_SECRET=
```

### 3. Supabase project setup

1. Create a project at [supabase.com](https://supabase.com).
2. In the SQL Editor, enable the vector extension first, on its own:
   ```sql
   create extension if not exists vector;
   ```
3. Run the full contents of `db/schema.sql`.
4. Run the RAG similarity function (not included in `schema.sql`):
   ```sql
   create or replace function match_benchmark_corpus(
     query_embedding vector(768),
     match_threshold float,
     match_count int
   )
   returns table (content text, source varchar(255), tag varchar(50), similarity float)
   language sql stable
   as $$
     select content, source, tag, 1 - (embedding <=> query_embedding) as similarity
     from benchmark_corpus
     where 1 - (embedding <=> query_embedding) > match_threshold
     order by embedding <=> query_embedding
     limit match_count;
   $$;
   ```
5. **Authentication → Providers → Google**: enable it, and paste in a Client ID/Secret
   from a Google Cloud OAuth client registered with Supabase's callback URL
   (`https://<your-project-ref>.supabase.co/auth/v1/callback`) — this is a **separate**
   OAuth client from the one used for the Google Sheets connector below.
6. For local development, under **Authentication → Providers → Email**, consider turning
   off "Confirm email" — Supabase's default email sender has a low rate limit that's easy
   to hit while testing signups repeatedly.
7. Populate the benchmark corpus: `python seed_corpus.py`.

### 4. OAuth apps (GitHub, Google Sheets)

Both need `http://localhost:8501` registered as their redirect/callback URI for local
development:

- **GitHub**: [github.com/settings/developers](https://github.com/settings/developers) →
  New OAuth App.
- **Google Sheets**: [console.cloud.google.com](https://console.cloud.google.com) →
  enable the Sheets API → configure the OAuth consent screen (add yourself as a test
  user) → Credentials → Create OAuth client ID (Web application).

Stripe and Notion connectors have real code paths in `connectors/` but are left
unconfigured in this build — see [Connectors](#connectors) below for why, and how to
enable them if you want to.

### 5. Run it (Two-Process Local Development)

The application runs as two decoupled processes:

```bash
# Terminal 1: Start FastAPI Backend (Port 8000)
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start Streamlit Frontend (Port 8501)
streamlit run frontend/app.py --server.port 8501
```

Open the frontend URL in your browser: `http://localhost:8501`.
The frontend communicates exclusively via HTTP with the backend at `http://localhost:8000` (configured via `BACKEND_BASE_URL`).

---

## Connectors

| Connector | Status | Used by | Why |
|---|---|---|---|
| GitHub | ✅ Live | VC | Checks real commit activity/repo age against "we've built this" claims |
| Google Sheets | ✅ Live | Financial Analyst | Reads the founder's actual financial model |
| Stripe | 🔲 Mock mode | Financial Analyst | Would check real MRR/revenue; left unconfigured because Stripe is currently invite-only for new India-based accounts. Swap in real credentials, or substitute a different payment processor with OAuth support (e.g. Razorpay), if you want this live |
| Notion | 🔲 Mock mode | Market Realist | Would read the founder's own market research; skipped for scope, straightforward to enable — register a public Notion integration and add credentials |

When a connector isn't configured, its persona simply reasons off the pitch text alone
for that angle — no fabricated data is used as a substitute.

---

## Known limitations / roadmap

- Text-only pitch input — no PDF/deck upload yet (parsing would slot in before the graph
  runs, without changing the graph itself)
- Grok currently sits second in the fallback chain due to an unfunded xAI account — flip
  `LLM_PROVIDER_ORDER` back to lead with `xai` once funded, for its stronger sarcastic tone
- Stripe and Notion connectors are code-complete but unconfigured (see above)
- Deployed instances (e.g. Streamlit Community Cloud) need `st.secrets` configured with
  the same keys as `.env`, and every OAuth app's redirect URI updated to the production
  URL alongside `localhost`
