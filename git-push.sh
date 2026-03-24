#!/bin/bash
# CRE Enterprise Suite - Git Push Script

echo "=========================================="
echo "  CRE Enterprise Suite - Git Push"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git config user.name "alankam555"
    git config user.email "alankam1969@icloud.com"
fi

# Add all files
echo "Adding files to git..."
git add .

# Commit
echo "Committing changes..."
git commit -m "CRE Enterprise Suite v1.0 - Complete CRE Analysis Platform

Features:
- FastAPI backend with 30+ API endpoints
- React frontend with 5 professional pages
- React Native mobile app (iOS/Android)
- PDF export (Investment memos, rent rolls, valuations)
- Excel import/export (Properties, rent rolls)
- OCR document scanning (Images, PDFs, Screenshots)
- ML predictions (Property value, vacancy risk, market trends)
- JWT authentication & role-based access
- Professional financial modeling (IRR, CoC, DSCR, Cap Rate)
- Docker deployment ready

Tech Stack:
- Backend: FastAPI, SQLAlchemy, SQLite, JWT, Scikit-learn, ReportLab
- Frontend: React 18, Vite, TailwindCSS
- Mobile: React Native, Expo
- Documents: ReportLab, OpenPyXL, Pandas
- OCR: Pytesseract, Pillow, PyPDF2

All phases complete: Backend, Frontend, Mobile, Advanced Features
Production-ready! 🚀"

# Check if remote exists
if ! git remote | grep -q origin; then
    echo "Adding remote origin..."
    git remote add origin https://github.com/alankam555/cre-enterprise.git
fi

# Push to GitHub
echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "=========================================="
echo "  Done! 🎉"
echo "=========================================="
