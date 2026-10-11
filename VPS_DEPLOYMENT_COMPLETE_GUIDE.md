# VPS Deployment Guide: Running Hermes Agent Platform on a Server

**Purpose:** Deploy your Hermes 4-agent system to a VPS (DigitalOcean, Linode, AWS, etc) correctly  
**Status:** Complete step-by-step deployment guide  
**Audience:** You, technical team, DevOps  

---

## Part 1: What We're Deploying

### The System You Built

You have a **FastAPI backend** that runs 4 LangChain agents:

```
Backend (/media/Dman/Hermes/Hermes/backend/)
├── main.py (FastAPI application with 4 agents)
├── requirements.txt (Python dependencies)
├── .env (API keys, database credentials)
├── run.sh (startup script)
└── venv/ (Python virtual environment)

Frontend (separate, Next.js dashboard)
├── Not yet deployed
├── Can be deployed separately to Vercel or same VPS

Database (PostgreSQL)
├── Local (development)
├── Can be AWS RDS or managed database on VPS
```

### What the Backend Does

```
1. FastAPI Server listens on port 8000
   ├── Receives HTTP requests from contractors
   ├── Receives Twilio webhooks (incoming calls)
   └── Exposes REST API

2. Four Agents (LangChain)
   ├── Lead Capture Agent (Twilio integration)
   ├── Quote Generation Agent (database queries)
   ├── Scheduling Agent (calendar/SMS)
   └── Billing Agent (Stripe/QB sync)

3. Database (PostgreSQL)
   ├── Stores leads, quotes, jobs, invoices
   ├── Accessed by all agents via SQLAlchemy ORM
   └── Backs up automatically

4. External Services
   ├── Twilio (phone calls + SMS)
   ├── Stripe (payments)
   ├── QuickBooks (accounting)
   └── OpenAI/Claude (LLM for agents)
```

---

## Part 2: Why Your Previous VPS Attempt Failed (Most Common Errors)

### Error 1: Python/Package Mismatch
```
Problem:
  ❌ VPS has Python 3.10, but requirements.txt needs 3.11+
  ❌ FastAPI version conflicts with LangChain
  ❌ Some packages don't install on Linux (macOS-only)

Solution:
  ✅ Specify exact Python version (3.11+)
  ✅ Use exact dependency versions in requirements.txt
  ✅ Test on Linux locally before deploying
```

### Error 2: Missing Environment Variables
```
Problem:
  ❌ .env file not copied to VPS
  ❌ API keys (OpenAI, Twilio, QB) not set
  ❌ Database URL wrong format

Solution:
  ✅ Never commit .env to git (security risk)
  ✅ Create .env on VPS via SSH after deploy
  ✅ Use environment secrets on VPS (AWS Secrets Manager, etc)
```

### Error 3: Database Not Ready
```
Problem:
  ❌ PostgreSQL not installed on VPS
  ❌ Database migrations not run
  ❌ Connection string wrong (localhost vs. RDS endpoint)

Solution:
  ✅ Use managed PostgreSQL (AWS RDS, Heroku Postgres) = no setup
  ✅ Or install PostgreSQL on VPS + run migrations
  ✅ Test connection before starting FastAPI
```

### Error 4: Port Binding Issues
```
Problem:
  ❌ FastAPI tries to bind port 8000, but it's already in use
  ❌ Firewall blocks port 8000 (not open to public)
  ❌ Running as wrong user (permission denied)

Solution:
  ✅ Use port 8000 internally, reverse proxy from 80/443
  ✅ Open firewall: sudo ufw allow 80/tcp 443/tcp
  ✅ Run FastAPI as non-root user (systemd service)
```

### Error 5: Long-Running Processes Crash
```
Problem:
  ❌ FastAPI crashes, stays down
  ❌ Agent processes hang waiting for LLM response
  ❌ No monitoring = you don't know it's down

Solution:
  ✅ Use systemd service (auto-restart on crash)
  ✅ Add timeout on LLM calls (don't wait forever)
  ✅ Use supervisord or PM2 for process management
```

---

## Part 3: Correct VPS Deployment (Step-by-Step)

### Step 1: Choose Your VPS Provider

**Recommended (easiest):**
- **Railway.app** — Deploy from GitHub, auto-scales, managed postgres
- **Render.com** — Similar to Railway, free tier available
- **Fly.io** — Global deployment, fast API responses

**Traditional (more control):**
- **DigitalOcean App Platform** — Managed container deployment
- **AWS EC2 + RDS** — Full control, more complex
- **Linode** — Simple Linux VPS

**My recommendation for you:** Start with **Railway** or **Render** (5-10 min deploy, no server management).

---

### Step 2: Prepare Your Code for Deployment

#### 2a. Fix requirements.txt

Current file: `/media/Dman/Hermes/Hermes/backend/requirements.txt`

```bash
# Check what's actually installed
cd /media/Dman/Hermes/Hermes/backend
source venv/bin/activate
pip freeze > requirements_current.txt
```

**Expected output:**
```
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
sqlalchemy==2.0.23
pydantic==2.5.0
langchain==0.1.0
langchain-openai==0.0.6
twilio==8.10.0
stripe==7.4.0
python-multipart==0.0.6
```

**Important:** Pin exact versions (not >=). Example:

```bash
# WRONG:
fastapi>=0.100

# RIGHT:
fastapi==0.104.1
```

#### 2b. Create .env.example (without secrets)

File: `/media/Dman/Hermes/Hermes/backend/.env.example`

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hermes
# On VPS: postgresql://user:password@rds-endpoint.amazonaws.com:5432/hermes

# API Keys (get from services, never commit real keys)
OPENAI_API_KEY=sk-xxx (replace with placeholder)
TWILIO_ACCOUNT_SID=AC_xxx
TWILIO_AUTH_TOKEN=xxx
STRIPE_API_KEY=sk_live_xxx
QUICKBOOKS_CLIENT_ID=xxx
QUICKBOOKS_CLIENT_SECRET=xxx

# App Settings
DEBUG=False
ALLOWED_HOSTS=localhost,yourdomain.com
```

#### 2c. Update main.py for Production

Open `/media/Dman/Hermes/Hermes/backend/main.py`

Find this section:

```python
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, debug=True)
```

Change to:

```python
if __name__ == "__main__":
    # Production: listen on all interfaces (0.0.0.0), not just localhost
    uvicorn.run(
        app,
        host="0.0.0.0",  # Listen on all IPs (will be proxied via Nginx)
        port=8000,
        debug=False,  # Never debug in production
        workers=4,  # Multiple worker processes
    )
```

#### 2d. Add Health Check Endpoint

Add this to main.py (before the agents routes):

```python
@app.get("/health")
def health_check():
    """Verify app is running"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
```

VPS will ping this to confirm the app is alive.

---

### Step 3: Set Up Database

#### Option A: Managed PostgreSQL (Easiest, Recommended)

**On Railway/Render:**
1. Click "Add Service" → "PostgreSQL"
2. They create the database automatically
3. Give you a connection string like:
   ```
   postgresql://user:password@db-endpoint.railway.app:5432/hermes
   ```
4. Copy this into your .env file (on VPS, not in git)

**On AWS RDS:**
1. Create RDS PostgreSQL instance
2. Get endpoint: `hermes-db.123456.us-east-1.rds.amazonaws.com`
3. Connection string:
   ```
   postgresql://admin:password@hermes-db.123456.us-east-1.rds.amazonaws.com:5432/hermes
   ```

#### Option B: PostgreSQL on Your VPS (More Work)

```bash
# SSH into your VPS
ssh ubuntu@your-vps-ip

# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on reboot

# Create database
sudo -u postgres psql -c "CREATE DATABASE hermes;"
sudo -u postgres psql -c "CREATE USER hermes_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "ALTER ROLE hermes_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hermes TO hermes_user;"

# Connection string for .env
DATABASE_URL=postgresql://hermes_user:secure_password@localhost:5432/hermes
```

#### 3c. Run Database Migrations

If using SQLAlchemy ORM (most likely):

```python
# In main.py, run this on startup:
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# This creates all tables defined in your models
Base.metadata.create_all(bind=engine)
```

**Better approach:** Use Alembic for migrations (but skip for now if it's not in your repo).

---

### Step 4: Deploy to Railway (Simplest Example)

#### 4a. Prepare Your Repo

```bash
cd /media/Dman/Hermes/Hermes

# Make sure you have a git repo
git init
git add -A
git commit -m "Initial commit: Hermes backend ready for deployment"

# Create GitHub repo (public is fine for now, make private later)
# Then push to GitHub
git remote add origin https://github.com/yourusername/hermes-backend
git push -u origin main
```

#### 4b. Connect Railway

1. Go to **railway.app**
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub Repo"
5. Choose your `hermes-backend` repo
6. Railway auto-detects Python + FastAPI
7. Click "Deploy"

#### 4c. Add Environment Variables

In Railway dashboard:

1. Go to your project → Variables
2. Add each var from your `.env`:
   ```
   OPENAI_API_KEY = sk-xxx
   TWILIO_ACCOUNT_SID = AC_xxx
   DATABASE_URL = (auto-created if you added PostgreSQL)
   ... etc
   ```
3. Click "Deploy" (redeploy with new vars)

#### 4d. Check Deployment Status

Railway shows:
- Logs (if there's an error, you'll see it)
- Health status
- URL where your app is live (e.g., `https://hermes-backend.railway.app`)

Test it:

```bash
curl https://hermes-backend.railway.app/health
# Should return: {"status":"ok","timestamp":"2026-10-08T..."}
```

---

### Step 5: Configure Reverse Proxy (If Using Traditional VPS)

If using DigitalOcean droplet or AWS EC2 (not Railway), you need Nginx to:
- Listen on ports 80/443
- Forward requests to FastAPI (port 8000)
- Handle SSL certificates

#### 5a. Install Nginx

```bash
sudo apt update
sudo apt install nginx

sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 5b. Configure Nginx

Create `/etc/nginx/sites-available/hermes`:

```nginx
upstream fastapi {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 5c. Enable and Test

```bash
sudo ln -s /etc/nginx/sites-available/hermes /etc/nginx/sites-enabled/
sudo nginx -t  # Test config
sudo systemctl restart nginx
```

#### 5d. Add SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# Auto-renew certificates
sudo systemctl enable certbot.timer
```

---

### Step 6: Run FastAPI as a Service (If on Traditional VPS)

Create `/etc/systemd/system/hermes.service`:

```ini
[Unit]
Description=Hermes FastAPI Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/ubuntu/hermes-backend
Environment="PATH=/home/ubuntu/hermes-backend/venv/bin"
ExecStart=/home/ubuntu/hermes-backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Auto-restart if it crashes
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable hermes
sudo systemctl start hermes

# Check status
sudo systemctl status hermes

# View logs
sudo journalctl -u hermes -f
```

---

## Part 4: Configure External Services

### Twilio Webhook Setup

Your Hermes backend receives calls via Twilio webhooks. Tell Twilio where to send them:

1. Go to **twilio.com** → Manage your account
2. Phone Numbers → Active numbers
3. Click your number
4. **Voice & Fax** section → "A Call Comes In"
5. Set webhook URL:
   ```
   https://yourdomain.com/api/twilio/incoming-call
   ```
6. Method: POST
7. Save

**Test it:**

```bash
curl -X POST https://yourdomain.com/api/twilio/incoming-call \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=%2B12505551234&To=%2B12505555678&CallSid=CA_test123"
```

### OpenAI API Key

1. Go to **platform.openai.com** → API keys
2. Create new key
3. Copy to `.env` on VPS:
   ```
   OPENAI_API_KEY=sk-xxx
   ```

### Stripe API Keys

1. Go to **dashboard.stripe.com** → Developers → API keys
2. Copy:
   - Publishable key (frontend)
   - Secret key (backend)
3. Add to `.env` on VPS:
   ```
   STRIPE_API_KEY=sk_live_xxx
   STRIPE_PUBLISHABLE_KEY=pk_live_xxx
   ```

### QuickBooks OAuth (Optional)

For QB sync, you need to set up OAuth:

1. Go to **developer.intuit.com**
2. Create app
3. Get Client ID + Secret
4. Add to `.env`:
   ```
   QUICKBOOKS_CLIENT_ID=xxx
   QUICKBOOKS_CLIENT_SECRET=xxx
   ```

---

## Part 5: Test Your Deployment

### 5a. Test API Endpoints

```bash
# Health check
curl https://yourdomain.com/health

# Create a test lead (simulating incoming call)
curl -X POST https://yourdomain.com/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Customer",
    "phone": "250-555-1234",
    "service_type": "plumbing"
  }'

# Get leads
curl https://yourdomain.com/api/leads
```

### 5b. Test Twilio Integration

```bash
# Trigger a test call from Twilio dashboard
# Check your logs to see if Hermes captured it

# View logs (Railway)
# Look in your Railway dashboard

# View logs (VPS with systemd)
sudo journalctl -u hermes -f --lines 50
```

### 5c. Test Database Connection

```bash
# SSH into VPS
ssh ubuntu@your-vps-ip

# Connect to database
psql postgresql://hermes_user:password@localhost:5432/hermes

# List tables
\dt

# Check leads table
SELECT * FROM leads;
```

### 5d. Test Agent Workflows

```bash
# Simulate a complete workflow:
# 1. Send incoming call event
# 2. Check if Lead Capture Agent captured it
# 3. Request a quote
# 4. Check if Quote Generation Agent created it
# 5. Request scheduling
# 6. Check if Scheduling Agent booked it

curl -X POST https://yourdomain.com/api/test-workflow
# Should return: {"status": "success", "leads": 1, "quotes": 1, "jobs": 1}
```

---

## Part 6: Monitoring & Troubleshooting

### 6a. Real-Time Logs

**Railway:**
```
Go to project → Deployments → View logs
```

**VPS:**
```bash
sudo journalctl -u hermes -f
# Or tail a log file if using one
tail -f /var/log/hermes.log
```

### 6b. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'fastapi'` | Package not installed | `pip install -r requirements.txt` |
| `psycopg2.OperationalError: could not connect to server` | Database down or wrong URL | Check `DATABASE_URL` in .env |
| `OPENAI_API_KEY not found` | Missing environment variable | Add to VPS secrets, redeploy |
| `Connection refused on port 8000` | FastAPI not running | Check systemd status: `systemctl status hermes` |
| `413 Request Entity Too Large` | Nginx body size limit | Increase: `client_max_body_size 100M;` in nginx.conf |
| `502 Bad Gateway` | FastAPI crashed or hung | Check logs: `journalctl -u hermes -f` |

### 6c. Performance Monitoring

```bash
# SSH into VPS

# Check CPU/Memory usage
top  # or htop if installed

# Check disk space
df -h

# Check which process is using most memory
ps aux | grep uvicorn

# Check FastAPI worker count
ps aux | grep "uvicorn main:app" | wc -l
```

---

## Part 7: Update & Maintenance

### 7a. Deploy New Code

**Railway:**
```
1. Push changes to GitHub
2. Railway auto-detects and redeploys
3. Check Deployments tab for status
```

**VPS:**
```bash
# SSH into VPS
cd /home/ubuntu/hermes-backend

# Pull latest code
git pull origin main

# Restart FastAPI
sudo systemctl restart hermes

# Check logs
sudo journalctl -u hermes -f
```

### 7b. Backup Database

**Managed PostgreSQL (Railway/RDS):**
- Automated backups included
- Check your provider's dashboard for restore options

**VPS PostgreSQL:**
```bash
# Manual backup
pg_dump -U hermes_user hermes > backup.sql

# Restore from backup
psql -U hermes_user hermes < backup.sql
```

### 7c. Update Dependencies

```bash
# Test locally first
pip install --upgrade -r requirements.txt
# Make sure nothing breaks

# Then update on VPS
ssh ubuntu@your-vps
cd /home/ubuntu/hermes-backend
pip install --upgrade -r requirements.txt
sudo systemctl restart hermes
```

---

## Part 8: Why the Desktop UI is Better (And How to Keep It)

### The Desktop App vs. Server Version

**Desktop Hermes (what you built):**
- ✅ Beautiful UI (you designed it)
- ✅ Runs locally (no server hassle)
- ✅ No deployment headaches
- ❌ Only works on your computer
- ❌ Can't scale to multiple users

**Server/Web Version (what keeps failing):**
- ✅ Accessible from anywhere
- ✅ Scalable to multiple contractors
- ✅ Mobile-friendly
- ❌ UI is generic/web-based
- ❌ Deployment is complex

### Solution: Keep the Desktop UI, Add Remote Backend

You can:
1. **Keep your beautiful desktop UI** (running locally)
2. **Connect it to the remote backend** (on VPS)
3. **Get the best of both worlds**

How it works:

```
Your Computer (Desktop App)
  ↓ (sends API requests to)
  → VPS (FastAPI backend on yourdomain.com)
     ↓ (stores data in)
     → Database (PostgreSQL on VPS)

Result: Your nice desktop UI talks to a remote backend
```

**Configuration:**
In your desktop app, change:
```python
# OLD (local backend)
API_URL = "http://localhost:8000"

# NEW (remote backend)
API_URL = "https://yourdomain.com"
```

Then:
- You get your beautiful UI ✅
- Backend runs on VPS for all contractors ✅
- Contractors can also use a web dashboard (separate, simpler UI) ✅

---

## Summary: Your Correct Deployment Path

1. **Fix code** (requirements.txt pinned, .env.example created)
2. **Choose provider** (Railway recommended for simplicity)
3. **Push to GitHub**
4. **Deploy to Railway** (click one button)
5. **Add environment variables** (API keys on VPS, not in git)
6. **Configure Twilio webhook** (tell Twilio where backend lives)
7. **Test workflow** (call API, check logs, verify database)
8. **Connect desktop UI** (change API_URL to your VPS domain)
9. **Monitor & troubleshoot** (check logs if issues arise)

**Time to deploy:** 30-60 minutes for first time, 5 minutes for updates

---

## Files to Create/Update

Create in your repo:

```
/media/Dman/Hermes/Hermes/backend/

1. requirements.txt (updated with pinned versions)
2. .env.example (no secrets, just placeholders)
3. main.py (updated for production)
4. Dockerfile (optional, but recommended)
5. docker-compose.yml (optional, for local testing)
6. .gitignore (never commit .env or venv/)
```

Do NOT commit to git:
```
.env (secrets only go on VPS via environment variables)
venv/ (auto-created locally)
__pycache__/ (auto-generated)
*.pyc (auto-generated)
```

---

## Next Steps

1. **Read your current `/media/Dman/Hermes/Hermes/backend/main.py`** — understand what agents do
2. **Fix requirements.txt** — pin all versions exactly
3. **Create .env.example** — placeholder for all secrets
4. **Choose Railway or Render** — sign up, connect GitHub
5. **Deploy** — click one button, let it build
6. **Test** — curl the API endpoints
7. **Configure Twilio** — point webhook to your VPS URL

Questions? I can walk through any of these steps in detail. What would you like to tackle first?
