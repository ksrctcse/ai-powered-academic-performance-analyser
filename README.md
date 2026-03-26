
# Phase 1 – AI Driven Academic Workload & Progress System

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
