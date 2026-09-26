# MindBridge: AI-Powered Cognitive Engagement & Memory Assistance Platform

MindBridge is an adaptive cognitive engagement platform supporting three differentiated experiences:
* **Elder Experience:** High-contrast, low cognitive load, accessible reminiscence and cognitive engagement.
* **Child Experience:** Goal-oriented attention and working-memory activities with structured progression.
* **Caregiver Dashboard:** Dependent management, progress monitoring, and memory verification.

> **Positioning Notice:** The initial platform baseline provides cognitive support and engagement. It does **not** provide clinical diagnosis or automated medical treatment recommendations.

---

## 1. System Architecture

The platform is architected as a **Modular Monolith** (ADR-001):
* **Web Frontend (`apps/web`):** Next.js (App Router), React, TypeScript, Tailwind CSS.
* **Backend API (`apps/api`):** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x.
* **Primary Database:** PostgreSQL 16 with `pgvector` for semantic memory retrieval.
* **Cache & Rate Limiting:** Redis 7.
* **Infrastructure:** Docker Compose for reproducible local development.

---

## 2. Prerequisites

* **Node.js:** `v20+` or `v24+` (`npm v10+`)
* **Python:** `3.11+` (`3.14.7` supported)
* **Docker Engine & Docker Compose:** Docker `24+` / Compose `v2+`

---

## 3. Quickstart & Local Setup

### Step 1: Clone and Configure Environment
```bash
# Copy the environment configuration template
cp .env.example .env
```

### Step 2: Start Infrastructure Services (PostgreSQL + pgvector & Redis)
```bash
docker compose up -d
```
Verify that services are running and healthy:
```bash
docker compose ps
```

### Step 3: Backend API Setup (`apps/api`)
```bash
cd apps/api

# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run development server
uvicorn app.main:app --reload --port 8000
```
Backend health check endpoints:
* **Liveness:** `http://localhost:8000/health/live`
* **Readiness:** `http://localhost:8000/health/ready`
* **Interactive OpenAPI Docs:** `http://localhost:8000/docs`

### Step 4: Frontend Web App Setup (`apps/web`)
```bash
cd apps/web

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 4. Troubleshooting & Common Issues

### Docker Socket Permission Denied
If `docker compose up` returns:
```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```
Grant your Linux user access to the `docker` group:
```bash
sudo usermod -aG docker $USER
```
Then refresh your shell session with `newgrp docker` or log out and log back in.

### Database Connection Issues
Ensure the PostgreSQL container is reporting healthy before launching the backend:
```bash
docker compose logs postgres
```

---

## 5. Security & Verification Rules
* **Never commit secrets:** Real credentials, `.env` files, and private keys are ignored by `.gitignore`.
* **Server authority:** Game scoring, session states, difficulty adaptation, and memory verification remain authoritative on the server.
* **Accessibility:** Elder interfaces adhere to WCAG 2.1 AA with touch targets $\ge 48\text{px}$.
