# User Profile API Testing Guide

## Overview

This document describes how to test the user profile API endpoints after deploying the user_profiles table to Supabase.

## Prerequisites

1. **Apply Database Migration**: Run the SQL from `backend/apply_user_profiles_migration.sql` in Supabase SQL Editor
2. **Get Supabase JWT Token**: Authenticate via Google Auth in your frontend to get a valid JWT token
3. **Start Backend Server**: `cd backend && uvicorn src.main:app --reload`

## API Endpoints

### 1. Get Current User Profile

**Endpoint**: `GET /api/profile/me`

**Authentication**: Required (Bearer token)

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "John Doe",
  "avatar_url": "https://lh3.googleusercontent.com/...",
  "preferences": {},
  "created_at": "2025-11-01T00:00:00",
  "updated_at": "2025-11-01T00:00:00",
  "last_login_at": "2025-11-01T12:00:00"
}
```

**Test with curl**:
```bash
# Replace YOUR_JWT_TOKEN with actual token from Supabase Auth
curl -s http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | python3 -m json.tool
```

### 2. Update Profile

**Endpoint**: `PUT /api/profile/me`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "display_name": "Jane Doe",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**Test with curl**:
```bash
curl -s -X PUT http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Jane Doe",
    "avatar_url": "https://example.com/avatar.jpg"
  }' \
  | python3 -m json.tool
```

### 3. Update Preferences

**Endpoint**: `PUT /api/profile/me/preferences`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "preferences": {
    "theme": "dark",
    "notifications": {
      "email": true,
      "push": false
    }
  },
  "merge": true
}
```

**Test with curl**:
```bash
curl -s -X PUT http://localhost:8000/api/profile/me/preferences \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "theme": "dark",
      "notifications": {"email": true, "push": false}
    },
    "merge": true
  }' \
  | python3 -m json.tool
```

### 4. Get Crawler Jobs

**Endpoint**: `GET /api/profile/me/crawler-jobs`

**Authentication**: Required (Bearer token)

**Query Parameters**:
- `status` (optional): Filter by status (processing, completed, failed)

**Response**:
```json
[
  {
    "id": "uuid",
    "job_id": "arxiv_20251101_001",
    "status": "processing",
    "source_type": "arxiv",
    "keywords": "machine learning",
    "papers_crawled": 42,
    "references_crawled": 128,
    "started_at": "2025-11-01T10:00:00",
    "completed_at": null
  }
]
```

**Test with curl**:
```bash
# All jobs
curl -s http://localhost:8000/api/profile/me/crawler-jobs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | python3 -m json.tool

# Active jobs only
curl -s "http://localhost:8000/api/profile/me/crawler-jobs?status=processing" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | python3 -m json.tool
```

### 5. Get Custom Topics

**Endpoint**: `GET /api/profile/me/topics`

**Authentication**: Required (Bearer token)

**Response**:
```json
[
  {
    "id": "uuid",
    "name": "my-custom-topic",
    "description": "Papers about reinforcement learning",
    "keywords": ["rl", "reinforcement learning", "agent"],
    "is_system": false,
    "created_at": "2025-11-01T09:00:00"
  }
]
```

**Test with curl**:
```bash
curl -s http://localhost:8000/api/profile/me/topics \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | python3 -m json.tool
```

### 6. Get User Statistics

**Endpoint**: `GET /api/profile/me/stats`

**Authentication**: Required (Bearer token)

**Response**:
```json
{
  "total_crawler_jobs": 5,
  "active_crawler_jobs": 2,
  "inactive_crawler_jobs": 3,
  "custom_topics": 4,
  "member_since": "2025-10-15T08:00:00",
  "last_login": "2025-11-01T12:00:00"
}
```

**Test with curl**:
```bash
curl -s http://localhost:8000/api/profile/me/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  | python3 -m json.tool
```

### 7. Delete Profile

**Endpoint**: `DELETE /api/profile/me`

**Authentication**: Required (Bearer token)

**Response**: HTTP 204 No Content

**Warning**: This CASCADE deletes all user data (jobs, topics)!

**Test with curl**:
```bash
curl -s -X DELETE http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"
```

## Getting a Supabase JWT Token

### Option 1: From Frontend (Browser DevTools)

1. Open your frontend application
2. Sign in with Google
3. Open Browser DevTools → Application → Local Storage
4. Find the Supabase auth token (key: `supabase.auth.token`)
5. Copy the `access_token` value

### Option 2: Using Supabase JavaScript Client

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Sign in with Google
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google'
})

// Get session
const { data: { session } } = await supabase.auth.getSession()
console.log('JWT Token:', session.access_token)
```

### Option 3: Manual Testing (Create Test User)

For testing without Google Auth, create a test user in Supabase:

1. Go to Supabase Dashboard → Authentication → Users
2. Click "Add User" → Email
3. Create test user: `test@example.com`
4. Use Supabase REST API to get token:

```bash
curl -X POST https://YOUR_PROJECT.supabase.co/auth/v1/token?grant_type=password \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test_password"
  }'
```

## Testing Complete Flow

### 1. First Login (Auto-Create Profile)
```bash
# First GET creates profile automatically
TOKEN="your_jwt_token_here"

curl -s http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

Expected: Profile created from Google Auth data

### 2. Update Profile Information
```bash
curl -s -X PUT http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Updated Name"
  }' \
  | python3 -m json.tool
```

Expected: Profile updated with new display name

### 3. Set Preferences
```bash
curl -s -X PUT http://localhost:8000/api/profile/me/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {"theme": "dark"},
    "merge": true
  }' \
  | python3 -m json.tool
```

Expected: Preferences merged with existing preferences

### 4. Check Statistics
```bash
curl -s http://localhost:8000/api/profile/me/stats \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

Expected: User stats with job counts and topics

## Database Verification

After API calls, verify in Supabase SQL Editor:

```sql
-- Check user profile
SELECT * FROM user_profiles WHERE email = 'user@example.com';

-- Check user's crawler jobs
SELECT cj.*
FROM crawler_jobs cj
JOIN user_profiles up ON cj.user_id = up.id
WHERE up.email = 'user@example.com';

-- Check user's custom topics
SELECT t.*
FROM topics t
JOIN user_profiles up ON t.user_id = up.id
WHERE up.email = 'user@example.com';
```

## Error Cases

### 401 Unauthorized
```bash
# No token
curl -s http://localhost:8000/api/profile/me
# Response: {"detail": "Not authenticated"}

# Invalid token
curl -s http://localhost:8000/api/profile/me \
  -H "Authorization: Bearer invalid_token"
# Response: {"detail": "Not authenticated"}
```

### 404 Not Found
```bash
# Profile doesn't exist (before auto-creation)
curl -s http://localhost:8000/api/profile/me/stats \
  -H "Authorization: Bearer $TOKEN"
# Response: {"detail": "Profile not found"}
```

## Interactive API Documentation

FastAPI provides interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Click "Authorize" button and enter your JWT token to test endpoints interactively.

## Next Steps

After testing:

1. **Update Crawler Job Creation**: Add `user_id` when creating jobs
2. **Update Topic Creation**: Add `user_id` for custom topics
3. **Frontend Integration**: Use these endpoints in your React frontend
4. **Add Middleware**: Optionally add rate limiting for profile endpoints

## Troubleshooting

### Token Expired
- Supabase JWT tokens expire after 1 hour by default
- Get a new token by re-authenticating

### Database Connection Error
- Check `DATABASE_URL` environment variable
- Verify Supabase pooler is accessible

### Import Errors
- Restart backend server: `uvicorn src.main:app --reload`
- Check all model imports are correct
