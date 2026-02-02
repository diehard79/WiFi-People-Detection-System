# ADR-005: Real-time Communication Protocol Selection

**Status:** Accepted
**Date:** 2025-02-02
**Context:** Real-time Detection Updates to Web Dashboard
**Decision:** WebSocket (Socket.io) for Bidirectional Communication

---

## Context

The system requires real-time communication between backend detection services and frontend dashboard:

**Communication Requirements:**
- **Latency:** <100ms from detection to UI update
- **Directionality:** Bidirectional (server → client push, client → server commands)
- **Concurrency:** 100+ simultaneous connections
- **Reliability:** Automatic reconnection on network failure
- **Scalability:** Support multi-server deployments
- **Browser Compatibility:** Modern browsers (Chrome, Firefox, Safari, Edge)

**Use Cases:**
1. **Detection Updates:** Push presence/count changes every 10 seconds
2. **Alert Notifications:** Immediate push on threshold violations
3. **Calibration Status:** Real-time progress updates during calibration
4. **Configuration Changes:** Broadcast detector changes to all connected clients

---

## Decision

**Selected Protocol: WebSocket (RFC 6455)**
**Implementation Library: Socket.io 4.5+ (Python) / Socket.io-client 4.5+ (JavaScript)**

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     WebSocket Layer                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  WebSocket Server (Python: Socket.io / python-socket.io)│   │
│  │  ├─ Room-based namespaces (/detection/{room_id})     │   │
│  │  ├─ Automatic reconnection handling                  │   │
│  │  ├─ Message acknowledgment (ACK)                    │   │
│  │  └─ Broadcast to all subscribers                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          │ WebSocket Persistent Connection   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Frontend (Next.js + Socket.io-client)              │   │
│  │  ├─ Auto-reconnect with exponential backoff         │   │
│  │  ├─ Room subscription management                    │   │
│  │  ├─ Message queuing during disconnect               │   │
│  │  └─ UI state synchronization                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Protocol Comparison

| Aspect | WebSocket | Server-Sent Events (SSE) | Polling (HTTP) | WebRTC |
|--------|-----------|--------------------------|----------------|---------|
| **Latency** | <50ms ✅ | <50ms ✅ | 1-5s ❌ | <20ms ✅ |
| **Directionality** | Bidirectional ✅ | Server→Client only ❌ | Client→Server only ⚠️ | Bidirectional ✅ |
| **Browser Support** | 99%+ ✅ | 95%+ ⚠️ | 100% ✅ | 85% ⚠️ |
| **Server Complexity** | Medium ⚠️ | Low ✅ | Low ✅ | High ❌ |
| **Scalability** | Good ✅ | Excellent ✅ | Poor ❌ | Medium ⚠️ |
| **Overhead** | Low (2 bytes) ✅ | Low (2 bytes) ✅ | High (500+ bytes) ❌ | Medium ⚠️ |
| **Reconnection** | Manual ⚠️ | Built-in ✅ | N/A | Manual ⚠️ |

### Why WebSocket Over Alternatives

**vs. Server-Sent Events (SSE):**

*SSE Limitations:*
- ❌ Unidirectional (server → client only)
- ❌ Cannot send commands from client to server
- ❌ No binary data support (text-only)
- ❌ Limited to one connection per domain (browser restriction)

*WebSocket Advantages:*
- ✅ Full-duplex communication
- ✅ Binary data support
- ✅ Multiple connections possible
- ✅ Lower protocol overhead (2 bytes vs. HTTP headers)

**vs. HTTP Polling:**

*Polling Limitations:*
- ❌ High latency (1-5 seconds between polls)
- ❌ Wasteful (repeated HTTP headers, server load)
- ❌ Not truly real-time
- ❌ Higher bandwidth usage

*WebSocket Advantages:*
- ✅ Persistent connection (no repeated handshakes)
- ✅ True real-time (<50ms latency)
- ✅ Efficient (no HTTP headers after handshake)
- ✅ Lower server load

**vs. WebRTC:**

*WebRTC Limitations:*
- ❌ Complex setup (ICE, STUN, TURN servers)
- ❌ Overkill for data-only transmission (designed for media)
- ❌ Less browser support (85% vs. 99%)
- ❌ Harder debugging and monitoring

*WebSocket Advantages:*
- ✅ Simple setup (single HTTP upgrade request)
- ✅ Designed for data transmission
- ✅ Universal browser support
- ✅ Easier to debug and monitor

### Why Socket.io Over Native WebSocket

**Socket.io Advantages:**

1. **Automatic Reconnection:**
```javascript
// Socket.io (automatic)
const socket = io('http://localhost:3000', {
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 10
});

// Native WebSocket (manual reconnection required)
const ws = new WebSocket('ws://localhost:3000');
ws.onclose = () => {
  setTimeout(() => {
    ws = new WebSocket('ws://localhost:3000');
  }, 1000);
};
```

2. **Fallback Support:**
```javascript
// Socket.io automatically tries:
// 1. WebSocket
// 2. HTTP long-polling (if WebSocket blocked)
// 3. HTTP short-polling (last resort)

const socket = io('http://localhost:3000', {
  transports: ['websocket', 'polling']  // Auto-fallback
});
```

3. **Room/Namespace Support:**
```python
# Server-side (Socket.io)
@sio.on('subscribe')
async def subscribe_room(sid, data):
    room_id = data['room_id']
    sio.enter_room(sid, room_id)

# Broadcast to specific room
await sio.emit('detection_update', data, room=room_id)

# Native WebSocket (manual room management)
rooms = {}  # Manual subscription tracking
```

4. **Message Acknowledgment:**
```javascript
// Socket.io (built-in ACK)
socket.emit('calibrate', {room_id: 'conf-a'}, (response) => {
  console.log('Calibration started:', response.job_id);
});

// Native WebSocket (manual ACK)
socket.send(JSON.stringify({
  type: 'calibrate',
  room_id: 'conf-a',
  id: generate_unique_id()
}));
// Need to match response ID manually
```

5. **Binary Data Support:**
```python
# Socket.io (automatic)
await sio.emit('image', binary_data, room=room_id)

# Native WebSocket (manual framing)
await ws.send(struct.pack('!I', len(binary_data)))
await ws.send(binary_data)
```

---

## Consequences

### Positive Consequences

**Performance:**
- ✅ <50ms latency (true real-time)
- ✅ Efficient bandwidth (2-byte frames vs. 500+ byte HTTP)
- ✅ Low server overhead (persistent connections)
- ✅ Supports 100+ concurrent connections per server

**User Experience:**
- ✅ Instant detection updates
- ✅ Smooth dashboard animations
- ✅ No page refreshes required
- ✅ Mobile-friendly (efficient battery usage)

**Reliability:**
- ✅ Automatic reconnection (Socket.io)
- ✅ Fallback to polling if WebSocket blocked
- ✅ Message queuing during disconnect
- ✅ Connection state monitoring

**Developer Experience:**
- ✅ Simple API (emit/on pattern)
- ✅ Room-based filtering
- ✅ Built-in acknowledgments
- ✅ Debugging tools (Socket.io admin UI)

**Scalability:**
- ✅ Redis adapter for multi-server deployments
- ✅ Sticky sessions supported
- ✅ Load balancing compatible
- ✅ Horizontal scaling possible

### Negative Consequences

**Complexity:**
- ❌ Stateful connections (harder to scale than stateless HTTP)
- ❌ Requires sticky sessions (load balancing)
- ❌ Memory usage increases with connections (~10KB per connection)
- ❌ Connection management overhead

**Operational Overhead:**
- ❌ Additional infrastructure (Redis pub/sub for multi-server)
- ❌ Monitoring complexity (connection health, reconnection rates)
- ❌ Debugging challenges (connection drops, timing issues)
- ❌ Firewall/proxy compatibility issues

**Browser Limitations:**
- ❌ Some corporate firewalls block WebSocket
- ❌ Proxy servers may timeout long-lived connections
- ❌ Mobile networks may interrupt WebSocket

**Mitigation Strategies:**
```python
# 1. Sticky sessions (Nginx)
upstream websocket_backend {
    ip_hash;  # Route same IP to same server
    server backend1:3000;
    server backend2:3000;
}

# 2. Connection health monitoring
@sio.on('connect')
async def on_connect(sid, environ):
    await sio.save_session(sid, {'last_seen': time.time()})

# 3. Automatic cleanup
async def cleanup_stale_connections():
    async for sid in sio.rooms():
        session = await sio.get_session(sid)
        if time.time() - session['last_seen'] > 300:  # 5 minutes
            await sio.disconnect(sid)
```

---

## Implementation

### Backend (Python Socket.io)

**Installation:**
```bash
pip install "python-socketio[asyncio_client]"
pip install aiohttp
pip install redis
```

**WebSocket Server:**
```python
import socketio
import asyncio
from aiohttp import web

# Create Socket.io server
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# Room management
@sio.on('connect')
async def on_connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.on('subscribe')
async def on_subscribe(sid, data):
    room_id = data['room_id']
    sio.enter_room(sid, room_id)
    await sio.emit('subscribed', {'room_id': room_id}, to=sid)

@sio.on('unsubscribe')
async def on_unsubscribe(sid, data):
    room_id = data['room_id']
    sio.leave_room(sid, room_id)
    await sio.emit('unsubscribed', {'room_id': room_id}, to=sid)

@sio.on('disconnect')
async def on_disconnect(sid):
    print(f"Client disconnected: {sid}")

# Detection updates (from ML service)
async def emit_detection_update(room_id: str, detection: dict):
    await sio.emit('detection_update', detection, room=room_id)

# Start server
if __name__ == '__main__':
    web.run_app(app, port=3001)
```

**Redis Adapter (Multi-Server):**
```python
import socketio
from redis import Redis

# Redis pub/sub for multi-server coordination
redis = Redis(host='localhost', port=6379)
sio = socketio.AsyncServer(
    async_mode='aiohttp',
    client_manager=socketio.AsyncRedisManager(redis=redis)
)
```

### Frontend (Next.js + Socket.io-client)

**Installation:**
```bash
npm install socket.io-client
```

**WebSocket Client:**
```typescript
// lib/websocket.ts
import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;

  connect(roomId: string) {
    this.socket = io(process.env.NEXT_PUBLIC_WS_URL!, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      query: { room_id: roomId }
    });

    this.socket.on('connect', () => {
      console.log('Connected to WebSocket');
      this.socket?.emit('subscribe', { room_id: roomId });
    });

    this.socket.on('detection_update', (data) => {
      console.log('Detection update:', data);
      // Update UI state
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket');
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected after ${attemptNumber} attempts`);
    });

    return this.socket;
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }

  on(event: string, callback: (...args: any[]) => void) {
    this.socket?.on(event, callback);
  }

  off(event: string) {
    this.socket?.off(event);
  }
}

export const wsService = new WebSocketService();
```

**React Hook:**
```typescript
// hooks/useWebSocket.ts
import { useEffect, useState } from 'react';
import { wsService } from '@/lib/websocket';

interface DetectionData {
  presence: boolean;
  count: number;
  confidence: number;
}

export function useWebSocket(roomId: string) {
  const [detection, setDetection] = useState<DetectionData | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = wsService.connect(roomId);

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));
    socket.on('detection_update', (data) => {
      setDetection(data);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('detection_update');
      wsService.disconnect();
    };
  }, [roomId]);

  return { detection, connected };
}
```

**Dashboard Component:**
```typescript
// components/dashboard/RealTimeDashboard.tsx
'use client';

import { useWebSocket } from '@/hooks/useWebSocket';

export function RealTimeDashboard({ roomId }: { roomId: string }) {
  const { detection, connected } = useWebSocket(roomId);

  if (!connected) {
    return <div>Connecting to detection stream...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className={`flex items-center ${connected ? 'text-green-500' : 'text-red-500'}`}>
        <span className="w-2 h-2 rounded-full bg-current mr-2" />
        {connected ? 'Connected' : 'Disconnected'}
      </div>

      {/* Detection Display */}
      {detection && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">People Count</h3>
          <p className="text-5xl font-bold">{detection.count}</p>
          <p className="text-sm text-gray-600 mt-2">
            Confidence: {(detection.confidence * 100).toFixed(1)}%
          </p>
        </div>
      )}
    </div>
  );
}
```

---

## Scalability Strategy

### Single Server Deployment

**Capacity:**
- 100 concurrent connections
- 1,000 messages/second
- Single WebSocket server

**Architecture:**
```
Clients → Load Balancer (Nginx) → WebSocket Server (Python)
```

### Multi-Server Deployment

**Capacity:**
- 1,000+ concurrent connections
- 10,000+ messages/second
- Multiple WebSocket servers

**Architecture:**
```
Clients → Load Balancer (Nginx + Sticky Sessions) →
  ├─ WebSocket Server 1 (Python) ─┐
  ├─ WebSocket Server 2 (Python) ─┼→ Redis Pub/Sub
  └─ WebSocket Server 3 (Python) ─┘
```

**Nginx Configuration:**
```nginx
upstream websocket_backend {
    ip_hash;  # Sticky sessions
    server ws1:3001;
    server ws2:3001;
    server ws3:3001;
}

server {
    listen 80;
    location /socket.io/ {
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

**Redis Adapter Configuration:**
```python
# All servers connect to same Redis
sio = socketio.AsyncServer(
    async_mode='aiohttp',
    client_manager=socketio.AsyncRedisManager(
        'redis://localhost:6379/0'
    )
)

# Broadcasts automatically go to all servers via Redis
await sio.emit('detection_update', data, room=room_id)
```

---

## Success Criteria

- **Latency:** <100ms from detection to UI update (P95)
- **Connection Success Rate:** >99% initial connection success
- **Reconnection Success Rate:** >95% automatic reconnection
- **Concurrent Connections:** Support 100+ simultaneous connections
- **Message Throughput:** 1,000 messages/second per server
- **Browser Compatibility:** Chrome, Firefox, Safari, Edge (latest 2 versions)
- **Mobile Support:** iOS Safari, Android Chrome

---

## References

1. [Socket.io Documentation](https://socket.io/docs/)
2. [WebSocket Protocol (RFC 6455)](https://datatracker.ietf.org/doc/html/rfc6455)
3. [System Architecture Document](/docs/architecture/SYSTEM_ARCHITECTURE.md)

---

**Document End**

*This ADR will be reviewed if latency requirements are not met or if WebSocket adoption issues arise.*
