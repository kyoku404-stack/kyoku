# KEEP — Developer Onboarding & Environment Setup Guide (docs/onboarding-guide.md)

> **Step-by-Step Local Setup Guide for KEEP Developers & Autonomous Agents**  
> *Owner: Member 1 (Project Lead & AI Architect)*

---

## 1. Prerequisites

Ensure your machine has the following installed:
- **Operating System**: Windows 11, Ubuntu 22.04+, or macOS Sonoma+
- **Git**: Latest Stable
- **Python**: 3.12+
- **Node.js**: 22 LTS & npm
- **Docker Desktop**: Latest version with Compose v2
- **PostgreSQL Client**: `psql` (optional for direct querying)

---

## 2. Quickstart Step-by-Step

### Step 1: Clone the Repository
```bash
git clone <repository_url> keep
cd keep
```

### Step 2: Environment Configuration
Copy the template `.env.example` into `.env`:
```bash
cp .env.example .env
```
*(Windows PowerShell: `Copy-Item .env.example .env`)*

Review `.env` and configure credentials if running services outside Docker.

### Step 3: Start Services via Docker Compose
To launch the full local environment (PostgreSQL 16 with pgvector, Redis, Backend, and Frontend):
```bash
docker-compose up -d --build
```

Verify running containers:
```bash
docker-compose ps
```

---

## 3. Local Development (Without Docker)

### Backend (FastAPI)
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run FastAPI development server:
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Access OpenAPI Swagger documentation at: `http://localhost:8000/docs`

### Frontend (React / Vite / Next.js)
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Access Frontend at: `http://localhost:3000` (or `http://localhost:5173`)

---

## 4. Running Verification Test Suites

### Backend Unit & Integration Tests:
```bash
pytest tests/unit/
pytest tests/integration/
```

### Frontend Tests & Type Checking:
```bash
cd frontend
npm test
npm run build
```

---

## 5. Standard Ports & Service Topology

| Service | Port | Local Endpoint | Notes |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend** | `8000` | `http://localhost:8000` | REST API & Swagger UI (`/docs`) |
| **Frontend Web App**| `3000` / `5173` | `http://localhost:3000` | Web user interface |
| **PostgreSQL 16**   | `5432` | `localhost:5432` | Relational DB + pgvector |
| **Redis**           | `6379` | `localhost:6379` | Task queue & cache broker |
