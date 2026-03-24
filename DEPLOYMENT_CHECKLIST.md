# Quick Deployment Checklist

## Pre-Deployment System Check

- [ ] Python 3.8+ installed (`python --version`)
- [ ] PostgreSQL 12+ installed and running (`psql --version`)
- [ ] Git installed
- [ ] 2GB+ free disk space
- [ ] Internet connection for pip packages

---

## Step-by-Step Deployment

### 1. Repository Setup
```bash
# Clone repository
git clone <repository-url>
cd ai-powered-academic-performance-analyser

# Check if .git exists
ls -la | grep ".git"
```
- [ ] Repository cloned
- [ ] Located in project directory

### 2. Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows

# Verify activation (should show .venv in prompt)
which python
```
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] `which python` shows .venv path

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt

# Verify installation
pip list | grep -E "fastapi|sqlalchemy|psycopg2"
```
- [ ] All packages installed successfully
- [ ] Key packages present: FastAPI, SQLAlchemy, psycopg2-binary, PyJWT

### 4. PostgreSQL Database Setup
```bash
# 4a. Create database user and database
psql -U postgres -c "CREATE USER academic_user WITH PASSWORD 'your_password';"
psql -U postgres -c "CREATE DATABASE academic_analyser OWNER academic_user;"
psql -U postgres -c "ALTER DATABASE academic_analyser SET client_encoding TO 'utf8';"

# 4b. Verify
psql -U postgres -l | grep academic_analyser
psql -U academic_user -d academic_analyser -c "SELECT 1;"
```
- [ ] Database 'academic_analyser' created
- [ ] User 'academic_user' created
- [ ] Connection test successful

### 5. Environment Configuration
```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://academic_user:your_password@localhost:5432/academic_analyser
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
GOOGLE_API_KEY=your-google-generative-ai-key
DEBUG=False
LOG_LEVEL=INFO
EOF

# Verify
cat .env
```
- [ ] `.env` file created in backend/
- [ ] DATABASE_URL correctly configured
- [ ] SECRET_KEY generated (random string)
- [ ] GOOGLE_API_KEY set (if using AI features)

### 6. Database Schema Setup
```bash
# Via migration system (recommended)
cd ..  # back to project root
python run_migrations.py status
python run_migrations.py

# OR via setup script
cd backend
python setup_db.py
```
Example output:
```
✓ Migration 001 executed successfully
✓ Migration 002 executed successfully
✓ Migration 003 executed successfully
✓ Migration 004 executed successfully
```
- [ ] All migrations executed
- [ ] No errors in output
- [ ] Migration history file created

### 7. Verify Database Schema
```bash
psql -U academic_user -d academic_analyser << EOF
\dt                          # List all tables
SELECT COUNT(*) FROM staff;  # Should return 0 (empty table is fine)
\q
EOF
```
Expected tables: staff, syllabus, unit_topic_concept, concept_progress, tasks, department, subject, unit, concept

- [ ] All 9 tables present
- [ ] Tables are empty (no errors)

### 8. Backend Health Check
```bash
cd backend

# Test database connection
python -c "from app.database import init_db; init_db(); print('✓ Database connected')"

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, test health endpoint
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "message": "API is running and database is connected"
}
```
- [ ] Backend server starts without errors
- [ ] Health check returns status 200
- [ ] Response includes "healthy" status

### 9. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Verify installation
npm list | head -20

# Start dev server
npm run dev
```
Expected: Vite dev server running on http://localhost:5173
- [ ] npm dependencies installed
- [ ] Vite dev server running
- [ ] Frontend accessible at http://localhost:5173

### 10. Full System Test
```bash
# Backend running?
curl -s http://localhost:8000/health | grep -q healthy && echo "✓ Backend OK"

# Frontend running?
curl -s http://localhost:5173 | grep -q "<!DOCTYPE" && echo "✓ Frontend OK"

# Database working?
psql -U academic_user -d academic_analyser -c "SELECT COUNT(*) FROM staff;" && echo "✓ Database OK"
```
Expected output:
```
✓ Backend OK
✓ Frontend OK
✓ Database OK
```
- [ ] All three systems operational
- [ ] No connection errors

---

## Post-Deployment Checks

### Logs
```bash
# Check backend logs
tail -50 backend/logs/app.log

# Check for errors
grep -i error backend/logs/app.log
```
- [ ] No critical errors in logs
- [ ] Connection messages present

### Database Health
```bash
psql -U academic_user -d academic_analyser << EOF
-- Check table row counts
SELECT 'staff' as table_name, COUNT(*) as rows FROM staff
UNION ALL
SELECT 'syllabus', COUNT(*) FROM syllabus
UNION ALL
SELECT 'unit_topic_concept', COUNT(*) FROM unit_topic_concept
UNION ALL
SELECT 'concept_progress', COUNT(*) FROM concept_progress
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks;
EOF
```
- [ ] All tables queryable
- [ ] No permission errors

### API Endpoints
```bash
# Test authentication endpoint
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPassword123!",
    "department": "CS"
  }'

# Should return success or validation error (both OK)
```
- [ ] API responds without connection errors
- [ ] Response includes proper error/success message

---

## Migration History

Migrations are tracked automatically. To see what's been applied:
```bash
cat backend/migrations/migration_history.json
```

Example:
```json
[
  {
    "name": "001_add_task_table_and_date_tracking",
    "executed_at": "2026-03-24T12:30:00",
    "direction": "up"
  },
  ...
]
```

- [ ] `migration_history.json` exists
- [ ] Contains all executed migrations

---

## Quick Commands Reference

```bash
# Status check
python run_migrations.py status

# Run migrations
python run_migrations.py

# Rollback last
python run_migrations.py rollback

# Backup database
pg_dump -U academic_user -d academic_analyser > backup_$(date +%Y%m%d).sql

# Access database
psql -U academic_user -d academic_analyser

# Start backend
cd backend && uvicorn app.main:app --reload

# Start frontend
cd frontend && npm run dev

# View logs
tail -f backend/logs/app.log
```

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| "Connection refused" | Start PostgreSQL: `brew services start postgresql@15` |
| "psql: FATAL: role does not exist" | Create user: `psql -U postgres -c "CREATE USER academic_user..."` |
| "database does not exist" | Create database: `psql -U postgres -c "CREATE DATABASE academic_analyser..."` |
| "No migrations run" | Run: `python run_migrations.py` from project root |
| "Module not found" | Install dependencies: `pip install -r requirements.txt` |
| "Virtual env not working" | Activate: `source .venv/bin/activate` |
| "Port 8000 already in use" | Kill: `lsof -ti:8000 \| xargs kill -9` |
| "Port 5173 already in use" | Kill: `lsof -ti:5173 \| xargs kill -9` |

---

## Final Verification

Run this master verification script:

```bash
#!/bin/bash
set -e

echo "=== AI Academic Performance Analyzer - Deployment Verification ==="
echo

echo "1. Checking Python..."
python --version

echo "2. Checking PostgreSQL..."
psql --version

echo "3. Checking virtual environment..."
which python | grep -q .venv && echo "   ✓ Virtual env active"

echo "4. Checking backend dependencies..."
python -c "import fastapi, sqlalchemy, psycopg2" && echo "   ✓ Dependencies OK"

echo "5. Checking database..."
psql -U academic_user -d academic_analyser -c "SELECT 1;" > /dev/null && echo "   ✓ Database OK"

echo "6. Checking migrations..."
[ -f backend/migrations/migration_history.json ] && echo "   ✓ Migrations initialized"

echo "7. Checking logs..."
[ -d backend/logs ] && echo "   ✓ Logs directory OK"

echo
echo "=== All checks passed! ✓ ==="
echo "Ready to start:"
echo "  Backend: cd backend && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
```

- [ ] Master verification passes
- [ ] Project ready for use

---

## Next Steps

1. **Populate test data** (optional):
   ```bash
   cd backend
   python
   >>> from app.database import SessionLocal
   >>> from app.models.staff import Staff
   >>> db = SessionLocal()
   >>> # Add test staff member
   ```

2. **Configure additional features** (if needed):
   - Google Generative AI integration
   - Email notifications
   - File upload limits
   - Authentication settings

3. **Set up monitoring** (production):
   - Email alerts for errors
   - Database backup automation
   - API performance metrics
   - User activity logging

4. **Production deployment**:
   - See `DEPLOYMENT_CHECKLIST.md`
   - Set up load balancer
   - Configure SSL/TLS
   - Set up CI/CD pipeline

---

**Last Updated**: March 24, 2026  
**Status**: ✓ Ready for deployment
