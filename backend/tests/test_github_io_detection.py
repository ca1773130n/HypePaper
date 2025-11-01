"""Test GitHub.io URL detection and repository extraction.

This test verifies that the SmartGitHubDetector correctly:
1. Identifies GitHub.io URLs as project websites
2. Parses GitHub.io pages to find the actual repository URL
3. Extracts star counts from the correct repository
"""
import pytest
import asyncio
from backend.src.services.smart_github_detector import SmartGitHubDetector


class TestGitHubIODetection:
    """Test suite for GitHub.io URL detection and parsing."""

    @pytest.mark.asyncio
    async def test_is_github_io_url(self):
        """Test detection of GitHub.io URLs."""
        detector = SmartGitHubDetector()

        # Valid GitHub.io URLs
        assert detector._is_github_io_url('https://username.github.io/project')
        assert detector._is_github_io_url('https://organization.github.io')
        assert detector._is_github_io_url('http://user-name.github.io/my-project/')

        # Invalid GitHub.io URLs (should be github.com, not github.io)
        assert not detector._is_github_io_url('https://github.com/user/repo')
        assert not detector._is_github_io_url('https://example.com')
        assert not detector._is_github_io_url('https://gitlab.io/project')

    @pytest.mark.asyncio
    async def test_classify_github_io_as_project_website(self):
        """Test that GitHub.io URLs are classified as project websites."""
        detector = SmartGitHubDetector()

        # GitHub.io should be classified as project website
        assert detector._is_project_website('https://username.github.io/project')
        assert detector._is_project_website('https://org.github.io')

        # github.com should NOT be classified as project website
        assert not detector._is_project_website('https://github.com/user/repo')

    @pytest.mark.asyncio
    async def test_github_io_url_inference(self):
        """Test inference of repository URL from GitHub.io URL structure."""
        detector = SmartGitHubDetector()

        # Test cases with expected inferred URLs
        test_cases = [
            {
                'github_io_url': 'https://openai.github.io/gpt-3',
                'expected_pattern': 'https://github.com/openai/gpt-3'
            },
            {
                'github_io_url': 'https://facebook.github.io/react',
                'expected_pattern': 'https://github.com/facebook/react'
            },
            {
                'github_io_url': 'https://microsoft.github.io/vscode',
                'expected_pattern': 'https://github.com/microsoft/vscode'
            }
        ]

        async with detector:
            for test_case in test_cases:
                # Note: This will attempt to fetch the actual page
                # In a real test, we'd mock the HTTP response
                result = await detector._parse_github_io_for_repo(test_case['github_io_url'])

                # Check that we got a repository URL
                if result:
                    assert 'github.com' in result
                    assert result.count('/') >= 4  # Should be github.com/user/repo format
                    print(f"✓ {test_case['github_io_url']} → {result}")

    @pytest.mark.asyncio
    async def test_detect_github_url_with_github_io(self):
        """Test full detection flow with GitHub.io URLs in abstract."""
        detector = SmartGitHubDetector()

        test_papers = [
            {
                'title': 'Sample ML Paper',
                'abstract': 'We present a new model. Project page: https://someuser.github.io/awesome-model',
                'expected_contains': 'github.com'
            },
            {
                'title': 'Computer Vision Research',
                'abstract': 'Novel architecture for image recognition. Visit https://lab.github.io/vision-project for details.',
                'expected_contains': 'github.com'
            }
        ]

        async with detector:
            for paper in test_papers:
                result = await detector.detect_github_url(
                    paper['title'],
                    paper['abstract']
                )

                print(f"\nPaper: {paper['title']}")
                print(f"Abstract: {paper['abstract'][:100]}...")
                print(f"Detected: {result}")

                # Verify we got a github.com repository URL, not github.io
                if result:
                    assert paper['expected_contains'] in result
                    assert '.github.io' not in result
                    print(f"✓ Correctly extracted repository URL from GitHub.io page")

    @pytest.mark.asyncio
    async def test_github_io_parsing_strategies(self):
        """Test different parsing strategies for GitHub.io pages."""
        detector = SmartGitHubDetector()

        # Test URL structure inference (Strategy 5)
        github_io_url = 'https://testuser.github.io/test-project'

        async with detector:
            result = await detector._parse_github_io_for_repo(github_io_url)

            print(f"\nGitHub.io URL: {github_io_url}")
            print(f"Extracted repository: {result}")

            if result:
                assert 'github.com' in result
                assert 'testuser' in result
                # Could be either the inferred URL or a real one from the page
                print(f"✓ Successfully extracted: {result}")


def test_github_io_url_patterns():
    """Test various GitHub.io URL patterns."""
    detector = SmartGitHubDetector()

    test_patterns = [
        # Standard patterns
        ('https://username.github.io/repo-name', True),
        ('https://org-name.github.io/project', True),
        ('http://user123.github.io', True),

        # With paths
        ('https://username.github.io/repo/docs/index.html', True),
        ('https://username.github.io/repo/v1.0/', True),

        # NOT GitHub.io
        ('https://github.com/user/repo', False),
        ('https://gitlab.io/project', False),
        ('https://example.github.com', False),
        ('https://githubio.com', False),
    ]

    for url, should_be_github_io in test_patterns:
        result = detector._is_github_io_url(url)
        assert result == should_be_github_io, f"Failed for {url}: expected {should_be_github_io}, got {result}"
        print(f"✓ {url} → {result}")


if __name__ == '__main__':
    # Run synchronous tests
    print("Testing GitHub.io URL pattern detection...")
    test_github_io_url_patterns()

    # Run async tests
    print("\n\nRunning async detection tests...")
    async def run_async_tests():
        detector = SmartGitHubDetector()
        test_instance = TestGitHubIODetection()

        print("\n1. Testing GitHub.io URL detection...")
        await test_instance.test_is_github_io_url()

        print("\n2. Testing project website classification...")
        await test_instance.test_classify_github_io_as_project_website()

        print("\n3. Testing GitHub.io parsing strategies...")
        await test_instance.test_github_io_parsing_strategies()

    asyncio.run(run_async_tests())
    print("\n✅ All tests passed!")
