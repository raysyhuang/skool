# Deployment Guide

This guide covers deploying Skool to Heroku and troubleshooting common issues.

## Prerequisites

- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
- Git repository initialized
- Heroku account

## Initial Deployment

### 1. Create Heroku App

```bash
heroku create your-app-name
```

### 2. Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:mini
```

This automatically sets the `DATABASE_URL` environment variable.

### 3. Set SECRET_KEY (REQUIRED)

```bash
# Generate a secure secret key
openssl rand -hex 32

# Set it on Heroku
heroku config:set SECRET_KEY=<your-generated-key>
```

⚠️ **The app will refuse to start on Heroku without a valid SECRET_KEY.**

### 4. Deploy

```bash
git push heroku main
```

### 5. Initialize Database

```bash
# Run migrations
heroku run alembic upgrade head

# Seed initial data (users, characters, topics)
heroku run python -m app.seed.seed_db
```

## Configuration

### Environment Variables

View current config:
```bash
heroku config
```

Set optional overrides:
```bash
# Allow unlimited sessions per day (default: 2)
heroku config:set MAX_SESSIONS_PER_DAY=0

# Enable debug mode (NOT recommended for production)
heroku config:set DEBUG=True
```

## Troubleshooting

### App Crashes on Startup

**Check logs:**
```bash
heroku logs --tail
```

**Common issues:**

1. **Missing SECRET_KEY**
   ```
   RuntimeError: SECRET_KEY is not set
   ```
   **Fix:** `heroku config:set SECRET_KEY=$(openssl rand -hex 32)`

2. **Database connection error**
   ```
   sqlalchemy.exc.OperationalError: could not connect to server
   ```
   **Fix:** Ensure PostgreSQL addon is attached: `heroku addons`

3. **Import error / Module not found**
   ```
   ModuleNotFoundError: No module named 'X'
   ```
   **Fix:** Ensure `requirements.txt` includes all dependencies and redeploy

### Database Migrations

**Run migrations manually:**
```bash
heroku run alembic upgrade head
```

**Check migration status:**
```bash
heroku run alembic current
```

**Reset database (WARNING: deletes all data):**
```bash
heroku pg:reset DATABASE_URL --confirm your-app-name
heroku run python -m app.seed.seed_db
```

### Application Errors

**500 Internal Server Error**

Check logs for stack traces:
```bash
heroku logs --tail | grep ERROR
```

**Session/Cookie Issues**

Cookies require HTTPS in production. If testing locally with Heroku-like settings:
```bash
# Local testing
export DEBUG=True
uvicorn app.main:app --reload
```

## Updating the App

```bash
git push heroku main
```

Heroku automatically:
1. Detects Python app via `runtime.txt` and `requirements.txt`
2. Installs dependencies
3. Runs the web process from `Procfile`

**After deployment, run migrations if schema changed:**
```bash
heroku run alembic upgrade head
```

## Re-importing Taxonomy Data

If you update topic data in `app/seed/taxonomy/`:

```bash
heroku run python -m app.seed.seed_taxonomy
```

This is **idempotent** — safe to run on a live database without losing user progress.

## Monitoring

**View recent logs:**
```bash
heroku logs --tail
```

**Monitor dyno status:**
```bash
heroku ps
```

**Check database size:**
```bash
heroku pg:info
```

## Performance

**Scale dynos (if needed):**
```bash
# Upgrade to a larger dyno type
heroku ps:resize web=standard-1x

# Add more dynos (requires paid plan)
heroku ps:scale web=2
```

## Backup and Restore

**Create manual backup:**
```bash
heroku pg:backups:capture
```

**List backups:**
```bash
heroku pg:backups
```

**Restore from backup:**
```bash
heroku pg:backups:restore <backup-id> DATABASE_URL
```

## Local Development vs. Production

| Environment | SECRET_KEY | DATABASE_URL | DEBUG | HTTPS |
|-------------|------------|--------------|-------|-------|
| Local dev   | Any value  | `sqlite:///./skool.db` | `True` | Not required |
| Heroku      | **Must set** | Auto-set by addon | `False` | Enforced |

## Getting Help

- Heroku logs: `heroku logs --tail`
- Database console: `heroku pg:psql`
- Python shell: `heroku run python`
- View config: `heroku config`
