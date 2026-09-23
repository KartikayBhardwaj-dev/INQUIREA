# INQUIREA

Getting Started

Prerequisites

Make sure you have the following installed:

* Python 3.10
* uv
* Node.js and npm
* PostgreSQL with the pgvector extension
* Redis
* A Google Cloud project with Gmail API enabled
* A Groq API key
* Optional: LangSmith account for tracing and evaluation

⸻

1. Clone the Repository

git clone https://github.com/KartikayBhardwaj-dev/INQUIREA.git
cd INQUIREA

⸻

2. Backend Setup

INQUIREA uses uv for Python environment and dependency management.

The Python version is pinned to Python 3.10 in pyproject.toml.

Create/sync the virtual environment and install all dependencies:

uv sync

uv reads the dependencies directly from pyproject.toml and creates the project’s .venv automatically.

Verify the Python version:

uv run python --version

Expected:

Python 3.10.x

⸻

3. Environment Variables

Create the backend environment file:

cp .env.example .env

Open .env and configure the required values:

APP_NAME=Inquirea
APP_ENV=development
DEBUG=false
DATABASE_URL=
CHECKPOINT_DATABASE_URL=
SECRET_KEY=
SESSION_SECRET_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GROQ_API_KEY=
REDIS_URL=
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=INQUIREA
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

Do not commit .env to Git.

The repository contains .env.example only as a configuration template.

⸻

4. Database

INQUIREA uses PostgreSQL with pgvector for persistent application data and vector-based email retrieval.

Configure the PostgreSQL connection strings in .env:

DATABASE_URL=your_database_url
CHECKPOINT_DATABASE_URL=your_checkpoint_database_url

Make sure the required PostgreSQL database and pgvector extension are available before starting the application.

If database migrations are required for your local setup, run:

uv run alembic upgrade head

⸻

5. Redis

Redis is used for background task processing and Celery.

Make sure Redis is running locally or provide a remote Redis URL:

REDIS_URL=your_redis_url
CELERY_BROKER_URL=your_redis_url
CELERY_RESULT_BACKEND=your_redis_url

For a local Redis installation, the default URL is commonly:

redis://localhost:6379/0

⸻

6. Google OAuth / Gmail API

INQUIREA connects to Gmail through Google OAuth.

Create OAuth credentials in Google Cloud and configure:

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

The application requests Gmail permissions for:

* Reading emails
* Modifying emails
* Sending emails

Make sure the OAuth redirect URI configured in Google Cloud matches the callback URL used by the application.

⸻

7. Start the Backend

From the project root:

uv run python main.py

The backend runs locally on the configured application port.

You can also verify the health endpoint:

http://localhost:8000/health

⸻

8. Start Celery

Celery runs separately from the FastAPI application.

Open a second terminal and from the project root run:

uv run celery -A backend.app.celery_app worker --loglevel=info --concurrency=5

Keep this terminal running while using the application.

Celery is responsible for background email-processing tasks and asynchronous workloads.

⸻

9. Frontend Setup

Open a third terminal:

cd frontend

Install the frontend dependencies:

npm install

Create the frontend environment file:

cp .env.example .env

The default local configuration is:

NEXT_PUBLIC_API_URL=http://localhost:8000

Start the Next.js development server:

npm run dev

The frontend will normally be available at:

http://localhost:3000

⸻

10. Running the Complete Application

INQUIREA requires three processes during local development.

Terminal 1 — Backend

From the project root:

uv run python main.py

Terminal 2 — Celery Worker

From the project root:

uv run celery -A backend.app.celery_app worker --loglevel=info --concurrency=5

Terminal 3 — Frontend

cd frontend
npm install
npm run dev

Then open:

http://localhost:3000

⸻

Project Structure

INQUIREA/
├── backend/
│   └── app/
│       ├── agents/
│       ├── api/
│       ├── auth/
│       ├── core/
│       ├── database/
│       ├── memory/
│       ├── models/
│       ├── repositories/
│       ├── schemas/
│       ├── services/
│       ├── tasks/
│       ├── tools/
│       └── workflows/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── stores/
│   │   └── utils/
│   ├── package.json
│   └── .env.example
│
├── alembic/
├── docs/
├── main.py
├── pyproject.toml
├── uv.lock
├── .env.example
└── README.md

Development Notes

Python dependencies

Python dependencies are managed through:

pyproject.toml

and locked with:

uv.lock

Use:

uv sync

rather than manually installing packages with pip.

Frontend dependencies

Frontend dependencies are managed through:

frontend/package.json
frontend/package-lock.json

Install them with:

cd frontend
npm install

Local environment files

The following files are intentionally ignored by Git:

.env
frontend/.env

Use the provided templates instead:

.env.example
frontend/.env.example

⸻

Troubleshooting

Backend does not start

Verify the Python environment:

uv run python --version

Then verify the application can be imported:

uv run python -c "import backend.app"

Check that all required environment variables are configured in .env.

Celery cannot connect

Verify Redis is running and that these variables point to the correct Redis instance:

REDIS_URL=
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=

Then restart the Celery worker:

uv run celery -A backend.app.celery_app worker --loglevel=info --concurrency=5

Frontend cannot reach backend

Verify the backend is running on:

http://localhost:8000

and the frontend .env contains:

NEXT_PUBLIC_API_URL=http://localhost:8000

Restart the Next.js development server after changing environment variables.

⸻

Local Development Summary

# Terminal 1 — Backend
uv sync
uv run python main.py
# Terminal 2 — Celery
uv run celery -A backend.app.celery_app worker --loglevel=info --concurrency=5
# Terminal 3 — Frontend
cd frontend
npm install
npm run dev

Open:

http://localhost:3000
