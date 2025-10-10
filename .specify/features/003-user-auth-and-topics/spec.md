# Feature Specification: User Authentication & Custom Topics

## Overview
Add user authentication with Google OAuth and enable users to create, manage, and track papers by their own custom topics.

## User Stories

### Authentication
- As a user, I want to sign up with my Google account so I can access personalized features
- As a user, I want to stay logged in across sessions so I don't have to re-authenticate
- As a user, I want to log out when I'm done using the app

### Custom Topics
- As a user, I want to add custom topics with keywords so I can track papers I'm interested in
- As a user, I want to edit my topic keywords so I can refine matching criteria
- As a user, I want to delete topics I no longer care about
- As a user, I want to see only my topics in the topic selector

### MVP Testing Interface
- As a developer, I want a testing dashboard to trigger paper crawling manually
- As a developer, I want to test PDF enrichment on specific papers
- As a developer, I want to verify GitHub repo matching works correctly
- As a developer, I want to inspect reference extraction results

### Paper Details Enhancement
- As a user, I want to see GitHub star growth charts on paper detail pages
- As a user, I want to see hype scores (average, weekly, monthly) with explanations
- As a user, I want to see cited papers and references in a graph
- As a user, I want to download or view the PDF directly from the app

## Technical Architecture

### Authentication Stack: Supabase Auth
**Choice Rationale**:
- Built-in Google OAuth integration
- PostgreSQL-native (aligns with existing DB)
- Free tier suitable for MVP
- JWT-based auth works with FastAPI
- Row-level security policies

### Database Schema Changes

```sql
-- Users table (managed by Supabase)
-- Using Supabase auth.users, reference by UUID

-- Add user_id to topics
ALTER TABLE topics ADD COLUMN user_id UUID REFERENCES auth.users(id);
ALTER TABLE topics ADD COLUMN is_system BOOLEAN DEFAULT false;
ALTER TABLE topics ADD COLUMN keywords TEXT[];

-- Add PDF storage
ALTER TABLE papers ADD COLUMN pdf_local_path TEXT;
ALTER TABLE papers ADD COLUMN pdf_downloaded_at TIMESTAMPTZ;

-- Admin logs for testing interface
CREATE TABLE admin_task_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(50) NOT NULL,
    task_params JSONB,
    status VARCHAR(20) NOT NULL,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### API Endpoints

#### Authentication
- `POST /api/v1/auth/google` - Exchange Google OAuth code for session
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/logout` - Logout and invalidate session

#### Topics (User-Specific)
- `GET /api/v1/topics` - List user's topics + system topics
- `POST /api/v1/topics` - Create custom topic (requires auth)
- `PUT /api/v1/topics/{id}` - Update topic (owner only)
- `DELETE /api/v1/topics/{id}` - Delete topic (owner only)

#### Admin Testing Interface
- `POST /api/v1/admin/crawl/arxiv` - Trigger ArXiv crawl with query
- `POST /api/v1/admin/crawl/conference` - Trigger conference crawl
- `POST /api/v1/admin/enrich/pdf/{paper_id}` - Enrich specific paper
- `POST /api/v1/admin/match/github/{paper_id}` - Match GitHub repo
- `POST /api/v1/admin/extract/references/{paper_id}` - Extract references
- `GET /api/v1/admin/tasks` - List recent admin tasks
- `GET /api/v1/admin/tasks/{task_id}` - Get task result

#### Papers Enhancement
- `GET /api/v1/papers/{id}/star-history` - Get star growth data
- `GET /api/v1/papers/{id}/hype-scores` - Get hype score breakdown
- `GET /api/v1/papers/{id}/references` - Get citation graph
- `GET /api/v1/papers/{id}/download-pdf` - Download PDF file

### Frontend Changes

#### New Pages
1. **Login Page** (`/login`) - Google OAuth button
2. **Profile Page** (`/profile`) - User info, manage topics
3. **Admin Dashboard** (`/admin`) - Testing interface (dev only)
4. **Paper Detail Page** (`/papers/:id`) - Enhanced with charts

#### State Management
- Use Pinia store for auth state
- Persist JWT token in localStorage
- Axios interceptor for auth headers

### Deployment Configuration

#### Backend (Render or Fly.io)
- FastAPI app with Uvicorn workers
- PostgreSQL connection via Supabase
- Environment variables: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`
- PDF storage: Local volume (Render) or Fly.io volume

#### Frontend (Vercel)
- Vue 3 SPA with Vite
- Environment variables: `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- CDN-optimized static assets

## Acceptance Criteria

### Authentication
- [x] User can sign up with Google account
- [x] User can log in with Google account
- [x] User can log out
- [x] User session persists across browser sessions
- [x] Protected routes redirect to login

### Custom Topics
- [x] User can create topic with name and keywords
- [x] User can edit topic name and keywords
- [x] User can delete their own topics
- [x] System topics (ML, CV, NLP, etc.) remain read-only
- [x] Topic matching runs automatically for new user topics

### MVP Testing Interface
- [x] Admin can trigger ArXiv crawl with custom query
- [x] Admin can trigger conference crawl (CVPR, ICLR)
- [x] Admin can enrich specific paper's metadata
- [x] Admin can force GitHub repo matching
- [x] Admin can extract references from paper
- [x] Admin sees task status and results in real-time

### Paper Details
- [x] Paper detail page shows star history chart (if GitHub repo exists)
- [x] Paper detail page shows hype scores with calculation explanation
- [x] Paper detail page shows references and citing papers
- [x] Paper detail page has PDF download button
- [x] PDF is stored locally after first download

## Out of Scope (Future)
- Multi-user collaboration on topics
- Email notifications for new papers
- Paper annotations/notes
- Social features (likes, comments)
- Paper recommendations based on reading history
