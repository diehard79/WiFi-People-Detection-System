# ADR-008: Authentication Strategy Selection

**Status:** Accepted
**Date:** 2025-02-02
**Context:** User Authentication and Authorization for WiFi Detection Platform
**Decision:** JWT-Based Authentication with Role-Based Access Control (RBAC)

---

## Context

The application requires secure access control for:
- **Admin Users:** Full system configuration, user management
- **Standard Users:** View dashboards, configure own rooms
- **Read-Only Users:** View-only access (no configuration)
- **Multi-Tenant Support:** Multiple organizations/rooms per account
- **API Access:** authenticated REST and WebSocket endpoints

**Security Requirements:**
- **GDPR Compliance:** Secure user data handling
- **Session Management:** Secure token handling
- **Password Security:** Hashing, salt, complexity requirements
- **Token Expiration:** Configurable session timeouts
- **Revocation:** Ability to invalidate sessions

---

## Decision

**Selected Strategy: JWT (JSON Web Tokens) with HTTP-Only Cookies**

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Authentication Flow                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. LOGIN REQUEST                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/auth/login                             │  │
│  │  Body: { email, password }                           │  │
│  └───────────────┬──────────────────────────────────────┘  │
│                  │                                           │
│                  ▼                                           │
│  2. SERVER VALIDATION                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  - Verify email exists                               │  │
│  │  - Compare password hash (bcrypt)                    │  │
│  │  - Generate JWT (access + refresh tokens)            │  │
│  │  - Set httpOnly cookie (refresh token)               │  │
│  │  - Return access token in body                       │  │
│  └───────────────┬──────────────────────────────────────┘  │
│                  │                                           │
│                  ▼                                           │
│  3. CLIENT STORAGE                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Access Token: Memory (React state)                  │  │
│  │  Refresh Token: HTTP-only cookie (automatic)          │  │
│  └───────────────┬──────────────────────────────────────┘  │
│                  │                                           │
│                  ▼                                           │
│  4. AUTHENTICATED REQUESTS                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  GET /api/v1/detection/count                          │  │
│  │  Headers: Authorization: Bearer <access_token>       │  │
│  └──────────────────────────────────────────────────────┘  │
│                  │                                           │
│                  ▼                                           │
│  5. TOKEN REFRESH (Automatic)                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/auth/refresh                           │  │
│  │  Cookie: refresh_token (httpOnly)                    │  │
│  │  Returns: New access_token                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Authentication Method Comparison

| Method | Security | Scalability | Complexity | Offline Support | MFA Support |
|--------|----------|-------------|------------|-----------------|-------------|
| **JWT (httpOnly)** | High ✅ | Excellent ✅ | Medium ⚠️ | No ❌ | Yes ✅ |
| Session (Cookie) | High ✅ | Medium ⚠️ | Low ✅ | No ❌ | Yes ✅ |
| OAuth 2.0 | High ✅ | Excellent ✅ | High ❌ | No ❌ | Yes ✅ |
| API Key | Low ❌ | Excellent ✅ | Low ✅ | Yes ✅ | No ❌ |
| Magic Link | High ✅ | Good ⚠️ | Medium ⚠️ | No ❌ | No ❌ |

### Why JWT Over Alternatives

**vs. Session-Based Authentication:**

*Session Limitations:*
- ❌ Requires server-side session storage (Redis/database)
- ❌ Harder to scale (sticky sessions required)
- ❌ Database lookup on every request (slower)
- ❌ Server memory overhead (100 bytes per session)

*JWT Advantages:*
- ✅ Stateless (no server-side storage)
- ✅ Scales horizontally (any server can validate)
- ✅ Faster (no database lookup, signature verification only)
- ✅ Self-contained (user data in token)
- ✅ Mobile-friendly (works on native apps)

**vs. OAuth 2.0:**

*OAuth Limitations:*
- ❌ Overkill for single-tenant application
- ❌ Complex setup (multiple endpoints, flows)
- ❌ External provider dependency (if using Google/GitHub)
- ❌ Longer development time

*JWT Advantages:*
- ✅ Simpler implementation
- ✅ Full control over user data
- ✅ No external dependencies
- ✅ Faster development (2-3 days vs. 1-2 weeks)

**vs. API Keys:**

*API Key Limitations:*
- ❌ Not secure for frontend apps (exposed in browser)
- ❌ No expiration (hard to revoke)
- ❌ No user context (can't associate with specific user)
- ❌ Vulnerable to CSRF attacks

*JWT Advantages:*
- ✅ Secure for frontend (short-lived access tokens)
- ✅ Automatic expiration (configurable TTL)
- ✅ User context embedded (user_id, role, permissions)
- ✅ CSRF protection (httpOnly cookies)

### Token Strategy: Dual-Token System

**Access Token (Short-Lived):**
```json
{
  "sub": "user_123",
  "email": "user@example.com",
  "role": "admin",
  "permissions": ["read:detection", "write:configuration"],
  "iat": 1706870400,
  "exp": 1706874000  // 1 hour expiration
}

// Characteristics:
// - Stored in memory (React state)
// - Sent in Authorization header (Bearer token)
// - Short-lived (1 hour)
// - Contains user data (no database lookup needed)
```

**Refresh Token (Long-Lived):**
```json
{
  "sub": "user_123",
  "token_id": "refresh_abc123",
  "iat": 1706870400,
  "exp": 1709462400  // 30 days expiration
}

// Characteristics:
// - Stored in httpOnly cookie (not accessible via JavaScript)
// - Sent automatically with requests (same-site)
// - Long-lived (30 days)
// - Used to obtain new access tokens
// - Revocable (store in database)
```

**Why Dual-Token:**
- ✅ Security (short-lived access tokens limit exposure)
- ✅ User Experience (refresh tokens enable "remember me")
- ✅ Revocation (refresh tokens can be blacklisted)
- ✅ Performance (access tokens don't require database lookup)

---

## Implementation

### Backend (Python FastAPI)

**Installation:**
```bash
pip install "python-jose[cryptography]"
pip install "passlib[bcrypt]"
pip install python-multipart
```

**JWT Utilities:**
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration
SECRET_KEY = "your-secret-key-here"  # Generate with: openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**Authentication Endpoints:**
```python
from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response):
    # 1. Verify user exists
    user = await db.fetch_one(
        "SELECT * FROM users WHERE email = $1", request.email
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2. Verify password
    if not verify_password(request.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 3. Create tokens
    access_token = create_access_token({
        "sub": str(user['id']),
        "email": user['email'],
        "role": user['role']
    })

    refresh_token = create_refresh_token({
        "sub": str(user['id']),
        "token_id": str(uuid4())
    })

    # 4. Store refresh token in database (for revocation)
    await db.execute(
        """INSERT INTO refresh_tokens (token_id, user_id, expires_at)
           VALUES ($1, $2, $3)""",
        refresh_token, user['id'], datetime.utcnow() + timedelta(days=30)
    )

    # 5. Set httpOnly cookie (refresh token)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="lax",  # CSRF protection
        max_age=30 * 24 * 60 * 60  # 30 days
    )

    # 6. Return access token (client stores in memory)
    return {
        "access_token": access_token,
        "user": {
            "id": str(user['id']),
            "email": user['email'],
            "role": user['role']
        }
    }

@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str = Cookie(None)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    # 1. Verify refresh token
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # 2. Check if token is revoked
    token_exists = await db.fetch_val(
        "SELECT EXISTS(SELECT 1 FROM refresh_tokens WHERE token_id = $1 AND revoked = FALSE)",
        payload['token_id']
    )
    if not token_exists:
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    # 3. Get user data
    user = await db.fetch_one(
        "SELECT * FROM users WHERE id = $1", payload['sub']
    )

    # 4. Create new access token
    access_token = create_access_token({
        "sub": str(user['id']),
        "email": user['email'],
        "role": user['role']
    })

    return {"access_token": access_token}

@router.post("/logout")
async def logout(response: Response, refresh_token: str = Cookie(None)):
    # 1. Revoke refresh token in database
    if refresh_token:
        payload = verify_token(refresh_token)
        if payload:
            await db.execute(
                "UPDATE refresh_tokens SET revoked = TRUE WHERE token_id = $1",
                payload['token_id']
            )

    # 2. Clear cookie
    response.delete_cookie("refresh_token")

    return {"message": "Logged out successfully"}
```

**Authentication Middleware:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", payload['sub'])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

async def require_role(required_role: str):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user['role'] != required_role and user['role'] != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )
        return user
    return role_checker

# Usage in endpoints
@app.get("/api/v1/configuration/rooms")
async def get_rooms(user: dict = Depends(get_current_user)):
    return await config_service.get_rooms(user)

@app.delete("/api/v1/configuration/rooms/{room_id}")
async def delete_room(
    room_id: str,
    user: dict = Depends(require_role("admin"))
):
    return await config_service.delete_room(room_id)
```

### Frontend (Next.js)

**Auth Store (Zustand):**
```typescript
// stores/authStore.ts
import create from 'zustand'

interface AuthState {
  user: User | null
  accessToken: string | null
  setAuth: (user: User, accessToken: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  setAuth: (user, accessToken) => set({ user, accessToken }),
  clearAuth: () => set({ user: null, accessToken: null })
}))
```

**Auth Client:**
```typescript
// lib/auth.ts
export const authService = {
  async login(email: string, password: string) {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include'  // Include cookies
    })

    if (!response.ok) {
      throw new Error('Invalid credentials')
    }

    const data = await response.json()
    return data
  },

  async logout() {
    await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include'
    })
  },

  async refreshAccessToken() {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error('Failed to refresh token')
    }

    const data = await response.json()
    return data.access_token
  }
}
```

**Auth Hook (Auto-Refresh):**
```typescript
// hooks/useAuth.ts
import { useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { authService } from '@/lib/auth'

export function useAuth() {
  const { user, accessToken, setAuth, clearAuth } = useAuthStore()

  useEffect(() => {
    // Auto-refresh access token before expiration
    if (accessToken) {
      const tokenData = JSON.parse(atob(accessToken.split('.')[1]))
      const expiresAt = tokenData.exp * 1000
      const refreshTime = expiresAt - Date.now() - 5 * 60 * 1000  // 5 min before

      const timeout = setTimeout(async () => {
        try {
          const newAccessToken = await authService.refreshAccessToken()
          setAuth(user, newAccessToken)
        } catch (error) {
          clearAuth()  // Session expired
        }
      }, refreshTime)

      return () => clearTimeout(timeout)
    }
  }, [accessToken, user])

  return {
    user,
    accessToken,
    isAuthenticated: !!user,
    login: authService.login,
    logout: authService.logout
  }
}
```

**Protected Route Component:**
```typescript
// components/auth/ProtectedRoute.tsx
'use client'

import { useAuth } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'

export function ProtectedRoute({ children, requiredRole }: {
  children: React.ReactNode
  requiredRole?: string
}) {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()

  if (!isAuthenticated) {
    router.push('/login')
    return null
  }

  if (requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
    router.push('/unauthorized')
    return null
  }

  return <>{children}</>
}
```

---

## Security Considerations

### Password Security

**Password Requirements:**
```python
import re

def validate_password(password: str) -> bool:
    """Enforce strong password policy"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False  # At least one uppercase
    if not re.search(r'[a-z]', password):
        return False  # At least one lowercase
    if not re.search(r'[0-9]', password):
        return False  # At least one digit
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False  # At least one special character
    return True
```

**Password Hashing (Bcrypt):**
```python
# Bcrypt with salt (built-in)
# Cost factor: 12 (2^12 = 4096 iterations)
# Example hash: $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW
```

### Token Security

**JWT Best Practices:**
```python
# 1. Use strong secret key (256-bit)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # From environment variable

# 2. Short expiration (access tokens)
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

# 3. Include token version (for forced rotation)
payload = {
    "sub": user_id,
    "version": 1,  # Increment to invalidate all tokens
    "exp": ...
}

# 4. Validate token on every request
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### CSRF Protection

**SameSite Cookies:**
```python
# Set SameSite=lax (or strict)
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,
    samesite="lax"  # CSRF protection
)
```

### Token Revocation

**Refresh Token Blacklist:**
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP
);

-- Revoke all user tokens
UPDATE refresh_tokens
SET revoked = TRUE, revoked_at = NOW()
WHERE user_id = $1 AND revoked = FALSE;
```

---

## Success Criteria

- **Authentication:** <500ms login time
- **Token Refresh:** Automatic (no user interaction)
- **Session Duration:** Configurable (1 hour access, 30 days refresh)
- **Security:** Bcrypt password hashing, JWT signature verification
- **Revocation:** <1 second to revoke all user sessions
- **MFA Ready:** Architecture supports TOTP/SMS MFA (future enhancement)

---

## References

1. [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
2. [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
3. System Architecture Document: `/docs/architecture/SYSTEM_ARCHITECTURE.md`

---

**Document End**

*This ADR will be reviewed if security vulnerabilities are discovered or if OAuth 2.0 integration is required.*
