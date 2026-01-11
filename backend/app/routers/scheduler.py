"""Scheduler management router"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from app.routers.dependencies import get_current_admin_user
from app.models.user import User
from app.scheduler.manager import scheduler_manager

router = APIRouter()


@router.get("/tasks")
async def list_tasks(
    current_user: User = Depends(get_current_admin_user)
):
    """List all scheduled tasks (admin only)"""
    jobs = scheduler_manager.get_jobs()
    
    tasks = []
    for job in jobs:
        next_run = job.next_run_time.isoformat() if job.next_run_time else None
        
        tasks.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run,
            "trigger": str(job.trigger),
            "pending": job.pending
        })
    
    return {
        "tasks": tasks,
        "total": len(tasks)
    }


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Get details of a specific task (admin only)"""
    job = scheduler_manager.get_job(task_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return {
        "id": job.id,
        "name": job.name,
        "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        "trigger": str(job.trigger),
        "pending": job.pending,
        "func": job.func.__name__ if hasattr(job.func, '__name__') else str(job.func)
    }


@router.post("/tasks/{task_id}/pause")
async def pause_task(
    task_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Pause a scheduled task (admin only)"""
    success = scheduler_manager.pause_job(task_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to pause task"
        )
    
    return {
        "success": True,
        "message": f"Task '{task_id}' paused"
    }


@router.post("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Resume a paused task (admin only)"""
    success = scheduler_manager.resume_job(task_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to resume task"
        )
    
    return {
        "success": True,
        "message": f"Task '{task_id}' resumed"
    }


@router.post("/tasks/{task_id}/trigger")
async def trigger_task(
    task_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Manually trigger a task to run now (admin only)"""
    success = scheduler_manager.trigger_job(task_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to trigger task"
        )
    
    return {
        "success": True,
        "message": f"Task '{task_id}' triggered"
    }


@router.get("/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_admin_user)
):
    """Get scheduler status (admin only)"""
    if not scheduler_manager.scheduler:
        return {
            "running": False,
            "jobs_count": 0
        }
    
    return {
        "running": scheduler_manager.scheduler.running,
        "jobs_count": len(scheduler_manager.get_jobs()),
        "state": str(scheduler_manager.scheduler.state) if scheduler_manager.scheduler else "NOT_INITIALIZED"
    }
