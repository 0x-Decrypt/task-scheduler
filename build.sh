#!/bin/bash

# Task Scheduler Build Script

set -e

echo "🏗️  Building Task Scheduler..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/
rm -rf build/
rm -rf frontend/dist/

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Install Python dependencies
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r backend/requirements.txt

# Install build dependencies
pip install pyinstaller

# Run tests
echo "🧪 Running tests..."
if [ -f "tests/test_api.py" ]; then
    python tests/test_api.py
else
    echo "⚠️  No tests found, skipping..."
fi

# Build backend executable
echo "🔧 Building backend executable..."
cd backend
pyinstaller --onefile --name task-scheduler-backend simple_api.py
cd ..

# Build frontend
echo "🖥️  Building frontend..."
npm run build

# Package application
echo "📦 Packaging application..."
mkdir -p dist/task-scheduler

# Copy backend executable
cp backend/dist/task-scheduler-backend dist/task-scheduler/

# Copy frontend files
cp -r frontend/src/* dist/task-scheduler/
cp package.json dist/task-scheduler/

# Copy documentation
cp README.md dist/task-scheduler/
cp LICENSE dist/task-scheduler/
cp CHANGELOG.md dist/task-scheduler/

# Create start scripts
cat > dist/task-scheduler/start.sh << 'EOF'
#!/bin/bash
echo "Starting Task Scheduler..."
./task-scheduler-backend &
BACKEND_PID=$!
sleep 2
npm start
kill $BACKEND_PID 2>/dev/null
EOF

cat > dist/task-scheduler/start.bat << 'EOF'
@echo off
echo Starting Task Scheduler...
start /B task-scheduler-backend.exe
timeout /t 2 /nobreak >nul
npm start
taskkill /f /im task-scheduler-backend.exe >nul 2>&1
EOF

chmod +x dist/task-scheduler/start.sh

# Create archive
echo "📦 Creating distributable archive..."
cd dist
tar -czf task-scheduler-$(date +%Y%m%d).tar.gz task-scheduler/
cd ..

echo "✅ Build complete!"
echo "📁 Distributable package: dist/task-scheduler-$(date +%Y%m%d).tar.gz"
echo ""
echo "To test the build:"
echo "  cd dist/task-scheduler"
echo "  ./start.sh  (Linux/macOS)"
echo "  start.bat   (Windows)"
