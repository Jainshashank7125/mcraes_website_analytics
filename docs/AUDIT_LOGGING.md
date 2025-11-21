# Audit Logging System

This document describes the comprehensive audit logging system that tracks user actions, logins, user creation, and data sync operations.

## Overview

The audit logging system provides:
- **Complete audit trail** - Track all user actions and data operations
- **User accountability** - Know who did what and when
- **Security monitoring** - Track login attempts and user creation
- **Data sync tracking** - Monitor when and what data was synced
- **Debugging support** - Historical record of all operations

## Database Schema

### Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    action auditlogaction NOT NULL,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB,
    status VARCHAR(50),  -- 'success', 'error', 'partial'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### Action Types (Enum)

- `login` - User login attempts
- `logout` - User logout
- `user_created` - New user account creation
- `sync_brands` - Brands data sync
- `sync_prompts` - Prompts data sync
- `sync_responses` - Responses data sync
- `sync_ga4` - Google Analytics 4 data sync
- `sync_agency_analytics` - Agency Analytics data sync
- `sync_all` - Complete data sync

## Migration

### Option 1: Using SQL File (Recommended for Supabase)

Run the SQL migration file in Supabase SQL Editor:

```bash
# File: migrations/create_audit_logs_table.sql
```

### Option 2: Using Alembic

```bash
cd /path/to/project
alembic upgrade head
```

## What Gets Logged

### 1. User Authentication

**Login:**
- User ID and email
- IP address
- User agent
- Status (success/error)
- Error message (if failed)

**Logout:**
- User ID and email
- IP address
- User agent
- Timestamp

**User Creation:**
- Creator user ID and email (if created by admin)
- New user ID and email
- Self-registration flag
- IP address
- User agent

### 2. Data Sync Operations

**All Sync Types:**
- User who performed sync
- Sync type (brands, prompts, responses, GA4, Agency Analytics, all)
- Status (success/error/partial)
- Sync details (counts, brand IDs, date ranges)
- Error messages (if failed)
- IP address and user agent

**Sync Details Include:**
- Total records synced
- Brand-specific counts
- Date ranges used
- Filter parameters
- Error details for failed brands/campaigns

## Usage

### Automatic Logging

All endpoints automatically log their operations:

- **Auth endpoints** - Login, logout, user creation
- **Sync endpoints** - All sync operations
- **Error handling** - Failed operations are logged with error details

### Manual Logging

You can also log custom events:

```python
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction

# Log a custom event
await audit_logger.log(
    action=AuditLogAction.USER_CREATED,
    user_id="user_123",
    user_email="admin@example.com",
    status="success",
    details={"new_user_email": "newuser@example.com"},
    request=request
)
```

## API Endpoints

### Get Audit Logs

```http
GET /api/v1/audit/logs
```

**Query Parameters:**
- `action` - Filter by action type
- `user_email` - Filter by user email
- `status` - Filter by status (success, error, partial)
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)
- `limit` - Number of records (default: 100)
- `offset` - Pagination offset (default: 0)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "action": "login",
      "user_id": "user_123",
      "user_email": "user@example.com",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "details": {},
      "status": "success",
      "error_message": null,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1,
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

### Get Audit Statistics

```http
GET /api/v1/audit/stats
```

**Query Parameters:**
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)

**Response:**
```json
{
  "total_logs": 500,
  "by_action": {
    "login": 150,
    "sync_brands": 50,
    "sync_ga4": 30
  },
  "by_status": {
    "success": 450,
    "error": 30,
    "partial": 20
  },
  "by_user": {
    "admin@example.com": 200,
    "user@example.com": 150
  },
  "recent_logins": 150,
  "recent_syncs": 200,
  "recent_user_creations": 5
}
```

### Get User Activity

```http
GET /api/v1/audit/user-activity
```

**Query Parameters:**
- `user_email` - User email (defaults to current user)
- `limit` - Number of records (default: 50)

**Response:**
```json
{
  "user_email": "user@example.com",
  "items": [...],
  "count": 50
}
```

## Example Log Entries

### Successful Login
```json
{
  "action": "login",
  "user_id": "abc123",
  "user_email": "user@example.com",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "status": "success",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Failed Login
```json
{
  "action": "login",
  "user_id": null,
  "user_email": "user@example.com",
  "ip_address": "192.168.1.100",
  "status": "error",
  "error_message": "Invalid credentials",
  "created_at": "2024-01-15T10:31:00Z"
}
```

### User Creation
```json
{
  "action": "user_created",
  "user_id": "admin123",
  "user_email": "admin@example.com",
  "details": {
    "new_user_id": "newuser123",
    "new_user_email": "newuser@example.com"
  },
  "status": "success",
  "created_at": "2024-01-15T11:00:00Z"
}
```

### Data Sync
```json
{
  "action": "sync_brands",
  "user_id": "user123",
  "user_email": "user@example.com",
  "details": {
    "count": 25
  },
  "status": "success",
  "created_at": "2024-01-15T12:00:00Z"
}
```

### Partial Sync (Some Errors)
```json
{
  "action": "sync_prompts",
  "user_id": "user123",
  "user_email": "user@example.com",
  "details": {
    "total_count": 150,
    "brand_count": 5,
    "brand_results": [
      {"brand_id": 1, "count": 50},
      {"brand_id": 2, "count": 0, "error": "API timeout"}
    ]
  },
  "status": "partial",
  "created_at": "2024-01-15T13:00:00Z"
}
```

## Query Examples

### Get All Logins Today
```sql
SELECT * FROM audit_logs
WHERE action = 'login'
  AND created_at >= CURRENT_DATE
ORDER BY created_at DESC;
```

### Get Failed Syncs
```sql
SELECT * FROM audit_logs
WHERE action LIKE 'sync_%'
  AND status = 'error'
ORDER BY created_at DESC;
```

### Get User Activity
```sql
SELECT * FROM audit_logs
WHERE user_email = 'user@example.com'
ORDER BY created_at DESC
LIMIT 50;
```

### Get Recent User Creations
```sql
SELECT 
  user_email as created_by,
  details->>'new_user_email' as new_user,
  created_at
FROM audit_logs
WHERE action = 'user_created'
ORDER BY created_at DESC;
```

## Security Considerations

1. **Access Control**: Audit log endpoints require authentication
2. **Data Privacy**: IP addresses and user agents are logged but can be anonymized if needed
3. **Retention**: Consider implementing log retention policies
4. **Performance**: Indexes are created for common queries

## Performance

The audit_logs table includes indexes on:
- `action` - For filtering by action type
- `user_id` - For user-specific queries
- `user_email` - For email-based queries
- `status` - For filtering by status
- `created_at` - For date range queries
- Composite index on `(user_email, action, created_at)` - For common queries

## Maintenance

### Cleanup Old Logs

```sql
-- Delete logs older than 1 year
DELETE FROM audit_logs
WHERE created_at < NOW() - INTERVAL '1 year';
```

### Archive Logs

Consider archiving old logs to a separate table or storage system for compliance.

## Integration

The audit logging is automatically integrated into:
- ✅ Authentication endpoints (`app/api/auth.py`)
- ✅ Sync endpoints (`app/api/sync.py`)
- ✅ Error handling (failed operations are logged)

All logging happens asynchronously and won't block the main operation.

