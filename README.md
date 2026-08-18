# ⚡ Supabase Full-Stack CRUD App (Database + Storage + 3 Edge Functions + UI)

A full-featured Python & Supabase CRUD application featuring Postgres Database CRUD, Supabase Storage Object CRUD, 3 Deno Edge Functions, an interactive Terminal CLI, and a Streamlit Web Dashboard ready for Streamlit Cloud deployment.

---

## 🌟 Features & Deliverables

- **Postgres Database CRUD**: Full Create, Read, Update, and Delete operations for custom database tables (`database_items`, `files_metadata`, `audit_logs`).
- **Supabase Storage CRUD**: Upload, download, update metadata, generate secure time-limited Signed URLs, and delete files in the `documents` storage bucket.
- **3 Serverless Deno Edge Functions**:
  1. `file-validator-processor` (Primary): Validates file size (max 10MB), checks allowed MIME extensions, and computes SHA-256 checksums on the server.
  2. `doc-summarizer` (Extra 1): Extracts text, character/word metrics, and generates automatic summary snippets for uploaded document files.
  3. `audit-logger` (Extra 2): Generates temporary Signed Storage URLs and records access events into an immutable Postgres `audit_logs` table.
- **Interactive Terminal CLI (`cli_app.py`)**: Menu-driven terminal interface powered by `rich`.
- **Streamlit Web UI Dashboard (`ui/app.py`)**: Multi-tab web dashboard for drag-and-drop file storage management, DB table grid editing, Edge Functions live testing room, and audit activity stream.

---

## 📁 Project Structure

```
D:\Dev\supabase-crud-app\
├── .env                        # Local secrets file (SUPABASE_URL, keys)
├── .env.example                # Template for environment credentials
├── .gitignore                  # Git ignore configuration
├── requirements.txt            # Python package dependencies
├── README.md                   # Complete documentation & deployment guide
├── supabase_config/            # Supabase Server & Edge Function configs
│   ├── schema.sql              # Database DDL script for tables & RLS policies
│   ├── config.toml             # Supabase CLI configuration
│   └── functions/
│       ├── file-validator-processor/ # Edge Function 1: File Validator
│       ├── doc-summarizer/           # Edge Function 2: Document Summarizer
│       └── audit-logger/             # Edge Function 3: Download Audit Logger
├── python_client/
│   ├── config.py               # Supabase Client setup (supports .env & st.secrets)
│   ├── db_crud.py              # Postgres Database CRUD handler
│   ├── storage_crud.py         # Storage Bucket CRUD & Metadata Sync
│   └── edge_invoker.py         # Deno Edge Functions invoker
├── cli_app.py                  # Interactive Terminal CLI Application
└── ui/
    └── app.py                  # Streamlit Web Dashboard UI
```

---

## 🚀 Setup & Installation

### 1. Install Dependencies

```bash
cd D:\Dev\supabase-crud-app
pip install -r requirements.txt
```

---

### 2. Configure Credentials (`.env`)

Copy `.env.example` to `.env` and fill in your Supabase credentials from your [Supabase Project API Settings](https://app.supabase.com/project/_/settings/api):

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=documents
```

---

### 3. Initialize Supabase Database Tables (`schema.sql`)

1. Open your project on the [Supabase Dashboard](https://app.supabase.com/).
2. Navigate to **SQL Editor** -> **New Query**.
3. Copy and paste the contents of `supabase_config/schema.sql`.
4. Click **Run** to create tables (`files_metadata`, `database_items`, `audit_logs`), triggers, RLS policies, and the `documents` storage bucket.

---

### 4. Deploy Deno Edge Functions via Supabase CLI

To deploy the 3 Edge Functions to your live Supabase project:

```bash
# 1. Login to Supabase CLI
npx supabase login

# 2. Link to your Supabase Project
npx supabase link --project-ref your-project-ref

# 3. Deploy all 3 Edge Functions
npx supabase functions deploy file-validator-processor --no-verify-jwt --workdir supabase_config
npx supabase functions deploy doc-summarizer --no-verify-jwt --workdir supabase_config
npx supabase functions deploy audit-logger --no-verify-jwt --workdir supabase_config
```

---

## 💻 Running the Terminal CLI Application

Run the interactive terminal app:

```bash
python cli_app.py
```

---

## 🖥️ Running the Streamlit Web UI

Run the Streamlit web dashboard locally:

```bash
streamlit run ui/app.py
```

Open `http://localhost:8501` in your web browser.

---

## ☁️ Deploying Streamlit UI to Streamlit Cloud

1. Push your repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Supabase CRUD App"
   git remote add origin https://github.com/your-username/supabase-crud-app.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io/) and create a **New App**.
3. Select your repository and set Main File Path to: `ui/app.py`.
4. Under **Advanced Settings** -> **Secrets**, paste your credentials:
   ```toml
   SUPABASE_URL = "https://your-project-ref.supabase.co"
   SUPABASE_ANON_KEY = "your-anon-public-key"
   SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"
   SUPABASE_STORAGE_BUCKET = "documents"
   ```
5. Click **Deploy!**
