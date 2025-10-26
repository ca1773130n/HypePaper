#!/bin/bash
# Quick deployment script for HypePaper

set -e

echo "🚀 HypePaper Deployment Helper"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo -e "${RED}Error: Please run this script from the HypePaper root directory${NC}"
    exit 1
fi

echo -e "${BLUE}What would you like to do?${NC}"
echo ""
echo "1) Deploy both frontend and backend (recommended)"
echo "2) Deploy frontend only (Cloudflare Pages)"
echo "3) Deploy backend only (Railway)"
echo "4) Run local build test"
echo "5) Check deployment status"
echo "6) View deployment logs"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo -e "${GREEN}Deploying both frontend and backend...${NC}"
        git add .
        read -p "Enter commit message: " commit_msg
        git commit -m "$commit_msg"

        echo -e "${BLUE}Pushing to GitHub...${NC}"
        git push origin $(git branch --show-current)

        echo -e "${GREEN}✓ Pushed to GitHub!${NC}"
        echo ""
        echo "GitHub Actions will now:"
        echo "  1. Build and deploy frontend to Cloudflare Pages"
        echo "  2. Deploy backend to Railway"
        echo ""
        echo "View progress at:"
        echo "  https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
        ;;

    2)
        echo -e "${GREEN}Deploying frontend to Cloudflare Pages...${NC}"
        cd frontend
        echo -e "${BLUE}Building frontend...${NC}"
        npm run build

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Frontend built successfully!${NC}"
            echo ""
            echo "To deploy to Cloudflare Pages:"
            echo "  1. Go to https://dash.cloudflare.com"
            echo "  2. Navigate to Workers & Pages > Your project"
            echo "  3. Trigger manual deployment or push to main branch"
        else
            echo -e "${RED}✗ Frontend build failed${NC}"
            exit 1
        fi
        cd ..
        ;;

    3)
        echo -e "${GREEN}Deploying backend to Railway...${NC}"

        if command -v railway &> /dev/null; then
            railway up
            echo -e "${GREEN}✓ Backend deployed to Railway!${NC}"
        else
            echo -e "${YELLOW}Railway CLI not found. Installing...${NC}"
            npm install -g @railway/cli
            railway login
            railway up
        fi
        ;;

    4)
        echo -e "${BLUE}Running local build tests...${NC}"
        echo ""

        # Test frontend build
        echo -e "${BLUE}Testing frontend build...${NC}"
        cd frontend
        npm run build
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Frontend build successful${NC}"
        else
            echo -e "${RED}✗ Frontend build failed${NC}"
            exit 1
        fi
        cd ..

        # Test backend
        echo -e "${BLUE}Testing backend dependencies...${NC}"
        cd backend
        python3 -m pip install -r requirements.txt --quiet
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Backend dependencies OK${NC}"
        else
            echo -e "${RED}✗ Backend dependency installation failed${NC}"
            exit 1
        fi
        cd ..

        echo ""
        echo -e "${GREEN}✓ All local build tests passed!${NC}"
        ;;

    5)
        echo -e "${BLUE}Checking deployment status...${NC}"
        echo ""

        echo "Frontend (Cloudflare Pages):"
        echo "  Dashboard: https://dash.cloudflare.com"
        echo ""

        echo "Backend (Railway):"
        if command -v railway &> /dev/null; then
            railway status
        else
            echo "  Dashboard: https://railway.app/dashboard"
        fi
        echo ""

        echo "GitHub Actions:"
        echo "  https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
        ;;

    6)
        echo -e "${BLUE}View deployment logs...${NC}"
        echo ""
        echo "1) Frontend logs (Cloudflare Pages)"
        echo "2) Backend logs (Railway)"
        echo "3) GitHub Actions logs"
        echo ""
        read -p "Choose [1-3]: " log_choice

        case $log_choice in
            1)
                echo "Opening Cloudflare Pages dashboard..."
                open "https://dash.cloudflare.com" 2>/dev/null || xdg-open "https://dash.cloudflare.com" 2>/dev/null || echo "Visit: https://dash.cloudflare.com"
                ;;
            2)
                if command -v railway &> /dev/null; then
                    railway logs
                else
                    echo "Opening Railway dashboard..."
                    open "https://railway.app/dashboard" 2>/dev/null || xdg-open "https://railway.app/dashboard" 2>/dev/null || echo "Visit: https://railway.app/dashboard"
                fi
                ;;
            3)
                echo "Opening GitHub Actions..."
                repo_url=$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')
                open "https://github.com/$repo_url/actions" 2>/dev/null || xdg-open "https://github.com/$repo_url/actions" 2>/dev/null || echo "Visit: https://github.com/$repo_url/actions"
                ;;
        esac
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done! 🎉${NC}"
