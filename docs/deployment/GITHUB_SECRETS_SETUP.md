# GitHub Secrets Setup Guide - OpenAI API Key

**Purpose:** Securely manage OpenAI API key for production without committing to git

**Status:** ✅ Configured in CD pipeline (commit 3d5448d)

---

## 🔐 Security Architecture

```
┌─────────────────┐
│ GitHub Secrets  │ (Encrypted storage)
│  OPENAI_API_KEY │
└────────┬────────┘
         │
         │ CD Workflow triggered on push to main
         ▼
┌─────────────────┐
│  cd.yml (L205)  │ env: OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
└────────┬────────┘
         │
         │ appleboy/ssh-action passes env var
         ▼
┌─────────────────┐
│ Droplet Server  │ Script receives $OPENAI_API_KEY
│ /opt/chitram    │
└────────┬────────┘
         │
         │ sed removes old key, tee appends new key
         ▼
┌─────────────────┐
│ .env.production │ OPENAI_API_KEY=sk-proj-...
└────────┬────────┘
         │
         │ docker-compose --env-file .env.production
         ▼
┌─────────────────┐
│ Backend Container│ process.env.OPENAI_API_KEY
└─────────────────┘
```

**Key Security Features:**
- ✅ API key encrypted at rest in GitHub
- ✅ Transmitted over SSH (encrypted in transit)
- ✅ Only visible to deployment workflow
- ✅ Never logged or committed to git
- ✅ Audit trail in GitHub Actions logs (value redacted)

---

## 📋 Setup Instructions

### Step 1: Get OpenAI API Key

1. **Sign up/Login:** https://platform.openai.com/
2. **Navigate to API Keys:** https://platform.openai.com/api-keys
3. **Create New Key:**
   - Click **"Create new secret key"**
   - Name: `Chitram Production`
   - Permissions: Default (full access)
4. **Copy Key Immediately:**
   - Format: `sk-proj-...` (starts with sk-proj or sk-)
   - ⚠️ You can only see it once!
   - Store temporarily in password manager

5. **Set Up Billing:**
   - Go to: https://platform.openai.com/account/billing
   - Add payment method
   - Set spending limit (recommended: $10/month for MVP)

**Cost Estimate:**
- gpt-4o-mini: ~$0.004 per image
- 1,000 images/month = $4
- 5,000 images/month = $20

### Step 2: Add Secrets to GitHub Repository

1. **Navigate to Repository Settings:**
   ```
   https://github.com/YOUR-USERNAME/chitram/settings/secrets/actions
   ```

2. **Add ALL AI Configuration Secrets:**

   Click **"New repository secret"** for each of these:

   | Secret Name | Value | Required? |
   |-------------|-------|-----------|
   | `OPENAI_API_KEY` | `sk-proj-your-key-here` | ✅ YES (your actual OpenAI key) |
   | `AI_PROVIDER` | `openai` | ✅ YES (or `mock` for testing) |
   | `AI_MAX_TAGS_PER_IMAGE` | `5` | Optional (defaults to 5) |
   | `AI_CONFIDENCE_THRESHOLD` | `70` | Optional (defaults to 70) |
   | `OPENAI_VISION_MODEL` | `gpt-4o-mini` | Optional (defaults to gpt-4o-mini) |

   **Important:** Secret names are case-sensitive and must match exactly!

3. **Verify All Secrets Added:**

   You should see all 5 AI secrets in the list:

   ```
   Repository secrets

   Secrets are encrypted and can only be accessed by GitHub Actions.

   OPENAI_API_KEY              Updated 3 minutes ago    [Update] [Remove]
   AI_PROVIDER                 Updated 3 minutes ago    [Update] [Remove]
   AI_MAX_TAGS_PER_IMAGE       Updated 3 minutes ago    [Update] [Remove]
   AI_CONFIDENCE_THRESHOLD     Updated 3 minutes ago    [Update] [Remove]
   OPENAI_VISION_MODEL         Updated 3 minutes ago    [Update] [Remove]
   DROPLET_HOST                Updated 7 days ago       [Update] [Remove]
   DROPLET_USER                Updated 7 days ago       [Update] [Remove]
   DROPLET_SSH_KEY             Updated 7 days ago       [Update] [Remove]
   ```

   **Note:** If you skip the optional secrets, the CD pipeline will use default values.

### Step 3: Deploy (Fully Automated - No Manual Steps!)

**That's it! No manual SSH needed.**

The CD pipeline will automatically inject ALL AI configuration from GitHub Secrets when you deploy.

**What happens during deployment:**

1. CD pipeline reads secrets from GitHub
2. Deploys code to droplet
3. **Automatically injects into .env.production:**
   ```bash
   OPENAI_API_KEY=sk-proj-... (from GitHub Secret)
   AI_PROVIDER=openai (from GitHub Secret)
   AI_MAX_TAGS_PER_IMAGE=5 (from GitHub Secret or default)
   AI_CONFIDENCE_THRESHOLD=70 (from GitHub Secret or default)
   OPENAI_VISION_MODEL=gpt-4o-mini (from GitHub Secret or default)
   ```
4. Restarts backend container with new config
5. ✅ Done!

**No manual editing of .env.production required!**

### Step 4: Deploy to Production

**Option A: Automatic Deployment (Recommended)**

Just push to main branch:

```bash
git checkout main
git merge feat/phase5-ai-vision-provider
git push origin main
```

The CD pipeline will:
1. ✅ Run all tests
2. ✅ Build Docker image
3. ✅ Deploy to droplet
4. ✅ **Inject OPENAI_API_KEY from GitHub Secrets**
5. ✅ Restart services
6. ✅ Run health checks

**Watch deployment:**
```
https://github.com/YOUR-USERNAME/chitram/actions
```

**Option B: Manual Deployment (Testing)**

If you want to test before merging to main:

```bash
# From feat/phase5-ai-vision-provider branch
git push origin feat/phase5-ai-vision-provider

# Manually trigger workflow
# Go to: https://github.com/YOUR-USERNAME/chitram/actions/workflows/cd.yml
# Click "Run workflow" → Select branch → Run
```

### Step 5: Verify Deployment

**SSH to droplet and check:**

```bash
ssh root@your-droplet-ip

# 1. Check .env.production has ALL AI config (injected by CD pipeline)
cd /opt/chitram/deploy
grep -E "^(OPENAI_API_KEY|AI_PROVIDER|AI_MAX_TAGS|AI_CONFIDENCE|OPENAI_VISION_MODEL)=" .env.production

# Should output all 5 values:
# OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE
# AI_PROVIDER=openai
# AI_MAX_TAGS_PER_IMAGE=5
# AI_CONFIDENCE_THRESHOLD=70
# OPENAI_VISION_MODEL=gpt-4o-mini

# 2. Check backend container has the env vars
docker-compose exec backend env | grep -E "^(OPENAI_API_KEY|AI_PROVIDER|AI_MAX_TAGS|AI_CONFIDENCE|OPENAI_VISION_MODEL)="

# Should output all 5 values from container

# 3. Check backend logs for AI provider initialization
docker-compose logs backend | grep -i "openai"

# Should see:
# INFO:app.services.ai.openai_vision:OpenAI Vision provider initialized (model=gpt-4o-mini, max_tags=5)
```

---

## 🧪 Testing AI Provider

After deployment, test the AI provider works:

### Test 1: Check Health Endpoint

```bash
curl https://chitram.io/health | jq .

# Should return:
# {
#   "status": "healthy",
#   ...
# }
```

### Test 2: Test AI Tagging (After Phase 5 Temporary Endpoint)

Once the temporary `/images/{id}/ai-tag` endpoint is deployed:

1. **Upload an image via web UI:**
   - Go to https://chitram.io
   - Login
   - Upload an image
   - Note the image ID from URL

2. **Trigger AI tagging (manual test):**

```bash
# Get auth token from browser cookies (chitram_auth)
AUTH_TOKEN="your-auth-token-from-cookie"

# Trigger AI tagging
curl -X POST https://chitram.io/api/v1/images/{IMAGE_ID}/ai-tag \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" | jq .

# Should return:
# {
#   "message": "Added 5 AI tags",
#   "tags": [
#     {"name": "landscape", "confidence": 90, "category": null},
#     {"name": "nature", "confidence": 90, "category": null},
#     ...
#   ]
# }
```

3. **Verify tags appear in web UI:**
   - Refresh image detail page
   - Should see AI tags (blue) with ✨ icon
   - Each tag shows 90% confidence

---

## 🔄 Rotating the API Key

If you need to rotate the key (security best practice: every 90 days):

### Step 1: Create New OpenAI Key

1. Go to https://platform.openai.com/api-keys
2. Create new key: `Chitram Production v2`
3. Copy the new key

### Step 2: Update GitHub Secret

1. Go to: `https://github.com/YOUR-USERNAME/chitram/settings/secrets/actions`
2. Click **[Update]** next to `OPENAI_API_KEY`
3. Paste new key
4. Click **"Update secret"**

### Step 3: Redeploy

```bash
# Trigger redeployment (push to main or manual workflow dispatch)
git commit --allow-empty -m "chore: rotate OpenAI API key"
git push origin main
```

The CD pipeline will:
- ✅ Inject new key into .env.production
- ✅ Restart backend container with new key
- ✅ Old key no longer used

### Step 4: Revoke Old Key

1. Go to https://platform.openai.com/api-keys
2. Find old key (`Chitram Production v1`)
3. Click trash icon to delete
4. Confirm deletion

---

## 🚨 Troubleshooting

### Issue 1: "OPENAI_API_KEY not found in GitHub Secrets"

**Symptoms:**
```
⚠️  WARNING: OPENAI_API_KEY not found in GitHub Secrets
```

**Cause:** Secret not added to GitHub or wrong name

**Fix:**
1. Verify secret name is exactly `OPENAI_API_KEY` (case-sensitive)
2. Check: https://github.com/YOUR-USERNAME/chitram/settings/secrets/actions
3. Re-add secret if missing

### Issue 2: "Invalid OpenAI API key"

**Symptoms:**
```
ERROR: OpenAI Vision API failed: Invalid API key
```

**Cause:** Wrong key format or revoked key

**Fix:**
1. Verify key starts with `sk-proj-` or `sk-`
2. Check key is active: https://platform.openai.com/api-keys
3. Generate new key and update GitHub Secret

### Issue 3: Backend container not seeing OPENAI_API_KEY

**Symptoms:**
```bash
docker-compose exec backend env | grep OPENAI_API_KEY
# No output
```

**Cause:** .env.production not loaded or key not injected

**Fix:**
```bash
# 1. Check .env.production has the key
cd /opt/chitram/deploy
cat .env.production | grep OPENAI_API_KEY

# If missing, manually trigger CD pipeline or add manually (temporary):
echo "OPENAI_API_KEY=sk-proj-YOUR-KEY" >> .env.production

# 2. Restart services
docker-compose down
docker-compose --env-file .env.production up -d

# 3. Verify
docker-compose exec backend env | grep OPENAI_API_KEY
```

### Issue 4: Rate Limit Exceeded

**Symptoms:**
```
ERROR: OpenAI rate limit exceeded. Please try again later.
```

**Cause:** Too many API requests (Tier 1: 500 requests/minute)

**Fix:**
1. Wait 60 seconds and retry
2. Reduce concurrent uploads (set `UPLOAD_CONCURRENCY_LIMIT=5`)
3. Upgrade OpenAI tier: https://platform.openai.com/account/limits

### Issue 5: CD Pipeline Failing to Inject Secret

**Symptoms:**
```
Error: ssh: handshake failed: ssh: unable to authenticate
```

**Cause:** SSH action can't connect to droplet

**Fix:**
1. Verify `DROPLET_HOST`, `DROPLET_USER`, `DROPLET_SSH_KEY` secrets
2. Test SSH manually: `ssh -i key.pem user@host`
3. Check droplet firewall allows GitHub Actions IPs

---

## 📊 Monitoring & Cost Tracking

### Monitor OpenAI Usage

1. **View Usage:**
   - Go to: https://platform.openai.com/usage
   - Filter by date range
   - Check cost per day

2. **Set Spending Limits:**
   - Go to: https://platform.openai.com/account/billing/limits
   - Set monthly limit: $10 (soft limit) and $20 (hard limit)
   - Get email alerts at 50%, 75%, 90%

3. **View API Logs:**
   ```bash
   # On droplet
   docker-compose logs backend | grep "OpenAI Vision returned"

   # Should show:
   # INFO:app.services.ai.openai_vision:OpenAI Vision returned 5 tags: ['landscape', 'nature', ...]
   ```

### Cost Alerts

**Recommended CloudWatch/Datadog alert:**
```
Alert: OpenAI API Cost > $15/day
Threshold: $15 daily spend
Action: Email + Slack notification
```

**Manual monitoring:**
- Check usage daily for first week
- Set calendar reminder to check weekly
- Review monthly invoice

---

## 🔒 Security Best Practices

### ✅ Do's

- ✅ Store API key in GitHub Secrets (encrypted)
- ✅ Rotate key every 90 days
- ✅ Set OpenAI spending limits ($10-20/month)
- ✅ Use separate keys for dev/staging/prod
- ✅ Revoke key immediately if compromised
- ✅ Monitor usage for anomalies

### ❌ Don'ts

- ❌ NEVER commit API key to git
- ❌ NEVER share key in chat/email/Slack
- ❌ NEVER log full API key (only first 10 chars: `sk-proj-Bk4HL...`)
- ❌ NEVER use production key in local development
- ❌ NEVER skip spending limits
- ❌ NEVER share screenshots showing full key

---

## 📚 Related Documentation

- [Phase 5 Implementation Plan](../implementation/phase5-ai-vision-provider-plan.md)
- [Phase 5 Implementation Summary](../implementation/phase5-ai-vision-provider-summary.md)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [appleboy/ssh-action Documentation](https://github.com/appleboy/ssh-action)

---

**Last Updated:** 2026-01-10
**Related Issue:** https://github.com/abhi10/chitram/issues/53
**CD Pipeline Commit:** `3d5448d`
