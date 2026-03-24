# Database & Project Deployment Guide

## Quick Start (5 minutes)

For experienced developers, here's the fast path:

```bash
# 1. Setup
git clone <repo>
cd ai-powered-academic-performance-analyser
python -m venv .venv && source .venv/bin/activate
cd backend && pip install -r requirements.txt

# 2. Database (PostgreSQL must be running)
psql -U postgres -c "CREATE DATABASE academic_analyser;"
psql -U postgres -c "CREATE USER academic_user WITH PASSWORD 'your_pw';"
psql -U postgres -c "GRANT ALL ON DATABASE academic_analyser TO academic_user;"

# 3. Configure
cat > .env << EOF
DATABASE_URL=postgresql://academic_user:your_pw@localhost:5432/academic_analyser
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
GOOGLE_API_KEY=your-key
EOF

# 4. Migrate
cd .. && python run_migrations.py

# 5. Run
cd backend && uvicorn app.main:app --reload  # Terminal 1
cd frontend && npm install && npm run dev     # Terminal 2

# Done! Open http://localhost:5173
```

---

## Full Documentation

Detailed guides for each step:

### For Setup & Installation
👉 **[DATABASE_SETUP.md](./DATABASE_SETUP.md)**
- Prerequisites and system requirements
- Step-by-step installation for macOS, Linux, Windows
- Database configuration
- Comprehensive troubleshooting

### For Deployment Step-by-Step
👉 **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)**
- Pre-deployment system checks
- Step-by-step deployment with verification
- Quick commands reference
- Common troubleshooting table

### For Database Migrations
👉 **[backend/migrations/README.md](./backend/migrations/README.md)**
- How the migration system works
- Using the migration runner
- Creating new migrations
- Best practices and advanced usage

### Existing Documentation
- **[QUICK_START_SYLLABUS.md](./QUICK_START_SYLLABUS.md)** - Feature-specific setup
- **[SYLLABUS_SYSTEM_OVERVIEW.md](./SYLLABUS_SYSTEM_OVERVIEW.md)** - Architecture overview
- **[SYLLABUS_API_DOCS.md](./SYLLABUS_API_DOCS.md)** - API endpoint documentation
- **[DATABASE_MIGRATION.md](./DATABASE_MIGRATION.md)** - Detailed migration info

---

## What Was Added

### New Migration System
✓ **File**: `run_migrations.py`
- Migration runner utility with full tracking
- Status reporting and selective rollback

✓ **File**: `backend/migrations/004_initial_schema_complete.py`
- Complete schema for fresh deployments
- All tables, indexes, and constraints
- Fully reversible with downgrade function

### Documentation
✓ **DATABASE_SETUP.md** - 200+ lines of detailed setup instructions  
✓ **DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist with examples  
✓ **backend/migrations/README.md** - Complete migration system documentation

---

## Database Schema

### Created Tables (9 total)

**Core Tables:**
1. `staff` - User accounts with auth
2. `syllabus` - Course documents and analysis
3. `unit_topic_concept` - Course hierarchy
4. `concept_progress` - Student progress tracking
5. `tasks` - Learning tasks and assignments

**Legacy Tables (For Compatibility):**
6. `department` - Course departments
7. `subject` - Course subjects
8. `unit` - Course units
9. `concept` - Learning concepts

### All Tables Include
- Auto-incrementing primary key
- Created/updated timestamps (UTC)
- Proper indexes for query performance
- Foreign key constraints with CASCADE delete
- JSONB support for flexible data storage

---

## Migration Commands

```bash
# View status
python run_migrations.py status

# Run all pending
python run_migrations.py

# Run with verbose output
python run_migrations.py --verbose

# Run specific migration
python run_migrations.py up 004_initial_schema_complete

# Rollback last
python run_migrations.py rollback

# Rollback specific
python run_migrations.py down 001_add_task_table_and_date_tracking
```

---

## File Structure

```
project/
├── backend/
│   ├── migrations/
│   │   ├── 001_add_task_table_and_date_tracking.py
│   │   ├── 002_add_updated_at_to_tasks.py
│   │   ├── 003_add_missing_task_columns.py
│   │   ├── 004_initial_schema_complete.py    ✭ NEW
│   │   ├── migration_history.json            ✭ Auto-created
│   │   └── README.md                         ✭ NEW
│   ├── setup_db.py                           (existing - still works)
│   ├── run_migration.py                      (existing - run directly)
│   └── requirements.txt
├── run_migrations.py                         ✭ NEW (main runner)
├── DATABASE_SETUP.md                         ✭ NEW (setup guide)
├── DEPLOYMENT_CHECKLIST.md                   ✭ NEW (deployment guide)
└── [other project files]
```

---

## Two Ways to Initialize Database

### Option 1: Using Migration System (Recommended)
```bash
python run_migrations.py
```
**Advantages:**
- Tracks all changes in `migration_history.json`
- Can rollback if needed
- Follows best practices
- Easy to version control

### Option 2: Using Setup Script (Quick)
```bash
cd backend
python setup_db.py
```
**Advantages:**
- Simpler for fresh setup
- Direct table creation
- No history tracking

---

## Environment Setup

### macOS
```bash
# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# Create user and database (as shown above)
```

### Linux (Ubuntu/Debian)
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Create user and database (as shown above)
```

### Windows
1. Download installer: https://www.postgresql.org/download/windows/
2. Run installer and remember superuser password
3. PostgreSQL starts automatically

---

## Verification Steps

```bash
# 1. Check PostgreSQL
psql --version && echo "✓ PostgreSQL OK"

# 2. Check Python
python --version && echo "✓ Python OK"

# 3. Check Virtual Environment
which python | grep -q .venv && echo "✓ venv OK"

# 4. Check Database Connection
psql -U academic_user -d academic_analyser -c "SELECT 1;" && echo "✓ Database OK"

# 5. Check Backend
curl http://localhost:8000/health 2>/dev/null | grep -q healthy && echo "✓ Backend OK"

# 6. Check Frontend  
curl http://localhost:5173 2>/dev/null | grep -q "<!DOCTYPE" && echo "✓ Frontend OK"
```

---

## Key Features

### Migration System
- ✓ Automatic migration tracking
- ✓ Sequential execution
- ✓ Rollback capability
- ✓ Error handling and logging
- ✓ Reversible migrations (up/down)

### Complete Initial Schema
- ✓ All 9 tables created
- ✓ Proper indexes for performance
- ✓ Foreign key constraints
- ✓ JSONB support for flexibility
- ✓ Comprehensive documentation

### Production Ready
- ✓ Full logging support
- ✓ Error recovery mechanisms
- ✓ Database backup instructions
- ✓ Monitoring commands
- ✓ Troubleshooting guides

---

## Troubleshooting

### PostgreSQL Not Running
```bash
# macOS
brew services start postgresql@15

# Linux
sudo systemctl start postgresql

# Windows - Check Services application
```

### Database Connection Error
```bash
# Verify database exists
psql -U postgres -l | grep academic_analyser

# Verify user exists
psql -U postgres -c "\du" | grep academic_user

# Test connection
psql -U academic_user -d academic_analyser -c "SELECT 1;"
```

### Migration Issues
```bash
# Check migration history
cat backend/migrations/migration_history.json

# Check logs
tail -50 backend/logs/app.log

# Manually verify table
psql -U academic_user -d academic_analyser -c "\dt"
```

### Port Already in Use
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9  # Backend (8000)
lsof -ti:5173 | xargs kill -9  # Frontend (5173)
```

---

## Next Steps

1. **Read Full Guides**: Start with [DATABASE_SETUP.md](./DATABASE_SETUP.md)
2. **Follow Deployment**: Use [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
3. **Check Migrations**: Review [backend/migrations/README.md](./backend/migrations/README.md)
4. **Run Migrations**: `python run_migrations.py`
5. **Start Development**: Begin with frontend and backend servers
6. **Create Test User**: Use signup endpoint to verify system

---

## Summary

You now have:

✓ **Complete migration system** with tracking and rollback  
✓ **Initial schema** for fresh deployments  
✓ **Three detailed guides** for setup and deployment  
✓ **Migration runner** with status reporting  
✓ **Full documentation** for future reference  

**Total added files: 5**
- `run_migrations.py` - Main migration runner
- `backend/migrations/004_initial_schema_complete.py` - Complete schema
- `backend/migrations/README.md` - Migration guide
- `DATABASE_SETUP.md` - Setup instructions
- `DEPLOYMENT_CHECKLIST.md` - Deployment checklist

**Project is now deployment-ready!** 🚀

---

## Quick Reference

| Task | Command |
|------|---------|
| Check migration status | `python run_migrations.py status` |
| Run all migrations | `python run_migrations.py` |
| Rollback last | `python run_migrations.py rollback` |
| Start backend | `cd backend && uvicorn app.main:app --reload` |
| Start frontend | `cd frontend && npm run dev` |
| Database backup | `pg_dump -U academic_user -d academic_analyser > backup.sql` |
| Database restore | `psql -U academic_user -d academic_analyser < backup.sql` |
| Check health | `curl http://localhost:8000/health` |
| View logs | `tail -f backend/logs/app.log` |

---

**Questions?** Check the relevant documentation file:
- Setup issues → **DATABASE_SETUP.md**
- Deployment issues → **DEPLOYMENT_CHECKLIST.md**
- Migration issues → **backend/migrations/README.md**
- API issues → **SYLLABUS_API_DOCS.md**

**Last Updated**: March 24, 2026
