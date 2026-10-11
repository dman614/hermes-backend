# Railway Deployment: Your Personal Guide

**For You, Using Railway**  
**Status: Let's do this step-by-step, starting now**

---

## The Plan

We're going to do this in 4 simple phases over the next 2 weeks:

**Phase 1 (This Week):** Gather your API keys  
**Phase 2 (Early Next Week):** Create GitHub account & upload code  
**Phase 3 (Mid Next Week):** Deploy to Railway  
**Phase 4 (End of Week):** Test & Launch  

Each phase has ONE task. You do the task. Tell me when done. I give you the next task.

---

## PHASE 1: Gather Your API Keys (TODAY/TOMORROW)

**What this is:** Getting passwords/tokens for services Hermes needs

**What you're getting:**
- OpenAI key (so Hermes can think)
- Twilio keys (so Hermes can answer calls)
- Stripe keys (so Hermes can collect payments)

**Each takes 5-10 minutes. Do ONE at a time.**

---

### Task 1.1: Get Your OpenAI API Key

**Time: 5 minutes**

1. Go to: https://platform.openai.com/api/keys
2. If you don't have an account, click "Sign up"
3. Fill in email and password
4. Verify your email
5. Go back to: https://platform.openai.com/api/keys
6. Click "+ Create new secret key"
7. Copy the key (starts with `sk-`)
8. **Paste it into a text file on your computer**

**Your file should look like:**
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

**Done? Tell me "Task 1.1 done"**

---

### Task 1.2: Get Your Twilio Keys

**Time: 10 minutes**

1. Go to: https://www.twilio.com/console
2. If you don't have account, click "Sign up" (https://www.twilio.com)
3. Fill in: Email, password, and phone number
4. Verify your phone (they'll call/text you with a code)
5. Once verified, go to: https://www.twilio.com/console
6. You'll see "Account SID" and "Auth Token" on the main page
7. Copy BOTH and paste into your text file

**Your file should now look like:**
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Done? Tell me "Task 1.2 done"**

---

### Task 1.3: Get Your Stripe Keys

**Time: 5 minutes**

1. Go to: https://dashboard.stripe.com
2. If you don't have account, click "Start now" (https://stripe.com)
3. Fill in email and password
4. Verify email
5. Back to: https://dashboard.stripe.com
6. Go to: "Developers" → "API keys" (left sidebar)
7. You'll see two keys:
   - Publishable key (starts with `pk_`)
   - Secret key (starts with `sk_`)
8. Copy BOTH and paste into your text file

**Your file should now look like:**
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
```

**Done? Tell me "Task 1.3 done"**

---

## PHASE 1 COMPLETE ✅

Once you've done all three tasks, you'll have a text file with 5 keys.

**Reply to me with:**
- "Phase 1 complete"
- Tell me the first 10 characters of each key (so I can verify):
  - OPENAI: sk-proj-...
  - TWILIO_SID: ACxx...
  - TWILIO_TOKEN: xx...
  - STRIPE_PUB: pk_...
  - STRIPE_SECRET: sk_...

**Do NOT send me the full keys. Just the first 10 characters so I know you have them.**

---

## What Happens Next

Once I confirm Phase 1 is done, I'll send you:

**Phase 2:** Create a GitHub account (free, takes 3 minutes)  
**Phase 3:** Upload your code to GitHub (copy-paste, 5 minutes)  
**Phase 4:** Deploy to Railway (click buttons, 10 minutes)  
**Phase 5:** Test it works  

---

## Questions While Doing Phase 1?

- **"I don't have an account for [service]"** → Sign up (free, takes 2 min)
- **"I can't find the API key"** → Tell me where you're stuck, I'll send you a screenshot
- **"What if I mess up?"** → You can generate new keys, no problem
- **"Is this safe?"** → Yes. These keys are meant to be used. Just keep them private (don't share with others)

---

## Don't Panic!

This looks like a lot, but it's really just:
1. Visit website
2. Sign up (if needed)
3. Click "Get API key" (or similar)
4. Copy text
5. Paste into file

**That's it. Literally just copy-pasting.**

---

## Start NOW

Do Task 1.1 (OpenAI) right now. Takes 5 minutes.

**Reply when done: "Task 1.1 done, got my OpenAI key"**

Then I'll know you're rolling and we can keep going.

---

**You've got this. Let's go! 🚀**

