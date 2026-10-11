# QUICK START: Hermes on Hostinger + 11 Labs Setup

**Goal:** Get Lead Capture Agent live on Hostinger in 1 week.

**Time Required:** ~50 hours (20-30 distributed)

**Status:** All code ready. Just deploy.

---

## Prerequisites Checklist

```
☐ Hostinger account (hostinger.com)
  - Get: VPS with Ubuntu 22.04, 2GB RAM
  - Cost: $5-10/month
  - Get: SSH login credentials
  
☐ Twilio account (twilio.com)
  - Get: Canadian phone number (250-555-XXXX)
  - Get: Account SID
  - Get: Auth Token
  - Cost: $1-2/month phone + pay-as-you-go calls
  
☐ 11 Labs account (elevenabs.io)
  - Get: API key
  - Cost: Free tier (limited) or $5-11/month
  
☐ OpenAI API key (platform.openai.com)
  - Get: API key
  - Cost: ~$5-20/month (pay-as-you-go)
  
☐ Stripe account (stripe.com) - for later
  - Get: API key
  - Cost: 2.9% + $0.30 per transaction
  
☐ Git setup (on your laptop)
  - Installed: git
  - SSH key configured
```

---

## STEP 1: Hostinger VPS Setup (30 minutes)

```bash
# 1. Go to hostinger.com
# 2. VPS → Create VPS
#    Select: Ubuntu 22.04 LTS
#    RAM: 2GB (minimum)
#    vCPU: 1
#    Storage: 50GB
#    Cost: $5/month
# 3. Click Create
# 4. Wait 5 minutes for VPS to boot
# 5. Get: IP address (e.g., 192.168.1.100) and SSH credentials

# 6. SSH into VPS (from your laptop)
ssh root@192.168.1.100
# Enter password when prompted

# 7. Update system
apt update && apt upgrade -y

# 8. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker --version  # Should return: Docker version X.X.X

# 9. Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version  # Should work

# 10. Create app directory
mkdir -p /var/www/hermes
cd /var/www/hermes

# DONE: VPS ready
```

---

## STEP 2: Clone Code & Setup Environment (15 minutes)

```bash
# Still SSH'd into Hostinger

# 1. Clone your repo (if on GitHub)
# If not on GitHub yet, copy files manually:
# 1a. Upload files via SFTP or FTP
#     Or push to GitHub first, then clone

# Assuming on GitHub:
git clone https://github.com/yourusername/hermes.git /var/www/hermes
cd /var/www/hermes/backend

# 2. Create .env file with your API keys
cat > .env << 'EOF'
# OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Twilio
TWILIO_ACCOUNT_SID=AC_your_sid
TWILIO_AUTH_TOKEN=your_auth_token

# 11 Labs (we'll add in Week 2)
ELEVEN_LABS_API_KEY=your_api_key

# Stripe (for later)
STRIPE_API_KEY=sk_test_your_key

# Database (we'll add in Week 2)
DATABASE_URL=postgresql://hermes:password@localhost/hermes
EOF

# 3. Verify files are there
ls -la
# Should see: main.py, requirements.txt, Dockerfile, .env

# DONE: Code ready
```

---

## STEP 3: Build & Deploy Docker Container (20 minutes)

```bash
# Still in /var/www/hermes/backend

# 1. Build Docker image
docker build -t hermes-api:latest .
# Takes 3-5 minutes
# Should see: "Successfully tagged hermes-api:latest"

# 2. Run container
docker run -d \
  --name hermes-api \
  -p 8000:8000 \
  --env-file .env \
  --restart always \
  hermes-api:latest

# Verify it's running
docker ps
# Should show hermes-api container running

# 3. Test API
curl http://localhost:8000/health
# Should return: {"status": "ok"}

# 4. Test from your laptop
# Replace 192.168.1.100 with your actual Hostinger IP
curl http://192.168.1.100:8000/health
# Should return: {"status": "ok"}

# DONE: API live and accessible
```

---

## STEP 4: Twilio Setup (15 minutes)

```bash
# Go to twilio.com (from your laptop browser)

# 1. Create account (if not already)
# 2. Verify your phone number
# 3. Buy a phone number
#    Country: Canada
#    Area code: 250 (Comox Valley)
#    Number will be: 250-555-XXXX
#    Cost: $1/month
# 4. Write down: Phone number (e.g., 250-555-1234)

# 5. Get API credentials
# Twilio Console → Account → API Credentials
# Copy: Account SID (AC...)
# Copy: Auth Token (...)
# Add to .env on Hostinger:
#   TWILIO_ACCOUNT_SID=AC...
#   TWILIO_AUTH_TOKEN=...

# 6. Configure Webhook
# Twilio Console → Phone Numbers → Manage → Active Numbers
# Click your number
# Voice section:
#   When a call comes in: Webhook
#   URL: http://192.168.1.100:8000/webhook/call
#   Method: POST
# Click Save

# 7. Test (from your phone)
# Call 250-555-1234
# Should hear: "Thanks for calling. How can I help?"
# Say: "I need a plumber"
# Agent should respond

# DONE: Phone calls working
```

---

## STEP 5: Test End-to-End (10 minutes)

```bash
# Test 1: API health
curl http://192.168.1.100:8000/health
# Response: {"status": "ok"}

# Test 2: Agent endpoint
curl -X POST http://192.168.1.100:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "I need a plumber",
    "phone": "250-555-1234",
    "contractor_id": 1
  }'
# Response: Agent response JSON

# Test 3: Live call (from your phone)
# Call 250-555-1234
# Should hear agent respond
# Agent should process your request

# Test 4: Check logs
docker logs hermes-api
# Should show: "Incoming call from 250-555-1234"
# Should show: "Extracted: plumbing service"

# DONE: Everything working
```

---

## STEP 6: Add 11 Labs Speech Integration (Week 2)

```
When ready (Week 2):

1. Create 11 Labs account
   - Go to elevenabs.io
   - Sign up
   - Get API key
   
2. Create /var/www/hermes/backend/tts_handler.py
   - POST to 11 Labs API
   - Convert agent text → audio
   - Return audio to Twilio
   
3. Update main.py
   - When agent generates response text
   - Call tts_handler.py
   - Get audio back
   - Send to Twilio
   
4. Test
   - Call 250-555-1234
   - Hear agent speak (natural voice, not robot)
   
Cost: $5-11/month for 11 Labs
```

---

## Monitoring: Keep It Running (Ongoing)

```bash
# SSH into Hostinger

# Check if container is running
docker ps

# If it crashed, restart it
docker start hermes-api

# Check logs for errors
docker logs hermes-api

# Monitor resource usage
docker stats hermes-api

# If you make changes to code:
cd /var/www/hermes
git pull
cd backend
docker build -t hermes-api:latest .
docker stop hermes-api
docker run -d --name hermes-api-new -p 8000:8000 --env-file .env hermes-api:latest
docker rm hermes-api
docker rename hermes-api-new hermes-api
```

---

## Troubleshooting

### Problem: "Connection refused" when calling Twilio webhook

```bash
# Check 1: Is API running?
docker ps
# Should show hermes-api running

# Check 2: Is port 8000 open?
curl http://192.168.1.100:8000/health
# Should return {"status": "ok"}

# Check 3: Is Twilio webhook configured correctly?
# Twilio Console → Phone Numbers → Your number
# Voice webhook should be: http://192.168.1.100:8000/webhook/call

# Check 4: Is Hostinger blocking port 8000?
# Hostinger → Security → Firewall → Allow 8000
```

### Problem: "No such file or directory" when building Docker

```bash
# Make sure Dockerfile exists in /var/www/hermes/backend
ls -la Dockerfile
# If not, copy it from repo

# Make sure main.py exists
ls -la main.py

# Make sure requirements.txt exists
ls -la requirements.txt
```

### Problem: Agent doesn't respond intelligently

```bash
# Check 1: Is OPENAI_API_KEY set?
docker exec hermes-api env | grep OPENAI
# Should show your key

# Check 2: Is OpenAI account active?
# Go to platform.openai.com
# Check billing → Have sufficient credits?

# Check 3: Check agent logs
docker logs hermes-api
# Should show LLM calls

# Check 4: Test API directly
curl -X POST http://192.168.1.100:8000/agent/process \
  -H "Content-Type: application/json" \
  -d '{"transcript": "test", "phone": "250-555-1234"}'
# Should return agent response
```

### Problem: Twilio webhook timeout

```bash
# Twilio has 10-second timeout
# If your agent takes >10 seconds, Twilio times out

# Solutions:
# 1. Make agent faster (reduce LLM token count)
# 2. Use OpenAI faster model (gpt-4-turbo instead of gpt-4)
# 3. Cache responses (same question → reuse answer)
# 4. Use Twilio Autopilot (separate from your agent)
```

---

## What You Have After Week 1

```
✅ Hostinger VPS running
✅ Docker container with FastAPI
✅ Lead Capture Agent processing calls
✅ Twilio integration (phone number working)
✅ 11 Labs integration (coming Week 2)
✅ Logs showing all call details

Next (Week 2):
  - Add PostgreSQL database
  - Persist leads to database
  - Add 11 Labs speech synthesis
  - Add real Twilio call handling

Next (Week 3):
  - Quote Generation Agent
  - Parts database
  - PDF generation

Next (Week 4):
  - Billing Agent
  - Scheduling Agent
  - Complete MVP
```

---

## Cost Breakdown

```
Monthly Recurring (when live):
  Hostinger VPS:        $5-10
  PostgreSQL (Hostinger): $5-10
  Twilio:               $2-5 (calls + SMS)
  11 Labs:              $5-11 (speech)
  OpenAI:               $5-20 (LLM calls)
  Stripe:               2.9% + $0.30 per transaction
  Monitoring:           $0-50 (optional)
  
  TOTAL:                $22-96/month

You charge per contractor: $500/month
At 10 contractors: $5,000/month revenue
Infrastructure cost: <$96/month
Margin: 98%

At 40 contractors: $20,000/month revenue
Infrastructure cost: ~$150-200/month (slight scale)
Margin: 99%
```

---

## Success Criteria: Week 1

```
✅ Week 1 Complete When:
  1. VPS running on Hostinger
  2. Docker container deployed
  3. API accessible at http://your-ip:8000
  4. Twilio phone number configured
  5. Test call → Agent responds
  6. Logs show incoming call and agent response
  7. No errors in docker logs

Once all 7 are working → READY FOR WEEK 2
```

---

## Next: Add Database (Week 2)

```
After Week 1, in Week 2:

1. Create PostgreSQL database
2. Run migrations (SQL schema)
3. Connect main.py to database
4. Save leads persistently
5. Retrieve contractor info
6. Add 11 Labs speech synthesis
7. Test end-to-end

All code is ready. Just deploy and wire together.
```

