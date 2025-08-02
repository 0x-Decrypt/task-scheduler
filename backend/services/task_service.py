import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import (
    TaskModel, TaskExecutionModel, TaskCreateRequest, TaskUpdateRequest,
    TaskResponse, TaskExecutionResponse, TaskStatus
)


class TaskService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, task_data: TaskCreateRequest) -> TaskModel:
        """Create a new task."""
        db_task = TaskModel(
            name=task_data.name,
            description=task_data.description,
            command=task_data.command,
            schedule_type=task_data.schedule_type.value,
            schedule_config=json.dumps(task_data.schedule_config),
            enabled=task_data.enabled,
            notify_on_success=task_data.notify_on_success,
            notify_on_failure=task_data.notify_on_failure,
            timeout=task_data.timeout
        )
        
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
    
    def get_task(self, task_id: UUID) -> Optional[TaskModel]:
        """Get a task by ID."""
        return self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
    
    def get_tasks(self, enabled_only: bool = False) -> List[TaskModel]:
        """Get all tasks."""
        query = self.db.query(TaskModel)
        if enabled_only:
            query = query.filter(TaskModel.enabled == True)
        return query.all()
    
    def update_task(self, task_id: UUID, task_data: TaskUpdateRequest) -> Optional[TaskModel]:
        """Update a task."""
        db_task = self.get_task(task_id)
        if not db_task:
            return None
        
        update_data = task_data.dict(exclude_unset=True)
        if 'schedule_config' in update_data:
            update_data['schedule_config'] = json.dumps(update_data['schedule_config'])
        if 'schedule_type' in update_data:
            update_data['schedule_type'] = update_data['schedule_type'].value
        
        for field, value in update_data.items():
            setattr(db_task, field, value)
        
        db_task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
    
    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task."""
        db_task = self.get_task(task_id)
        if not db_task:
            return False
        
        # Delete related executions
        self.db.query(TaskExecutionModel).filter(
            TaskExecutionModel.task_id == task_id
        ).delete()
        
        self.db.delete(db_task)
        self.db.commit()
        return True
    
    def toggle_task(self, task_id: UUID) -> Optional[TaskModel]:
        """Toggle task enabled status."""
        db_task = self.get_task(task_id)
        if not db_task:
            return None
        
        db_task.enabled = not db_task.enabled
        db_task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
    
    def get_task_executions(self, task_id: UUID, limit: int = 50) -> List[TaskExecutionModel]:
        """Get task execution history."""
        return self.db.query(TaskExecutionModel).filter(
            TaskExecutionModel.task_id == task_id
        ).order_by(desc(TaskExecutionModel.started_at)).limit(limit).all()
    
    def get_all_executions(self, limit: int = 100) -> List[TaskExecutionModel]:
        """Get all task executions."""
        return self.db.query(TaskExecutionModel).order_by(
            desc(TaskExecutionModel.started_at)
        ).limit(limit).all()
    
    def create_execution(self, task_id: UUID, status: TaskStatus) -> TaskExecutionModel:
        """Create a new task execution record."""
        execution = TaskExecutionModel(
            task_id=task_id,
            status=status.value,
            started_at=datetime.utcnow()
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    def update_execution(self, execution_id: UUID, **kwargs) -> Optional[TaskExecutionModel]:
        """Update a task execution record."""
        execution = self.db.query(TaskExecutionModel).filter(
            TaskExecutionModel.id == execution_id
        ).first()
        
        if not execution:
            return None
        
        for field, value in kwargs.items():
            if hasattr(execution, field):
                setattr(execution, field, value)
        
        self.db.commit()
        self.db.refresh(execution)
        return execution
    
    def to_response(self, task: TaskModel) -> TaskResponse:
        """Convert TaskModel to TaskResponse."""
        schedule_config = {}
        if task.schedule_config:
            try:
                schedule_config = json.loads(task.schedule_config)
            except json.JSONDecodeError:
                schedule_config = {}
        
        return TaskResponse(
            id=str(task.id),
            name=task.name,
            description=task.description,
            command=task.command,
            schedule_type=task.schedule_type,
            schedule_config=schedule_config,
            enabled=task.enabled,
            notify_on_success=task.notify_on_success,
            notify_on_failure=task.notify_on_failure,
            timeout=task.timeout,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
    
    def execution_to_response(self, execution: TaskExecutionModel) -> TaskExecutionResponse:
        """Convert TaskExecutionModel to TaskExecutionResponse."""
        return TaskExecutionResponse(
            id=str(execution.id),
            task_id=str(execution.task_id),
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            exit_code=execution.exit_code,
            stdout=execution.stdout,
            stderr=execution.stderr,
            error_message=execution.error_message
        )
