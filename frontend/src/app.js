// Task Scheduler Frontend Application

class TaskSchedulerApp {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.currentTab = 'tasks';
        this.tasks = [];
        this.executions = [];
        this.editingTaskId = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadTasks();
        this.loadExecutions();
    }
    
    bindEvents() {
        // Tab navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = e.currentTarget.dataset.tab;
                this.switchTab(tab);
            });
        });
        
        // Modal events
        document.getElementById('newTaskBtn').addEventListener('click', () => {
            this.openTaskModal();
        });
        
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeTaskModal();
        });
        
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.closeTaskModal();
        });
        
        // Form events
        document.getElementById('scheduleType').addEventListener('change', (e) => {
            this.toggleScheduleConfig(e.target.value);
        });
        
        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTask();
        });
        
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Filter
        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.filterTasks(e.target.value);
        });
        
        // Settings
        document.getElementById('themeSelect').addEventListener('change', (e) => {
            this.changeTheme(e.target.value);
        });
        
        // Close modal on backdrop click
        document.getElementById('taskModal').addEventListener('click', (e) => {
            if (e.target.id === 'taskModal') {
                this.closeTaskModal();
            }
        });
    }
    
    switchTab(tab) {
        this.currentTab = tab;
        
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tab}Tab`).classList.add('active');
        
        // Load data if needed
        if (tab === 'history') {
            this.loadExecutions();
        }
    }
    
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
            throw error;
        }
    }
    
    async loadTasks() {
        try {
            this.tasks = await this.apiCall('/tasks');
            this.renderTasks();
        } catch (error) {
            document.getElementById('tasksList').innerHTML = 
                '<div class="error">Failed to load tasks. Please check if the backend is running.</div>';
        }
    }
    
    async loadExecutions() {
        try {
            this.executions = await this.apiCall('/executions?limit=50');
            this.renderExecutions();
        } catch (error) {
            document.getElementById('historyList').innerHTML = 
                '<div class="error">Failed to load execution history.</div>';
        }
    }
    
    renderTasks() {
        const container = document.getElementById('tasksList');
        
        if (this.tasks.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <h3>No tasks yet</h3>
                    <p>Create your first task to get started!</p>
                    <button class="btn btn-primary" onclick="app.openTaskModal()">Create Task</button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.tasks.map(task => this.createTaskCard(task)).join('');
    }
    
    createTaskCard(task) {
        const scheduleText = this.formatSchedule(task.schedule_type, task.schedule_config);
        const statusClass = task.enabled ? 'enabled' : 'disabled';
        const statusText = task.enabled ? 'Enabled' : 'Disabled';
        
        return `
            <div class="task-card">
                <div class="task-header">
                    <div>
                        <div class="task-title">${this.escapeHtml(task.name)}</div>
                        ${task.description ? `<div class="task-description">${this.escapeHtml(task.description)}</div>` : ''}
                    </div>
                    <div class="task-status">
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                </div>
                
                <div class="task-details">
                    <div class="task-detail">
                        <div class="task-detail-label">Command</div>
                        <div class="task-detail-value">${this.escapeHtml(task.command)}</div>
                    </div>
                    <div class="task-detail">
                        <div class="task-detail-label">Schedule</div>
                        <div class="task-detail-value">${scheduleText}</div>
                    </div>
                    <div class="task-detail">
                        <div class="task-detail-label">Timeout</div>
                        <div class="task-detail-value">${task.timeout}s</div>
                    </div>
                    <div class="task-detail">
                        <div class="task-detail-label">Created</div>
                        <div class="task-detail-value">${new Date(task.created_at).toLocaleString()}</div>
                    </div>
                </div>
                
                <div class="task-actions">
                    <button class="btn btn-success btn-sm" onclick="app.runTask('${task.id}')">
                        ▶️ Run Now
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="app.editTask('${task.id}')">
                        ✏️ Edit
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="app.toggleTask('${task.id}')">
                        ${task.enabled ? '⏸️ Disable' : '▶️ Enable'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="app.deleteTask('${task.id}')">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `;
    }
    
    renderExecutions() {
        const container = document.getElementById('historyList');
        
        if (this.executions.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No execution history available.</div>';
            return;
        }
        
        container.innerHTML = this.executions.map(exec => this.createExecutionCard(exec)).join('');
    }
    
    createExecutionCard(execution) {
        const task = this.tasks.find(t => t.id === execution.task_id);
        const taskName = task ? task.name : 'Unknown Task';
        const statusClass = execution.status.toLowerCase();
        const duration = execution.completed_at ? 
            Math.round((new Date(execution.completed_at) - new Date(execution.started_at)) / 1000) : 
            'Running';
        
        return `
            <div class="execution-card">
                <div class="execution-header">
                    <div class="execution-task">${this.escapeHtml(taskName)}</div>
                    <div class="execution-time">${new Date(execution.started_at).toLocaleString()}</div>
                </div>
                
                <div class="execution-status">
                    <span class="status-badge ${statusClass}">${execution.status}</span>
                    ${execution.exit_code !== null ? `Exit Code: ${execution.exit_code}` : ''}
                    ${duration !== 'Running' ? `Duration: ${duration}s` : ''}
                </div>
                
                ${execution.stdout ? `
                    <div class="execution-output">
                        <strong>Output:</strong><br>
                        ${this.escapeHtml(execution.stdout)}
                    </div>
                ` : ''}
                
                ${execution.stderr ? `
                    <div class="execution-output">
                        <strong>Error:</strong><br>
                        ${this.escapeHtml(execution.stderr)}
                    </div>
                ` : ''}
                
                ${execution.error_message ? `
                    <div class="execution-output">
                        <strong>Error Message:</strong><br>
                        ${this.escapeHtml(execution.error_message)}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    formatSchedule(type, config) {
        switch (type) {
            case 'cron':
                return `Cron: ${config.expression}`;
            case 'interval':
                const parts = [];
                if (config.hours) parts.push(`${config.hours}h`);
                if (config.minutes) parts.push(`${config.minutes}m`);
                if (config.seconds) parts.push(`${config.seconds}s`);
                return `Every ${parts.join(' ')}`;
            case 'once':
                return `Once: ${new Date(config.run_date).toLocaleString()}`;
            case 'startup':
                return 'On Startup';
            default:
                return 'Unknown';
        }
    }
    
    openTaskModal(task = null) {
        this.editingTaskId = task ? task.id : null;
        const modal = document.getElementById('taskModal');
        const title = document.getElementById('modalTitle');
        
        title.textContent = task ? 'Edit Task' : 'Create New Task';
        
        if (task) {
            this.populateTaskForm(task);
        } else {
            this.resetTaskForm();
        }
        
        modal.classList.add('show');
    }
    
    closeTaskModal() {
        document.getElementById('taskModal').classList.remove('show');
        this.resetTaskForm();
        this.editingTaskId = null;
    }
    
    populateTaskForm(task) {
        document.getElementById('taskName').value = task.name;
        document.getElementById('taskDescription').value = task.description || '';
        document.getElementById('taskCommand').value = task.command;
        document.getElementById('scheduleType').value = task.schedule_type;
        document.getElementById('taskTimeout').value = task.timeout;
        document.getElementById('taskEnabled').checked = task.enabled;
        document.getElementById('notifySuccess').checked = task.notify_on_success;
        document.getElementById('notifyFailure').checked = task.notify_on_failure;
        
        this.toggleScheduleConfig(task.schedule_type);
        this.populateScheduleConfig(task.schedule_type, task.schedule_config);
    }
    
    populateScheduleConfig(type, config) {
        switch (type) {
            case 'cron':
                document.getElementById('cronExpression').value = config.expression || '';
                break;
            case 'interval':
                document.getElementById('intervalHours').value = config.hours || 0;
                document.getElementById('intervalMinutes').value = config.minutes || 0;
                document.getElementById('intervalSeconds').value = config.seconds || 0;
                break;
            case 'once':
                if (config.run_date) {
                    const date = new Date(config.run_date);
                    document.getElementById('runDate').value = date.toISOString().slice(0, 16);
                }
                break;
        }
    }
    
    resetTaskForm() {
        document.getElementById('taskForm').reset();
        document.getElementById('taskEnabled').checked = true;
        document.getElementById('notifyFailure').checked = true;
        document.getElementById('taskTimeout').value = 3600;
        this.toggleScheduleConfig('');
    }
    
    toggleScheduleConfig(type) {
        document.querySelectorAll('.schedule-config').forEach(config => {
            config.style.display = 'none';
        });
        
        if (type) {
            const configElement = document.getElementById(`${type}Config`);
            if (configElement) {
                configElement.style.display = 'block';
            }
        }
    }
    
    async saveTask() {
        try {
            const taskData = this.getTaskFormData();
            
            if (this.editingTaskId) {
                await this.apiCall(`/tasks/${this.editingTaskId}`, {
                    method: 'PUT',
                    body: JSON.stringify(taskData)
                });
                this.showNotification('Task updated successfully!', 'success');
            } else {
                await this.apiCall('/tasks', {
                    method: 'POST',
                    body: JSON.stringify(taskData)
                });
                this.showNotification('Task created successfully!', 'success');
            }
            
            this.closeTaskModal();
            this.loadTasks();
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    getTaskFormData() {
        const formData = {
            name: document.getElementById('taskName').value,
            description: document.getElementById('taskDescription').value || null,
            command: document.getElementById('taskCommand').value,
            schedule_type: document.getElementById('scheduleType').value,
            schedule_config: this.getScheduleConfig(),
            enabled: document.getElementById('taskEnabled').checked,
            notify_on_success: document.getElementById('notifySuccess').checked,
            notify_on_failure: document.getElementById('notifyFailure').checked,
            timeout: parseInt(document.getElementById('taskTimeout').value)
        };
        
        return formData;
    }
    
    getScheduleConfig() {
        const type = document.getElementById('scheduleType').value;
        
        switch (type) {
            case 'cron':
                return {
                    expression: document.getElementById('cronExpression').value
                };
            case 'interval':
                const config = {};
                const hours = parseInt(document.getElementById('intervalHours').value) || 0;
                const minutes = parseInt(document.getElementById('intervalMinutes').value) || 0;
                const seconds = parseInt(document.getElementById('intervalSeconds').value) || 0;
                
                if (hours > 0) config.hours = hours;
                if (minutes > 0) config.minutes = minutes;
                if (seconds > 0) config.seconds = seconds;
                
                return config;
            case 'once':
                return {
                    run_date: document.getElementById('runDate').value
                };
            case 'startup':
                return {};
            default:
                return {};
        }
    }
    
    async runTask(taskId) {
        try {
            await this.apiCall(`/tasks/${taskId}/run`, { method: 'POST' });
            this.showNotification('Task started successfully!', 'success');
            setTimeout(() => this.loadExecutions(), 1000);
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async editTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (task) {
            this.openTaskModal(task);
        }
    }
    
    async toggleTask(taskId) {
        try {
            await this.apiCall(`/tasks/${taskId}/toggle`, { method: 'POST' });
            this.showNotification('Task status updated!', 'success');
            this.loadTasks();
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }
        
        try {
            await this.apiCall(`/tasks/${taskId}`, { method: 'DELETE' });
            this.showNotification('Task deleted successfully!', 'success');
            this.loadTasks();
        } catch (error) {
            // Error already handled in apiCall
        }
    }
    
    filterTasks(filter) {
        let filteredTasks = this.tasks;
        
        if (filter === 'enabled') {
            filteredTasks = this.tasks.filter(task => task.enabled);
        } else if (filter === 'disabled') {
            filteredTasks = this.tasks.filter(task => !task.enabled);
        }
        
        const container = document.getElementById('tasksList');
        if (filteredTasks.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No tasks match the current filter.</div>';
        } else {
            container.innerHTML = filteredTasks.map(task => this.createTaskCard(task)).join('');
        }
    }
    
    refreshData() {
        this.loadTasks();
        if (this.currentTab === 'history') {
            this.loadExecutions();
        }
        this.showNotification('Data refreshed!', 'info');
    }
    
    changeTheme(theme) {
        // Simple theme implementation
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }
    
    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            z-index: 2000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Add notification styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);

// Initialize the app
const app = new TaskSchedulerApp();
