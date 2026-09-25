# Setup & Run

## Prerequisites

- Python 3.10
- Node.js
- PostgreSQL with pgvector
- Redis
- Git
- `uv`

## 1. Clone the repository

    git clone https://github.com/KartikayBhardwaj-dev/INQUIREA.git
    cd INQUIREA

## 2. Install uv

### macOS / Linux

    curl -LsSf https://astral.sh/uv/install.sh | sh

### Windows

    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

Restart your terminal after installation if `uv` is not recognized.

Verify:

    uv --version

## 3. Create the Python environment

    uv venv --python 3.10

Activate it if you want to use the environment directly:

### macOS / Linux

    source .venv/bin/activate

### Windows

    .venv\Scripts\activate

## 4. Install Python dependencies

All backend dependencies are defined in `pyproject.toml` and locked in `uv.lock`.

    uv sync

Do not use `pip install -r requirements.txt`.

## 5. Configure environment variables

Create the backend environment file:

    cp .env.example .env

Fill in the required values in `.env`, including:

- PostgreSQL / Supabase database URL
- Google OAuth credentials
- Groq API key
- Redis URL
- LangSmith credentials if tracing is enabled
- Celery configuration

Never commit `.env`.

## 6. Run database migrations

    uv run alembic upgrade head

## 7. Frontend setup

Open a separate terminal:

    cd frontend
    npm install
    cp .env.example .env

The frontend `.env` should contain:

    NEXT_PUBLIC_API_URL=http://localhost:8000

## 8. Start the application

INQUIREA requires three processes.

### Terminal 1 — FastAPI backend

From the project root:

    uv run python main.py

Backend:

    http://localhost:8000

Health check:

    http://localhost:8000/health

### Terminal 2 — Celery worker

From the project root:

    uv run celery -A backend.app.celery_app worker --loglevel=info --concurrency=5

### Terminal 3 — Next.js frontend

From the project root:

    cd frontend
    npm run dev

Frontend:

    http://localhost:3000

## 9. Development workflow

After the initial setup, start the backend with:

    uv run python main.py

Start Celery with:

    uv run celery -A backend.app.celery_app worker --loglevel=info --concurrency=5

Start the frontend with:

    cd frontend
    npm run dev

`npm install` is only required when dependencies need to be installed or updated.

## 10. Recreate the Python environment

If the Python environment becomes corrupted or dependencies need to be reinstalled:

    rm -rf .venv
    uv venv --python 3.10
    uv sync

On Windows, remove `.venv` manually and run:

    uv venv --python 3.10
    uv sync

## 11. Dependency management

Add a Python dependency:

    uv add <package-name>

Remove a Python dependency:

    uv remove <package-name>

Synchronize the environment:

    uv sync

Update the lock file and dependencies:

    uv lock

The project uses `pyproject.toml` for dependency configuration and `uv.lock` for reproducible dependency resolution.

## 12. Project URLs

Frontend:

    http://localhost:3000

Backend:

    http://localhost:8000

API health:

    http://localhost:8000/health

FastAPI documentation:

    http://localhost:8000/docs
