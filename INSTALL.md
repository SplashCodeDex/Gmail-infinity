# Installation & Setup Instructions

## 🚀 Quick Start Guide

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.9+ (for backend)

---

## Backend Setup (FastAPI)

### 1. Navigate to API directory
```bash
cd api
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install project dependencies
```bash
cd ..
pip install -r requirements.txt
```

### 4. Start the API server
```bash
cd api
python main.py
```

✅ **Backend running at:** http://localhost:8000  
📚 **API Docs:** http://localhost:8000/docs

---

## Frontend Setup (Vite + Vue 3)

### 1. Navigate to web directory
```bash
cd web
```

### 2. Install npm dependencies
```bash
npm install
```

### 3. Start development server
```bash
npm run dev
```

✅ **Frontend running at:** http://localhost:3000

---

## 🎯 Access the Dashboard

Open your browser and go to:
```
http://localhost:3000
```

---

## 🛠️ Development Workflow

### Run Both Servers Simultaneously

**Terminal 1 (Backend):**
```bash
cd api
python main.py
```

**Terminal 2 (Frontend):**
```bash
cd web
npm run dev
```

---

## 📦 Production Build

### Build frontend for production
```bash
cd web
npm run build
```

The optimized build will be in `web/dist/`

### Serve production build
```bash
npm run preview
```

---

## 🧪 Testing

### Test API endpoints
Visit: http://localhost:8000/docs

### Test WebSocket connection
Open browser console on dashboard and check for:
```
WebSocket connected
```

---

## 🔧 Troubleshooting

### Port already in use
**Backend (8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Frontend (3000):**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

### CORS errors
Make sure backend is running before starting frontend.

### WebSocket not connecting
1. Check backend is running on port 8000
2. Check browser console for errors
3. Verify CORS settings in `api/main.py`

---

## 📁 Project Structure
```
├── api/               # FastAPI backend
│   ├── main.py       # API server
│   └── requirements.txt
├── web/              # Vite frontend
│   ├── src/
│   │   ├── components/
│   │   ├── stores/
│   │   ├── views/
│   │   └── main.js
│   └── package.json
└── requirements.txt  # Python project deps
```

---

## 🎉 You're Ready!

Once both servers are running:
1. Open http://localhost:3000
2. Configure your session settings
3. Click "Start Creating Accounts"
4. Watch the magic happen! ✨
