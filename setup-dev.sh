#!/bin/bash

# Metra Development Environment Setup Script
# This script helps set up the complete development environment for Metra

echo "🚀 Setting up Metra development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "Metra_PRD.md" ]; then
    echo -e "${RED}Error: Please run this script from the Metra project root directory${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3.10; then
    echo -e "${RED}Error: Python 3.10 is required but not installed${NC}"
    echo "Please install Python 3.10 first"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}Error: Node.js is required but not installed${NC}"
    echo "Please install Node.js 18+ first"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}Error: npm is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites installed${NC}"

# 2. Setup Backend
echo -e "\n${YELLOW}Setting up backend...${NC}"

cd metra-backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3.10 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp example.env .env
    echo -e "${YELLOW}⚠️  Please update .env with your actual API keys${NC}"
fi

echo -e "${GREEN}✓ Backend setup complete${NC}"

# 3. Setup Frontend
echo -e "\n${YELLOW}Setting up frontend...${NC}"

cd ../metra-ai-factory-main

# Install dependencies
echo "Installing Node dependencies..."
npm install

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"

# 4. Create startup scripts
cd ..

# Backend startup script
cat > start-backend.sh << 'EOF'
#!/bin/bash
cd metra-backend
source venv/bin/activate
echo "Starting FastAPI server..."
INNGEST_DEV=1 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF

# Frontend startup script
cat > start-frontend.sh << 'EOF'
#!/bin/bash
cd metra-ai-factory-main
echo "Starting Vite dev server..."
npm run dev
EOF

# Inngest startup script
cat > start-inngest.sh << 'EOF'
#!/bin/bash
echo "Starting Inngest Dev Server..."
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
EOF

# Make scripts executable
chmod +x start-backend.sh start-frontend.sh start-inngest.sh

# 5. Print success message
echo -e "\n${GREEN}✅ Development environment setup complete!${NC}"
echo -e "\n${YELLOW}To start development:${NC}"
echo "1. Terminal 1: ./start-backend.sh"
echo "2. Terminal 2: ./start-frontend.sh"
echo "3. Terminal 3: ./start-inngest.sh"
echo -e "\n${YELLOW}Important:${NC}"
echo "- Update metra-backend/.env with your API keys"
echo "- Backend API: http://localhost:8000"
echo "- Frontend: http://localhost:5173"
echo "- API Docs: http://localhost:8000/docs"
echo -e "\n${GREEN}Happy coding! 🎉${NC}" 