# ✅ Deployment Checklist - Internal File Sharing System

Use this checklist to ensure proper deployment of the system.

## Pre-Deployment

### 1. Environment Setup
- [ ] `.env` file created from `.env.example`
- [ ] `SECRET_KEY` changed to a secure random value (32+ characters)
- [ ] Database credentials updated (not default values)
- [ ] `DEBUG=False` for production
- [ ] CORS origins configured for production domain
- [ ] All storage paths configured correctly

### 2. Infrastructure
- [ ] Docker and Docker Compose installed
- [ ] Minimum system requirements met (4GB RAM, 20GB disk)
- [ ] Network ports available (5173, 8000, 5432)
- [ ] SSL/TLS certificates obtained (if using HTTPS)
- [ ] Nginx installed and configured (production)

### 3. Storage
- [ ] Storage directories created (`data/{active,deleted,temp,backups,logs}`)
- [ ] Proper permissions set on storage directories
- [ ] Sufficient disk space available (20GB minimum)
- [ ] Backup location configured

## Deployment Steps

### 4. Initial Setup
- [ ] Repository cloned
- [ ] Environment variables configured
- [ ] Storage directories created
- [ ] Docker images built (`docker-compose build`)
- [ ] Services started (`docker-compose up -d`)
- [ ] PostgreSQL is healthy (`docker-compose ps`)

### 5. Database Setup
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Initial admin user created
- [ ] Database connection verified
- [ ] Backup directory accessible

### 6. Application Verification
- [ ] Backend health check passes (`curl http://localhost:8000/health`)
- [ ] Frontend accessible (http://localhost:5173)
- [ ] API documentation accessible (http://localhost:8000/docs)
- [ ] Admin login successful
- [ ] File upload/download works

### 7. Security Hardening
- [ ] Default admin password changed
- [ ] Additional admin users created (if needed)
- [ ] SSL/TLS configured (production)
- [ ] Firewall rules configured
- [ ] Rate limiting enabled
- [ ] Security headers configured in Nginx

## Post-Deployment

### 8. Monitoring Setup
- [ ] Application logs accessible (`docker-compose logs`)
- [ ] Error logging configured
- [ ] System health metrics monitored
- [ ] Storage alerts configured (>80%)
- [ ] Backup verification scheduled

### 9. Scheduler Configuration
- [ ] All 8 scheduled tasks visible in admin panel
- [ ] Session cleanup running (verify hourly)
- [ ] Temp files cleanup running (verify 6-hour)
- [ ] Database backup running (verify daily)
- [ ] Rclone sync configured (if enabled)

### 10. Rclone Sync (Optional)
- [ ] Rclone installed
- [ ] Windows server remote configured
- [ ] Connection to Windows server verified
- [ ] Sync paths configured in `.env`
- [ ] Initial sync tested
- [ ] Sync tasks enabled in scheduler

### 11. Testing
- [ ] Admin login tested
- [ ] User creation tested
- [ ] File upload tested (small file)
- [ ] File upload tested (large file > 100MB)
- [ ] File download tested
- [ ] Bulk download tested
- [ ] File operations tested (rename, delete, restore)
- [ ] Search functionality tested
- [ ] Admin dashboard accessible
- [ ] User management tested
- [ ] Scheduler management tested
- [ ] Audit logs accessible
- [ ] CSV export tested

### 12. User Onboarding
- [ ] User accounts created
- [ ] User credentials shared securely
- [ ] User documentation provided
- [ ] Training session scheduled (if needed)
- [ ] Support contact information shared

## Production Checklist

### 13. Production Hardening
- [ ] Systemd services configured
- [ ] Services set to auto-start on boot
- [ ] Nginx reverse proxy configured
- [ ] SSL/TLS certificate installed
- [ ] Domain name configured
- [ ] HTTPS redirect enabled
- [ ] HTTP security headers configured
- [ ] Log rotation configured

### 14. Backup & Recovery
- [ ] Database backup tested
- [ ] Backup restoration tested
- [ ] Backup retention policy defined
- [ ] Off-site backup configured
- [ ] Disaster recovery plan documented

### 15. Final Verification
- [ ] All features tested in production environment
- [ ] Performance tested with multiple users
- [ ] Mobile access verified
- [ ] Browser compatibility tested
- [ ] Error handling verified
- [ ] Session timeout verified
- [ ] Account lockout verified

## Maintenance

### 16. Ongoing Tasks
- [ ] Regular security updates scheduled
- [ ] Database backups verified weekly
- [ ] Log files reviewed weekly
- [ ] Storage usage monitored
- [ ] User access reviewed monthly
- [ ] Audit logs reviewed monthly

---

## Quick Reference

### Useful Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart backend
docker-compose restart backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Create backup manually
docker-compose exec postgres pg_dump -U fileuser filedb > backup.sql

# Check service status
docker-compose ps

# Access PostgreSQL
docker-compose exec postgres psql -U fileuser -d filedb
```

### Service URLs

- **Frontend**: http://localhost:5173 (dev) or https://your-domain.com (prod)
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

### Default Credentials

- **Username**: admin
- **Password**: Admin@12345 (⚠️ CHANGE IMMEDIATELY)

---

## Troubleshooting

If any step fails, refer to:
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Troubleshooting section
- `docker-compose logs -f` - View real-time logs
- [SECURITY.md](SECURITY.md) - Security guidelines

---

**Date Deployed**: _______________
**Deployed By**: _______________
**Production URL**: _______________
**Notes**: _______________________________________________

---

✅ **Deployment Complete!**

Once all items are checked, the system is ready for production use.
