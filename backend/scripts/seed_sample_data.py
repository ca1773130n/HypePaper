"""Seed sample papers and metrics for testing.

Creates ~50 sample papers with metadata and initial metric snapshots.
"""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path
from random import randint, random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import AsyncSessionLocal
from src.services import MetricService, PaperService


SAMPLE_PAPERS = [
    {
        "title": "Neural Radiance Fields for View Synthesis",
        "authors": ["Ben Mildenhall", "Pratul P. Srinivasan", "Matthew Tancik"],
        "abstract": "We present a method that achieves state-of-the-art results for synthesizing novel views of complex scenes by optimizing an underlying continuous volumetric scene function using a sparse set of input views.",
        "arxiv_id": "2003.08934",
        "published_date": date(2020, 3, 19),
        "venue": "ECCV 2020",
        "github_url": "https://github.com/bmild/nerf",
    },
    {
        "title": "Denoising Diffusion Probabilistic Models",
        "authors": ["Jonathan Ho", "Ajay Jain", "Pieter Abbeel"],
        "abstract": "We present high quality image synthesis results using diffusion probabilistic models, a class of latent variable models inspired by considerations from nonequilibrium thermodynamics.",
        "arxiv_id": "2006.11239",
        "published_date": date(2020, 6, 19),
        "venue": "NeurIPS 2020",
        "github_url": "https://github.com/hojonathanho/diffusion",
    },
    {
        "title": "Instant Neural Graphics Primitives",
        "authors": ["Thomas Müller", "Alex Evans", "Christoph Schied"],
        "abstract": "We present a versatile new input encoding that permits the use of a smaller network without sacrificing quality, thus significantly reducing the number of floating point operations required.",
        "arxiv_id": "2201.05989",
        "published_date": date(2022, 1, 16),
        "venue": "SIGGRAPH 2022",
        "github_url": "https://github.com/NVlabs/instant-ngp",
    },
    {
        "title": "CLIP: Learning Transferable Visual Models",
        "authors": ["Alec Radford", "Jong Wook Kim", "Chris Hallacy"],
        "abstract": "State-of-the-art computer vision systems are trained to predict a fixed set of predetermined object categories. We present a simple pre-training task that efficiently learns visual concepts from natural language supervision.",
        "arxiv_id": "2103.00020",
        "published_date": date(2021, 2, 26),
        "venue": "ICML 2021",
        "github_url": "https://github.com/openai/CLIP",
    },
    {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
        "arxiv_id": "1706.03762",
        "published_date": date(2017, 6, 12),
        "venue": "NeurIPS 2017",
        "github_url": "https://github.com/tensorflow/tensor2tensor",
    },
]

# Additional titles for bulk generation
ADDITIONAL_TITLES = [
    "Self-Supervised Learning of Visual Features",
    "Few-Shot Learning with Meta-Learning",
    "3D Gaussian Splatting for Real-Time Rendering",
    "Segment Anything: A Foundation Model for Image Segmentation",
    "DreamFusion: Text-to-3D using 2D Diffusion",
    "Plenoxels: Radiance Fields without Neural Networks",
    "MipNeRF 360: Unbounded Anti-Aliased Neural Radiance Fields",
    "Point-E: Text-to-Point Cloud Diffusion",
    "Stable Diffusion: High-Resolution Image Synthesis",
    "GPT-4: Multimodal Foundation Models",
    "LLaMA: Open and Efficient Foundation Language Models",
    "DALL-E 2: Hierarchical Text-Conditional Image Generation",
    "Flamingo: Visual Language Model for Few-Shot Learning",
    "SAM: Segment Anything Model",
    "BEV-Former: Bird's Eye View Transformer for Autonomous Driving",
    "DiT: Scalable Diffusion Models with Transformers",
    "VideoPoet: Large Language Model for Zero-Shot Video Generation",
    "Make-A-Video: Text-to-Video Generation without Text-Video Data",
    "InstructPix2Pix: Learning to Follow Image Editing Instructions",
    "DreamBooth: Fine Tuning Text-to-Image Diffusion Models",
    "ControlNet: Adding Conditional Control to Diffusion Models",
    "VQ-Diffusion: Vector Quantized Diffusion Model for Text-to-Image",
    "Imagen Video: High Definition Video Generation",
    "Parti: Pathways Autoregressive Text-to-Image Model",
    "MaskGIT: Masked Generative Image Transformer",
    "MUSE: Text-To-Image Generation via Masked Generative Transformers",
    "UniDiffuser: One Transformer Fits All Distributions",
    "GLIGEN: Open-Set Grounded Text-to-Image Generation",
    "eDiffi: Text-to-Image Diffusion Models with Expert Denoisers",
    "StyleGAN3: Alias-Free Generative Adversarial Networks",
    "Pix2NeRF: Unsupervised Conditional π-GAN",
    "EG3D: Efficient Geometry-aware 3D Generative Adversarial Networks",
    "GET3D: Generative Model of High Quality 3D Textured Shapes",
    "Magic3D: High-Resolution Text-to-3D Content Creation",
    "ProlificDreamer: High-Fidelity and Diverse Text-to-3D Generation",
    "MVDream: Multi-view Diffusion for 3D Generation",
    "Zero-1-to-3: Zero-shot One Image to 3D Object",
    "Shap-E: Generating Conditional 3D Implicit Functions",
    "MeshFormer: End-to-End Mesh Generation from Videos",
    "VolSDF: Volume Rendering of Neural Implicit Surfaces",
    "NeuS: Learning Neural Implicit Surfaces by Volume Rendering",
    "MonoSDF: Exploring Monocular Geometric Cues for Neural Surface Reconstruction",
    "BakedSDF: Meshing Neural SDFs for Real-Time View Synthesis",
    "PermutoSDF: Fast Multi-View Reconstruction",
    "NeuralAngelo: High-Fidelity Neural Surface Reconstruction",
]


async def seed_sample_papers():
    """Seed sample papers and their initial metrics."""
    print("Seeding sample papers...")

    async with AsyncSessionLocal() as session:
        paper_service = PaperService(session)
        metric_service = MetricService(session)

        created_papers = 0

        # Create the 5 famous papers first
        for paper_data in SAMPLE_PAPERS:
            try:
                # Check if paper already exists
                existing = await paper_service.get_paper_by_arxiv_id(
                    paper_data["arxiv_id"]
                )

                if existing:
                    print(f"Paper '{paper_data['title'][:50]}' already exists")
                    continue

                # Create paper
                paper = await paper_service.create_paper(paper_data)
                created_papers += 1
                print(f"Created paper: {paper_data['title'][:60]}...")

                # Create initial metric snapshot
                snapshot_date = date.today()
                github_stars = randint(1000, 20000)  # Random stars for demo
                citation_count = randint(100, 5000)  # Random citations for demo

                await metric_service.create_metric_snapshot(
                    paper_id=paper.id,
                    snapshot_date=snapshot_date,
                    github_stars=github_stars,
                    citation_count=citation_count,
                )

                # Create historical snapshots (last 30 days)
                for i in range(1, 31):
                    past_date = date.today() - timedelta(days=i)
                    past_stars = max(100, int(github_stars * (0.8 + random() * 0.2)))
                    past_citations = max(10, int(citation_count * (0.85 + random() * 0.15)))

                    await metric_service.create_metric_snapshot(
                        paper_id=paper.id,
                        snapshot_date=past_date,
                        github_stars=past_stars,
                        citation_count=past_citations,
                    )

            except Exception as e:
                print(f"Error creating paper: {e}")
                continue

        # Create additional papers (without arXiv IDs, for testing)
        for idx, title in enumerate(ADDITIONAL_TITLES[:45]):  # Total ~50 papers
            try:
                # Generate synthetic data
                paper_data = {
                    "title": title,
                    "authors": [f"Author {idx+1}", f"Author {idx+2}", f"Author {idx+3}"],
                    "abstract": f"Abstract for {title}. This is a synthetic paper for testing purposes.",
                    "arxiv_id": f"23{idx:02d}.{(idx*123)%99999:05d}",
                    "published_date": date.today() - timedelta(days=randint(30, 365)),
                    "venue": "Test Conference 2024",
                }

                # Create paper
                paper = await paper_service.create_paper(paper_data)
                created_papers += 1

                # Create metrics
                snapshot_date = date.today()
                github_stars = randint(10, 5000)
                citation_count = randint(5, 500)

                await metric_service.create_metric_snapshot(
                    paper_id=paper.id,
                    snapshot_date=snapshot_date,
                    github_stars=github_stars,
                    citation_count=citation_count,
                )

                # Create 7 days of history (shorter for bulk papers)
                for i in range(1, 8):
                    past_date = date.today() - timedelta(days=i)
                    past_stars = max(5, int(github_stars * (0.9 + random() * 0.1)))
                    past_citations = max(1, int(citation_count * (0.95 + random() * 0.05)))

                    await metric_service.create_metric_snapshot(
                        paper_id=paper.id,
                        snapshot_date=past_date,
                        github_stars=past_stars,
                        citation_count=past_citations,
                    )

            except Exception as e:
                print(f"Error creating paper '{title}': {e}")
                continue

        await session.commit()
        print(f"\nSeeding complete: {created_papers} papers created with metrics")


if __name__ == "__main__":
    asyncio.run(seed_sample_papers())
