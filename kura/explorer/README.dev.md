# Kura Explorer - Development Setup with Hot Reloading

This guide explains how to run the Kura Explorer with automatic rebuilding when files change.

## Quick Start

### Option 1: Use the Development Script (Recommended)
```bash
./dev.sh
```

### Option 2: Manual Docker Compose
```bash
# Start with hot reloading
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Or in detached mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

## What's Enabled

### 🔥 **Backend Hot Reloading** (Already working)
- **Volume Mount**: `./backend:/app` - Your code changes are reflected immediately
- **Auto-reload**: `uvicorn --reload` watches for Python file changes
- **Access**: http://localhost:8001

### 🔥 **Frontend Hot Reloading** (New)
- **Volume Mount**: `./frontend:/app` - Your code changes trigger rebuilds
- **Vite Dev Server**: Fast HMR (Hot Module Replacement)
- **File Polling**: Works reliably in Docker environment
- **Access**: http://localhost:5173

## Development Features

- ✅ **Instant file watching** - Changes trigger rebuilds automatically
- ✅ **Fast builds** - Only changed files are processed
- ✅ **API proxy** - Frontend automatically proxies `/api` calls to backend
- ✅ **TypeScript support** - Full type checking and compilation
- ✅ **Tailwind CSS** - Instant style updates
- ✅ **React Fast Refresh** - State preservation during development

## File Change Detection

The setup uses:
- **Backend**: `uvicorn --reload` with inotify file watching
- **Frontend**: Vite with polling (checks every 1 second for changes)

## Stopping the Environment

```bash
# Stop all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Stop and remove volumes/networks
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

## Production Build

For production builds, use the regular docker-compose:
```bash
docker-compose up --build
```

## Troubleshooting

### Changes not detected?
1. Make sure you're editing files in the `./backend` or `./frontend` directories
2. Check that the containers have the volume mounts (visible in `docker-compose ps`)
3. Try restarting: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart`

### Port conflicts?
Set custom ports in `.env` file:
```env
FRONTEND_PORT=3000
BACKEND_PORT=8000
```

### Performance issues?
The frontend uses polling which can be CPU intensive. To adjust:
- Edit `frontend/vite.config.ts`
- Increase `interval` from 1000ms to 2000ms or higher 