# Internal File Sharing System - Requirements Document

## Project Overview

An internal file sharing web application for 15 users to upload, download, browse, and manage GB-sized files. Syncs bidirectionally with a remote Windows server.

---

## 1. Functional Requirements

### 1.1 User Authentication & Authorization

| ID | Requirement | Priority |
|----|-------------|----------|
| AUTH-01 | Users must log in with username and password | High |
| AUTH-02 | Admin can create, edit, and delete user accounts | High |
| AUTH-03 | Password policy: minimum 12 characters with complexity | High |
| AUTH-04 | Account lockout after 5 failed login attempts | High |
| AUTH-05 | Session timeout after 30 minutes of inactivity | Medium |
| AUTH-06 | Maximum 15 concurrent active sessions | Medium |
| AUTH-07 | Optional: Two-factor authentication (2FA) with authenticator app | Low |
| AUTH-08 | Admin can manually unlock locked accounts | Medium |
| AUTH-09 | Users can change their own password | High |
| AUTH-10 | Force password change on first login | Medium |

### 1.2 File Browser

| ID | Requirement | Priority |
|----|-------------|----------|
| FB-01 | Display files with name, size, modified date, and actions | High |
| FB-02 | Navigate folder hierarchy with breadcrumb navigation | High |
| FB-03 | Pagination: 100 files per page | High |
| FB-04 | Virtual scrolling for large file lists | Low |
| FB-05 | Lazy load thumbnails/previews | Low |
| FB-06 | Cache file list with 30-second refresh interval | Medium |
| FB-07 | All files visible to all authenticated users | High |
| FB-08 | Sort by name, size, date, uploader (ascending/descending) | High |
| FB-09 | Preview common file types (PDF, images, text) without download | Medium |

### 1.3 File Upload

| ID | Requirement | Priority |
|----|-------------|----------|
| UP-01 | Drag & drop file upload interface | High |
| UP-02 | Browse button for file selection | High |
| UP-03 | Chunked upload: 50-100 MB chunks for large files | High |
| UP-04 | Resume capability: continue from last chunk on failure | High |
| UP-05 | Progress indicator: percentage, speed, ETA | High |
| UP-06 | Upload queue display per user | High |
| UP-07 | Maximum 3 simultaneous uploads per user | Medium |
| UP-08 | Cancel individual uploads without affecting others | High |
| UP-09 | File appears in browser immediately after upload | High |
| UP-10 | Lock files during upload to prevent conflicts | Medium |
| UP-11 | Duplicate file handling: warn if file exists (overwrite/rename/skip) | High |

### 1.4 File Download

| ID | Requirement | Priority |
|----|-------------|----------|
| DL-01 | Single file: direct streaming download | High |
| DL-02 | Multiple files: zip archive creation and download | High |
| DL-03 | Large files (>500 MB): streaming with progress | High |
| DL-04 | Support range requests for pause/resume | Medium |
| DL-05 | Generate download links with 1-hour expiration | Medium |
| DL-06 | Maximum 5 simultaneous downloads per user | Medium |
| DL-07 | Queue additional downloads beyond limit | Medium |

### 1.5 File Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FM-01 | Soft delete files (move to deleted folder) | High |
| FM-02 | Restore soft-deleted files | High |
| FM-03 | Retain deleted files for 90 days (configurable) | High |
| FM-04 | Permanent delete after retention period | High |
| FM-05 | Bulk operations: multi-select delete/download | High |
| FM-06 | Search files by name and date | High |
| FM-07 | Advanced filters (size, type, date range, uploader) | Medium |
| FM-08 | Rename files | Medium |
| FM-09 | Move files between folders | Medium |

### 1.6 Sync Service (Windows ↔ Ubuntu)

| ID | Requirement | Priority |
|----|-------------|----------|
| SYNC-01 | Bidirectional sync with remote Windows server | High |
| SYNC-02 | Incremental sync: only changed portions (delta transfer) | High |
| SYNC-03 | Checksum verification before/after transfer | High |
| SYNC-04 | Resume interrupted sync transfers | High |
| SYNC-05 | Windows → Ubuntu: every 30 min (off-peak) or hourly (peak) | Medium |
| SYNC-06 | Ubuntu → Windows: every 1 hour (batch uploads) | Medium |
| SYNC-07 | Priority queue: small files first (<100 MB), large files later | Medium |
| SYNC-08 | Large files (>1 GB): sync during off-peak hours (11 PM - 5 AM) | Medium |
| SYNC-09 | Bandwidth throttling to avoid network congestion | Medium |
| SYNC-10 | Conflict detection and resolution UI | High |
| SYNC-11 | Admin can manually trigger sync for specific files/folders | Medium |

### 1.7 Admin Dashboard

| ID | Requirement | Priority |
|----|-------------|----------|
| ADMIN-01 | View active users count (e.g., 8/15) | High |
| ADMIN-02 | View current uploads (file count, total size) | High |
| ADMIN-03 | View current downloads (file count, total size) | High |
| ADMIN-04 | Network usage visualization | Low |
| ADMIN-05 | Storage overview: active, deleted, available space | High |
| ADMIN-06 | Storage alerts when >80% full | High |
| ADMIN-07 | Suggest files for permanent deletion | Low |
| ADMIN-08 | View and manage sync status/conflicts | High |
| ADMIN-09 | Configure retention policy | Medium |
| ADMIN-10 | User management interface | High |
| ADMIN-11 | System health monitoring (CPU, RAM, disk I/O) | Medium |

### 1.8 Scheduler Management (Admin)

| ID | Requirement | Priority |
|----|-------------|----------|
| SCHED-01 | View all scheduled tasks (sync, cleanup, backups) | High |
| SCHED-02 | Enable/disable individual scheduled tasks | High |
| SCHED-03 | Modify schedule timing (cron expression or simple UI) | High |
| SCHED-04 | Trigger any scheduled task manually (Run Now) | High |
| SCHED-05 | View last run status and next scheduled run | High |
| SCHED-06 | View execution history per task | Medium |
| SCHED-07 | Set peak/off-peak hours for sync scheduling | Medium |
| SCHED-08 | Email notification on task failure | Medium |

**Scheduled Tasks to Manage:**

| Task | Default Schedule | Description |
|------|------------------|-------------|
| Windows → Ubuntu Sync | Every 30 min | Pull files from Windows server |
| Ubuntu → Windows Sync | Every 1 hour | Push user uploads to Windows |
| Deleted Files Cleanup | Daily at 2 AM | Permanently delete files past retention |
| Storage Check | Every 6 hours | Check storage and alert if >80% |
| Session Cleanup | Every 1 hour | Remove expired sessions |
| Audit Log Archival | Weekly (Sunday 3 AM) | Archive old logs |
| Database Backup | Daily at 1 AM | Backup PostgreSQL database |
| Temp Files Cleanup | Every 6 hours | Remove orphaned upload chunks |

### 1.9 Audit Logging

| ID | Requirement | Priority |
|----|-------------|----------|
| LOG-01 | Log every login/logout with IP address | High |
| LOG-02 | Log file uploads (filename, size, duration) | High |
| LOG-03 | Log file downloads (user, file, timestamp) | High |
| LOG-04 | Log soft delete actions (user, file, reason) | High |
| LOG-05 | Log restore actions | High |
| LOG-06 | Log failed login attempts | High |
| LOG-07 | Log sync operations (start, end, errors) | High |
| LOG-08 | Admin reports: most active users, most accessed files | Medium |
| LOG-09 | Daily/weekly activity summary | Medium |
| LOG-10 | Storage trends over time | Low |
| LOG-11 | Export logs as CSV with date range filter | Medium |
| LOG-12 | Search logs by user/action/date | Medium |
| LOG-13 | Log scheduler task executions | High |
| LOG-14 | Log admin configuration changes | High |

### 1.10 Notifications & Feedback

| ID | Requirement | Priority |
|----|-------------|----------|
| NOTIF-01 | Toast notifications for success/error actions | High |
| NOTIF-02 | Upload complete notification | High |
| NOTIF-03 | Download ready notification (for bulk zip) | High |
| NOTIF-04 | Sync conflict notification for admin | Medium |
| NOTIF-05 | Storage warning notification (>80% full) | High |
| NOTIF-06 | Optional: Email notifications for critical events | Low |

---

## 2. Non-Functional Requirements

### 2.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| PERF-01 | Support 15 concurrent users | Required |
| PERF-02 | Handle GB-sized file uploads/downloads | Required |
| PERF-03 | File list load time | < 2 seconds |
| PERF-04 | Search results | < 3 seconds |
| PERF-05 | Upload speed | Limited by network, not application |

### 2.2 Security

| ID | Requirement | Priority |
|----|-------------|----------|
| SEC-01 | HTTPS with SSL/TLS encryption | High |
| SEC-02 | Accessible only within local network | High |
| SEC-03 | VPN required for remote access | High |
| SEC-04 | Firewall: only ports 443 (HTTPS) and 22 (SSH) | High |
| SEC-05 | Optional: encrypt files at rest | Low |
| SEC-06 | Strong password enforcement | High |
| SEC-07 | Password change capability for users | High |
| SEC-08 | Force password change on first login | Medium |
| SEC-09 | Secure session token handling (HttpOnly, Secure flags) | High |

### 2.3 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| REL-01 | System uptime | 99% during business hours |
| REL-02 | Data integrity verification (checksums) | Required |
| REL-03 | Daily incremental backups | Required |
| REL-04 | Weekly full backups | Required |
| REL-05 | Resume capability for interrupted transfers | Required |
| REL-06 | Graceful error handling with user feedback | Required |

### 2.4 Usability

| ID | Requirement | Priority |
|----|-------------|----------|
| UX-01 | Responsive design (desktop, tablet, mobile) | High |
| UX-02 | Intuitive drag & drop interface | High |
| UX-03 | Clear progress indicators for long operations | High |
| UX-04 | Browser support: Chrome, Firefox, Edge | High |
| UX-05 | Keyboard shortcuts for common actions | Low |
| UX-06 | Loading states for all async operations | High |

---

## 3. Technical Requirements

### 3.1 Infrastructure

| Component | Specification |
|-----------|---------------|
| Server OS | Ubuntu Server (LTS) |
| CPU | 4-8 cores |
| RAM | 16-32 GB |
| Storage | 2-4 TB SSD |
| Network | Gigabit connection minimum |

### 3.2 Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | Python FastAPI | 0.109+ |
| Frontend | Vue.js 3 | Composition API |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy 2.0 | Async |
| Task Scheduler | APScheduler | In-process |
| File Sync | Rclone | External CLI |
| Web Server | Nginx | Reverse proxy |
| Chunked Upload | Uppy.js | Frontend |

### 3.3 Database Schema (Core Tables)

```
users
├── id (PK)
├── username (unique)
├── password_hash
├── email
├── role (admin/user)
├── is_active
├── failed_login_attempts
├── locked_until
├── must_change_password
├── created_at
└── updated_at

files
├── id (PK)
├── filename
├── filepath
├── size
├── checksum
├── mime_type
├── uploaded_by (FK → users)
├── upload_date
├── is_deleted
├── deleted_at
├── deleted_by (FK → users)
└── sync_status

sync_logs
├── id (PK)
├── sync_type (win_to_ubuntu / ubuntu_to_win)
├── started_at
├── completed_at
├── files_synced
├── bytes_transferred
├── status (success/failed/partial)
└── error_message

audit_logs
├── id (PK)
├── user_id (FK → users)
├── action (login/logout/upload/download/delete/restore/config_change)
├── target_file_id (FK → files)
├── ip_address
├── user_agent
├── details (JSON)
└── timestamp

sessions
├── id (PK)
├── user_id (FK → users)
├── token
├── ip_address
├── created_at
└── expires_at

scheduled_tasks
├── id (PK)
├── task_name (unique)
├── task_type (sync/cleanup/backup/storage_check)
├── cron_expression
├── is_enabled
├── last_run_at
├── last_run_status (success/failed/running)
├── next_run_at
├── created_at
└── updated_at

task_execution_history
├── id (PK)
├── task_id (FK → scheduled_tasks)
├── started_at
├── completed_at
├── status (success/failed/cancelled)
├── error_message
├── details (JSON)
└── triggered_by (system/manual/user_id)

upload_chunks
├── id (PK)
├── upload_id (unique identifier for the upload session)
├── chunk_number
├── chunk_size
├── checksum
├── uploaded_at
├── expires_at
└── file_path (temp location)

system_settings
├── id (PK)
├── key (unique)
├── value (JSON)
├── updated_by (FK → users)
└── updated_at
```

### 3.4 Database Indexes

```sql
CREATE INDEX idx_files_is_deleted ON files(is_deleted);
CREATE INDEX idx_files_uploaded_by ON files(uploaded_by);
CREATE INDEX idx_files_upload_date ON files(upload_date);
CREATE INDEX idx_files_filename ON files(filename);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_scheduled_tasks_next_run ON scheduled_tasks(next_run_at);
CREATE INDEX idx_task_history_task_id ON task_execution_history(task_id);
CREATE INDEX idx_upload_chunks_upload_id ON upload_chunks(upload_id);
```

### 3.5 File Storage Structure

```
/data/
├── active/              # Active files (is_deleted = false)
│   ├── 2024/
│   ├── 2025/
│   └── 2026/
├── deleted/             # Soft-deleted files (90-day retention)
│   ├── 2024/
│   ├── 2025/
│   └── 2026/
├── temp/                # Temporary upload chunks
│   └── {upload_id}/
├── backups/             # Database backups
│   ├── daily/
│   └── weekly/
└── logs/                # Archived audit logs
    └── {year}/
```

---

## 4. API Endpoints (Core)

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh session token
- `POST /api/auth/change-password` - Change own password

### Files
- `GET /api/files` - List files (paginated, with filters, sorting)
- `GET /api/files/{id}` - Get file metadata
- `GET /api/files/{id}/preview` - Get file preview (images, PDF, text)
- `POST /api/files/upload/init` - Initialize chunked upload
- `POST /api/files/upload/chunk` - Upload file chunk
- `POST /api/files/upload/complete` - Complete chunked upload
- `POST /api/files/upload/cancel` - Cancel ongoing upload
- `GET /api/files/{id}/download` - Download single file
- `POST /api/files/download/bulk` - Download multiple files as zip
- `DELETE /api/files/{id}` - Soft delete file
- `POST /api/files/{id}/restore` - Restore deleted file
- `PUT /api/files/{id}/rename` - Rename file
- `PUT /api/files/{id}/move` - Move file to another folder
- `GET /api/files/deleted` - List deleted files
- `GET /api/files/check-duplicate` - Check if filename exists

### Search
- `GET /api/search` - Search files by name, date, etc.

### Folders
- `GET /api/folders` - List folders
- `POST /api/folders` - Create folder
- `PUT /api/folders/{id}` - Rename folder
- `DELETE /api/folders/{id}` - Delete folder (if empty)

### Admin - Users
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/{id}` - Update user
- `DELETE /api/admin/users/{id}` - Delete user
- `POST /api/admin/users/{id}/unlock` - Unlock user account
- `POST /api/admin/users/{id}/reset-password` - Reset user password

### Admin - Dashboard
- `GET /api/admin/dashboard` - Dashboard stats
- `GET /api/admin/storage` - Storage overview
- `GET /api/admin/system-health` - System health metrics

### Admin - Sync
- `GET /api/admin/sync/status` - Sync status
- `POST /api/admin/sync/trigger` - Trigger manual sync
- `GET /api/admin/sync/conflicts` - List sync conflicts
- `POST /api/admin/sync/resolve` - Resolve sync conflict

### Admin - Scheduler
- `GET /api/admin/scheduler/tasks` - List all scheduled tasks
- `GET /api/admin/scheduler/tasks/{id}` - Get task details
- `PUT /api/admin/scheduler/tasks/{id}` - Update task schedule
- `POST /api/admin/scheduler/tasks/{id}/toggle` - Enable/disable task
- `POST /api/admin/scheduler/tasks/{id}/run` - Trigger task manually
- `GET /api/admin/scheduler/history` - View execution history

### Admin - Settings
- `GET /api/admin/settings` - Get system settings
- `PUT /api/admin/settings` - Update system settings

### Audit
- `GET /api/admin/audit` - Query audit logs
- `GET /api/admin/audit/export` - Export logs as CSV
- `GET /api/admin/audit/summary` - Activity summary report

---

## 5. Implementation Phases

### Phase 1: Core Functionality (4-6 weeks)
- [ ] Ubuntu server setup + PostgreSQL database
- [ ] User authentication system (login, logout, password change)
- [ ] File browser with pagination and sorting
- [ ] Chunked file upload (GB support) with resume
- [ ] Streaming file download
- [ ] User management (admin creates users)
- [ ] Soft delete + restore
- [ ] Basic audit logging
- [ ] Scheduler service with basic tasks
- [ ] Bidirectional sync (Windows ↔ Ubuntu)
- [ ] Nginx reverse proxy + SSL

### Phase 2: Enhanced Features (2-3 weeks)
- [ ] Advanced search and filters
- [ ] Bulk operations (multi-select)
- [ ] Admin dashboard (storage, activity, system health)
- [ ] Scheduler management UI
- [ ] Conflict resolution UI
- [ ] File preview (PDF, images, text)
- [ ] Duplicate file handling
- [ ] Export audit logs

### Phase 3: Polish & Optimization (1-2 weeks)
- [ ] Email notifications (optional)
- [ ] Performance optimization
- [ ] Mobile responsiveness refinement
- [ ] User documentation
- [ ] Admin documentation

---

## 6. Success Criteria

1. All 15 users can concurrently upload/download files without performance degradation
2. GB-sized files upload successfully with resume capability
3. Files sync reliably between Windows and Ubuntu servers
4. Deleted files are recoverable within 90-day retention period
5. Admin has full visibility into system activity and storage
6. All file operations are logged for audit purposes
7. System is accessible only within local network (secure)
8. Scheduled tasks run reliably and are manageable via UI
9. Users receive clear feedback for all actions (success/error)

---

## 7. Out of Scope (Future Considerations)

- Folder-level permissions per user/group
- File versioning
- Real-time collaboration/editing
- External user access (outside organization)
- Mobile native apps
- OCR/content search within files
- File comments/annotations
- Sharing files with expiring links (external)

---

# Internal File Sharing System - Copilot Instructions

## Project Overview
An internal file sharing web application for 15 users to upload, download, browse, and manage GB-sized files. Syncs bidirectionally with a remote Windows server.

## Tech Stack (STRICT - Do not deviate)

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | Python FastAPI | 0.109+ |
| Frontend | Vue.js 3 | Composition API |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy 2.0 | Async |
| Task Scheduler | APScheduler | In-process |
| File Sync | Rclone | External CLI |
| Web Server | Nginx | Reverse proxy |
| Chunked Upload | Uppy.js | Frontend |

## NOT Using (Do not suggest)
- ❌ Celery
- ❌ Redis  
- ❌ Bull
- ❌ React
- ❌ Node.js/Express for backend
- ❌ Django
- ❌ MongoDB

## Project Structure

```
internal-file-sharing/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings/environment
│   │   ├── database.py          # DB connection
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── file.py
│   │   │   ├── audit.py
│   │   │   ├── session.py
│   │   │   ├── scheduler.py
│   │   │   └── sync.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── file.py
│   │   │   ├── auth.py
│   │   │   └── scheduler.py
│   │   ├── routers/             # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── files.py
│   │   │   ├── folders.py
│   │   │   ├── admin.py
│   │   │   ├── scheduler.py
│   │   │   └── search.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── file_service.py
│   │   │   ├── sync_service.py
│   │   │   ├── scheduler_service.py
│   │   │   └── audit_service.py
│   │   ├── utils/               # Helpers
│   │   │   ├── __init__.py
│   │   │   ├── security.py      # Password hashing, tokens
│   │   │   ├── file_utils.py    # Checksum, chunking
│   │   │   └── validators.py
│   │   └── scheduler/           # APScheduler tasks
│   │       ├── __init__.py
│   │       ├── jobs.py          # Task definitions
│   │       └── manager.py       # Scheduler management
│   ├── alembic/                 # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   ├── stores/              # Pinia stores
│   │   ├── components/
│   │   ├── views/
│   │   ├── composables/         # Vue composables
│   │   ├── services/            # API calls
│   │   └── utils/
│   ├── package.json
│   └── vite.config.js
├── data/                        # File storage (gitignored)
│   ├── active/
│   ├── deleted/
│   ├── temp/
│   ├── backups/
│   └── logs/
├── nginx/
│   └── nginx.conf
├── scripts/                     # Deployment scripts
├── .env.example
├── docker-compose.yml
└── REQUIREMENTS.md
```

## Database Tables

### users
- id (UUID, PK)
- username (unique, varchar 50)
- password_hash (varchar 255)
- email (varchar 100)
- role (enum: admin/user)
- is_active (boolean, default true)
- failed_login_attempts (int, default 0)
- locked_until (timestamp, nullable)
- must_change_password (boolean, default true)
- created_at (timestamp)
- updated_at (timestamp)

### files
- id (UUID, PK)
- filename (varchar 255)
- filepath (varchar 500)
- size (bigint)
- checksum (varchar 64, SHA-256)
- mime_type (varchar 100)
- uploaded_by (FK → users)
- upload_date (timestamp)
- is_deleted (boolean, default false)
- deleted_at (timestamp, nullable)
- deleted_by (FK → users, nullable)
- sync_status (enum: pending/synced/conflict/error)

### sessions
- id (UUID, PK)
- user_id (FK → users)
- token (varchar 255, unique)
- ip_address (varchar 45)
- user_agent (text)
- created_at (timestamp)
- expires_at (timestamp)

### audit_logs
- id (UUID, PK)
- user_id (FK → users, nullable)
- action (varchar 50)
- target_file_id (FK → files, nullable)
- ip_address (varchar 45)
- user_agent (text)
- details (JSONB)
- timestamp (timestamp)

### scheduled_tasks
- id (UUID, PK)
- task_name (unique, varchar 100)
- task_type (varchar 50)
- cron_expression (varchar 50)
- is_enabled (boolean, default true)
- last_run_at (timestamp, nullable)
- last_run_status (enum: success/failed/running, nullable)
- next_run_at (timestamp, nullable)
- created_at (timestamp)
- updated_at (timestamp)

### task_execution_history
- id (UUID, PK)
- task_id (FK → scheduled_tasks)
- started_at (timestamp)
- completed_at (timestamp, nullable)
- status (enum: success/failed/cancelled/running)
- error_message (text, nullable)
- details (JSONB)
- triggered_by (varchar 50)

### sync_logs
- id (UUID, PK)
- sync_type (enum: win_to_ubuntu/ubuntu_to_win)
- started_at (timestamp)
- completed_at (timestamp, nullable)
- files_synced (int)
- bytes_transferred (bigint)
- status (enum: success/failed/partial/running)
- error_message (text, nullable)

### upload_chunks
- id (UUID, PK)
- upload_id (UUID, indexed)
- filename (varchar 255)
- total_chunks (int)
- chunk_number (int)
- chunk_size (bigint)
- checksum (varchar 64)
- uploaded_at (timestamp)
- expires_at (timestamp)
- file_path (varchar 500)

### system_settings
- id (UUID, PK)
- key (unique, varchar 100)
- value (JSONB)
- updated_by (FK → users)
- updated_at (timestamp)

## API Conventions

### Base URL
`/api/v1/`

### Authentication
- Bearer token in Authorization header
- Token stored in sessions table
- 30-minute expiry, refresh before expiry

### Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "errors": []
}
```

### Error Response
```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "errors": [
    { "field": "username", "message": "Required" }
  ]
}
```

### Pagination
```json
{
  "items": [...],
  "total": 234,
  "page": 1,
  "page_size": 100,
  "total_pages": 3
}
```

## Code Style Guidelines

### Python (Backend)
- Use type hints for all functions
- Async/await for all DB operations
- Pydantic for request/response validation
- Use dependency injection for services
- Prefix private methods with underscore
- Use logging, not print statements

### Vue.js (Frontend)
- Composition API with `<script setup>`
- Pinia for state management
- Use TypeScript for type safety (optional but preferred)
- Components in PascalCase
- Composables prefixed with `use`
- API calls in `/services/` directory

## File Upload Flow
1. Client calls `POST /api/v1/files/upload/init` with filename, size
2. Server returns `upload_id` and chunk size
3. Client uploads chunks to `POST /api/v1/files/upload/chunk`
4. Client calls `POST /api/v1/files/upload/complete`
5. Server assembles chunks, verifies checksum, moves to active storage

## Scheduler (APScheduler)
- Runs in-process with FastAPI
- Jobs stored in database (scheduled_tasks table)
- Use `AsyncIOScheduler`
- Jobs defined in `backend/app/scheduler/jobs.py`

## Security Requirements
- Passwords: bcrypt with 12 rounds
- Session tokens: 32-byte random + base64
- All endpoints require authentication except login
- Admin endpoints check user.role == 'admin'
- CORS: only allow frontend origin
- Rate limiting: 100 requests/minute per IP

## File Storage
- Active files: `/data/active/{year}/{month}/{filename}`
- Deleted files: `/data/deleted/{year}/{month}/{filename}`
- Upload chunks: `/data/temp/{upload_id}/{chunk_number}`
- Store original filename in DB, use UUID on disk

## Common Pitfalls to Avoid
1. Don't use synchronous DB calls
2. Don't store passwords in plain text
3. Don't return password_hash in API responses
4. Don't allow path traversal in file operations
5. Don't skip checksum verification
6. Don't hardcode secrets - use environment variables
7. Don't create files outside /data directory