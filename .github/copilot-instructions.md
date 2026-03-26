# Copilot Instructions for AI Academic Performance Analyzer

## Project Overview

This is a full-stack educational platform analyzing academic performance using AI. **Key architecture**: FastAPI backend with JWT authentication → PostgreSQL/SQLAlchemy ORM → Google Generative AI agents → FAISS vector store. React frontend with PrimeReact components manages authentication and workflows.

**Critical insight**: Data flows hierarchically (Department → Subject → Unit → Concept). All AI processing uses Google Generative AI models (`gemini-pro` for analysis, `embedding-001` for vectors).

---

## Backend Architecture (FastAPI)

### Database Hierarchy Pattern
- **Data Structure**: Department → Subject → Unit → Topic → Concept
- **Syllabus Model**: [app/models/syllabus.py](app/models/syllabus.py) stores hierarchical structure in `hierarchy` JSON field
- **Structure format**:
```json
{
  "course_title": "Course Name",
  "units": [
    {
      "unit_id": 1,
      "unit_name": "Unit Name",
      "description": "Description",
      "topics": [
        {
          "topic_id": 1,
          "topic_name": "Topic Name",
          "concepts": ["Concept 1", "Concept 2", "Concept 3"]
        }
      ]
    }
  ]
}
```
- **Vector Storage**: Each unit's content is indexed in FAISS for semantic search
- **Database Storage**: Full hierarchy persisted in PostgreSQL `hierarchy` JSON column

### Auth & Security Pattern
- **Location**: [app/core/security.py](app/core/security.py), [app/api/auth.py](app/api/auth.py)
- JWT token format: `Authorization: Bearer <token>`
- Extract token: `get_current_user_id()` function used across all API endpoints
- Password hashing: `werkzeug` utilities
- Staff model supports both staff and student user types with optional `roll_number` field

### API Structure
- **Router pattern**: Each API module (`auth`, `syllabus`, `progress`, `tasks`) defines its own FastAPI router with prefix
- **Error handling**: Custom exceptions return `JSONResponse` with status codes and structured messages
- **CORS**: Allows localhost:5173 and localhost:3000 (development)
- **Documentation**: Auto-generated Swagger UI at `/docs`, ReDoc at `/redoc`

### Database Layer (SQLAlchemy ORM)
- **Session management**: [app/database/session.py](app/database/session.py)
- **Models**: [app/models/staff.py](app/models/staff.py), [app/models/syllabus.py](app/models/syllabus.py)
- **Relationships**: Staff → Syllabus (one-to-many), Syllabus stores hierarchical unit→topic→concept data
- **Initialization**: `init_db()` called on app startup creates all tables

### File Processing Pattern
- **Location**: [app/utils/file_processor.py](app/utils/file_processor.py) (330 lines, well-commented)
- **Supported formats**: PDF (PyPDF2), DOCX (python-docx), CSV (pandas), TXT
- **Validation**: 50MB size limit, extension checking, empty file detection
- **Error handling**: Custom `FileProcessingError` exception with detailed messages
- **Encoding support**: UTF-8, Latin-1, cp1252 for robustness
- **Entry point**: `process_file()` routes to format-specific handlers

### AI Agents Pattern
- **Location**: [app/agents/](app/agents/) directory
- **All agents use**: `GoogleGenerativeAI(model="gemini-pro")` from `langchain_google_genai`
- **Syllabus Agent** ([app/agents/syllabus_agent.py](app/agents/syllabus_agent.py)): 
  - Extracts hierarchical structure (units → topics → concepts) from syllabus text
  - Returns JSON with `course_title` and `units` array
  - Each unit contains `topics`, each topic contains `concepts` list
  - Fallback to flat structure if parsing fails
- **Other agents** (`unit_progress_agent.py`, `task_agent.py`, `complexity_agent.py`): Follow similar `analyze(text)` pattern
- **Integration**: Agents called from API endpoints, results stored in database with hierarchy preserved

### Vector Store Pattern
- **Location**: [app/vectorstore/store.py](app/vectorstore/store.py)
- **Technology**: FAISS with Google embeddings (`embedding-001`)
- **Pattern**: Global `db` variable, lazy initialization on first `add(text)` call
- **Usage**: Syllabus content indexed for semantic search; stores course title + full text for better context

### Logging
- **Location**: [app/core/logger.py](app/core/logger.py)
- **Usage pattern**: `logger = get_logger(__name__)` in each module
- **Logs written to**: `logs/` directory
- **Log calls**: `logger.info()`, `logger.error(..., exc_info=True)` for tracebacks

---

## API Endpoints Pattern

### Authentication
```
POST /auth/signup
POST /auth/login
```

### Syllabus Management (file upload & analysis)
```
POST /syllabus/upload          # Requires Bearer token, file validation, agent analysis
GET /syllabus/list             # Lists user's syllabuses
GET /syllabus/{id}             # Single syllabus retrieval
DELETE /syllabus/{id}          # With ownership verification
```

### Progress Tracking
```
POST /progress/concept         # Updates concept progress, triggers unit progress calculation
```

### Task Generation
```
POST /tasks/generate           # AI-powered task generation
```

---

## Frontend Architecture (React)

### Syllabus Upload Component
- **Location**: [src/components/SyllabusUpload.jsx](src/components/SyllabusUpload.jsx)
- **Features**:
  - File upload with progress tracking
  - Real-time validation (extension, size)
  - Hierarchical view dialog showing units → topics → concepts
  - Display analysis summary: total units, topics, concepts
  - Integrated with PrimeReact components (FileUpload, Dialog, Badge, Divider)
- **Data structure display**:
  ```jsx
  {
    hierarchy: {
      course_title: "...",
      units: [{ unit_name, topics: [{ topic_name, concepts: [...] }] }]
    },
    analysis_summary: { total_units, total_topics, total_concepts }
  }
  ```
- **Styling**: Component-scoped CSS with stats grid, hierarchy view, and responsive design

### Auth Pattern
- **Token storage**: `localStorage` (key: `'token'`, `'user'`)
- **Initial check**: `useEffect` in [App.jsx](src/pages/App.jsx) on mount to restore session
- **Request pattern**: Include `Authorization: Bearer <token>` header in all API calls
- **Location**: [src/api/api.js](src/api/api.js) centralized API client

### Component Structure
- **Layout**: App.jsx (routing) → Login.jsx or Dashboard.jsx → SyllabusUpload.jsx
- **Styling**: Component-scoped CSS files (e.g., Login.css, Dashboard.css, SyllabusUpload.css)
- **UI Framework**: PrimeReact components with theme `lara-light-cyan`
- **Custom hooks**: `useApi` in [src/hooks/useApi.js](src/hooks/useApi.js)

### Error Handling
- **ErrorBoundary.jsx**: Catches React errors, logs structured error objects
- **Global error handlers**: `window.addEventListener` for uncaught errors and unhandled rejections in main.jsx
- **Structured logging**: All errors logged with timestamp, context, and full stack

---

## Development Workflows

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Database Initialization
- Script: [backend/setup_db.py](backend/setup_db.py)
- Runs automatically on app startup via `init_db()`
- Migrations: Check [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) for schema updates

### Testing API
- Interactive Swagger: http://localhost:8000/docs
- Health check: GET `/health`
- Test endpoints via Swagger UI directly

---

## Project-Specific Conventions

### Naming & Structure
- **API responses**: Consistent format: `{"success": bool, "message": str, "data": object}`
- **Pydantic models**: Used for request validation with `BaseModel` and `field_validator`
- **Router prefixes**: Each API module has a prefix (e.g., `/auth`, `/syllabus`)
- **Database timestamps**: All models use `created_at`, `updated_at` (UTC)

### Authentication Pattern
Every protected endpoint extracts token via:
```python
def get_current_user_id(authorization: Header):  # FastAPI Depends pattern
    # Extract "Bearer <token>", decode JWT, return user_id
```

### Agent Integration Pattern
1. Accept text input from API endpoint
2. Call `agent.analyze(text)` 
3. Parse JSON response
4. Store in database with metadata (timestamps, ownership)
5. Return structured response to client

### Error Conventions
- **Validation errors**: 400 Bad Request with field details
- **Auth errors**: 401 Unauthorized (missing/invalid token)
- **Not found**: 404
- **Server errors**: 500 with traceback in logs (never exposed to client)

---

## External Dependencies

### Critical LLM Integration
- **Model**: Google Generative AI (`gemini-pro` for text, `embedding-001` for embeddings)
- **Library**: `langchain-google-genai`
- **Required**: Valid Google API key in environment
- **Usage**: All AI analysis goes through these models

### Database
- **PostgreSQL** with `psycopg2-binary` driver
- **ORM**: SQLAlchemy with declarative base patterns

### File Handling
- **PDF**: PyPDF2 (page-by-page extraction)
- **DOCX**: python-docx
- **CSV**: pandas with openpyxl support

---

## Key Files for Reference

| Purpose | File |
|---------|------|
| API routing & middleware setup | [app/main.py](app/main.py) |
| Auth endpoints & JWT logic | [app/api/auth.py](app/api/auth.py) |
| Syllabus upload (main feature) | [app/api/syllabus.py](app/api/syllabus.py) |
| File format handling | [app/utils/file_processor.py](app/utils/file_processor.py) |
| AI analysis (example) | [app/agents/syllabus_agent.py](app/agents/syllabus_agent.py) |
| Database models | [app/models/staff.py](app/models/staff.py), [app/models/syllabus.py](app/models/syllabus.py) |
| Frontend routing | [src/pages/App.jsx](src/pages/App.jsx) |
| API client | [src/api/api.js](src/api/api.js) |

---

## Common Tasks & Patterns

### Adding a New API Endpoint
1. Create endpoint in appropriate router file (`app/api/*.py`)
2. Use `@router.post/get/delete()` with docstring
3. Extract token via `get_current_user_id()` if authenticated
4. Query database via SQLAlchemy session
5. Return consistent response format: `{"success": ..., "message": ..., "data": ...}`

### Adding a New AI Agent
1. Create file: `app/agents/your_agent.py`
2. Import: `from langchain_google_genai import GoogleGenerativeAI`
3. Define prompt and `analyze(text)` function
4. Call from API endpoint, store results in database

### Modifying Database Schema
1. Update model in [app/models/](app/models/)
2. Ensure model is imported in [app/database/__init__.py](app/database/__init__.py)
3. Run `setup_db.py` or use migrations (see DATABASE_MIGRATION.md)

### Frontend API Integration
1. Define API call in [src/api/api.js](src/api/api.js)
2. Add auth header: `Authorization: Bearer ${localStorage.getItem('token')}`
3. Handle errors in component or via `useApi` hook
4. Store token/user in localStorage after login

---

## Debugging Tips

- **Backend logs**: Check `backend/logs/` for detailed execution traces
- **Database issues**: Enable SQLAlchemy echo in [app/database/config.py](app/database/config.py) for SQL logging
- **Token issues**: Decode JWT at https://jwt.io to verify claims
- **File processing**: Review `FileProcessingError` messages for specific format issues
- **Agent issues**: Check LLM model availability and Google API quotas

---

## Documentation References

- **Detailed setup & migration**: [QUICK_START_SYLLABUS.md](QUICK_START_SYLLABUS.md), [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md)
- **Feature overview**: [SYLLABUS_SYSTEM_OVERVIEW.md](SYLLABUS_SYSTEM_OVERVIEW.md)
- **API reference**: [SYLLABUS_API_DOCS.md](SYLLABUS_API_DOCS.md)
- **Code examples**: [CODE_SNIPPETS.md](CODE_SNIPPETS.md)
- **Deployment**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
