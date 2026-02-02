# WiFi People Detection Dashboard

Real-time dashboard for WiFi-based people detection system using machine learning and WiFi signal analysis.

## Overview

This dashboard provides real-time visualization of people detection data processed by the backend ML system. It connects via WebSocket to receive live updates and displays:

- **People Presence Detection**: Real-time indication of whether people are detected in the monitored area
- **People Count**: Accurate count of individuals with confidence scores
- **Historical Charts**: 60-minute historical view of detection patterns
- **Scenario Information**: Current detection scenario and context
- **Technical Details**: Raw feature vectors and detection data

## Features

- Real-time WebSocket connection for live updates
- Responsive design that works on desktop, tablet, and mobile
- Modern UI with TailwindCSS
- Interactive charts using Recharts
- TypeScript for type safety
- Automatic reconnection on connection loss
- Loading and error states
- Technical details view for debugging

## Technology Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **WebSocket**: Socket.io Client
- **Charts**: Recharts
- **State Management**: Zustand
- **Data Fetching**: SWR
- **HTTP Client**: Axios
- **Icons**: Lucide React

## Prerequisites

Before running this dashboard, ensure you have:

- Node.js 18+ installed
- npm or yarn package manager
- The backend detection server running on port 8000 (or configured URL)

## Installation

1. **Clone and navigate to the frontend directory**:
```bash
cd /home/vinns/experiments/detectPeople/frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Configure environment variables**:
```bash
cp .env.example .env.local
```

Edit `.env.local` with your backend configuration:
```env
NEXT_PUBLIC_WS_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Run the development server**:
```bash
npm run dev
```

5. **Open your browser**:
Navigate to [http://localhost:3000](http://localhost:3000)

## Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# Run ESLint
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main dashboard page
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   └── dashboard/         # Dashboard components
│   │       ├── PresenceIndicator.tsx
│   │       ├── CountGauge.tsx
│   │       ├── DetectionChart.tsx
│   │       ├── ScenarioInfo.tsx
│   │       ├── StatusBar.tsx
│   │       └── TechnicalDetails.tsx
│   ├── hooks/
│   │   └── useWebSocket.ts    # Custom WebSocket hook
│   ├── types/
│   │   └── detection.ts       # TypeScript type definitions
│   └── lib/                   # Utility functions
├── public/                    # Static assets
├── .env.local                 # Environment variables (local)
├── .env.example              # Environment variables template
├── next.config.js            # Next.js configuration
├── tailwind.config.ts        # TailwindCSS configuration
├── tsconfig.json             # TypeScript configuration
└── package.json              # Dependencies and scripts
```

## Component Overview

### PresenceIndicator
Displays whether people are detected with a visual indicator and confidence score.

**Props:**
- `presence`: boolean - Whether people are detected
- `confidence`: number - Confidence score (0-1)

### CountGauge
Shows the number of people detected with a color-coded display.

**Props:**
- `count`: number - Number of people detected
- `confidence`: number - Confidence score (0-1)

### DetectionChart
Displays a 60-minute historical view of detection counts using an area chart.

**Features:**
- Auto-generated historical data (simulated)
- Responsive area chart
- Gradient fill
- Tooltips and legend

### ScenarioInfo
Shows the current detection scenario with contextual information.

**Props:**
- `scenario`: string - Current scenario name

### StatusBar
Displays connection status, room ID, and error messages.

**Props:**
- `connected`: boolean - WebSocket connection status
- `error`: string | null - Error message if any
- `roomId`: string - Current room ID

### TechnicalDetails
Expandable section showing raw detection data and feature vectors.

**Props:**
- `detection`: DetectionData | null - Detection data object

## WebSocket Integration

The dashboard uses Socket.io to connect to the backend WebSocket server:

```typescript
// Connection URL from environment
const wsUrl = process.env.NEXT_PUBLIC_WS_URL

// Subscribe to detection updates
socket.emit('subscribe', { room_id: 'default-room' })

// Receive detection updates
socket.on('detection_update', (data: DetectionData) => {
  // Update UI with new detection data
})
```

## Detection Data Format

```typescript
interface DetectionData {
  timestamp: string           // ISO timestamp
  presence: boolean           // Whether people are present
  presence_confidence: number // Presence confidence (0-1)
  count: number              // Number of people detected
  count_confidence: number   // Count confidence (0-1)
  scenario: string           // Current scenario
  features: Record<string, number> // Raw feature vector
}
```

## Customization

### Changing Backend URL

Edit `.env.local`:
```env
NEXT_PUBLIC_WS_URL=http://your-backend-url:port
```

### Modifying Chart Time Range

Edit `DetectionChart.tsx`:
```typescript
// Change from 60 minutes to desired range
for (let i = 60; i >= 0; i--) {
  // ...
}
```

### Adding New Components

1. Create component in `src/components/dashboard/`
2. Export from component file
3. Import and use in `src/app/page.tsx`

## Troubleshooting

### Connection Issues

If the dashboard shows "Disconnected":

1. Check if the backend server is running on the configured URL
2. Verify the WebSocket URL in `.env.local`
3. Check browser console for error messages
4. Ensure CORS is enabled on the backend

### Build Errors

If you encounter build errors:

1. Clear the Next.js cache: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check Node.js version: `node --version` (should be 18+)

### Chart Not Displaying

If charts don't render:

1. Check browser console for Recharts errors
2. Ensure data is being received from WebSocket
3. Verify window size (charts need minimum width)

## Development Tips

1. **Hot Reload**: The dev server supports hot module replacement for fast development
2. **TypeScript**: Use strict type checking to catch errors early
3. **Console Logging**: WebSocket events are logged to the console for debugging
4. **Component Props**: All components have TypeScript interfaces defined

## Production Deployment

### Build for Production

```bash
npm run build
npm start
```

### Environment Variables

Set production environment variables before building:
```env
NEXT_PUBLIC_WS_URL=https://your-production-backend.com
NEXT_PUBLIC_API_URL=https://your-production-backend.com
```

### Deployment Platforms

This Next.js app can be deployed to:
- Vercel (recommended)
- Netlify
- AWS Amplify
- DigitalOcean App Platform
- Any Node.js hosting service

## Performance Considerations

- WebSocket reconnection is automatic with exponential backoff
- Charts render 60 data points for optimal performance
- Components use React.memo for unnecessary re-renders
- Images and icons are optimized

## Security

- No sensitive data is stored in the frontend
- WebSocket connections use secure WebSocket (wss://) in production
- Environment variables are prefixed with `NEXT_PUBLIC_` for client-side access

## Contributing

To add new features:

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test thoroughly: `npm run build && npm start`
4. Submit a pull request

## License

This project is part of the WiFi People Detection System.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review browser console for errors
3. Check backend server logs
4. Verify WebSocket connection in browser DevTools Network tab

## Roadmap

Future enhancements:
- [ ] Multiple room monitoring
- [ ] Alert configuration and notifications
- [ ] Historical data export
- [ ] Dark mode support
- [ ] Mobile app version
- [ ] Real-time video feed integration
- [ ] Advanced analytics and reporting
