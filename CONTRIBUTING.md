# Contributing to Task Scheduler

Thank you for your interest in contributing to Task Scheduler! This document provides guidelines for contributing to this open-source project.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- Git

### Setup Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/task-scheduler.git
cd task-scheduler
```

3. Set up the development environment:
```bash
chmod +x setup.sh
./setup.sh
```

4. Start the application:
```bash
./start.sh
```

## Development Workflow

### Code Style Guidelines

#### Python Backend
- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Write docstrings for all public functions and classes

#### JavaScript Frontend
- Use ES6+ features consistently
- Use 2 spaces for indentation
- Use const/let instead of var
- Use meaningful variable names
- Follow consistent async/await patterns

### Project Structure
```
task-scheduler/
├── backend/              # Python FastAPI backend
│   ├── simple_api.py    # Main API application
│   ├── models.py        # Data models
│   ├── database.py      # Database utilities
│   └── services/        # Business logic
├── frontend/            # Electron GUI
│   └── src/            # HTML/CSS/JS source
├── tests/              # Test suites
└── docs/               # Documentation
```

## Making Contributions

### Reporting Issues
- Use the GitHub issue tracker
- Provide clear reproduction steps
- Include system information (OS, Python version, Node.js version)
- Add relevant logs and error messages

### Submitting Pull Requests

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes following the coding standards
3. Add or update tests as needed
4. Ensure all tests pass:
```bash
npm test
```

5. Update documentation if needed
6. Commit your changes with clear commit messages
7. Push to your fork and submit a pull request

### Commit Message Format
```
type: brief description

Longer description if needed

- List specific changes
- Reference issues with #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Code Quality Standards

### Testing
- Write unit tests for new features
- Maintain test coverage above 80%
- Test across different operating systems when possible
- Include integration tests for API endpoints

### Documentation
- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update API documentation for endpoint changes
- Include examples in documentation

### Performance
- Keep functions under 25 lines when possible
- Use efficient algorithms and data structures
- Minimize memory usage for long-running processes
- Profile code for performance bottlenecks

## Review Process

### Pull Request Reviews
- All PRs require at least one review
- Address all reviewer feedback
- Keep PRs focused on a single feature/fix
- Squash commits before merging when appropriate

### Maintainer Guidelines
- Be respectful and constructive in reviews
- Focus on code quality and project goals
- Help contributors improve their submissions
- Respond to PRs within 48 hours when possible

## Release Process

### Version Numbering
We follow Semantic Versioning (SemVer):
- MAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist
- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Build and test executables
- [ ] Create GitHub release
- [ ] Update documentation

## Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and contribute
- Maintain a welcoming environment

### Getting Help
- Check existing issues and documentation first
- Ask questions in GitHub discussions
- Be patient and respectful when asking for help
- Provide context and details in questions

## Recognition

Contributors will be:
- Listed in the project README
- Credited in release notes
- Invited to join the maintainer team for significant contributions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Task Scheduler! Your efforts help make this project better for everyone.

**Maintained by**: 0x-Decrypt
**Repository**: https://github.com/0x-Decrypt/task-scheduler
