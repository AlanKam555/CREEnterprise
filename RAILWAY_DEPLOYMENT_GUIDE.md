# How to Deploy the CRE-Enterprise Project on Railway

This guide provides step-by-step instructions for deploying the CRE-Enterprise (Commercial Real Estate Analysis Platform) on Railway.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure Overview](#project-structure-overview)
3. [Step 1: Prepare Your Repository](#step-1-prepare-your-repository)
4. [Step 2: Create a Railway Account](#step-2-create-a-railway-account)
5. [Step 3: Create a New Project](#step-3-create-a-new-project)
6. [Step 4: Deploy the Backend Service](#step-4-deploy-the-backend-service)
7. [Step 5: Deploy the Frontend Service](#step-5-deploy-the-frontend-service)
8. [Step 6: Configure Environment Variables](#step-6-configure-environment-variables)
9. [Step 7: Set Up Database](#step-7-set-up-database)
10. [Step 8: Configure Custom Domain (Optional)](#step-8-configure-custom-domain-optional)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- A [GitHub](https://github.com) account
- The CRE-Enterprise code pushed to a GitHub repository
- A [Railway](https://railway.app) account (you can sign up with GitHub)
- Basic familiarity with command line tools

---

## Project Structure Overview

The CRE-Enterprise project consists of:

```
CREEnterprise/
├── backend/          # FastAPI Python backend
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   └── cre.db       # SQLite database
├── frontend/         # React + Vite frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── mobile/          # React Native mobile app (optional)
```

**Note:** For Railway deployment, we'll focus on deploying the backend and frontend services.

---

## Step 1: Prepare Your Repository

### 1.1 Add a `railway.toml` Configuration File

Create a `railway.toml` file in the root of your repository:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

### 1.2 Add a `Procfile` (Alternative)

If you prefer using a Procfile, create one in the root:

```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 1.3 Update Backend CORS Settings

Ensure your `backend/main.py` allows Railway domains:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "https://*.railway.app",   # Railway deployments
        "https://your-custom-domain.com"  # Your custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 1.4 Create a Health Check Endpoint

Add a health check endpoint to `backend/main.py`:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cre-enterprise-backend"}
```

### 1.5 Update Frontend API URL

In your frontend code, update the API base URL to use environment variables:

```javascript
// frontend/src/api.js or similar
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

### 1.6 Commit and Push Changes

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

---

## Step 2: Create a Railway Account

1. Go to [https://railway.app](https://railway.app)
2. Click **"Get Started"** or **"Login"**
3. Choose **"Continue with GitHub"**
4. Authorize Railway to access your GitHub repositories
5. Complete the onboarding process

---

## Step 3: Create a New Project

### Option A: Deploy from GitHub (Recommended)

1. From the Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. If prompted, install the Railway GitHub App and grant access to your repository
4. Search for and select your `cre-enterprise` repository
5. Click **"Deploy Now"**

### Option B: Deploy from Template

If you have a Railway template JSON, you can use:

1. Go to your project dashboard
2. Click **"New"** → **"Service"**
3. Select **"Deploy from GitHub"**

---

## Step 4: Deploy the Backend Service

### 4.1 Configure the Backend Service

1. Once the project is created, you'll see your service on the canvas
2. Click on the service to open its settings
3. Go to the **"Settings"** tab

### 4.2 Set Build and Start Commands

In the service settings:

- **Build Command:** (Leave empty if using `railway.toml` or Nixpacks auto-detection)
- **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

### 4.3 Configure Health Checks

1. In the service settings, find **"Healthcheck"**
2. Set **Healthcheck Path:** `/health`
3. Set **Healthcheck Timeout:** `100` seconds

### 4.4 Deploy the Backend

1. Click **"Deploy"** in the top right
2. Wait for the deployment to complete (you'll see logs in real-time)
3. Once deployed, note the backend URL (e.g., `https://backend-service-name.up.railway.app`)

---

## Step 5: Deploy the Frontend Service

### 5.1 Create a New Service for Frontend

1. In your Railway project, click **"New"** → **"Service"**
2. Select **"GitHub Repo"**
3. Choose the same repository
4. This will create a second service

### 5.2 Configure Frontend Service Settings

1. Click on the new frontend service
2. Go to **"Settings"**
3. Set the **Root Directory:** `frontend`
4. **Build Command:** `npm install && npm run build`
5. **Start Command:** `npx serve -s dist -l $PORT`

### 5.3 Install Serve Package (Alternative)

Alternatively, add `serve` to your `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "start": "serve -s dist -l $PORT"
  },
  "dependencies": {
    "serve": "^14.0.0"
  }
}
```

Then set **Start Command:** `npm start`

### 5.4 Deploy the Frontend

1. Click **"Deploy"**
2. Wait for the build and deployment to complete
3. Note the frontend URL

---

## Step 6: Configure Environment Variables

### 6.1 Backend Environment Variables

Click on your backend service → **"Variables"** tab → **"New Variable"**

Add the following variables:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `DATABASE_URL` | Database connection string | `sqlite:///./cre.db` or PostgreSQL URL |
| `SECRET_KEY` | JWT secret key | `your-super-secret-key-here` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://frontend-url.up.railway.app` |
| `ENVIRONMENT` | Environment name | `production` |

### 6.2 Frontend Environment Variables

Click on your frontend service → **"Variables"** tab

Add:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `VITE_API_URL` | Backend API URL | `https://backend-service.up.railway.app` |

**Note:** For Vite projects, environment variables must start with `VITE_` to be exposed to the client.

### 6.3 Redeploy After Adding Variables

After adding environment variables, Railway will automatically redeploy your services.

---

## Step 7: Set Up Database

### Option A: SQLite (Simple, for testing)

If using SQLite, no additional setup is needed. The database file will be created in the container.

**⚠️ Warning:** SQLite data will be lost if the container restarts. For production, use PostgreSQL.

### Option B: PostgreSQL (Recommended for Production)

1. In your Railway project, click **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway will create and configure a PostgreSQL database
3. Go to the PostgreSQL service → **"Connect"** tab
4. Copy the `DATABASE_URL` or `DATABASE_PUBLIC_URL`
5. Paste it into your backend service's environment variables

### 7.1 Update Backend for PostgreSQL

Update `backend/models.py` or database configuration:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cre.db")

# Handle Railway's postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### 7.2 Run Database Migrations

If you have migration scripts, run them:

1. Go to your backend service
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. Click **"Shell"** tab
5. Run: `cd backend && python -c "from models import Base, engine; Base.metadata.create_all(bind=engine)"`

---

## Step 8: Configure Custom Domain (Optional)

### 8.1 Add a Custom Domain

1. Click on your service (frontend or backend)
2. Go to **"Settings"** → **"Domains"**
3. Click **"Generate Domain"** for a free Railway subdomain, or
4. Click **"Custom Domain"** to add your own domain
5. Follow the DNS configuration instructions

### 8.2 Update CORS and Environment Variables

After setting up custom domains, update:

1. Backend CORS origins to include your custom domain
2. Frontend `VITE_API_URL` to point to the backend custom domain

---

## Troubleshooting

### Issue: Deployment Fails

**Solution:**
- Check the deployment logs for error messages
- Verify your `requirements.txt` includes all dependencies
- Ensure your start command uses `$PORT` environment variable

### Issue: Backend Health Check Fails

**Solution:**
- Verify the `/health` endpoint exists and returns HTTP 200
- Check that the backend is binding to `0.0.0.0` not `127.0.0.1`
- Ensure the port is read from the `$PORT` environment variable

### Issue: Frontend Can't Connect to Backend

**Solution:**
- Verify `VITE_API_URL` is set correctly
- Check CORS settings in the backend include the frontend URL
- Ensure both services are deployed and running

### Issue: Database Connection Errors

**Solution:**
- Verify `DATABASE_URL` is set correctly
- For PostgreSQL, ensure the URL uses `postgresql://` not `postgres://`
- Check that the database service is running

### Issue: Environment Variables Not Working

**Solution:**
- Redeploy the service after adding variables
- For frontend, ensure variables start with `VITE_`
- Check that variables are set in the correct service

---

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway GitHub Integration](https://docs.railway.app/guides/github-autodeploys)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)

---

## Quick Reference Commands

```bash
# Local development
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Railway CLI (optional)
npm install -g @railway/cli
railway login
railway link
railway up
```

---

**Last Updated:** 2026-03-26  
**Version:** 1.0.0
