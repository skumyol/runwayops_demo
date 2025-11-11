#!/bin/bash

# IROP Re-accommodation Dashboard - Quick Deployment Script

set -e

echo "🚀 IROP Dashboard Deployment Script"
echo "=================================="

# Check if required tools are installed
command -v npm >/dev/null 2>&1 || { echo "❌ npm is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Aborting." >&2; exit 1; }

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Frontend Build Test${NC}"
cd frontend/dashboard

# Install dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Build frontend
echo "🏗️ Building frontend..."
npm run build

if [ -d "build" ]; then
    echo -e "${GREEN}✅ Frontend build successful!${NC}"
else
    echo -e "${RED}❌ Frontend build failed!${NC}"
    exit 1
fi

cd ../../

echo -e "${YELLOW}Step 2: Backend Setup${NC}"
cd backend

# Check if uv is available, if not try pip
if command -v uv >/dev/null 2>&1; then
    echo "📦 Installing backend dependencies with uv..."
    uv pip install -r requirements.txt
else
    echo "📦 Installing backend dependencies with pip..."
    pip install -r requirements.txt
fi

echo -e "${GREEN}✅ Backend setup complete!${NC}"

cd ../

echo -e "${YELLOW}Step 3: Environment Setup${NC}"
echo "Please ensure you have:"
echo "1. Railway account for backend (recommended)"
echo "2. Vercel account for frontend"
echo "3. Set your API keys in environment variables"
echo ""
echo -e "${GREEN}Deployment files created:${NC}"
echo "✅ frontend/dashboard/vercel.json - Vercel configuration"
echo "✅ frontend/dashboard/.env.example - Environment template"
echo "✅ VERCEL_DEPLOYMENT.md - Complete deployment guide"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Deploy backend to Railway:"
echo "   cd backend && railway up"
echo ""
echo "2. Deploy frontend to Vercel:"
echo "   - Connect your GitHub repo to Vercel"
echo "   - Select frontend/dashboard as project root"
echo "   - Set VITE_MONITOR_API to your Railway URL"
echo ""
echo "3. Read VERCEL_DEPLOYMENT.md for detailed instructions"

echo -e "${GREEN}🎉 Deployment preparation complete!${NC}"