# Droplet Setup Guide

Step-by-step guide to provision and configure a DigitalOcean droplet for Chitram.

## Production Droplet

| Property | Value |
|----------|-------|
| **IP Address** | `157.230.139.161` |
| **Hostname** | `chitram-prod` |
| **SSH** | `ssh root@157.230.139.161` |

## Prerequisites

- DigitalOcean account
- SSH key pair (generate with `ssh-keygen -t ed25519`)
- Domain name (optional, for SSL)

## Step 1: Create Droplet

### Via DigitalOcean Console

1. Go to https://cloud.digitalocean.com/droplets
2. Click "Create Droplet"
3. Configure:
   - **Region:** Choose closest to your users
   - **Image:** Ubuntu 22.04 LTS
   - **Size:** Basic, Regular, $18/month (2 vCPU, 2GB RAM, 50GB SSD)
   - **Authentication:** SSH keys (add your public key)
   - **Hostname:** `chitram-prod`
4. Click "Create Droplet"
5. Note the IP address

### Via doctl CLI

```bash
# Install doctl
brew install doctl  # macOS
# or: snap install doctl  # Ubuntu

# Authenticate
doctl auth init

# Create droplet
doctl compute droplet create chitram-prod \
  --region nyc1 \
  --size s-2vcpu-2gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header | head -1)

# Get IP address
doctl compute droplet list --format "Name,PublicIPv4"
```

## Step 2: Initial Server Setup

SSH into the server:

```bash
ssh root@<droplet-ip>
```

### 2.1 Update System

```bash
apt update && apt upgrade -y
```

### 2.2 Create Non-Root User (Optional but Recommended)

```bash
# Create user
adduser chitram

# Add to sudo group
usermod -aG sudo chitram

# Copy SSH keys
mkdir -p /home/chitram/.ssh
cp ~/.ssh/authorized_keys /home/chitram/.ssh/
chown -R chitram:chitram /home/chitram/.ssh
chmod 700 /home/chitram/.ssh
chmod 600 /home/chitram/.ssh/authorized_keys

# Test login (in a new terminal)
ssh chitram@<droplet-ip>
```

### 2.3 Configure Firewall

```bash
# Allow SSH
ufw allow 22/tcp

# Allow HTTP and HTTPS (for Caddy)
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Verify
ufw status
```

Expected output:
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

## Step 3: Install Docker

Run as root (or use `sudo` prefix for each command):

```bash
# Install dependencies
apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's GPG key (note: sudo before gpg, not before curl)
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Add user to docker group (if using non-root user)
usermod -aG docker chitram
```

> **Note:** After `usermod -aG docker chitram`, log out and back in for the group to take effect.

## Step 4: Configure DNS (Optional, for SSL)

If you have a domain:

1. Go to your DNS provider
2. Add an A record:
   - **Name:** `@` (or subdomain like `images`)
   - **Type:** A
   - **Value:** `<droplet-ip>`
   - **TTL:** 300 (5 minutes)

3. Wait for DNS propagation (5-30 minutes):
   ```bash
   dig +short your-domain.com
   # Should return your droplet IP
   ```

## Step 5: Deploy Application

### 5.1 Clone Repository

For **public repositories**:
```bash
# Create application directory
sudo mkdir -p /opt/chitram
sudo chown chitram:chitram /opt/chitram
cd /opt/chitram

# Clone repository
git clone https://github.com/abhi10/chitram.git .
```

For **private repositories**, use a Deploy Key:

```bash
# 1. Generate deploy key (as the chitram user)
ssh-keygen -t ed25519 -C "chitram-prod-deploy" -f ~/.ssh/github_deploy -N ""

# 2. Fix permissions
chmod 600 ~/.ssh/github_deploy
chmod 644 ~/.ssh/github_deploy.pub

# 3. Show the public key
cat ~/.ssh/github_deploy.pub

# 4. Add to GitHub:
#    - Go to: https://github.com/abhi10/chitram/settings/keys
#    - Click "Add deploy key"
#    - Paste the public key, give it a name
#    - Click "Add key" (read-only is fine)

# 5. Create application directory
sudo mkdir -p /opt/chitram
sudo chown chitram:chitram /opt/chitram
cd /opt/chitram

# 6. Clone with deploy key
GIT_SSH_COMMAND="ssh -i ~/.ssh/github_deploy" git clone git@github.com:abhi10/chitram.git .
```

> **Troubleshooting:** If you get "Permission denied" on the key file, ensure the key is owned by the correct user:
> ```bash
> sudo chown chitram:chitram ~/.ssh/github_deploy ~/.ssh/github_deploy.pub
> chmod 600 ~/.ssh/github_deploy
> ```

### 5.2 Create Production Environment

```bash
cd /opt/chitram/deploy

# Copy template
cp .env.production.example .env.production

# Generate secrets
echo "Generating secrets..."
echo ""
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)"
echo "MINIO_SECRET_KEY=$(openssl rand -base64 32)"
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
echo "JWT_SECRET_KEY=$(openssl rand -base64 64)"
echo ""

# Edit .env.production with generated secrets
nano .env.production
```

**Important settings to update:**
- `DOMAIN`: Your domain (e.g., `images.example.com`) or `localhost` (if no domain)
- `POSTGRES_PASSWORD`: Generated password (update in TWO places: the variable AND in `DATABASE_URL`)
- `JWT_SECRET_KEY`: Generated secret
- `MINIO_ROOT_PASSWORD`: Generated password
- `MINIO_SECRET_KEY`: Generated secret (update in TWO places if `MINIO_ACCESS_KEY` uses same value)
- `REDIS_PASSWORD`: Generated password

> **Important:** The `DATABASE_URL` must use the same password as `POSTGRES_PASSWORD`. Update both!

### 5.3 Start Services

```bash
# Start all services
docker compose --env-file .env.production up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5.4 Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# If using domain with SSL
curl https://your-domain.com/health
```

## Step 6: Configure GitHub Secrets (for CD Pipeline)

In your GitHub repository:

1. Go to Settings → Secrets and variables → Actions
2. Add these repository secrets:

| Secret | Value |
|--------|-------|
| `DROPLET_HOST` | Your droplet IP address |
| `DROPLET_USER` | `root` (or `chitram` if using non-root) |
| `DROPLET_SSH_KEY` | Your private SSH key (full content) |

To get your private key:
```bash
cat ~/.ssh/id_ed25519
# Copy the entire content including BEGIN and END lines
```

## Step 7: Set Up Automated Backups

```bash
# Create backup directory
mkdir -p /opt/chitram-backups

# Add cron job for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/chitram/scripts/backup.sh >> /var/log/chitram-backup.log 2>&1") | crontab -

# Add cron job for weekly cleanup on Sunday at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * 0 /opt/chitram/scripts/backup.sh --cleanup >> /var/log/chitram-backup.log 2>&1") | crontab -

# Verify cron jobs
crontab -l
```

## Step 8: Test CD Pipeline

1. Make a small change in your repository
2. Push to main branch
3. Watch GitHub Actions for deployment
4. Verify the change is live

## Verification Checklist

Run these commands to verify everything is working:

```bash
# 1. Check Docker
docker --version
docker compose version

# 2. Check firewall
sudo ufw status

# 3. Check running containers
docker compose -f /opt/chitram/deploy/docker-compose.yml ps

# 4. Check health endpoint
curl http://localhost:8000/health

# 5. Check SSL (if using domain)
curl -I https://your-domain.com

# 6. Check cron jobs
crontab -l

# 7. Test backup
/opt/chitram/scripts/backup.sh --db-only
ls -la /opt/chitram-backups/
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs <service-name>

# Common issues:
# - Port already in use: Check with `netstat -tlnp`
# - Permission denied: Check file permissions
# - Out of memory: Check with `free -m`
```

### SSL Certificate Issues

```bash
# Check Caddy logs
docker compose logs caddy

# Common issues:
# - DNS not propagated: Wait and try again
# - Firewall blocking: Ensure ports 80/443 are open
# - Rate limited: Wait 1 hour (Let's Encrypt limit)
```

### Can't SSH to Server

```bash
# Check if SSH service is running
systemctl status ssh

# Check firewall
ufw status

# Check SSH config
cat /etc/ssh/sshd_config | grep -E "^(PermitRootLogin|PasswordAuthentication)"
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Remove old backups
/opt/chitram/scripts/backup.sh --cleanup
```

## Security Recommendations

1. **Disable password authentication:**
   ```bash
   sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
   systemctl restart ssh
   ```

2. **Enable automatic security updates:**
   ```bash
   apt install unattended-upgrades
   dpkg-reconfigure -plow unattended-upgrades
   ```

3. **Install fail2ban:**
   ```bash
   apt install fail2ban
   systemctl enable fail2ban
   systemctl start fail2ban
   ```

## Maintenance

### Updating the Application

The CD pipeline handles this automatically. For manual updates:

```bash
cd /opt/chitram
git pull origin main
cd deploy
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app

# Last 100 lines
docker compose logs --tail=100 app
```

### Restarting Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart app
```
