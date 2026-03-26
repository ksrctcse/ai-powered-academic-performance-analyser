#!/bin/bash

# Quick Start Deployment Script
# This script automates the initial setup for deploying to Render + Vercel + Neon

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Banner
clear
cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║       AI Academic Performance Analyzer - Quick Deploy          ║
║                                                                ║
║  Automated setup for: Render (Backend) + Vercel (Frontend)    ║
║                     + Neon (Database)                         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
EOF

echo -e "\n${BLUE}📋 Prerequisites Check:${NC}\n"

# Check prerequisites
check_cmd() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅${NC} $2"
        return 0
    else
        echo -e "${RED}❌${NC} $2 - Install from $3"
        return 1
    fi
}

check_cmd "git" "Git" "https://git-scm.com"
check_cmd "gh" "GitHub CLI" "https://cli.github.com"
check_cmd "curl" "curl" "brew install curl"
check_cmd "python3" "Python" "https://python.org"

echo -e "\n${BLUE}🔐 GitHub Authentication:${NC}\n"

# Check GitHub login
if gh auth status &>/dev/null; then
    GITHUB_USER=$(gh api user --jq .login)
    echo -e "${GREEN}✅${NC} Logged in as: $GITHUB_USER"
else
    echo -e "${YELLOW}ℹ️  GitHub CLI not authenticated${NC}"
    echo "Run: gh auth login"
    exit 1
fi

echo -e "\n${BLUE}📂 Repository Setup:${NC}\n"

# Get repo info
REPO_URL=$(git config --get remote.origin.url)
REPO_NAME=$(basename -s .git "$REPO_URL")
REPO_OWNER=$(gh repo view --json owner --jq .owner.login)

echo "Repository: $REPO_OWNER/$REPO_NAME"
echo "Remote URL: $REPO_URL"

echo -e "\n${BLUE}🌐 Setup Summary:${NC}\n"
echo "This script will help you:"
echo "  1. Create databases on Neon"
echo "  2. Deploy backend to Render"
echo "  3. Deploy frontend to Vercel"
echo "  4. Configure GitHub Actions CI/CD"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 1: GitHub Secrets
echo -e "\n${BLUE}Step 1: Configure GitHub Secrets${NC}\n"

echo "Collecting required information..."
echo ""

read -p "PostgreSQL Password (secure, 12+ chars): " -s db_password
echo ""
read -p "Google API Key (from makersuite.google.com): " -s google_api_key
echo ""
read -p "JWT Secret (press Enter to auto-generate): " secret_key

if [ -z "$secret_key" ]; then
    secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "Generated: $secret_key"
fi

read -p "Backend URL (e.g., https://api.yourdomain.com): " backend_url
read -p "Frontend URL (e.g., https://yourdomain.com): " frontend_url

echo -e "\n${YELLOW}📝 Setting GitHub Secrets...${NC}"

# Create .env file for reference
cat > .env.reference << EOF
# This is for reference only - do NOT commit this file!
DATABASE_URL=postgresql://postgres:$db_password@[neon-host]/academic_analyser
GOOGLE_API_KEY=$google_api_key
SECRET_KEY=$secret_key
BACKEND_URL=$backend_url
FRONTEND_URL=$frontend_url
EOF

echo "Reference saved to .env.reference (DO NOT COMMIT)"

# Set GitHub secrets
echo "$db_password" | gh secret set POSTGRES_PASSWORD 2>/dev/null && echo -e "${GREEN}✅${NC} POSTGRES_PASSWORD"
echo "$google_api_key" | gh secret set GOOGLE_API_KEY 2>/dev/null && echo -e "${GREEN}✅${NC} GOOGLE_API_KEY"
echo "$secret_key" | gh secret set SECRET_KEY 2>/dev/null && echo -e "${GREEN}✅${NC} SECRET_KEY"
echo "$backend_url" | gh secret set BACKEND_URL 2>/dev/null && echo -e "${GREEN}✅${NC} BACKEND_URL"
echo "$frontend_url" | gh secret set FRONTEND_URL 2>/dev/null && echo -e "${GREEN}✅${NC} FRONTEND_URL"

# Step 2: Deploy backend to Render
echo -e "\n${BLUE}Step 2: Deploy Backend to Render${NC}\n"

echo "Before deploying backend to Render:"
echo "  1. Go to: https://render.com/"
echo "  2. Sign up / Login"
echo "  3. Go to https://render.com/api-tokens"
echo "  4. Create an API token and copy it"
echo ""

read -p "Paste your Render API Token (or submit to skip): " render_api_key

if [ -n "$render_api_key" ]; then
    read -p "Create backend service on Render? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "You'll need to:"
        echo "  1. Go to https://render.com/dashboard"
        echo "  2. New + Web Service"
        echo "  3. Connect to GitHub repository"
        echo "  4. Configure build/start commands from DEPLOYMENT_GUIDE.md"
        echo "  5. Copy the Service ID from the dashboard URL"
        echo ""
        read -p "Press Enter after creating the service on Render..."
        read -p "Paste the Render Service ID (srv-xxxxx): " render_service_id
        
        echo "$render_api_key" | gh secret set RENDER_API_KEY 2>/dev/null && echo -e "${GREEN}✅${NC} RENDER_API_KEY"
        echo "$render_service_id" | gh secret set RENDER_SERVICE_ID 2>/dev/null && echo -e "${GREEN}✅${NC} RENDER_SERVICE_ID"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping Render backend setup${NC}"
fi

# Step 3: Deploy frontend to Vercel
echo -e "\n${BLUE}Step 3: Deploy Frontend to Vercel${NC}\n"

echo "Before deploying to Vercel:"
echo "  1. Go to: https://vercel.com/"
echo "  2. Sign up / Login"
echo "  3. Go to https://vercel.com/account/tokens"
echo "  4. Create a token and copy it"
echo ""

read -p "Paste your Vercel Token (or submit to skip): " vercel_token

if [ -n "$vercel_token" ]; then
    read -p "Create frontend project on Vercel? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "You'll need to:"
        echo "  1. Go to https://vercel.com/dashboard"
        echo "  2. 'Add New...' → 'Project'"
        echo "  3. Import from GitHub repository"
        echo "  4. Set Root Directory: frontend"
        echo "  5. Copy the Org ID and Project ID from Settings"
        echo ""
        read -p "Press Enter after creating the project on Vercel..."
        read -p "Paste the Vercel Org ID: " vercel_org_id
        read -p "Paste the Vercel Project ID: " vercel_project_id
        
        echo "$vercel_token" | gh secret set VERCEL_TOKEN 2>/dev/null && echo -e "${GREEN}✅${NC} VERCEL_TOKEN"
        echo "$vercel_org_id" | gh secret set VERCEL_ORG_ID 2>/dev/null && echo -e "${GREEN}✅${NC} VERCEL_ORG_ID"
        echo "$vercel_project_id" | gh secret set VERCEL_PROJECT_ID 2>/dev/null && echo -e "${GREEN}✅${NC} VERCEL_PROJECT_ID"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping Vercel frontend setup${NC}"
fi

# Step 4: Database setup on Neon
echo -e "\n${BLUE}Step 4: Setup Database on Neon${NC}\n"

echo "To create database on Neon:"
echo "  1. Go to: https://console.neon.tech/"
echo "  2. Sign up / Login"
echo "  3. Create a new project"
echo "  4. Copy the PostgreSQL connection string"
echo ""

read -p "Paste the Neon connection string (postgresql://...): " database_url

if [ -n "$database_url" ]; then
    echo "$database_url" | gh secret set DATABASE_URL 2>/dev/null && echo -e "${GREEN}✅${NC} DATABASE_URL set"
fi

# Final summary
echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅  All GitHub Secrets Configured!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}\n"

echo "Configure the following on the respective platforms:"
echo ""
echo "📘 Render (Backend):"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: uvicorn app.main:app --host 0.0.0.0 --port 10000"
echo "   - Add all environment variables from GitHub Secrets"
echo "   - Enable Auto-Deploy from GitHub"
echo ""
echo "⚡ Vercel (Frontend):"
echo "   - Root Directory: frontend"
echo "   - Build Command: npm run build"
echo "   - Output Directory: dist"
echo "   - Add VITE_API_BASE_URL environment variable"
echo "   - Enable Auto-Deploy from GitHub"
echo ""
echo "🗄️  Neon (Database):"
echo "   - Run migrations: python backend/setup_db.py"
echo "   - Verify tables created"
echo ""

echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo "  1. Make sure your local changes are committed"
echo "  2. git push origin main"
echo "  3. Check GitHub Actions tab for workflow runs"
echo "  4. Wait for deployments to complete (~5-10 minutes)"
echo "  5. Visit your deployed applications:"
echo "     - Backend: $backend_url/docs"
echo "     - Frontend: $frontend_url"
echo ""

echo -e "${BLUE}📚 For detailed information, see: DEPLOYMENT_GUIDE.md${NC}\n"

# Cleanup
rm -f .env.reference

exit 0
