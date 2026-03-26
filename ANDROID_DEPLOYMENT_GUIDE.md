# How to Deploy the CRE-Enterprise Project on Android Phone

This guide provides step-by-step instructions for running the CRE-Enterprise (Commercial Real Estate Analysis Platform) on an Android phone using Termux and other tools.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Method 1: Run Backend + Frontend on Android (Termux)](#method-1-run-backend--frontend-on-android-termux)
4. [Method 2: Access Deployed Version via Mobile Browser](#method-2-access-deployed-version-via-mobile-browser)
5. [Method 3: Build Android APK with React Native](#method-3-build-android-apk-with-react-native)
6. [Troubleshooting](#troubleshooting)

---

## Overview

There are three ways to use CRE-Enterprise on your Android phone:

1. **Method 1:** Run the full stack (backend + frontend) directly on your Android device using Termux
2. **Method 2:** Access a cloud-deployed version through your mobile browser
3. **Method 3:** Build and install a native Android app (APK) using the React Native mobile code

---

## Prerequisites

### For Method 1 (Termux):
- Android 7.0+ (API level 24+)
- At least 2GB free storage
- Termux app from F-Droid (recommended) or Google Play
- Stable internet connection

### For Method 2 (Browser):
- Any modern Android browser (Chrome, Firefox, Samsung Internet)
- The app must be deployed to Railway/AWS/VPS first

### For Method 3 (Native APK):
- Android Studio or Android SDK
- Node.js and npm
- React Native CLI or Expo CLI
- USB debugging enabled on your phone

---

## Method 1: Run Backend + Frontend on Android (Termux)

This method runs the entire application stack locally on your Android device.

### Step 1: Install Termux

1. **Download Termux** from F-Droid (recommended):
   - Visit: https://f-droid.org/packages/com.termux/
   - Download and install the APK
   - *Note: The Google Play version is outdated and not recommended*

2. **Open Termux** and update packages:
   ```bash
   pkg update && pkg upgrade -y
   ```

### Step 2: Install Required Packages

```bash
# Install essential packages
pkg install -y git python nodejs-lts sqlite

# Verify installations
python --version
node --version
npm --version
```

### Step 3: Clone the Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/AlanKam555/cre-enterprise.git

# Enter the project directory
cd cre-enterprise
```

### Step 4: Set Up the Backend

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# If pip install fails, try installing packages individually:
pip install fastapi uvicorn sqlalchemy pydantic python-jose passlib python-multipart
pip install scikit-learn pandas PyPDF2 openpyxl
```

### Step 5: Configure Backend for Mobile

Edit `backend/main.py` to allow mobile access:

```bash
# Install nano or use vim
pkg install nano

# Edit main.py
nano main.py
```

Update the CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for mobile testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Save and exit (Ctrl+X, then Y, then Enter).

### Step 6: Start the Backend Server

```bash
# Make sure you're in the backend directory and virtual environment is active
source venv/bin/activate

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at:
- Local: `http://localhost:8000`
- On your phone: `http://127.0.0.1:8000`

**Keep this terminal running.** Open a new Termux session for the frontend.

### Step 7: Set Up the Frontend (New Termux Session)

Swipe right from the left edge in Termux and tap **"New Session"**:

```bash
# Navigate to frontend
cd ~/cre-enterprise/frontend

# Install dependencies
npm install

# If npm install fails due to memory, try:
npm install --legacy-peer-deps

# Or use yarn if installed:
pkg install yarn
yarn install
```

### Step 8: Configure Frontend API URL

Edit the frontend configuration to point to the local backend:

```bash
# Find and edit the API configuration file
# Common locations:
nano src/api.js
# or
nano src/config.js
# or
nano src/App.jsx
```

Update the API base URL:

```javascript
const API_BASE_URL = 'http://localhost:8000';
// or
const API_URL = 'http://127.0.0.1:8000';
```

### Step 9: Start the Frontend Development Server

```bash
# In the frontend directory
npm run dev
```

The frontend will start on `http://localhost:5173` (or similar).

### Step 10: Access the Application

1. **On the same device:** Open your Android browser and go to:
   ```
   http://localhost:5173
   ```

2. **From another device on the same network:**
   - Find your phone's IP address:
     ```bash
     # In Termux
     ifconfig
     # or
     ip addr show
     ```
   - Access via: `http://YOUR_PHONE_IP:5173`

---

## Method 2: Access Deployed Version via Mobile Browser

If you've deployed CRE-Enterprise to Railway, AWS, or another cloud provider:

### Step 1: Get the Deployed URL

- Railway: `https://your-project-name.up.railway.app`
- Custom domain: `https://your-domain.com`

### Step 2: Access on Android

1. Open Chrome, Firefox, or any mobile browser
2. Enter the deployed URL
3. The app should load and function normally

### Step 3: Add to Home Screen (PWA)

1. Open the deployed URL in Chrome
2. Tap the **menu (⋮)** → **"Add to Home screen"**
3. Name it "CRE Enterprise"
4. Tap **"Add"**

Now you have an app-like icon on your home screen that opens the full application.

---

## Method 3: Build Android APK with React Native

This method creates a native Android app from the mobile codebase.

### Step 1: Prepare Your Computer

You'll need a computer (Windows/Mac/Linux) with:
- Node.js 16+ installed
- Android Studio or Android SDK
- Java JDK 11+

### Step 2: Set Up React Native Environment

On your computer:

```bash
# Install React Native CLI
npm install -g react-native-cli

# Or use Expo (easier for beginners)
npm install -g expo-cli
```

### Step 3: Prepare the Mobile Code

```bash
# Clone the repository
git clone https://github.com/AlanKam555/cre-enterprise.git
cd cre-enterprise/mobile

# Install dependencies
npm install
```

### Step 4: Configure API Endpoint

Edit the API configuration in the mobile app:

```javascript
// Find the API base URL configuration
// Usually in App.js, config.js, or api.js

const API_BASE_URL = 'https://your-backend-url.railway.app';
// or for local testing:
// const API_BASE_URL = 'http://YOUR_COMPUTER_IP:8000';
```

### Step 5: Build the APK (Using Expo - Easiest Method)

```bash
# Install Expo tools
npm install -g expo-cli

# Login to Expo
expo login

# Configure app.json
{
  "expo": {
    "name": "CRE Enterprise",
    "slug": "cre-enterprise",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain"
    },
    "android": {
      "package": "com.yourcompany.creenterprise",
      "versionCode": 1
    }
  }
}

# Build the APK
expo build:android -t apk

# Or using EAS (Expo Application Services)
npm install -g eas-cli
eas build --platform android --profile preview
```

### Step 6: Build the APK (Using React Native CLI)

```bash
# Navigate to android directory
cd android

# Make gradlew executable (Linux/Mac)
chmod +x gradlew

# Build the release APK
./gradlew assembleRelease

# The APK will be at:
# android/app/build/outputs/apk/release/app-release.apk
```

### Step 7: Install APK on Android Phone

**Method A: Direct Download**
1. Transfer the APK to your phone (USB, email, cloud storage)
2. On your phone, enable **"Install from unknown sources"**:
   - Settings → Security → Unknown Sources (or Install unknown apps)
3. Open the APK file and install

**Method B: ADB (Android Debug Bridge)**
```bash
# Connect phone via USB with debugging enabled
adb devices

# Install the APK
adb install android/app/build/outputs/apk/release/app-release.apk
```

**Method C: Expo Go (Development)**
1. Install Expo Go app from Play Store
2. Run `expo start` on your computer
3. Scan the QR code with Expo Go

---

## Troubleshooting

### Issue: Termux Packages Won't Install

**Solution:**
```bash
# Update package lists
pkg update

# Fix repository issues
termux-change-repo
# Select a mirror and try again
```

### Issue: Python pip Install Fails

**Solution:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Install packages one by one
pip install fastapi
pip install uvicorn
# etc.

# If memory error occurs, increase Termux memory or install packages individually
```

### Issue: npm install Hangs or Fails

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Use legacy peer deps
npm install --legacy-peer-deps

# Or use yarn instead
pkg install yarn
yarn install
```

### Issue: Backend Won't Start

**Solution:**
```bash
# Check if port is already in use
lsof -i :8000

# Kill process using the port
kill -9 <PID>

# Or use a different port
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Issue: Frontend Can't Connect to Backend

**Solution:**
- Ensure backend is running (check Termux session)
- Verify API URL in frontend config uses `localhost` or `127.0.0.1`
- Check CORS settings allow the frontend origin
- Try accessing backend directly: `http://localhost:8000/docs`

### Issue: APK Build Fails

**Solution:**
```bash
# Clean build cache
cd android
./gradlew clean

# Rebuild
./gradlew assembleRelease

# Check Android SDK is properly configured
# Set ANDROID_HOME environment variable
export ANDROID_HOME=$HOME/Android/Sdk
```

### Issue: App Crashes on Launch

**Solution:**
- Check that API_BASE_URL is correctly set
- Verify the backend is accessible from your phone
- Check app permissions (Internet access)
- Review logs with `adb logcat`

---

## Performance Tips

### For Termux Method:
1. **Use a lightweight browser** like Via or Lightning Browser
2. **Close unused Termux sessions** to free memory
3. **Use a swap file** if running out of memory:
   ```bash
   pkg install swapspace
   ```
4. **Keep the device plugged in** - running servers drains battery

### For Native APK:
1. **Enable ProGuard** in `android/app/build.gradle` for smaller APK
2. **Use Hermes** JavaScript engine for better performance
3. **Optimize images** in the assets folder

---

## Security Considerations

⚠️ **Warning:** Running on Android with Method 1 is suitable for:
- Personal development and testing
- Demo purposes
- Offline access to the application

**Not recommended for:**
- Production use with sensitive data
- Multi-user scenarios
- Public-facing deployments

For production use, deploy to Railway/AWS and use Method 2 or 3.

---

## Quick Reference Commands

```bash
# Termux setup
pkg update && pkg upgrade -y
pkg install -y git python nodejs-lts sqlite nano

# Clone and setup
git clone https://github.com/AlanKam555/cre-enterprise.git
cd cre-enterprise

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (new session)
cd ~/cre-enterprise/frontend
npm install
npm run dev

# Find IP address
ifconfig

# Check ports
lsof -i :8000
lsof -i :5173
```

---

## Additional Resources

- [Termux Wiki](https://wiki.termux.com)
- [React Native Android Setup](https://reactnative.dev/docs/environment-setup)
- [Expo Documentation](https://docs.expo.dev)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

---

**Last Updated:** 2026-03-26  
**Version:** 1.0.0
