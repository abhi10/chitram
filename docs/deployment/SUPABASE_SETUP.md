# Supabase Authentication Setup Guide

This guide explains how to configure Chitram to use Supabase for authentication instead of the local auth provider.

## Overview

Chitram supports two authentication providers:
- **Local Auth** (default): bcrypt password hashing + JWT tokens issued by our backend
- **Supabase Auth**: Supabase handles auth, our backend syncs users to local DB for FK relationships

Both providers use the same API endpoints, so **no frontend changes are needed**.

## Prerequisites

- Chitram backend deployed and running
- A Supabase account (free tier is fine)

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Enter project details:
   - **Name**: chitram-auth (or your preferred name)
   - **Database Password**: Generate a strong password (save it somewhere)
   - **Region**: Choose closest to your server
4. Wait for project to be created (~2 minutes)

## Step 2: Get API Credentials

1. In your Supabase project, go to **Settings** > **API**
2. Copy these values:
   - **Project URL** (e.g., `https://abc123.supabase.co`)
   - **anon public** key (safe to expose in frontend)

## Step 3: Configure Supabase Auth Settings

1. Go to **Authentication** > **Settings**
2. Configure these settings:

### Email Auth
- Enable "Email" provider
- Disable "Confirm email" (optional, for easier testing)
- Set "Minimum password length" to 8

### Site URL
- Set **Site URL** to your production URL: `https://chitram.io`
- Add **Redirect URLs**:
  - `https://chitram.io`
  - `https://chitram.io/login`
  - `http://localhost:8000` (for development)

### Rate Limits (Optional)
Under **Rate Limits**, you can adjust:
- Email signups per hour: 100
- Token refreshes per hour: 1000

## Step 4: Update Chitram Configuration

### Option A: Environment Variables (Recommended)

Add to your `.env` file or deployment environment:

```bash
# Switch to Supabase auth
AUTH_PROVIDER=supabase

# Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Option B: Docker Compose

Update `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - AUTH_PROVIDER=supabase
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
```

### Option C: DigitalOcean/Production

If using DigitalOcean droplet with our deployment scripts:

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Edit environment file
nano /opt/chitram/.env

# Add/update these lines:
AUTH_PROVIDER=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Restart the application
cd /opt/chitram
docker-compose down
docker-compose up -d
```

## Step 5: Run Database Migration

The migration adds a `supabase_id` column to the users table:

```bash
# Local development
cd backend
uv run alembic upgrade head

# Production (via Docker)
docker-compose exec backend alembic upgrade head
```

## Step 6: Verify Configuration

1. **Check health endpoint**:
   ```bash
   curl https://chitram.io/health
   ```
   Should return `{"status": "healthy"}`

2. **Test registration**:
   - Go to https://chitram.io/register
   - Create a new account
   - Should redirect to home page after success

3. **Verify in Supabase Dashboard**:
   - Go to **Authentication** > **Users**
   - You should see the new user listed

## How It Works

### Sync-on-Auth Strategy

When a user registers or logs in with Supabase:

1. Supabase handles password verification/storage
2. On success, our backend:
   - Looks up user by `supabase_id` in local DB
   - If not found, looks up by email (migration path)
   - If still not found, creates new local user
3. Local user ID is used for all FK relationships (images, etc.)

### Migration Path

Existing local auth users can migrate to Supabase:
1. User registers in Supabase with same email
2. Backend links existing local user to Supabase ID
3. User continues to own all their existing images

## Rollback to Local Auth

If you need to switch back to local auth:

```bash
# Update environment
AUTH_PROVIDER=local

# Restart
docker-compose restart backend
```

Note: Users created via Supabase won't have password hashes in local DB, so they won't be able to log in with local auth.

## Troubleshooting

### Error: "SUPABASE_URL is required"
- Make sure `AUTH_PROVIDER=supabase` is set
- Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set

### Error: "Invalid API key"
- Check that you're using the `anon` key, not the `service_role` key
- Verify the key is copied correctly (no extra spaces)

### Users not syncing to local DB
- Check backend logs for errors
- Verify database migration ran: `alembic current`
- Check that `supabase_id` column exists in users table

### Password reset emails not sending
- Check Supabase **Authentication** > **Email Templates**
- Verify SMTP settings in Supabase (or use their built-in email)
- Check spam folder

## Security Considerations

1. **Never expose `service_role` key** - only use `anon` key in backend
2. **Enable RLS in Supabase** if storing additional data there
3. **Use HTTPS** for all API calls
4. **Set proper CORS** in Supabase settings

## Next Steps

After Supabase is working:
- [ ] Configure email templates in Supabase
- [ ] Enable OAuth providers (Google, GitHub)
- [ ] Set up password reset flow
- [ ] Monitor auth metrics in Supabase dashboard
