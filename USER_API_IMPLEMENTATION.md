# User API Key System - Implementation Summary

## Overview

A complete user API key authentication system has been implemented to allow users to interact with the QtRvSim Web Evaluation platform via external applications.

## Features Implemented

### 1. Database Schema
- Added `user_api_key` (64 chars) and `user_api_key_expiry` (timestamp) columns to `users` table
- Created database migration script: `docker/migrations/001_add_user_api_keys.sql`
- Added index for faster API key lookups

### 2. Database Functions (`web/db.py`)
- `generate_user_api_key(user_id, api_key, expiry_date)` - Generate/update user API key
- `get_user_api_key(user_id)` - Retrieve user's current API key and expiry
- `verify_user_api_key(api_key)` - Validate API key and return user info
- `revoke_user_api_key(user_id)` - Revoke/delete user's API key

### 3. Authentication (`web/auth.py`)
- New `user_api_key_required` decorator
- Validates API key from Authorization header
- Checks key expiry, user verification, and submission permissions
- Passes `user_id` and `username` to wrapped functions

### 4. Profile Routes (`web/profile.py`)
- `GET /profile/api-key` - API key management page
- `POST /profile/api-key/generate` - Generate new 30-day API key
- `POST /profile/api-key/revoke` - Revoke existing API key

### 5. User Interface
**New Template:** `web/templates/profile_apikey.html`
- Displays current API key with copy-to-clipboard functionality
- Shows expiry date and status (Active/Expired)
- Generate/regenerate/revoke buttons
- API usage documentation with curl examples
- Lists available endpoints

**Profile Page Enhancement:** `web/templates/profile.html`
- Added "🔑 API Key" card linking to API key management

### 6. API Endpoints (`web/api.py`)
**Three new user-authenticated endpoints:**

1. `GET /api/user/tasks`
   - List all available tasks
   - Returns task IDs and names

2. `GET /api/user/task/<task_id>`
   - Get detailed task information
   - Includes description, deadlines, template code
   - Shows user's last submission and scores

3. `POST /api/user/submit`
   - Submit code for a task
   - Validates deadlines
   - Same submission process as web interface

### 7. Documentation
**Created:** `docs/USER_API.md`
- Complete API reference
- Authentication guide
- Endpoint documentation with examples
- Error codes and messages
- Python code examples
- Curl examples

## Security Features

1. **Secure Key Generation**
   - Uses `secrets.token_urlsafe(48)` for cryptographically secure 64-character keys
   
2. **Automatic Expiry**
   - Keys expire after 30 days
   - Database-level expiry checking

3. **Authorization Header**
   - Standard Bearer token authentication
   - `Authorization: Bearer <api_key>`

4. **User Validation**
   - Checks if user is verified
   - Checks if user can submit
   - Validates API key hasn't expired

5. **Same Restrictions as Web**
   - Deadline enforcement
   - Task availability checking
   - User ban status (inherited from user account)

## How It Works

### User Workflow
1. User logs into web interface
2. Navigates to Profile → API Key
3. Generates API key (valid for 30 days)
4. Copies API key to use in external applications
5. Uses API key in Authorization header for API requests

### API Request Flow
```
Client Request
    ↓
Authorization header validated
    ↓
API key looked up in database
    ↓
Key expiry checked
    ↓
User verification & permissions checked
    ↓
user_id & username passed to endpoint
    ↓
Endpoint processes request
    ↓
Response returned
```

## Database Migration

To apply the schema changes to an existing database:

```bash
psql -U qtrvsim -d qtrvsim_web_eval -f docker/migrations/001_add_user_api_keys.sql
```

Or for new installations, the columns are already included in `docker/webeval_schema.sql`.

## API vs Web Submission

Both methods use the same backend:
- Same validation logic
- Same deadline checking
- Same database tables
- Same evaluation queue

The only difference is authentication method:
- Web: Session-based (cookies)
- API: Token-based (API keys)

## Example Usage

### Generate Key (Web Interface)
1. Visit `/profile/api-key`
2. Click "Generate API Key"
3. Copy the displayed key

### Use Key (External App)
```bash
# Get tasks
curl -H "Authorization: Bearer YOUR_KEY" \
  https://your-domain.com/api/user/tasks

# Submit code
curl -X POST \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"task_id": 1, "code": "..."}' \
  https://your-domain.com/api/user/submit
```

## Future Enhancements (Optional)

1. **Rate Limiting**
   - Add request throttling per API key
   - Prevent abuse

2. **Key Usage Stats**
   - Track API calls per key
   - Show usage history in UI

3. **Multiple Keys**
   - Allow users to have multiple named keys
   - Different keys for different applications

4. **Scoped Permissions**
   - Read-only vs read-write keys
   - Task-specific keys

5. **Webhooks**
   - Notify external apps when evaluation completes

6. **API Key Logs**
   - Log all API requests
   - Audit trail for submissions

## Files Modified/Created

### Modified
- `docker/webeval_schema.sql` - Added user API key columns
- `web/db.py` - Added 4 new functions
- `web/auth.py` - Added user_api_key_required decorator
- `web/profile.py` - Added 3 new routes
- `web/api.py` - Added 3 new endpoints
- `web/templates/profile.html` - Added API key card

### Created
- `docker/migrations/001_add_user_api_keys.sql` - Migration script
- `web/templates/profile_apikey.html` - API key management UI
- `docs/USER_API.md` - API documentation

## Testing Checklist

- [ ] Apply database migration
- [ ] Restart web application
- [ ] Log in as regular user
- [ ] Navigate to Profile → API Key
- [ ] Generate API key
- [ ] Copy API key
- [ ] Test GET /api/user/tasks with key
- [ ] Test GET /api/user/task/1 with key
- [ ] Test POST /api/user/submit with key
- [ ] Verify submission appears in web interface
- [ ] Wait for key to be evaluated
- [ ] Check scores update correctly
- [ ] Test with expired key (manually set expiry in DB)
- [ ] Test revoke functionality
- [ ] Test regenerate functionality

## Notes

- API keys are 64 characters (URL-safe base64)
- Keys stored in plain text in database (like admin API keys)
- Expiry checked at database level in WHERE clause
- No session required for API endpoints
- Compatible with existing admin API key system
