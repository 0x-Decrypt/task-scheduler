#!/usr/bin/env python3
"""
Simple Task Scheduler API - Minimal working version
"""

import json
import sqlite3
import subprocess
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_FILE = "tasks.db"

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            command TEXT NOT NULL,
            schedule_type TEXT NOT NULL,
            schedule_config TEXT,
            enabled BOOLEAN DEFAULT 1,
            notify_on_success BOOLEAN DEFAULT 0,
            notify_on_failure BOOLEAN DEFAULT 1,
            timeout INTEGER DEFAULT 3600,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create executions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS executions (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            status TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            exit_code INTEGER,
            stdout TEXT,
            stderr TEXT,
            error_message TEXT
        )
    """)
    
    conn.commit()
    conn.close()

# Pydantic models
class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    command: str
    schedule_type: str
    schedule_config: Dict[str, Any]
    enabled: bool = True
    notify_on_success: bool = False
    notify_on_failure: bool = True
    timeout: int = 3600

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    command: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    timeout: Optional[int] = None

class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    command: str
    schedule_type: str
    schedule_config: Dict[str, Any]
    enabled: bool
    notify_on_success: bool
    notify_on_failure: bool
    timeout: int
    created_at: str
    updated_at: str

class ExecutionResponse(BaseModel):
    id: str
    task_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    error_message: Optional[str]

# FastAPI app
app = FastAPI(
    title="Task Scheduler API",
    description="A simple task scheduler API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()
    logger.info("Task Scheduler API started")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Task Scheduler API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """Create a new task."""
    task_id = str(uuid4())
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO tasks (id, name, description, command, schedule_type, 
                             schedule_config, enabled, notify_on_success, 
                             notify_on_failure, timeout)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, task.name, task.description, task.command,
            task.schedule_type, json.dumps(task.schedule_config),
            task.enabled, task.notify_on_success, task.notify_on_failure,
            task.timeout
        ))
        
        conn.commit()
        
        # Fetch the created task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        return row_to_task_response(row)
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(enabled_only: bool = False):
    """Get all tasks."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        if enabled_only:
            cursor.execute("SELECT * FROM tasks WHERE enabled = 1 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        return [row_to_task_response(row) for row in rows]
        
    finally:
        conn.close()

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return row_to_task_response(row)
        
    finally:
        conn.close()

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task: TaskUpdate):
    """Update a task."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if task exists
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Build update query dynamically
        updates = []
        values = []
        
        for field, value in task.dict(exclude_unset=True).items():
            if field == 'schedule_config' and value is not None:
                updates.append(f"{field} = ?")
                values.append(json.dumps(value))
            else:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(task_id)
            
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        # Return updated task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return row_to_task_response(row)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        cursor.execute("DELETE FROM executions WHERE task_id = ?", (task_id,))
        conn.commit()
        
        return {"message": "Task deleted successfully"}
        
    finally:
        conn.close()

@app.post("/tasks/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task(task_id: str):
    """Toggle task enabled status."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT enabled FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        new_enabled = not bool(row[0])
        cursor.execute(
            "UPDATE tasks SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_enabled, task_id)
        )
        conn.commit()
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return row_to_task_response(row)
        
    finally:
        conn.close()

@app.post("/tasks/{task_id}/run", response_model=ExecutionResponse)
async def run_task(task_id: str):
    """Run a task immediately."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Get task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task_row = cursor.fetchone()
        
        if not task_row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        command = task_row[3]  # command column
        timeout = task_row[9]  # timeout column
        
        # Create execution record
        exec_id = str(uuid4())
        started_at = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO executions (id, task_id, status, started_at)
            VALUES (?, ?, ?, ?)
        """, (exec_id, task_id, "running", started_at))
        conn.commit()
        
        # Execute command
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            completed_at = datetime.utcnow().isoformat()
            status = "success" if process.returncode == 0 else "failed"
            
            cursor.execute("""
                UPDATE executions 
                SET status = ?, completed_at = ?, exit_code = ?, stdout = ?, stderr = ?
                WHERE id = ?
            """, (
                status, completed_at, process.returncode,
                stdout.decode('utf-8', errors='ignore'),
                stderr.decode('utf-8', errors='ignore'),
                exec_id
            ))
            
        except asyncio.TimeoutError:
            cursor.execute("""
                UPDATE executions 
                SET status = ?, completed_at = ?, error_message = ?
                WHERE id = ?
            """, (
                "failed", datetime.utcnow().isoformat(),
                f"Task timed out after {timeout} seconds",
                exec_id
            ))
            
        except Exception as e:
            cursor.execute("""
                UPDATE executions 
                SET status = ?, completed_at = ?, error_message = ?
                WHERE id = ?
            """, (
                "failed", datetime.utcnow().isoformat(), str(e), exec_id
            ))
        
        conn.commit()
        
        # Return execution details
        cursor.execute("SELECT * FROM executions WHERE id = ?", (exec_id,))
        exec_row = cursor.fetchone()
        return row_to_execution_response(exec_row)
        
    finally:
        conn.close()

@app.get("/executions", response_model=List[ExecutionResponse])
async def get_executions(limit: int = 100):
    """Get execution history."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM executions 
            ORDER BY started_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        return [row_to_execution_response(row) for row in rows]
        
    finally:
        conn.close()

@app.get("/tasks/{task_id}/executions", response_model=List[ExecutionResponse])
async def get_task_executions(task_id: str, limit: int = 50):
    """Get task execution history."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM executions 
            WHERE task_id = ?
            ORDER BY started_at DESC 
            LIMIT ?
        """, (task_id, limit))
        
        rows = cursor.fetchall()
        return [row_to_execution_response(row) for row in rows]
        
    finally:
        conn.close()

def row_to_task_response(row) -> TaskResponse:
    """Convert database row to TaskResponse."""
    schedule_config = {}
    if row[5]:  # schedule_config column
        try:
            schedule_config = json.loads(row[5])
        except json.JSONDecodeError:
            schedule_config = {}
    
    return TaskResponse(
        id=row[0],
        name=row[1],
        description=row[2],
        command=row[3],
        schedule_type=row[4],
        schedule_config=schedule_config,
        enabled=bool(row[6]),
        notify_on_success=bool(row[7]),
        notify_on_failure=bool(row[8]),
        timeout=row[9],
        created_at=row[10],
        updated_at=row[11]
    )

def row_to_execution_response(row) -> ExecutionResponse:
    """Convert database row to ExecutionResponse."""
    return ExecutionResponse(
        id=row[0],
        task_id=row[1],
        status=row[2],
        started_at=row[3],
        completed_at=row[4],
        exit_code=row[5],
        stdout=row[6],
        stderr=row[7],
        error_message=row[8]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
