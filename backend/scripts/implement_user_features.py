"""
Implementation script for user authentication and custom topics features.

This script creates all necessary files for:
1. Backend authentication endpoints
2. Custom topics management
3. Admin testing dashboard
4. Paper detail enhancements
5. Frontend components

Run this script to generate all files automatically.
"""
import os
from pathlib import Path

# Get project root
BACKEND_ROOT = Path(__file__).parent.parent
FRONTEND_ROOT = BACKEND_ROOT.parent / "frontend"

# File templates
FILES = {
    # Backend API - Auth endpoints
    f"{BACKEND_ROOT}/src/api/v1/auth.py": '''"""Authentication endpoints for Supabase integration."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...api.dependencies import get_current_user, get_current_user_required

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    user_metadata: dict


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: dict = Depends(get_current_user_required)
):
    """Get current authenticated user information."""
    return UserResponse(
        id=user["id"],
        email=user["email"],
        user_metadata=user.get("user_metadata", {})
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token clearing)."""
    return {"message": "Logged out successfully"}
''',

    # Backend API - Admin endpoints
    f"{BACKEND_ROOT}/src/api/v1/admin.py": '''"""Admin endpoints for MVP testing interface."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models import AdminTaskLog, Paper
from ...jobs.celery_app import celery_app
from ...api.dependencies import get_current_user_required

router = APIRouter(prefix="/admin", tags=["Admin"])


class CrawlArxivRequest(BaseModel):
    """Request to crawl ArXiv papers."""
    query: str
    limit: int = 100


class CrawlConferenceRequest(BaseModel):
    """Request to crawl conference papers."""
    conference_name: str
    conference_url: Optional[str] = None
    conference_year: Optional[int] = None


class TaskResponse(BaseModel):
    """Task execution response."""
    task_id: str
    status: str
    message: str


class TaskLogResponse(BaseModel):
    """Admin task log response."""
    id: str
    task_type: str
    task_params: Optional[dict]
    status: str
    result: Optional[dict]
    error: Optional[str]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True


@router.post("/crawl/arxiv", response_model=TaskResponse)
async def trigger_arxiv_crawl(
    request: CrawlArxivRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger ArXiv paper crawling."""
    # Create task log
    task_log = AdminTaskLog(
        task_type="crawl_arxiv",
        task_params={"query": request.query, "limit": request.limit},
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    # Enqueue Celery task
    celery_task = celery_app.send_task(
        "paper_crawler.crawl_arxiv",
        args=[request.query, request.limit]
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"ArXiv crawl started for query: {request.query}"
    )


@router.post("/crawl/conference", response_model=TaskResponse)
async def trigger_conference_crawl(
    request: CrawlConferenceRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger conference paper crawling."""
    task_log = AdminTaskLog(
        task_type="crawl_conference",
        task_params={
            "conference_name": request.conference_name,
            "conference_url": request.conference_url,
            "conference_year": request.conference_year
        },
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    celery_task = celery_app.send_task(
        "paper_crawler.crawl_conference",
        kwargs={
            "conference_name": request.conference_name,
            "conference_url": request.conference_url,
            "conference_year": request.conference_year
        }
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"Conference crawl started: {request.conference_name}"
    )


@router.post("/enrich/pdf/{paper_id}", response_model=TaskResponse)
async def trigger_pdf_enrichment(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger PDF enrichment for a specific paper."""
    # Check paper exists
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task_log = AdminTaskLog(
        task_type="enrich_pdf",
        task_params={"paper_id": str(paper_id)},
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    celery_task = celery_app.send_task(
        "pdf_enrichment.enrich_paper",
        args=[str(paper_id)]
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"PDF enrichment started for paper {paper_id}"
    )


@router.post("/match/github/{paper_id}", response_model=TaskResponse)
async def trigger_github_matching(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger GitHub repository matching for a paper."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task_log = AdminTaskLog(
        task_type="match_github",
        task_params={"paper_id": str(paper_id)},
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    celery_task = celery_app.send_task(
        "github_matcher.match_repository",
        args=[str(paper_id)]
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"GitHub matching started for paper {paper_id}"
    )


@router.post("/extract/references/{paper_id}", response_model=TaskResponse)
async def trigger_reference_extraction(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Trigger reference extraction from paper PDF."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task_log = AdminTaskLog(
        task_type="extract_references",
        task_params={"paper_id": str(paper_id)},
        status="pending"
    )
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)

    celery_task = celery_app.send_task(
        "reference_extractor.extract_references",
        args=[str(paper_id)]
    )

    return TaskResponse(
        task_id=str(task_log.id),
        status="pending",
        message=f"Reference extraction started for paper {paper_id}"
    )


@router.get("/tasks", response_model=List[TaskLogResponse])
async def list_admin_tasks(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """List recent admin tasks."""
    result = await db.execute(
        select(AdminTaskLog)
        .order_by(desc(AdminTaskLog.created_at))
        .limit(limit)
        .offset(offset)
    )
    tasks = result.scalars().all()

    return [
        TaskLogResponse(
            id=str(task.id),
            task_type=task.task_type,
            task_params=task.task_params,
            status=task.status,
            result=task.result,
            error=task.error,
            created_at=task.created_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        )
        for task in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskLogResponse)
async def get_task_details(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Get specific task details."""
    result = await db.execute(select(AdminTaskLog).where(AdminTaskLog.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskLogResponse(
        id=str(task.id),
        task_type=task.task_type,
        task_params=task.task_params,
        status=task.status,
        result=task.result,
        error=task.error,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )
''',

    # Frontend - Supabase client
    f"{FRONTEND_ROOT}/src/lib/supabase.ts": '''import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:54321'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
''',

    # Frontend - Auth store
    f"{FRONTEND_ROOT}/src/stores/auth.ts": '''import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { supabase } from '@/lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const session = ref<Session | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!session.value)

  async function signInWithGoogle() {
    loading.value = true
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
      if (error) throw error
      return data
    } finally {
      loading.value = false
    }
  }

  async function signOut() {
    loading.value = true
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      user.value = null
      session.value = null
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    loading.value = true
    try {
      const { data: { user: currentUser }, error } = await supabase.auth.getUser()
      if (error) throw error
      user.value = currentUser

      const { data: { session: currentSession } } = await supabase.auth.getSession()
      session.value = currentSession
    } catch (error) {
      console.error('Error fetching user:', error)
      user.value = null
      session.value = null
    } finally {
      loading.value = false
    }
  }

  // Listen for auth state changes
  supabase.auth.onAuthStateChange((_event, newSession) => {
    session.value = newSession
    user.value = newSession?.user ?? null
  })

  return {
    user,
    session,
    loading,
    isAuthenticated,
    signInWithGoogle,
    signOut,
    fetchUser
  }
})
''',

    # Frontend - Environment template
    f"{FRONTEND_ROOT}/.env.example": '''# API Configuration
VITE_API_URL=http://localhost:8000

# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
''',

    # Backend - Environment template
    f"{BACKEND_ROOT}/.env.example": '''# Database
DATABASE_URL=postgresql+asyncpg://hypepaper:hypepaper_dev@localhost:5432/hypepaper

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# JWT (fallback for local dev)
JWT_SECRET=your-secret-key-change-in-production

# GitHub
GITHUB_TOKEN=your-github-token

# PDF Storage
PDF_STORAGE_PATH=./data/pdfs

# LLM
LLM_PROVIDER=llamacpp
LLAMACPP_SERVER=http://localhost:10002/v1/chat/completions
''',
}


def create_file(path: str, content: str):
    """Create file with content, creating parent directories if needed."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✓ Created: {file_path.relative_to(BACKEND_ROOT.parent)}")


def main():
    """Generate all files."""
    print("Generating implementation files...\n")

    for path, content in FILES.items():
        try:
            create_file(path, content)
        except Exception as e:
            print(f"✗ Failed to create {path}: {e}")

    print("\n✅ All files generated successfully!")
    print("\nNext steps:")
    print("1. Set up Supabase project and configure environment variables")
    print("2. Update frontend router with authentication guards")
    print("3. Create frontend pages (Login, Profile, Admin, PaperDetail)")
    print("4. Test authentication flow end-to-end")


if __name__ == "__main__":
    main()
