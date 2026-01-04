# ElectroMart Multi-Agent System

A production-ready intelligent customer support system powered by LangGraph, FastAPI, and Next.js with real-time communication capabilities.

## Overview

ElectroMart is a sophisticated multi-agent system that uses AI to handle customer inquiries across different domains (Sales, Marketing, Support, Logistics) with seamless agent handoffs and real-time communication.

## Technology Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **LangGraph** - Agent orchestration and workflow management
- **LangChain** - LLM integration and tooling
- **OpenAI GPT-4** - Language model for agent intelligence
- **Socket.IO** - Real-time bidirectional communication
- **SQLAlchemy** - ORM for database operations
- **Redis** - Session persistence and caching (optional)
- **SQLite/PostgreSQL** - Database storage
- **TextBlob** - Sentiment analysis
- **Pytest** - Testing framework

### Frontend
- **Next.js 16** - React framework with server-side rendering
- **React 19** - Modern UI library
- **TypeScript** - Type-safe development
- **Material-UI (MUI) v5** - Component library
- **Emotion** - CSS-in-JS styling
- **Socket.IO Client** - Real-time communication

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **npm or yarn** - Comes with Node.js
- **Redis** (Optional) - [Installation Guide](https://redis.io/docs/getting-started/)
- **PostgreSQL** (Optional) - [Download](https://www.postgresql.org/download/)

**Required:**
- OpenAI API Key - [Get one here](https://platform.openai.com/api-keys)

## Quick Start

### Option 1: Automated Setup (Recommended)

Run the setup script to install all dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

Then configure your environment:
```bash
# Edit .env and add your OPENAI_API_KEY
nano .env

# Edit backend/.env if needed
nano backend/.env.example
cp backend/.env.example backend/.env
```

### Option 2: Manual Setup

#### 1. Clone and Navigate
```bash
cd ElectromartAgent
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download TextBlob corpora (for sentiment analysis)
python -m textblob.download_corpora

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
nano .env
```

#### 3. Frontend Setup

```bash
# Navigate to frontend directory (from root)
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit if you need to change the backend URL (default: http://localhost:8000)
```

#### 4. Configure Environment Variables

**Backend (.env or backend/.env):**
```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Database (SQLite by default, no additional setup needed)
DATABASE_URL=sqlite:///./data/electromart.db

# Optional: Redis for session persistence
REDIS_URL=redis://localhost:6379/0

# Optional: LangSmith for tracing
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=ls__your-key-here
LANGCHAIN_PROJECT=electromart-agents

# Server settings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000

# Security
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_SOCKET_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Start Redis (Optional but Recommended)

If you have Redis installed:
```bash
# In a new terminal
redis-server

# Or using make
make redis
```

### Start Backend Server

```bash
# In a new terminal
cd backend
source venv/bin/activate  # On macOS/Linux
python -m backend.main

# Or using make (from root directory)
make backend
```

Backend will start at: **http://localhost:8000**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Start Frontend Server

```bash
# In a new terminal
cd frontend
npm run dev

# Or using make (from root directory)
make frontend
```

Frontend will start at: **http://localhost:3000**

## Using Make Commands

The project includes a comprehensive Makefile for common tasks:

```bash
make help              # Show all available commands
make install           # Install all dependencies
make setup             # Initial project setup
make backend           # Run backend server
make frontend          # Run frontend server
make test              # Run all tests
make test-coverage     # Run tests with coverage
make lint              # Check code style
make format            # Format code with black
make db-seed           # Seed database with mock data
make health            # Check service health
make status            # Check if services are running
make clean             # Clean generated files
make info              # Show project information
```

## Project Structure

```
ElectromartAgent/
├── backend/
│   ├── agents/              # Agent implementations (Sales, Marketing, Support, Logistics)
│   ├── api/                 # FastAPI routes and Socket.IO handlers
│   ├── core/                # Core business logic and constants
│   ├── database/            # Database models and migrations
│   ├── graph/               # LangGraph workflow definitions
│   ├── knowledge/           # Knowledge bases for each agent (JSON)
│   ├── schemas/             # Pydantic models for validation
│   ├── services/            # Business services
│   ├── utils/               # Utilities (logging, config, analytics, etc.)
│   ├── tests/               # Test suite
│   ├── main.py              # Application entry point
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── app/                 # Next.js app directory
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   └── lib/             # Utilities and Socket.IO setup
│   ├── public/              # Static assets
│   ├── next.config.mjs      # Next.js configuration
│   ├── package.json         # Node dependencies
│   └── tsconfig.json        # TypeScript configuration
│
├── .env.example             # Environment variables template
├── setup.sh                 # Automated setup script
├── Makefile                 # Development commands
└── README.md                # This file
```

## Development

### Backend Development

```bash
# Run with auto-reload
cd backend
source venv/bin/activate
python -m backend.main

# Run tests
pytest

# Run tests with coverage
pytest --cov=backend --cov-report=html

# Format code
black .

# Type checking
mypy backend --ignore-missing-imports
```

### Frontend Development

```bash
cd frontend

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint
```

## Key Features

### Multi-Agent System
- **Sales Agent** - Product recommendations, pricing, promotions
- **Marketing Agent** - Campaigns, branding, content
- **Support Agent** - Technical issues, troubleshooting
- **Logistics Agent** - Shipping, tracking, delivery

### Advanced Capabilities
- Intelligent agent routing based on query intent
- Seamless agent handoffs when expertise changes
- Real-time bidirectional communication via Socket.IO
- Session persistence with Redis
- Sentiment analysis for customer messages
- Conversation analytics and metrics
- Human handoff detection for escalations
- Message deduplication and rate limiting

### Real-time Communication
- Live typing indicators
- Agent status updates
- Instant message delivery
- Connection state management
- Automatic reconnection handling

## API Endpoints

### REST API
- `GET /health` - Health check
- `GET /metrics` - System metrics
- `GET /analytics/agents` - Agent analytics
- `GET /docs` - Interactive API documentation

### WebSocket Events (Socket.IO)
- `connect` - Client connection
- `disconnect` - Client disconnection
- `user_message` - User sends message
- `agent_message` - Agent responds
- `agent_handoff` - Agent transfer notification
- `typing_indicator` - Typing status
- `error` - Error notifications

## Database

### SQLite (Default)
No additional setup required. Database file is created automatically at `backend/data/electromart.db`.

### PostgreSQL (Optional)
If you prefer PostgreSQL:

1. Install PostgreSQL
2. Create database:
   ```bash
   createdb electromart
   ```
3. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/electromart
   ```

### Seed Database
```bash
make db-seed
# Or
cd backend
python -m backend.database.seed
```

## Testing

### Run All Tests
```bash
cd backend
pytest
```

### Run Specific Test Types
```bash
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest tests/test_*.py      # Specific test file
```

### Coverage Report
```bash
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or change port in backend/.env
BACKEND_PORT=8001
```

**OpenAI API errors:**
- Verify your `OPENAI_API_KEY` in `.env`
- Check you have API credits: https://platform.openai.com/account/usage
- Ensure you're using a valid model name

**Redis connection failed:**
- Redis is optional; system will work without it
- Start Redis: `redis-server`
- Check Redis is running: `redis-cli ping`

**Module not found:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**Port 3000 already in use:**
```bash
# Change port in package.json
"dev": "next dev -p 3001"
```

**Socket connection failed:**
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_SOCKET_URL` in `.env.local`
- Verify CORS settings in backend `.env`

**Module not found:**
```bash
cd frontend
rm -rf node_modules package-lock.json .next
npm install
```

### Check Service Status
```bash
make status
```

## Production Deployment

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend
```bash
cd frontend
npm run build
npm start
```

### Environment Variables
- Set `ENVIRONMENT=production` in `.env`
- Use strong `JWT_SECRET`
- Configure proper `CORS_ORIGINS`
- Use PostgreSQL for production database
- Enable Redis for session persistence
- Set up proper logging and monitoring

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics
```bash
curl http://localhost:8000/metrics | python -m json.tool
```

### Agent Analytics
```bash
curl http://localhost:8000/analytics/agents | python -m json.tool
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Next.js Documentation](https://nextjs.org/docs)
- [Material-UI Documentation](https://mui.com)
- [Socket.IO Documentation](https://socket.io/docs/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## License

MIT License

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review troubleshooting section

---

**Happy coding!** Built with FastAPI, LangGraph, and Next.js.
