# Quick Start Guide

Get the WiFi People Detection Dashboard up and running in minutes.

## Prerequisites

- Node.js 18+ installed
- Backend detection server running (typically on port 8000)

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd /home/vinns/experiments/detectPeople/frontend
npm install
```

### Step 2: Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local` if your backend is not at `http://localhost:8000`:
```env
NEXT_PUBLIC_WS_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Start Development Server

```bash
npm run dev
```

### Step 4: Open Dashboard

Open your browser and navigate to:
```
http://localhost:3000
```

## Verify It's Working

You should see:
- **Connected** status indicator (green)
- **People Presence** card showing detection status
- **People Count** gauge with count
- **Detection History** chart with simulated data
- **Scenario** information

If you see "Disconnected":
1. Check if backend server is running
2. Verify the WebSocket URL in `.env.local`
3. Check browser console (F12) for errors

## Available Commands

```bash
npm run dev      # Start development server (http://localhost:3000)
npm run build    # Build for production
npm start        # Start production server
npm run lint     # Run ESLint
```

## Troubleshooting

### "Connection Error"

**Problem**: Cannot connect to backend

**Solutions**:
1. Ensure backend server is running: `cd ../backend && python -m uvicorn main:app --reload`
2. Check WebSocket URL in `.env.local`
3. Verify no firewall blocking port 8000
4. Check browser console for detailed errors

### "Build Failed"

**Problem**: TypeScript or build errors

**Solutions**:
1. Clear cache: `rm -rf .next node_modules`
2. Reinstall: `npm install`
3. Check Node.js version: `node --version` (should be 18+)

### Charts Not Showing

**Problem**: DetectionChart component empty

**Solutions**:
1. Check browser console for Recharts errors
2. Verify WebSocket is receiving data
3. Try resizing browser window
4. Check if data is being logged in console

### Port Already in Use

**Problem**: Port 3000 already taken

**Solutions**:
1. Kill process on port 3000: `lsof -ti:3000 | xargs kill`
2. Or use different port: `PORT=3001 npm run dev`

## Development Tips

1. **Hot Reload**: Changes to files auto-refresh the browser
2. **Console Logs**: WebSocket events are logged for debugging
3. **Type Safety**: TypeScript errors show in browser and terminal
4. **Component Props**: All components have type definitions

## Next Steps

1. **Customize UI**: Edit components in `src/components/dashboard/`
2. **Add Features**: Extend `src/app/page.tsx`
3. **Change Styling**: Modify `tailwind.config.ts` and `src/app/globals.css`
4. **Add API Calls**: Use `axios` or `swr` in components
5. **Deploy**: Run `npm run build` and deploy to Vercel/Netlify

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- Review browser console for error messages
- Check backend server logs
- Verify WebSocket connection in DevTools Network tab

## Architecture Overview

```
Frontend (Next.js)
    ↓ WebSocket
Backend (FastAPI)
    ↓
ML Model (Python)
    ↓
WiFi Data (CSI/RTS)
```

The dashboard receives real-time updates via WebSocket and displays:
- Current detection status
- People count with confidence
- Historical trends
- Technical details
