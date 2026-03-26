# GitHub Secrets Setup Guide

This guide explains how to set up GitHub Secrets required for automated deployment.

## What are GitHub Secrets?

GitHub Secrets are encrypted environment variables stored in your repository. They're used to store sensitive information like API keys and database URLs without committing them to version control.

## Required Secrets

### 1. DATABASE_URL
**Value**: PostgreSQL connection string
**Example**: `postgresql://user:password@host:5432/dbname?sslmode=require`

**Where to get it**:
- **Neon**: https://console.neon.tech/ → Project → Connection string
- **Railway**: https://railway.app/ → PostgreSQL plugin → Variables
- **Supabase**: https://supabase.com/ → Settings → Database

### 2. GOOGLE_API_KEY
**Value**: Google GenerativeAI API Key
**Where to get it**: https://makersuite.google.com/app/apikey

**Steps**:
1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### 3. SECRET_KEY
**Value**: Strong random JWT secret (minimum 32 characters)

**Generate one**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. BACKEND_URL
**Value**: Your deployed backend URL
**Examples**:
- `https://academic-analyzer-api.onrender.com` (Render)
- `https://api.yourdomain.com` (Custom domain)

### 5. FRONTEND_URL
**Value**: Your deployed frontend URL
**Examples**:
- `https://academic-analyzer-frontend.vercel.app` (Vercel)
- `https://yourdomain.com` (Custom domain)

### 6. RENDER_API_KEY & RENDER_SERVICE_ID
**Only needed if deploying backend to Render**

**Where to get**:
- **RENDER_API_KEY**: https://dashboard.render.com/account/api-tokens
- **RENDER_SERVICE_ID**: Render dashboard → Service → Settings (look in URL: `srv-xxxxx`)

### 7. VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID
**Only needed if deploying frontend to Vercel**

**Where to get**:
- **VERCEL_TOKEN**: https://vercel.com/account/tokens
- **VERCEL_ORG_ID**: Vercel dashboard → Settings → General (Org ID)
- **VERCEL_PROJECT_ID**: Vercel dashboard → Project → Settings → General (Project ID)

### 8. LANGCHAIN_API_KEY (Optional)
**Value**: LangChain API key (if using LangChain features)
**Where to get**: https://www.langchain.com/ (optional, can leave blank)

## How to Add Secrets

### Using GitHub CLI (Easiest)

```bash
# Make sure you're authenticated
gh auth login

# Add a secret
gh secret set GITHUB_SECRET_NAME
# Paste the value and press Ctrl+D

# Example:
gh secret set DATABASE_URL
# Paste: postgresql://user:password@host/db
# Press Ctrl+D
```

### Using GitHub Web Interface

1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `SECRET_NAME` (e.g., `DATABASE_URL`)
5. Value: Paste the secret value
6. Click "Add secret"

### Using Deployment Script

```bash
# Make the script executable
chmod +x deploy.sh

# Run the interactive deployment script
./deploy.sh

# Follow the prompts to add all secrets
```

## Verification

### Verify Secrets are Set

```bash
# List all secrets (values are hidden)
gh secret list

# Output example:
# DATABASE_URL       Updated 2024-03-20
# GOOGLE_API_KEY     Updated 2024-03-20
# SECRET_KEY         Updated 2024-03-20
# ...
```

### Check Workflow Runs

After pushing to `main`, check if workflows run:

```bash
# View recent workflow runs
gh run list --limit 5

# View logs for a specific run
gh run view <RUN_ID>

# Watch logs in real-time
gh run watch
```

## Security Best Practices

1. **Never commit secrets**: Use `.env.example` for reference, not actual secrets
2. **Rotate regularly**: Update passwords and API keys periodically
3. **Use service accounts**: For databases, create dedicated service accounts
4. **Limit permissions**: Restrict scope of API keys to minimum needed
5. **Monitor access**: Review workflow logs for any suspicious activities
6. **Use environment-specific secrets**: Different values for dev/prod

## Troubleshooting

### "Secrets are not found" error in workflow

**Solution**: 
- Verify secret names exactly match in workflow files
- Check secret was actually created: `gh secret list`
- Secrets must be added before commit that uses them

### API Key not working

**Solution**:
- Copy the exact value without extra spaces
- Re-generate the key if it was shared/exposed
- Check API key expiration date

### Database connection timeout

**Solution**:
- Verify DATABASE_URL format is correct
- Check if IP whitelist allows your server
- Ensure sslmode is included for cloud databases

### Workflow triggers but deployment fails

**Solution**:
- Check workflow logs: Actions tab → Select workflow → View logs
- Verify all required secrets are set
- Check service (Render/Vercel) is accessible

## Example Complete Setup

```bash
# 1. Generate strong secret
STRONG_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Set all required secrets
gh secret set DATABASE_URL < <(echo "postgresql://user:pass@host/db")
gh secret set GOOGLE_API_KEY < <(echo "AIzaSyB...")
gh secret set SECRET_KEY < <(echo "$STRONG_SECRET")
gh secret set BACKEND_URL < <(echo "https://api.yourdomain.com")
gh secret set FRONTEND_URL < <(echo "https://yourdomain.com")

# 3. Verify
gh secret list

# 4. Push to trigger workflows
git push origin main

# 5. Monitor
gh run watch
```

## Next Steps

1. ✅ Set up all required secrets
2. ✅ Push to main branch
3. ✅ Check workflow runs in Actions tab
4. ✅ Verify deployment URLs work
5. ✅ Test the deployed application
6. ✅ Set up custom domain (optional)
