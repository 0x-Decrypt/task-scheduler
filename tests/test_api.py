#!/usr/bin/env python3
"""
Task Scheduler Tests
Basic test suite for the Task Scheduler API
"""

import unittest
import json
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from simple_api import app
from fastapi.testclient import TestClient

class TestTaskSchedulerAPI(unittest.TestCase):
    """Test cases for Task Scheduler API"""
    
    def setUp(self):
        """Set up test client and temporary database"""
        self.client = TestClient(app)
        
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Patch the DB_FILE in simple_api
        self.db_patcher = patch('simple_api.DB_FILE', self.temp_db.name)
        self.db_patcher.start()
        
        # Initialize test database
        from simple_api import init_db
        init_db()
    
    def tearDown(self):
        """Clean up test database"""
        self.db_patcher.stop()
        os.unlink(self.temp_db.name)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Task Scheduler API")
        self.assertEqual(data["version"], "1.0.0")
    
    def test_create_task(self):
        """Test task creation"""
        task_data = {
            "name": "Test Task",
            "description": "A test task",
            "command": "echo 'Hello World'",
            "schedule_type": "cron",
            "schedule_config": {"expression": "0 9 * * *"},
            "enabled": True,
            "timeout": 3600
        }
        
        response = self.client.post("/tasks", json=task_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["name"], "Test Task")
        self.assertEqual(data["command"], "echo 'Hello World'")
        self.assertEqual(data["schedule_type"], "cron")
        self.assertTrue(data["enabled"])
        self.assertIn("id", data)
    
    def test_get_tasks(self):
        """Test getting all tasks"""
        # Create a test task first
        task_data = {
            "name": "Test Task",
            "command": "echo 'test'",
            "schedule_type": "once",
            "schedule_config": {"run_date": "2025-12-31T23:59:59"}
        }
        
        create_response = self.client.post("/tasks", json=task_data)
        self.assertEqual(create_response.status_code, 200)
        
        # Get all tasks
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Test Task")
    
    def test_get_task_by_id(self):
        """Test getting a specific task"""
        # Create a test task
        task_data = {
            "name": "Specific Task",
            "command": "echo 'specific'",
            "schedule_type": "interval",
            "schedule_config": {"hours": 1}
        }
        
        create_response = self.client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Get the specific task
        response = self.client.get(f"/tasks/{task_id}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["name"], "Specific Task")
        self.assertEqual(data["id"], task_id)
    
    def test_get_nonexistent_task(self):
        """Test getting a task that doesn't exist"""
        response = self.client.get("/tasks/nonexistent-id")
        self.assertEqual(response.status_code, 404)
    
    def test_update_task(self):
        """Test updating a task"""
        # Create a test task
        task_data = {
            "name": "Original Task",
            "command": "echo 'original'",
            "schedule_type": "cron",
            "schedule_config": {"expression": "0 0 * * *"}
        }
        
        create_response = self.client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Update the task
        update_data = {
            "name": "Updated Task",
            "command": "echo 'updated'"
        }
        
        response = self.client.put(f"/tasks/{task_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["name"], "Updated Task")
        self.assertEqual(data["command"], "echo 'updated'")
    
    def test_toggle_task(self):
        """Test toggling task enabled status"""
        # Create an enabled task
        task_data = {
            "name": "Toggle Task",
            "command": "echo 'toggle'",
            "schedule_type": "startup",
            "schedule_config": {},
            "enabled": True
        }
        
        create_response = self.client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Toggle to disabled
        response = self.client.post(f"/tasks/{task_id}/toggle")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["enabled"])
        
        # Toggle back to enabled
        response = self.client.post(f"/tasks/{task_id}/toggle")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["enabled"])
    
    def test_delete_task(self):
        """Test deleting a task"""
        # Create a test task
        task_data = {
            "name": "Delete Me",
            "command": "echo 'delete'",
            "schedule_type": "cron",
            "schedule_config": {"expression": "0 0 * * *"}
        }
        
        create_response = self.client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Delete the task
        response = self.client.delete(f"/tasks/{task_id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify it's deleted
        get_response = self.client.get(f"/tasks/{task_id}")
        self.assertEqual(get_response.status_code, 404)
    
    @patch('simple_api.asyncio.create_subprocess_shell')
    def test_run_task(self, mock_subprocess):
        """Test running a task immediately"""
        # Mock subprocess
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"Hello World\n", b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        # Create a test task
        task_data = {
            "name": "Run Task",
            "command": "echo 'Hello World'",
            "schedule_type": "cron",
            "schedule_config": {"expression": "0 0 * * *"}
        }
        
        create_response = self.client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Run the task
        with patch('simple_api.asyncio.wait_for') as mock_wait:
            mock_wait.return_value = (b"Hello World\n", b"")
            response = self.client.post(f"/tasks/{task_id}/run")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["task_id"], task_id)
        self.assertIn("stdout", data)
    
    def test_get_executions(self):
        """Test getting execution history"""
        response = self.client.get("/executions")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_invalid_task_data(self):
        """Test creating task with invalid data"""
        invalid_data = {
            "name": "",  # Empty name should fail
            "command": "echo 'test'",
            "schedule_type": "invalid_type",
            "schedule_config": {}
        }
        
        response = self.client.post("/tasks", json=invalid_data)
        self.assertEqual(response.status_code, 422)  # Validation error


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations directly"""
    
    def setUp(self):
        """Set up temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # Initialize database
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE tasks (
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
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up database"""
        os.unlink(self.temp_db.name)
    
    def test_database_connection(self):
        """Test database connection and basic operations"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Insert test data
        cursor.execute("""
            INSERT INTO tasks (id, name, command, schedule_type, schedule_config)
            VALUES ('test-id', 'Test Task', 'echo test', 'cron', '{"expression": "0 0 * * *"}')
        """)
        
        # Query data
        cursor.execute("SELECT * FROM tasks WHERE id = 'test-id'")
        row = cursor.fetchone()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'Test Task')  # name column
        
        conn.close()


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
