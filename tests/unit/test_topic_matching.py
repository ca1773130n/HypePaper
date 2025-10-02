"""
Unit tests for topic matching service logic.

Tests topic matching without database or LLM dependencies.
"""
import pytest
from typing import List


class MockTopic:
    """Mock topic for testing."""
    def __init__(self, id: int, name: str, keywords: List[str]):
        self.id = id
        self.name = name
        self.keywords = keywords


class MockPaper:
    """Mock paper for testing."""
    def __init__(self, id: int, title: str, abstract: str):
        self.id = id
        self.title = title
        self.abstract = abstract


def calculate_keyword_relevance(paper: MockPaper, topic: MockTopic) -> float:
    """
    Calculate relevance score based on keyword matching.

    Returns score from 0-10 based on keyword matches.
    """
    combined_text = f"{paper.title} {paper.abstract}".lower()

    # Count unique keyword matches
    matches = set()
    for keyword in topic.keywords:
        if keyword.lower() in combined_text:
            matches.add(keyword.lower())

    # Score: 2 points per match, max 10
    score = min(len(matches) * 2, 10)
    return float(score)


class TestTopicMatchingService:
    """Test suite for topic matching logic."""

    def test_exact_keyword_match(self):
        """Test paper with exact keyword matches gets high relevance."""
        topic = MockTopic(
            id=1,
            name="neural rendering",
            keywords=["nerf", "neural radiance fields", "view synthesis", "novel view"]
        )

        paper = MockPaper(
            id=1,
            title="Neural Radiance Fields for View Synthesis",
            abstract="We present NeRF, a method for novel view synthesis using neural radiance fields"
        )

        score = calculate_keyword_relevance(paper, topic)

        # Should match: nerf, neural radiance fields, view synthesis, novel view = 4 keywords = 8 points
        assert score >= 6.0, f"Expected relevance >= 6.0 for strong keyword match, got {score}"

    def test_partial_keyword_match(self):
        """Test paper with some keyword matches gets medium relevance."""
        topic = MockTopic(
            id=2,
            name="diffusion models",
            keywords=["diffusion", "denoising", "ddpm", "score matching", "generative"]
        )

        paper = MockPaper(
            id=2,
            title="Denoising Diffusion Models for Image Generation",
            abstract="A new approach to generative modeling using diffusion processes"
        )

        score = calculate_keyword_relevance(paper, topic)

        # Should match: diffusion, denoising, generative = 3 keywords = 6 points
        assert 4.0 <= score <= 8.0, \
            f"Expected relevance between 4-8 for partial match, got {score}"

    def test_no_keyword_match(self):
        """Test paper with no keyword matches gets zero relevance."""
        topic = MockTopic(
            id=3,
            name="quantum computing",
            keywords=["quantum", "qubits", "superposition", "entanglement"]
        )

        paper = MockPaper(
            id=3,
            title="Deep Learning for Image Classification",
            abstract="We use convolutional neural networks for classifying images"
        )

        score = calculate_keyword_relevance(paper, topic)

        assert score == 0.0, f"Expected 0 relevance for no keyword match, got {score}"

    def test_case_insensitive_matching(self):
        """Test that keyword matching is case insensitive."""
        topic = MockTopic(
            id=4,
            name="transformers",
            keywords=["transformer", "attention", "bert", "gpt"]
        )

        paper = MockPaper(
            id=4,
            title="TRANSFORMERS: Attention Is All You Need",
            abstract="We propose the TRANSFORMER architecture using ATTENTION mechanisms"
        )

        score = calculate_keyword_relevance(paper, topic)

        # Should match transformer and attention regardless of case
        assert score >= 4.0, \
            f"Expected relevance >= 4.0 for case-insensitive match, got {score}"

    def test_keyword_in_title_counts(self):
        """Test that keywords in title are counted."""
        topic = MockTopic(
            id=5,
            name="3d reconstruction",
            keywords=["3d reconstruction", "structure from motion", "slam"]
        )

        paper = MockPaper(
            id=5,
            title="3D Reconstruction from Images",  # Keyword in title
            abstract="A method for reconstructing scenes"
        )

        score = calculate_keyword_relevance(paper, topic)

        assert score >= 2.0, \
            f"Expected relevance >= 2.0 when keyword in title, got {score}"

    def test_keyword_in_abstract_counts(self):
        """Test that keywords in abstract are counted."""
        topic = MockTopic(
            id=6,
            name="reinforcement learning",
            keywords=["reinforcement learning", "q-learning", "policy gradient", "dqn"]
        )

        paper = MockPaper(
            id=6,
            title="Learning to Play Games",
            abstract="We use reinforcement learning with Q-learning and DQN algorithms"
        )

        score = calculate_keyword_relevance(paper, topic)

        # Should match: reinforcement learning, q-learning, dqn = 3 keywords = 6 points
        assert score >= 6.0, \
            f"Expected relevance >= 6.0 for keywords in abstract, got {score}"

    def test_duplicate_keyword_counts_once(self):
        """Test that same keyword appearing multiple times counts once."""
        topic = MockTopic(
            id=7,
            name="gans",
            keywords=["gan", "generative adversarial", "discriminator", "generator"]
        )

        paper = MockPaper(
            id=7,
            title="GAN-based Image Synthesis using GANs",
            abstract="Generative adversarial networks (GANs) use a GAN architecture"
        )

        score = calculate_keyword_relevance(paper, topic)

        # "gan" appears 3 times but should count once
        # Should match: gan, generative adversarial = 2 unique keywords = 4 points
        assert score == 4.0, \
            f"Expected relevance = 4.0 (2 unique keywords), got {score}"

    def test_threshold_filtering(self):
        """Test that papers below relevance threshold are filtered."""
        threshold = 6.0

        topic = MockTopic(
            id=8,
            name="computer vision",
            keywords=["vision", "image", "detection", "segmentation", "classification"]
        )

        high_relevance_paper = MockPaper(
            id=8,
            title="Image Segmentation for Computer Vision",
            abstract="Object detection and classification using vision transformers"
        )

        low_relevance_paper = MockPaper(
            id=9,
            title="Natural Language Processing",
            abstract="Text classification using transformers"
        )

        high_score = calculate_keyword_relevance(high_relevance_paper, topic)
        low_score = calculate_keyword_relevance(low_relevance_paper, topic)

        assert high_score >= threshold, \
            f"High relevance paper should pass threshold, got {high_score}"
        assert low_score < threshold, \
            f"Low relevance paper should fail threshold, got {low_score}"

    def test_max_score_capped_at_10(self):
        """Test that relevance score is capped at 10."""
        topic = MockTopic(
            id=9,
            name="deep learning",
            keywords=["deep learning", "neural network", "cnn", "rnn", "lstm",
                     "transformer", "attention", "backprop", "sgd", "batch norm"]
        )

        paper = MockPaper(
            id=10,
            title="Deep Learning: CNNs, RNNs, LSTMs, and Transformers",
            abstract="Neural networks with attention, trained using SGD and batch norm via backprop"
        )

        score = calculate_keyword_relevance(paper, topic)

        # Even with 9 keyword matches (18 points), should cap at 10
        assert score == 10.0, f"Expected max score of 10.0, got {score}"


class TestMultiTopicMatching:
    """Test matching a paper to multiple topics."""

    def test_paper_matches_multiple_topics(self):
        """Test that a paper can match multiple relevant topics."""
        topics = [
            MockTopic(1, "neural rendering", ["neural", "rendering", "view synthesis"]),
            MockTopic(2, "3d reconstruction", ["3d", "reconstruction", "geometry"]),
            MockTopic(3, "deep learning", ["neural", "network", "deep learning"])
        ]

        paper = MockPaper(
            id=1,
            title="Neural 3D Reconstruction and Rendering",
            abstract="Using deep neural networks for 3D geometry reconstruction and view synthesis"
        )

        matches = []
        for topic in topics:
            score = calculate_keyword_relevance(paper, topic)
            if score >= 6.0:
                matches.append((topic.name, score))

        # Should match at least 2 topics
        assert len(matches) >= 2, \
            f"Expected paper to match multiple topics, got {len(matches)}: {matches}"

    def test_paper_matches_best_topic(self):
        """Test that paper is matched to most relevant topic."""
        topics = [
            MockTopic(1, "diffusion models", ["diffusion", "denoising", "ddpm", "probabilistic"]),
            MockTopic(2, "generative models", ["generative", "gan", "vae"]),
            MockTopic(3, "image synthesis", ["synthesis", "generation", "image"])
        ]

        paper = MockPaper(
            id=2,
            title="Denoising Diffusion Probabilistic Models",
            abstract="A new diffusion-based approach for image generation using denoising"
        )

        scores = []
        for topic in topics:
            score = calculate_keyword_relevance(paper, topic)
            scores.append((topic.name, score))

        best_match = max(scores, key=lambda x: x[1])

        assert best_match[0] == "diffusion models", \
            f"Expected 'diffusion models' as best match, got '{best_match[0]}'"
        assert best_match[1] >= 6.0, \
            f"Expected high relevance for best match, got {best_match[1]}"

    def test_unrelated_paper_matches_no_topics(self):
        """Test that unrelated paper doesn't match any topics."""
        topics = [
            MockTopic(1, "computer vision", ["vision", "image", "detection"]),
            MockTopic(2, "nlp", ["language", "text", "nlp", "bert"]),
            MockTopic(3, "reinforcement learning", ["rl", "policy", "reward"])
        ]

        paper = MockPaper(
            id=3,
            title="Quantum Computing for Cryptography",
            abstract="Using quantum algorithms for secure encryption"
        )

        threshold = 6.0
        matches = []
        for topic in topics:
            score = calculate_keyword_relevance(paper, topic)
            if score >= threshold:
                matches.append((topic.name, score))

        assert len(matches) == 0, \
            f"Expected no matches for unrelated paper, got {len(matches)}: {matches}"


class TestEdgeCases:
    """Test edge cases in topic matching."""

    def test_empty_keywords(self):
        """Test topic with no keywords returns 0 relevance."""
        topic = MockTopic(id=1, name="test topic", keywords=[])
        paper = MockPaper(id=1, title="Test Paper", abstract="This is a test")

        score = calculate_keyword_relevance(paper, topic)

        assert score == 0.0, f"Expected 0 relevance for empty keywords, got {score}"

    def test_empty_paper_text(self):
        """Test paper with no title/abstract returns 0 relevance."""
        topic = MockTopic(id=1, name="test", keywords=["test", "keyword"])
        paper = MockPaper(id=1, title="", abstract="")

        score = calculate_keyword_relevance(paper, topic)

        assert score == 0.0, f"Expected 0 relevance for empty paper, got {score}"

    def test_special_characters_in_keywords(self):
        """Test keywords with special characters are matched correctly."""
        topic = MockTopic(
            id=1,
            name="3d vision",
            keywords=["3d", "2d-to-3d", "multi-view"]
        )

        paper = MockPaper(
            id=1,
            title="3D Reconstruction from Multi-View Images",
            abstract="Converting 2D-to-3D using multiple views"
        )

        score = calculate_keyword_relevance(paper, topic)

        # Should match all 3 keywords
        assert score >= 6.0, \
            f"Expected relevance >= 6.0 for special char keywords, got {score}"

    def test_numeric_keywords(self):
        """Test that numeric keywords are matched."""
        topic = MockTopic(
            id=1,
            name="architectures",
            keywords=["resnet", "vgg16", "alexnet", "inception-v3"]
        )

        paper = MockPaper(
            id=1,
            title="Comparing ResNet and VGG16 Architectures",
            abstract="We evaluate Inception-v3 against AlexNet"
        )

        score = calculate_keyword_relevance(paper, topic)

        # Should match resnet, vgg16, inception-v3, alexnet = 4 keywords
        assert score >= 6.0, \
            f"Expected relevance >= 6.0 for numeric keywords, got {score}"
