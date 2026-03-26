# Complete Deployment Guide: AI Academic Performance Analyzer

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [GitHub Setup & CI/CD](#github-setup--cicd)
3. [Database Hosting (PostgreSQL)](#database-hosting-postgresql)
4. [Backend Deployment (FastAPI)](#backend-deployment-fastapi)
5. [Frontend Deployment (React)](#frontend-deployment-react)
6. [Environment Configuration](#environment-configuration)
7. [Deployment Workflows](#deployment-workflows)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Cost Estimates](#cost-estimates)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Repository                          │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────────┐  │
│  │   GitHub   │  │  GitHub    │  │  GitHub Actions CI/CD   │  │
│  │  Actions   │  │  Secrets   │  │   (Auto-Deploy)         │  │
│  │  Workflows │  │ (.env vars)│  │                         │  │
│  └────────────┘  └────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
         │                    │                         │
         │                    │                         │
    ┌────▼─────┐        ┌─────▼──────┐        ┌────────▼─────────┐
    │           │        │            │        │                  │
    │ Vercel    │        │  Render    │        │   Neon/Railway   │
    │(Frontend) │        │ (Backend)  │        │  (PostgreSQL DB) │
    │           │        │            │        │                  │
    └───────────┘        └────────────┘        └──────────────────┘
         │                    │                         │
         │                    │                         │
    User Browser ┌────────────┴─────────┬────────────────┘
                 │                      │
            API Calls              DB Queries
```

---

## GitHub Setup & CI/CD

### Step 1: Initialize GitHub Repository

```bash
cd /path/to/ai-powered-academic-performance-analyser
git init
git add .
git commit -m "Initial commit: AI Academic Performance Analyzer"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-powered-academic-performance-analyser.git
git push -u origin main
```

### Step 2: Create GitHub Secrets

GitHub Secrets store sensitive environment variables securely. Navigate to:
**Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Value | Required |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | Yes |
| `GOOGLE_API_KEY` | Your Google GenerativeAI key | Yes |
| `SECRET_KEY` | Strong JWT secret (≥32 chars) | Yes |
| `FRONTEND_URL` | `https://yourdomain.com` | Yes |
| `BACKEND_URL` | `https://api.yourdomain.com` | Yes |

### Step 3: Create GitHub Actions Workflows

Create `.github/workflows/` directory:

```bash
mkdir -p .github/workflows
```

#### File: `.github/workflows/deploy-backend.yml`

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/deploy-backend.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        run: |
          curl https://api.render.com/deploy/srv-${{ secrets.RENDER_SERVICE_ID }}?key=${{ secrets.RENDER_API_KEY }}
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
          RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
          
      - name: Verify Deployment
        run: |
          sleep 10
          curl -f https://${{ secrets.BACKEND_URL }}/health || exit 1
```

#### File: `.github/workflows/deploy-frontend.yml`

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/deploy-frontend.yml'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: cd frontend && npm ci
        
      - name: Build
        run: |
          cd frontend
          npm run build
        env:
          VITE_API_BASE_URL: ${{ secrets.BACKEND_URL }}
          
      - name: Deploy to Vercel
        uses: vercel/action@main
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: frontend
```

#### File: `.github/workflows/db-migrations.yml`

```yaml
name: Database Migrations

on:
  push:
    branches: [main]
    paths:
      - 'backend/migrations/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          
      - name: Run migrations
        run: |
          cd backend
          python run_migrations.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SQLALCHEMY_ECHO: 'False'
```

---

## Database Hosting (PostgreSQL)

### Option 1: Neon (Recommended - Easiest)

**Pros**: Serverless PostgreSQL, generous free tier, auto-scaling, backups included
**Free Tier**: 3 projects, 3GB storage, 20 connections
**Cost**: Free tier → ~$15/month (production)

#### Setup Steps:

1. **Create Account**: https://console.neon.tech/
2. **Create Project**:
   - Project name: `academic-analyzer`
   - Region: Closest to users
3. **Get Connection String**:
   - Dashboard → Connection string → Copy PostgreSQL connection
   - Format: `postgresql://user:password@host/database`

4. **Update GitHub Secret**:
   ```
   DATABASE_URL=postgresql://[user]:[password]@[host]/[database]?sslmode=require
   ```

5. **Initialize Database**:
   ```bash
   # Run from local machine first
   cd backend
   export DATABASE_URL="your-neon-connection-string"
   python setup_db.py
   ```

### Option 2: Railway

**Pros**: Simple CLI deployment, auto-deploys from GitHub, great free tier
**Free Tier**: Minimal usage (~$5 credit/month)
**Cost**: Pay-as-you-go (~$10-20/month production)

#### Setup Steps:

1. **Create Account**: https://railway.app/
2. **Link GitHub**: Settings → GitHub
3. **Create PostgreSQL Plugin**:
   - Dashboard → New Project → Add Plugin → PostgreSQL
4. **Get URL** from plugin dashboard
5. **Add to GitHub Secrets** as `DATABASE_URL`

### Option 3: Supabase (PostgreSQL + Auth)

**Pros**: Firebase-like experience, includes auth, real-time capabilities
**Free Tier**: 500MB, 2 GB bandwidth
**Cost**: Free → ~$25/month (production)

#### Setup Steps:

1. **Create Account**: https://supabase.com/
2. **New Project**: Fill in project details
3. **Copy Connection String**: Settings → Database → Connection string
4. **Add to GitHub Secrets**

---

## Backend Deployment (FastAPI)

### Option 1: Render (Recommended)

**Pros**: GitHub integration, auto-deploys, free tier, easy environment variables
**Free Tier**: 1 free web service, 750 compute hours/month
**Cost**: Free → ~$20/month (production)

#### Setup Steps:

1. **Create Account**: https://render.com/
2. **Connect GitHub**:
   - Dashboard → GitHub → Authorize
3. **Create Web Service**:
   - New → Web Service
   - Select repository: `your-repo`
   - Name: `academic-analyzer-api`
   - Environment: `Python`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
4. **Set Environment Variables**:
   - Runtime settings → Environment
   - Add each secret from GitHub:
     - `DATABASE_URL`
     - `GOOGLE_API_KEY`
     - `SECRET_KEY`
     - `LANGCHAIN_API_KEY`
     - `ENVIRONMENT=production`
5. **Enable Auto-Deploy**:
   - Settings → Auto-Deploy: Yes
6. **Note the URL**: `https://academic-analyzer-api.onrender.com`

#### Render Dockerfile (Optional, for production):

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY setup_db.py run_migrations.py ./

ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
```

Add to Render settings:
- Build command: `docker build -t academic-analyzer .`
- Start command: `docker run -p 10000:10000 academic-analyzer`

### Option 2: Railway

**Pros**: Simple, free credit, good GitHub integration
**Cost**: Free credit (~$5/month) → pay-as-you-go

#### Setup Steps:

1. **Create Account**: https://railway.app/
2. **New Project → Deploy from GitHub**
3. **Select `backend` folder as root**
4. **Railway auto-detects FastAPI**
5. **Add Environment Variables** from secrets
6. **Deploy** - Railway handles everything automatically

### Option 3: Fly.io

**Pros**: Geographically distributed, fast deployments, generous free tier
**Cost**: Free tier included, ~$5-15/month (production)

#### Setup Steps:

1. **Install Fly CLI**: `brew install flyctl` (macOS)
2. **Login**: `flyctl auth login`
3. **Initialize**: `flyctl launch` (from backend directory)
4. **Set secrets**:
   ```bash
   flyctl secrets set DATABASE_URL="postgresql://..."
   flyctl secrets set GOOGLE_API_KEY="..."
   flyctl secrets set SECRET_KEY="..."
   ```
5. **Deploy**: `flyctl deploy`

Create `backend/fly.toml`:

```toml
app = "academic-analyzer-api"

[build]
  builder = "paketobuildpacks"

[[services]]
  internal_port = 8000
  processes = ["app"]

  [services.concurrency]
    soft_limit = 1024
    hard_limit = 4096

[env]
  PYTHONUNBUFFERED = "1"
  ENVIRONMENT = "production"
```

---

## Frontend Deployment (React)

### Option 1: Vercel (Recommended)

**Pros**: Optimized for Next.js/React, serverless, instant deployments, analytics
**Free Tier**: Unlimited deployments, analytics included
**Cost**: Free → ~$20/month (optional pro features)

#### Setup Steps:

1. **Create Account**: https://vercel.com/
2. **Import Project**:
   - Import Git Repository
   - Select your GitHub repo
   - Project name: `academic-analyzer-frontend`
3. **Build Settings**:
   - Framework: `Vite`
   - Build command: `npm run build`
   - Output directory: `dist`
   - Root directory: `frontend`
4. **Environment Variables**:
   - Add: `VITE_API_BASE_URL` = `https://academic-analyzer-api.onrender.com`
5. **Deploy** - Vercel auto-deploys on push to `main`
6. **Get URL**: `https://academic-analyzer-frontend.vercel.app`

### Option 2: Netlify

**Pros**: Simple, free tier, includes CI/CD, forms support
**Cost**: Free → ~$20/month

#### Setup Steps:

1. **Create Account**: https://netlify.com/
2. **Connect Git Repository**
3. **Build Configuration**:
   - Build command: `cd frontend && npm run build`
   - Publish directory: `frontend/dist`
4. **Set Environment**:
   - Site settings → Build & deploy → Environment
   - Add `VITE_API_BASE_URL`
5. **Deploy** - Auto-deploys on push
6. **Custom Domain** (optional):
   - Site settings → Domain management → Add custom domain

Create `netlify.toml` in root:

```toml
[build]
  command = "cd frontend && npm run build"
  publish = "frontend/dist"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Option 3: GitHub Pages

**Pros**: Free, easy, no configuration needed
**Cons**: Static only (no server-side routing)

#### Setup Steps:

1. **Enable GitHub Pages**:
   - Settings → Pages → Source: GitHub Actions
2. **Create** `.github/workflows/pages.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build
      - uses: actions/upload-pages-artifact@v2
        with:
          path: frontend/dist
      - uses: actions/deploy-pages@v2
```

3. **Update vite.config.js**:
```javascript
export default {
  base: '/ai-powered-academic-performance-analyser/',
  // ... rest of config
}
```

---

## Environment Configuration

### Backend Environment Variables

Create `.env.production` in `backend/`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@neon-host/dbname?sslmode=require

# JWT
SECRET_KEY=your-super-secret-key-change-this-in-production-to-random-string-32-chars-min
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_TITLE=AI Academic Performance Analyzer
API_VERSION=1.0.0
ENVIRONMENT=production

# AI/ML
GOOGLE_API_KEY=your-actual-google-api-key
LANGCHAIN_API_KEY=your-langchain-api-key

# CORS (Update to your frontend URL)
CORS_ORIGINS=https://academic-analyzer-frontend.vercel.app

# Database Connection Pooling
SQLALCHEMY_POOL_SIZE=5
SQLALCHEMY_MAX_OVERFLOW=10
SQLALCHEMY_ECHO=False
```

### Frontend Environment Variables

Create `.env.production` in `frontend/`:

```bash
VITE_API_BASE_URL=https://academic-analyzer-api.onrender.com
VITE_APP_NAME=AI Academic Performance Analyzer
```

### Update CORS in Backend

Edit [app/main.py](app/main.py):

```python
import os

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Load from env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Deployment Workflows

### Workflow A: Quick Deployment (Render + Vercel + Neon)

This is the **fastest, lowest-maintenance setup**:

```
┌─────────────────────────┐
│   Push to main branch   │
└────────────┬────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌──────────────┐  ┌──────────────┐
│   Render     │  │  Vercel      │
│  (Backend)   │  │ (Frontend)   │
│  Auto-deploy │  │  Auto-deploy │
└──────────────┘  └──────────────┘
      │                 │
      │     Database    │
      │     (Neon)      │
      └────────┬────────┘
```

**Time to Production**: ~1 hour

**Steps**:
1. Create Neon database → copy URL to GitHub secrets
2. Deploy backend to Render → enable auto-deploy from GitHub
3. Deploy frontend to Vercel → add environment variable with backend URL
4. Push to main → both automatically deploy

### Workflow B: Advanced Deployment (Railway + Netlify)

```
┌──────────────────────┐
│  Push to main branch │
└────────┬─────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
┌────────┐   ┌───────┐
│Railway │   │Netlify│
│ API    │   │ Front │
│ DB     │   │       │
└────────┘   └───────┘
```

**Steps**:
1. `flyctl launch` from backend directory
2. `flyctl deploy`
3. Connect frontend repo to Netlify, select `frontend` as root
4. Done - both services auto-update on push

### Workflow C: Self-Hosted (Docker + VPS)

For maximum control, use DigitalOcean, Linode, AWS EC2:

Create `docker-compose.yml` in root:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: academic_analyser
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/academic_analyser
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
    depends_on:
      postgres:
        condition: service_healthy
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      VITE_API_BASE_URL: http://backend:8000
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: always

volumes:
  postgres_data:
```

---

## Monitoring & Maintenance

### 1. Backend Monitoring

#### Render Built-in Monitoring:
- Dashboard → Service → Logs tab
- View real-time logs and deployment status
- HTTP metrics and error rates

#### Add Health Endpoint Status:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500
```

#### GitHub Checks:
- Push to main triggers CI/CD workflows
- View workflow runs: **Actions** tab
- Failed deployment → check logs immediately

### 2. Database Monitoring

#### Neon Console:
- Monitor CPU, memory, storage at https://console.neon.tech/
- Set up backup retention

#### Query Logs:
```bash
# SSH into Neon and check logs
psql postgresql://user@host/database
\dt  -- List tables
SELECT pg_size_pretty(pg_total_relation_size(datname)) FROM pg_database WHERE datname = 'academic_analyser';
```

### 3. Frontend Monitoring

#### Vercel Analytics:
- Dashboard shows Web Vitals, build metrics
- Track performance over time

#### Error Tracking:
- Add Sentry for error monitoring:
```bash
npm install @sentry/react
```

```javascript
// main.jsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: process.env.VITE_SENTRY_DSN,
  environment: "production"
});
```

### 4. Uptime Monitoring

Use free service: **UptimeRobot** or **Pingdom**

- Add monitors for:
  - `https://api.yourdomain.com/health`
  - `https://yourdomain.com`
- Get alerts if services go down

---

## Deployment Checklist

### Pre-Deployment
- [ ] Update CORS origins in backend
- [ ] Add all environment variables to GitHub Secrets
- [ ] Test locally with production database URL
- [ ] Run migrations locally first
- [ ] Test API endpoints with production database
- [ ] Build frontend: `npm run build`
- [ ] Verify `dist/` folder created
- [ ] Check for hardcoded localhost URLs

### Database Setup
- [ ] Create PostgreSQL database (Neon/Railway)
- [ ] Copy connection string to GitHub secret `DATABASE_URL`
- [ ] Run `python setup_db.py` with production database
- [ ] Verify tables created: `\dt` in psql

### Backend Deployment
- [ ] Create Render/Railway service
- [ ] Add environment variables
- [ ] Enable auto-deploy from GitHub
- [ ] Deploy and wait for success
- [ ] Test health endpoint: `/health`
- [ ] Test API: `/docs` (Swagger UI)
- [ ] Copy backend URL for frontend

### Frontend Deployment
- [ ] Create Vercel/Netlify project
- [ ] Set `VITE_API_BASE_URL` environment variable
- [ ] Deploy and wait for success
- [ ] Test frontend loads
- [ ] Test API calls work
- [ ] Check browser console for CORS errors

### Post-Deployment
- [ ] Monitor logs for errors (first 24 hours)
- [ ] Test all features: signup, login, upload, analysis
- [ ] Verify database backups enabled
- [ ] Set up uptime monitoring
- [ ] Configure custom domain (optional)
- [ ] Update README with production URLs
- [ ] Document any environment-specific configurations

---

## Cost Estimates

### Monthly Costs (Production Setup)

| Service | Free Tier | Production | Notes |
|---------|-----------|-----------|-------|
| **Database** (Neon) | $0 | $15 | 3GB storage, auto-scaling |
| **Backend** (Render) | $0 | $7 | Basic plan, 750 compute hours free |
| **Frontend** (Vercel) | $0 | $0 | Free tier includes pro features |
| **Domain** (Namecheap) | - | $10 | Email, WHOIS protection ~$4/year |
| **Monitoring** | $0 | $0 | UptimeRobot free tier |
| **Total** | **$0** | **~$25/month** | Very affordable! |

### Cost Optimization Tips

1. **Use Free Tiers**: Neon has 3GB free, Render has 750 hours free
2. **Database Optimization**: Index frequently queried columns
3. **Frontend**: Vercel includes free tier with analytics
4. **CDN**: Both Vercel and Netlify include built-in CDN
5. **Scaling**: Scale horizontally across Render's free tier before upgrading

---

## Troubleshooting

### CORS Errors
```
Access to XMLHttpRequest blocked by CORS policy
```
**Solution**: Update `CORS_ORIGINS` environment variable in backend to include frontend URL

### Database Connection Timeout
```
psycopg2.OperationalError: could not connect to server
```
**Solution**: 
- Check DATABASE_URL format includes `?sslmode=require`
- Verify Neon/Railway IP whitelist allows connections from Render

### Frontend Can't Reach API
```
Network request failed
```
**Solution**: 
- Check `VITE_API_BASE_URL` environment variable matches backend URL
- Verify backend service is running: `https://backend-url/health`

### Deployment Stuck
**Solution**: 
- Check GitHub Actions logs
- Verify all environment variables are in GitHub Secrets (not committed)
- Check Render/Vercel deployment logs

### Database Migration Failed
**Solution**:
```bash
# Check current schema
psql $DATABASE_URL
SELECT * FROM alembic_version;

# Manual migration
cd backend
export DATABASE_URL="your-prod-db"
python run_migrations.py
```

---

## Summary

| Step | Duration | Service |
|------|----------|---------|
| 1. Create Neon database | 5 min | Neon |
| 2. Deploy backend | 5 min | Render |
| 3. Deploy frontend | 5 min | Vercel |
| 4. Configure domain | 10 min | Domain registrar |
| 5. Set up monitoring | 5 min | UptimeRobot |
| **Total to production** | **~30 minutes** | |

**Next Steps**:
1. Start with GitHub setup (.github/workflows/)
2. Create Neon database, get connection string
3. Deploy backend to Render
4. Deploy frontend to Vercel
5. Monitor and iterate

This setup provides:
- ✅ Zero downtime deployments
- ✅ Automatic scaling
- ✅ Database backups
- ✅ SSL/HTTPS included
- ✅ CDN integrated
- ✅ Monitoring and alerting
- ✅ ~$25/month total cost
