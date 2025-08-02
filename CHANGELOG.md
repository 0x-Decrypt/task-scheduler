# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and core functionality
- FastAPI backend with SQLite database
- Electron-based desktop GUI
- Task creation, editing, and deletion
- Multiple schedule types (cron, interval, once, startup)
- Immediate task execution
- Execution history tracking
- Cross-platform compatibility
- System notifications support
- Dark/light theme support

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- Input validation for all API endpoints
- Sanitized command execution

## [1.0.0] - 2025-08-02

### Added
- Initial release of Task Scheduler
- Core scheduling functionality with multiple schedule types
- Modern web-based GUI built with Electron
- RESTful API for task management
- SQLite database for data persistence
- Task execution with timeout support
- Comprehensive logging and error handling
- Cross-platform support (Windows, macOS, Linux)
- Import/export functionality for task configurations
- System tray integration
- Notification system for task completion/failure

### Features
- **Task Management**: Create, edit, delete, enable/disable tasks
- **Schedule Types**: 
  - Cron expressions for complex scheduling
  - Interval-based scheduling (seconds, minutes, hours)
  - One-time execution at specific date/time
  - Startup execution
- **Execution Engine**: 
  - Immediate task execution
  - Configurable timeouts
  - Output capture (stdout/stderr)
  - Exit code tracking
- **User Interface**:
  - Clean, modern design
  - Task list with status indicators
  - Task creation/editing forms
  - Execution history viewer
  - Settings panel
- **Integration**:
  - System notifications
  - System tray support
  - Auto-start capabilities

### Technical Details
- **Backend**: Python 3.8+ with FastAPI
- **Frontend**: Electron with HTML/CSS/JavaScript
- **Database**: SQLite for lightweight data storage
- **Packaging**: Cross-platform executables
- **Dependencies**: Minimal external dependencies for security

### Known Issues
- None at initial release

---

**Repository**: https://github.com/0x-Decrypt/task-scheduler
**Author**: 0x-Decrypt
