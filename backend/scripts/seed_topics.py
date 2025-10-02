"""Seed predefined topics into the database.

Inserts initial topics for the MVP:
- Neural rendering
- Diffusion models
- 3D reconstruction
- And others related to computer vision and machine learning
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import AsyncSessionLocal
from src.services import TopicService


PREDEFINED_TOPICS = [
    {
        "name": "neural rendering",
        "description": "Novel view synthesis, NeRF, neural radiance fields, and related techniques",
        "keywords": ["nerf", "neural radiance", "view synthesis", "novel view", "volumetric rendering"],
    },
    {
        "name": "diffusion models",
        "description": "Diffusion-based generative models for images, video, and 3D content",
        "keywords": ["diffusion", "denoising", "score matching", "stable diffusion", "imagen"],
    },
    {
        "name": "3d reconstruction",
        "description": "Reconstructing 3D geometry and appearance from images or videos",
        "keywords": ["3d reconstruction", "structure from motion", "sfm", "mvs", "multiview"],
    },
    {
        "name": "large language models",
        "description": "Foundation models for natural language understanding and generation",
        "keywords": ["llm", "gpt", "transformer", "language model", "bert"],
    },
    {
        "name": "computer vision",
        "description": "General computer vision tasks including detection, segmentation, tracking",
        "keywords": ["detection", "segmentation", "tracking", "object recognition", "vision"],
    },
    {
        "name": "reinforcement learning",
        "description": "RL algorithms, policy learning, and interactive agents",
        "keywords": ["reinforcement", "policy", "q-learning", "actor-critic", "rl"],
    },
    {
        "name": "multimodal learning",
        "description": "Models that combine vision, language, and other modalities",
        "keywords": ["multimodal", "vision-language", "clip", "cross-modal", "alignment"],
    },
    {
        "name": "generative adversarial networks",
        "description": "GAN-based approaches for image and content generation",
        "keywords": ["gan", "generator", "discriminator", "adversarial", "stylegan"],
    },
    {
        "name": "self-supervised learning",
        "description": "Learning representations without manual labels",
        "keywords": ["self-supervised", "contrastive", "pretraining", "representation learning"],
    },
    {
        "name": "few-shot learning",
        "description": "Learning from limited labeled examples",
        "keywords": ["few-shot", "meta-learning", "one-shot", "zero-shot", "prototypical"],
    },
]


async def seed_topics():
    """Seed topics into the database."""
    print("Seeding topics...")

    async with AsyncSessionLocal() as session:
        topic_service = TopicService(session)
        created_count = 0

        for topic_data in PREDEFINED_TOPICS:
            try:
                # Check if topic already exists
                existing = await topic_service.get_topic_by_name(topic_data["name"])

                if existing:
                    print(f"Topic '{topic_data['name']}' already exists, skipping")
                    continue

                # Create topic
                await topic_service.create_topic(topic_data)
                created_count += 1
                print(f"Created topic: {topic_data['name']}")

            except Exception as e:
                print(f"Error creating topic '{topic_data['name']}': {e}")
                continue

        await session.commit()
        print(f"\nSeeding complete: {created_count} topics created")


if __name__ == "__main__":
    asyncio.run(seed_topics())
