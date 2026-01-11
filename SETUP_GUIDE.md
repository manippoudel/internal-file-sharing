# 🚀 Complete Setup Guide - Internal File Sharing System

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Manual Setup](#manual-setup)
4. [Initial Configuration](#initial-configuration)
5. [Creating Admin User](#creating-admin-user)
6. [Testing the Application](#testing-the-application)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker** 20.10+ and **Docker Compose** 2.0+ (recommended)
- **Python** 3.11+ (for manual setup)
- **Node.js** 20+ and **npm** 9+ (for manual setup)
- **PostgreSQL** 15+ (for manual setup)
- **Git** 2.30+

### System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Disk Space**: Minimum 20GB (for file storage)
- **CPU**: 2+ cores recommended
- **OS**: Linux (Ubuntu 22.04+), macOS, or Windows with WSL2

---

## Quick Start (Docker)

### Step 1: Clone Repository

```bash
git clone https://github.com/manippoudel/internal-file-sharing.git
cd internal-file-sharing
```

### Step 2: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**⚠️ IMPORTANT: Change these in production:**

```bash
# Change this to a secure random key (32+ characters)
SECRET_KEY=your-very-secure-secret-key-here-change-this

# Update database credentials
DATABASE_URL=postgresql+asyncpg://fileuser:securepassword@postgres:5432/filedb
```

### Step 3: Create Required Directories

```bash
# Create data directories
mkdir -p data/active data/deleted data/temp data/backups data/logs

# Set permissions (Linux/Mac)
chmod -R 755 data/
```

### Step 4: Start Services with Docker Compose

```bash
# Start all services (PostgreSQL, Backend, Frontend)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Run Database Migrations

```bash
# Wait for PostgreSQL to be ready (about 10 seconds)
sleep 10

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Step 6: Create Initial Admin User

```bash
# Access backend container
docker-compose exec backend python -c "
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password
from datetime import datetime

db = SessionLocal()

# Create admin user
admin = User(
    username='admin',
    email='admin@example.com',
    password_hash=hash_password('Admin@12345'),
    is_admin=True,
    is_active=True,
    created_at=datetime.utcnow()
)

db.add(admin)
db.commit()
print('✅ Admin user created successfully!')
print('Username: admin')
print('Password: Admin@12345')
print('⚠️  Please change the password after first login!')
db.close()
"
```

### Step 7: Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**Default Login:**
- Username: `admin`
- Password: `Admin@12345`

---

## Manual Setup

### Backend Setup

#### 1. Set Up Python Environment

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

#### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Set Up PostgreSQL Database

```bash
# Install PostgreSQL 15+
sudo apt-get install postgresql-15  # Ubuntu/Debian
# OR
brew install postgresql@15          # macOS

# Start PostgreSQL service
sudo systemctl start postgresql     # Linux
# OR
brew services start postgresql@15   # macOS

# Create database and user
sudo -u postgres psql
```

In PostgreSQL console:

```sql
CREATE DATABASE filedb;
CREATE USER fileuser WITH PASSWORD 'filepassword';
GRANT ALL PRIVILEGES ON DATABASE filedb TO fileuser;
\q
```

#### 4. Configure Environment

```bash
# Copy environment file
cp ../.env.example ../.env

# Edit database URL
# DATABASE_URL=postgresql+asyncpg://fileuser:filepassword@localhost:5432/filedb
```

#### 5. Run Migrations

```bash
# From backend directory
alembic upgrade head
```

#### 6. Create Admin User

```bash
python -c "
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password
from datetime import datetime

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@example.com',
    password_hash=hash_password('Admin@12345'),
    is_admin=True,
    is_active=True,
    created_at=datetime.utcnow()
)
db.add(admin)
db.commit()
print('Admin user created!')
db.close()
"
```

#### 7. Start Backend Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Configure API Endpoint (if needed)

Edit `vite.config.js` if backend is not on localhost:8000:

```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://your-backend-host:8000',
        changeOrigin: true,
      },
    },
  },
})
```

#### 3. Start Development Server

```bash
# Development mode
npm run dev

# Production build
npm run build
npm run preview
```

---

## Initial Configuration

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Secret key for session tokens | - | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection string | - | ✅ Yes |
| `STORAGE_PATH` | Base path for file storage | `/data` | ✅ Yes |
| `MAX_UPLOAD_SIZE` | Max file size in bytes | 10737418240 (10GB) | No |
| `CHUNK_SIZE` | Upload chunk size in bytes | 52428800 (50MB) | No |
| `SESSION_EXPIRE_MINUTES` | Session expiry time | 30 | No |
| `MAX_LOGIN_ATTEMPTS` | Failed login limit | 5 | No |
| `ACCOUNT_LOCKOUT_MINUTES` | Lockout duration | 30 | No |
| `DELETED_FILES_RETENTION_DAYS` | Soft delete retention | 90 | No |
| `SCHEDULER_ENABLED` | Enable background jobs | True | No |
| `SYNC_ENABLED` | Enable Rclone sync | True | No |
| `DEBUG` | Debug mode | False | No |

### Storage Directory Structure

```
data/
├── active/          # Active user files
├── deleted/         # Soft-deleted files (90-day retention)
├── temp/           # Temporary upload chunks
├── backups/        # Database backups
└── logs/           # Application logs
```

---

## Creating Admin User

### Method 1: Using Python Script (Recommended)

Create a file `create_admin.py` in the backend directory:

```python
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password
from datetime import datetime

def create_admin(username, email, password):
    db = SessionLocal()
    
    # Check if user exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"❌ User '{username}' already exists!")
        return
    
    # Create admin user
    admin = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_admin=True,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(admin)
    db.commit()
    
    print(f"✅ Admin user '{username}' created successfully!")
    print(f"Email: {email}")
    print(f"⚠️  Please change the password after first login!")
    
    db.close()

if __name__ == "__main__":
    create_admin("admin", "admin@example.com", "Admin@12345")
```

Run it:

```bash
cd backend
python create_admin.py
```

### Method 2: Using API (After First Admin Exists)

Once you have one admin user, you can create more users via the Admin UI or API:

```bash
curl -X POST "http://localhost:8000/api/v1/admin/users" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newadmin",
    "email": "newadmin@example.com",
    "password": "SecurePassword@123",
    "is_admin": true
  }'
```

---

## Testing the Application

### 1. Backend API Tests

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response: {"status":"healthy"}
```

```bash
# Test login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@12345"
  }'

# Expected: Returns session token
```

### 2. Frontend Access

1. Open browser: http://localhost:5173
2. Login with admin credentials
3. Test features:
   - ✅ File upload (try a small file first)
   - ✅ File download
   - ✅ File browser (search, sort, pagination)
   - ✅ Admin dashboard (if admin user)
   - ✅ User management (create test user)
   - ✅ Scheduler management
   - ✅ Audit logs

### 3. Automated Test Checklist

**Authentication:**
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (should fail)
- [ ] Account lockout after 5 failed attempts
- [ ] Password change functionality
- [ ] Logout

**File Operations:**
- [ ] Upload small file (< 50MB)
- [ ] Upload large file (> 50MB, tests chunking)
- [ ] Download file
- [ ] Bulk download (multiple files)
- [ ] Rename file
- [ ] Delete file (soft delete)
- [ ] Restore deleted file
- [ ] Search files
- [ ] Sort files (by name, size, date)

**Admin Features:**
- [ ] View dashboard statistics
- [ ] Create new user
- [ ] Edit user
- [ ] Delete user
- [ ] Unlock locked account
- [ ] Reset user password
- [ ] View system health metrics
- [ ] View storage monitoring

**Scheduler:**
- [ ] View scheduled tasks
- [ ] Pause task
- [ ] Resume task
- [ ] Manually trigger task

**Audit Logs:**
- [ ] View audit logs
- [ ] Filter logs by user
- [ ] Filter logs by action
- [ ] Filter logs by date range
- [ ] Export logs to CSV

---

## Production Deployment

### 1. Security Hardening

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env with the generated key
SECRET_KEY=REPLACE_WITH_THE_GENERATED_KEY_ABOVE
DEBUG=False
```

### 2. Set Up Rclone (For Windows Sync)

```bash
# Install Rclone
curl https://rclone.org/install.sh | sudo bash

# Configure Rclone
rclone config

# Follow prompts to set up Windows server remote
# Name it: windows-remote

# Test connection
rclone ls windows-remote:

# Update .env
SYNC_ENABLED=True
WINDOWS_SERVER_PATH=windows-remote:/path/to/files
```

### 3. Set Up Nginx Reverse Proxy

Create `/etc/nginx/sites-available/fileshare`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10G;
    
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for large uploads
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/fileshare /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Set Up SSL/TLS with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 5. Set Up Systemd Services

Create `/etc/systemd/system/fileshare-backend.service`:

```ini
[Unit]
Description=File Share Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/internal-file-sharing/backend
Environment="PATH=/opt/internal-file-sharing/backend/venv/bin"
ExecStart=/opt/internal-file-sharing/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/fileshare-frontend.service`:

```ini
[Unit]
Description=File Share Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/internal-file-sharing/frontend
ExecStart=/usr/bin/npm run preview -- --host 0.0.0.0 --port 5173
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fileshare-backend fileshare-frontend
sudo systemctl start fileshare-backend fileshare-frontend
```

### 6. Set Up Database Backups

The system includes automated daily backups (1 AM). Configure backup retention:

```bash
# Add to cron for backup cleanup (keep 30 days)
0 2 * * * find /data/backups -name "*.sql" -mtime +30 -delete
```

---

## Troubleshooting

### Issue: Database Connection Fails

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -h localhost -U fileuser -d filedb

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### Issue: File Upload Fails

```bash
# Check storage directory permissions
ls -la data/

# Fix permissions
chmod -R 755 data/
chown -R www-data:www-data data/  # Linux production

# Check disk space
df -h
```

### Issue: Frontend Can't Connect to Backend

```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS settings in .env
cat .env | grep CORS_ORIGINS

# Verify Vite proxy configuration
cat frontend/vite.config.js
```

### Issue: Scheduler Not Running

```bash
# Check SCHEDULER_ENABLED in .env
cat .env | grep SCHEDULER_ENABLED

# View scheduler logs
docker-compose logs backend | grep -i scheduler

# Manually trigger a task via API
curl -X POST "http://localhost:8000/api/v1/scheduler/tasks/session_cleanup/trigger" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Issue: Admin Can't Access Admin Panel

```bash
# Verify user is admin in database
docker-compose exec backend python -c "
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
user = db.query(User).filter(User.username == 'admin').first()
print(f'Username: {user.username}')
print(f'Is Admin: {user.is_admin}')
print(f'Is Active: {user.is_active}')
db.close()
"
```

### Issue: Account Locked Out

```bash
# Unlock account manually
docker-compose exec backend python -c "
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
user = db.query(User).filter(User.username == 'admin').first()
user.failed_login_attempts = 0
user.locked_until = None
db.commit()
print('Account unlocked!')
db.close()
"
```

---

## 🎉 You're Ready!

If you've completed all steps successfully:

✅ **Backend** is running on port 8000
✅ **Frontend** is running on port 5173
✅ **Database** is initialized with tables
✅ **Admin user** is created
✅ **File storage** directories are set up
✅ **Scheduler** is running background jobs

**Next Steps:**

1. Login to the frontend
2. Change the default admin password
3. Create additional users
4. Test file upload/download
5. Review admin dashboard
6. Configure Rclone for Windows sync (if needed)

**Need Help?**

- Check logs: `docker-compose logs -f`
- API documentation: http://localhost:8000/docs
- Review SECURITY.md for security best practices

---

## 📞 Support

For issues or questions:

- Check the troubleshooting section above
- Review API documentation at `/docs`
- Check application logs in `data/logs/`
- Review Docker logs: `docker-compose logs`

---

**Last Updated**: 2024-01-10
**Version**: 1.0.0
