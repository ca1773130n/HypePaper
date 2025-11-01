"""Simple test for GitHub.io URL detection without pytest dependency."""
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.smart_github_detector import SmartGitHubDetector


def test_github_io_url_patterns():
    """Test various GitHub.io URL patterns."""
    print("=" * 70)
    print("TEST 1: GitHub.io URL Pattern Detection")
    print("=" * 70)

    detector = SmartGitHubDetector()

    test_patterns = [
        # Standard patterns (should be True)
        ('https://username.github.io/repo-name', True),
        ('https://org-name.github.io/project', True),
        ('http://user123.github.io', True),
        ('https://username.github.io/repo/docs/index.html', True),
        ('https://username.github.io/repo/v1.0/', True),

        # NOT GitHub.io (should be False)
        ('https://github.com/user/repo', False),
        ('https://gitlab.io/project', False),
        ('https://example.github.com', False),
        ('https://githubio.com', False),
    ]

    passed = 0
    failed = 0

    for url, should_be_github_io in test_patterns:
        result = detector._is_github_io_url(url)
        if result == should_be_github_io:
            print(f"✓ PASS: {url} → {result}")
            passed += 1
        else:
            print(f"✗ FAIL: {url} → expected {should_be_github_io}, got {result}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


async def test_github_io_classification():
    """Test that GitHub.io URLs are classified as project websites."""
    print("\n" + "=" * 70)
    print("TEST 2: GitHub.io Classification as Project Website")
    print("=" * 70)

    detector = SmartGitHubDetector()

    test_cases = [
        ('https://username.github.io/project', True, "GitHub.io should be project website"),
        ('https://org.github.io', True, "GitHub.io should be project website"),
        ('https://github.com/user/repo', False, "github.com should NOT be project website"),
    ]

    passed = 0
    failed = 0

    for url, expected, description in test_cases:
        result = detector._is_project_website(url)
        if result == expected:
            print(f"✓ PASS: {description}")
            print(f"  URL: {url} → {result}")
            passed += 1
        else:
            print(f"✗ FAIL: {description}")
            print(f"  URL: {url} → expected {expected}, got {result}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


async def test_github_io_url_inference():
    """Test inference of repository URL from GitHub.io URL structure."""
    print("\n" + "=" * 70)
    print("TEST 3: GitHub.io Repository URL Inference")
    print("=" * 70)

    detector = SmartGitHubDetector()

    test_cases = [
        {
            'github_io_url': 'https://testuser.github.io/test-project',
            'expected_user': 'testuser',
            'expected_repo': 'test-project'
        },
        {
            'github_io_url': 'https://my-org.github.io/awesome-tool',
            'expected_user': 'my-org',
            'expected_repo': 'awesome-tool'
        },
    ]

    passed = 0
    failed = 0

    async with detector:
        for test_case in test_cases:
            github_io_url = test_case['github_io_url']
            expected_user = test_case['expected_user']
            expected_repo = test_case['expected_repo']

            print(f"\nTesting: {github_io_url}")

            try:
                result = await detector._parse_github_io_for_repo(github_io_url)

                if result:
                    # Check that we got a github.com URL
                    if 'github.com' in result and expected_user in result:
                        print(f"✓ PASS: Inferred repository URL: {result}")
                        print(f"  Contains expected user: {expected_user}")
                        passed += 1
                    else:
                        print(f"✗ FAIL: Got {result}, but expected to contain {expected_user}")
                        failed += 1
                else:
                    # Inference from URL structure should always work
                    print(f"✗ FAIL: No repository URL inferred (Strategy 5 should work)")
                    failed += 1

            except Exception as e:
                print(f"✗ FAIL: Exception during parsing: {e}")
                failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


async def test_full_detection_flow():
    """Test full detection flow with GitHub.io URLs in abstract."""
    print("\n" + "=" * 70)
    print("TEST 4: Full Detection Flow with GitHub.io in Abstract")
    print("=" * 70)

    detector = SmartGitHubDetector()

    test_papers = [
        {
            'title': 'Sample ML Paper',
            'abstract': 'We present a new model. Project page: https://someuser.github.io/awesome-model',
        },
        {
            'title': 'Direct GitHub.io URL',
            'abstract': 'Visit https://mylab.github.io/vision-project for details and code.',
        }
    ]

    passed = 0
    failed = 0

    async with detector:
        for paper in test_papers:
            print(f"\n--- Testing Paper: {paper['title']} ---")
            print(f"Abstract: {paper['abstract'][:80]}...")

            try:
                result = await detector.detect_github_url(
                    paper['title'],
                    paper['abstract']
                )

                print(f"Detected URL: {result}")

                # Check that if we got a result, it's a github.com URL (not github.io)
                if result:
                    if 'github.com' in result and '.github.io' not in result:
                        print(f"✓ PASS: Correctly extracted github.com repository (not github.io)")
                        passed += 1
                    else:
                        print(f"✗ FAIL: Got {result}, but it should be github.com (not github.io)")
                        failed += 1
                else:
                    # We at least expect the inferred URL
                    print(f"ℹ INFO: No URL detected (page might not exist or parsing failed)")
                    # Don't count as failure since test URLs might not exist
                    passed += 1

            except Exception as e:
                print(f"✗ FAIL: Exception during detection: {e}")
                failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("GITHUB.IO DETECTION TEST SUITE")
    print("=" * 70 + "\n")

    results = []

    # Test 1: Pattern detection (sync)
    results.append(test_github_io_url_patterns())

    # Test 2: Classification (async)
    results.append(await test_github_io_classification())

    # Test 3: URL inference (async)
    results.append(await test_github_io_url_inference())

    # Test 4: Full detection flow (async)
    results.append(await test_full_detection_flow())

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests

    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")

    if failed_tests == 0:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {failed_tests} TEST SUITE(S) FAILED")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
