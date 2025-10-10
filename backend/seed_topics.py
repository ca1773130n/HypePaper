"""Seed system topics in Supabase database."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.models import Topic
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

SYSTEM_TOPICS = [
    {
        "name": "machine learning",
        "description": "Machine Learning and AI",
        "keywords": ["machine learning", "ML", "AI", "deep learning", "neural network"],
    },
    {
        "name": "computer vision",
        "description": "Computer Vision",
        "keywords": ["computer vision", "CV", "image", "video", "visual", "detection", "segmentation"],
    },
    {
        "name": "natural language processing",
        "description": "Natural Language Processing",
        "keywords": ["NLP", "natural language", "text", "language model", "LLM", "transformer"],
    },
    {
        "name": "reinforcement learning",
        "description": "Reinforcement Learning",
        "keywords": ["reinforcement learning", "RL", "agent", "policy", "reward"],
    },
    {
        "name": "robotics",
        "description": "Robotics and Automation",
        "keywords": ["robot", "robotics", "automation", "control", "manipulation"],
    },
]


async def seed_topics():
    """Seed system topics."""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for topic_data in SYSTEM_TOPICS:
            # Check if topic already exists
            result = await session.execute(
                select(Topic).where(Topic.name == topic_data["name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Topic '{topic_data['name']}' already exists, skipping...")
                continue

            # Create new topic
            topic = Topic(
                name=topic_data["name"],
                description=topic_data["description"],
                keywords=topic_data["keywords"],
                is_system=True,
                user_id=None,
            )
            session.add(topic)
            print(f"Created topic: {topic_data['name']}")

        await session.commit()
        print("\n✅ Seeding completed!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_topics())
