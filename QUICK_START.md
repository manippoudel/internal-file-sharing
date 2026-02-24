# Quick Start Guide
## Internal File Sharing System

Get the application running in under 5 minutes!

---

## 🚀 Fastest Method (Docker - Recommended)

**Prerequisites**: Docker and Docker Compose installed

```bash
# 1. Clone and navigate to project
cd internal-file-sharing

# 2. Run the startup script
./start-docker.sh

# 3. Wait for services to start (~30 seconds)

# 4. Create admin user (first time only)
docker-compose exec backend python -m app.scripts.create_admin

# 5. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

That's it! 🎉

---

## 📋 Alternative Methods

### Method 1: Interactive Menu (Easiest)

```bash
./start.sh
```

This presents a menu where you can choose:
1. Docker mode (recommended)
2. Development mode (local backend/frontend)
3. Stop all services

### Method 2: Development Mode (For Development)

Good for debugging and development with hot reload:

```bash
./start-dev.sh
```

This runs:
- Database in Docker
- Backend locally (Python virtual environment)
- Frontend locally (Node.js)

**Prerequisites**:
- Docker installed
- Python 3.11+
- Node.js 18+

### Method 3: Manual Docker Compose

```bash
# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🛑 Stopping the Application

### Docker Mode

```bash
docker-compose down
```

### Development Mode

```bash
./stop-dev.sh
```

### Stop Everything

```bash
./stop-dev.sh
docker-compose down
```

---

## 🔧 First-Time Setup

### 1. Environment Configuration (Optional)

The application works with defaults, but you can customize:

```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit configuration (optional)
nano backend/.env
```

### 2. Create Admin User (Required)

After starting the application, create an admin user:

**Docker mode**:
```bash
docker-compose exec backend python -m app.scripts.create_admin
```

**Development mode**:
```bash
cd backend
source venv/bin/activate
python -m app.scripts.create_admin
```

Follow the prompts to set username, email, and password.

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (credentials in .env)

---

## 📊 Checking Status

### Docker Mode

```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs -f

# Check specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Development Mode

```bash
# Check backend log
tail -f logs/backend.log

# Check frontend log
tail -f logs/frontend.log

# Check database
docker-compose logs -f postgres
```

---

## 🐛 Troubleshooting

### Port Already in Use

**Error**: Port 8000, 5173, or 5432 already in use

**Solution**:
```bash
# Find and kill process using the port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
lsof -ti:5432 | xargs kill -9  # Database
```

### Docker Issues

**Problem**: Docker containers won't start

**Solution**:
```bash
# Reset everything
docker-compose down -v
docker-compose up -d --build
```

### Database Connection Failed

**Problem**: Backend can't connect to database

**Solution**:
```bash
# Check database is running
docker ps | grep postgres

# Restart database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

### Permission Denied on Scripts

**Problem**: Cannot execute ./start.sh

**Solution**:
```bash
chmod +x start.sh start-dev.sh start-docker.sh stop-dev.sh
```

### Frontend 404 Errors

**Problem**: Frontend shows 404 for API calls

**Solution**:
- Ensure backend is running on port 8000
- Check `frontend/vite.config.js` proxy configuration
- Verify no CORS errors in browser console

---

## 🔄 Common Commands

### Development Workflow

```bash
# Start everything
./start-docker.sh

# Make code changes (auto-reload enabled)

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# Stop everything
docker-compose down
```

### Database Operations

```bash
# Access database shell
docker-compose exec postgres psql -U fileuser -d filedb

# Run migrations
docker-compose exec backend alembic upgrade head

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Backup database
docker-compose exec postgres pg_dump -U fileuser filedb > backup.sql

# Restore database
docker-compose exec -T postgres psql -U fileuser -d filedb < backup.sql
```

### Testing

```bash
# Start test database
docker-compose --profile test up -d test-db

# Run backend tests
cd backend
pytest --cov=app

# Run frontend tests
cd frontend
npm run test
```

---

## 📁 Project Structure

```
internal-file-sharing/
├── backend/          # FastAPI backend
├── frontend/         # Vue.js frontend
├── data/            # File storage
├── logs/            # Application logs
├── tests/           # Test files
├── start.sh         # Interactive startup menu
├── start-dev.sh     # Development mode startup
├── start-docker.sh  # Docker mode startup
├── stop-dev.sh      # Stop development services
└── docker-compose.yml
```

---

## 🎯 Next Steps

After getting the application running:

1. ✅ **Create admin user** (see First-Time Setup above)
2. ✅ **Login** at http://localhost:5173
3. ✅ **Create regular users** via Admin Dashboard
4. ✅ **Upload test files** to verify functionality
5. ✅ **Review** [TESTING.md](TESTING.md) for running tests
6. ✅ **Check** [README.md](README.md) for full documentation

---

## 💡 Tips

### For Development

- Use **Development Mode** (`./start-dev.sh`) for hot reload
- Backend auto-reloads on Python file changes
- Frontend auto-reloads on Vue file changes
- Keep logs open: `tail -f logs/*.log`

### For Production

- Use **Docker Mode** for consistent environment
- Configure `.env` with production settings
- Set up proper SSL/TLS (see SETUP_GUIDE.md)
- Enable scheduled backups
- Monitor disk space for file storage

### For Testing

- Use separate test database: `docker-compose --profile test up test-db`
- Run tests before deploying: `pytest` and `npm run test`
- Check coverage: `pytest --cov=app --cov-report=html`

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs** - Most issues are visible in logs
2. **Review** [TESTING.md](TESTING.md) - Troubleshooting section
3. **Check** [README.md](README.md) - Full documentation
4. **Restart** - Sometimes a restart fixes issues
5. **Reset** - `docker-compose down -v` for clean slate

---

## 🎉 Success Checklist

- [ ] Application starts without errors
- [ ] Can access frontend at http://localhost:5173
- [ ] Can access API docs at http://localhost:8000/docs
- [ ] Admin user created successfully
- [ ] Can login with admin credentials
- [ ] Can upload a test file
- [ ] Can download the uploaded file
- [ ] Dashboard shows statistics

If all checked, you're ready to go! 🚀

---

**Quick Reference**:
- Start: `./start.sh` or `./start-docker.sh`
- Stop: `docker-compose down` or `./stop-dev.sh`
- Logs: `docker-compose logs -f`
- Admin: `docker-compose exec backend python -m app.scripts.create_admin`
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
