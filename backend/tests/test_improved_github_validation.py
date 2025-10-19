#!/usr/bin/env python3
"""Test improved GitHub validation to prevent daily-ai-papers type assignments."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.smart_github_detector import SmartGitHubDetector


async def test_improved_validation():
    """Test that improved validation catches daily-ai-papers type repositories."""

    print("=" * 80)
    print("TESTING IMPROVED GITHUB VALIDATION")
    print("=" * 80)

    async with SmartGitHubDetector() as detector:
        # Test cases that should be rejected
        bad_repos = [
            "https://github.com/gabrielchua/daily-ai-papers",
            "https://github.com/someone/awesome-ai-papers",
            "https://github.com/user/ml-papers-digest",
            "https://github.com/test/trending-papers",
        ]

        print("Testing repositories that should be REJECTED:")
        for repo_url in bad_repos:
            is_valid = await detector._is_valid_implementation_repo(repo_url, "Test Paper Title")
            status = "✅ PASSED (correctly rejected)" if not is_valid else "❌ FAILED (incorrectly accepted)"
            print(f"  {repo_url}: {status}")

        print("\nTesting repositories that should be ACCEPTED:")
        # Test cases that should be accepted (if they exist and have implementation files)
        good_repos = [
            "https://github.com/pytorch/pytorch",
            "https://github.com/tensorflow/tensorflow",
        ]

        for repo_url in good_repos:
            is_valid = await detector._is_valid_implementation_repo(repo_url, "Test Paper Title")
            status = "✅ PASSED (correctly accepted)" if is_valid else "⚠️  REJECTED (but might be valid - check manually)"
            print(f"  {repo_url}: {status}")

    print("\n" + "=" * 80)
    print("VALIDATION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_improved_validation())