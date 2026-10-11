# Railway Deployment: Quick Reference Card

**Keep this handy while you work**

---

## Phase 1: Get API Keys (This week)

### Task 1.1: OpenAI
```
Website: https://platform.openai.com/api/keys
Sign up: If you don't have account
Get: Secret API Key (starts with sk-)
Save: OPENAI_API_KEY=sk-...
Time: 5 minutes
```

### Task 1.2: Twilio
```
Website: https://www.twilio.com/console
Sign up: https://www.twilio.com (if needed)
Verify: Phone (they'll call/text)
Get: Account SID (AC...) + Auth Token
Save: TWILIO_ACCOUNT_SID=AC...
      TWILIO_AUTH_TOKEN=...
Time: 10 minutes
```

### Task 1.3: Stripe
```
Website: https://dashboard.stripe.com
Sign up: https://stripe.com (if needed)
Go to: Developers → API keys
Get: Publishable key (pk_) + Secret key (sk_)
Save: STRIPE_PUBLISHABLE_KEY=pk_...
      STRIPE_SECRET_KEY=sk_...
Time: 5 minutes
```

---

## Phase 2: GitHub Account (Next week)

```
Website: https://github.com
Sign up: Email + password
Verify: Email confirmation
Time: 3 minutes
```

---

## Phase 3: Upload Code (Next week)

```
We'll use copy-paste commands
You paste into Terminal
Code goes to GitHub automatically
Time: 5 minutes
```

---

## Phase 4: Deploy to Railway (Next week)

```
Website: https://railway.app
Sign up: With GitHub
Create project: Click buttons
Add your API keys: Copy-paste
Deploy: Click deploy
Time: 10 minutes
```

---

## Phase 5: Test (Next week)

```
Visit: https://your-app-url/health
Should see: {"status": "ok"}
If yes: It works!
If no: Tell me the error
Time: 2 minutes
```

---

## Your Text File Template

**Create a file called `hermes_keys.txt` and fill it in:**

```
OPENAI_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
STRIPE_PUBLISHABLE_KEY=
STRIPE_SECRET_KEY=
```

Keep this file PRIVATE. Don't share it with anyone.

---

## Timeline

```
Today/Tomorrow: Phase 1 (get keys) — 20 minutes
Early next week: Phase 2-3 (GitHub) — 10 minutes
Mid next week: Phase 4 (Railway) — 10 minutes
End of week: Phase 5 (test) — 5 minutes

Total time: ~45 minutes
```

---

## Help

Got stuck? Tell me:
1. Which task?
2. What happened?
3. Any error messages?

I'll walk you through it.

---

## Next Step

**Start Task 1.1 now (OpenAI)**

Reply when done: "Task 1.1 done"

