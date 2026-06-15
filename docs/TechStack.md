# MediaSense — Tech Stack Installation Guide

**Platform:** Windows 11
**Last verified:** June 2026

---

## 1. Prerequisites

### 1.1 Python 3.12

1. Download from https://www.python.org/downloads/ → Python 3.12.x (latest patch)
2. Run installer — check **"Add python.exe to PATH"** and **"Install for all users"**
3. Verify:
```powershell
python --version   # Python 3.12.x
pip --version      # pip 24.x
```

### 1.2 Node.js 24 LTS

1. Download from https://nodejs.org/en/download → **LTS** installer (24.x)
2. Run installer with defaults
3. Verify:
```powershell
node --version   # v24.x.x
npm --version    # 10.x.x
```

### 1.3 Git

1. Download from https://git-scm.com/download/win → **64-bit Git for Windows**
2. Install with defaults (Git Bash included)
3. Verify:
```powershell
git --version   # git version 2.4x.x
```

---

## 2. Python Environment Setup

```powershell
# From the project root
cd "D:\SS\AI\MediaSentimentAnalysis - CC\backend"
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verify key packages:
```powershell
python -c "import fastapi; print(fastapi.__version__)"   # 0.115.x
python -c "import feedparser; print(feedparser.__version__)"  # 6.0.x
python -c "from google import genai; print('Gemini OK')"
python -c "from groq import Groq; print('Groq OK')"
```

### requirements.txt (current pinned versions)

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic-settings==2.6.1
feedparser==6.0.11
httpx==0.27.2
google-genai==1.12.1
groq==0.13.1
supabase==2.10.0
influxdb-client==1.45.0
boto3==1.35.74
redis==5.2.1
APScheduler==3.10.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.12
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-mock==3.14.0
```

### fasttext Installation (Windows — special step)

`fasttext` has no official Windows wheel. Install the pre-built wheel:

```powershell
pip install fasttext-wheel
```

If that fails, install via the unofficial Windows wheel:
```powershell
pip install fasttext-wheel==0.9.2
```

Verify:
```powershell
python -c "import fasttext; print('fasttext OK')"
```

### Download fasttext Language Model

```powershell
# Run once from the backend/ directory
python -c "
import urllib.request, os, pathlib
models_dir = pathlib.Path('models')
models_dir.mkdir(exist_ok=True)
dest = models_dir / 'lid.176.bin'
if not dest.exists():
    print('Downloading fasttext lid.176.bin (~900MB)...')
    urllib.request.urlretrieve(
        'https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin',
        str(dest)
    )
    print('Done:', dest)
else:
    print('Already exists:', dest)
"
```

---

## 3. External Service Setup

### 3.1 Supabase (Free — PostgreSQL + Auth + Storage)

1. Go to https://supabase.com → **Start your project** → Sign in with GitHub
2. Click **New Project** → choose **Free plan**
   - Project name: `mediasense`
   - Database password: generate and save securely
   - Region: **South Asia (ap-south-1)** → Singapore is closest available
3. Wait ~2 minutes for project to provision
4. Go to **Settings → API**:
   - Copy **Project URL** → `SUPABASE_URL`
   - Copy **anon public** key → `SUPABASE_ANON_KEY`
   - Copy **service_role** key → `SUPABASE_SERVICE_ROLE_KEY`
5. Go to **SQL Editor** → run `supabase/migrations/001_schema.sql` then `002_rls.sql`
6. Verify in **Table Editor** — you should see: `agencies`, `brands`, `brand_configs`, `user_roles`, `articles`, `dedupe_hashes`

**Install Supabase CLI (optional, for local dev):**
```powershell
npm install -g supabase
supabase --version   # 2.x.x
```

---

### 3.2 InfluxDB Cloud (Free — Time-Series DB)

1. Go to https://cloud2.influxdata.com/signup → Sign up free
2. Choose **AWS** → **us-east-1** (or any region)
3. Choose **Free Plan** (10GB writes/month, 30-day retention)
4. After sign-in → **Load Data → API Tokens**:
   - Click **Generate API Token → All Access Token**
   - Copy token → `INFLUXDB_TOKEN`
5. Copy your **Org name** (shown top-left) → `INFLUXDB_ORG`
6. Copy the **URL** from browser address bar (e.g., `https://us-east-1-1.aws.cloud2.influxdata.com`) → `INFLUXDB_URL`
7. Go to **Buckets → Create Bucket**:
   - Name: `mediasense`
   - Retention: **30 days**
   - Click Create
8. Set `INFLUXDB_BUCKET=mediasense`

Verify Python connection:
```python
from influxdb_client import InfluxDBClient
c = InfluxDBClient(url="YOUR_URL", token="YOUR_TOKEN", org="YOUR_ORG")
print(c.ping())   # True
```

---

### 3.3 Cloudflare R2 (Free — Object Storage)

1. Go to https://dash.cloudflare.com → Sign up free (requires phone verification)
2. In left sidebar → **R2 Object Storage → Create bucket**
   - Bucket name: `mediasense-raw`
   - Location: **Automatic**
   - Click **Create bucket**
3. Go to **R2 → Manage R2 API Tokens**:
   - Click **Create API token**
   - Token name: `mediasense-backend`
   - Permissions: **Object Read & Write**
   - Specify bucket: `mediasense-raw`
   - Click **Create API Token**
   - Copy **Access Key ID** → `R2_ACCESS_KEY_ID`
   - Copy **Secret Access Key** → `R2_SECRET_ACCESS_KEY`
4. From the R2 overview page, copy your **Account ID** (top-right) → `R2_ACCOUNT_ID`

Verify Python connection:
```python
import boto3
s3 = boto3.client("s3",
    endpoint_url="https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com",
    aws_access_key_id="YOUR_KEY",
    aws_secret_access_key="YOUR_SECRET",
    region_name="auto",
)
print(s3.list_buckets())  # should show mediasense-raw
```

---

### 3.4 Upstash Redis (Free — Job Queue)

1. Go to https://console.upstash.com → Sign up free with GitHub
2. Click **Create Database**:
   - Name: `mediasense-queue`
   - Type: **Regional**
   - Region: **ap-south-1 (Mumbai)**
   - Enable **TLS** ✓
   - Click **Create**
3. In the database details page:
   - Copy **Endpoint** → `UPSTASH_REDIS_HOST`
   - Copy **Port** → `UPSTASH_REDIS_PORT` (usually `6379`)
   - Copy **Password** → `UPSTASH_REDIS_PASSWORD`

Verify:
```python
import redis
r = redis.Redis(host="YOUR_HOST", port=6379, password="YOUR_PASS", ssl=True, decode_responses=True)
r.set("test", "ok")
print(r.get("test"))   # ok
```

---

### 3.5 Google Gemini API Key

You already have a Gemini API key. If you need to verify or create:

1. Go to https://aistudio.google.com/app/apikey
2. Click **Create API Key** → select a Google Cloud project or create new
3. Copy the key → `GEMINI_API_KEY`
4. Verify free tier limits: **1,500 requests/day**, **1M tokens/min** for Gemini 2.0 Flash

Verify:
```python
from google import genai
client = genai.Client(api_key="YOUR_KEY")
resp = client.models.generate_content(model="gemini-2.0-flash", contents="Say OK")
print(resp.text)   # OK
```

---

### 3.6 Groq API Key (Free — Fallback NLP)

1. Go to https://console.groq.com → Sign up free
2. Go to **API Keys → Create API Key**
   - Name: `mediasense-fallback`
   - Copy key → `GROQ_API_KEY`
3. Free tier: **6,000 requests/day** for `gemma2-9b-it`, **14,400/day** for `llama-3.1-8b-instant`

Verify:
```python
from groq import Groq
client = Groq(api_key="YOUR_KEY")
resp = client.chat.completions.create(
    model="gemma2-9b-it",
    messages=[{"role": "user", "content": "Say OK"}],
)
print(resp.choices[0].message.content)   # OK
```

---

### 3.7 Railway (Free — Backend Hosting)

1. Go to https://railway.app → Sign in with GitHub
2. Click **New Project → Empty Project**
3. Install CLI:
```powershell
npm install -g @railway/cli
railway login
```
4. In your `backend/` directory:
```powershell
railway init   # links local dir to Railway project
```
5. Set environment variables:
```powershell
railway variables set SUPABASE_URL="https://xxx.supabase.co"
railway variables set SUPABASE_ANON_KEY="eyJ..."
railway variables set SUPABASE_SERVICE_ROLE_KEY="eyJ..."
railway variables set INFLUXDB_URL="https://..."
railway variables set INFLUXDB_TOKEN="..."
railway variables set INFLUXDB_ORG="..."
railway variables set INFLUXDB_BUCKET="mediasense"
railway variables set R2_ACCOUNT_ID="..."
railway variables set R2_ACCESS_KEY_ID="..."
railway variables set R2_SECRET_ACCESS_KEY="..."
railway variables set UPSTASH_REDIS_HOST="..."
railway variables set UPSTASH_REDIS_PORT="6379"
railway variables set UPSTASH_REDIS_PASSWORD="..."
railway variables set GEMINI_API_KEY="..."
railway variables set GROQ_API_KEY="..."
railway variables set SECRET_KEY="your-32-char-random-string"
railway variables set ENVIRONMENT="production"
```
6. Deploy:
```powershell
railway up
```
7. After deploy, get your URL:
```powershell
railway status   # shows https://xxx.up.railway.app
```

---

### 3.8 Vercel (Free — Frontend Hosting)

1. Go to https://vercel.com → Sign in with GitHub
2. Install CLI:
```powershell
npm install -g vercel
vercel login
```
3. In `frontend/` directory, create `.env.production`:
```
VITE_API_URL=https://your-backend.up.railway.app
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_BRAND_ID=paste-a-brand-uuid-after-creating-one
```
4. Deploy:
```powershell
cd frontend
vercel --prod
```
5. Set environment variables in Vercel dashboard:
   - **Project Settings → Environment Variables** → add all `VITE_*` vars above

---

## 4. Local Development Setup

### 4.1 Backend (FastAPI dev server)

```powershell
cd backend
venv\Scripts\activate
cp .env.example .env        # fill in real values
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive API docs.

### 4.2 Frontend (Vite dev server)

```powershell
cd frontend
cp .env.example .env.local  # VITE_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173

### 4.3 Run tests

```powershell
cd backend
venv\Scripts\activate
pytest tests/ -v
```

---

## 5. Environment Variables Reference

Create `backend/.env` by copying `.env.example` and filling in all values:

| Variable | Where to get it |
|---|---|
| `SUPABASE_URL` | Supabase → Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Supabase → Settings → API → anon public |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → service_role |
| `INFLUXDB_URL` | InfluxDB Cloud browser URL |
| `INFLUXDB_TOKEN` | InfluxDB Cloud → API Tokens |
| `INFLUXDB_ORG` | InfluxDB Cloud org name (top-left) |
| `INFLUXDB_BUCKET` | `mediasense` |
| `R2_ACCOUNT_ID` | Cloudflare dashboard → top-right |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 → API Tokens |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 → API Tokens |
| `UPSTASH_REDIS_HOST` | Upstash console → Endpoint |
| `UPSTASH_REDIS_PORT` | Upstash console → Port (6379) |
| `UPSTASH_REDIS_PASSWORD` | Upstash console → Password |
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey |
| `GROQ_API_KEY` | https://console.groq.com → API Keys |
| `SECRET_KEY` | Any 32+ char random string |
| `ENVIRONMENT` | `development` or `production` |

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `fasttext` import error on Windows | Use `pip install fasttext-wheel` instead of `fasttext` |
| `ValueError: Unable to avoid copy` from fasttext | `fasttext-wheel` is incompatible with NumPy 2.x. Run `pip install "numpy<2.0"` |
| `ModuleNotFoundError: app` in pytest | Run pytest from `backend/` with venv activated |
| Supabase RLS blocking queries | Use `service_role_key` (not `anon_key`) in backend |
| InfluxDB `401 Unauthorized` | Token needs **All Access** or **Write** permission to bucket |
| R2 `SignatureDoesNotMatch` | Ensure `region_name="auto"` in boto3 client |
| Upstash `SSL WRONGVERSION` | Set `ssl=True` in redis.Redis() |
| Railway deploy fails | Ensure `Procfile` exists in `backend/` and `PORT` env var is used |
| Vercel blank page | Check `VITE_API_URL` does not have trailing slash |
| Gemini 429 rate limit | Batching: pass 2-3 articles per request; Groq fallback activates automatically |
