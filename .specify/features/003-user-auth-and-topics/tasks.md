# Implementation Tasks: User Auth & Custom Topics

## Phase 1: Setup & Database (T001-T010)

### T001: Install Supabase client dependencies
- Backend: `pip install supabase==2.3.4`
- Frontend: `npm install @supabase/supabase-js`

### T002: Create Supabase project
- Sign up at supabase.com
- Create new project: `hypepaper-prod`
- Enable Google OAuth in Authentication settings
- Copy project URL and anon key

### T003: Database migration - Add user_id to topics
```sql
ALTER TABLE topics ADD COLUMN user_id UUID REFERENCES auth.users(id);
ALTER TABLE topics ADD COLUMN is_system BOOLEAN DEFAULT false;
ALTER TABLE topics ADD COLUMN keywords TEXT[];
UPDATE topics SET is_system = true WHERE user_id IS NULL;
```

### T004: Database migration - Add PDF storage fields
```sql
ALTER TABLE papers ADD COLUMN pdf_local_path TEXT;
ALTER TABLE papers ADD COLUMN pdf_downloaded_at TIMESTAMPTZ;
```

### T005: Database migration - Create admin_task_logs table
```sql
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

### T006: Create backend config for Supabase
- File: `backend/src/config.py`
- Add: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`

### T007: Create Supabase client singleton
- File: `backend/src/utils/supabase_client.py`
- Initialize with service key for admin operations

### T008: Create auth middleware
- File: `backend/src/api/dependencies.py`
- Function: `get_current_user()` - verify JWT from Supabase

### T009: Create frontend Supabase client
- File: `frontend/src/lib/supabase.ts`
- Initialize with anon key

### T010: Create Pinia auth store
- File: `frontend/src/stores/auth.ts`
- State: `user`, `session`, `isAuthenticated`
- Actions: `signInWithGoogle()`, `signOut()`, `fetchUser()`

## Phase 2: Authentication (T011-T020)

### T011: Backend - Auth endpoints
- File: `backend/src/api/v1/auth.py`
- `POST /auth/google` - Exchange OAuth code
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

### T012: Backend - Update topic model
- File: `backend/src/models/topic.py`
- Add fields: `user_id`, `is_system`, `keywords`

### T013: Backend - Update topic endpoints for user filtering
- File: `backend/src/api/v1/topics.py`
- Filter topics by `user_id` OR `is_system=true`
- Add ownership checks for PUT/DELETE

### T014: Frontend - Login page
- File: `frontend/src/pages/LoginPage.vue`
- Google OAuth button
- Redirect after successful login

### T015: Frontend - Auth route guards
- File: `frontend/src/router/index.ts`
- Redirect to `/login` if not authenticated

### T016: Frontend - Axios interceptor for auth
- File: `frontend/src/services/api.ts`
- Add JWT token to `Authorization` header

### T017: Frontend - Profile page skeleton
- File: `frontend/src/pages/ProfilePage.vue`
- Display user email and name

### T018: Frontend - Navbar with user menu
- File: `frontend/src/components/Navbar.vue`
- Show user avatar, dropdown with Profile/Logout

### T019: Frontend - Logout functionality
- Update auth store `signOut()`
- Clear localStorage, redirect to login

### T020: Test authentication flow
- Sign up with Google
- Verify JWT token in requests
- Verify logout clears session

## Phase 3: Custom Topics (T021-T030)

### T021: Backend - Create topic endpoint
- File: `backend/src/api/v1/topics.py`
- `POST /topics` - Create user topic with keywords

### T022: Backend - Update topic endpoint
- `PUT /topics/{id}` - Update name/keywords (owner only)

### T023: Backend - Delete topic endpoint
- `DELETE /topics/{id}` - Delete topic (owner only)

### T024: Backend - Topic matching service update
- File: `backend/src/services/topic_matching.py`
- Include `keywords` field in LLM context

### T025: Frontend - Topic management UI in profile
- File: `frontend/src/pages/ProfilePage.vue`
- List user topics
- Add/Edit/Delete buttons

### T026: Frontend - Add topic modal
- Component: `frontend/src/components/AddTopicModal.vue`
- Form: Name, Keywords (multi-input)

### T027: Frontend - Edit topic modal
- Component: `frontend/src/components/EditTopicModal.vue`
- Pre-fill existing data

### T028: Frontend - Delete confirmation modal
- Component: `frontend/src/components/DeleteTopicModal.vue`
- Confirm before deletion

### T029: Backend - Auto-trigger topic matching for new topics
- After creating topic, enqueue matching job

### T030: Test custom topics flow
- Create topic "Quantum ML" with keywords ["quantum", "machine learning"]
- Edit keywords to add "qubit"
- Delete topic
- Verify papers are matched correctly

## Phase 4: MVP Admin Dashboard (T031-T045)

### T031: Backend - Admin task logs model
- File: `backend/src/models/admin_task_log.py`
- Fields: task_type, task_params, status, result, error

### T032: Backend - Admin service
- File: `backend/src/services/admin_service.py`
- `log_task()`, `update_task()`, `get_tasks()`

### T033: Backend - Admin crawl endpoints
- File: `backend/src/api/v1/admin.py`
- `POST /admin/crawl/arxiv` - Trigger ArXiv crawl
- `POST /admin/crawl/conference` - Trigger conference crawl

### T034: Backend - Admin enrich endpoints
- `POST /admin/enrich/pdf/{paper_id}` - Enrich metadata
- `POST /admin/match/github/{paper_id}` - Match GitHub repo
- `POST /admin/extract/references/{paper_id}` - Extract refs

### T035: Backend - Admin task list endpoint
- `GET /admin/tasks` - List tasks with pagination
- `GET /admin/tasks/{task_id}` - Get task details

### T036: Frontend - Admin dashboard page
- File: `frontend/src/pages/AdminDashboard.vue`
- Tabs: Crawl, Enrich, Tasks

### T037: Frontend - ArXiv crawl form
- Form: Query, Limit
- Button: Trigger crawl
- Show task status

### T038: Frontend - Conference crawl form
- Form: Conference name, URL, Year
- Button: Trigger crawl

### T039: Frontend - Paper enrichment form
- Search papers by title
- Select paper
- Buttons: Enrich PDF, Match GitHub, Extract References

### T040: Frontend - Task logs table
- Display: Task type, Status, Created, Result
- Refresh button

### T041: Frontend - Real-time task status updates
- Poll task endpoint every 2 seconds
- Show spinner for in-progress tasks

### T042: Backend - Connect admin endpoints to Celery tasks
- Enqueue tasks instead of running synchronously

### T043: Test ArXiv crawl via admin dashboard
- Trigger crawl for "diffusion models"
- Verify papers appear in database

### T044: Test GitHub matching via admin dashboard
- Select paper without GitHub repo
- Trigger matching
- Verify repo is found and stored

### T045: Test reference extraction via admin dashboard
- Select paper with PDF
- Trigger extraction
- Verify references appear in database

## Phase 5: Paper Detail Enhancements (T046-T060)

### T046: Backend - Star history endpoint
- File: `backend/src/api/v1/papers.py`
- `GET /papers/{id}/star-history` - Return time-series data

### T047: Backend - Hype scores endpoint
- `GET /papers/{id}/hype-scores` - Return scores + formulas

### T048: Backend - References graph endpoint
- `GET /papers/{id}/references` - Return cited + citing papers

### T049: Backend - PDF download endpoint
- `GET /papers/{id}/download-pdf` - Stream PDF file
- If not exists locally, download from ArXiv first

### T050: Backend - PDF download service
- File: `backend/src/services/pdf_service.py`
- `download_pdf(paper_id)` - Download and save locally

### T051: Frontend - Paper detail page
- File: `frontend/src/pages/PaperDetailPage.vue`
- Fetch paper by ID

### T052: Frontend - Star history chart component
- Component: `frontend/src/components/StarHistoryChart.vue`
- Use Recharts to display line chart

### T053: Frontend - Hype scores display component
- Component: `frontend/src/components/HypeScores.vue`
- Show average, weekly, monthly with tooltips

### T054: Frontend - Citation graph component
- Component: `frontend/src/components/CitationGraph.vue`
- Display references and citing papers as list

### T055: Frontend - PDF viewer component
- Component: `frontend/src/components/PdfViewer.vue`
- Embed PDF or download button

### T056: Frontend - Integrate all components in detail page
- Add star chart, hype scores, citation graph, PDF viewer

### T057: Frontend - Loading states for detail page
- Show skeletons while data is loading

### T058: Test paper detail page with GitHub repo
- Navigate to paper with stars
- Verify chart displays correctly

### T059: Test paper detail page without GitHub repo
- Verify graceful fallback (no chart shown)

### T060: Test PDF download
- Click download button
- Verify PDF is saved locally
- Second download should use cached file

## Phase 6: Deployment Preparation (T061-T070)

### T061: Backend - Create Dockerfile
- Multi-stage build
- Install dependencies + AnyStyle
- Expose port 8000

### T062: Backend - Create docker-compose.yml for production
- FastAPI service
- PostgreSQL (or use Supabase)
- Redis
- Celery worker

### T063: Backend - Environment variable template
- File: `backend/.env.example`
- Document all required variables

### T064: Frontend - Build configuration for Vercel
- File: `frontend/vercel.json`
- Set build command, output directory

### T065: Frontend - Environment variable template
- File: `frontend/.env.example`
- Document: `VITE_API_URL`, `VITE_SUPABASE_URL`, etc.

### T066: Backend - Deploy to Render or Fly.io
- Create service, connect GitHub repo
- Configure environment variables
- Set up persistent volume for PDFs

### T067: Frontend - Deploy to Vercel
- Import GitHub repo
- Configure environment variables
- Deploy

### T068: Configure CORS for production
- Update `backend/src/main.py`
- Allow frontend domain

### T069: Set up Supabase production database
- Create tables via migrations
- Seed system topics

### T070: End-to-end production test
- Sign up with Google
- Create custom topic
- Crawl papers
- View paper details
- Download PDF

## Phase 7: Polish & Documentation (T071-T080)

### T071: Add error boundaries in frontend
- Handle API errors gracefully
- Show user-friendly messages

### T072: Add loading indicators for all async operations

### T073: Add input validation for topic creation

### T074: Add rate limiting for admin endpoints

### T075: Add pagination for task logs

### T076: Write deployment guide
- File: `docs/deployment.md`

### T077: Write user guide
- File: `docs/user-guide.md`

### T078: Write admin guide
- File: `docs/admin-guide.md`

### T079: Update README with new features

### T080: Create demo video/screenshots

## Parallelizable Tasks
- T001-T010 can run in parallel (setup tasks)
- T011-T013 (backend auth) parallel with T014-T019 (frontend auth)
- T021-T024 (backend topics) parallel with T025-T028 (frontend topics)
- T031-T035 (backend admin) parallel with T036-T041 (frontend admin)
- T046-T050 (backend enhancements) parallel with T051-T056 (frontend enhancements)
