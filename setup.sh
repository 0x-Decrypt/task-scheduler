#!/bin/bash

# Task Scheduler Setup Script

echo "🔧 Setting up Task Scheduler..."

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install Python dependencies (already done)
echo "🐍 Python dependencies already installed"

# Create basic test script
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  ./start.sh"
echo ""
echo "Or manually:"
echo "  Backend: cd backend && python -m uvicorn api.main:app --reload"
echo "  Frontend: npm run dev"
