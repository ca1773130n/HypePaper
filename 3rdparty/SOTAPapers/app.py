from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from pathlib import Path

from sotapapers.core.database import DataBase
from sotapapers.core.models import PaperORM
from sotapapers.core.schemas import PaperGraph, PaperEdge, Paper
from sotapapers.core.settings import Settings
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import loguru

app = FastAPI()

# Serve static files (JS, CSS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow requests from any origin (you can restrict this if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate your database class
config_path = Path('sotapapers/configs')
settings = Settings(config_path)

logger = loguru.logger

db_url = settings.get('database.url')
db = DataBase(db_url, logger)

# Route to serve index.html
@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.get("/api/papers", response_model=PaperGraph)
async def get_paper_graph():
    async with db.AsyncSession as session:
        all_papers = await db.get_all_papers_async()

        # Create nodes
        nodes = []
        id_map = {}
        for paper in all_papers:
            logger.info(f"Paper: {paper.title}")
            nodes.append(paper)

        # Create edges
        edges = []
        for paper in id_map.values():
            if not paper.content or not paper.content.references:
                continue
            for ref in paper.content.references:
                if ref.id in id_map:
                    edges.append(PaperEdge(source=paper.id, target=ref.id))

        return PaperGraph(nodes=nodes, edges=edges)

if __name__ == "__main__":
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=10000)
    args = parser.parse_args()
    uvicorn.run(app, host='0.0.0.0', port=args.port)