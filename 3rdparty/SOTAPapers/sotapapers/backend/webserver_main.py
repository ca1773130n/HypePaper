from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from sotapapers.core.database import DataBase
from sotapapers.core.models import PaperORM, UserORM

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:10000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class Paper(BaseModel):
    id: str
    title: str
    authors: dict
    github_star_avg_hype: Optional[int]
    primary_task: Optional[str]
    secondary_task: Optional[str]
    tertiary_task: Optional[str]
    references: List[str]
    cited_by: List[str]

class UserCreate(BaseModel):
    google_id: str
    username: str
    settings: Optional[dict] = {}

class User(BaseModel):
    id: int
    google_id: str
    username: str
    settings: dict

class CrawlerTask(BaseModel):
    id: int
    user_id: int
    config: dict
    status: str
    created_at: str

# Database Dependency
def get_db():
    database = DataBase()
    db = database.Session()
    try:
        yield db
    finally:
        db.close()

@app.post("/trpc")
async def handle_trpc(request: Request):
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})

    # Mock database
    tasks = []

    if method == "getCrawlerTasks":
        google_id = params.get("google_id")
        # Replace with actual database query
        return {"result": [
            {
                "id": 1,
                "user_id": google_id,
                "config": {"url": "arxiv.org", "depth": 2, "max_papers": 100},
                "status": "pending",
                "created_at": "2025-06-27T20:41:00Z"
            }
        ]}
    elif method == "createCrawlerTask":
        task = params.get("task")
        # Replace with actual database save
        tasks.append(task)
        return {"result": task}
    else:
        return JSONResponse(status_code=400, content={"error": "Method not found"})

# User Endpoints
@app.post("/users", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(UserORM).filter(UserORM.google_id == user.google_id).first()
    if existing_user:
        return existing_user
    db_user = UserORM(google_id=user.google_id, username=user.username, settings=user.settings)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{google_id}", response_model=User)
async def get_user(google_id: str, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.google_id == google_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{google_id}/settings")
async def update_settings(google_id: str, settings: dict, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.google_id == google_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.settings = settings
    db.commit()
    return {"message": "Settings updated"}

# Paper Endpoints
@app.get("/papers/top", response_model=List[Paper])
async def get_top_papers(limit: int = 10, db: Session = Depends(get_db)):
    papers = db.query(PaperORM).order_by(PaperORM.github_star_avg_hype.desc()).limit(limit).all()
    return [
        {
            **paper.__dict__,
            "references": [ref.id for ref in paper.references],
            "cited_by": [cite.id for cite in paper.cited_by]
        }
        for paper in papers
    ]

@app.get("/papers/subgraph", response_model=List[Paper])
async def get_subgraph(task: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(PaperORM)
    if task:
        query = query.filter(
            (PaperORM.primary_task == task) |
            (PaperORM.secondary_task == task) |
            (PaperORM.tertiary_task == task)
        )
    papers = query.all()
    return [
        {
            **paper.__dict__,
            "references": [ref.id for ref in paper.references],
            "cited_by": [cite.id for cite in paper.cited_by]
        }
        for paper in papers
    ]

# Crawler Tasks (Placeholder)
@app.get("/crawler/tasks", response_model=List[CrawlerTask])
async def get_crawler_tasks(google_id: str, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.google_id == google_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Placeholder: Replace with actual crawler task logic
    return [
        {"id": 1, "user_id": user.id, "config": {"url": "example.com"}, "status": "running", "created_at": "2025-06-27T15:26:00"}
    ]

@app.post("/crawler/tasks")
async def create_crawler_task(task: CrawlerTask, google_id: str, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.google_id == google_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Placeholder: Implement crawler task creation
    db_task = {"id": 1, "user_id": user.id, "config": task.config, "status": "pending", "created_at": "2025-06-27T15:26:00"}
    return db_task
