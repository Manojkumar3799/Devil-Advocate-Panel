# Deployment Guide — Devil's Advocate Panel

This guide details how to deploy Devil's Advocate Panel to **Streamlit Community Cloud** (or custom hosting) and configure external integrations (Supabase, LLMs, and OAuth connectors).

---

## 1. Secrets Configuration

When deploying to Streamlit Community Cloud:
1. Open your app on [share.streamlit.io](https://share.streamlit.io).
2. Go to **Settings** -> **Secrets**.
3. Copy the contents of [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example) and fill in your production values.

### Essential Variables

| Secret Key | Description | Example / Note |
|---|---|---|
| `APP_BASE_URL` | Public production URL of your deployed app | `https://your-app-name.streamlit.app` (no trailing slash) |
| `SUPABASE_URL` | Supabase project URL | `https://xyzcompany.supabase.co` |
| `SUPABASE_KEY` | Supabase Anon public key | `eyJhbGciOi...` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (optional for client/admin) | `eyJhbGciOi...` |
| `GOOGLE_API_KEY` | Gemini API key (for Market Realist / embeddings) | `AIzaSy...` |
| `XAI_API_KEY` | xAI Grok API key (for VC persona) | `xai-...` |
| `GROQ_API_KEY` | Groq API key (for Financial Analyst persona) | `gsk_...` |
| `TAVILY_API_KEY` | Tavily web search key | `tvly-...` |

---

## 2. Supabase Auth Configuration (Google OAuth)

The primary login is **"Continue with Google"** backed by Supabase Auth.
Depending on your Supabase project settings, authentication may use either **Implicit Flow** (tokens returned in the URL hash `#access_token=...`) or **PKCE Flow** (authorization code returned in query parameters `?code=...`). The app handles both seamlessly.

1. In your **Google Cloud Console** ([console.cloud.google.com](https://console.cloud.google.com)):
   - Under **APIs & Services** -> **Credentials**, create or edit your OAuth 2.0 Web Client ID.
   - Under **Authorized JavaScript origins**, add:
     - `http://localhost:8501` (for local development)
     - `https://your-app-name.streamlit.app` (for production)
     - `https://<YOUR_SUPABASE_PROJECT_ID>.supabase.co`
   - Under **Authorized redirect URIs**, add:
     - `https://<YOUR_SUPABASE_PROJECT_ID>.supabase.co/auth/v1/callback`
     *(Note: Supabase handles the initial OAuth exchange with Google, so Google redirects back to Supabase's callback endpoint).*

2. In your **Supabase Dashboard** ([supabase.com/dashboard](https://supabase.com/dashboard)):
   - Navigate to **Authentication** -> **Providers** -> **Google**:
     - Enable Google provider.
     - Enter your Google Client ID and Google Client Secret from step 1.
   - Navigate to **Authentication** -> **URL Configuration**:
     - **Site URL**: Set to `APP_BASE_URL` (`http://localhost:8501` for local development, or `https://your-app-name.streamlit.app` in production).
     - **Redirect URLs**: Add the wildcard paths so Supabase redirects users back to your app:
       - `http://localhost:8501/**` (local development)
       - `https://your-app-name.streamlit.app/**` (production)

### How the Flows Work Under the Hood:
- **Implicit Flow**: Supabase redirects back to `http://localhost:8501/#access_token=...&refresh_token=...`. Because browsers never send URL hashes to the Streamlit Python server, `ui/auth.py` executes a client-side JavaScript bridge via `st.html(..., unsafe_allow_javascript=True)` to convert the hash to `?sb_access_token=...`, which Streamlit then parses and clears.
- **PKCE Flow**: Supabase redirects back with `?code=...&state=...`. `ui/auth.py` detects the code (verifying state does not belong to third-party connector tools) and calls `client.auth.exchange_code_for_session({"auth_code": code})` to authenticate the user session.

---

## 3. Connector OAuth Applications

For users to link GitHub, Google Sheets, Stripe, or Notion, register OAuth apps with each provider and add the redirect URI:

**Redirect URI pattern:**
The app handles OAuth callbacks directly at its base URL:
```text
https://your-app-name.streamlit.app
```
(During local development: `http://localhost:8501`)

### GitHub OAuth App
- Go to GitHub -> Settings -> Developer Settings -> OAuth Apps -> New OAuth App.
- **Authorization callback URL**: `https://your-app-name.streamlit.app`
- Add `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` to secrets.

### Google Sheets OAuth App
- In Google Cloud Console -> APIs & Services -> Credentials.
- Add `https://your-app-name.streamlit.app` to **Authorized redirect URIs**.
- Ensure the Google Sheets API is enabled.
- Add `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` to secrets.

### Notion OAuth Integration
- Go to [Notion Developers](https://www.notion.so/my-integrations).
- Set Redirect URI to `https://your-app-name.streamlit.app`.
- Add `NOTION_CLIENT_ID` and `NOTION_CLIENT_SECRET` to secrets.

### Stripe Connect (Optional)
- In Stripe Dashboard -> Settings -> Connect -> Integration settings.
- Add Redirect URI: `https://your-app-name.streamlit.app`.
- Add `STRIPE_CLIENT_ID` and `STRIPE_CLIENT_SECRET` to secrets.

---

## 4. Supabase Database Schema

Ensure the schema in [`db/schema.sql`](db/schema.sql) has been executed in the Supabase SQL editor:
- Tables: `pitch_sessions`, `interrogation_transcripts`, `verdicts`, `user_connections`, `benchmark_corpus`.
- pgvector extension and `match_benchmark_corpus` RPC function.

---

## 5. Verification

1. Deploy the repository pointing to `app.py`.
2. Visit the public URL.
3. Click "Continue with Google" to test authentication.
4. Go to **Connect Accounts** and test connecting GitHub or Google Sheets.
5. Submit a pitch and run an interrogation session.
