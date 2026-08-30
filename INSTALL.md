# Installation & Setup Instructions

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+
- Node.js 18+

---

## 1. One-Time Setup

### Install Python Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### Install Frontend Dependencies
```bash
cd web
npm install
cd ..
```

---

## 2. Launch Development Stack

Run the unified dev launcher from the project root:
```bash
npm run dev
```

This single command starts both servers concurrently:
* 🌐 **Web Dashboard:** [http://localhost:3000](http://localhost:3000)
* ⚡ **FastAPI Backend:** [http://localhost:8000](http://localhost:8000)
* 📚 **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 3. Available Root Commands

| Command | Action |
|---|---|
| `npm run dev` | Launch FastAPI Backend + Vite Frontend together |
| `npm run dev:api` | Launch FastAPI Backend only (`http://localhost:8000`) |
| `npm run dev:web` | Launch Vite Frontend only (`http://localhost:3000`) |
| `npm run build` | Build optimized frontend in `web/dist/` |
| `npm run cli` | Run automated zero-interaction CLI (`enhanced_creator.py`) |

---

## 4. Production Build

```bash
npm run build
```
Optimized assets are emitted to `web/dist/`.
