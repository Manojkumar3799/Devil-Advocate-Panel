# Devil's Advocate Panel — Implementation Plan

**Pitch your idea. Get grilled by AI investors who won't go easy on you.**

This plan builds the complete application per the spec: a Streamlit app where a user submits a pitch, gets interrogated by three AI personas (VC, Financial Analyst, Market Realist) via a LangGraph-orchestrated multi-round conversation, and receives a severity-ranked verdict with downloadable PDF.

> [!IMPORTANT]
> The scaffold files referenced in the spec (`state.py`, `prompts.py`, `llm.py`, `graph.py`, `run_demo.py`) **do not exist yet** — the workspace only contains a Python 3.14.2 venv. This plan treats everything as greenfield, following the spec's prescribed build order.

---

## Assumptions (spec was silent on these)

1. **Supabase project** — You already have a Supabase project provisioned. I'll need `SUPABASE_URL`, `SUPABASE_KEY` (anon key), and `SUPABASE_SERVICE_KEY` in `.env`.
2. **Tavily API key** — You have a Tavily account. Key goes in `TAVILY_API_KEY`.
3. **OAuth app credentials** — GitHub, Stripe, Google, and Notion OAuth apps are registered externally; their client IDs/secrets go in `.env`. Implementation phase 4 will create the flows but can't test without real credentials.
4. **RAG corpus content** — Phase 5 will create the schema and ingestion pipeline; actual curated content (post-mortems, SaaS benchmarks) will be loaded via a seed script you provide or I'll include a few placeholder entries.
5. **Checkpointer** — Using `MemorySaver` (in-process) for local dev. The plan notes where to swap for `PostgresSaver` in production.
6. **Streamlit async** — Streamlit doesn't natively run an asyncio event loop. I'll use `asyncio.run()` in a background thread to drive `astream_events`, piping chunks to the UI via Streamlit's `st.write_stream`-compatible generators and `st.session_state`.
7. **PDF library** — Using `reportlab` as specified.
8. **Token streaming in Streamlit** — Since `astream_events` is async and Streamlit is sync, I'll wrap the async generator in a sync adapter using `asyncio.run_coroutine_threadsafe` on a dedicated event loop thread.

---

## Open Questions

> [!IMPORTANT]
> **Supabase credentials**: Do you already have a Supabase project? I need the URL and keys to wire the auth/database layer. If not, I'll build the Supabase integration with placeholder config and add a setup guide.

> [!IMPORTANT]
> **OAuth app registrations**: The 4 OAuth connectors (GitHub, Stripe, Google Sheets, Notion) each require registered OAuth apps with redirect URIs pointing to your Streamlit app. Do you have these registered? If not, I'll build the flows with clear setup instructions and mock-compatible fallbacks.

> [!NOTE]
> **Deployment target**: The plan assumes local development (`streamlit run`). If you plan to deploy (e.g., Streamlit Cloud, Railway), some adjustments to the OAuth redirect flow and checkpointer persistence would be needed.

---

## Project Structure

```
Devil's Advocate Panel/
├── .env.example                  # Template with all required env vars
├── .env                          # Actual secrets (gitignored)
├── .gitignore
├── requirements.txt
├── app.py                        # Streamlit entry point
├── core/
│   ├── __init__.py
│   ├── state.py                  # LangGraph state definition (TypedDict)
│   ├── prompts.py                # Persona identities + intensity blocks (template system)
│   ├── llm.py                    # LLM factory: fallback chain, retry, reasoning extraction
│   ├── graph.py                  # LangGraph StateGraph: nodes, edges, router, verdict
│   ├── reasoning.py              # Per-provider reasoning extraction/normalization
│   └── tools.py                  # Tool definitions (Tavily, MCP stubs → real later)
├── connectors/
│   ├── __init__.py
│   ├── oauth.py                  # OAuth flow helpers (GitHub, Stripe, Google, Notion)
│   ├── github_tools.py           # GitHub MCP connector tools
│   ├── stripe_tools.py           # Stripe MCP connector tools
│   ├── sheets_tools.py           # Google Sheets MCP connector tools
│   └── notion_tools.py           # Notion MCP connector tools
├── db/
│   ├── __init__.py
│   ├── client.py                 # Supabase client init
│   ├── sessions.py               # Session CRUD
│   ├── transcripts.py            # Transcript entry CRUD
│   ├── verdicts.py               # Verdict CRUD + PDF URL
│   ├── connections.py            # User connections (OAuth tokens)
│   ├── rag.py                    # pgvector benchmark corpus retrieval
│   └── schema.sql                # Full DDL for all tables + RLS policies
├── export/
│   ├── __init__.py
│   └── pdf.py                    # PDF generation with reportlab
├── ui/
│   ├── __init__.py
│   ├── auth.py                   # Streamlit auth UI (login/signup via Supabase)
│   ├── connections.py            # "Connect accounts" screen
│   ├── pitch.py                  # Pitch submission form + intensity selector
│   ├── session.py                # Live session view (streaming reasoning + question)
│   ├── verdict.py                # Verdict report view + download button
│   ├── history.py                # Past sessions list
│   └── components.py             # Shared UI components (persona cards, progress)
├── run_demo.py                   # CLI demo (no Streamlit, tests core loop)
└── seed_corpus.py                # Script to seed benchmark_corpus with sample data
```

---

## Proposed Changes — Phase by Phase

Following the spec's prescribed build order (§10).

---

### Phase 1: Core Loop (LangGraph + LLM Fallback + Personas + CLI Demo)

This phase creates the scaffold referenced in §9. Everything runs headless via `run_demo.py`.

---

#### [NEW] [requirements.txt](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/requirements.txt)

All dependencies:
```
streamlit>=1.45
langgraph>=0.4
langchain>=0.3
langchain-core>=0.3
langchain-xai>=0.2              # ChatXAI for Grok
langchain-google-genai>=2.1     # ChatGoogleGenerativeAI for Gemini
langchain-groq>=0.3             # ChatGroq
langchain-tavily>=0.1           # TavilySearchResults tool
supabase>=2.0                   # Supabase Python client
vecs>=0.4                       # pgvector via Supabase
reportlab>=4.0                  # PDF generation
python-dotenv>=1.0
httpx>=0.27                     # For OAuth HTTP calls
```

#### [NEW] [.env.example](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/.env.example)

Template listing every required environment variable:
- `XAI_API_KEY` — Grok
- `GOOGLE_API_KEY` — Gemini
- `GROQ_API_KEY` — Groq
- `TAVILY_API_KEY` — live market search
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
- `STRIPE_CLIENT_ID`, `STRIPE_CLIENT_SECRET`
- `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- `NOTION_CLIENT_ID`, `NOTION_CLIENT_SECRET`

#### [NEW] [core/state.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/core/state.py)

LangGraph state as a `TypedDict`:
```python
class PanelState(TypedDict):
    pitch_text: str
    intensity: str                            # "light" | "normal" | "heavy" | "no_mercy"
    personas: list[str]                       # ["vc", "analyst", "realist"]
    current_persona_index: int
    rounds: dict[str, int]                    # {"vc": 0, "analyst": 0, "realist": 0}
    resolved: dict[str, bool]                 # {"vc": False, ...}
    transcript: list[TranscriptEntry]         # Full conversation log
    llm_call_count: int                       # Session-wide budget tracker (max 12)
    active_provider: str | None               # Sticky fallback provider
    connected_providers: list[str]            # ["github", "stripe", ...]
    user_id: str | None
    session_id: str | None
    verdict: dict | None                      # Final verdict JSON
```

`TranscriptEntry` is a `TypedDict` with: `persona`, `round`, `thinking_text`, `question_text`, `user_reply`, `provider_used`, `resolved`.

#### [NEW] [core/prompts.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/core/prompts.py)

**Design**: One shared template with two substitution slots per persona call:
1. `{identity_block}` — fixed per persona (3 total)
2. `{intensity_block}` — 4 levels × 3 personas = 12 short snippets stored in a `dict[str, dict[str, str]]`

Template structure:
```
SYSTEM_TEMPLATE = """
You are {persona_name}, an expert panelist on the Devil's Advocate Panel.

{identity_block}

## Intensity & Tone
{intensity_block}

## Rules
- Your REASONING must be genuine, specific analysis of the pitch. No sarcasm in reasoning.
- Your spoken CHALLENGE that follows the reasoning should be in-character: sharp, specific, sarcastic.
- End your response with exactly: RESOLVED: true or RESOLVED: false
- If the founder's reply adequately addresses your concern, mark RESOLVED: true.
- If not, explain why and press harder.

## Pitch
{pitch_text}

## Conversation so far
{conversation_history}
"""
```

Identity blocks:
- **VC**: Founder credibility, execution evidence, moat, ask-vs-stage fit.
- **Financial Analyst**: Unit economics, revenue claims, burn rate, model integrity. References benchmarks from RAG.
- **Market Realist**: Market size claims, competitive landscape, novelty. Uses live search data.

Intensity snippets vary across 4 axes (tone, bar-to-accept, follow-ups, tool aggressiveness) per §4.

#### [NEW] [core/reasoning.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/core/reasoning.py)

Normalized reasoning extraction per provider:
```python
def extract_reasoning(response: AIMessage, provider: str) -> tuple[str, str]:
    """Returns (thinking_text, answer_text)."""
    if provider == "grok":
        thinking = response.additional_kwargs.get("reasoning_content", "")
        answer = response.content
    elif provider == "gemini":
        # Gemini with include_thoughts=True returns thought-marked parts
        # Parse thought parts vs content parts from response
        thinking, answer = _parse_gemini_thoughts(response)
    elif provider == "groq":
        # Check for <think>...</think> tags in content
        thinking, answer = _parse_groq_think_tags(response.content)
        if not thinking:
            thinking = "⚠️ Reasoning unavailable for this response"
    return thinking, answer
```

#### [NEW] [core/llm.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/core/llm.py)

LLM factory with the specified fallback chain:

1. **ChatXAI** (`grok-4`, streaming=True) → retry once → fallback to:
2. **ChatGoogleGenerativeAI** (`gemini-2.5-flash`, thinking_budget=-1, include_thoughts=True) → retry once → fallback to:
3. **ChatGroq** (`llama-3.3-70b-versatile`, reasoning_format="parsed") → retry once → error

Key design decisions:
- **Retry policy**: `with_retry(stop_after_attempt=2, retry_if_exception_type=(RateLimitError, TimeoutError, ConnectionError))`. Auth errors, bad requests, content-policy errors are NOT retried.
- **Fallback chain**: `grok.with_retry(...).with_fallbacks([gemini.with_retry(...), groq.with_retry(...)])`
- **Sticky fallback**: Once a session falls back off Grok, `state["active_provider"]` is set to the working provider and subsequent calls skip Grok entirely. Implemented by having `get_llm(state)` check `active_provider` and return either the full chain or a pruned chain.
- **Budget tracking**: Each call increments `state["llm_call_count"]`; checked before calling.

#### [NEW] [core/tools.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/core/tools.py)

- **Tavily**: `TavilySearchResults` from `langchain_tavily`, bound directly to the market realist node.
- **Mock tools** for GitHub, Stripe, Sheets, Notion — clearly marked `# MOCK: replace in Phase 4`.
- **Benchmark retriever** — mock function returning sample data, marked `# MOCK: replace in Phase 5`.

#### [NEW] [core/graph.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/core/graph.py)

LangGraph `StateGraph` with these nodes:

```
START → vc_node → router_node → analyst_node → router_node → realist_node → router_node → verdict_node → END
                                                                              ↑                              
                                                              (loop back if unresolved & under caps)
```

**Node implementations:**

1. **`persona_node_factory(persona_name)`** — Returns a node function that:
   - Checks `llm_call_count < 12`; if exceeded, returns immediately (router will force verdict)
   - Builds system prompt from template + identity + intensity block
   - Conditionally attaches tools based on `connected_providers`
   - Calls LLM via fallback chain, increments `llm_call_count`
   - Extracts `(thinking, answer)` via `reasoning.extract_reasoning()`
   - Parses `RESOLVED: true/false` from answer
   - Appends `TranscriptEntry` to `state["transcript"]`
   - Calls `interrupt({"persona": name, "question": answer, "thinking": thinking})` to pause for user reply
   - On resume, receives user reply and either marks resolved or continues

2. **`router_node`** — Examines state:
   - If `llm_call_count >= 12` → route to `verdict_node`
   - If all personas resolved → route to `verdict_node`
   - Advance `current_persona_index` to next unresolved persona (or loop if any persona has rounds left < 3)
   - If all at round cap → route to `verdict_node`

3. **`verdict_node`** — Single LLM call over full transcript, returns strict JSON:
   ```json
   {"weaknesses": [{"issue": "...", "severity": 1-5, "fix": "..."}, ...]}
   ```
   Severity calibrated by intensity setting.

**Compilation**: `graph.compile(checkpointer=MemorySaver())`

#### [NEW] [run_demo.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/run_demo.py)

CLI script that:
1. Prompts for pitch text and intensity
2. Invokes the graph
3. On each interrupt, prints the persona's thinking + question, prompts for user reply
4. Resumes with `Command(resume=reply)`
5. Prints the final verdict

Used to validate the core loop works before wrapping in Streamlit.

---

### Phase 2: Streamlit Wrapper

Wraps the validated core graph in a full Streamlit UI with streaming.

---

#### [NEW] [app.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/app.py)

Main Streamlit entry point. Manages page routing via `st.session_state`:
- **Login page** → (Phase 3, initially bypassed with a mock user)
- **Connect accounts** → (Phase 4, initially shows "coming soon")
- **Pitch submission** → Pitch text area + intensity selector
- **Live session** → Streaming persona turns
- **Verdict** → Results + PDF download
- **History** → Past sessions

#### [NEW] [ui/pitch.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/ui/pitch.py)

- `st.text_area` for pitch (minimum 50 chars validation)
- `st.select_slider` with options: Light / Normal / Heavy / No Mercy
- Submit button triggers graph invocation
- Stores `thread_id` in `st.session_state`

#### [NEW] [ui/session.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/ui/session.py)

The most complex UI component. For each persona turn:

1. **Header**: Persona name + avatar emoji + round indicator (e.g., "🎯 VC — Round 1/3")
2. **Reasoning pane**: `st.expander("🧠 Reasoning")` with live-updating content
3. **Question pane**: Main area with the persona's challenge, streaming in real-time
4. **Reply box**: `st.text_area` + submit button, appears after question completes
5. **Fallback indicator**: If mid-stream fallback occurs, shows "⚡ Response interrupted, retrying..."

**Streaming implementation**:
- Dedicated async event loop in a background thread (created once per session)
- `graph.astream_events(input, version="v2")` filtered for `on_chat_model_stream` from the active node
- Chunks written to `st.session_state` buffers for thinking/answer
- `st.empty()` containers with `st.markdown()` updates to render progressive text
- On interrupt event, switch from streaming mode to reply-input mode
- On reply submission: `graph.invoke(Command(resume=reply), config)` resumes the graph

#### [NEW] [ui/verdict.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/ui/verdict.py)

- Renders weaknesses as severity-sorted cards/rows
- Color-coded severity (1=green → 5=red)
- Each card shows: issue, severity badge, recommended fix
- "Download PDF" button (wired in Phase 6)

#### [NEW] [ui/components.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/ui/components.py)

Shared components:
- `persona_card(name, emoji, status)` — displays persona identity and current state
- `progress_tracker(state)` — shows overall session progress (which personas done, rounds left, budget used)
- `intensity_badge(level)` — visual indicator of intensity setting

---

### Phase 3: Supabase Layer

Adds persistence, authentication, and session history.

---

#### [NEW] [db/schema.sql](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/db/schema.sql)

Full DDL per §8:
- `sessions` — id (uuid), user_id, pitch_text, intensity, status, round_count, created_at
- `transcript_entries` — id, session_id (FK), persona, round, thinking_text, question_text, user_reply, provider_used, created_at
- `verdicts` — id, session_id (FK), weaknesses (jsonb), pdf_url
- `user_connections` — per §5 exact schema
- `benchmark_corpus` — id, content, embedding (vector(1536)), source, tag

RLS policies:
- `sessions`, `user_connections`: `auth.uid() = user_id`
- `transcript_entries`, `verdicts`: via session_id join to sessions
- `benchmark_corpus`: `SELECT` for all authenticated users (read-only, shared)

#### [NEW] [db/client.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/db/client.py)

Singleton Supabase client initialized from `.env`.

#### [NEW] [db/sessions.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/db/sessions.py)

CRUD for sessions: `create_session()`, `update_session_status()`, `get_user_sessions()`, `get_session()`.

#### [NEW] [db/transcripts.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/db/transcripts.py)

`save_transcript_entry()`, `get_session_transcript()` — called from graph nodes to persist each turn.

#### [NEW] [db/verdicts.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/db/verdicts.py)

`save_verdict()`, `update_pdf_url()`, `get_verdict()`.

#### [NEW] [ui/auth.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/ui/auth.py)

Streamlit login page using Supabase Auth:
- OAuth sign-in (Google) button
- Email/password fallback
- Session token stored in `st.session_state`
- Auth guard decorator for protected pages

#### [NEW] [ui/history.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/ui/history.py)

- Lists past sessions with date, intensity, status
- Click to re-open transcript (read-only)
- Re-download PDF if available

---

### Phase 4: OAuth Connectors

Replaces mock tool calls with real MCP client integrations.

---

#### [NEW] [connectors/oauth.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/connectors/oauth.py)

Generic OAuth flow helper:
- `start_oauth_flow(provider)` → generates auth URL with state param
- `handle_oauth_callback(provider, code, state)` → exchanges code for tokens
- `save_connection(user_id, provider, access_token, refresh_token)` → stores in `user_connections`
- `get_connection(user_id, provider)` → retrieves token
- `refresh_if_needed(connection)` → handles token refresh

#### [MODIFY] [connectors/github_tools.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/connectors/github_tools.py)

Replace MOCK with real GitHub API calls:
- `get_repo_activity(owner, repo)` → commit frequency, repo age, contributor count
- `get_user_repos(username)` → list repos with stars, last commit date
- Bound as LangChain tools on the VC node

#### [MODIFY] [connectors/stripe_tools.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/connectors/stripe_tools.py)

Replace MOCK with real Stripe API calls:
- `get_mrr()` → Monthly Recurring Revenue
- `get_churn_rate()` → Customer churn
- `get_revenue_trend(months)` → Revenue over time

#### [MODIFY] [connectors/sheets_tools.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/connectors/sheets_tools.py)

Replace MOCK with Google Sheets API:
- `get_spreadsheet_data(spreadsheet_id, range)` → fetch financial model data
- `analyze_formulas(spreadsheet_id)` → extract and validate formula logic

#### [MODIFY] [connectors/notion_tools.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/connectors/notion_tools.py)

Replace MOCK with Notion API:
- `search_pages(query)` → find market research pages
- `get_page_content(page_id)` → extract text content

#### [NEW] [ui/connections.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/ui/connections.py)

"Connect accounts" screen:
- Four cards (GitHub, Stripe, Google Sheets, Notion)
- Each shows connected/disconnected status
- Connect button → initiates OAuth flow
- Disconnect button → removes from `user_connections`

---

### Phase 5: RAG (Benchmark Corpus)

---

#### [NEW] [db/rag.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/db/rag.py)

Replace mock retriever with real pgvector similarity search:
- Uses `vecs` library or direct SQL via Supabase client
- `retrieve_benchmarks(query_embedding, top_k=5)` → returns relevant benchmark docs
- Embedding generation via Google's `text-embedding-004` model (free tier, uses `GOOGLE_API_KEY`)

#### [NEW] [seed_corpus.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/seed_corpus.py)

Populates `benchmark_corpus` with curated data:
- SaaS benchmark metrics (median CAC, LTV, churn rates by stage)
- Marketplace benchmark metrics (take rates, GMV/revenue ratios)
- Startup failure post-mortem summaries (CB Insights top-20 reasons, notable case studies)
- Each entry: content text + embedding vector + source URL + tag

---

### Phase 6: Verdict + PDF

---

#### [NEW] [export/pdf.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/export/pdf.py)

PDF generation with `reportlab`:

**Layout:**
1. **Cover page**: "Devil's Advocate Panel — Session Report", date, intensity level
2. **Pitch section**: Full pitch text
3. **Transcript section**: Persona-by-persona, round-by-round:
   - Persona header with emoji
   - "🧠 Reasoning" block (gray background)
   - "Challenge" block (persona's question)
   - "Founder's Reply" block
   - Resolution status
4. **Verdict section**: Severity-ranked table:
   - Severity (color-coded 1-5)
   - Issue description
   - Recommended fix

Upload to Supabase Storage → store URL in `verdicts.pdf_url` → surface download link in UI.

#### [MODIFY] [ui/verdict.py](file:///c:/Users/manoj/Desktop/projects/Devil's%20Advocate%20Panel/ui/verdict.py)

Add functional "Download PDF" button that:
1. Triggers PDF generation via `export/pdf.py`
2. Uploads to Supabase Storage
3. Returns a signed download URL
4. Renders as `st.download_button`

---

## Key Technical Decisions

### Streaming Architecture (Phase 2)

The trickiest integration point. Streamlit is synchronous; LangGraph streaming is async.

**Solution:**
1. Create a dedicated `asyncio` event loop running in a background `threading.Thread`
2. Submit `graph.astream_events()` coroutine to that loop
3. Use a `queue.Queue` to bridge async → sync: async consumer pushes chunks, sync Streamlit code polls
4. Two separate `st.empty()` containers (reasoning expander + question area) update via `st.markdown()` as chunks arrive
5. When an `interrupt` is detected in the event stream, switch the UI to reply-input mode
6. On submit, `graph.invoke(Command(resume=reply), config)` runs synchronously (or via the async loop)

### Fallback with Sticky Provider (Phase 1)

```python
def get_llm_for_session(state: PanelState) -> tuple[BaseChatModel, str]:
    """Returns (llm, provider_name). Respects sticky fallback."""
    if state["active_provider"] == "gemini":
        return gemini_with_retry.with_fallbacks([groq_with_retry]), "gemini"
    elif state["active_provider"] == "groq":
        return groq_with_retry, "groq"
    else:
        # Full chain — will set active_provider on first fallback
        return grok_with_retry.with_fallbacks([gemini_with_retry, groq_with_retry]), "grok"
```

After any invocation, detect which model actually responded (from the response metadata) and update `state["active_provider"]` if it changed.

### Interrupt/Resume in Streamlit (Phase 2)

Each persona turn:
1. Graph runs → hits `interrupt()` → returns the interrupt payload
2. Streamlit renders the question and shows a text input
3. User types reply → clicks submit
4. `graph.invoke(Command(resume=user_reply), config)` resumes the node
5. Node processes reply, potentially marks resolved, appends to transcript
6. Graph continues to `router_node` which decides next step

The `thread_id` (same as session UUID) is stored in `st.session_state` to maintain continuity across Streamlit reruns.

### Error Classification for Retry/Fallback

```python
RETRYABLE_ERRORS = (
    RateLimitError,      # 429
    TimeoutError,        # Timeout
    ConnectionError,     # Network issues
    APIConnectionError,  # Provider down
)

NON_RETRYABLE_ERRORS = (
    AuthenticationError, # 401/403 — bad API key
    BadRequestError,     # 400 — malformed request
    ContentPolicyError,  # Content filter triggered
)
```

`with_retry` is configured with `retry_if_exception_type=RETRYABLE_ERRORS` only.

---

## Verification Plan

### Phase 1 Verification
- Run `run_demo.py` end-to-end with a sample pitch
- Verify all 3 personas ask questions, reasoning is extracted correctly per provider
- Test fallback by using an invalid Grok key → should fall to Gemini
- Test budget cap by setting `MAX_LLM_CALLS=4` → should force early verdict
- Verify `RESOLVED: true/false` parsing works and router respects it

### Phase 2 Verification
- `streamlit run app.py` → submit a pitch → see streaming reasoning + question
- Reply to each persona → verify interrupt/resume cycle works
- Verify fallback UI ("retrying...") by simulating a provider error
- Verify verdict renders correctly after all rounds

### Phase 3 Verification
- Login with Supabase OAuth → verify session persists
- Submit a pitch → verify session/transcript/verdict saved to Supabase
- Check history view loads past sessions correctly
- Verify RLS: user A can't see user B's sessions

### Phase 4 Verification
- Connect GitHub → verify VC persona uses real repo data
- Connect Stripe → verify analyst gets real MRR
- Test without connections → verify personas work on pitch text alone
- Test OAuth token refresh flow

### Phase 5 Verification
- Run `seed_corpus.py` → verify embeddings stored in `benchmark_corpus`
- Submit pitch with financial claims → verify analyst cites relevant benchmarks
- Verify similarity search returns relevant results (not random)

### Phase 6 Verification
- Complete a full session → download PDF
- Verify PDF contains: pitch, full transcript (with reasoning), verdict table
- Verify PDF uploaded to Supabase Storage
- Verify download link works from history view
