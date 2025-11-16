#!/usr/bin/env python3
"""
LLM-Focused Benchmark Generator for PyToon

Generates benchmark files specifically designed for LLM workflows where TOON excels:
- API response batching (uniform tabular data)
- Time-series metrics for context window maximization
- Multi-agent communication patterns
- RAG/retrieval document chunks

These patterns represent real-world LLM use cases where developers pass structured
data to language models.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Seed for reproducibility
SEED = 42
random.seed(SEED)

# Output directories
BASE_DIR = Path(__file__).parent
TIER1_DIR = BASE_DIR / "tier1_optimal"
TIER2_DIR = BASE_DIR / "tier2_good"
TIER3_DIR = BASE_DIR / "tier3_fair"
TIER4_DIR = BASE_DIR / "tier4_skip"

for d in [TIER1_DIR, TIER2_DIR, TIER3_DIR, TIER4_DIR]:
    d.mkdir(exist_ok=True)

# ============================================================================
# Common Data Generators
# ============================================================================

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
]

PRODUCT_CATEGORIES = ["Electronics", "Clothing", "Home", "Sports", "Books", "Toys", "Food", "Beauty"]
PRODUCT_ADJECTIVES = ["Premium", "Basic", "Pro", "Ultra", "Mini", "Max", "Smart", "Classic"]
PRODUCT_NOUNS = ["Widget", "Gadget", "Device", "Tool", "Kit", "Set", "Pack", "Bundle"]


def generate_uuid() -> str:
    """Generate deterministic UUID-like string."""
    hex_chars = "0123456789abcdef"
    parts = [
        "".join(random.choices(hex_chars, k=8)),
        "".join(random.choices(hex_chars, k=4)),
        "4" + "".join(random.choices(hex_chars, k=3)),
        random.choice("89ab") + "".join(random.choices(hex_chars, k=3)),
        "".join(random.choices(hex_chars, k=12)),
    ]
    return "-".join(parts)


def generate_iso_timestamp(days_back: int = 30) -> str:
    """Generate ISO format timestamp."""
    base = datetime(2025, 11, 17, 12, 0, 0)
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    dt = base - delta
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_email(first: str, last: str) -> str:
    """Generate realistic email."""
    domains = ["gmail.com", "outlook.com", "company.com", "email.org"]
    return f"{first.lower()}.{last.lower()}@{random.choice(domains)}"


def generate_price() -> float:
    """Generate realistic price."""
    return round(random.lognormvariate(3.5, 1.2), 2)


# ============================================================================
# TIER 1: LLM-OPTIMAL (40-60% savings expected)
# Large uniform tabular arrays - the sweet spot for TOON
# ============================================================================


def generate_product_catalog_entry(product_id: int) -> dict:
    """Generate uniform product entry for LLM catalog analysis."""
    adj = random.choice(PRODUCT_ADJECTIVES)
    noun = random.choice(PRODUCT_NOUNS)
    return {
        "id": product_id,
        "sku": f"SKU{product_id:06d}",
        "name": f"{adj} {noun}",
        "category": random.choice(PRODUCT_CATEGORIES),
        "price": generate_price(),
        "stock": random.randint(0, 1000),
        "rating": round(random.uniform(1.0, 5.0), 1),
        "reviews": random.randint(0, 500),
        "active": random.random() > 0.1,
    }


def generate_user_profile(user_id: int) -> dict:
    """Generate uniform user profile for LLM user analysis."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return {
        "user_id": f"u{user_id:06d}",
        "username": f"{first.lower()}{random.randint(100, 9999)}",
        "followers": random.randint(0, 50000),
        "following": random.randint(0, 5000),
        "posts": random.randint(0, 10000),
        "verified": random.random() > 0.9,
        "active": random.random() > 0.2,
        "created_days_ago": random.randint(1, 2000),
        "engagement_rate": round(random.uniform(0.01, 0.15), 4),
    }


def generate_event_log_entry(event_id: int, base_timestamp: datetime) -> dict:
    """Generate uniform event log entry for LLM pattern analysis."""
    # Sequential timestamps for realistic time-series
    ts = base_timestamp + timedelta(seconds=event_id * random.randint(1, 60))
    return {
        "event_id": event_id,
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "user_id": random.randint(1, 10000),
        "action": random.choice(["view", "click", "scroll", "hover", "submit"]),
        "page": f"/page/{random.randint(1, 100)}",
        "session_id": random.randint(100000, 999999),
        "duration_ms": random.randint(10, 30000),
    }


def generate_search_result(result_id: int) -> dict:
    """Generate uniform search result for LLM result ranking."""
    return {
        "rank": result_id,
        "doc_id": f"doc{result_id:08d}",
        "title": f"Result {result_id}: {random.choice(PRODUCT_ADJECTIVES)} {random.choice(PRODUCT_NOUNS)}",
        "score": round(random.uniform(0.1, 1.0), 4),
        "clicks": random.randint(0, 10000),
        "impressions": random.randint(100, 100000),
        "ctr": round(random.uniform(0.001, 0.15), 4),
        "freshness_days": random.randint(0, 365),
    }


def generate_timeseries_metric(idx: int, base_timestamp: datetime) -> dict:
    """Generate uniform time-series metric for LLM anomaly detection."""
    ts = base_timestamp + timedelta(minutes=idx * 5)
    return {
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cpu": round(random.uniform(10.0, 95.0), 2),
        "memory": round(random.uniform(30.0, 90.0), 2),
        "disk": round(random.uniform(40.0, 95.0), 2),
        "network_in": random.randint(1000, 100000),
        "network_out": random.randint(1000, 100000),
        "requests": random.randint(10, 10000),
        "errors": random.randint(0, 100),
    }


# ============================================================================
# TIER 2: LLM-GOOD (25-40% savings expected)
# Nested structures with uniform sub-arrays
# ============================================================================


def generate_invoice_with_items(invoice_id: int) -> dict:
    """Generate invoice with uniform line items for LLM processing."""
    num_items = random.randint(2, 8)
    items = []
    subtotal = 0.0

    for i in range(num_items):
        qty = random.randint(1, 10)
        unit_price = generate_price()
        line_total = round(qty * unit_price, 2)
        subtotal += line_total
        items.append({
            "line": i + 1,
            "product": f"{random.choice(PRODUCT_ADJECTIVES)} {random.choice(PRODUCT_NOUNS)}",
            "qty": qty,
            "unit_price": unit_price,
            "total": line_total,
        })

    tax = round(subtotal * 0.08, 2)
    return {
        "invoice_id": f"INV{invoice_id:08d}",
        "customer_id": random.randint(1000, 99999),
        "date": generate_iso_timestamp(days_back=90),
        "items": items,
        "subtotal": round(subtotal, 2),
        "tax": tax,
        "total": round(subtotal + tax, 2),
        "status": random.choice(["paid", "pending", "overdue"]),
    }


def generate_task_batch_item(task_id: int) -> dict:
    """Generate uniform task item for multi-agent communication."""
    return {
        "task_id": f"task_{task_id:06d}",
        "status": random.choice(["completed", "pending", "failed"]),
        "result": random.choice(["success", "error", "timeout", "retry"]),
        "duration_ms": random.randint(100, 30000),
        "retries": random.randint(0, 3),
        "worker_id": f"worker_{random.randint(1, 10)}",
        "priority": random.randint(1, 10),
        "created_at": generate_iso_timestamp(days_back=1),
    }


def generate_chat_message(msg_id: int, base_timestamp: datetime) -> dict:
    """Generate uniform chat message for LLM context."""
    ts = base_timestamp + timedelta(seconds=msg_id * random.randint(30, 300))
    return {
        "msg_id": msg_id,
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sender": random.choice(["user", "assistant", "system"]),
        "role": random.choice(["user", "assistant", "system"]),
        "content": f"Message content #{msg_id}: " + " ".join(
            random.choices(["hello", "help", "please", "thanks", "question", "answer"], k=random.randint(5, 20))
        ),
        "tokens": random.randint(10, 200),
    }


def generate_survey_response(response_id: int) -> dict:
    """Generate uniform survey response for LLM analysis."""
    return {
        "response_id": response_id,
        "respondent_id": random.randint(1000, 99999),
        "timestamp": generate_iso_timestamp(days_back=30),
        "q1_rating": random.randint(1, 5),
        "q2_rating": random.randint(1, 5),
        "q3_rating": random.randint(1, 5),
        "q4_rating": random.randint(1, 5),
        "q5_rating": random.randint(1, 5),
        "nps_score": random.randint(0, 10),
        "completed": random.random() > 0.1,
    }


def generate_document_with_metadata(doc_id: int) -> dict:
    """Generate document with metadata for LLM document processing."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return {
        "doc_id": f"doc_{doc_id:08d}",
        "title": f"Document {doc_id}: {random.choice(['Analysis', 'Report', 'Summary', 'Review'])}",
        "author": f"{first} {last}",
        "created": generate_iso_timestamp(days_back=365),
        "modified": generate_iso_timestamp(days_back=30),
        "version": f"{random.randint(1, 10)}.{random.randint(0, 9)}",
        "status": random.choice(["draft", "review", "published"]),
        "word_count": random.randint(500, 10000),
        "page_count": random.randint(1, 50),
    }


# ============================================================================
# TIER 3: LLM-FAIR (10-25% savings expected)
# RAG documents, mixed content (metadata + large text)
# ============================================================================


def generate_rag_document_chunk(chunk_id: int) -> dict:
    """Generate RAG document chunk - metadata uniform but text varies."""
    # Large text content reduces relative savings (text dominates)
    text_length = random.randint(200, 1000)
    text = " ".join(
        random.choices(
            ["the", "a", "is", "in", "to", "and", "of", "for", "with", "on", "as", "by", "this", "that", "from"],
            k=text_length
        )
    )
    return {
        "chunk_id": f"chunk_{chunk_id:08d}",
        "doc_id": f"doc_{random.randint(1, 1000):06d}",
        "chunk_num": random.randint(1, 50),
        "text": text,
        "relevance_score": round(random.uniform(0.5, 1.0), 4),
        "embedding_id": generate_uuid()[:16],
    }


def generate_mixed_content_item(item_id: int) -> dict:
    """Generate mixed content - some uniform fields, some variable."""
    # Medium-sized text reduces but doesn't eliminate savings
    description_length = random.randint(50, 200)
    description = " ".join(
        random.choices(["word", "text", "content", "data", "info", "detail"], k=description_length)
    )
    return {
        "item_id": item_id,
        "title": f"Item {item_id}",
        "category": random.choice(PRODUCT_CATEGORIES),
        "description": description,
        "score": round(random.uniform(0, 100), 2),
        "active": random.random() > 0.2,
        "updated": generate_iso_timestamp(days_back=30),
    }


def generate_sparse_data_item(item_id: int) -> dict:
    """Generate sparse data with many null fields."""
    item = {
        "id": item_id,
        "type": random.choice(["A", "B", "C", "D"]),
        "timestamp": generate_iso_timestamp(days_back=30),
    }

    # 30%+ fields are null
    if random.random() > 0.4:
        item["field1"] = random.randint(1, 100)
    else:
        item["field1"] = None

    if random.random() > 0.5:
        item["field2"] = f"value_{random.randint(1, 100)}"
    else:
        item["field2"] = None

    if random.random() > 0.6:
        item["field3"] = round(random.uniform(0, 1), 4)
    else:
        item["field3"] = None

    if random.random() > 0.7:
        item["field4"] = random.choice([True, False])
    else:
        item["field4"] = None

    if random.random() > 0.8:
        item["field5"] = generate_uuid()[:8]
    else:
        item["field5"] = None

    return item


# ============================================================================
# TIER 4: LLM-SKIP (-5% to +5%)
# Configs, deeply nested hierarchies - use JSON instead
# ============================================================================


def generate_config_preferences() -> dict:
    """Generate user preferences - deeply nested, heterogeneous."""
    return {
        "user_id": generate_uuid(),
        "theme": random.choice(["light", "dark", "auto"]),
        "language": random.choice(["en", "es", "fr", "de", "ja"]),
        "notifications": {
            "email": random.random() > 0.3,
            "push": random.random() > 0.5,
            "sms": random.random() > 0.8,
            "frequency": random.choice(["immediate", "daily", "weekly"]),
        },
        "privacy": {
            "profile_visible": random.random() > 0.4,
            "show_activity": random.random() > 0.6,
            "allow_indexing": random.random() > 0.7,
        },
        "display": {
            "items_per_page": random.choice([10, 25, 50, 100]),
            "compact_mode": random.random() > 0.5,
            "show_previews": random.random() > 0.3,
        },
    }


def generate_nested_hierarchy(depth: int = 0, max_depth: int = 6) -> dict:
    """Generate deeply nested organizational hierarchy."""
    node = {
        "id": generate_uuid()[:12],
        "name": f"Node_{random.randint(1, 1000)}",
        "level": depth,
        "value": random.randint(1, 100),
    }

    if depth < max_depth and random.random() > 0.3:
        num_children = random.randint(1, 3)
        node["children"] = [
            generate_nested_hierarchy(depth + 1, max_depth)
            for _ in range(num_children)
        ]
    else:
        node["children"] = []

    return node


def generate_polymorphic_item(item_id: int) -> dict:
    """Generate highly variable structure - different fields each time."""
    structures = [
        lambda: {"type": "A", "value_a": random.randint(1, 100)},
        lambda: {"type": "B", "value_b": f"string_{random.randint(1, 100)}", "extra": True},
        lambda: {"type": "C", "nested": {"x": 1, "y": 2}},
        lambda: {"type": "D", "list": [1, 2, 3], "count": 3},
        lambda: {"type": "E", "data": None, "status": "empty"},
    ]
    base = random.choice(structures)()
    base["id"] = item_id
    return base


# ============================================================================
# File Generation Functions
# ============================================================================


def save_json(data: list | dict, filepath: Path, description: str) -> None:
    """Save data to JSON file with metadata."""
    with open(filepath, "w") as f:
        json.dump(data, f, separators=(",", ":"))  # Compact JSON for fair comparison
    size = filepath.stat().st_size
    record_count = len(data) if isinstance(data, list) else 1
    print(f"  {filepath.name:<45} {record_count:>6} records | {size:>10,} bytes | {description}")


def generate_tier1_files() -> None:
    """Generate Tier 1: LLM-Optimal files (40-60% savings expected)."""
    print("\n=== TIER 1: LLM-OPTIMAL (Expected 40-60% Token Savings) ===")
    print("Large uniform tabular arrays - TOON's sweet spot\n")

    # Product catalog - 1000 items
    save_json(
        [generate_product_catalog_entry(i) for i in range(1, 1001)],
        TIER1_DIR / "llm_product_catalog_1k.json",
        "1K products for LLM catalog analysis"
    )

    # Product catalog - 5000 items (stress test)
    save_json(
        [generate_product_catalog_entry(i) for i in range(1, 5001)],
        TIER1_DIR / "llm_product_catalog_5k.json",
        "5K products for large-scale analysis"
    )

    # User profiles batch - 500 users
    save_json(
        [generate_user_profile(i) for i in range(1, 501)],
        TIER1_DIR / "llm_user_profiles_500.json",
        "500 user profiles for batch analysis"
    )

    # User profiles batch - 2000 users
    save_json(
        [generate_user_profile(i) for i in range(1, 2001)],
        TIER1_DIR / "llm_user_profiles_2k.json",
        "2K user profiles for large-scale analysis"
    )

    # Event stream - 10000 events
    base_ts = datetime(2025, 11, 17, 0, 0, 0)
    save_json(
        [generate_event_log_entry(i, base_ts) for i in range(1, 10001)],
        TIER1_DIR / "llm_event_stream_10k.json",
        "10K events for pattern recognition"
    )

    # Search results - 500 results
    save_json(
        [generate_search_result(i) for i in range(1, 501)],
        TIER1_DIR / "llm_search_results_500.json",
        "500 search results for ranking"
    )

    # Time-series metrics - 2000 data points (7 days @ 5min intervals)
    base_ts = datetime(2025, 11, 10, 0, 0, 0)
    save_json(
        [generate_timeseries_metric(i, base_ts) for i in range(2000)],
        TIER1_DIR / "llm_timeseries_metrics_2k.json",
        "2K metrics for anomaly detection"
    )


def generate_tier2_files() -> None:
    """Generate Tier 2: LLM-Good files (25-40% savings expected)."""
    print("\n=== TIER 2: LLM-GOOD (Expected 25-40% Token Savings) ===")
    print("Nested structures with uniform sub-arrays\n")

    # Invoices with line items - 200 invoices
    save_json(
        [generate_invoice_with_items(i) for i in range(1, 201)],
        TIER2_DIR / "llm_invoices_200.json",
        "200 invoices with line items"
    )

    # Task batches - 500 tasks
    save_json(
        [generate_task_batch_item(i) for i in range(1, 501)],
        TIER2_DIR / "llm_task_batch_500.json",
        "500 tasks for multi-agent comm"
    )

    # Chat history - 300 messages
    base_ts = datetime(2025, 11, 17, 10, 0, 0)
    save_json(
        [generate_chat_message(i, base_ts) for i in range(1, 301)],
        TIER2_DIR / "llm_chat_history_300.json",
        "300 chat messages for context"
    )

    # Survey responses - 1000 responses
    save_json(
        [generate_survey_response(i) for i in range(1, 1001)],
        TIER2_DIR / "llm_survey_responses_1k.json",
        "1K survey responses for analysis"
    )

    # Documents with metadata - 500 documents
    save_json(
        [generate_document_with_metadata(i) for i in range(1, 501)],
        TIER2_DIR / "llm_documents_metadata_500.json",
        "500 documents with metadata"
    )


def generate_tier3_files() -> None:
    """Generate Tier 3: LLM-Fair files (10-25% savings expected)."""
    print("\n=== TIER 3: LLM-FAIR (Expected 10-25% Token Savings) ===")
    print("RAG documents, mixed content (text dominates)\n")

    # RAG document chunks - 100 chunks
    save_json(
        [generate_rag_document_chunk(i) for i in range(1, 101)],
        TIER3_DIR / "llm_rag_chunks_100.json",
        "100 RAG chunks with text"
    )

    # Mixed content - 300 items
    save_json(
        [generate_mixed_content_item(i) for i in range(1, 301)],
        TIER3_DIR / "llm_mixed_content_300.json",
        "300 mixed content items"
    )

    # Sparse data - 500 items
    save_json(
        [generate_sparse_data_item(i) for i in range(1, 501)],
        TIER3_DIR / "llm_sparse_data_500.json",
        "500 sparse data items"
    )


def generate_tier4_files() -> None:
    """Generate Tier 4: LLM-Skip files (recommend JSON instead)."""
    print("\n=== TIER 4: LLM-SKIP (Expected -5% to +5% - Use JSON) ===")
    print("Configs, deeply nested hierarchies - TOON overhead not worth it\n")

    # Config preferences - 100 users
    save_json(
        [generate_config_preferences() for _ in range(100)],
        TIER4_DIR / "config_user_preferences_100.json",
        "100 user configs (heterogeneous)"
    )

    # Nested hierarchies - 50 trees
    save_json(
        [generate_nested_hierarchy(0, 6) for _ in range(50)],
        TIER4_DIR / "nested_org_hierarchy_50.json",
        "50 deeply nested trees"
    )

    # Polymorphic data - 200 items
    save_json(
        [generate_polymorphic_item(i) for i in range(1, 201)],
        TIER4_DIR / "polymorphic_mixed_200.json",
        "200 highly variable structures"
    )


def main() -> None:
    """Generate all LLM-focused benchmark files."""
    print("=" * 70)
    print("PyToon LLM-Focused Benchmark Generator")
    print("=" * 70)
    print("\nGenerating benchmark files optimized for LLM workflow patterns...")
    print(f"Base directory: {BASE_DIR}")

    # Reset seed for consistency
    random.seed(SEED)

    generate_tier1_files()
    generate_tier2_files()
    generate_tier3_files()
    generate_tier4_files()

    # Count total files
    total_files = (
        len(list(TIER1_DIR.glob("*.json")))
        + len(list(TIER2_DIR.glob("*.json")))
        + len(list(TIER3_DIR.glob("*.json")))
        + len(list(TIER4_DIR.glob("*.json")))
    )

    print("\n" + "=" * 70)
    print(f"Generated {total_files} LLM-focused benchmark files")
    print(f"\nTier 1 (Optimal):  {TIER1_DIR}")
    print(f"Tier 2 (Good):     {TIER2_DIR}")
    print(f"Tier 3 (Fair):     {TIER3_DIR}")
    print(f"Tier 4 (Skip):     {TIER4_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
