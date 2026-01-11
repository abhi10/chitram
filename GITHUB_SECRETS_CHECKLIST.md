# GitHub Secrets Checklist - Phase 5 AI Auto-Tagging

**Quick setup guide for fully automated AI configuration**

---

## ✅ Add These 5 Secrets to GitHub

Go to: **https://github.com/YOUR-USERNAME/chitram/settings/secrets/actions**

Click **"New repository secret"** for each:

### 1. OPENAI_API_KEY (REQUIRED ✅)
- **Name:** `OPENAI_API_KEY`
- **Value:** `sk-proj-your-actual-key-here`
- **Get from:** https://platform.openai.com/api-keys

### 2. AI_PROVIDER (REQUIRED ✅)
- **Name:** `AI_PROVIDER`
- **Value:** `openai`
- **Options:** `openai` (paid), `mock` (free testing)

### 3. AI_MAX_TAGS_PER_IMAGE (Optional)
- **Name:** `AI_MAX_TAGS_PER_IMAGE`
- **Value:** `5`
- **Default if skipped:** `5`
- **Range:** 1-10 (lower = cheaper, fewer tags)

### 4. AI_CONFIDENCE_THRESHOLD (Optional)
- **Name:** `AI_CONFIDENCE_THRESHOLD`
- **Value:** `70`
- **Default if skipped:** `70`
- **Range:** 0-100 (higher = only confident tags)

### 5. OPENAI_VISION_MODEL (Optional)
- **Name:** `OPENAI_VISION_MODEL`
- **Value:** `gpt-4o-mini`
- **Default if skipped:** `gpt-4o-mini`
- **Options:** `gpt-4o-mini` ($0.004/image), `gpt-4o` ($0.020/image)

---

## 📋 Copy-Paste Values (Recommended Settings)

**For production use:**

| Secret Name | Value to Enter |
|-------------|----------------|
| `OPENAI_API_KEY` | ← Your actual key from platform.openai.com |
| `AI_PROVIDER` | `openai` |
| `AI_MAX_TAGS_PER_IMAGE` | `5` |
| `AI_CONFIDENCE_THRESHOLD` | `70` |
| `OPENAI_VISION_MODEL` | `gpt-4o-mini` |

**For testing (no cost):**

| Secret Name | Value to Enter |
|-------------|----------------|
| `OPENAI_API_KEY` | ← Still need a real key (won't be used) |
| `AI_PROVIDER` | `mock` |
| (skip the rest) | (will use defaults) |

---

## 🚀 After Adding Secrets

**1. Deploy to production:**
```bash
git checkout main
git merge feat/phase5-ai-vision-provider
git push origin main
```

**2. Watch deployment:**
Go to: https://github.com/YOUR-USERNAME/chitram/actions

**3. Verify (after deployment completes):**
```bash
# SSH to droplet
ssh root@your-droplet-ip

# Check all values were injected
cd /opt/chitram/deploy
grep -E "^(OPENAI_API_KEY|AI_PROVIDER|AI_MAX_TAGS|AI_CONFIDENCE|OPENAI_VISION_MODEL)=" .env.production

# Should see all 5 values
```

**4. Test AI tagging:**
- Upload image at https://chitram.io
- Go to Swagger UI: https://chitram.io/docs
- Call `POST /api/v1/images/{id}/ai-tag`
- Refresh image page → see AI tags (blue ✨)

---

## 🔒 Security Notes

**Safe to share (not secrets):**
- ✅ AI_PROVIDER=openai
- ✅ AI_MAX_TAGS_PER_IMAGE=5
- ✅ AI_CONFIDENCE_THRESHOLD=70
- ✅ OPENAI_VISION_MODEL=gpt-4o-mini

**NEVER share (actual secrets):**
- ❌ OPENAI_API_KEY (costs money if leaked!)

**Why put non-secrets in GitHub Secrets?**
- Full automation (zero manual steps)
- Easy to change via GitHub UI
- Consistent across environments
- Audit trail

---

## 💰 Cost Estimate

**With recommended settings:**
- Model: gpt-4o-mini
- Max tags: 5 per image
- Cost: ~$0.004 per image

**Monthly estimates:**
- 100 images = $0.40
- 1,000 images = $4
- 5,000 images = $20
- 10,000 images = $40

**Set spending limit:** https://platform.openai.com/account/billing/limits

---

## ❓ Troubleshooting

**"Secret not found" error in CD logs:**
- Check secret name matches exactly (case-sensitive)
- Check secret was added to correct repo
- Try removing and re-adding secret

**AI tagging returns "mock" tags instead of real ones:**
- Check `AI_PROVIDER` secret is set to `openai` (not `mock`)
- Redeploy after changing secret

**"Invalid API key" error:**
- Check `OPENAI_API_KEY` is correct
- Test key at: https://platform.openai.com/playground
- Generate new key if needed

**Can't see secrets in logs:**
- This is correct! GitHub redacts secret values in logs
- Shows `***` instead of actual value

---

## 📚 Full Documentation

See: `docs/deployment/GITHUB_SECRETS_SETUP.md` for complete guide

---

**Last Updated:** 2026-01-10
**Related Commits:** `3d5448d`, `60a42ab`
