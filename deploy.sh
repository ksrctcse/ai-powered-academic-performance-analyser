#!/bin/bash

# Deploy Script - Sets up GitHub Secrets and deploys the project
# Usage: ./deploy.sh --service backend --provider render

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if GitHub CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI is not installed"
        echo "Install from: https://cli.github.com/"
        exit 1
    fi
    print_success "GitHub CLI found"
}

# Get repository info
get_repo_info() {
    REPO_OWNER=$(gh repo view --json owner --jq .owner.login)
    REPO_NAME=$(gh repo view --json name --jq .name)
    print_info "Repository: $REPO_OWNER/$REPO_NAME"
}

# Set GitHub secret
set_github_secret() {
    local secret_name=$1
    local secret_value=$2
    
    echo -n "Setting $secret_name... "
    echo "$secret_value" | gh secret set "$secret_name"
    print_success "Set $secret_name"
}

# Setup GitHub Secrets
setup_github_secrets() {
    print_info "Setting up GitHub Secrets..."
    
    # Database URL
    read -p "Enter PostgreSQL connection string (DATABASE_URL): " database_url
    set_github_secret "DATABASE_URL" "$database_url"
    
    # Google API Key
    read -p "Enter Google API Key (GOOGLE_API_KEY): " google_api_key
    set_github_secret "GOOGLE_API_KEY" "$google_api_key"
    
    # JWT Secret
    read -p "Enter JWT Secret (SECRET_KEY): " secret_key
    set_github_secret "SECRET_KEY" "$secret_key"
    
    # Backend URL
    read -p "Enter Backend URL (BACKEND_URL): " backend_url
    set_github_secret "BACKEND_URL" "$backend_url"
    
    # Frontend URL
    read -p "Enter Frontend URL (FRONTEND_URL): " frontend_url
    set_github_secret "FRONTEND_URL" "$frontend_url"
    
    # Render API Key (if using Render)
    read -p "Enter Render API Key (optional): " render_api_key
    if [ -n "$render_api_key" ]; then
        set_github_secret "RENDER_API_KEY" "$render_api_key"
        read -p "Enter Render Service ID: " render_service_id
        set_github_secret "RENDER_SERVICE_ID" "$render_service_id"
    fi
    
    # Vercel tokens (if using Vercel)
    read -p "Enter Vercel Token (optional): " vercel_token
    if [ -n "$vercel_token" ]; then
        set_github_secret "VERCEL_TOKEN" "$vercel_token"
        read -p "Enter Vercel Org ID: " vercel_org_id
        set_github_secret "VERCEL_ORG_ID" "$vercel_org_id"
        read -p "Enter Vercel Project ID: " vercel_project_id
        set_github_secret "VERCEL_PROJECT_ID" "$vercel_project_id"
    fi
    
    print_success "All GitHub Secrets configured!"
}

# Deploy using Docker Compose
deploy_docker_compose() {
    print_info "Setting up Docker Compose deployment..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found!"
        exit 1
    fi
    
    # Ask for environment variables
    read -p "Enter PostgreSQL password: " db_password
    read -p "Enter Google API Key: " google_api_key
    read -p "Enter JWT Secret: " secret_key
    
    # Create .env file for docker-compose
    cat > .env.docker << EOF
POSTGRES_DB=academic_analyser
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$db_password
GOOGLE_API_KEY=$google_api_key
SECRET_KEY=$secret_key
ENVIRONMENT=production
VITE_API_BASE_URL=http://localhost:8000
EOF
    
    print_success "Created .env.docker"
    
    # Start services
    echo "Starting services with Docker Compose..."
    docker-compose up -d
    
    print_success "Docker Compose deployment started!"
    echo "Services:"
    echo "  - API: http://localhost:8000"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Database: localhost:5432"
    echo "  - Nginx: http://localhost:80"
}

# Main menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "AI Academic Performance Analyzer - Deploy"
    echo "=========================================="
    echo "1. Setup GitHub Secrets only"
    echo "2. Deploy with GitHub Actions (backend + frontend)"
    echo "3. Deploy with Docker Compose (local / self-hosted)"
    echo "4. View deployment status"
    echo "5. Exit"
    echo ""
}

main() {
    check_gh_cli
    get_repo_info
    
    while true; do
        show_menu
        read -p "Select option (1-5): " choice
        
        case $choice in
            1)
                setup_github_secrets
                ;;
            2)
                print_info "Ensuring GitHub Secrets are set..."
                setup_github_secrets
                print_info "Push to main branch to trigger automatic deployment"
                print_info "  git push origin main"
                ;;
            3)
                deploy_docker_compose
                ;;
            4)
                print_info "Checking deployment status..."
                gh run list -L 10
                ;;
            5)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
    done
}

main "$@"
