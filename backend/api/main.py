import json
import asyncio
import subprocess
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, init_database
from models import (
    TaskCreateRequest, TaskUpdateRequest, TaskResponse, TaskExecutionResponse,
    TaskModel, TaskExecutionModel, TaskStatus
)
from services.task_service import TaskService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Task Scheduler API",
    description="A simple, intuitive task scheduler API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global task runner for immediate execution
class TaskRunner:
    @staticmethod
    async def run_task(task: TaskModel) -> TaskExecutionModel:
        """Execute a task immediately and return execution details."""
        execution = TaskExecutionModel()
        execution.task_id = task.id
        execution.status = TaskStatus.RUNNING.value
        execution.started_at = datetime.utcnow()
        
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                task.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=task.timeout
            )
            
            execution.status = TaskStatus.SUCCESS.value if process.returncode == 0 else TaskStatus.FAILED.value
            execution.completed_at = datetime.utcnow()
            execution.exit_code = process.returncode
            execution.stdout = stdout.decode('utf-8', errors='ignore')
            execution.stderr = stderr.decode('utf-8', errors='ignore')
            
        except asyncio.TimeoutError:
            execution.status = TaskStatus.FAILED.value
            execution.completed_at = datetime.utcnow()
            execution.error_message = f"Task timed out after {task.timeout} seconds"
            
        except Exception as e:
            execution.status = TaskStatus.FAILED.value
            execution.completed_at = datetime.utcnow()
            execution.error_message = str(e)
        
        return execution


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_database()
    logger.info("Task Scheduler API started")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Task Scheduler API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Task endpoints
@app.post("/tasks", response_model=TaskResponse)
async def create_task(task_data: TaskCreateRequest, db: Session = Depends(get_db)):
    """Create a new task."""
    try:
        service = TaskService(db)
        task = service.create_task(task_data)
        return service.to_response(task)
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(enabled_only: bool = False, db: Session = Depends(get_db)):
    """Get all tasks."""
    service = TaskService(db)
    tasks = service.get_tasks(enabled_only=enabled_only)
    return [service.to_response(task) for task in tasks]


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task."""
    try:
        task_uuid = UUID(task_id)
        service = TaskService(db)
        task = service.get_task(task_uuid)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return service.to_response(task)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")


@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_data: TaskUpdateRequest, db: Session = Depends(get_db)):
    """Update a task."""
    try:
        task_uuid = UUID(task_id)
        service = TaskService(db)
        task = service.update_task(task_uuid, task_data)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return service.to_response(task)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task."""
    try:
        task_uuid = UUID(task_id)
        service = TaskService(db)
        success = service.delete_task(task_uuid)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")


@app.post("/tasks/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task(task_id: str, db: Session = Depends(get_db)):
    """Toggle task enabled status."""
    try:
        task_uuid = UUID(task_id)
        service = TaskService(db)
        task = service.toggle_task(task_uuid)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return service.to_response(task)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")


@app.post("/tasks/{task_id}/run", response_model=TaskExecutionResponse)
async def run_task_now(task_id: str, db: Session = Depends(get_db)):
    """Run a task immediately."""
    try:
        task_uuid = UUID(task_id)
        service = TaskService(db)
        task = service.get_task(task_uuid)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Execute task
        execution = await TaskRunner.run_task(task)
        
        # Save execution to database
        db_execution = service.create_execution(task_uuid, TaskStatus(execution.status))
        service.update_execution(
            db_execution.id,
            completed_at=execution.completed_at,
            exit_code=execution.exit_code,
            stdout=execution.stdout,
            stderr=execution.stderr,
            error_message=execution.error_message
        )
        
        return service.execution_to_response(db_execution)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    except Exception as e:
        logger.error(f"Error running task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Execution endpoints
@app.get("/tasks/{task_id}/executions", response_model=List[TaskExecutionResponse])
async def get_task_executions(task_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Get task execution history."""
    try:
        task_uuid = UUID(task_id)
        service = TaskService(db)
        executions = service.get_task_executions(task_uuid, limit)
        return [service.execution_to_response(exec) for exec in executions]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")


@app.get("/executions", response_model=List[TaskExecutionResponse])
async def get_all_executions(limit: int = 100, db: Session = Depends(get_db)):
    """Get all task executions."""
    service = TaskService(db)
    executions = service.get_all_executions(limit)
    return [service.execution_to_response(exec) for exec in executions]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
