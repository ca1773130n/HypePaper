from sqlalchemy import create_engine, select, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, joinedload, selectinload
from sotapapers.core.models import Base, PaperORM, UserORM
from sotapapers.core.paper import create_paper_from_schema, create_paper_from_orm
from sotapapers.core.schemas import Paper
from typing import List, Optional
import loguru
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import bcrypt

from sotapapers.utils.id_util import make_generated_id

class DataBase:
    def __init__(self, db_url: str, logger: loguru.logger):
        self.engine = create_engine(f'sqlite:///{db_url}', echo=False)
        self.async_engine = create_async_engine(f'sqlite+aiosqlite:///{db_url}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.AsyncSession = sessionmaker(bind=self.async_engine, class_=AsyncSession)
        self.log = logger
        self.init_db()

    def init_db(self):
        self.migrate_db()
        session = self.Session()
        papers = session.query(PaperORM).all()
        users = session.query(UserORM).all()
        self.log.info(f"DB initialized: {len(papers)} papers, {len(users)} users exist in the database.")

    def migrate_db(self):
        Base.metadata.create_all(self.engine)

    def create_user_table(self):
        with self.Session() as session:
            # create user table if it doesn't exist
            if not session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")).fetchone():
                session.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, google_id TEXT UNIQUE, username TEXT UNIQUE, password_hash TEXT, settings JSON)"))
            session.commit()

    def drop_user_table(self):
        self.log.info("Attempting to drop the 'users' table if it exists...")
        with self.Session() as session: 
            session.execute(text("DROP TABLE IF EXISTS users"))
            session.commit()
        self.log.info("Finished dropping the 'users' table.")

    def dispose(self):
        self.engine.dispose()

    def get_papers_with_code(self):
        with self.Session() as session:
            return session.query(PaperORM).filter(PaperORM.code_url.isnot(None)).all()

    def get_user_by_google_id(self, google_id: str) -> Optional[UserORM]:
        session = self.Session()
        try:
            return session.query(UserORM).filter_by(google_id=google_id).first()
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> Optional[UserORM]:
        session = self.Session()
        try:
            return session.query(UserORM).filter_by(username=username).first()
        finally:
            session.close()

    def create_user(self, username: str, password: str, google_id: Optional[str] = None, settings: Optional[dict] = None) -> UserORM:
        with self.Session() as session:
            hashed_password = bcrypt.hash(password)
            new_user = UserORM(username=username, password_hash=hashed_password, google_id=google_id, settings=settings or {})
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            self.log.info(f"New user created: {username}")
            return new_user

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.verify(password, hashed_password)

    def delete_user(self, user_id: int) -> bool:
        session = self.Session()
        try:
            user = session.query(UserORM).filter_by(id=user_id).first()
            if user:
                session.delete(user)
                session.commit()
                self.log.info(f"User deleted: {user.username} (ID: {user_id})")
                return True
            self.log.warning(f"User not found for deletion: ID {user_id}")
            return False
        except Exception as e:
            session.rollback()
            self.log.error(f"Error deleting user ID {user_id}: {e}")
            return False
        finally:
            session.close()

    def get_paper(self, id: str) -> Optional[PaperORM]:
        session = self.Session()
        try:
            return session.query(PaperORM).filter_by(id=id).first()
        finally:
            session.close()

    def insert_paper(self, paper: Paper):
        self.log.info(f"Trying to insert paper to database: [{paper.title}]")
        
        with self.Session() as session:
            try:
                paper_orm = session.query(PaperORM).options(joinedload(PaperORM.references), joinedload(PaperORM.cited_by)).filter_by(id=paper.id).first()
                if paper_orm is None:
                    self.log.info(f"Inserting paper to database: [{paper.title}]")
                    paper_orm = create_paper_from_schema(paper)
                    session.add(paper_orm)
                    session.flush()
                else:
                    self.log.info(f"Paper already exists in database. updating: [{paper.title}]")
                    paper_orm = session.merge(paper_orm)

                session.refresh(paper_orm)

                if paper.content.references is not None:
                    for ref_paper in paper.content.references:
                        ref_paper_orm = self._get_paper_data_by_id(ref_paper.id, session=session)
                        if ref_paper_orm is None:
                            ref_paper_orm = create_paper_from_schema(ref_paper)
                            session.add(ref_paper_orm)
                            session.flush()
                        else:
                            ref_paper_orm = session.merge(ref_paper_orm)
                        
                        if ref_paper_orm not in paper_orm.references:
                            paper_orm.references.append(ref_paper_orm)
                    
                if paper.content.cited_by is not None:
                    for citing_paper in paper.content.cited_by:
                        citing_paper_orm = self._get_paper_data_by_id(citing_paper.id, session=session)
                        if citing_paper_orm is None:
                            citing_paper_orm = create_paper_from_schema(citing_paper)
                            session.add(citing_paper_orm)
                            session.flush()
                        else:
                            citing_paper_orm = session.merge(citing_paper_orm)
                        
                        if citing_paper_orm is not None and paper_orm not in citing_paper_orm.references:
                            citing_paper_orm.references.append(paper_orm)
            finally:
                session.commit()
            
    def _get_paper_data_by_id(self, paper_id: str, session=None, load_relations=False) -> Optional[PaperORM]:
        should_close_session = False
        if session is None:
            session = self.Session()
            should_close_session = True
            
        try:
            if load_relations:
                return session.query(PaperORM).options(joinedload(PaperORM.references), joinedload(PaperORM.cited_by)).filter_by(id=paper_id).first()
            else:
                return session.query(PaperORM).filter_by(id=paper_id).first()
        finally:
            if should_close_session:
                session.close()

    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        with self.Session() as session:
            paper_orm = self._get_paper_data_by_id(paper_id, session, load_relations=True)
            if paper_orm is None:
                return None
            paper = create_paper_from_orm(paper_orm)

            references = []
            cited_by = []

            if paper_orm.references is not None:
                for ref in paper_orm.references:
                    references.append(create_paper_from_orm(ref))
                if paper_orm.cited_by is not None:
                    for citing in paper_orm.cited_by:
                        cited_by.append(create_paper_from_orm(citing))

            paper.content.references = references
            paper.content.cited_by = cited_by

            return paper

    async def get_all_papers_async(self) -> List[Paper]:
        async with self.AsyncSession as session:
            result = await session.execute(
                select(PaperORM)
                .options(
                    selectinload(PaperORM.references),
                    selectinload(PaperORM.cited_by),
                )
            )
            paper_orms = result.scalars().all()

            papers = [create_paper_from_orm(paper) for paper in paper_orms]
            
            for i, paper in enumerate(papers):
                paper_orm = paper_orms[i]

                references = []
                cited_by = []

                if paper_orm.references is not None:
                    for ref in paper_orm.references:
                        references.append(create_paper_from_orm(ref))
                if paper_orm.cited_by is not None:
                    for citing in paper_orm.cited_by:
                        cited_by.append(create_paper_from_orm(citing))

                paper.content.references = references
                paper.content.cited_by = cited_by 
            return papers

    def get_paper_by_title_and_year(self, title: str, year: Optional[int] = None) -> Optional[Paper]:
        session = self.Session()
        paper_id = make_generated_id(title, year)
        try:
            return session.query(Paper).filter_by(id=paper_id).first()
        finally:
            session.close()

    def list_papers(self):
        session = self.Session()
        try:
            return session.query(Paper).all()
        finally:
            session.close()