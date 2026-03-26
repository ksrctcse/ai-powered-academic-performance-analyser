
# Phase 1 – AI Driven Academic Workload & Progress System

## Clone repo into local in terminal / command prompt. Before cloning install github desktop / github cli

git clone https://github.com/ksrctcse/ai-powered-academic-performance-analyser.git

After cloning run the migrations using the below commands:
Install python3 
  # If windows download python3 from the python website and set the PATH accordingly
  # If mac use brew install python3
Install Postgres
  # 🐘 Install PostgreSQL on Windows
🔽 1. Download PostgreSQL
Go to the official site: PostgreSQL
Download the Windows installer (by EnterpriseDB)
⚙️ 2. Run the Installer

During setup:

You’ll be asked to configure:
Installation Directory → keep default
Components → ensure:
✅ PostgreSQL Server
✅ pgAdmin (GUI tool)
Password → set a password for user postgres ⚠️ remember this
Port → default is 5432 (keep it unless conflict)
🧪 3. Verify Installation

After installation:

Option A: Using Command Prompt
psql -U postgres

Enter your password → you should see:

postgres=#


**Then run the below migration for the first time. ** 
cd backend
python run_migrations.py up

## Features
- Staff Signup & Login (JWT)
- Department → Subject → Unit → Concept hierarchy
- Syllabus upload & AI analysis
- Concept complexity analysis
- Concept progress update
- AI-based unit progress calculation
- AI-based task generation
- PrimeReact frontend
- Interactive Swagger API documentation

## Run Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### API Documentation
The backend includes interactive Swagger UI documentation:

- **Swagger UI (Interactive)**: http://localhost:8000/docs
- **ReDoc (Alternative UI)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

#### Available API Endpoints:

**Authentication**
- `POST /auth/signup` - Register a new staff member
- `POST /auth/login` - Login and get JWT token

**Syllabus Management**
- `POST /syllabus/upload` - Upload and analyze syllabus documents

**Progress Tracking**
- `POST /progress/concept` - Update concept progress and calculate unit progress

**Task Generation**
- `POST /tasks/generate` - Generate AI-powered learning tasks

## Run Frontend
```bash
cd frontend
npm install
npm run dev
```
