import argparse
import os
import sys

from loguru import logger
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sotapapers.core.settings import Settings
from sotapapers.core.database import DataBase
from sotapapers.core.schemas import Paper, PaperContent, PaperMedia, PaperMetrics, PaperType, PaperSessionType, PaperAcceptStatus
from sotapapers.core.models import PaperORM # Import PaperORM
from sotapapers.modules.paper_reader import PaperReader
from sotapapers.utils.config import get_config_path
from python_json_config import Config

def main():
    parser = argparse.ArgumentParser(description="Update paper database using LLM.")
    parser.add_argument('--config-path', type=str, default=get_config_path().absolute())
    args = parser.parse_args()

    config_path = Path(args.config_path)
    settings = Settings(config_path)

    db = DataBase(settings.config.database.url, logger=logger)
    session = db.Session()

    paper_reader = PaperReader(settings, logger=logger)
    pdf_download_basepath = settings.config.paper_crawler.pdf_download_basepath

    # Get all papers with PDF URLs and missing abstracts or tasks or methods or datasets or metrics or comparisons or limitations
    papers_to_process = session.query(PaperORM).filter(PaperORM.pdf_url.isnot(None), (PaperORM.abstract == None) | (PaperORM.primary_task == None) | (PaperORM.secondary_task == None) | (PaperORM.tertiary_task == None) | (PaperORM.primary_method == None) | (PaperORM.secondary_method == None) | (PaperORM.tertiary_method == None) | (PaperORM.datasets_used == None) | (PaperORM.metrics_used == None) | (PaperORM.comparisons == None) | (PaperORM.limitations == None)).all()

    logger.info(f"Found {len(papers_to_process)} papers to process.")

    for paper_orm in papers_to_process:
        logger.info(f"Processing paper: {paper_orm.title}")
        try:
            # Set the file path for PaperReader. Assuming pdf_url is a local path.
            if paper_orm.paper_type == PaperType.ARXIV_PAPER:
                pdf_path = Path(pdf_download_basepath) / 'arxiv' / str(paper_orm.year) / f'{paper_orm.title}.pdf'
            elif paper_orm.paper_type == PaperType.CONFERENCE_PAPER:
                conference_name = paper_orm.venue
                pdf_path = Path(pdf_download_basepath) / 'conference' / conference_name / str(paper_orm.year) / f'{paper_orm.title}.pdf'
            else:
                logger.warning(f"Unsupported paper type: {paper_orm.paper_type}")
                continue

            # Check if the PDF file actually exists before proceeding
            if not pdf_path.exists():
                logger.warning(f"PDF file not found for paper {paper_orm.title}: {pdf_path}")
                continue
            
            paper_reader.set_file_path(pdf_path)

            # Extract abstract
            if paper_orm.abstract is None or len(paper_orm.abstract) == 0:
                abstract = paper_reader.extract_abstract()
                if abstract:
                    paper_orm.abstract = abstract
                    logger.info(f"Extracted abstract for {paper_orm.title}")

            # Extract tasks
            if paper_orm.primary_task is None or len(paper_orm.primary_task) == 0 or paper_orm.secondary_task is None or len(paper_orm.secondary_task) == 0 or paper_orm.tertiary_task is None or len(paper_orm.tertiary_task) == 0:
                tasks = paper_reader.extract_tasks()
                if tasks and len(tasks) > 0:
                    paper_orm.primary_task = tasks[0] if len(tasks) > 0 else None
                    paper_orm.secondary_task = tasks[1] if len(tasks) > 1 else None
                    paper_orm.tertiary_task = tasks[2] if len(tasks) > 2 else None
                    logger.info(f"Extracted tasks for {paper_orm.title}: {tasks}")
            
            # Extract methods
            if paper_orm.primary_method is None or len(paper_orm.primary_method) == 0 or paper_orm.secondary_method is None or len(paper_orm.secondary_method) == 0 or paper_orm.tertiary_method is None or len(paper_orm.tertiary_method) == 0:
                methods = paper_reader.extract_methods()
                if methods and len(methods) > 0:
                    paper_orm.primary_method = methods[0] if len(methods) > 0 else None
                    paper_orm.secondary_method = methods[1] if len(methods) > 1 else None
                    paper_orm.tertiary_method = methods[2] if len(methods) > 2 else None
                    logger.info(f"Extracted methods for {paper_orm.title}: {methods}")

            # Extract datasets and metrics
            if paper_orm.datasets_used is None or len(paper_orm.datasets_used) == 0 or paper_orm.metrics_used is None or len(paper_orm.metrics_used) == 0 or paper_orm.comparisons is None or len(paper_orm.comparisons) == 0:
                datasets, metrics, comparisons = paper_reader.extract_datasets_and_metrics()
                if datasets:
                    paper_orm.datasets_used = datasets
                if metrics:
                    paper_orm.metrics_used = metrics
                if comparisons:
                    paper_orm.comparisons = comparisons
                logger.info(f"Extracted datasets, metrics, and comparisons for {paper_orm.title}")

            # Extract limitations
            if paper_orm.limitations is None or len(paper_orm.limitations) == 0:
                limitations = paper_reader.extract_limitations()
                if limitations:
                    paper_orm.limitations = limitations
                    logger.info(f"Extracted limitations for {paper_orm.title}")
            
            session.add(paper_orm) # Add the updated ORM object to the session
            session.commit() # Commit changes for each paper
            logger.info(f"Successfully updated and committed paper: {paper_orm.title}")

        except Exception as e:
            session.rollback()
            logger.error(f"Error processing paper {paper_orm.title}: {e}")

    session.close()

if __name__ == "__main__":
    main() 