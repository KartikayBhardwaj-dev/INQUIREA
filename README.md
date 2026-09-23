# INQUIREA

# Setup & Run

## 1. Clone Repository

git clone https://github.com/KartikayBhardwaj-dev/INQUIREA.git
cd INQUIREA

## 2. Backend Setup

# Requires Python 3.10 and uv

uv sync

# Create environment file
cp .env.example .env

# Configure .env with your credentials and local services.

## 3. Database

# Run migrations if required
uv run alembic upgrade head

## 4. Frontend Setup

cd frontend

npm install

cp .env.example .env

# Start frontend
npm run dev

# Frontend:
# http://localhost:3000

## 5. Start Backend

# Open a new terminal
cd INQUIREA

uv run python main.py

# Backend:
# http://localhost:8000

# Health check:
# http://localhost:8000/health

## 6. Start Celery Worker

# Open another terminal
cd INQUIREA

uv run celery -A backend.app.celery_app worker --loglevel=info --concurrency=5

## Running the Application

# Terminal 1 — Backend
cd INQUIREA
uv run python main.py

# Terminal 2 — Celery Worker
cd INQUIREA
uv run celery -A backend.app.celery_app worker --loglevel=info --concurrency=5

# Terminal 3 — Frontend
cd INQUIREA/frontend
npm install
npm run dev

# Open:
# http://localhost:3000
