# 🚀 AI Academic Performance Analyzer - Deployment Guide

**Complete, production-ready deployment guide with GitHub Actions CI/CD automation.**

## 🎯 Quick Navigation

| Goal | Time | Difficulty | Document |
|------|------|-----------|----------|
| Deploy in 30 minutes | 30 min | ⭐ Easy | [Quick Start](#quick-start) |
| Step-by-step setup | 1-2 hrs | ⭐⭐ Medium | [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) |
| Complete reference | - | ⭐⭐⭐ Advanced | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| GitHub Secrets setup | 10 min | ⭐ Easy | [GITHUB_SECRETS_GUIDE.md](GITHUB_SECRETS_GUIDE.md) |

---

## 🚀 Quick Start (30 Minutes)

### 1️⃣ Prerequisites
```bash
# Install GitHub CLI
brew install gh  # macOS
# or follow github.com/cli/cli

# Authenticate
gh auth login
```

### 2️⃣ Setup GitHub Repository
```bash
cd ai-powered-academic-performance-analyser
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/repo.git
git branch -M main
git push -u origin main
```

### 3️⃣ Run Interactive Setup
```bash
chmod +x quick-deploy.sh
./quick-deploy.sh
```

The script will:
- ✅ Collect all necessary configuration
- ✅ Create GitHub Secrets automatically
- ✅ Guide you through Neon database setup
- ✅ Configure Render backend deployment
- ✅ Configure Vercel frontend deployment

### 4️⃣ Deploy
```bash
git push origin main
```

GitHub Actions will automatically:
- Build backend
- Build frontend
- Run tests
- Deploy to Render (backend)
- Deploy to Vercel (frontend)

### 5️⃣ Verify
- **Backend API**: `https://your-backend.onrender.com/docs`
- **Frontend**: `https://your-frontend.vercel.app`
- **Status**: Check GitHub Actions tab for workflow runs

---

## 📋 Architecture Overview

```ascii
┌──────────────────────────────────────────────────────────────────┐
│                    GitHub Repository                            │
│  ┌─────────────┐  ┌────────────┐  ┌──────────────────────────┐ │
│  │ GitHub      │  │ GitHub     │  │ GitHub Actions CI/CD     │ │
│  │ Actions     │  │ Secrets    │  │ (Auto-Deploy on Push)    │ │
│  │ Workflows   │  │ (.env vars)│  │                          │ │
│  └─────────────┘  └────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                    │                         │
    ┌────▼─────┐        ┌─────▼──────┐        ┌────────▼──────────┐
    │           │        │            │        │                   │
    │ Vercel    │        │  Render    │        │   Neon / Railway   │
    │(Frontend) │        │ (Backend)  │        │  (PostgreSQL DB)   │
    │           │        │            │        │                    │
    └───────────┘        └────────────┘        └────────────────────┘
         │                    │                         │
         └────────────────────┴─────────────────────────┘
                        Internet
                  (HTTPS / SSL included)
```

---

## 📚 Deployment Options

### Option A: Render + Vercel + Neon ✅ **Recommended**
- **Pros**: Free tier, easy setup, auto-deploy, no DevOps needed
- **Cost**: ~$25/month (starting free)
- **Setup Time**: 30 minutes
- **Docs**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md#scenario-1-using-render--vercel--neon-recommended---easiest)

### Option B: Railway + Netlify + Railway DB
- **Pros**: Simple CLI, generous free tier, auto-scaling
- **Cost**: Free → $20/month
- **Setup Time**: 30 minutes
- **Docs**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#option-2-railway)

### Option C: Self-Hosted Docker Compose
- **Pros**: Maximum control, run anywhere (VPS, local)
- **Cost**: $5-15/month (VPS)
- **Setup Time**: 1-2 hours
- **Docs**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md#scenario-2-self-hosted-with-docker-compose)

---

## 🔧 Available Tools & Scripts

### `quick-deploy.sh`
**Interactive setup script** - Collects config and sets GitHub Secrets automatically.
```bash
chmod +x quick-deploy.sh
./quick-deploy.sh
```

### `deploy.sh`
**Advanced deployment script** - For managing secrets and triggering deployments.
```bash
chmod +x deploy.sh
./deploy.sh
```

### GitHub Actions Workflows
Automatic CI/CD pipelines in `.github/workflows/`:
- `deploy-backend.yml` - Build & deploy FastAPI to Render
- `deploy-frontend.yml` - Build & deploy React to Vercel
- `db-migrations.yml` - Automated database migrations
- `test-backend.yml` - Python linting & testing
- `test-frontend.yml` - Node linting & build tests

### Docker Compose
**For self-hosted deployment**:
```bash
docker-compose up -d
```
Runs database, backend, frontend, and nginx in containers.

---

## 📖 Documentation Structure

### For First-Time Deployment
1. **Start Here**: [Quick Start](#quick-start) (10 min read)
2. **Then**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) (step-by-step, 30-60 min)
3. **Reference**: [GITHUB_SECRETS_GUIDE.md](GITHUB_SECRETS_GUIDE.md) (troubleshooting)

### For Advanced Setup
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete architecture & flows
2. [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Scenarios & checklists
3. Individual provider docs (Render, Vercel, Neon)

---

## 🔐 Required Secrets

All secrets stored safely in GitHub → No credentials in code:

| Secret | Example | Where to Get |
|--------|---------|--------------|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | Neon/Railway console |
| `GOOGLE_API_KEY` | `AIzaSyB...` | makersuite.google.com |
| `SECRET_KEY` | `random-32-char-string` | Generated with `quick-deploy.sh` |
| `BACKEND_URL` | `https://api.yourdomain.com` | Your backend domain |
| `FRONTEND_URL` | `https://yourdomain.com` | Your frontend domain |
| `RENDER_API_KEY` | From dashboard | render.com/account/api-tokens |
| `VERCEL_TOKEN` | From dashboard | vercel.com/account/tokens |

**Setup Guide**: [GITHUB_SECRETS_GUIDE.md](GITHUB_SECRETS_GUIDE.md)

---

## 📊 Cost Comparison

### Scenario: 100 DAU (Users/Day)

| Provider | Free Tier | Production | Notes |
|----------|-----------|-----------|-------|
| **Neon** (Database) | 3GB | $50 | PostgreSQL serverless |
| **Render** (Backend) | 750 hrs | $7 | 2vCPU, 512MB RAM |
| **Vercel** (Frontend) | ∞ | Free | Analytics included |
| **Railway** (Database) | $5 credit | $5-15 | Pay-as-you-go |
| **Railway** (Backend) | Included | Included | Generous free tier |
| **Domain** | - | $10/yr | Optional |
| **Monitoring** | Free | Free | UptimeRobot |
| **Total/Month** | **$0** | **~$25-35** | Very affordable! |

---

## ✅ Deployment Checklist

### Before Deployment
- [ ] Code committed & pushed to GitHub
- [ ] No hardcoded localhost URLs
- [ ] `.env.example` created (no secrets!)
- [ ] GitHub Secrets configured
- [ ] Database ready (Neon/Railway/PostgreSQL)

### After Deployment
- [ ] Backend API responding (`/health` endpoint)
- [ ] Frontend loads without errors
- [ ] Login/signup works end-to-end
- [ ] CORS errors resolved
- [ ] Database backups enabled
- [ ] Monitoring setup (UptimeRobot)
- [ ] Custom domain configured (optional)

**Full Checklist**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md#step-by-step-checklist)

---

## 🐛 Troubleshooting

### CORS Errors
```
Access to XMLHttpRequest blocked by CORS policy
```
**Fix**: Update `CORS_ORIGINS` environment variable to include frontend URL

### Database Connection Failed
```
psycopg2.OperationalError: could not connect to server
```
**Fix**: Verify DATABASE_URL includes `?sslmode=require` for cloud databases

### Frontend Can't Reach API
```
Network request failed
```
**Fix**: Check `VITE_API_BASE_URL` environment variable matches backend URL

**More solutions**: [DEPLOYMENT_GUIDE.md#troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 📈 Scaling Checklist

As your app grows:

### Database (Growth Path)
- Start: Neon Free Tier (3GB)
- Growth: Neon Professional ($50/mo, 10GB+)
- Scale: Managed PostgreSQL on AWS/Google Cloud

### Backend (Growth Path)
- Start: Render Free (750 hrs)
- Growth: Render Standard ($15-25/mo)
- Scale: Containerized on Kubernetes

### Frontend (Growth Path)
- Start: Vercel Free
- Growth: Vercel Pro ($20/mo)
- Scale: CDN edge caching

---

## 🔗 External Resources

### Deployment Providers
- **Render**: https://render.com/docs
- **Vercel**: https://vercel.com/docs
- **Railway**: https://railway.app/docs
- **Neon**: https://neon.tech/docs

### Frameworks & Tools
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Docker**: https://docs.docker.com/
- **GitHub Actions**: https://docs.github.com/en/actions

### Monitoring & Tools
- **UptimeRobot**: https://uptimerobot.com/
- **Sentry**: https://sentry.io/
- **GitHub CLI**: https://cli.github.com/

---

## 🤝 Getting Help

### Documentation Flow
1. **Quick questions?** → [GITHUB_SECRETS_GUIDE.md](GITHUB_SECRETS_GUIDE.md)
2. **Step-by-step guidance?** → [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
3. **Deep dive?** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
4. **Troubleshooting?** → See Troubleshooting in respective doc

### Common Issues
- **"How do I get Google API Key?"** → GITHUB_SECRETS_GUIDE.md
- **"What's my Render Service ID?"** → IMPLEMENTATION_GUIDE.md
- **"CORS errors"** → DEPLOYMENT_GUIDE.md#troubleshooting
- **"Database won't connect"** → DEPLOYMENT_GUIDE.md#troubleshooting

---

## 🎓 Learn More

### Understanding the Architecture
- **Database hierarchy**: See copilot-instructions.md
- **API structure**: See DEPLOYMENT_GUIDE.md#api-structure-pattern
- **Auth flow**: See copilot-instructions.md#auth--security-pattern
- **File processing**: See copilot-instructions.md#file-processing-pattern

### Best Practices
- **Security**: Never commit .env files, use GitHub Secrets
- **CI/CD**: Push to main to trigger auto-deployment
- **Monitoring**: Setup uptime alerts from day 1
- **Backups**: Enable database backups immediately

---

## ✨ Next Steps

### For First-Time Users
1. Run `./quick-deploy.sh`
2. Wait for automatic deployment
3. Visit deployed application
4. Star this repo if helpful! ⭐

### For Advanced Users
1. Explore [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Setup multi-region deployment
3. Configure custom monitoring
4. Optimize for your scale

---

## 📝 Notes

- **All information is production-ready** - based on industry best practices
- **Zero downtime deployments** - automatic with CI/CD
- **Cost-effective** - start free, scale as needed
- **Open source** - all deployment tools are free/open
- **Fully automated** - GitHub Actions handle everything

---

## 🚀 You're Ready!

```bash
# 1. Setup
chmod +x quick-deploy.sh
./quick-deploy.sh

# 2. Deploy
git push origin main

# 3. Monitor
gh run watch

# 4. Access
# Frontend: https://your-frontend.vercel.app
# API: https://your-backend.onrender.com/docs
```

**Questions?** Check the documentation files above.
**Ready?** Start with the [Quick Start](#quick-start) section!

---

**Happy Deploying! 🎉**
