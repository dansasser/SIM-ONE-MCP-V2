# Admin Dashboard Implementation Plan

**Project:** SIM-ONE-MCP-V2 Admin Dashboard
**Branch:** claude/features-admin-dashboard
**Parent Project:** SIM-ONE-MCP-V2
**Created:** 2025-10-18
**Status:** Planning

---

## 🎯 Project Overview

Create a web-based admin dashboard for managing API keys in the SIM-ONE-MCP-V2 server. The dashboard will provide a user-friendly interface for administrators to create, view, revoke, and monitor API keys.

## 📋 Goals

1. **Primary Goal:** Web-based GUI for API key management
2. **Secondary Goal:** Enhanced CLI with additional features
3. **Tertiary Goal:** Usage analytics and monitoring

## 🏗️ Architecture

### Tech Stack

**Backend:**
- FastAPI (already in use)
- Existing auth system (extend for admin access)
- SQLite database (already in place)

**Frontend:**
- Single-page application (SPA)
- Vanilla JavaScript (no build tools required)
- Tailwind CSS via Play CDN for styling
- Chart.js for usage graphs

**Deployment:**
- Runs on separate port (default: 8001)
- Localhost only by default (security)
- Optional reverse proxy for remote access

### Directory Structure

```
SIM-ONE-MCP-V2/
├── src/
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── server.py          # FastAPI admin server
│   │   ├── auth.py            # Admin authentication
│   │   └── routes.py          # Admin API routes
│   └── auth/                  # Existing auth system
├── admin-ui/
│   ├── index.html             # Main dashboard page
│   ├── assets/
│   │   ├── css/
│   │   │   └── admin.css      # Custom styles
│   │   └── js/
│   │       ├── dashboard.js   # Dashboard logic
│   │       ├── api.js         # API client
│   │       └── charts.js      # Chart rendering
│   └── components/            # Reusable UI components
│       ├── key-list.html
│       ├── create-key.html
│       └── stats.html
├── scripts/
│   ├── manage_api_keys.py     # Enhanced CLI (existing)
│   ├── run_admin.py           # Admin server launcher
│   └── create_admin_user.py   # Admin user setup
└── docs/
    ├── ADMIN_DASHBOARD.md     # User documentation
    └── ADMIN_DASHBOARD_PLAN.md # This file

```

---

## 📱 Features Specification

### Phase 1: Core Functionality (MVP)

#### 1.1 Admin Authentication
- **Master admin account** stored in separate admin table
- Username/password authentication
- Session-based auth with secure cookies
- Password hashing with bcrypt
- Login page with CSRF protection

#### 1.2 API Key Management UI
- **Dashboard home page:**
  - Total keys count (active/revoked)
  - Recent activity feed
  - Quick stats

- **Keys list view:**
  - Sortable table (by date, email, status)
  - Search/filter by email, description, status
  - Pagination (50 per page)
  - Status indicators (active=green, revoked=red)
  - Last used timestamp

- **Create key modal:**
  - Email input (validated)
  - Description input
  - One-time display of generated key
  - Copy-to-clipboard button

- **Key details view:**
  - Full key information
  - Usage statistics
  - Activity log
  - Revoke button (with confirmation)

#### 1.3 REST API Endpoints

```
GET    /admin/login              # Login page
POST   /admin/login              # Login submission
POST   /admin/logout             # Logout
GET    /admin/                   # Dashboard home
GET    /admin/api/keys           # List all keys (paginated)
GET    /admin/api/keys/:id       # Get key details
POST   /admin/api/keys           # Create new key
DELETE /admin/api/keys/:id       # Revoke key
GET    /admin/api/stats          # Get statistics
GET    /admin/api/activity       # Get activity log
```

### Phase 2: Enhanced Features

#### 2.1 Usage Analytics
- **Request count per key** (daily, weekly, monthly)
- **Rate limit hit tracking**
- **Charts and graphs:**
  - Total requests over time
  - Requests by key
  - Most active keys
  - Rate limit violations

#### 2.2 Enhanced CLI
- **New commands:**
  - `stats` - Show usage statistics
  - `renew` - Rotate key (create new, revoke old)
  - `export` - Export keys to CSV/JSON
  - `import` - Bulk import keys
  - `interactive` - Interactive menu mode

- **Better formatting:**
  - Color-coded output (rich library)
  - Pretty tables
  - Progress bars

#### 2.3 Advanced Management
- **Bulk operations:**
  - Revoke multiple keys
  - Export filtered keys
  - Bulk email notification

- **Key policies:**
  - Optional expiration dates
  - Custom rate limits per key
  - Key scopes/permissions (future)

### Phase 3: Monitoring & Alerts

#### 3.1 Activity Logging
- **Audit trail:**
  - Who created/revoked keys
  - When keys were used
  - Failed authentication attempts
  - Admin actions log

#### 3.2 Alerts (Optional)
- Email notifications for:
  - New key created
  - Key revoked
  - Unusual activity
  - Rate limit exceeded

---

## 🔐 Security Considerations

### Admin Authentication
1. **Separate admin credentials** - Not using API keys for admin access
2. **Session management** - Secure HTTP-only cookies
3. **CSRF protection** - Token-based protection
4. **Password requirements** - Minimum complexity rules
5. **Failed login tracking** - Lock account after N attempts

### Network Security
1. **Default to localhost** - Bind to 127.0.0.1 by default
2. **HTTPS recommendation** - Document reverse proxy setup
3. **CORS policy** - Restrict origins if needed
4. **Rate limiting** - Protect admin endpoints

### Data Protection
1. **Never log full keys** - Only prefixes
2. **Secure password storage** - Bcrypt with high work factor
3. **Database encryption** - Optional (future)

---

## 📊 Database Schema Extensions

### New Table: admin_users

```sql
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);
```

### New Table: admin_sessions

```sql
CREATE TABLE admin_sessions (
    id TEXT PRIMARY KEY,  -- session token
    admin_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
);
```

### New Table: activity_log (optional for Phase 2)

```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,  -- 'create_key', 'revoke_key', 'admin_login', etc.
    admin_user_id INTEGER,
    api_key_id INTEGER,
    details TEXT,  -- JSON with additional info
    ip_address TEXT,
    FOREIGN KEY (admin_user_id) REFERENCES admin_users(id),
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
);
```

### Extend Existing: api_keys (for Phase 2)

```sql
-- Add columns to existing api_keys table
ALTER TABLE api_keys ADD COLUMN request_count INTEGER DEFAULT 0;
ALTER TABLE api_keys ADD COLUMN rate_limit_hits INTEGER DEFAULT 0;
ALTER TABLE api_keys ADD COLUMN expires_at TIMESTAMP;  -- Already exists
```

---

## 🚀 Implementation Phases

### Phase 1: MVP (Essential Features) - 1 Week

**Day 1-2: Backend Setup**
- [ ] Create admin module structure
- [ ] Implement admin authentication system
- [ ] Create admin database tables
- [ ] Create admin user setup script
- [ ] Implement admin API routes

**Day 3-4: Frontend Core**
- [ ] Create base HTML template with Tailwind CSS
- [ ] Implement login page
- [ ] Build dashboard home page
- [ ] Create keys list view
- [ ] Add create key modal

**Day 5: Integration & Testing**
- [ ] Connect frontend to API
- [ ] Add error handling
- [ ] Test all CRUD operations
- [ ] Security testing

**Day 6-7: Documentation & Polish**
- [ ] Write user documentation
- [ ] Add setup instructions
- [ ] Code cleanup
- [ ] Final testing

### Phase 2: Enhanced Features - 3-5 Days

**Day 1-2: Analytics**
- [ ] Implement usage tracking
- [ ] Create stats API endpoints
- [ ] Build charts/graphs UI
- [ ] Add activity log

**Day 3: Enhanced CLI**
- [ ] Add new CLI commands
- [ ] Implement color output
- [ ] Create interactive mode

**Day 4-5: Advanced Management**
- [ ] Bulk operations
- [ ] Export/import functionality
- [ ] Testing and documentation

### Phase 3: Monitoring (Optional) - 2-3 Days

- [ ] Activity logging system
- [ ] Email notifications (optional)
- [ ] Advanced analytics
- [ ] Alerting system

---

## 🧪 Testing Strategy

### Unit Tests
- Admin authentication logic
- API route handlers
- Database operations
- Session management

### Integration Tests
- Login flow
- Key creation workflow
- Revocation workflow
- Search and filter

### Security Tests
- SQL injection attempts
- XSS protection
- CSRF protection
- Session hijacking prevention
- Brute force protection

### User Acceptance Tests
- Can create admin user
- Can log in to dashboard
- Can create API key
- Can view all keys
- Can revoke key
- Can search keys

---

## 📚 Dependencies

### New Python Packages

```txt
# requirements-admin.txt
python-multipart>=0.0.6    # Form data handling
itsdangerous>=2.1.2        # Session token generation
```

### Frontend Libraries (CDN)

```html
<!-- Tailwind CSS Play CDN (dev mode - perfect for localhost admin tools) -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Heroicons for icons (optional, Tailwind's recommended icon set) -->
<!-- Or use any icon library you prefer -->

<!-- Chart.js (Phase 2) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

**Note:** Tailwind Play CDN shows a console warning about dev-only use. This is fine for a localhost admin dashboard - the warning just means the file is larger (includes all utilities) vs a production build. For our use case, this is perfect!

---

## 🎨 UI/UX Design

### Color Scheme
- **Primary:** #3b82f6 (Tailwind blue-500)
- **Success:** #22c55e (Tailwind green-500, Active keys)
- **Danger:** #ef4444 (Tailwind red-500, Revoked keys)
- **Warning:** #f59e0b (Tailwind amber-500, Warnings)
- **Background:** #f9fafb (Tailwind gray-50)

### Layout
- **Sidebar navigation** (left)
- **Main content area** (center)
- **Stats cards** at top of pages
- **Responsive design** (mobile-friendly)

### Key UI Components
1. Login page (centered card)
2. Dashboard (grid of stat cards + recent activity)
3. Keys table (sortable, searchable, paginated)
4. Create key modal (form overlay)
5. Key details panel (slide-in)
6. Charts (Phase 2)

---

## 📖 Documentation Requirements

### User Documentation (ADMIN_DASHBOARD.md)
1. Installation and setup
2. Creating first admin user
3. Logging in
4. Managing API keys
5. Understanding statistics
6. Security best practices

### Developer Documentation
1. Architecture overview
2. API reference
3. Database schema
4. Contributing guidelines
5. Testing guide

---

## 🔄 Future Enhancements (Post-Launch)

1. **Multi-admin support** with role-based access control
2. **OAuth/SSO integration** for admin login
3. **Webhooks** for key events
4. **Key rotation policies** (auto-expire old keys)
5. **Usage quotas** per key
6. **IP whitelisting** per key
7. **API versioning** support
8. **Dark mode** UI theme
9. **Export audit logs** to external systems
10. **Real-time dashboard** updates (WebSockets)

---

## ✅ Success Criteria

### MVP Success Metrics
- [ ] Admin can create account via CLI script
- [ ] Admin can log in to web dashboard
- [ ] Admin can create new API key in < 30 seconds
- [ ] Admin can revoke key in < 10 seconds
- [ ] Admin can search and find key in < 5 seconds
- [ ] Dashboard loads in < 2 seconds
- [ ] All security tests pass
- [ ] Documentation complete

### Phase 2 Success Metrics
- [ ] Usage statistics display correctly
- [ ] Charts render without errors
- [ ] CLI commands work as expected
- [ ] Export functionality produces valid files

---

## 🚨 Risks & Mitigations

### Risk 1: Security Vulnerabilities
**Mitigation:** Thorough security testing, follow OWASP guidelines, code review

### Risk 2: Performance with Many Keys
**Mitigation:** Pagination, indexing, lazy loading, caching

### Risk 3: Admin Account Compromise
**Mitigation:** Strong password requirements, session expiry, 2FA (future)

### Risk 4: Database Corruption
**Mitigation:** Regular backups, validation checks, transaction management

---

## 📞 Support & Maintenance

### Monitoring
- Health check endpoint
- Error logging
- Performance metrics

### Backup Strategy
- Daily database backups
- Backup admin credentials securely
- Disaster recovery plan

### Update Process
- Semantic versioning
- Migration scripts for schema changes
- Backward compatibility

---

## 🎓 Learning Resources

- FastAPI documentation: https://fastapi.tiangolo.com
- Tailwind CSS docs: https://tailwindcss.com
- Chart.js docs: https://www.chartjs.org
- OWASP security guide: https://owasp.org

---

## 📝 Notes

- Keep UI simple and intuitive
- Mobile-first responsive design
- Accessibility (WCAG 2.1 AA compliance)
- Fast page loads (< 2s)
- Clear error messages
- Progressive enhancement

---

**Next Steps:**
1. Review this plan
2. Set up development environment
3. Create initial project structure
4. Begin Phase 1 implementation
