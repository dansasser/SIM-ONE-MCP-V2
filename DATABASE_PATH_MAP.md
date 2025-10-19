# Database Path Mapping

## Current Problem
- Python MCP server and Admin Dashboard are using DIFFERENT databases
- Keys created in dashboard don't work with Python server

## Correct Database Location (SINGLE SOURCE OF TRUTH)
**Absolute Path:** `C:\Claude\SIM-ONE-MCP-V2\data\api_keys.db`

---

## System 1: Python MCP Server

**File:** `src\auth\database.py`

**How it finds database:**
```python
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'api_keys.db')
```

**Resolves to:**
- From: `C:\Claude\SIM-ONE-MCP-V2\src\auth\database.py`
- Goes up: `..` = `C:\Claude\SIM-ONE-MCP-V2\src`
- Goes up: `..` = `C:\Claude\SIM-ONE-MCP-V2`
- Adds: `data\api_keys.db`
- **Final path:** `C:\Claude\SIM-ONE-MCP-V2\data\api_keys.db` ✅

---

## System 2: Admin Dashboard

**File:** `admin-dashboard\.env`

**Current (WRONG) setting:**
```env
DATABASE_URL="file:../data/api_keys.db"
```

**Why it's wrong:**
- Prisma resolves paths from `admin-dashboard/prisma/schema.prisma` location
- `../data/api_keys.db` from `prisma/` = `admin-dashboard/data/api_keys.db` (WRONG!)
- We need to go up TWO levels, not one

**Correct setting (relative path):**
```env
DATABASE_URL="file:../../data/api_keys.db"
```

**Why this works:**
- From `admin-dashboard/prisma/schema.prisma`
- `../` = `admin-dashboard`
- `../../` = `SIM-ONE-MCP-V2` (project root)
- `../../data/api_keys.db` = `SIM-ONE-MCP-V2/data/api_keys.db` ✅

---

## Current State

### Database 1 (CORRECT - Python uses this):
- **Path:** `C:\Claude\SIM-ONE-MCP-V2\data\api_keys.db`
- **Keys:** 0
- **Status:** EMPTY ❌

### Database 2 (WRONG - Dashboard created this):
- **Path:** `C:\Claude\SIM-ONE-MCP-V2\admin-dashboard\data\api_keys.db`
- **Keys:** 1 (sk_simone_pASKfpRT)
- **Status:** HAS YOUR KEY ❌

---

## Fix Steps

1. ✅ Map out paths (this document)
2. ⏳ Update `admin-dashboard\.env` with absolute path
3. ⏳ Stop dashboard server (Ctrl+C)
4. ⏳ Delete `admin-dashboard\data\api_keys.db`
5. ⏳ Delete entire `admin-dashboard\data\` directory
6. ⏳ Restart dashboard server
7. ⏳ Create new API key
8. ⏳ Verify key is in `C:\Claude\SIM-ONE-MCP-V2\data\api_keys.db`
9. ⏳ Test key with Python MCP server

---

## Verification Commands

**Check both databases:**
```bash
python check_both_dbs.py
```

**Should show:**
```
data/api_keys.db: 1+ keys          ✅
admin-dashboard/data/api_keys.db: ERROR (file not found) ✅
```
