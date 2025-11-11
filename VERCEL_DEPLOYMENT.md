# IROP Re-accommodation Dashboard - Vercel Deployment Guide

## Overview
This guide will help you deploy the IROP (Irregular Operations) re-accommodation dashboard to Vercel. The system consists of:
- **Frontend**: React/Vite dashboard (deploy to Vercel)
- **Backend**: FastAPI service (deploy to Railway/Render/fly.io)

## Prerequisites
- Vercel account
- Railway account (for backend)
- GitHub repository

## Backend Deployment Strategy

### Option 1: Railway (Recommended)
Railway provides excellent FastAPI support and integrates well with Vercel.

1. **Create Railway Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Initialize in backend directory
   cd backend
   railway init
   ```

2. **Deploy to Railway**
   ```bash
   # Add environment variables
   railway variables set FLIGHT_MONITOR_MODE=synthetic
   railway variables set AGENTIC_ENABLED=false
   railway variables set LLM_PROVIDER=deepseek
   railway variables set DEEPSEEK_API_KEY=your-key
   
   # Deploy
   railway up
   ```

3. **Get Railway URL**
   After deployment, note your Railway app URL (e.g., `https://your-app.railway.app`)

### Option 2: Render
Render supports FastAPI deployment via Docker or buildpacks.

## Frontend Deployment to Vercel

### 1. Connect Repository
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Select the `frontend/dashboard` directory as the project root

### 2. Configure Environment Variables
In Vercel project settings, add:
```
VITE_MONITOR_API=https://your-railway-app.railway.app
```

### 3. Build Settings
- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `build`
- **Install Command**: `npm install`

### 4. Deploy
Click "Deploy" and Vercel will automatically build and deploy your frontend.

## Alternative: Vercel + FastAPI (Serverless)

### FastAPI on Vercel with serverless functions
For a single-platform deployment, you can convert the FastAPI backend to Vercel serverless functions.

#### 1. Install Vercel Python adapter
```bash
pip install vercel
```

#### 2. Create `api/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vercel import app

# FastAPI app
api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import your routes
from app.routes import reaccommodation, agentic

api.include_router(reaccommodation.router)
api.include_router(agentic.router)

@api.get("/health")
def health():
    return {"status": "ok"}

# Mount FastAPI to Vercel
app.mount("/", api)
```

#### 3. Add `vercel.json` to backend
```json
{
  "functions": {
    "api/main.py": {
      "runtime": "python3.9"
    }
  }
}
```

#### 4. Update Vercel Configuration
Update `frontend/dashboard/vercel.json` to point to the same domain:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "framework": "vite",
  "public": true,
  "env": {
    "VITE_MONITOR_API": "https://your-vercel-app.vercel.app"
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/$1"
    }
  ]
}
```

## Post-Deployment Steps

### 1. Update Environment Variables
- Set `VITE_MONITOR_API` in Vercel to your backend URL
- For Railway: `https://your-app.railway.app`
- For serverless: `https://your-vercel-app.vercel.app`

### 2. Test Deployment
1. Visit your Vercel URL
2. Check that the dashboard loads
3. Verify API calls work by checking browser dev tools
4. Test IROP signals display
5. Test passenger suggestions functionality

### 3. Custom Domain (Optional)
1. In Vercel dashboard, go to project Settings
2. Add your custom domain
3. Update DNS records as instructed
4. Update `VITE_MONITOR_API` to use custom domain

## Environment Variables Reference

### Frontend (Vercel)
- `VITE_MONITOR_API`: Backend API URL

### Backend (Railway/Render)
- `FLIGHT_MONITOR_MODE`: synthetic|mongo|realtime
- `AGENTIC_ENABLED`: true|false
- `LLM_PROVIDER`: deepseek|openai|openrouter|gemini
- `DEEPSEEK_API_KEY`: Your DeepSeek API key
- `MONGO_URI`: MongoDB connection string (if using mongo mode)

## Troubleshooting

### Frontend Issues
- **Build fails**: Check Node.js version compatibility
- **API calls fail**: Verify `VITE_MONITOR_API` URL
- **CORS errors**: Ensure backend allows Vercel domain

### Backend Issues
- **FastAPI startup errors**: Check environment variables
- **Database connections**: Verify MongoDB URI and network access
- **Memory issues**: Railway provides 512MB by default, may need upgrade

## Security Considerations
- Never commit API keys to repository
- Use environment variables for all sensitive data
- Enable CORS properly for production
- Consider rate limiting for public deployment

## Monitoring
- Vercel: Use built-in analytics and function logs
- Railway: Use Railway dashboard and logs
- Set up error tracking (Sentry, etc.) for production

## Cost Considerations
- **Vercel**: Free tier includes 100GB bandwidth, sufficient for most use cases
- **Railway**: Free tier includes 500 hours/month
- **MongoDB Atlas**: Free tier provides 512MB storage

## Support
For deployment issues:
1. Check platform-specific documentation
2. Review application logs
3. Verify all environment variables are set correctly
4. Test locally with production environment variables