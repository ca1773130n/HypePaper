from sqlalchemy import Column, String, Integer, Table, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum

Base = declarative_base()

# Association table for references
paper_references = Table(
    "paper_references",
    Base.metadata,
    Column("paper_id", String, ForeignKey("papers.id"), primary_key=True),
    Column("reference_id", String, ForeignKey("papers.id"), primary_key=True),
)

class PaperORM(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True)
    arxiv_id = Column(String, index=True)
    title = Column(String)
    authors = Column(JSON)
    affiliations = Column(JSON)
    affiliations_country = Column(JSON)
    year = Column(Integer)
    venue = Column(String)
    pages = Column(JSON)
    paper_type = Column(String)
    session_type = Column(String)
    accept_status = Column(String)
    note = Column(String)

    # Flattened embedded data (or link to sub-tables if you prefer)
    abstract = Column(String)
    bibtex = Column(String)
    primary_task = Column(String)
    secondary_task = Column(String)
    tertiary_task = Column(String)
    primary_method = Column(String)
    secondary_method = Column(String)
    tertiary_method = Column(String)
    datasets_used = Column(JSON)
    metrics_used = Column(JSON)
    comparisons = Column(JSON)
    limitations = Column(String)
    
    pdf_url = Column(String)
    youtube_url = Column(String)
    github_url = Column(String)
    project_page_url = Column(String)
    arxiv_url = Column(String)
    github_star_count = Column(Integer)
    github_star_avg_hype = Column(Integer)
    github_star_weekly_hype = Column(Integer)
    github_star_monthly_hype = Column(Integer)
    github_star_tracking_start_date = Column(String)
    github_star_tracking_latest_footprint = Column(JSON)
    citations_total = Column(Integer)

    references = relationship(
        "PaperORM",
        secondary=paper_references,
        primaryjoin=id == paper_references.c.paper_id,
        secondaryjoin=id == paper_references.c.reference_id,
        backref="cited_by",
        lazy="joined"
    )

class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    google_id = Column(String, unique=True, nullable=False)  # Store Google user ID
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False) # New field for hashed password
    settings = Column(JSON)  # Store user-specific settings (e.g., crawler configs, topic preferences)
