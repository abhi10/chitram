# Image Hosting App - Phase 3 Requirements (Web UI)

## Overview

This document defines the functional and non-functional requirements for Phase 3 (Web UI) of the Image Hosting Application using the **EARS (Easy Approach to Requirements Specification)** format.

**Phase 3 Goal:** Add a web-based user interface using HTMX and Jinja2 templates for image gallery, upload, and user management.

**Prerequisites:** Phase 2 complete (Auth + Thumbnails)

> **Note:** This document defines *what* to build (requirements). For implementation *progress* and *status*, see [TODO.md](./TODO.md).

---

## EARS Patterns Reference

| Pattern | Template | Use Case |
|---------|----------|----------|
| **Ubiquitous** | The [system] shall [action] | Always-on behavior |
| **Event-driven** | When [trigger], the [system] shall [action] | Response to events |
| **State-driven** | While [state], the [system] shall [action] | Behavior during states |
| **Optional** | Where [feature enabled], the [system] shall [action] | Configurable features |
| **Unwanted** | If [condition], then the [system] shall [action] | Error/edge cases |

---

## Architecture Decision

**Technology Stack:** HTMX + Jinja2 + TailwindCSS (monorepo)

| Option Evaluated | Verdict | Reason |
|------------------|---------|--------|
| **HTMX + Jinja2** | ✅ Chosen | Python-only, fast iteration, no JS build step |
| React SPA | ❌ Deferred | Separate toolchain, overkill for MVP |
| Next.js | ❌ Deferred | Node.js runtime, extra complexity |

**Reference:** [ADR-0013: Web UI with HTMX](docs/adr/0013-web-ui-htmx.md)

---

## Functional Requirements

### FR-3.1: Public Pages

#### FR-3.1.1: Home Page (Gallery)
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.1.1a | The system shall display a gallery of recent public images on the home page | Must |
| FR-3.1.1b | The gallery shall show thumbnails (300px) for faster loading | Must |
| FR-3.1.1c | **When** a user scrolls to the bottom, the system shall load more images (infinite scroll or pagination) | Should |
| FR-3.1.1d | **When** a user clicks an image thumbnail, the system shall navigate to the image detail page | Must |

#### FR-3.1.2: Image Detail Page
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.1.2a | The system shall display the full-size image on the detail page | Must |
| FR-3.1.2b | The system shall display image metadata (filename, size, dimensions, upload date) | Must |
| FR-3.1.2c | The system shall provide a "Copy Link" button to copy the direct image URL | Should |
| FR-3.1.2d | **If** the user is the image owner, the system shall display a "Delete" button | Must |

#### FR-3.1.3: Navigation
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.1.3a | The system shall display a navigation bar on all pages | Must |
| FR-3.1.3b | The navigation bar shall include: Home, Upload, Login/Register (or Profile if logged in) | Must |
| FR-3.1.3c | **While** a user is authenticated, the navigation shall show their email and logout link | Must |

---

### FR-3.2: Authentication Pages

#### FR-3.2.1: Registration Page
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.2.1a | The system shall provide a registration form with email and password fields | Must |
| FR-3.2.1b | **When** registration succeeds, the system shall redirect to the home page as logged in | Must |
| FR-3.2.1c | **If** registration fails, the system shall display the error message inline | Must |
| FR-3.2.1d | The system shall validate email format on the client side before submission | Should |

#### FR-3.2.2: Login Page
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.2.2a | The system shall provide a login form with email and password fields | Must |
| FR-3.2.2b | **When** login succeeds, the system shall store the JWT token and redirect to home | Must |
| FR-3.2.2c | **If** login fails, the system shall display "Invalid credentials" error | Must |
| FR-3.2.2d | The system shall provide a link to the registration page | Should |

#### FR-3.2.3: Logout
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.2.3a | **When** a user clicks logout, the system shall clear the JWT token | Must |
| FR-3.2.3b | **When** logout completes, the system shall redirect to the home page | Must |

---

### FR-3.3: Upload Page

#### FR-3.3.1: Upload Form
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.3.1a | The system shall provide an upload form with file input | Must |
| FR-3.3.1b | The upload form shall support drag-and-drop file selection | Should |
| FR-3.3.1c | The system shall display a file preview before upload | Should |
| FR-3.3.1d | **If** the file is not JPEG or PNG, the system shall display a validation error | Must |
| FR-3.3.1e | **If** the file exceeds 5MB, the system shall display a validation error | Must |

#### FR-3.3.2: Upload Progress
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.3.2a | **While** upload is in progress, the system shall display a progress indicator | Should |
| FR-3.3.2b | **When** upload succeeds, the system shall redirect to the image detail page | Must |
| FR-3.3.2c | **If** upload fails, the system shall display the error message | Must |

#### FR-3.3.3: Anonymous Upload
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.3.3a | **Where** the user is not authenticated, the system shall allow anonymous uploads | Must |
| FR-3.3.3b | **When** anonymous upload succeeds, the system shall display the delete token prominently | Must |
| FR-3.3.3c | The system shall warn: "Save this token! It's the only way to delete this image." | Must |

---

### FR-3.4: User Dashboard

#### FR-3.4.1: My Images Page
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.4.1a | **Where** the user is authenticated, the system shall provide a "My Images" page | Must |
| FR-3.4.1b | The page shall display all images uploaded by the current user | Must |
| FR-3.4.1c | Each image shall have a delete button | Must |
| FR-3.4.1d | **When** delete is clicked, the system shall confirm before deleting | Should |

---

### FR-3.5: HTMX Integration

#### FR-3.5.1: Partial Page Updates
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.5.1a | The system shall use HTMX for form submissions without full page reload | Must |
| FR-3.5.1b | The system shall use HTMX for infinite scroll/load more functionality | Should |
| FR-3.5.1c | The system shall use HTMX for delete confirmations | Should |

#### FR-3.5.2: Error Handling
| ID | EARS Requirement | Priority |
|----|------------------|----------|
| FR-3.5.2a | **If** an HTMX request fails, the system shall display an error toast/message | Must |
| FR-3.5.2b | **If** the JWT token expires, the system shall redirect to login page | Must |

---

## Non-Functional Requirements

### NFR-3.1: Performance

| ID | EARS Requirement | Target | Priority |
|----|------------------|--------|----------|
| NFR-3.1.1 | Gallery page shall load in < 2 seconds on 3G connection | < 2s | Should |
| NFR-3.1.2 | Thumbnails shall be used for gallery (not full images) | Always | Must |
| NFR-3.1.3 | CSS shall be minified and cached | Always | Should |

### NFR-3.2: Accessibility

| ID | EARS Requirement | Priority |
|----|------------------|----------|
| NFR-3.2.1 | All images shall have alt text (filename as fallback) | Should |
| NFR-3.2.2 | Forms shall have proper labels for screen readers | Should |
| NFR-3.2.3 | The site shall be navigable with keyboard only | Should |

### NFR-3.3: Responsiveness

| ID | EARS Requirement | Priority |
|----|------------------|----------|
| NFR-3.3.1 | The UI shall be responsive (mobile, tablet, desktop) | Must |
| NFR-3.3.2 | Gallery shall adjust grid columns based on viewport width | Must |
| NFR-3.3.3 | Navigation shall collapse to hamburger menu on mobile | Should |

### NFR-3.4: Security

| ID | EARS Requirement | Priority |
|----|------------------|----------|
| NFR-3.4.1 | JWT tokens shall be stored in httpOnly cookies (not localStorage) | Must |
| NFR-3.4.2 | CSRF protection shall be enabled for all forms | Must |
| NFR-3.4.3 | All user input shall be sanitized to prevent XSS | Must |

---

## Project Structure

```
backend/
├── app/
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html           # Layout with TailwindCSS
│   │   ├── home.html           # Gallery grid
│   │   ├── upload.html         # Upload form
│   │   ├── image.html          # Image detail
│   │   ├── login.html          # Login form
│   │   ├── register.html       # Registration form
│   │   ├── my_images.html      # User dashboard
│   │   └── partials/           # HTMX fragments
│   │       ├── gallery_item.html
│   │       ├── upload_progress.html
│   │       └── error_toast.html
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css      # TailwindCSS output
│   │   └── js/
│   │       └── htmx.min.js     # HTMX library
│   └── api/
│       └── web.py              # Template routes
```

---

## Page Routes

| Route | Method | Description | Auth Required |
|-------|--------|-------------|---------------|
| `/` | GET | Home page (gallery) | No |
| `/image/{id}` | GET | Image detail page | No |
| `/upload` | GET | Upload form | No |
| `/upload` | POST | Handle upload | No |
| `/login` | GET | Login form | No |
| `/login` | POST | Handle login | No |
| `/register` | GET | Registration form | No |
| `/register` | POST | Handle registration | No |
| `/logout` | POST | Handle logout | Yes |
| `/my-images` | GET | User's images | Yes |

---

## Acceptance Criteria

Phase 3 is considered complete when:

### Public Pages
- [x] Home page shows gallery of images with thumbnails ✅
- [x] Image detail page shows full image and metadata ✅
- [x] Navigation bar present on all pages ✅

### Authentication
- [x] Registration form works ✅
- [x] Login form works ✅
- [ ] JWT stored in httpOnly cookie ⏳ (currently JS-accessible)
- [x] Logout clears token ✅

### Upload
- [x] Upload form works (logged in and anonymous) ✅
- [x] Drag-and-drop works ✅
- [ ] Delete token shown for anonymous uploads ⏳
- [x] Validation errors displayed ✅

### User Dashboard
- [x] My Images page shows user's uploads ✅
- [x] Delete button works with confirmation ✅

### Technical
- [x] HTMX used for partial updates ✅ (Load More)
- [x] Responsive design (mobile/tablet/desktop) ✅ (CSS columns)
- [ ] All forms have CSRF protection ⏳
- [ ] Tests for template routes ⏳

---

## Implementation Status

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 3A: Foundation | ✅ Complete | 100% |
| Phase 3B: Core Pages | ✅ Complete | 100% |
| Phase 3C: Auth + Dashboard | ✅ Complete | 90% |
| Phase 3D: Polish | 🟡 In Progress | 60% |

**Remaining Items:**
- httpOnly cookies (security hardening)
- CSRF protection middleware
- Delete token display for anonymous uploads
- Template route tests
- Accessibility audit

**Runbook:** [docs/PHASE3_UI_RUNBOOK.md](../PHASE3_UI_RUNBOOK.md)

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial Phase 3 UI requirements |
| 1.1 | 2026-01-03 | Added implementation status (Phase 3A-C complete) |

---

## References

- [Phase 2 Requirements](./phase2.md) - API requirements
- [HTMX Documentation](https://htmx.org/docs/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [ADR-0013: Web UI with HTMX](docs/adr/0013-web-ui-htmx.md)
