# Deployment Implementation Guide

## Quick Start (30 Minutes to Production)

### Scenario 1: Using Render + Vercel + Neon (Recommended - Easiest)

This is the fastest way to get your app live with zero DevOps knowledge required.

#### 1. Create GitHub Repository

```bash
cd /path/to/ai-powered-academic-performance-analyser
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ai-powered-academic-performance-analyser.git
git branch -M main
git push -u origin main
```

#### 2. Create Neon Database (5 min)

```bash
# 1. Go to https://console.neon.tech/
# 2. Click "Sign Up"
# 3. Create account with GitHub
# 4. Create new project:
#    - Name: academic-analyzer
#    - Region: Pick closest to you
# 5. In Dashboard, find "Connection string"
# 6. Copy the PostgreSQL URL
```

Save the connection string - you'll need it soon.

#### 3. Run Setup Script (10 min)

```bash
# Make script executable
chmod +x quick-deploy.sh

# Run interactive setup
./quick-deploy.sh

# Follow prompts to:
# - Enter database connection string
# - Enter Google API Key
# - Generate JWT secret
# - Provide deployment URLs
```

The script will set up GitHub Secrets automatically.

#### 4. Deploy Backend to Render (5 min)

```bash
# 1. Go to https://render.com/
# 2. Sign up with GitHub
# 3. Click "New +" → "Web Service"
# 4. Select your GitHub repository
# 5. Fill in:
#    - Name: academic-analyzer-api
#    - Environment: Python 3
#    - Build command: pip install -r requirements.txt
#    - Start command: uvicorn app.main:app --host 0.0.0.0 --port 10000
# 6. Create the service
# 7. Copy Service ID from dashboard (srv-xxxxx)
# 8. Run in terminal:
gh secret set RENDER_SERVICE_ID
# Paste the Service ID
```

**Render API Token Setup**:
1. Go to https://dashboard.render.com/account/api-tokens
2. Create new token
3. Run: `gh secret set RENDER_API_KEY`
4. Paste the token

#### 5. Deploy Frontend to Vercel (5 min)

```bash
# 1. Go to https://vercel.com/
# 2. Sign up with GitHub
# 3. Click "Add New..." → "Project"
# 4. Import from GitHub
# 5. Select your repository
# 6. Fill in:
#    - Framework: Vite
#    - Root Directory: frontend
#    - Build Command: npm run build
#    - Output Directory: dist
# 7. Add Environment Variable:
#    - Name: VITE_API_BASE_URL
#    - Value: Your Render backend URL (e.g., https://academic-analyzer-api.onrender.com)
# 8. Deploy
```

**Vercel Token Setup**:
1. Go to https://vercel.com/account/tokens
2. Create token
3. Copy Org ID from https://vercel.com/account
4. Get Project ID from Vercel dashboard
5. Run:
```bash
gh secret set VERCEL_TOKEN
gh secret set VERCEL_ORG_ID
gh secret set VERCEL_PROJECT_ID
```

#### 6. Push to Trigger Deployment

```bash
# This triggers GitHub Actions workflows
git push origin main

# Monitor deployments:
gh run list -L 10

# View specific run:
gh run view <RUN_ID> --log
```

#### 7. Verify Deployment

- Backend API: `https://academic-analyzer-api.onrender.com/docs`
- Frontend: `https://academic-analyzer-frontend.vercel.app`

✅ **You're live!** The app is now deployed to the world.

---

## Scenario 2: Self-Hosted with Docker Compose

For maximum control and running on your own VPS (DigitalOcean, Linode, AWS):

### 1. Setup VPS

```bash
# 1. Create VPS on DigitalOcean / Linode / AWS
# 2. SSH into server
ssh root@your_vps_ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-powered-academic-performance-analyser.git
cd ai-powered-academic-performance-analyser
```

### 3. Create Environment File

```bash
cp .env.example .env
nano .env

# Fill in:
# - DATABASE_URL (PostgreSQL)
# - GOOGLE_API_KEY
# - SECRET_KEY
# - CORS_ORIGINS (your domain)
# - VITE_API_BASE_URL (your API URL)
```

### 4. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services will be available at**:
- API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Database: `localhost:5432`
- Nginx: `http://localhost` (if enabled)

### 5. Setup SSL Certificates

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Generate certificate (replace with your domain)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates for Docker
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
sudo chown $USER ./ssl/*
```

### 6. Update nginx.conf

Edit `nginx.conf`:
- Replace `academic-analyzer.com` with your domain
- Update certificate paths if needed

### 7. Restart Services

```bash
docker-compose down
docker-compose up -d
```

---

## Scenario 3: Advanced GitHub Actions + Multiple Platforms

For organizations wanting multi-region deployment:

### 1. Deploy to Multiple Backends

Modify `.github/workflows/deploy-backend.yml` to deploy to multiple services:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [render, railway, fly]
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to ${{ matrix.service }}
        run: |
          case ${{ matrix.service }} in
            render)
              curl https://api.render.com/deploy/srv-$RENDER_SERVICE_ID?key=$RENDER_API_KEY
              ;;
            railway)
              railway up --environment production
              ;;
            fly)
              flyctl deploy --remote-only
              ;;
          esac
```

### 2. Setup Monitoring

```yaml
- name: Setup Monitoring
  run: |
    # Send deployment event to monitoring service
    curl --request POST \
      --url https://api.sentry.io/api/0/organizations/$ORG_ID/releases/ \
      --header 'Authorization: Bearer $SENTRY_TOKEN' \
      --data '{"version": "${{ github.sha }}"}'
```

---

## Step-by-Step Checklist

### Pre-Deployment (Local)

- [ ] All code committed to git
- [ ] `git log` shows all commits
- [ ] No uncommitted changes: `git status`
- [ ] Tested locally with: `npm run dev` (frontend), `uvicorn app.main:app --reload` (backend)
- [ ] No hardcoded localhost URLs in code
- [ ] Python requirements.txt is updated
- [ ] Node packages are pinned to versions

### GitHub Setup

- [ ] Repository created on GitHub
- [ ] `.github/workflows/` directory exists with YML files
- [ ] All required GitHub Secrets are set (use `gh secret list`)
- [ ] Secrets match variable names in workflow files exactly

### Database Setup (Choose One)

#### Neon Setup
- [ ] Account created at https://console.neon.tech/
- [ ] Project created with proper password
- [ ] Connection string copied to `DATABASE_URL` secret
- [ ] Connection includes `?sslmode=require`

#### Railway Setup
- [ ] Account created at https://railway.app/
- [ ] PostgreSQL plugin added
- [ ] Connection URL copied

#### Local PostgreSQL
- [ ] PostgreSQL installed and running
- [ ] Database created: `createdb academic_analyser`
- [ ] Password is secure

### Backend Deployment (Choose One)

#### Render Setup
- [ ] Web Service created at https://render.com/
- [ ] GitHub repository connected
- [ ] Build && Start commands configured
- [ ] All environment variables from secrets added
- [ ] Auto-deploy enabled
- [ ] Service ID stored in RENDER_SERVICE_ID secret
- [ ] API responds to https://YOUR-SERVICE.onrender.com/docs

#### Railway Setup
- [ ] Project created at https://railway.app/
- [ ] Backend pushed/auto-deployed
- [ ] Service is running (green status)
- [ ] API accessible from backend URL

#### Docker Compose (Local/VPS)
- [ ] Docker installed
- [ ] docker-compose.yml present
- [ ] `.env` file configured with all secrets
- [ ] Services starting: `docker-compose up -d`
- [ ] Health checks passing: `docker-compose ps`

### Frontend Deployment (Choose One)

#### Vercel Setup
- [ ] Project created at https://vercel.app/
- [ ] GitHub repository connected
- [ ] Root Directory: `frontend`
- [ ] Build command: `npm run build`
- [ ] Output: `dist`
- [ ] Environment variables configured
- [ ] Auto-deploy enabled
- [ ] Frontend accessible at deployed URL

#### Netlify Setup
- [ ] Project created at https://netlify.com/
- [ ] GitHub repository connected
- [ ] Build command: `cd frontend && npm run build`
- [ ] Publish directory: `frontend/dist`
- [ ] Environment variables configured
- [ ] Site is live

#### Docker Compose
- [ ] Frontend service building
- [ ] Accessible at http://localhost:3000

### Final Verification

- [ ] Backend health check passes: `/health` returns 200
- [ ] Frontend loads without errors
- [ ] API calls from frontend to backend work
- [ ] No CORS errors in browser console
- [ ] Login/signup works end-to-end
- [ ] File uploads work
- [ ] GitHub Actions workflows run on push
- [ ] Deployments complete without errors
- [ ] Monitor services for errors

---

## Production Readiness Checklist

### Security

- [ ] CORS_ORIGINS set to production domain only
- [ ] SECRET_KEY is random and strong (≥32 chars)
- [ ] Database password is strong
- [ ] API keys are rotated (never committed)
- [ ] HTTPS/SSL enabled on all endpoints
- [ ] Database backups enabled

### Performance

- [ ] Database indexes on frequently queried columns
- [ ] Frontend built with production optimizations
- [ ] Backend using async/await for concurrency
- [ ] Large files chunked for upload
- [ ] Database connection pooling configured

### Monitoring

- [ ] Uptime monitoring enabled (UptimeRobot)
- [ ] Error tracking configured (Sentry)
- [ ] Logs being collected and monitored
- [ ] Alerts configured for failures
- [ ] Performance metrics tracked

### Maintenance

- [ ] Regular backup schedule for database
- [ ] API documentation updated
- [ ] README includes production URLs
- [ ] Deployment runbook documented
- [ ] Team has access to all services
- [ ] Incident response plan in place

---

## Troubleshooting Guide

### Deployment Shows as "Building" Forever

**Solution**:
```bash
# Check build logs
gh run view <RUN_ID> --log

# Common causes:
# 1. Dependency installation failing - check requirements.txt
# 2. Database migration timeout - increase timeout in workflow
# 3. Service quota exceeded - check provider's usage limits
```

### CORS Errors in Browser

**Solution**:
1. Check frontend URL is in CORS_ORIGINS
2. Update backend with:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
)
```
3. Redeploy backend
4. Clear browser cache

### Database Connection Refused

**Solution**:
1. Verify DATABASE_URL format: `postgresql://user:pass@host:5432/db`
2. Add `?sslmode=require` for cloud databases
3. Check IP whitelist allows your server
4. Verify password doesn't contain special characters (URL encode if needed)

### Frontend Can't Reach Backend

**Solution**:
1. Check VITE_API_BASE_URL matches backend URL
2. Verify backend service is running
3. Check backend is accessible from internet: `curl https://your-backend/health`
4. Verify no CORS errors in browser console

### Service Won't Start

**Solution**:
```bash
# View logs
docker-compose logs backend  # for Docker
gh run view <ID> --log      # for GitHub Actions

# Check:
# 1. All environment variables are set
# 2. Database URL is correct
# 3. Port is not in use (change port in config)
# 4. Python/Node version matches requirements
```

---

## Cost Analysis

### Recommended (Render + Vercel + Neon)

| Service | Tier | Cost |
|---------|------|------|
| Neon | Starter | Free ($0) |
| Render | Basic | $7 |
| Vercel | Pro | Free ($0) |
| Domain | .com | ~$10/year |
| **Monthly Total** | **~$1** | **$8.33** |

### Production Load (100+ users)

| Service | Tier | Cost |
|---------|------|------|
| Neon | Professional | $50 |
| Render | Standard | $25 |
| Vercel | Pro | Free ($0) |
| Domain + CDN | - | $10 |
| **Monthly Total** | **~$64** | |

---

## Next Steps After Deployment

1. **Setup Custom Domain**
   - Update DNS records to point to Vercel/Render
   - Enable HTTPS/SSL
   - Update CORS_ORIGINS

2. **Configure Monitoring**
   - Add Sentry for error tracking
   - Setup UptimeRobot for availability
   - Enable service health checks

3. **Setup Backups**
   - Enable database auto-backups
   - Configure backup retention period
   - Test restore procedure

4. **Documentation**
   - Update README with production URLs
   - Document deployment procedure
   - Create runbooks for common issues

5. **Team Access**
   - Give team members GitHub access
   - Share secret management procedures
   - Setup audit logging

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Neon Docs**: https://neon.tech/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **Docker Docs**: https://docs.docker.com/

Good luck with your deployment! 🚀
