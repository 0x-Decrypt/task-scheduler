import json
import subprocess
import asyncio
import logging
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from croniter import croniter

from database import get_db_session, engine
from models import TaskModel, TaskExecutionModel, TaskStatus, ScheduleType

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        jobstores = {
            'default': SQLAlchemyJobStore(engine=engine)
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )
        self._is_running = False
    
    async def start(self):
        """Start the scheduler."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Task scheduler started")
    
    async def shutdown(self):
        """Shutdown the scheduler."""
        if self._is_running:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("Task scheduler stopped")
    
    def add_task(self, task: TaskModel) -> bool:
        """Add a task to the scheduler."""
        try:
            job_id = str(task.id)
            schedule_config = json.loads(task.schedule_config) if task.schedule_config else {}
            
            if task.schedule_type == ScheduleType.CRON:
                self._add_cron_job(job_id, task, schedule_config)
            elif task.schedule_type == ScheduleType.INTERVAL:
                self._add_interval_job(job_id, task, schedule_config)
            elif task.schedule_type == ScheduleType.ONCE:
                self._add_once_job(job_id, task, schedule_config)
            elif task.schedule_type == ScheduleType.STARTUP:
                self._add_startup_job(job_id, task)
            
            logger.info(f"Task {task.name} added to scheduler")
            return True
            
        except Exception as e:
            logger.error(f"Error adding task {task.name}: {e}")
            return False
    
    def remove_task(self, task_id: UUID) -> bool:
        """Remove a task from the scheduler."""
        try:
            job_id = str(task_id)
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Task {task_id} removed from scheduler")
            return True
        except Exception as e:
            logger.error(f"Error removing task {task_id}: {e}")
            return False
    
    def update_task(self, task: TaskModel) -> bool:
        """Update a task in the scheduler."""
        self.remove_task(task.id)
        if task.enabled:
            return self.add_task(task)
        return True
    
    def _add_cron_job(self, job_id: str, task: TaskModel, config: Dict[str, Any]):
        """Add a cron-based job."""
        expression = config.get('expression', '0 0 * * *')
        if not croniter.is_valid(expression):
            raise ValueError(f"Invalid cron expression: {expression}")
        
        self.scheduler.add_job(
            self._execute_task,
            'cron',
            id=job_id,
            args=[task.id],
            **self._parse_cron_expression(expression),
            misfire_grace_time=60
        )
    
    def _add_interval_job(self, job_id: str, task: TaskModel, config: Dict[str, Any]):
        """Add an interval-based job."""
        kwargs = {}
        if 'seconds' in config:
            kwargs['seconds'] = config['seconds']
        if 'minutes' in config:
            kwargs['minutes'] = config['minutes']
        if 'hours' in config:
            kwargs['hours'] = config['hours']
        if 'days' in config:
            kwargs['days'] = config['days']
        
        self.scheduler.add_job(
            self._execute_task,
            'interval',
            id=job_id,
            args=[task.id],
            **kwargs
        )
    
    def _add_once_job(self, job_id: str, task: TaskModel, config: Dict[str, Any]):
        """Add a one-time job."""
        run_date = config.get('run_date')
        if isinstance(run_date, str):
            run_date = datetime.fromisoformat(run_date)
        
        self.scheduler.add_job(
            self._execute_task,
            'date',
            id=job_id,
            args=[task.id],
            run_date=run_date
        )
    
    def _add_startup_job(self, job_id: str, task: TaskModel):
        """Add a startup job."""
        self.scheduler.add_job(
            self._execute_task,
            'date',
            id=job_id,
            args=[task.id],
            run_date=datetime.now()
        )
    
    def _parse_cron_expression(self, expression: str) -> Dict[str, Any]:
        """Parse cron expression into APScheduler format."""
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts")
        
        minute, hour, day, month, day_of_week = parts
        
        return {
            'minute': minute,
            'hour': hour,
            'day': day,
            'month': month,
            'day_of_week': day_of_week
        }
    
    async def _execute_task(self, task_id: UUID):
        """Execute a task and log the results."""
        execution_id = None
        
        try:
            with get_db_session() as db:
                # Get task details
                task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
                if not task or not task.enabled:
                    return
                
                # Create execution record
                execution = TaskExecutionModel(
                    task_id=task_id,
                    status=TaskStatus.RUNNING,
                    started_at=datetime.utcnow()
                )
                db.add(execution)
                db.commit()
                execution_id = execution.id
                
                logger.info(f"Starting task execution: {task.name}")
                
                # Execute command
                process = await asyncio.create_subprocess_shell(
                    task.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=task.timeout
                    )
                    
                    # Update execution record
                    execution.status = TaskStatus.SUCCESS if process.returncode == 0 else TaskStatus.FAILED
                    execution.completed_at = datetime.utcnow()
                    execution.exit_code = process.returncode
                    execution.stdout = stdout.decode('utf-8', errors='ignore')
                    execution.stderr = stderr.decode('utf-8', errors='ignore')
                    
                    db.commit()
                    
                    # Send notification if configured
                    if (execution.status == TaskStatus.SUCCESS and task.notify_on_success) or \
                       (execution.status == TaskStatus.FAILED and task.notify_on_failure):
                        await self._send_notification(task, execution.status)
                    
                    logger.info(f"Task {task.name} completed with status: {execution.status}")
                    
                except asyncio.TimeoutError:
                    process.kill()
                    execution.status = TaskStatus.FAILED
                    execution.completed_at = datetime.utcnow()
                    execution.error_message = f"Task timed out after {task.timeout} seconds"
                    db.commit()
                    
                    if task.notify_on_failure:
                        await self._send_notification(task, TaskStatus.FAILED)
                    
                    logger.warning(f"Task {task.name} timed out")
                
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            
            if execution_id:
                try:
                    with get_db_session() as db:
                        execution = db.query(TaskExecutionModel).filter(
                            TaskExecutionModel.id == execution_id
                        ).first()
                        if execution:
                            execution.status = TaskStatus.FAILED
                            execution.completed_at = datetime.utcnow()
                            execution.error_message = str(e)
                            db.commit()
                except Exception as db_error:
                    logger.error(f"Error updating execution record: {db_error}")
    
    async def _send_notification(self, task: TaskModel, status: TaskStatus):
        """Send system notification for task completion."""
        try:
            from plyer import notification
            
            title = f"Task {status.value.title()}"
            message = f"Task '{task.name}' {status.value}"
            
            notification.notify(
                title=title,
                message=message,
                timeout=5
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_running_jobs(self) -> List[Dict[str, Any]]:
        """Get list of currently running jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs


# Global scheduler instance
scheduler = TaskScheduler()
