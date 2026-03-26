# Quick Start Guide - How to Run CRE Enterprise

This guide explains how to start the CRE Enterprise application on your local machine.

---

## 🚀 Option 1: Double-Click start-app.bat (Recommended)

This is the easiest way to start the application.

### Step-by-Step Instructions

#### Step 1: Open File Explorer
- Press `Win + E` to open File Explorer
- Navigate to this folder:
  ```
  C:\Users\alank\.qclaw\workspace\CREEnterprise
  ```

#### Step 2: Find the start-app.bat File
You should see `start-app.bat` in the folder:

```
📁 CREEnterprise/
   ├── 📄 start-app.bat        ← Double-click this file
   ├── 📄 stop-app.bat
   ├── 📁 backend/
   ├── 📁 frontend/
   └── ...
```

#### Step 3: Double-Click start-app.bat
1. **Double-click** `start-app.bat`
2. A command prompt window will open and display:
   ```
   ==========================================
     CRE Enterprise Suite - Quick Start
   ==========================================
   
   [OK] Python and Node.js are installed
   
   [1/2] Starting Backend Server...
         Backend running at: http://localhost:8000
         API Documentation: http://localhost:8000/docs
   
   [2/2] Starting Frontend Server...
         Frontend running at: http://localhost:5173
   ```

#### Step 4: Wait for Servers to Start
Two terminal windows will open:

| Window | What it does |
|--------|--------------|
| **CRE Backend** | Runs FastAPI server on port 8000 |
| **CRE Frontend** | Runs Vite dev server on port 5173 |

Wait about **5-10 seconds** for both to fully start.

#### Step 5: Browser Opens Automatically
The script will:
1. Wait for you to **press any key**
2. Open `http://localhost:5173` in your default browser
3. You should see the CRE Enterprise application

---

## 🎯 What You Should See

### Frontend (http://localhost:5173)
- CRE Enterprise login page
- Click "Sign up" to create an account
- Fill in: Email, Username, Password
- After registration, login with your credentials

### Backend API (http://localhost:8000/docs)
- FastAPI interactive documentation
- All API endpoints listed
- Test API calls directly from browser

---

## ⚠️ Troubleshooting

### Problem: "Python not found"
**Solution:**
- Install Python 3.11+ from https://python.org
- Make sure to check "Add Python to PATH" during installation

### Problem: "Node.js not found"
**Solution:**
- Install Node.js 18+ from https://nodejs.org
- Download the LTS version

### Problem: "Port 8000 already in use"
**Solution:**
- Another application is using port 8000
- Close other applications or run `stop-app.bat` first

### Problem: "Port 5173 already in use"
**Solution:**
- Another application is using port 5173
- Close other applications or run `stop-app.bat` first

### Problem: Servers won't start
**Solution:**
1. Double-click `stop-app.bat` to stop any running servers
2. Wait 5 seconds
3. Double-click `start-app.bat` again

### Problem: "npm error ENOENT package.json"
**Solution:**
- Make sure you run `start-app.bat` from the correct folder:
  ```
  C:\Users\alank\.qclaw\workspace\CREEnterprise\
  ```
- NOT from `C:\Users\alank\OneDrive\` or any other folder

---

## 🛑 How to Stop the Application

### Option A: Double-click stop-app.bat
- Navigate to `C:\Users\alank\.qclaw\workspace\CREEnterprise\`
- Double-click `stop-app.bat`

### Option B: Close Terminal Windows
- Close the **CRE Backend** window
- Close the **CRE Frontend** window

---

## 🖥️ Create Desktop Shortcuts (Optional)

### Method 1: Right-Click Drag
1. Open File Explorer and go to:
   ```
   C:\Users\alank\.qclaw\workspace\CREEnterprise\
   ```
2. Find `start-app.bat`
3. **Right-click and drag** it to your desktop
4. Release mouse button
5. Select **"Create shortcuts here"**
6. Repeat for `stop-app.bat`

### Method 2: Create Shortcut Manually
1. Right-click on empty desktop space
2. Select **New → Shortcut**
3. Browse to or paste:
   ```
   C:\Users\alank\.qclaw\workspace\CREEnterprise\start-app.bat
   ```
4. Click **Next**
5. Name it: `🚀 Start CRE Enterprise`
6. Click **Finish**
7. Repeat for `stop-app.bat` (name: `🛑 Stop CRE Enterprise`)

---

## 📁 After Creating Desktop Shortcuts

Your desktop will look like:

```
🖥️ Desktop
├── 🚀 Start CRE Enterprise    ← Double-click to start
├── 🛑 Stop CRE Enterprise     ← Double-click to stop
└── ... (other icons)
```

| Action | What to do |
|--------|------------|
| **Start app** | Double-click `Start CRE Enterprise` |
| **Stop app** | Double-click `Stop CRE Enterprise` |

---

## 📋 Quick Reference

| URL | Description |
|-----|-------------|
| http://localhost:5173 | Frontend Application |
| http://localhost:8000 | Backend API Root |
| http://localhost:8000/docs | API Documentation (Swagger) |
| http://localhost:8000/redoc | API Documentation (ReDoc) |

---

## ✅ Sign Up / Login Instructions

### To Sign Up (New Users):
1. Go to http://localhost:5173
2. Click **"Sign up"** link below the Login button
3. Fill in:
   - **Email:** your-email@example.com
   - **Username:** your-username
   - **Password:** your-password (minimum 6 characters)
4. Click **"Sign Up"** button
5. You should see "Account created! You can now login."

### To Login:
1. Enter your **Email** (or Username)
2. Enter your **Password**
3. Click **"Login"** button
4. You will be taken to the Dashboard

---

## 🔄 Manual Start (Alternative)

If `start-app.bat` doesn't work, you can start manually:

### Start Backend:
```powershell
cd C:\Users\alank\.qclaw\workspace\CREEnterprise\backend
python -m uvicorn main:app --reload --port 8000
```

### Start Frontend (new terminal):
```powershell
cd C:\Users\alank\.qclaw\workspace\CREEnterprise\frontend
npm run dev
```

---

## 🐳 Docker Start (Alternative)

If you have Docker installed:

```powershell
cd C:\Users\alank\.qclaw\workspace\CREEnterprise
docker-compose up
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

**Last Updated:** 2026-03-26  
**Version:** 1.0.0
