# Production Deployment Guide

## Prerequisites

1. **Fly.io Account**: Sign up at https://fly.io
2. **Fly CLI**: Install via `curl -L https://fly.io/install.sh | sh`
3. **Secrets**: Prepare environment variables

## Step 1: Create Fly.io App

```bash
# Login to Fly.io
fly auth login

# Create app (already configured in fly.toml)
fly apps create africa-offline-os --org personal

# Create persistent volume for SQLite
fly volumes create aos_data --size 10 --region jnb
```

## Step 2: Set Secrets

```bash
# Set required secrets
fly secrets set \
  AOS_MASTER_SECRET="your-32-char-secret-key" \
  TELEGRAM_BOT_TOKEN="your-telegram-bot-token" \
  TELEGRAM_WEBHOOK_SECRET="your-webhook-secret"
```

## Step 3: Deploy

```bash
# Deploy to Fly.io
fly deploy

# Check deployment status
fly status

# View logs
fly logs
```

## Step 4: Verify Deployment

```bash
# Check health endpoint
curl https://africa-offline-os.fly.dev/health

# Expected response:
# {
#   "status": "ok",
#   "db_status": "healthy",
#   "disk_free_mb": 9500,
#   "uptime_seconds": 120
# }

# Check readiness
curl https://africa-offline-os.fly.dev/health/ready

# Expected response:
# {
#   "ready": true,
#   "checks": {
#     "database": "ok",
#     "event_dispatcher": "ok",
#     "disk_space": "9500MB"
#   }
# }
```

## Step 5: Setup Automated Backups

```bash
# SSH into the running instance
fly ssh console

# Test backup script
python -m aos.scripts.backup_db

# Verify backup created
ls -lh /data/backups/

# Setup cron (add to Dockerfile or use Fly.io scheduled tasks)
```

## Monitoring

### View Logs
```bash
fly logs --app africa-offline-os
```

### Check Metrics
```bash
fly status --app africa-offline-os
fly vm status
```

### Scale (if needed)
```bash
# Scale to 2 instances (not recommended for SQLite)
fly scale count 2

# Scale back to 1
fly scale count 1
```

## Rollback

```bash
# List releases
fly releases

# Rollback to previous version
fly releases rollback <version>
```

## Troubleshooting

### Database Issues
```bash
# SSH into instance
fly ssh console

# Check SQLite mode
sqlite3 /data/aos.db "PRAGMA journal_mode;"
# Should return: wal

# Check integrity
sqlite3 /data/aos.db "PRAGMA integrity_check;"
# Should return: ok
```

### Disk Space Issues
```bash
# Check disk usage
fly ssh console
df -h /data

# Cleanup old backups
python -m aos.scripts.backup_db  # Runs cleanup automatically
```

### Health Check Failures
```bash
# Check logs
fly logs

# Common issues:
# - Database not initialized: Check migrations ran
# - Low disk space: Cleanup backups or increase volume size
# - Event dispatcher not running: Check startup logs
```

## Production Checklist

- [ ] Fly.io app created
- [ ] Volume created (10GB minimum)
- [ ] Secrets configured
- [ ] Deployment successful
- [ ] Health check returns 200
- [ ] Readiness check returns 200
- [ ] SQLite in WAL mode
- [ ] Backups tested
- [ ] Logs are clean
- [ ] HTTPS working
- [ ] Domain configured (optional)

## Next Steps

After production hardening is verified:
1. **WhatsApp Integration** - Add Meta Business API
2. **Monitoring** - Setup Sentry or self-hosted monitoring
3. **Alerts** - Configure Fly.io alerts for health check failures
