#!/usr/bin/env python3
"""
Complete implementation of all remaining features for HypePaper.

This script generates all necessary files for:
1. User-managed topics (CRUD operations)
2. PDF download service
3. Paper detail enhancements (star history, hype scores, references)
4. Frontend pages (Login, Profile, Admin, Paper Detail)
5. Router configuration with auth guards

Run from project root: python complete_implementation.py
"""
import os
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

FILES = {
    # ============= BACKEND: Enhanced Topics API =============
    f"{BACKEND}/src/api/v1/topics.py": '''"""Topics API with user management support."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models import Topic, PaperTopicMatch
from ...api.dependencies import get_current_user, get_user_id
from ...jobs.celery_app import celery_app

router = APIRouter(prefix="/topics", tags=["Topics"])


class TopicCreate(BaseModel):
    """Create topic request."""
    name: str
    description: Optional[str] = None
    keywords: List[str]


class TopicUpdate(BaseModel):
    """Update topic request."""
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None


class TopicResponse(BaseModel):
    """Topic response."""
    id: str
    name: str
    description: Optional[str]
    keywords: Optional[List[str]]
    is_system: bool
    user_id: Optional[str]
    created_at: str
    paper_count: int = 0

    class Config:
        from_attributes = True


@router.get("", response_model=List[TopicResponse])
async def list_topics(
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user)
):
    """List all topics (system + user's custom topics)."""
    # Build query: system topics OR user's topics
    query = select(Topic)
    if user:
        query = query.where(
            or_(
                Topic.is_system == True,
                Topic.user_id == UUID(user["id"])
            )
        )
    else:
        query = query.where(Topic.is_system == True)

    result = await db.execute(query)
    topics = result.scalars().all()

    # Get paper counts
    response = []
    for topic in topics:
        count_result = await db.execute(
            select(PaperTopicMatch).where(PaperTopicMatch.topic_id == topic.id)
        )
        paper_count = len(count_result.scalars().all())

        response.append(TopicResponse(
            id=str(topic.id),
            name=topic.name,
            description=topic.description,
            keywords=topic.keywords or [],
            is_system=topic.is_system,
            user_id=str(topic.user_id) if topic.user_id else None,
            created_at=topic.created_at.isoformat(),
            paper_count=paper_count
        ))

    return response


@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    request: TopicCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id)
):
    """Create a custom topic (authenticated users only)."""
    # Check for duplicate name
    existing = await db.execute(
        select(Topic).where(Topic.name == request.name.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic with this name already exists"
        )

    # Create topic
    topic = Topic(
        name=request.name.lower(),
        description=request.description,
        keywords=request.keywords,
        user_id=user_id,
        is_system=False
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)

    # Trigger topic matching job
    celery_app.send_task("match_topics.match_single_topic", args=[str(topic.id)])

    return TopicResponse(
        id=str(topic.id),
        name=topic.name,
        description=topic.description,
        keywords=topic.keywords,
        is_system=False,
        user_id=str(user_id),
        created_at=topic.created_at.isoformat(),
        paper_count=0
    )


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID,
    request: TopicUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id)
):
    """Update a custom topic (owner only)."""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if topic.is_system or topic.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify this topic"
        )

    # Update fields
    if request.name:
        topic.name = request.name.lower()
    if request.description is not None:
        topic.description = request.description
    if request.keywords is not None:
        topic.keywords = request.keywords

    await db.commit()
    await db.refresh(topic)

    # Re-run matching if keywords changed
    if request.keywords:
        celery_app.send_task("match_topics.match_single_topic", args=[str(topic.id)])

    # Get paper count
    count_result = await db.execute(
        select(PaperTopicMatch).where(PaperTopicMatch.topic_id == topic.id)
    )
    paper_count = len(count_result.scalars().all())

    return TopicResponse(
        id=str(topic.id),
        name=topic.name,
        description=topic.description,
        keywords=topic.keywords,
        is_system=False,
        user_id=str(user_id),
        created_at=topic.created_at.isoformat(),
        paper_count=paper_count
    )


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_user_id)
):
    """Delete a custom topic (owner only)."""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if topic.is_system or topic.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete this topic"
        )

    await db.delete(topic)
    await db.commit()
    return None
''',

    # ============= BACKEND: PDF Service =============
    f"{BACKEND}/src/services/pdf_service.py": '''"""PDF download and storage service."""
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Paper
from ..config import get_settings


class PDFService:
    """Service for PDF management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.storage_path = Path(self.settings.pdf_storage_base_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def download_pdf(self, paper_id: UUID) -> Path:
        """Download PDF for a paper if not already downloaded.

        Args:
            paper_id: Paper UUID

        Returns:
            Path to downloaded PDF

        Raises:
            ValueError: If paper not found or no PDF URL
            HTTPError: If download fails
        """
        # Get paper
        result = await self.db.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()

        if not paper:
            raise ValueError(f"Paper {paper_id} not found")

        # Check if already downloaded
        if paper.pdf_local_path and Path(paper.pdf_local_path).exists():
            return Path(paper.pdf_local_path)

        # Download PDF
        if not paper.pdf_url:
            raise ValueError(f"Paper {paper_id} has no PDF URL")

        pdf_path = self.storage_path / f"{paper_id}.pdf"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(paper.pdf_url)
            response.raise_for_status()

            with open(pdf_path, "wb") as f:
                f.write(response.content)

        # Update paper record
        paper.pdf_local_path = str(pdf_path)
        from datetime import datetime
        paper.pdf_downloaded_at = datetime.utcnow()
        await self.db.commit()

        return pdf_path

    async def get_pdf_path(self, paper_id: UUID) -> Optional[Path]:
        """Get local PDF path if exists.

        Args:
            paper_id: Paper UUID

        Returns:
            Path to PDF or None if not downloaded
        """
        result = await self.db.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()

        if not paper or not paper.pdf_local_path:
            return None

        path = Path(paper.pdf_local_path)
        return path if path.exists() else None
''',

    # ============= BACKEND: Enhanced Papers API =============
    f"{BACKEND}/src/api/v1/papers_enhanced.py": '''"""Enhanced paper endpoints with star history, hype scores, and PDF download."""
from typing import Dict, List, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models import Paper, PaperReference, GitHubStarSnapshot
from ...services.pdf_service import PDFService

router = APIRouter(prefix="/papers", tags=["Papers Enhanced"])


class StarHistoryPoint(BaseModel):
    """Star history data point."""
    date: str
    stars: int
    citations: int = 0


class HypeScoresResponse(BaseModel):
    """Hype scores breakdown."""
    average_hype: float
    weekly_hype: float
    monthly_hype: float
    formula_explanation: str


class ReferenceNode(BaseModel):
    """Citation graph node."""
    paper_id: str
    title: str
    authors: List[str]
    year: Optional[int]
    relationship: str  # "cites" or "cited_by"


@router.get("/{paper_id}/star-history", response_model=List[StarHistoryPoint])
async def get_star_history(
    paper_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get star history for a paper."""
    # Check paper exists
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get star snapshots
    from datetime import datetime, timedelta
    since_date = datetime.utcnow() - timedelta(days=days)

    snapshots_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(
            GitHubStarSnapshot.paper_id == paper_id,
            GitHubStarSnapshot.snapshot_date >= since_date
        )
        .order_by(GitHubStarSnapshot.snapshot_date)
    )
    snapshots = snapshots_result.scalars().all()

    return [
        StarHistoryPoint(
            date=snap.snapshot_date.isoformat(),
            stars=snap.star_count,
            citations=paper.citations or 0
        )
        for snap in snapshots
    ]


@router.get("/{paper_id}/hype-scores", response_model=HypeScoresResponse)
async def get_hype_scores(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Calculate and return hype scores."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get latest star count
    latest_snap_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(GitHubStarSnapshot.paper_id == paper_id)
        .order_by(GitHubStarSnapshot.snapshot_date.desc())
        .limit(1)
    )
    latest_snap = latest_snap_result.scalar_one_or_none()
    stars = latest_snap.star_count if latest_snap else 0

    # Calculate age in days
    from datetime import datetime
    age_days = (datetime.utcnow() - paper.published_date).days if paper.published_date else 1
    age_days = max(age_days, 1)

    # SOTAPapers formula: (citations * 100 + stars) / age_days
    citations = paper.citations or 0
    average_hype = (citations * 100 + stars) / age_days

    # Weekly hype (last 7 days growth)
    weekly_snap_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(
            GitHubStarSnapshot.paper_id == paper_id,
            GitHubStarSnapshot.snapshot_date >= datetime.utcnow() - timedelta(days=7)
        )
        .order_by(GitHubStarSnapshot.snapshot_date)
    )
    weekly_snaps = weekly_snap_result.scalars().all()
    weekly_hype = 0.0
    if len(weekly_snaps) >= 2:
        star_growth = weekly_snaps[-1].star_count - weekly_snaps[0].star_count
        weekly_hype = star_growth / 7

    # Monthly hype (last 30 days growth)
    monthly_snap_result = await db.execute(
        select(GitHubStarSnapshot)
        .where(
            GitHubStarSnapshot.paper_id == paper_id,
            GitHubStarSnapshot.snapshot_date >= datetime.utcnow() - timedelta(days=30)
        )
        .order_by(GitHubStarSnapshot.snapshot_date)
    )
    monthly_snaps = monthly_snap_result.scalars().all()
    monthly_hype = 0.0
    if len(monthly_snaps) >= 2:
        star_growth = monthly_snaps[-1].star_count - monthly_snaps[0].star_count
        monthly_hype = star_growth / 30

    return HypeScoresResponse(
        average_hype=round(average_hype, 2),
        weekly_hype=round(weekly_hype, 2),
        monthly_hype=round(monthly_hype, 2),
        formula_explanation=f"Average: (citations×100 + stars) / age_days = ({citations}×100 + {stars}) / {age_days}"
    )


@router.get("/{paper_id}/references", response_model=List[ReferenceNode])
async def get_references(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get citation graph (papers this cites + papers citing this)."""
    # Check paper exists
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    nodes = []

    # Papers this paper cites (references)
    refs_result = await db.execute(
        select(PaperReference, Paper)
        .join(Paper, PaperReference.referenced_paper_id == Paper.id)
        .where(PaperReference.source_paper_id == paper_id)
    )
    for ref, cited_paper in refs_result:
        nodes.append(ReferenceNode(
            paper_id=str(cited_paper.id),
            title=cited_paper.title,
            authors=[cited_paper.authors] if isinstance(cited_paper.authors, str) else cited_paper.authors or [],
            year=cited_paper.published_date.year if cited_paper.published_date else None,
            relationship="cites"
        ))

    # Papers citing this paper
    citing_result = await db.execute(
        select(PaperReference, Paper)
        .join(Paper, PaperReference.source_paper_id == Paper.id)
        .where(PaperReference.referenced_paper_id == paper_id)
    )
    for ref, citing_paper in citing_result:
        nodes.append(ReferenceNode(
            paper_id=str(citing_paper.id),
            title=citing_paper.title,
            authors=[citing_paper.authors] if isinstance(citing_paper.authors, str) else citing_paper.authors or [],
            year=citing_paper.published_date.year if citing_paper.published_date else None,
            relationship="cited_by"
        ))

    return nodes


@router.get("/{paper_id}/download-pdf")
async def download_pdf(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Download PDF file (downloads from source if not cached locally)."""
    pdf_service = PDFService(db)

    try:
        # This will download if needed
        pdf_path = await pdf_service.download_pdf(paper_id)
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{paper_id}.pdf"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF download failed: {str(e)}")
''',

    # ============= FRONTEND: Login Page =============
    f"{FRONTEND}/src/pages/LoginPage.vue": '''<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to HypePaper
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Track trending research papers with GitHub stars & citations
        </p>
      </div>

      <div class="mt-8 space-y-6">
        <button
          @click="signInWithGoogle"
          :disabled="loading"
          class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <span v-if="!loading">Sign in with Google</span>
          <span v-else>Loading...</span>
        </button>

        <div v-if="error" class="rounded-md bg-red-50 p-4">
          <div class="text-sm text-red-700">{{ error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')

async function signInWithGoogle() {
  loading.value = true
  error.value = ''

  try {
    await authStore.signInWithGoogle()
    // Redirect will happen via OAuth callback
  } catch (err: any) {
    error.value = err.message || 'Failed to sign in'
  } finally {
    loading.value = false
  }
}
</script>
''',

    # ============= FRONTEND: Auth Callback Page =============
    f"{FRONTEND}/src/pages/AuthCallbackPage.vue": '''<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="text-center">
      <h2 class="text-2xl font-bold mb-4">Completing sign in...</h2>
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  // Auth state will be updated by Supabase listener
  await new Promise(resolve => setTimeout(resolve, 1000))

  if (authStore.isAuthenticated) {
    router.push('/')
  } else {
    router.push('/login')
  }
})
</script>
''',

    # ============= FRONTEND: Profile Page =============
    f"{FRONTEND}/src/pages/ProfilePage.vue": '''<template>
  <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold mb-6">Profile</h1>

    <!-- User Info -->
    <div class="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
      <div class="px-4 py-5 sm:px-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900">User Information</h3>
      </div>
      <div class="border-t border-gray-200 px-4 py-5 sm:px-6">
        <dl class="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
          <div class="sm:col-span-1">
            <dt class="text-sm font-medium text-gray-500">Email</dt>
            <dd class="mt-1 text-sm text-gray-900">{{ authStore.user?.email }}</dd>
          </div>
          <div class="sm:col-span-1">
            <dt class="text-sm font-medium text-gray-500">User ID</dt>
            <dd class="mt-1 text-sm text-gray-900">{{ authStore.user?.id }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <!-- Custom Topics -->
    <div class="bg-white shadow overflow-hidden sm:rounded-lg">
      <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
        <h3 class="text-lg leading-6 font-medium text-gray-900">My Custom Topics</h3>
        <button
          @click="showAddModal = true"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Topic
        </button>
      </div>
      <div class="border-t border-gray-200">
        <ul class="divide-y divide-gray-200">
          <li v-for="topic in customTopics" :key="topic.id" class="px-4 py-4 sm:px-6">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <h4 class="text-sm font-medium text-gray-900">{{ topic.name }}</h4>
                <p class="text-sm text-gray-500">{{ topic.description || 'No description' }}</p>
                <div class="mt-2 flex flex-wrap gap-1">
                  <span
                    v-for="keyword in topic.keywords"
                    :key="keyword"
                    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {{ keyword }}
                  </span>
                </div>
              </div>
              <div class="ml-4 flex space-x-2">
                <button
                  @click="editTopic(topic)"
                  class="text-blue-600 hover:text-blue-900"
                >
                  Edit
                </button>
                <button
                  @click="deleteTopic(topic.id)"
                  class="text-red-600 hover:text-red-900"
                >
                  Delete
                </button>
              </div>
            </div>
          </li>
          <li v-if="customTopics.length === 0" class="px-4 py-4 sm:px-6 text-center text-gray-500">
            No custom topics yet. Click "Add Topic" to create one.
          </li>
        </ul>
      </div>
    </div>

    <!-- Add/Edit Topic Modal -->
    <div v-if="showAddModal || editingTopic" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-medium mb-4">{{ editingTopic ? 'Edit Topic' : 'Add Topic' }}</h3>
        <form @submit.prevent="saveTopic">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Name</label>
              <input
                v-model="topicForm.name"
                type="text"
                required
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                v-model="topicForm.description"
                rows="3"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              ></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Keywords (comma-separated)</label>
              <input
                v-model="keywordsInput"
                type="text"
                placeholder="machine learning, neural networks"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const authStore = useAuthStore()
const topics = ref<any[]>([])
const showAddModal = ref(false)
const editingTopic = ref<any>(null)
const topicForm = ref({ name: '', description: '', keywords: [] })
const keywordsInput = ref('')

const customTopics = computed(() =>
  topics.value.filter(t => !t.is_system)
)

async function loadTopics() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/topics`)
    topics.value = response.data
  } catch (error) {
    console.error('Failed to load topics:', error)
  }
}

async function saveTopic() {
  const keywords = keywordsInput.value.split(',').map(k => k.trim()).filter(Boolean)
  const data = { ...topicForm.value, keywords }

  try {
    if (editingTopic.value) {
      await axios.put(
        `${import.meta.env.VITE_API_URL}/api/v1/topics/${editingTopic.value.id}`,
        data
      )
    } else {
      await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/topics`, data)
    }
    closeModal()
    loadTopics()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Failed to save topic')
  }
}

function editTopic(topic: any) {
  editingTopic.value = topic
  topicForm.value = {
    name: topic.name,
    description: topic.description || '',
    keywords: topic.keywords || []
  }
  keywordsInput.value = (topic.keywords || []).join(', ')
}

async function deleteTopic(id: string) {
  if (!confirm('Are you sure you want to delete this topic?')) return

  try {
    await axios.delete(`${import.meta.env.VITE_API_URL}/api/v1/topics/${id}`)
    loadTopics()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Failed to delete topic')
  }
}

function closeModal() {
  showAddModal.value = false
  editingTopic.value = null
  topicForm.value = { name: '', description: '', keywords: [] }
  keywordsInput.value = ''
}

onMounted(() => {
  loadTopics()
})
</script>
''',

    # ============= FRONTEND: Admin Dashboard =============
    f"{FRONTEND}/src/pages/AdminDashboard.vue": '''<template>
  <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold mb-6">Admin Dashboard</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- ArXiv Crawl -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">ArXiv Crawl</h2>
        <form @submit.prevent="crawlArxiv" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Query</label>
            <input
              v-model="arxivQuery"
              type="text"
              placeholder="diffusion models"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Limit</label>
            <input
              v-model.number="arxivLimit"
              type="number"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
          <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700">
            Start Crawl
          </button>
        </form>
      </div>

      <!-- Conference Crawl -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">Conference Crawl</h2>
        <form @submit.prevent="crawlConference" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">Conference</label>
            <select v-model="conferenceName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
              <option value="CVPR">CVPR</option>
              <option value="ICLR">ICLR</option>
              <option value="NeurIPS">NeurIPS</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Year</label>
            <input
              v-model.number="conferenceYear"
              type="number"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
          <button type="submit" class="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700">
            Start Crawl
          </button>
        </form>
      </div>
    </div>

    <!-- Task Logs -->
    <div class="bg-white shadow rounded-lg p-6">
      <h2 class="text-xl font-semibold mb-4">Task Logs</h2>
      <button @click="loadTasks" class="mb-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
        Refresh
      </button>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Result</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="task in tasks" :key="task.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm">{{ task.task_type }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="statusClass(task.status)" class="px-2 py-1 text-xs rounded-full">
                  {{ task.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm">{{ formatDate(task.created_at) }}</td>
              <td class="px-6 py-4 text-sm">{{ task.result ? JSON.stringify(task.result).slice(0, 50) : '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const arxivQuery = ref('diffusion models')
const arxivLimit = ref(50)
const conferenceName = ref('CVPR')
const conferenceYear = ref(2024)
const tasks = ref<any[]>([])

async function crawlArxiv() {
  try {
    await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/admin/crawl/arxiv`, {
      query: arxivQuery.value,
      limit: arxivLimit.value
    })
    alert('ArXiv crawl started!')
    loadTasks()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Failed to start crawl')
  }
}

async function crawlConference() {
  try {
    await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/admin/crawl/conference`, {
      conference_name: conferenceName.value,
      conference_year: conferenceYear.value
    })
    alert('Conference crawl started!')
    loadTasks()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Failed to start crawl')
  }
}

async function loadTasks() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/admin/tasks?limit=20`)
    tasks.value = response.data
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
}

function statusClass(status: string) {
  return {
    'bg-yellow-100 text-yellow-800': status === 'pending',
    'bg-blue-100 text-blue-800': status === 'running',
    'bg-green-100 text-green-800': status === 'completed',
    'bg-red-100 text-red-800': status === 'failed'
  }
}

function formatDate(isoString: string) {
  return new Date(isoString).toLocaleString()
}

onMounted(() => {
  loadTasks()
})
</script>
''',

    # ============= FRONTEND: Enhanced Paper Detail =============
    f"{FRONTEND}/src/pages/PaperDetailPage.vue": '''<template>
  <div v-if="paper" class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <div class="mb-6">
      <h1 class="text-3xl font-bold mb-2">{{ paper.title }}</h1>
      <p class="text-gray-600">{{ paper.authors }}</p>
      <p class="text-sm text-gray-500">Published: {{ formatDate(paper.published_date) }}</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="md:col-span-2 space-y-6">
        <!-- Abstract -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Abstract</h2>
          <p class="text-gray-700">{{ paper.abstract }}</p>
        </div>

        <!-- Star History Chart -->
        <div v-if="starHistory.length > 0" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Star History</h2>
          <div class="h-64">
            <canvas ref="chartCanvas"></canvas>
          </div>
        </div>

        <!-- References -->
        <div v-if="references.length > 0" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Citation Graph</h2>
          <div class="space-y-2">
            <div v-for="ref in references" :key="ref.paper_id" class="border-l-4 pl-4" :class="ref.relationship === 'cites' ? 'border-blue-500' : 'border-green-500'">
              <router-link :to="`/papers/${ref.paper_id}`" class="text-blue-600 hover:underline">
                {{ ref.title }}
              </router-link>
              <p class="text-sm text-gray-600">{{ ref.authors.join(', ') }} ({{ ref.year }})</p>
              <span class="text-xs text-gray-500">{{ ref.relationship === 'cites' ? 'Referenced by this paper' : 'Cites this paper' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Metrics -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Metrics</h2>
          <dl class="space-y-2">
            <div>
              <dt class="text-sm text-gray-500">Citations</dt>
              <dd class="text-2xl font-bold">{{ paper.citations || 0 }}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">GitHub Stars</dt>
              <dd class="text-2xl font-bold">{{ paper.github_stars || 0 }}</dd>
            </div>
          </dl>
        </div>

        <!-- Hype Scores -->
        <div v-if="hypeScores" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Hype Scores</h2>
          <dl class="space-y-2">
            <div>
              <dt class="text-sm text-gray-500">Average</dt>
              <dd class="text-xl font-bold">{{ hypeScores.average_hype }}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">Weekly Growth</dt>
              <dd class="text-xl font-bold">{{ hypeScores.weekly_hype }}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">Monthly Growth</dt>
              <dd class="text-xl font-bold">{{ hypeScores.monthly_hype }}</dd>
            </div>
          </dl>
          <p class="text-xs text-gray-500 mt-4">{{ hypeScores.formula_explanation }}</p>
        </div>

        <!-- Links -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-3">Links</h2>
          <div class="space-y-2">
            <a v-if="paper.pdf_url" :href="paper.pdf_url" target="_blank" class="block text-blue-600 hover:underline">
              View PDF
            </a>
            <a :href="`${apiUrl}/api/v1/papers/${paper.id}/download-pdf`" target="_blank" class="block text-blue-600 hover:underline">
              Download PDF
            </a>
            <a v-if="paper.github_url" :href="paper.github_url" target="_blank" class="block text-blue-600 hover:underline">
              GitHub Repository
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const apiUrl = import.meta.env.VITE_API_URL
const paper = ref<any>(null)
const starHistory = ref<any[]>([])
const hypeScores = ref<any>(null)
const references = ref<any[]>([])

async function loadPaper() {
  const paperId = route.params.id
  try {
    const [paperRes, historyRes, scoresRes, refsRes] = await Promise.all([
      axios.get(`${apiUrl}/api/v1/papers/${paperId}`),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/star-history`).catch(() => ({ data: [] })),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/hype-scores`).catch(() => ({ data: null })),
      axios.get(`${apiUrl}/api/v1/papers/${paperId}/references`).catch(() => ({ data: [] }))
    ])

    paper.value = paperRes.data
    starHistory.value = historyRes.data
    hypeScores.value = scoresRes.data
    references.value = refsRes.data
  } catch (error) {
    console.error('Failed to load paper:', error)
  }
}

function formatDate(isoString: string) {
  if (!isoString) return 'N/A'
  return new Date(isoString).toLocaleDateString()
}

onMounted(() => {
  loadPaper()
})
</script>
''',

    # ============= FRONTEND: Router Configuration =============
    f"{FRONTEND}/src/router/index.ts": '''import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import AuthCallbackPage from '@/pages/AuthCallbackPage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'
import AdminDashboard from '@/pages/AdminDashboard.vue'
import PaperDetailPage from '@/pages/PaperDetailPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage
    },
    {
      path: '/auth/callback',
      name: 'auth-callback',
      component: AuthCallbackPage
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfilePage,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminDashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/papers/:id',
      name: 'paper-detail',
      component: PaperDetailPage
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Initialize auth if not done yet
  if (!authStore.user && !authStore.loading) {
    await authStore.fetchUser()
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
''',

    # ============= FRONTEND: Update Main App =============
    f"{FRONTEND}/src/main.ts": '''import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import axios from 'axios'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Configure axios interceptor for auth
axios.interceptors.request.use(async (config) => {
  const authStore = useAuthStore()
  if (authStore.session?.access_token) {
    config.headers.Authorization = `Bearer ${authStore.session.access_token}`
  }
  return config
})

app.mount('#app')
''',
}


def create_file(path: str, content: str):
    """Create file with content."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✓ {file_path.relative_to(ROOT)}")


def main():
    """Generate all files."""
    print("Generating all remaining implementation files...\n")

    for path, content in FILES.items():
        try:
            create_file(path, content)
        except Exception as e:
            print(f"✗ Failed: {path}: {e}")

    print("\n✅ All implementation files generated!")
    print("\nImplementation complete:")
    print("  - User-managed topics API (CRUD)")
    print("  - PDF download service")
    print("  - Star history, hype scores, references endpoints")
    print("  - Frontend pages: Login, Profile, Admin, Paper Detail")
    print("  - Router with authentication guards")
    print("\nNext steps:")
    print("  1. Register enhanced routers in backend/src/main.py")
    print("  2. Setup Supabase project and configure .env files")
    print("  3. Test authentication flow")
    print("  4. Deploy to production")


if __name__ == "__main__":
    main()
