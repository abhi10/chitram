# Product Requirements Document: Pluggable Authentication System

**Feature:** Pluggable Authentication Provider Architecture (Supabase-Style)
**Version:** 1.0
**Author:** Product Management
**Date:** 2026-01-07
**Status:** Draft

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Problem Statement](#problem-statement)
- [Goals & Success Metrics](#goals--success-metrics)
- [Architecture Overview](#architecture-overview)
- [User Stories](#user-stories)
- [Functional Requirements](#functional-requirements)
- [Non-Functional Requirements](#non-functional-requirements)
- [Auth Provider Interface Design](#auth-provider-interface-design)
- [Supabase Provider Specification](#supabase-provider-specification)
- [Migration Strategy](#migration-strategy)
- [API Contract Changes](#api-contract-changes)
- [Database Schema Changes](#database-schema-changes)
- [Security Considerations](#security-considerations)
- [Testing Strategy](#testing-strategy)
- [Acceptance Criteria](#acceptance-criteria)
- [Out of Scope](#out-of-scope)
- [Dependencies & Risks](#dependencies--risks)
- [Rollout Strategy](#rollout-strategy)
- [References](#references)

---

## Executive Summary

This PRD defines requirements for replacing Chitram's current custom JWT authentication with a **pluggable authentication system** that supports multiple providers, with **Supabase Auth** as the primary implementation.

### Why Pluggable Auth?

| Current State | Target State |
|---------------|--------------|
| Custom JWT implementation | Provider-agnostic auth interface |
| Manual password hashing (bcrypt) | Delegated to auth provider |
| No password reset | Provider-managed recovery |
| No social login | OAuth providers via Supabase |
| No MFA | Built-in MFA support |
| Self-managed user table | Provider-managed with sync |

### Business Value

1. **Reduced Maintenance**: Delegate auth complexity to battle-tested services
2. **Enhanced Security**: Professional security teams maintain auth infrastructure
3. **Feature Velocity**: Instant access to social login, MFA, magic links
4. **Flexibility**: Swap providers without rewriting application code
5. **Compliance Ready**: OAuth 2.1/OIDC compliance built-in

---

## Problem Statement

### Current Auth Limitations (ADR-0011)

Based on analysis of the existing implementation:

| Limitation | Impact | Business Risk |
|------------|--------|---------------|
| **No password reset** | Users locked out permanently | Support burden, user churn |
| **No email verification** | Fake accounts, typo registrations | Data quality, abuse |
| **No token revocation** | Compromised tokens valid for 24h | Security vulnerability |
| **No social login** | Friction at registration | Lower conversion |
| **No MFA** | Single factor only | Enterprise blockers |
| **No rate limiting on auth** | Brute force vulnerable | Account takeover risk |
| **Manual crypto management** | bcrypt, JWT secrets | Potential misconfig |

### Current Auth Dependencies

The existing system has these touchpoints that must be preserved:

```
Files Affected:
├── app/services/auth_service.py      # 125 lines - REPLACE
├── app/api/auth.py                   # 132 lines - MODIFY
├── app/api/web.py                    # Cookie auth - MODIFY
├── app/api/images.py                 # Protected routes - PRESERVE
├── app/models/user.py                # User model - SYNC/REPLACE
├── app/schemas/auth.py               # Schemas - EXTEND
├── app/services/image_service.py     # Delete tokens - PRESERVE
├── app/config.py                     # JWT config - EXTEND
└── tests/                            # 70+ auth tests - REWRITE
```

---

## Goals & Success Metrics

### Primary Goals

1. **Zero Breaking Changes**: Existing API contracts must be preserved
2. **Provider Agnostic**: Support swapping auth providers via configuration
3. **Supabase First**: Full Supabase Auth integration as default provider
4. **Graceful Migration**: Existing users can continue using the system

### Success Metrics (KPIs)

| Metric | Current | Target |
|--------|---------|--------|
| Auth-related code lines | 650+ | < 200 (excluding provider impl) |
| Password reset support | No | Yes |
| Social login providers | 0 | 3+ (Google, GitHub, etc.) |
| MFA support | No | Yes (TOTP) |
| Token revocation | No | Yes |
| Auth test coverage | 70 tests | 70+ tests (adapted) |
| Migration success rate | N/A | 100% existing users |

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Routes    │  Dependencies     │  Services               │
│  (/api/v1/auth/*)  │  (get_current_user)│  (ImageService)        │
└────────────┬───────┴────────┬──────────┴──────────┬─────────────┘
             │                │                      │
             ▼                ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Auth Provider Interface                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  class AuthProvider(ABC):                                │   │
│  │    + register(email, password) -> AuthResult             │   │
│  │    + login(email, password) -> AuthResult                │   │
│  │    + verify_token(token) -> UserInfo | None              │   │
│  │    + refresh_token(refresh_token) -> AuthResult          │   │
│  │    + logout(token) -> bool                               │   │
│  │    + get_user(user_id) -> UserInfo | None                │   │
│  │    + reset_password_request(email) -> bool               │   │
│  │    + reset_password_confirm(token, new_password) -> bool │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             ▼                                    ▼
┌─────────────────────────┐        ┌─────────────────────────────┐
│   SupabaseAuthProvider  │        │   LocalAuthProvider         │
│   (Primary - Production)│        │   (Fallback - Development)  │
├─────────────────────────┤        ├─────────────────────────────┤
│  - Supabase Python SDK  │        │  - Current bcrypt/JWT impl  │
│  - GoTrue API calls     │        │  - For offline/testing      │
│  - Managed user storage │        │  - Local PostgreSQL users   │
└────────────┬────────────┘        └──────────────┬──────────────┘
             │                                    │
             ▼                                    ▼
┌─────────────────────────┐        ┌─────────────────────────────┐
│    Supabase Cloud       │        │   Local PostgreSQL          │
│    (Auth + Database)    │        │   (users table)             │
└─────────────────────────┘        └─────────────────────────────┘
```

### Provider Selection Flow

```
Application Startup
       │
       ▼
┌──────────────────┐
│ Read AUTH_PROVIDER│
│ from config      │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│supabase│ │ local │
└───┬───┘ └───┬───┘
    │         │
    ▼         ▼
┌─────────────────────┐  ┌─────────────────────┐
│SupabaseAuthProvider │  │ LocalAuthProvider   │
│ - Validate config   │  │ - Use existing impl │
│ - Test connection   │  │ - JWT + bcrypt      │
│ - Initialize client │  │ - Local DB          │
└─────────────────────┘  └─────────────────────┘
```

---

## User Stories

### Epic 1: Auth Provider Abstraction

#### US-1.1: Provider Interface Definition
**As a** developer
**I want** a well-defined auth provider interface
**So that** I can implement different auth backends without changing application code

**Acceptance Criteria:**
- Abstract base class `AuthProvider` defines all required methods
- Methods use standardized input/output types (not provider-specific)
- Interface supports: register, login, logout, verify, refresh, password reset
- Provider selection via `AUTH_PROVIDER` environment variable
- Provider initialized during application lifespan

---

#### US-1.2: Supabase Provider Implementation
**As a** developer
**I want** a Supabase-specific provider implementation
**So that** I can use Supabase Auth as the authentication backend

**Acceptance Criteria:**
- `SupabaseAuthProvider` implements `AuthProvider` interface
- Uses official `supabase-py` SDK
- Supports email/password authentication
- Supports OAuth providers (Google, GitHub) via Supabase config
- Handles token refresh automatically
- Maps Supabase user to application `UserInfo` model

---

#### US-1.3: Local Provider Implementation (Fallback)
**As a** developer
**I want** a local auth provider for development/testing
**So that** I can work offline and run tests without external dependencies

**Acceptance Criteria:**
- `LocalAuthProvider` implements `AuthProvider` interface
- Uses existing bcrypt/JWT implementation
- Stores users in local PostgreSQL (current behavior)
- Feature-compatible with Supabase provider (except social login)
- Default provider when `AUTH_PROVIDER=local`

---

#### US-1.4: Provider Configuration
**As a** DevOps engineer
**I want** to configure auth providers via environment variables
**So that** I can switch providers without code changes

**Acceptance Criteria:**
- `AUTH_PROVIDER`: "supabase" | "local" (default: "local")
- Supabase config: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`
- Local config: existing `JWT_SECRET_KEY`, `JWT_EXPIRE_MINUTES`
- Validation on startup: fail fast if required config missing
- Health endpoint reports active provider

---

### Epic 2: Supabase Integration

#### US-2.1: Supabase Registration
**As a** new user
**I want to** register with email and password via Supabase
**So that** my account is securely managed

**Acceptance Criteria:**
- `POST /api/v1/auth/register` delegates to Supabase `auth.sign_up()`
- Email confirmation sent by Supabase (configurable)
- User created in Supabase `auth.users` table
- Local `users` table synced with Supabase user ID
- Response format unchanged: `{user, access_token, token_type}`
- Error handling maps Supabase errors to existing error codes

---

#### US-2.2: Supabase Login
**As a** registered user
**I want to** login with email and password
**So that** I receive access and refresh tokens

**Acceptance Criteria:**
- `POST /api/v1/auth/login` delegates to Supabase `auth.sign_in_with_password()`
- Returns access_token (JWT) and refresh_token
- Refresh token stored in httpOnly cookie (web) or returned in response (API)
- Session tracked in Supabase
- Failed login returns 401 with generic error (no enumeration)

---

#### US-2.3: Token Verification
**As the** application
**I want to** verify JWT tokens issued by Supabase
**So that** I can authenticate API requests

**Acceptance Criteria:**
- `verify_token()` validates Supabase JWT signature
- Uses Supabase JWT secret or public key (RS256)
- Extracts user_id from token `sub` claim
- Checks token expiration
- Returns `UserInfo` or raises `AuthenticationError`

---

#### US-2.4: Token Refresh
**As a** logged-in user
**I want** my session to refresh automatically
**So that** I don't have to login repeatedly

**Acceptance Criteria:**
- `POST /api/v1/auth/refresh` endpoint added
- Accepts refresh_token, returns new access_token
- Supabase handles refresh logic
- Old refresh token invalidated (rotation)
- Web UI refreshes token before expiry

---

#### US-2.5: Logout with Token Revocation
**As a** logged-in user
**I want to** logout and invalidate my session
**So that** my tokens cannot be reused

**Acceptance Criteria:**
- `POST /api/v1/auth/logout` calls Supabase `auth.sign_out()`
- Access token added to revocation list (Supabase managed)
- Refresh token invalidated
- Cookie cleared (web UI)
- Subsequent requests with old token return 401

---

#### US-2.6: Password Reset
**As a** user who forgot my password
**I want to** reset it via email
**So that** I can regain access to my account

**Acceptance Criteria:**
- `POST /api/v1/auth/forgot-password` triggers Supabase password reset email
- Email contains secure reset link (Supabase hosted or custom)
- `POST /api/v1/auth/reset-password` accepts token + new password
- Old sessions invalidated after password change
- Rate limited to prevent abuse

---

### Epic 3: Social Login (OAuth)

#### US-3.1: OAuth Provider Support
**As a** user
**I want to** login with Google or GitHub
**So that** I don't need to remember another password

**Acceptance Criteria:**
- `GET /api/v1/auth/oauth/{provider}` initiates OAuth flow
- Supported providers: Google, GitHub (Supabase configured)
- Redirects to provider consent screen
- Callback handles token exchange
- Creates/links user account automatically
- Returns same auth response as email login

---

#### US-3.2: Account Linking
**As a** user with existing email account
**I want to** link my social login
**So that** I can login with either method

**Acceptance Criteria:**
- OAuth login with existing email links accounts
- User can unlink social provider from settings (future)
- Primary email remains from original registration
- Supabase handles identity linking

---

### Epic 4: Multi-Factor Authentication

#### US-4.1: MFA Enrollment
**As a** security-conscious user
**I want to** enable TOTP-based MFA
**So that** my account has additional protection

**Acceptance Criteria:**
- `POST /api/v1/auth/mfa/enroll` initiates TOTP setup
- Returns QR code / secret for authenticator app
- `POST /api/v1/auth/mfa/verify` confirms enrollment with code
- MFA status stored in Supabase user metadata
- Recovery codes generated and shown once

---

#### US-4.2: MFA Challenge
**As a** user with MFA enabled
**I want to** provide TOTP code during login
**So that** my account is protected by second factor

**Acceptance Criteria:**
- Login returns `mfa_required: true` if MFA enabled
- `POST /api/v1/auth/mfa/challenge` accepts TOTP code
- Successful challenge returns full auth tokens
- Failed challenge returns 401 with attempts remaining
- Recovery code can be used instead of TOTP

---

### Epic 5: Backward Compatibility

#### US-5.1: API Contract Preservation
**As an** API consumer
**I want** existing auth endpoints to work unchanged
**So that** my integration doesn't break

**Acceptance Criteria:**
- `POST /api/v1/auth/register` - same request/response schema
- `POST /api/v1/auth/login` - same request/response schema
- `POST /api/v1/auth/token` - OAuth2 form endpoint preserved
- `GET /api/v1/auth/me` - same user response schema
- All existing error codes preserved

---

#### US-5.2: Protected Route Compatibility
**As a** developer
**I want** `get_current_user` dependency to work with any provider
**So that** protected routes don't need changes

**Acceptance Criteria:**
- `Depends(get_current_user)` works with Supabase tokens
- `Depends(require_current_user)` raises 401 appropriately
- Image upload continues to require authentication
- Image deletion authorization logic unchanged
- Cookie-based auth for web UI continues working

---

#### US-5.3: User Data Migration
**As an** existing user
**I want** my account migrated to Supabase
**So that** I can continue using the service

**Acceptance Criteria:**
- Migration script exports local users to Supabase
- Password hashes compatible (or force reset)
- User IDs preserved or mapped
- Images retain user ownership
- Delete tokens continue working

---

### Epic 6: Web UI Auth Flow

#### US-6.1: Cookie-Based Session (Web)
**As a** web user
**I want** my session managed via cookies
**So that** I stay logged in across page loads

**Acceptance Criteria:**
- Login sets `httpOnly` cookie with access_token
- Refresh token stored in separate `httpOnly` cookie
- CSRF protection enabled for cookie-based auth
- Auto-refresh before token expiry
- Logout clears all auth cookies

---

#### US-6.2: OAuth Redirect Flow (Web)
**As a** web user clicking "Login with Google"
**I want** a seamless redirect experience
**So that** I can authenticate without confusion

**Acceptance Criteria:**
- Click initiates redirect to Google consent
- Callback URL handles code exchange
- Success redirects to intended page (or home)
- Error shows user-friendly message
- State parameter prevents CSRF

---

---

## Functional Requirements

### FR-1: Auth Provider Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System shall define abstract `AuthProvider` interface | Must Have |
| FR-1.2 | Interface shall include: register, login, logout, verify_token, refresh_token, get_user | Must Have |
| FR-1.3 | Interface shall include: reset_password_request, reset_password_confirm | Should Have |
| FR-1.4 | Interface shall include: oauth_authorize, oauth_callback | Should Have |
| FR-1.5 | Interface shall include: mfa_enroll, mfa_verify, mfa_challenge | Nice to Have |
| FR-1.6 | Provider selection shall be configurable via environment variable | Must Have |
| FR-1.7 | System shall validate provider configuration on startup | Must Have |

### FR-2: Supabase Provider

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Supabase provider shall implement all `AuthProvider` methods | Must Have |
| FR-2.2 | Provider shall use official `supabase-py` SDK | Must Have |
| FR-2.3 | Provider shall handle Supabase-specific errors gracefully | Must Have |
| FR-2.4 | Provider shall map Supabase user to application UserInfo | Must Have |
| FR-2.5 | Provider shall support email confirmation flow | Should Have |
| FR-2.6 | Provider shall support OAuth providers configured in Supabase | Should Have |

### FR-3: Local Provider (Fallback)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Local provider shall implement core `AuthProvider` methods | Must Have |
| FR-3.2 | Local provider shall use existing bcrypt/JWT implementation | Must Have |
| FR-3.3 | Local provider shall be default when AUTH_PROVIDER not set | Must Have |
| FR-3.4 | Local provider shall work without external dependencies | Must Have |

### FR-4: API Endpoints

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Existing endpoints shall maintain backward compatibility | Must Have |
| FR-4.2 | New endpoint: POST /api/v1/auth/refresh | Should Have |
| FR-4.3 | New endpoint: POST /api/v1/auth/forgot-password | Should Have |
| FR-4.4 | New endpoint: POST /api/v1/auth/reset-password | Should Have |
| FR-4.5 | New endpoint: GET /api/v1/auth/oauth/{provider} | Nice to Have |
| FR-4.6 | New endpoint: GET /api/v1/auth/oauth/callback | Nice to Have |

### FR-5: User Synchronization

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | System shall sync Supabase users to local database | Must Have |
| FR-5.2 | Sync shall occur on first login / registration | Must Have |
| FR-5.3 | Local user record shall store Supabase user ID | Must Have |
| FR-5.4 | Image ownership shall reference synced user | Must Have |

---

## Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Token verification latency (cached) | < 10ms |
| NFR-1.2 | Token verification latency (uncached) | < 100ms |
| NFR-1.3 | Login response time | < 500ms |
| NFR-1.4 | Registration response time | < 1s |

### NFR-2: Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-2.1 | Auth system availability | 99.9% (Supabase SLA) |
| NFR-2.2 | Graceful degradation if Supabase unavailable | Cached tokens valid |
| NFR-2.3 | Local provider fallback for development | Always available |

### NFR-3: Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-3.1 | Token signature algorithm | RS256 (asymmetric) |
| NFR-3.2 | Access token lifetime | 1 hour (configurable) |
| NFR-3.3 | Refresh token lifetime | 7 days (configurable) |
| NFR-3.4 | Password requirements | Supabase default (8+ chars) |
| NFR-3.5 | Rate limiting on auth endpoints | 10 req/min per IP |

### NFR-4: Compatibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-4.1 | Python version | 3.11+ |
| NFR-4.2 | Supabase SDK version | Latest stable |
| NFR-4.3 | Existing API contract | 100% backward compatible |

---

## Auth Provider Interface Design

### Abstract Base Class

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class AuthProviderType(str, Enum):
    SUPABASE = "supabase"
    LOCAL = "local"

@dataclass
class UserInfo:
    """Provider-agnostic user representation."""
    id: str
    email: str
    is_active: bool
    created_at: datetime
    email_verified: bool = False
    metadata: dict = field(default_factory=dict)

@dataclass
class AuthResult:
    """Authentication result with tokens."""
    user: UserInfo
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = 3600
    mfa_required: bool = False

@dataclass
class AuthError:
    """Standardized auth error."""
    code: str
    message: str
    details: dict = field(default_factory=dict)

class AuthProvider(ABC):
    """Abstract interface for authentication providers."""

    @abstractmethod
    async def register(
        self,
        email: str,
        password: str,
        metadata: dict | None = None
    ) -> AuthResult:
        """Register new user."""
        pass

    @abstractmethod
    async def login(
        self,
        email: str,
        password: str
    ) -> AuthResult:
        """Authenticate user with credentials."""
        pass

    @abstractmethod
    async def verify_token(
        self,
        token: str
    ) -> UserInfo | None:
        """Verify access token and return user info."""
        pass

    @abstractmethod
    async def refresh_token(
        self,
        refresh_token: str
    ) -> AuthResult:
        """Refresh access token."""
        pass

    @abstractmethod
    async def logout(
        self,
        token: str
    ) -> bool:
        """Invalidate user session."""
        pass

    @abstractmethod
    async def get_user(
        self,
        user_id: str
    ) -> UserInfo | None:
        """Get user by ID."""
        pass

    # Optional methods with default implementations
    async def reset_password_request(self, email: str) -> bool:
        """Request password reset email."""
        raise NotImplementedError("Password reset not supported")

    async def reset_password_confirm(
        self,
        token: str,
        new_password: str
    ) -> bool:
        """Confirm password reset with token."""
        raise NotImplementedError("Password reset not supported")

    async def oauth_authorize(
        self,
        provider: str,
        redirect_uri: str
    ) -> str:
        """Get OAuth authorization URL."""
        raise NotImplementedError("OAuth not supported")

    async def oauth_callback(
        self,
        provider: str,
        code: str
    ) -> AuthResult:
        """Handle OAuth callback."""
        raise NotImplementedError("OAuth not supported")
```

### Provider Factory

```python
def get_auth_provider(settings: Settings) -> AuthProvider:
    """Factory function to create auth provider based on config."""
    provider_type = AuthProviderType(settings.auth_provider)

    if provider_type == AuthProviderType.SUPABASE:
        return SupabaseAuthProvider(
            url=settings.supabase_url,
            anon_key=settings.supabase_anon_key,
            service_key=settings.supabase_service_key,
        )
    elif provider_type == AuthProviderType.LOCAL:
        return LocalAuthProvider(
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expire_minutes=settings.jwt_expire_minutes,
        )
    else:
        raise ValueError(f"Unknown auth provider: {provider_type}")
```

---

## Supabase Provider Specification

### Configuration

```python
# Environment Variables
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
AUTH_PROVIDER=supabase
```

### SDK Usage Patterns

```python
from supabase import create_client, Client

class SupabaseAuthProvider(AuthProvider):
    def __init__(self, url: str, anon_key: str, service_key: str):
        self.client: Client = create_client(url, anon_key)
        self.admin_client: Client = create_client(url, service_key)

    async def register(self, email: str, password: str, metadata: dict | None = None) -> AuthResult:
        response = self.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": metadata or {}}
        })
        # Map response to AuthResult
        return self._map_auth_response(response)

    async def login(self, email: str, password: str) -> AuthResult:
        response = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return self._map_auth_response(response)

    async def verify_token(self, token: str) -> UserInfo | None:
        # Decode and verify JWT (Supabase uses HS256 with JWT secret)
        # Or use admin client to get user
        response = self.admin_client.auth.get_user(token)
        if response.user:
            return self._map_user(response.user)
        return None
```

### Error Mapping

| Supabase Error | Application Error Code | HTTP Status |
|----------------|------------------------|-------------|
| `invalid_credentials` | `INVALID_CREDENTIALS` | 401 |
| `user_already_registered` | `EMAIL_EXISTS` | 400 |
| `email_not_confirmed` | `EMAIL_NOT_VERIFIED` | 403 |
| `token_expired` | `TOKEN_EXPIRED` | 401 |
| `invalid_token` | `INVALID_TOKEN` | 401 |
| `user_not_found` | `USER_NOT_FOUND` | 404 |

---

## Migration Strategy

### Phase 1: Interface Abstraction (Non-Breaking)

1. Create `AuthProvider` abstract class
2. Create `LocalAuthProvider` wrapping existing `AuthService`
3. Update dependencies to use provider interface
4. All tests continue passing

### Phase 2: Supabase Provider Implementation

1. Implement `SupabaseAuthProvider`
2. Add Supabase configuration options
3. Create integration tests with Supabase
4. Feature flag for provider selection

### Phase 3: User Migration

```
Migration Script Flow:
┌─────────────────────┐
│ Read local users    │
│ from PostgreSQL     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ For each user:      │
│ - Create in Supabase│
│ - Force password    │
│   reset email       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Update local user   │
│ with Supabase ID    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Verify image        │
│ ownership intact    │
└─────────────────────┘
```

### Phase 4: Cutover

1. Set `AUTH_PROVIDER=supabase` in production
2. Monitor auth metrics
3. Disable local provider registration (login only for migration)
4. Remove local auth code after migration window

---

## API Contract Changes

### Preserved Endpoints (No Changes)

| Endpoint | Method | Notes |
|----------|--------|-------|
| `/api/v1/auth/register` | POST | Same request/response |
| `/api/v1/auth/login` | POST | Same request/response |
| `/api/v1/auth/token` | POST | OAuth2 form preserved |
| `/api/v1/auth/me` | GET | Same user response |

### New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/logout` | POST | Logout and revoke tokens |
| `/api/v1/auth/forgot-password` | POST | Request password reset |
| `/api/v1/auth/reset-password` | POST | Confirm password reset |
| `/api/v1/auth/oauth/{provider}` | GET | Initiate OAuth flow |
| `/api/v1/auth/oauth/callback` | GET | OAuth callback handler |
| `/api/v1/auth/mfa/enroll` | POST | Start MFA enrollment |
| `/api/v1/auth/mfa/verify` | POST | Verify MFA setup |
| `/api/v1/auth/mfa/challenge` | POST | Verify MFA code on login |

### Response Schema Additions

```python
# Extended AuthResponse
class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str | None = None  # NEW
    token_type: str = "bearer"
    expires_in: int = 3600  # NEW
    mfa_required: bool = False  # NEW

# Extended UserResponse
class UserResponse(BaseModel):
    id: str
    email: str
    is_active: bool
    created_at: datetime
    email_verified: bool = False  # NEW
    mfa_enabled: bool = False  # NEW
```

---

## Database Schema Changes

### Option A: Sync Model (Recommended)

Keep local `users` table, sync with Supabase:

```sql
-- Add Supabase reference to existing users table
ALTER TABLE users ADD COLUMN supabase_id VARCHAR(36) UNIQUE;
ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20) DEFAULT 'local';

-- Index for lookups
CREATE INDEX idx_users_supabase_id ON users(supabase_id);
```

### Option B: Reference Model

Remove local users, reference Supabase directly:

```sql
-- Drop local users table
-- Update images FK to reference Supabase user ID directly
ALTER TABLE images DROP CONSTRAINT images_user_id_fkey;
ALTER TABLE images ADD COLUMN supabase_user_id VARCHAR(36);
-- Migrate existing user_id values
```

### Recommendation

**Option A (Sync Model)** is recommended because:
- Preserves existing foreign key relationships
- Allows local queries without Supabase API calls
- Supports offline/fallback scenarios
- Simpler migration path

---

## Security Considerations

### Token Security

| Aspect | Local Provider | Supabase Provider |
|--------|----------------|-------------------|
| Algorithm | HS256 | RS256 (recommended) |
| Secret Storage | .env file | Supabase managed |
| Token Revocation | Not supported | Supabase managed |
| Refresh Tokens | Not implemented | Supported |

### Cookie Security (Web UI)

```python
# Secure cookie settings
COOKIE_SETTINGS = {
    "httponly": True,
    "secure": True,  # HTTPS only
    "samesite": "lax",
    "max_age": 3600,  # 1 hour for access token
}

REFRESH_COOKIE_SETTINGS = {
    "httponly": True,
    "secure": True,
    "samesite": "strict",
    "max_age": 604800,  # 7 days for refresh token
    "path": "/api/v1/auth/refresh",  # Limit scope
}
```

### CSRF Protection

- Required for cookie-based auth
- Use `itsdangerous` for CSRF tokens (already in dependencies)
- Validate on all state-changing endpoints

---

## Testing Strategy

### Test Categories

| Category | Description | Provider |
|----------|-------------|----------|
| Unit Tests | Provider interface, error mapping | Mock |
| Integration Tests | Supabase API calls | Supabase Test Project |
| Contract Tests | API backward compatibility | Local |
| E2E Tests | Full auth flows | Both |

### Test Fixtures

```python
@pytest.fixture
def mock_auth_provider():
    """Mock auth provider for unit tests."""
    provider = Mock(spec=AuthProvider)
    provider.verify_token.return_value = UserInfo(
        id="test-user-id",
        email="test@example.com",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    return provider

@pytest.fixture
async def supabase_test_user(supabase_provider):
    """Create test user in Supabase."""
    result = await supabase_provider.register(
        email=f"test-{uuid4()}@example.com",
        password="TestPassword123!",
    )
    yield result.user
    # Cleanup: delete test user
    await supabase_provider.admin_delete_user(result.user.id)
```

### Migration Tests

```python
async def test_migration_preserves_image_ownership():
    """Verify images remain linked to correct user after migration."""
    # Create user with local provider
    # Upload image
    # Migrate user to Supabase
    # Verify image.user_id still works
    # Verify deletion authorization still works
```

---

## Acceptance Criteria

### Definition of Done

- [ ] `AuthProvider` interface defined with all required methods
- [ ] `LocalAuthProvider` wraps existing implementation
- [ ] `SupabaseAuthProvider` implements all methods
- [ ] Provider selection via `AUTH_PROVIDER` config
- [ ] All existing auth tests pass with local provider
- [ ] New integration tests for Supabase provider
- [ ] API backward compatibility verified
- [ ] Migration script for existing users
- [ ] Documentation updated
- [ ] Security review completed

### Demo Checklist

1. [ ] Register with email/password (Supabase)
2. [ ] Login and receive tokens (Supabase)
3. [ ] Access protected route with Supabase token
4. [ ] Refresh token works
5. [ ] Logout invalidates session
6. [ ] Password reset flow works
7. [ ] OAuth login with Google/GitHub
8. [ ] Existing local provider still works
9. [ ] Switch providers via config
10. [ ] Migrate existing user to Supabase

---

## Out of Scope

| Feature | Reason | Future Phase |
|---------|--------|--------------|
| Enterprise SSO (SAML) | Complexity | Phase 5+ |
| Custom OAuth providers | Start with built-in | Phase 5+ |
| Passwordless (magic link only) | Focus on password first | Phase 4.5 |
| Phone/SMS auth | Regional complexity | Future |
| Custom email templates | Use Supabase defaults | Phase 4.5 |
| Admin user management UI | API-only for now | Phase 5+ |

---

## Dependencies & Risks

### Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Supabase project setup | DevOps | Required |
| `supabase-py` SDK | PyPI | Available |
| Supabase Auth configuration | DevOps | Required |
| OAuth app credentials (Google, GitHub) | DevOps | Optional |

### Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Supabase downtime | Auth unavailable | Low | Local provider fallback, cached tokens |
| Migration data loss | Users locked out | Medium | Thorough testing, rollback plan |
| API breaking changes | Client apps fail | High | Contract tests, staged rollout |
| Supabase pricing changes | Cost increase | Low | Provider abstraction allows switching |
| Password hash incompatibility | Users can't login | Medium | Force password reset on migration |

---

## Rollout Strategy

### Phase 1: Foundation (Week 1)

- [ ] Create `AuthProvider` interface
- [ ] Wrap existing code in `LocalAuthProvider`
- [ ] Refactor dependencies to use interface
- [ ] All tests passing

### Phase 2: Supabase Implementation (Week 2)

- [ ] Implement `SupabaseAuthProvider`
- [ ] Create Supabase test project
- [ ] Integration tests
- [ ] Password reset & refresh token endpoints

### Phase 3: OAuth & MFA (Week 3)

- [ ] OAuth provider support
- [ ] MFA enrollment/challenge
- [ ] Web UI updates for new flows

### Phase 4: Migration & Cutover (Week 4)

- [ ] User migration script
- [ ] Staged rollout (10% → 50% → 100%)
- [ ] Monitor and fix issues
- [ ] Deprecate local provider for new registrations

### Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `auth_provider` | local | Active auth provider |
| `enable_oauth` | false | Enable OAuth login buttons |
| `enable_mfa` | false | Enable MFA enrollment |
| `enable_password_reset` | false | Enable password reset flow |

---

## References

### Official Documentation

- [Supabase Auth Architecture](https://supabase.com/docs/guides/auth/architecture)
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Supabase Python SDK](https://supabase.com/docs/reference/python/introduction)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

### Design Patterns

- [Strategy Pattern for Authentication](https://refactoring.guru/design-patterns/strategy)
- [FastAPI Best Practices](https://medium.com/@lautisuarez081/fastapi-best-practices-and-design-patterns-building-quality-python-apis-31774ff3c28a)
- [Dependency Inversion Principle](https://camillovisini.com/coding/abstracting-fastapi-services)

### Implementation References

- [FastAPI Supabase Template](https://github.com/AtticusZeller/fastapi_supabase_template) - Reference implementation
- [FastAPI Flask Quickstart](https://supabase.com/docs/guides/getting-started/quickstarts/flask) - Pattern reference
- [FastAPI + Supabase Article](https://adarshkumardalai.medium.com/the-story-of-when-fastapi-met-supabase-47b69a5878cd)

### Internal Documents

- [ADR-0011: User Authentication with JWT](../adr/0011-user-authentication-jwt.md)
- [Current Auth Implementation Analysis](#problem-statement)

---

*Document Version: 1.0*
*Last Updated: 2026-01-07*
*Next Review: Before implementation kickoff*
