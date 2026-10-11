# Railway Deployment: Step-by-Step (No Coding Required)

**Easiest way to deploy Hermes. Takes 15 minutes total.**

**Status:** Do this after you have your API keys gathered

---

## What is Railway?

Railway is a website that:
1. Takes your code
2. Runs it on their computers
3. Keeps it running 24/7
4. You pay $5/month

Think of it like renting a computer that runs your code.

---

## Prerequisites (Before Starting)

✅ You have your API keys saved in a text file:
```
OPENAI_API_KEY=sk-xxx
TWILIO_ACCOUNT_SID=AC_xxx
TWILIO_AUTH_TOKEN=xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_SECRET_KEY=sk_xxx
```

✅ You have a GitHub account (free, takes 2 minutes to create)

**If you don't have GitHub:**
1. Go to https://github.com
2. Sign up (email, password)
3. Verify email
4. Come back here

---

## Step-by-Step Deployment

### STEP 1: Upload Code to GitHub (5 minutes)

**GitHub is like a cloud storage for code. Railway reads from GitHub to deploy.**

#### 1a. Create a GitHub Repository

1. Go to https://github.com/new
2. Sign in (if not already)
3. Fill in:
   - Repository name: `hermes-backend`
   - Description: `Hermes AI Agent Platform`
   - Public ✓ (it's fine, no secrets will be in the code)
   - Click "Create repository"
4. You'll see a page with instructions

#### 1b. Push Your Code to GitHub

**I'm giving you EXACT commands to copy-paste. You don't need to understand them.**

Open your Terminal/Command Prompt and run these commands one-by-one:

```bash
# Go to your Hermes folder
cd /media/Dman/Hermes/Hermes

# Initialize git (one-time setup)
git init
git add -A
git commit -m "Initial Hermes backend"

# Add GitHub as remote (replace with YOUR GitHub username)
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/hermes-backend

# Push code to GitHub
git branch -M main
git push -u origin main
```

**What to do if you get an error:**
- Copy the error message
- Send it to me
- I'll fix it

**If successful, you'll see:**
```
Enumerating objects: ...
Writing objects: ...
✓ Done
```

---

### STEP 2: Create Railway Account (3 minutes)

1. Go to https://railway.app
2. Click "Create Account"
3. Sign up with GitHub (click "Sign up with GitHub")
4. Authorize Railway (click "Authorize")
5. You're logged in

---

### STEP 3: Create New Railway Project (3 minutes)

1. In Railway dashboard, click "New Project"
2. Click "Deploy from GitHub repo"
3. Select your `hermes-backend` repository
4. Click "Deploy"

**Railway will:**
- Detect it's a Python app
- Auto-configure it
- Start deployment (takes 1-2 minutes)

You'll see a progress bar. Wait for it to finish.

---

### STEP 4: Add Your API Keys to Railway (3 minutes)

**Railway needs your API keys to run the app.**

1. In Railway dashboard, find your project
2. Click the "hermes-backend" service
3. Click "Variables" tab
4. Click "Add Variable" for each one:

```
Name: OPENAI_API_KEY
Value: sk-xxx (copy from your text file)
```

Repeat for each:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- STRIPE_PUBLISHABLE_KEY
- STRIPE_SECRET_KEY
- DATABASE_URL (Railway creates this automatically, leave empty)

5. After adding all variables, click the deploy button

**Railway redeploys with your keys. Wait 1-2 minutes.**

---

### STEP 5: Get Your App URL (1 minute)

Once deployment is done:

1. In Railway, click your project
2. Look for "Deployments"
3. You'll see a URL like: `https://hermes-backend-prod-xxx.railway.app`
4. Copy this URL
5. **Save it somewhere**

This is your app's address on the internet.

---

### STEP 6: Test It Works (2 minutes)

1. Open a new browser tab
2. Visit: `https://hermes-backend-prod-xxx.railway.app/health`
   (Replace with YOUR URL from Step 5)
3. You should see:
   ```json
   {
     "status": "ok",
     "timestamp": "2024-09-07T..."
   }
   ```

**If you see this:** ✅ It works!

**If you see an error:** Tell me the error, I'll fix it

---

### STEP 7: Add PostgreSQL Database (Optional, Do Later)

For now, your app is running but won't store data persistently.

Later, we'll add:
1. A PostgreSQL database
2. Connect it to your app
3. Now everything is stored

**For now, skip this. We'll do it in a follow-up.**

---

## You're Done! 🎉

Your Hermes backend is now running on Railway 24/7.

**Next steps:**
1. Buy a Twilio phone number
2. Configure call forwarding
3. Make a test call
4. Watch Hermes answer

---

## Troubleshooting

### Problem: Deployment failed
**Solution:** 
1. Check that you pushed code to GitHub correctly
2. Go to Railway and check the logs (Deployments tab)
3. Send me the error message

### Problem: Can't see the health check
**Solution:**
1. Make sure you used YOUR correct Railway URL
2. Check that Railway finished deploying (green checkmark)
3. Wait a few seconds and try again

### Problem: API keys not working
**Solution:**
1. Double-check you copied the keys correctly
2. Make sure no extra spaces were added
3. Redeploy (Railway should auto-redeploy when you add variables)

---

## What Happens Now?

- Your app runs 24/7 on Railway
- When a customer calls your Twilio number, it hits your app
- Your app (Hermes) processes the call
- Everything works

**You can now:**
- Make changes to code (push to GitHub, Railway redeploys automatically)
- Add more services (database, etc.)
- Scale up (Railway handles it)
- Monitor (Railway shows you what's running)

---

## Questions?

If anything is unclear:
1. Tell me what's confusing
2. I'll explain in simpler terms
3. No judgment, no tech jargon

**You've got this. Let me know when you're done!**

