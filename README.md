# Task Scheduler

A simple, intuitive Task Scheduler - a cron-like job scheduler with GUI, notifications, and flexible scheduling options built for modern cross-platform usage.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node-16+-green.svg)](https://nodejs.org/)

> 🚀 **Portfolio Project**: Professional-grade task scheduler showcasing full-stack development skills with Python, JavaScript, and modern frameworks.

## 📸 Preview

<!-- Add screenshots here after first release -->
*Screenshots and demo GIFs will be added after first release*

## ✨ Features

### 🎯 Core Functionality
- **Cross-platform**: Works seamlessly on Windows, macOS, and Linux
- **Multiple Schedule Types**: Cron expressions, intervals, one-time tasks, and startup tasks
- **Immediate Execution**: Run any task instantly for testing and debugging
- **Task Management**: Full CRUD operations (Create, Read, Update, Delete)
- **Execution History**: Complete logging with stdout, stderr, and exit codes
- **Error Handling**: Robust timeout management and error reporting

### 🖥️ User Interface
- **Modern GUI**: Clean, responsive Electron-based desktop interface
- **Task Dashboard**: Visual status indicators and real-time updates
- **Easy Task Creation**: Intuitive forms with validation and helpful examples
- **Execution Monitoring**: Detailed execution history with searchable logs
- **Theme Support**: Light and dark mode support

### 🔧 Technical Features
- **RESTful API**: Complete HTTP API for integration and automation
- **SQLite Database**: Lightweight, file-based data persistence
- **System Notifications**: Native OS notifications for task completion/failure
- **Configurable Timeouts**: Per-task execution time limits
- **JSON Configuration**: Easy import/export of task configurations

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** - Backend API and task execution
- **Node.js 16+** - Frontend GUI and build tools
- **Git** - Version control (for development)

### Option 1: Quick Demo (Recommended)
```bash
# Clone and setup
git clone https://github.com/0x-Decrypt/task-scheduler.git
cd task-scheduler
chmod +x setup.sh demo.sh start.sh

# Install dependencies and run demo
./setup.sh
./start.sh &      # Starts backend in background
./demo.sh         # Interactive demo
```

### Option 2: Manual Installation
```bash
# 1. Clone repository
git clone https://github.com/0x-Decrypt/task-scheduler.git
cd task-scheduler

# 2. Install dependencies
npm install
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# 3. Start backend API
python backend/simple_api.py &

# 4. Start frontend GUI
npm run dev
```

### Option 3: Production Build
```bash
# Build executables for distribution
chmod +x build.sh
./build.sh

# Run the built application
cd dist/task-scheduler
./start.sh  # Linux/macOS
# or start.bat  # Windows
```

## 📋 Usage Examples

### Creating Tasks via API
```bash
# Create a daily backup task
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Backup",
    "description": "Backup important files",
    "command": "rsync -av ~/Documents ~/Backup/",
    "schedule_type": "cron",
    "schedule_config": {"expression": "0 2 * * *"},
    "timeout": 3600
  }'

# Create an interval-based system monitor
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "System Monitor",
    "command": "df -h && free -h",
    "schedule_type": "interval",
    "schedule_config": {"minutes": 15}
  }'

# Run a task immediately
curl -X POST "http://localhost:8000/tasks/{task-id}/run"
```

### Schedule Types
| Type | Description | Configuration Example |
|------|-------------|----------------------|
| `cron` | Traditional cron expressions | `{"expression": "0 9 * * MON-FRI"}` |
| `interval` | Fixed time intervals | `{"hours": 2, "minutes": 30}` |
| `once` | Single execution at specific time | `{"run_date": "2025-12-31T23:59:59"}` |
| `startup` | Run when scheduler starts | `{}` |

### Common Cron Expressions
```bash
0 0 * * *          # Daily at midnight
0 9 * * MON-FRI    # Weekdays at 9 AM
0 0 1 * *          # First day of each month
0 */6 * * *        # Every 6 hours
*/15 * * * *       # Every 15 minutes
```

## 🏗️ Architecture

### Project Structure
```
task-scheduler/
├── backend/                 # Python FastAPI backend
│   ├── simple_api.py       # Main API application
│   ├── models.py           # Data models and validation
│   ├── database.py         # Database configuration
│   └── requirements.txt    # Python dependencies
├── frontend/               # Electron desktop GUI
│   └── src/
│       ├── main.js         # Electron main process
│       ├── index.html      # Main application UI
│       ├── styles.css      # Application styling
│       └── app.js          # Frontend JavaScript logic
├── tests/                  # Test suites
│   └── test_api.py        # API integration tests
├── .github/               # GitHub workflows and templates
│   ├── workflows/         # CI/CD pipelines
│   └── ISSUE_TEMPLATE/    # Issue templates
├── scripts/               # Utility scripts
│   ├── setup.sh          # Environment setup
│   ├── start.sh          # Application launcher
│   ├── demo.sh           # Interactive demonstration
│   └── build.sh          # Production build
└── docs/                 # Documentation
    ├── README.md         # This file
    ├── CONTRIBUTING.md   # Contribution guidelines
    └── CHANGELOG.md      # Version history
```

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List all tasks |
| `POST` | `/tasks` | Create new task |
| `GET` | `/tasks/{id}` | Get specific task |
| `PUT` | `/tasks/{id}` | Update task |
| `DELETE` | `/tasks/{id}` | Delete task |
| `POST` | `/tasks/{id}/run` | Execute task immediately |
| `POST` | `/tasks/{id}/toggle` | Enable/disable task |
| `GET` | `/executions` | Get all execution history |
| `GET` | `/tasks/{id}/executions` | Get task-specific history |

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python tests/test_api.py

# Run with coverage
pip install pytest pytest-cov
pytest tests/ --cov=backend --cov-report=html

# Integration testing
./demo.sh  # Interactive test of all features
```

### Manual Testing
```bash
# Test backend API directly
curl http://localhost:8000/health
curl http://localhost:8000/tasks

# Test task execution
curl -X POST "http://localhost:8000/tasks" -H "Content-Type: application/json" \
  -d '{"name":"Test","command":"echo Hello","schedule_type":"once","schedule_config":{"run_date":"2025-12-31T23:59:59"}}'
```

## 🛠️ Development

### Setting Up Development Environment
```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/task-scheduler.git
cd task-scheduler

# Create feature branch
git checkout -b feature/your-feature-name

# Install development dependencies
npm install
pip install -r backend/requirements.txt
pip install pytest pytest-cov flake8  # Development tools

# Run in development mode
python backend/simple_api.py &  # Backend with auto-reload
npm run dev                     # Frontend with DevTools
```

### Code Style
- **Python**: Follow PEP 8, use type hints, max 100 characters per line
- **JavaScript**: ES6+, 2-space indentation, semicolons required
- **General**: Meaningful names, functions ≤25 lines, comprehensive error handling

### Contributing
1. Read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines
2. Create feature branch from `main`
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit pull request with clear description

## 📦 Building and Distribution

### Create Production Build
```bash
./build.sh
```

This creates:
- Standalone executables for each platform
- Packaged application in `dist/task-scheduler/`
- Compressed archive for distribution

### System Requirements
| Platform | Minimum | Recommended |
|----------|---------|-------------|
| **Windows** | Windows 10 | Windows 11 |
| **macOS** | macOS 10.14 | macOS 12+ |
| **Linux** | Ubuntu 18.04 | Ubuntu 22.04+ |
| **Memory** | 512 MB RAM | 1 GB RAM |
| **Disk** | 100 MB free | 500 MB free |

## 🤝 Contributing

We welcome contributions! Whether you're fixing bugs, adding features, improving documentation, or reporting issues, your help makes this project better.

### Ways to Contribute
- 🐛 **Bug Reports**: Found a bug? [Create an issue](https://github.com/0x-Decrypt/task-scheduler/issues)
- 💡 **Feature Requests**: Have an idea? [Suggest a feature](https://github.com/0x-Decrypt/task-scheduler/issues)
- 📝 **Documentation**: Help improve our docs
- 🧪 **Testing**: Help test new features and report issues
- 💻 **Code**: Submit pull requests with bug fixes or new features

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- Electron for cross-platform desktop applications
- SQLite for reliable embedded database
- The open-source community for inspiration and feedback

## 📞 Support

- 📖 **Documentation**: Check the [docs](docs/) folder
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/0x-Decrypt/task-scheduler/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/0x-Decrypt/task-scheduler/discussions)
- ✉️ **Contact**: Open an issue for questions or feedback

## 🏆 Author

**0x-Decrypt**
- GitHub: [@0x-Decrypt](https://github.com/0x-Decrypt)
- Repository: [task-scheduler](https://github.com/0x-Decrypt/task-scheduler)

---

⭐ **Star this repository if you find it useful!** ⭐

*Built with ❤️ for the open-source community*
