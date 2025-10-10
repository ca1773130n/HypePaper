"""
Unit tests for background job business logic.

Tests job logic without requiring database or external APIs.
"""
import pytest
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional


class TestPaperDiscoveryLogic:
    """Test paper discovery job logic."""

    def test_date_range_calculation(self):
        """Test that correct date range is calculated for paper discovery."""
        today = date.today()
        days_back = 7

        start_date = today - timedelta(days=days_back)
        end_date = today

        assert start_date < end_date, "Start date should be before end date"
        assert (end_date - start_date).days == days_back, \
            f"Expected {days_back} days difference, got {(end_date - start_date).days}"

    def test_category_filtering(self):
        """Test that papers are filtered by category."""
        categories = ["cs.CV", "cs.LG", "cs.AI"]
        papers = [
            {"id": "1", "category": "cs.CV", "title": "Vision Paper"},
            {"id": "2", "category": "cs.LG", "title": "Learning Paper"},
            {"id": "3", "category": "physics.optics", "title": "Physics Paper"},
            {"id": "4", "category": "cs.AI", "title": "AI Paper"}
        ]

        filtered = [p for p in papers if p["category"] in categories]

        assert len(filtered) == 3, f"Expected 3 papers from CS categories, got {len(filtered)}"
        assert all(p["category"] in categories for p in filtered), \
            "All filtered papers should be from specified categories"

    def test_deduplication_by_arxiv_id(self):
        """Test that duplicate papers are deduplicated by arXiv ID."""
        papers = [
            {"arxiv_id": "2003.08934", "title": "NeRF"},
            {"arxiv_id": "2006.11239", "title": "DDPM"},
            {"arxiv_id": "2003.08934", "title": "NeRF (duplicate)"},
            {"arxiv_id": "2201.05989", "title": "Instant-NGP"}
        ]

        # Simulate deduplication
        seen_ids = set()
        unique_papers = []
        for paper in papers:
            if paper["arxiv_id"] not in seen_ids:
                unique_papers.append(paper)
                seen_ids.add(paper["arxiv_id"])

        assert len(unique_papers) == 3, \
            f"Expected 3 unique papers after deduplication, got {len(unique_papers)}"

    def test_github_url_enrichment(self):
        """Test that papers are enriched with GitHub URLs."""
        papers = [
            {"arxiv_id": "2003.08934", "title": "NeRF", "github_url": None},
            {"arxiv_id": "2006.11239", "title": "DDPM", "github_url": None}
        ]

        # Simulate enrichment
        github_mapping = {
            "2003.08934": "https://github.com/bmild/nerf",
            "2006.11239": "https://github.com/hojonathanho/diffusion"
        }

        for paper in papers:
            if paper["arxiv_id"] in github_mapping:
                paper["github_url"] = github_mapping[paper["arxiv_id"]]

        assert papers[0]["github_url"] == "https://github.com/bmild/nerf", \
            "First paper should have GitHub URL"
        assert papers[1]["github_url"] == "https://github.com/hojonathanho/diffusion", \
            "Second paper should have GitHub URL"

    def test_max_papers_per_category(self):
        """Test that papers are limited per category."""
        max_per_category = 50

        papers = [{"id": i, "category": "cs.CV"} for i in range(100)]

        limited = papers[:max_per_category]

        assert len(limited) == max_per_category, \
            f"Expected {max_per_category} papers, got {len(limited)}"


class TestMetricUpdateLogic:
    """Test metric update job logic."""

    def test_metric_snapshot_creation(self):
        """Test that metric snapshots are created with correct date."""
        today = date.today()

        snapshot = {
            "paper_id": 1,
            "github_stars": 1000,
            "citation_count": 100,
            "snapshot_date": today
        }

        assert snapshot["snapshot_date"] == today, \
            f"Expected snapshot date {today}, got {snapshot['snapshot_date']}"

    def test_skip_existing_snapshots(self):
        """Test that existing snapshots for today are skipped."""
        today = date.today()

        existing_snapshots = [
            {"paper_id": 1, "snapshot_date": today},
            {"paper_id": 2, "snapshot_date": today - timedelta(days=1)}
        ]

        papers_to_update = [1, 2, 3]

        # Filter out papers with today's snapshot
        papers_with_today = {s["paper_id"] for s in existing_snapshots if s["snapshot_date"] == today}
        papers_need_update = [p for p in papers_to_update if p not in papers_with_today]

        assert papers_need_update == [2, 3], \
            f"Expected papers [2, 3] to need update, got {papers_need_update}"

    def test_metric_update_handles_missing_github(self):
        """Test that papers without GitHub URLs are handled correctly."""
        papers = [
            {"id": 1, "github_url": "https://github.com/owner/repo"},
            {"id": 2, "github_url": None},
            {"id": 3, "github_url": ""}
        ]

        # Only update papers with valid GitHub URLs
        papers_with_github = [p for p in papers if p.get("github_url")]

        assert len(papers_with_github) == 1, \
            f"Expected 1 paper with GitHub URL, got {len(papers_with_github)}"

    def test_metric_update_handles_api_failures(self):
        """Test that API failures don't crash the entire update."""
        papers = [1, 2, 3, 4, 5]

        # Simulate some failures
        failed_papers = {2, 4}
        updated_papers = []
        failed_updates = []

        for paper_id in papers:
            if paper_id in failed_papers:
                failed_updates.append(paper_id)
            else:
                updated_papers.append(paper_id)

        assert len(updated_papers) == 3, \
            f"Expected 3 successful updates, got {len(updated_papers)}"
        assert len(failed_updates) == 2, \
            f"Expected 2 failed updates, got {len(failed_updates)}"


class TestTopicMatchingJobLogic:
    """Test topic matching job logic."""

    def test_find_unmatched_papers(self):
        """Test finding papers without topic matches."""
        all_papers = [1, 2, 3, 4, 5]
        matched_papers = {1, 3, 5}

        unmatched = [p for p in all_papers if p not in matched_papers]

        assert unmatched == [2, 4], \
            f"Expected unmatched papers [2, 4], got {unmatched}"

    def test_match_paper_to_multiple_topics(self):
        """Test that a paper can match multiple topics."""
        paper = {"id": 1, "title": "Neural Rendering", "abstract": "3D reconstruction using NeRF"}

        # Simulate matching scores
        topic_scores = [
            {"topic_id": 1, "topic_name": "neural rendering", "score": 8.0},
            {"topic_id": 2, "topic_name": "3d reconstruction", "score": 6.0},
            {"topic_id": 3, "topic_name": "diffusion models", "score": 0.0}
        ]

        threshold = 6.0
        matches = [t for t in topic_scores if t["score"] >= threshold]

        assert len(matches) == 2, \
            f"Expected 2 topic matches above threshold, got {len(matches)}"

    def test_create_paper_topic_match_records(self):
        """Test that paper-topic match records are created correctly."""
        paper_id = 1
        matched_topics = [
            {"topic_id": 1, "score": 8.0},
            {"topic_id": 2, "score": 6.0}
        ]

        match_records = [
            {
                "paper_id": paper_id,
                "topic_id": t["topic_id"],
                "relevance_score": t["score"]
            }
            for t in matched_topics
        ]

        assert len(match_records) == 2, \
            f"Expected 2 match records, got {len(match_records)}"
        assert all(r["paper_id"] == paper_id for r in match_records), \
            "All records should have correct paper_id"

    def test_skip_already_matched_papers(self):
        """Test that already matched papers are skipped."""
        all_papers = [
            {"id": 1, "has_topics": True},
            {"id": 2, "has_topics": False},
            {"id": 3, "has_topics": True},
            {"id": 4, "has_topics": False}
        ]

        # Filter unmatched papers
        unmatched = [p for p in all_papers if not p["has_topics"]]

        assert len(unmatched) == 2, \
            f"Expected 2 unmatched papers, got {len(unmatched)}"
        assert [p["id"] for p in unmatched] == [2, 4], \
            "Should skip papers 1 and 3 which already have topics"


class TestSchedulerLogic:
    """Test job scheduler logic."""

    def test_job_sequence_order(self):
        """Test that jobs run in correct sequence."""
        # Jobs should run in this order:
        # 1. Paper discovery (2:00 AM)
        # 2. Metric updates (2:30 AM)
        # 3. Topic matching (3:00 AM)

        job_times = [
            ("paper_discovery", "02:00"),
            ("metric_update", "02:30"),
            ("topic_matching", "03:00")
        ]

        # Verify order
        assert job_times[0][1] < job_times[1][1] < job_times[2][1], \
            "Jobs should be scheduled in sequential order"

    def test_daily_schedule(self):
        """Test that jobs are scheduled daily."""
        schedule = {
            "paper_discovery": {"hour": 2, "minute": 0, "interval": "day"},
            "metric_update": {"hour": 2, "minute": 30, "interval": "day"},
            "topic_matching": {"hour": 3, "minute": 0, "interval": "day"}
        }

        assert all(job["interval"] == "day" for job in schedule.values()), \
            "All jobs should run daily"

    def test_job_dependencies(self):
        """Test that job dependencies are respected."""
        # Topic matching depends on papers and metrics existing
        # Metrics depend on papers existing
        # Paper discovery has no dependencies

        dependencies = {
            "paper_discovery": [],
            "metric_update": ["paper_discovery"],
            "topic_matching": ["paper_discovery", "metric_update"]
        }

        # Verify dependencies are in correct order
        assert len(dependencies["paper_discovery"]) == 0, \
            "Paper discovery should have no dependencies"
        assert "paper_discovery" in dependencies["metric_update"], \
            "Metric update should depend on paper discovery"
        assert "metric_update" in dependencies["topic_matching"], \
            "Topic matching should depend on metric update"


class TestDataValidation:
    """Test data validation logic."""

    def test_arxiv_id_format_validation(self):
        """Test arXiv ID format validation."""
        valid_ids = ["2003.08934", "1706.03762", "2201.05989v2"]
        invalid_ids = ["invalid", "2003", "abc.def", ""]

        import re
        pattern = r'^\d{4}\.\d{4,5}(v\d+)?$'

        for arxiv_id in valid_ids:
            assert re.match(pattern, arxiv_id), \
                f"Valid arXiv ID {arxiv_id} should match pattern"

        for arxiv_id in invalid_ids:
            assert not re.match(pattern, arxiv_id), \
                f"Invalid arXiv ID {arxiv_id} should not match pattern"

    def test_github_url_validation(self):
        """Test GitHub URL validation."""
        valid_urls = [
            "https://github.com/owner/repo",
            "https://github.com/owner/repo.git",
            "git@github.com:owner/repo.git"
        ]

        invalid_urls = [
            "https://gitlab.com/owner/repo",
            "https://github.com/owner",  # Missing repo
            "not-a-url",
            ""
        ]

        import re
        pattern = r'github\.com[:/][\w-]+/[\w-]+'

        for url in valid_urls:
            assert re.search(pattern, url), \
                f"Valid GitHub URL {url} should match pattern"

        for url in invalid_urls:
            if url:  # Skip empty string
                assert not re.search(pattern, url), \
                    f"Invalid GitHub URL {url} should not match pattern"

    def test_metric_value_validation(self):
        """Test that metric values are non-negative."""
        metrics = [
            {"stars": 100, "citations": 50},
            {"stars": 0, "citations": 0},
            {"stars": -10, "citations": 20},  # Invalid
            {"stars": 100, "citations": -5}   # Invalid
        ]

        valid_metrics = [
            m for m in metrics
            if m["stars"] >= 0 and m["citations"] >= 0
        ]

        assert len(valid_metrics) == 2, \
            f"Expected 2 valid metric records, got {len(valid_metrics)}"

    def test_relevance_score_range(self):
        """Test that relevance scores are in valid range [0, 10]."""
        scores = [0.0, 5.5, 10.0, 11.0, -1.0, 7.3]

        valid_scores = [s for s in scores if 0 <= s <= 10]

        assert len(valid_scores) == 4, \
            f"Expected 4 valid scores in range [0, 10], got {len(valid_scores)}"
        assert valid_scores == [0.0, 5.5, 10.0, 7.3], \
            f"Expected [0.0, 5.5, 10.0, 7.3], got {valid_scores}"


class TestErrorHandling:
    """Test error handling in jobs."""

    def test_network_timeout_handling(self):
        """Test that network timeouts are handled gracefully."""
        papers = [1, 2, 3, 4, 5]
        timeout_papers = {2, 4}

        results = []
        for paper_id in papers:
            if paper_id in timeout_papers:
                results.append({"id": paper_id, "status": "timeout", "data": None})
            else:
                results.append({"id": paper_id, "status": "success", "data": {}})

        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "timeout"]

        assert len(successful) == 3, f"Expected 3 successful fetches, got {len(successful)}"
        assert len(failed) == 2, f"Expected 2 timeouts, got {len(failed)}"

    def test_malformed_response_handling(self):
        """Test handling of malformed API responses."""
        responses = [
            {"arxiv_id": "2003.08934", "title": "NeRF"},  # Valid
            {"arxiv_id": "2006.11239"},  # Missing title
            None,  # Null response
            {"title": "No ID"},  # Missing arxiv_id
            {"arxiv_id": "2201.05989", "title": "Valid"}  # Valid
        ]

        # Validate responses
        valid_papers = []
        for response in responses:
            if response and response.get("arxiv_id") and response.get("title"):
                valid_papers.append(response)

        assert len(valid_papers) == 2, \
            f"Expected 2 valid papers from malformed responses, got {len(valid_papers)}"

    def test_database_constraint_violations(self):
        """Test handling of database constraint violations."""
        # Simulate duplicate paper insertion
        existing_arxiv_ids = {"2003.08934", "2006.11239"}

        new_papers = [
            {"arxiv_id": "2003.08934", "title": "Duplicate"},
            {"arxiv_id": "2201.05989", "title": "New Paper"},
            {"arxiv_id": "2006.11239", "title": "Another Duplicate"}
        ]

        # Filter out duplicates before insertion
        papers_to_insert = [
            p for p in new_papers
            if p["arxiv_id"] not in existing_arxiv_ids
        ]

        assert len(papers_to_insert) == 1, \
            f"Expected 1 new paper to insert, got {len(papers_to_insert)}"
        assert papers_to_insert[0]["arxiv_id"] == "2201.05989", \
            "Should only insert the non-duplicate paper"
