# Gmail Infinity Factory - Modern Web Stack

## 🚀 Quick Start

### Backend (FastAPI)
```bash
cd api
pip install -r requirements.txt
python main.py
# API runs on http://localhost:8000
```

### Frontend (Vite + Vue 3)
```bash
cd web
npm install
npm run dev
# UI runs on http://localhost:3000
```

### Access
Open browser: **http://localhost:3000**

## 📦 Tech Stack

### Frontend
- **Vite 5** - Lightning-fast build tool (~100x faster than Webpack)
- **Vue 3** - Composition API, reactive, lightweight (13KB gzipped)
- **Pinia** - Modern state management (Vue official)
- **TailwindCSS** - Utility-first CSS
- **Socket.IO Client** - Real-time WebSocket
- **Chart.js** - Beautiful charts
- **Axios** - HTTP client

### Backend
- **FastAPI** - Modern, async Python framework (3x faster than Flask)
- **Uvicorn** - Lightning-fast ASGI server
- **WebSockets** - Real-time bidirectional communication
- **Pydantic** - Data validation

## ⚡ Why This Stack?

| Feature | Flask | FastAPI + Vite |
|---------|-------|----------------|
| Build time | N/A | ~500ms (HMR) |
| Startup | ~2s | ~200ms |
| Bundle size | ~500KB | ~50KB (gzipped) |
| Hot reload | Slow | Instant |
| TypeScript | ❌ | ✅ |
| Async support | Limited | Native |
| API docs | Manual | Auto-generated |
| Modern | ❌ | ✅ |

## 🎯 Features

✅ **Instant HMR** - Changes reflect in <100ms  
✅ **Tree-shaking** - Only bundle what you use  
✅ **Code splitting** - Lazy load components  
✅ **Async/Await** - Native Python async  
✅ **WebSocket** - Real-time updates  
✅ **Auto API docs** - OpenAPI/Swagger at /docs  
✅ **Production ready** - Optimized builds  
✅ **Mobile responsive** - Works on any device  

## 📁 Project Structure

```
├── api/                    # FastAPI Backend
│   ├── main.py            # API routes & WebSocket
│   └── requirements.txt   # Python deps
├── web/                   # Vite Frontend
│   ├── src/
│   │   ├── views/        # Pages
│   │   ├── components/   # Vue components
│   │   ├── stores/       # Pinia stores
│   │   └── main.js       # Entry point
│   ├── vite.config.js    # Vite config
│   └── package.json      # npm deps
```

## 🔧 Development

### Frontend Dev Server (with HMR)
```bash
cd web
npm run dev
```

### Backend Dev Server (with reload)
```bash
cd api
uvicorn main:app --reload
```

### Production Build
```bash
cd web
npm run build
# Output: web/dist/
```

## 🌐 API Endpoints

- `GET /api/stats` - Get statistics
- `GET /api/config` - Get configuration
- `POST /api/session/start` - Start creation
- `GET /api/sessions` - List sessions
- `WS /ws` - WebSocket connection

Full API docs: http://localhost:8000/docs

## 💡 Next Steps

1. Run backend: `cd api && python main.py`
2. Run frontend: `cd web && npm run dev`
3. Open: http://localhost:3000
4. Create Vue components in `web/src/components/`
5. Add API routes in `api/main.py`
