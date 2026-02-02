# ADR-007: Frontend Framework Selection

**Status:** Accepted
**Date:** 2025-02-02
**Context:** Web Dashboard for Real-Time People Monitoring
**Decision:** Next.js 14 with TypeScript, TailwindCSS, and shadcn/ui

---

## Context

The frontend application requires:
- **Real-Time Updates:** WebSocket integration for live detection data
- **Data Visualization:** Charts, gauges, heatmaps for occupancy trends
- **Responsive Design:** Desktop, tablet, and mobile support
- **Performance:** Fast initial load, smooth animations
- **Developer Experience:** Type safety, hot reload, modern tooling
- **SEO:** Discoverable for marketing (if public-facing)

**Frontend Complexity:**
- 3-5 main pages (dashboard, analytics, configuration, alerts)
- 10-20 reusable components
- Real-time data streaming (WebSocket)
- Historical data querying (REST API)
- Form handling (room/detector configuration)

---

## Decision

**Selected Framework: Next.js 14 (App Router)**
**UI Library:** TailwindCSS + shadcn/ui
**State Management:** Zustand
**Data Fetching:** SWR
**Charts:** Recharts + D3.js

### Tech Stack Rationale

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Stack                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Framework: Next.js 14 (App Router)                  │  │
│  │  - Server-Side Rendering (SSR)                       │  │
│  │  - API Routes (BFF pattern)                          │  │
│  │  - File-based routing                                 │  │
│  │  - TypeScript support                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  UI: TailwindCSS + shadcn/ui                         │  │
│  │  - Utility-first CSS                                 │  │
│  │  - Pre-built accessible components                   │  │
│  │  - Dark mode support                                 │  │
│  │  - Responsive design                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  State & Data: Zustand + SWR                         │  │
│  │  - Client state (Zustand)                            │  │
│  │  - Server state (SWR)                                │  │
│  │  - Real-time revalidation                            │  │
│  │  - Automatic caching                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Visualization: Recharts + D3.js                     │  │
│  │  - Line/Bar charts (Recharts)                        │  │
│  │  - Custom heatmaps (D3.js)                           │  │
│  │  - Real-time gauges                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Framework Comparison

| Framework | SSR | SSG | API Routes | TypeScript | Performance | DX |
|-----------|-----|-----|------------|------------|-------------|-----|
| **Next.js 14** | ✅ | ✅ | ✅ | ✅ | Excellent ✅ | Excellent ✅ |
| React (Vite) | ❌ | ✅ | ❌ | ✅ | Good ⚠️ | Good ✅ |
| Vue + Nuxt | ✅ | ✅ | ✅ | ✅ | Excellent ✅ | Good ⚠️ |
| SvelteKit | ✅ | ✅ | ✅ | ✅ | Excellent ✅ | Good ⚠️ |
| Angular | ✅ | ✅ | ❌ | ✅ | Good ⚠️ | Fair ❌ |

### Next.js Advantages

**1. Server-Side Rendering (SSR):**
```typescript
// app/dashboard/page.tsx
async function DashboardPage() {
  // Server-side data fetching
  const rooms = await fetch(`${API_URL}/rooms`, {
    cache: 'no-store'
  }).then(r => r.json())

  return (
    <div>
      <h1>Dashboard</h1>
      <RoomList rooms={rooms} />
    </div>
  )
}

// Benefits:
// - Faster initial page load (HTML rendered on server)
// - Better SEO (if public-facing)
// - Improved Core Web Vitals (LCP < 2.5s)
```

**2. API Routes (BFF Pattern):**
```typescript
// app/api/detection/route.ts
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const room_id = searchParams.get('room_id')

  // Backend for Frontend (BFF)
  const detection = await backendService.getDetection(room_id)

  return NextResponse.json(detection)
}

// Benefits:
// - Single codebase (frontend + backend)
// - No separate API server needed
// - Type-safe API calls
```

**3. File-Based Routing:**
```
app/
├── dashboard/
│   ├── page.tsx              (GET /dashboard)
│   ├── real-time/
│   │   └── page.tsx          (GET /dashboard/real-time)
│   ├── analytics/
│   │   ├── page.tsx          (GET /dashboard/analytics)
│   │   └── trends/
│   │       └── page.tsx      (GET /dashboard/analytics/trends)
│   └── layout.tsx            (Shared layout for dashboard/*)
├── configuration/
│   ├── page.tsx              (GET /configuration)
│   └── rooms/
│       └── [id]/
│           └── page.tsx      (GET /configuration/rooms/:id)
└── api/
    └── detection/
        └── route.ts          (GET/POST /api/detection)
```

**4. Built-In Optimization:**
```typescript
// Automatic code splitting
// Each page only loads its own JavaScript

// Image optimization
import Image from 'next/image'

<Image
  src="/dashboard.png"
  width={800}
  height={600}
  alt="Dashboard"
  // Benefits:
  // - Automatic WebP conversion
  // - Lazy loading
  // - Responsive images
/>

// Font optimization
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })
// Benefits:
// - Self-hosting (no Google Fonts request)
// - Automatic font subsetting
// - Zero layout shift
```

### Why Not Alternatives

**vs. React (Vite):**
- ❌ No built-in SSR (manual setup required)
- ❌ No API routes (separate backend needed)
- ❌ Slower initial page load (client-side only)

**vs. Vue + Nuxt:**
- ⚠️ Smaller ecosystem than React
- ⚠️ Fewer developers familiar with Vue
- ⚠️ Less mature component libraries

**vs. Angular:**
- ❌ Verbose (2-3x more code than React)
- ❌ Heavier bundle size (slower load)
- ❌ Steeper learning curve
- ❌ Slower development cycle

### UI Library: TailwindCSS + shadcn/ui

**TailwindCSS Benefits:**
```css
/* Utility-first CSS */
<div className="flex items-center justify-between p-6 bg-white rounded-lg shadow">
  <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
  <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
    Refresh
  </button>
</div>

/* Benefits:
   - No custom CSS files
   - Consistent design system
   - Responsive utilities (sm:, md:, lg:)
   - Dark mode support (class="dark:bg-gray-900")
*/
```

**shadcn/ui Benefits:**
```typescript
// Pre-built accessible components
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

// Benefits:
// - Copy-paste components (not npm package)
// - Full customization (you own the code)
// - Radix UI primitives (accessible)
// - TailwindCSS styling (consistent)
```

### State Management: Zustand

**Why Zustand over Redux/Context:**

```typescript
// Zustand (Simple)
import create from 'zustand'

const useStore = create((set) => ({
  rooms: [],
  setRooms: (rooms) => set({ rooms }),
  addRoom: (room) => set((state) => ({ rooms: [...state.rooms, room] }))
}))

// Usage
const { rooms, addRoom } = useStore()

// Benefits:
// - Minimal boilerplate (1 file vs. 10+ for Redux)
// - No providers needed
// - TypeScript-first
// - Tiny bundle size (1KB vs. 15KB for Redux)
```

**vs. Redux Toolkit:**
- ❌ More boilerplate (actions, reducers, slices)
- ❌ Steeper learning curve
- ❌ Overkill for this app size

**vs. React Context:**
- ❌ Performance issues (re-renders all consumers)
- ❌ No built-in dev tools
- ❌ Manual optimization required

### Data Fetching: SWR

**Why SWR over React Query/TanStack Query:**

```typescript
// SWR (Stale-While-Revalidate)
import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then(r => r.json())

function DetectionData({ roomId }: { roomId: string }) {
  const { data, error, isLoading } = useSWR(
    `/api/detection?room_id=${roomId}`,
    fetcher,
    {
      refreshInterval: 10000,  // Revalidate every 10s
      revalidateOnFocus: true,
      revalidateOnReconnect: true
    }
  )

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading data</div>

  return <div>Count: {data.count}</div>
}

// Benefits:
// - Automatic caching
// - Real-time revalidation
// - Lightweight (4KB vs. 13KB for React Query)
// - Simple API (perfect for our use case)
```

**vs. React Query:**
- ⚠️ Larger bundle size
- ⚠️ More features than we need (mutation, pagination)
- ⚠️ Slightly more complex API

**vs. useEffect + fetch:**
- ❌ Manual caching
- ❌ No automatic revalidation
- ❌ Race conditions
- ❌ More boilerplate

---

## Consequences

### Positive Consequences

**Performance:**
- ✅ Fast initial page load (SSR, LCP < 2.5s)
- ✅ Smooth interactions (client-side navigation)
- ✅ Optimized bundles (automatic code splitting)
- ✅ Efficient caching (SWR stale-while-revalidate)

**Developer Experience:**
- ✅ TypeScript support (catch errors at compile time)
- ✅ Hot reload (instant feedback)
- ✅ File-based routing (intuitive)
- ✅ API routes (single codebase)
- ✅ Built-in image optimization
- ✅ Excellent documentation (Next.js)

**SEO:**
- ✅ Server-rendered HTML (discoverable by search engines)
- ✅ Meta tags API (social media previews)
- ✅ Sitemap generation (automatic)
- ✅ robots.txt configuration

**Scalability:**
- ✅ Easy to add new pages (file-based routing)
- ✅ Component reusability (React + shadcn/ui)
- ✅ State management scales (Zustand)
- ✅ Data fetching optimized (SWR)

**Ecosystem:**
- ✅ Largest React component library
- ✅ Active community (2.5M+ weekly downloads)
- ✅ Extensive tooling (ESLint, Prettier, Playwright)
- ✅ Vercel integration (zero-config deployment)

### Negative Consequences

**Learning Curve:**
- ❌ Next.js App Router (new mental model)
- ❌ React Server Components (different from client components)
- ❌ TypeScript (if team unfamiliar)
- ❌ TailwindCSS (utility-first approach)

**Build Complexity:**
- ❌ Longer build times (SSR + SSG)
- ❌ More configuration (if customizing defaults)
- ❌ Vercel lock-in (if using Vercel-specific features)

**Bundle Size:**
- ❌ Heavier than vanilla React (SSR overhead)
- ❌ TailwindCSS CSS file (10-20KB unminified)
- ❌ shadcn/ui components (not tree-shakeable)

**Mitigation Strategies:**
```typescript
// 1. Code splitting (automatic in Next.js)
// Each page is automatically split

// 2. Dynamic imports (for heavy components)
import dynamic from 'next/dynamic'

const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <div>Loading chart...</div>,
  ssr: false  // Skip SSR for client-only components
})

// 3. Tree shaking (automatic for named exports)
import { Button } from '@/components/ui/button'  // Only imports Button

// 4. Image optimization (built-in)
import Image from 'next/image'
// Automatically converts to WebP, lazy loads, responsive
```

---

## Project Structure

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── dashboard/
│   │   ├── page.tsx              (Main dashboard)
│   │   ├── real-time/
│   │   │   └── page.tsx          (Live monitoring)
│   │   ├── analytics/
│   │   │   ├── page.tsx          (Historical trends)
│   │   │   ├── occupancy/
│   │   │   │   └── page.tsx
│   │   │   └── trends/
│   │   │       └── page.tsx
│   │   ├── alerts/
│   │   │   └── page.tsx
│   │   └── layout.tsx            (Dashboard layout)
│   ├── configuration/
│   │   ├── page.tsx              (Room management)
│   │   ├── rooms/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx      (Room details)
│   │   ├── detectors/
│   │   │   └── page.tsx
│   │   └── calibration/
│   │       └── page.tsx
│   ├── api/
│   │   └── detection/
│   │       └── route.ts          (BFF API)
│   ├── layout.tsx                (Root layout)
│   └── page.tsx                  (Home page)
├── components/
│   ├── dashboard/
│   │   ├── RealTimeDashboard.tsx
│   │   ├── PresenceIndicator.tsx
│   │   ├── CountGauge.tsx
│   │   └── MovementChart.tsx
│   ├── analytics/
│   │   ├── OccupancyChart.tsx
│   │   └── Heatmap.tsx
│   ├── configuration/
│   │   ├── RoomCard.tsx
│   │   └── DetectorGrid.tsx
│   └── ui/                       (shadcn/ui components)
│       ├── button.tsx
│       ├── card.tsx
│       └── ...
├── lib/
│   ├── websocket.ts              (Socket.io client)
│   ├── api.ts                    (REST client)
│   └── utils.ts
├── hooks/
│   ├── useWebSocket.ts
│   └── useDetection.ts
├── stores/
│   └── useStore.ts               (Zustand)
├── types/
│   └── index.ts                  (TypeScript types)
└── public/
    └── images/
```

---

## Success Criteria

- **Performance:** Core Web Vitals (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- **Bundle Size:** <200KB initial JS bundle
- **TypeScript:** 100% type coverage (no any types)
- **Accessibility:** WCAG 2.1 AA compliance
- **Browser Support:** Chrome, Firefox, Safari, Edge (latest 2 versions)
- **Mobile:** Responsive design on iOS Safari, Android Chrome
- **Lighthouse Score:** >90 performance, >100 accessibility

---

## References

1. [Next.js Documentation](https://nextjs.org/docs)
2. [TailwindCSS Documentation](https://tailwindcss.com/docs)
3. [shadcn/ui Components](https://ui.shadcn.com/)
4. [Zustand Documentation](https://github.com/pmndrs/zustand)
5. [SWR Documentation](https://swr.vercel.app/)

---

**Document End**

*This ADR will be reviewed if performance requirements are not met or if developer feedback is negative.*
