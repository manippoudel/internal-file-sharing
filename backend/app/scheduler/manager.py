"""APScheduler manager"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional

from app.config import settings
from app.scheduler import jobs

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Manager for APScheduler"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._initialized = False
    
    def init_scheduler(self):
        """Initialize the scheduler with all jobs"""
        if self._initialized:
            logger.warning("Scheduler already initialized")
            return
        
        if not settings.SCHEDULER_ENABLED:
            logger.info("Scheduler is disabled in settings")
            return
        
        logger.info("Initializing APScheduler")
        
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        
        # Add all scheduled jobs
        
        # Session cleanup - every hour
        self.scheduler.add_job(
            jobs.cleanup_expired_sessions,
            trigger=IntervalTrigger(hours=1),
            id="session_cleanup",
            name="Session Cleanup",
            replace_existing=True
        )
        
        # Expired chunks cleanup - every 6 hours
        self.scheduler.add_job(
            jobs.cleanup_expired_chunks,
            trigger=IntervalTrigger(hours=6),
            id="chunks_cleanup",
            name="Temp Files Cleanup",
            replace_existing=True
        )
        
        # Deleted files cleanup - daily at 2 AM
        self.scheduler.add_job(
            jobs.cleanup_deleted_files,
            trigger=CronTrigger(hour=2, minute=0),
            id="deleted_files_cleanup",
            name="Deleted Files Cleanup",
            replace_existing=True
        )
        
        # Storage check - every 6 hours
        self.scheduler.add_job(
            jobs.check_storage,
            trigger=IntervalTrigger(hours=6),
            id="storage_check",
            name="Storage Check",
            replace_existing=True
        )
        
        # Windows → Ubuntu sync - every 30 minutes (can be adjusted based on peak/off-peak)
        self.scheduler.add_job(
            jobs.sync_windows_to_ubuntu,
            trigger=IntervalTrigger(minutes=30),
            id="sync_win_to_ubuntu",
            name="Windows → Ubuntu Sync",
            replace_existing=True
        )
        
        # Ubuntu → Windows sync - every hour
        self.scheduler.add_job(
            jobs.sync_ubuntu_to_windows,
            trigger=IntervalTrigger(hours=1),
            id="sync_ubuntu_to_win",
            name="Ubuntu → Windows Sync",
            replace_existing=True
        )
        
        # Database backup - daily at 1 AM
        self.scheduler.add_job(
            jobs.backup_database,
            trigger=CronTrigger(hour=1, minute=0),
            id="database_backup",
            name="Database Backup",
            replace_existing=True
        )
        
        # Audit log archival - weekly on Sunday at 3 AM
        self.scheduler.add_job(
            jobs.archive_audit_logs,
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
            id="audit_log_archival",
            name="Audit Log Archival",
            replace_existing=True
        )
        
        logger.info("APScheduler initialized with 8 jobs")
        self._initialized = True
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler:
            logger.warning("Scheduler not initialized")
            return
        
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("APScheduler shut down")
    
    def get_jobs(self):
        """Get all scheduled jobs"""
        if not self.scheduler:
            return []
        return self.scheduler.get_jobs()
    
    def get_job(self, job_id: str):
        """Get a specific job"""
        if not self.scheduler:
            return None
        return self.scheduler.get_job(job_id)
    
    def pause_job(self, job_id: str):
        """Pause a job"""
        if not self.scheduler:
            return False
        try:
            self.scheduler.pause_job(job_id)
            return True
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str):
        """Resume a job"""
        if not self.scheduler:
            return False
        try:
            self.scheduler.resume_job(job_id)
            return True
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False
    
    def trigger_job(self, job_id: str):
        """Manually trigger a job"""
        if not self.scheduler:
            return False
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                return True
            return False
        except Exception as e:
            logger.error(f"Error triggering job {job_id}: {e}")
            return False


# Global scheduler instance
scheduler_manager = SchedulerManager()
