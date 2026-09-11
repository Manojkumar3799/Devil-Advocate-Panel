"""
Seed script for populating the benchmark_corpus table with sample SaaS, marketplace, and startup post-mortem data.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

from db.client import get_supabase_client
from db.rag import get_embedding

load_dotenv()

SAMPLE_BENCHMARKS = [
    {
        "content": "SaaS B2B Benchmark: Median CAC payback period for Seed to Series A SaaS companies is 14 months. Best-in-class is under 8 months. Greater than 24 months is considered capital inefficient.",
        "source": "OpenView SaaS Benchmarks 2024",
        "tag": "saas",
    },
    {
        "content": "SaaS Unit Economics: Enterprise SaaS gross margins typically range between 75% and 85%. Gross margins below 65% suggest heavy professional services or unscalable COGS.",
        "source": "Bessemer Cloud Index",
        "tag": "saas",
    },
    {
        "content": "Marketplace Metrics: Healthy two-sided marketplaces demonstrate take rates of 12% to 25%. Repeat transaction rate must exceed 40% within 90 days to offset high initial buyer/seller acquisition costs.",
        "source": "a16z Marketplace 100",
        "tag": "marketplace",
    },
    {
        "content": "Startup Failure Study: 42% of startups fail due to building products with no market need. 29% fail from running out of cash before achieving positive unit economics.",
        "source": "CB Insights Top 20 Startup Failure Reasons",
        "tag": "post_mortem",
    },
    {
        "content": "Sales Velocity: For ACVs under $10,000, sales cycles should average under 30 days. ACVs between $10k-$50k typically require 60-90 days.",
        "source": "HubSpot & Bridge Group Benchmarks",
        "tag": "saas",
    },
]


def main():
    client = get_supabase_client()
    if not client:
        print("⚠️ Supabase credentials not set in .env. Skipping remote DB seed.")
        print(f"Sample benchmarks count: {len(SAMPLE_BENCHMARKS)}")
        return

    print("Seeding benchmark corpus into Supabase...")
    for item in SAMPLE_BENCHMARKS:
        emb = get_embedding(item["content"])
        payload = {
            "content": item["content"],
            "source": item["source"],
            "tag": item["tag"],
        }
        if emb:
            payload["embedding"] = emb
        try:
            client.table("benchmark_corpus").insert(payload).execute()
            print(f"✓ Inserted: [{item['tag']}] {item['source']}")
        except Exception as e:
            print(f"Failed to insert item {item['source']}: {e}")

    print("Corpus seeding completed.")


if __name__ == "__main__":
    main()
