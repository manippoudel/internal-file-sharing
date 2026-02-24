# CLAUDE.md — Internal File Sharing System

## Project Overview
Internal File Sharing System — production-ready web app for secure internal file management.
- Up to 15 concurrent users, GB-sized files, automated Windows↔Ubuntu sync via Rclone
- Auth, RBAC (admin/user), audit logging, chunked uploads, background scheduler
- Status: 100% complete and production-ready

---

## Architecture

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI | 0.109.1 |
| Language | Python | 3.11+ |
| Database | PostgreSQL | 15 |
| ORM | SQLAlchemy (async) | 2.0.25 |
| DB Driver | asyncpg | 0.29.0 |
| Scheduler | APScheduler | 3.10.4 |
| Frontend | Vue.js | 3.4+ (Composition API) |
| Build | Vite | 5.0 |
| State | Pinia | 2.1.7 |
| Router | Vue Router | 4.2.5 |
| File Upload | Uppy.js | 5.x |
| HTTP Client | Axios | 1.6.5 |
| Infrastructure | Docker Compose | 3 services |

**Ports:** PostgreSQL:5440, Backend:8000, Frontend:5173

---

## Key File Paths

### Backend
- `backend/app/main.py` — FastAPI app entry point, startup events
- `backend/app/config.py` — Pydantic BaseSettings (all env vars)
- `backend/app/database.py` — AsyncSession, engine setup
- `backend/app/models/` — SQLAlchemy models: User, File, Session, AuditLog, UploadChunk, SyncLog, ScheduledTask, SystemSetting
- `backend/app/routers/` — 5 routers: auth, files, admin, audit, scheduler
- `backend/app/services/auth_service.py` — login, session, lockout, password
- `backend/app/services/file_service.py` — chunked upload, soft delete, cleanup
- `backend/app/services/audit_service.py` — audit logging, CSV export
- `backend/app/scheduler/manager.py` — APScheduler with 8 background jobs
- `backend/app/routers/dependencies.py` — get_current_user, get_current_admin_user
- `backend/requirements.txt` — Python deps

### Frontend
- `frontend/src/main.js` — Vue app creation, Pinia, Router, auth init
- `frontend/src/router/index.js` — Routes + navigation guards
- `frontend/src/stores/auth.js` — Pinia auth store (login/logout/fetchCurrentUser)
- `frontend/src/stores/files.js` — Pinia files store (list/sort/search/select)
- `frontend/src/components/FileBrowser.vue` — Main file table with search/sort/pagination
- `frontend/src/components/FileUpload.vue` — Uppy chunked upload integration
- `frontend/src/services/` — authService, fileService, adminService, auditService, schedulerService
- `frontend/vite.config.js` — Proxy `/api` → `http://backend:8000`

### Config / Infrastructure
- `docker-compose.yml` — postgres, backend, frontend + test-db profile
- `.env` / `.env.example` — environment configuration
- `backend/conftest.py` — Pytest async fixtures (db_session, client, auth_headers)
- `backend/pytest.ini` — test paths, markers, coverage config
- `frontend/vitest.config.js` — Vitest + happy-dom config

---

## Development Commands

```bash
# Start
./start-docker.sh          # Full Docker mode (recommended)
./start-dev.sh             # DB in Docker, backend+frontend local

# Stop
./stop-dev.sh

# Backend
cd backend && pytest                              # Run tests
cd backend && pytest --cov=app --cov-report=html # With coverage
cd backend && python create_admin.py             # Create admin user

# Frontend
cd frontend && npm run dev        # Dev server
cd frontend && npm run test       # Run tests
cd frontend && npm run test:coverage

# Access
# Frontend:  http://localhost:5173
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
# Admin:     admin / Admin@12345
```

---

## API Surface (38+ endpoints)

### Auth (`/api/v1/auth`)
- `POST /login` — credentials → session token
- `POST /logout` — invalidate session
- `POST /change-password` — password update
- `GET  /me` — current user info

### Files (`/api/v1/files`)
- `POST /upload/init` → `POST /upload/chunk` → `POST /upload/complete` — chunked upload flow
- `POST /upload/cancel` — cancel upload, clean up chunks
- `GET  /` — paginated list (sort, search, deleted filter)
- `GET  /{id}/download` — stream file as attachment
- `POST /download/bulk` — stream ZIP of multiple files
- `DELETE /{id}` — soft delete (moves to /data/deleted/)
- `POST /{id}/restore` — restore from trash
- `PUT  /{id}/rename` — rename file
- `GET  /check-duplicate/{filename}` — duplicate check
- `GET  /deleted` — list soft-deleted files

### Admin (`/api/v1/admin`)
- CRUD: `GET/POST /users`, `GET/PUT/DELETE /users/{id}`
- `POST /users/{id}/unlock` — unlock locked account
- `POST /users/{id}/reset-password` — force password change
- `GET  /dashboard` — stats (users, files, storage)
- `GET  /storage` — disk usage breakdown
- `GET  /system-health` — CPU, RAM, Disk I/O (psutil)

### Audit (`/api/v1/audit`)
- `GET /logs` — query with filters (user, action, date range)
- `GET /summary` — action counts, top users
- `GET /export` — CSV download
- `GET /my-activity` — current user's own logs

### Scheduler (`/api/v1/scheduler`)
- `GET /tasks` — list all 8 jobs
- `POST /tasks/{id}/pause|resume|trigger` — manage jobs
- `GET /status` — scheduler running status

---

## Key Patterns

### Authentication
- Session-based Bearer tokens stored in DB (NOT JWT)
- 30-min expiry, cleaned up hourly by scheduler
- 5 failed logins → 30-min account lockout

### File Storage Layout
```
/data/
├── active/{YYYY/MM}/filename   # Live files
├── deleted/{YYYY/MM}/filename  # Soft-deleted (90-day retention)
├── temp/{upload_id}/chunk_N    # In-progress uploads (24hr TTL)
├── backups/                    # pg_dump backups
└── logs/
```

### Chunked Upload Flow
1. `POST /upload/init` → get `upload_id`, `chunk_size` (50MB)
2. Split file into 50MB chunks, compute SHA-256 per chunk
3. `POST /upload/chunk` × N — upload with checksum
4. `POST /upload/complete` — assemble, verify final checksum, move to active/

### Database
- All operations use `AsyncSession` from SQLAlchemy 2.0
- Dependency injection via `Depends(get_db_session)`
- Tests use separate DB (port 5433) with per-test rollback via `conftest.py`

### Password Policy
- bcrypt hashing, 12 rounds
- Min 12 chars, requires: uppercase, lowercase, digit, special char

### Background Jobs (8 total, APScheduler)
1. Session cleanup — hourly
2. Chunk cleanup — every 6h
3. Deleted files cleanup — daily 2 AM (90-day retention)
4. Storage check — every 6h (alert if >80%)
5. Win→Ubuntu sync — every 30 min (Rclone)
6. Ubuntu→Win sync — hourly (Rclone)
7. DB backup — daily 1 AM (pg_dump)
8. Audit archival — weekly Sun 3 AM

---

## Database Models

| Model | Key Fields |
|-------|-----------|
| User | id, username, password_hash, email, role, is_active, failed_login_attempts, locked_until, must_change_password |
| File | id, filename, filepath, size, checksum, mime_type, uploaded_by, is_deleted, deleted_at, sync_status |
| Session | id, user_id, token, ip_address, expires_at |
| AuditLog | id, user_id, action, target_file_id, ip_address, details (JSONB), timestamp |
| UploadChunk | id, upload_id, chunk_number, chunk_size, checksum, expires_at, file_path |
| SyncLog | id, sync_type, files_synced, bytes_transferred, status |
| ScheduledTask | id, task_name, cron_expression, is_enabled, last_run_at, next_run_at |
| SystemSetting | id, key (unique), value (JSONB) |

---

## Testing Infrastructure

**Backend (pytest):**
- `backend/tests/` — 6 modules: test_auth_service, test_file_service, test_admin_service, test_audit_service, test_models, test_integration
- 83+ tests, targeting 70%+ coverage
- Markers: `unit`, `integration`, `slow`, `auth`, `files`, `admin`, `audit`
- Test DB: port 5433, `docker-compose --profile test up -d test-db`

**Frontend (Vitest):**
- `frontend/tests/` — stores/auth.test.js, stores/files.test.js, components/
- 25+ tests with @vue/test-utils and happy-dom

---

## Workflow Orchestration

### 1. Plan Node Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

---

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
