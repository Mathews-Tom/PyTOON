#!/usr/bin/env python3
"""
Benchmark Sample Generator for PyToon

Generates deterministic, realistic JSON benchmark files for testing TOON performance.
Uses seeded random generation for reproducibility.
"""

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

# Seed for reproducibility
SEED = 42
random.seed(SEED)

# Output directory
OUTPUT_DIR = Path(__file__).parent / "samples"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# Data Generators (Realistic Patterns)
# ============================================================================

FIRST_NAMES = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "David",
    "Barbara",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
    "Thomas",
    "Sarah",
    "Charles",
    "Karen",
    "Christopher",
    "Nancy",
    "Daniel",
    "Lisa",
    "Matthew",
    "Betty",
    "Anthony",
    "Margaret",
    "Mark",
    "Sandra",
    "Donald",
    "Ashley",
    "Steven",
    "Kimberly",
    "Paul",
    "Emily",
    "Andrew",
    "Donna",
    "Joshua",
    "Michelle",
    "Kenneth",
    "Dorothy",
    "Kevin",
    "Carol",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Torres",
    "Nguyen",
    "Hill",
    "Flores",
    "Green",
    "Adams",
    "Nelson",
    "Baker",
]

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "company.com", "email.org"]

PRODUCT_CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home",
    "Sports",
    "Books",
    "Toys",
    "Food",
    "Beauty",
]

PRODUCT_ADJECTIVES = ["Premium", "Basic", "Pro", "Ultra", "Mini", "Max", "Smart", "Classic"]

PRODUCT_NOUNS = ["Widget", "Gadget", "Device", "Tool", "Kit", "Set", "Pack", "Bundle"]

EVENT_TYPES = ["click", "view", "purchase", "signup", "login", "logout", "search", "share"]

NOTIFICATION_TYPES = ["email", "push", "sms", "in_app", "webhook"]


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


def generate_email(first: str, last: str) -> str:
    """Generate realistic email from name."""
    domain = random.choice(EMAIL_DOMAINS)
    patterns = [
        f"{first.lower()}.{last.lower()}@{domain}",
        f"{first.lower()}{last.lower()}@{domain}",
        f"{first[0].lower()}{last.lower()}@{domain}",
        f"{first.lower()}_{last.lower()}@{domain}",
    ]
    return random.choice(patterns)


def generate_datetime(days_back: int = 730) -> str:
    """Generate ISO format datetime within last N days."""
    base = datetime(2025, 11, 16, 12, 0, 0)
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    dt = base - delta
    return dt.isoformat() + "Z"


def generate_date(days_back: int = 730) -> str:
    """Generate ISO format date. Negative values = future dates."""
    base = date(2025, 11, 16)
    if days_back < 0:
        # Future date
        delta = timedelta(days=random.randint(1, abs(days_back)))
        d = base + delta
    else:
        delta = timedelta(days=random.randint(0, days_back))
        d = base - delta
    return d.isoformat()


def generate_price() -> float:
    """Generate realistic price (log-normal distribution)."""
    # Log-normal gives realistic price distribution
    price = random.lognormvariate(3.5, 1.2)
    return round(price, 2)


def generate_ip() -> str:
    """Generate random IP address."""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"


# ============================================================================
# Tier A: TOON Optimal (40-60%+ savings expected)
# ============================================================================


def generate_uniform_user(user_id: int) -> dict:
    """Generate a uniform user object (A1)."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return {
        "id": user_id,
        "uuid": generate_uuid(),
        "firstName": first,
        "lastName": last,
        "email": generate_email(first, last),
        "age": random.randint(18, 80),
        "active": random.random() > 0.2,  # 80% active
        "createdAt": generate_datetime(),
        "loginCount": random.randint(0, 500),
        "score": round(random.uniform(0, 100), 2),
    }


def generate_uniform_product(product_id: int) -> dict:
    """Generate a uniform product object (A1)."""
    adj = random.choice(PRODUCT_ADJECTIVES)
    noun = random.choice(PRODUCT_NOUNS)
    return {
        "id": product_id,
        "sku": f"SKU-{product_id:06d}",
        "name": f"{adj} {noun}",
        "category": random.choice(PRODUCT_CATEGORIES),
        "price": generate_price(),
        "inStock": random.random() > 0.1,  # 90% in stock
        "quantity": random.randint(0, 1000),
        "rating": round(random.uniform(1, 5), 1),
        "reviewCount": random.randint(0, 500),
        "featured": random.random() > 0.9,  # 10% featured
    }


def generate_sparse_profile(user_id: int) -> dict:
    """Generate a sparse user profile with ~40% nulls (A2)."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)

    # Core fields (always present)
    profile = {
        "id": user_id,
        "username": f"{first.lower()}{random.randint(100, 9999)}",
        "email": generate_email(first, last),
        "createdAt": generate_datetime(),
    }

    # Optional fields (30-50% null rate each)
    if random.random() > 0.4:
        profile["firstName"] = first
    else:
        profile["firstName"] = None

    if random.random() > 0.4:
        profile["lastName"] = last
    else:
        profile["lastName"] = None

    if random.random() > 0.6:  # 60% null - bio often empty
        profile["bio"] = None
    else:
        profile["bio"] = (
            f"I'm {first} and I love {random.choice(['coding', 'reading', 'travel', 'music', 'sports'])}."
        )

    if random.random() > 0.5:
        profile["phone"] = None
    else:
        profile["phone"] = (
            f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        )

    if random.random() > 0.7:  # 70% null - avatar often missing
        profile["avatarUrl"] = None
    else:
        profile["avatarUrl"] = f"https://cdn.example.com/avatars/{generate_uuid()}.jpg"

    if random.random() > 0.3:
        profile["lastLoginAt"] = generate_datetime(days_back=30)
    else:
        profile["lastLoginAt"] = None

    if random.random() > 0.5:
        profile["location"] = None
    else:
        profile["location"] = random.choice(
            ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
        )

    if random.random() > 0.8:  # 80% null - website rare
        profile["website"] = None
    else:
        profile["website"] = f"https://{first.lower()}{last.lower()}.com"

    if random.random() > 0.4:
        profile["verified"] = random.random() > 0.7
    else:
        profile["verified"] = None

    if random.random() > 0.6:
        profile["followerCount"] = None
    else:
        profile["followerCount"] = random.randint(0, 10000)

    return profile


def generate_sparse_inventory(item_id: int) -> dict:
    """Generate sparse inventory item (A2)."""
    item = {
        "itemId": item_id,
        "sku": f"INV-{item_id:08d}",
        "name": f"{random.choice(PRODUCT_ADJECTIVES)} {random.choice(PRODUCT_NOUNS)}",
        "quantity": random.randint(0, 500),
    }

    # Optional metadata (many nulls)
    if random.random() > 0.3:
        item["location"] = random.choice(["Warehouse A", "Warehouse B", "Store Front", "Transit"])
    else:
        item["location"] = None

    if random.random() > 0.5:
        item["lastRestocked"] = None
    else:
        item["lastRestocked"] = generate_date(days_back=90)

    if random.random() > 0.4:
        item["supplier"] = None
    else:
        item["supplier"] = random.choice(["SupplierCo", "Global Goods", "FastShip", "QualityFirst"])

    if random.random() > 0.6:
        item["unitCost"] = None
    else:
        item["unitCost"] = round(random.uniform(1, 100), 2)

    if random.random() > 0.7:
        item["expirationDate"] = None
    else:
        item["expirationDate"] = generate_date(days_back=-365)  # Future date

    if random.random() > 0.5:
        item["batchNumber"] = None
    else:
        item["batchNumber"] = f"BATCH-{random.randint(10000, 99999)}"

    if random.random() > 0.8:
        item["notes"] = None
    else:
        item["notes"] = random.choice(
            ["Handle with care", "Fragile", "Keep refrigerated", "Oversized"]
        )

    return item


def generate_polymorphic_event(event_id: int) -> dict:
    """Generate polymorphic event (A3) - different fields per type."""
    event_type = random.choices(
        EVENT_TYPES,
        weights=[30, 25, 10, 5, 15, 10, 3, 2],  # Zipf-like distribution
        k=1,
    )[0]

    base = {
        "id": event_id,
        "type": event_type,
        "timestamp": generate_datetime(days_back=30),
        "userId": random.randint(1, 10000),
        "sessionId": generate_uuid(),
    }

    # Type-specific fields
    if event_type == "click":
        base["elementId"] = f"btn-{random.randint(1, 100)}"
        base["pageUrl"] = f"/page/{random.randint(1, 50)}"
        base["x"] = random.randint(0, 1920)
        base["y"] = random.randint(0, 1080)
    elif event_type == "view":
        base["pageUrl"] = f"/page/{random.randint(1, 50)}"
        base["duration"] = random.randint(1, 300)
        base["scrollDepth"] = random.randint(0, 100)
    elif event_type == "purchase":
        base["orderId"] = generate_uuid()
        base["amount"] = generate_price()
        base["currency"] = "USD"
        base["itemCount"] = random.randint(1, 10)
    elif event_type == "signup":
        base["method"] = random.choice(["email", "google", "facebook", "apple"])
        base["referrer"] = random.choice(["organic", "paid", "social", "direct"])
    elif event_type == "login":
        base["method"] = random.choice(["password", "sso", "2fa"])
        base["success"] = random.random() > 0.1
        base["ipAddress"] = generate_ip()
    elif event_type == "logout":
        base["sessionDuration"] = random.randint(60, 7200)
    elif event_type == "search":
        base["query"] = random.choice(["laptop", "phone", "shoes", "book", "camera"])
        base["resultsCount"] = random.randint(0, 500)
        base["filters"] = random.randint(0, 5)
    elif event_type == "share":
        base["platform"] = random.choice(["twitter", "facebook", "linkedin", "email"])
        base["contentId"] = generate_uuid()

    return base


def generate_polymorphic_notification(notif_id: int) -> dict:
    """Generate polymorphic notification (A3)."""
    notif_type = random.choice(NOTIFICATION_TYPES)

    base = {
        "id": notif_id,
        "type": notif_type,
        "createdAt": generate_datetime(days_back=7),
        "userId": random.randint(1, 10000),
        "read": random.random() > 0.4,
    }

    if notif_type == "email":
        base["subject"] = f"Notification #{notif_id}"
        base["body"] = "Your action is required."
        base["from"] = "noreply@example.com"
        base["to"] = f"user{base['userId']}@example.com"
    elif notif_type == "push":
        base["title"] = "New Update"
        base["body"] = "Check out what's new!"
        base["icon"] = "notification_icon"
        base["badge"] = random.randint(1, 10)
    elif notif_type == "sms":
        base["phoneNumber"] = f"+1{random.randint(2000000000, 9999999999)}"
        base["message"] = "Your code is 123456"
        base["carrier"] = random.choice(["AT&T", "Verizon", "T-Mobile"])
    elif notif_type == "in_app":
        base["title"] = "New Feature"
        base["message"] = "Try our new feature!"
        base["actionUrl"] = "/features/new"
        base["dismissable"] = True
    elif notif_type == "webhook":
        base["url"] = f"https://webhook.site/{generate_uuid()}"
        base["payload"] = {"event": "notification", "id": notif_id}
        base["retryCount"] = random.randint(0, 3)

    return base


# ============================================================================
# Tier B: TOON Strong (25-40% savings expected)
# ============================================================================


def generate_audit_log_entry(entry_id: int) -> dict:
    """Generate audit log with rich types (B1)."""
    return {
        "id": generate_uuid(),
        "entryNumber": entry_id,
        "timestamp": generate_datetime(days_back=90),
        "userId": generate_uuid(),
        "action": random.choice(["CREATE", "UPDATE", "DELETE", "READ", "LOGIN", "LOGOUT"]),
        "resource": random.choice(["user", "product", "order", "payment", "config"]),
        "resourceId": generate_uuid(),
        "ipAddress": generate_ip(),
        "userAgent": f"Mozilla/5.0 ({random.choice(['Windows', 'Mac', 'Linux'])})",
        "duration": random.randint(10, 5000),
        "success": random.random() > 0.05,
        "metadata": {
            "requestId": generate_uuid(),
            "traceId": generate_uuid(),
        },
    }


def generate_financial_transaction(tx_id: int) -> dict:
    """Generate financial transaction with Decimals (B1)."""
    amount = round(random.uniform(1, 10000), 2)
    fee = round(amount * 0.029, 2)  # 2.9% fee
    return {
        "transactionId": generate_uuid(),
        "sequenceNumber": tx_id,
        "timestamp": generate_datetime(days_back=365),
        "amount": amount,
        "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
        "fee": fee,
        "netAmount": round(amount - fee, 2),
        "type": random.choice(["credit", "debit", "transfer", "refund"]),
        "status": random.choice(["completed", "pending", "failed"]),
        "fromAccount": f"ACC-{random.randint(10000000, 99999999)}",
        "toAccount": f"ACC-{random.randint(10000000, 99999999)}",
        "reference": f"REF-{generate_uuid()[:8].upper()}",
        "processedAt": generate_datetime(days_back=365),
    }


def generate_order_with_refs(order_id: int, products: list) -> dict:
    """Generate order with product references (B2)."""
    num_items = random.randint(1, 5)
    items = []
    total = 0.0

    for _ in range(num_items):
        product = random.choice(products)
        qty = random.randint(1, 3)
        subtotal = round(product["price"] * qty, 2)
        total += subtotal
        items.append(
            {
                "productId": product["id"],  # Reference, not embedded
                "quantity": qty,
                "unitPrice": product["price"],
                "subtotal": subtotal,
            }
        )

    return {
        "orderId": order_id,
        "orderNumber": f"ORD-{order_id:08d}",
        "customerId": random.randint(1, 10000),
        "items": items,
        "subtotal": round(total, 2),
        "tax": round(total * 0.08, 2),
        "total": round(total * 1.08, 2),
        "status": random.choice(["pending", "processing", "shipped", "delivered"]),
        "createdAt": generate_datetime(days_back=90),
    }


def generate_org_chart_employee(emp_id: int, max_id: int) -> dict:
    """Generate employee with manager reference (B2)."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)

    # Top-level managers have no manager
    manager_id = None if emp_id <= 5 else random.randint(1, min(emp_id - 1, max_id // 2))

    return {
        "employeeId": emp_id,
        "firstName": first,
        "lastName": last,
        "email": generate_email(first, last),
        "title": random.choice(["Engineer", "Manager", "Director", "VP", "Analyst"]),
        "department": random.choice(["Engineering", "Sales", "Marketing", "HR", "Finance"]),
        "managerId": manager_id,  # Reference to another employee
        "hireDate": generate_date(days_back=1825),  # Up to 5 years
        "salary": random.randint(50000, 200000),
    }


def generate_nested_category(
    cat_id: int, parent_id: int | None, depth: int, max_depth: int
) -> dict:
    """Generate nested category tree (B3)."""
    cat = {
        "id": cat_id,
        "name": f"Category {cat_id}",
        "slug": f"category-{cat_id}",
        "parentId": parent_id,
        "level": depth,
        "active": random.random() > 0.1,
        "itemCount": random.randint(0, 100),
    }

    # Recursively add children if not at max depth
    if depth < max_depth and random.random() > 0.3:
        num_children = random.randint(1, 4)
        cat["children"] = []
        for i in range(num_children):
            child_id = cat_id * 10 + i + 1
            child = generate_nested_category(child_id, cat_id, depth + 1, max_depth)
            cat["children"].append(child)
    else:
        cat["children"] = []

    return cat


def generate_menu_item(item_id: int, parent_id: int | None, depth: int, max_depth: int) -> dict:
    """Generate menu hierarchy item (B3)."""
    item = {
        "id": item_id,
        "label": f"Menu Item {item_id}",
        "url": f"/menu/{item_id}",
        "icon": random.choice(["home", "settings", "user", "chart", "folder"]),
        "parentId": parent_id,
        "order": random.randint(1, 10),
        "visible": random.random() > 0.1,
    }

    if depth < max_depth and random.random() > 0.4:
        num_children = random.randint(1, 5)
        item["children"] = []
        for i in range(num_children):
            child_id = item_id * 10 + i + 1
            child = generate_menu_item(child_id, item_id, depth + 1, max_depth)
            item["children"].append(child)
    else:
        item["children"] = []

    return item


# ============================================================================
# Tier C: TOON Moderate (10-25% savings expected)
# ============================================================================


def generate_blog_post(post_id: int) -> dict:
    """Generate semi-structured blog post (C1)."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)

    # Some structure variation
    post = {
        "id": post_id,
        "title": f"Blog Post Title #{post_id}",
        "slug": f"blog-post-{post_id}",
        "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        * random.randint(5, 20),
        "authorId": random.randint(1, 100),
        "authorName": f"{first} {last}",
        "publishedAt": generate_datetime(days_back=365),
        "updatedAt": generate_datetime(days_back=30),
        "status": random.choice(["draft", "published", "archived"]),
        "viewCount": random.randint(0, 10000),
        "likeCount": random.randint(0, 500),
    }

    # Variable structure elements
    if random.random() > 0.3:
        post["tags"] = random.sample(
            ["tech", "news", "tutorial", "opinion", "review"], k=random.randint(1, 3)
        )

    if random.random() > 0.5:
        post["featuredImage"] = f"https://cdn.example.com/posts/{post_id}.jpg"

    if random.random() > 0.6:
        post["excerpt"] = post["content"][:100] + "..."

    if random.random() > 0.7:
        post["metadata"] = {
            "readTime": random.randint(2, 15),
            "wordCount": random.randint(200, 2000),
        }

    return post


def generate_api_response(resp_id: int) -> dict:
    """Generate varied API response (C1)."""
    response_types = ["user", "product", "order", "error", "list", "stats"]
    resp_type = random.choice(response_types)

    base = {
        "requestId": generate_uuid(),
        "timestamp": generate_datetime(days_back=1),
        "status": random.choice([200, 201, 400, 404, 500]) if resp_type == "error" else 200,
    }

    if resp_type == "user":
        base["data"] = generate_uniform_user(resp_id)
    elif resp_type == "product":
        base["data"] = generate_uniform_product(resp_id)
    elif resp_type == "order":
        base["data"] = {
            "orderId": resp_id,
            "total": generate_price(),
            "status": "completed",
        }
    elif resp_type == "error":
        base["error"] = {
            "code": random.choice(["INVALID_INPUT", "NOT_FOUND", "SERVER_ERROR"]),
            "message": "An error occurred",
        }
    elif resp_type == "list":
        base["data"] = [{"id": i, "name": f"Item {i}"} for i in range(random.randint(1, 10))]
        base["pagination"] = {
            "page": 1,
            "perPage": 10,
            "total": random.randint(10, 1000),
        }
    elif resp_type == "stats":
        base["data"] = {
            "totalUsers": random.randint(1000, 100000),
            "activeToday": random.randint(100, 10000),
            "revenue": round(random.uniform(1000, 100000), 2),
        }

    return base


def generate_search_result(result_id: int) -> dict:
    """Generate search result with varied metadata (C2)."""
    result = {
        "id": result_id,
        "title": f"Search Result {result_id}",
        "url": f"/result/{result_id}",
        "score": round(random.uniform(0.1, 1.0), 4),
        "snippet": "This is a search result snippet..." * random.randint(1, 3),
    }

    # Partially uniform - some fields always present, some vary
    if random.random() > 0.3:
        result["category"] = random.choice(PRODUCT_CATEGORIES)

    if random.random() > 0.4:
        result["price"] = generate_price()

    if random.random() > 0.5:
        result["rating"] = round(random.uniform(1, 5), 1)

    if random.random() > 0.6:
        result["inStock"] = random.random() > 0.2

    if random.random() > 0.7:
        result["highlights"] = [f"highlight {i}" for i in range(random.randint(1, 3))]

    return result


def generate_threaded_comment(comment_id: int, parent_id: int | None, depth: int) -> dict:
    """Generate threaded comment (C2)."""
    first = random.choice(FIRST_NAMES)

    comment = {
        "id": comment_id,
        "authorId": random.randint(1, 1000),
        "authorName": first,
        "content": "This is a comment. " * random.randint(1, 10),
        "createdAt": generate_datetime(days_back=30),
        "likes": random.randint(0, 100),
        "parentId": parent_id,
        "depth": depth,
    }

    # Variable nesting depth
    if depth < 5 and random.random() > 0.6:
        num_replies = random.randint(0, 3)
        if num_replies > 0:
            comment["replies"] = [
                generate_threaded_comment(comment_id * 10 + i, comment_id, depth + 1)
                for i in range(num_replies)
            ]

    return comment


def generate_feature_flag(flag_id: int) -> dict:
    """Generate feature flag config (C3)."""
    flag_types = ["boolean", "percentage", "user_list", "variant"]
    flag_type = random.choice(flag_types)

    flag = {
        "id": flag_id,
        "name": f"feature_{flag_id}",
        "description": f"Feature flag #{flag_id} for testing",
        "enabled": random.random() > 0.3,
        "type": flag_type,
        "createdAt": generate_date(days_back=180),
    }

    if flag_type == "boolean":
        flag["value"] = random.random() > 0.5
    elif flag_type == "percentage":
        flag["value"] = random.randint(0, 100)
    elif flag_type == "user_list":
        flag["value"] = [random.randint(1, 10000) for _ in range(random.randint(1, 10))]
    elif flag_type == "variant":
        flag["value"] = {
            "control": random.randint(10, 50),
            "treatment_a": random.randint(10, 50),
            "treatment_b": random.randint(10, 50),
        }

    return flag


# ============================================================================
# Tier D: Minimal/Negative (0-15% or worse expected)
# ============================================================================


def generate_irregular_schema_type(type_id: int) -> dict:
    """Generate irregular schema definition (D1)."""
    type_name = f"Type{type_id}"

    # Highly irregular structure
    schema = {
        "name": type_name,
        "kind": random.choice(["object", "enum", "union", "interface"]),
    }

    if schema["kind"] == "object":
        num_fields = random.randint(1, 10)
        schema["fields"] = {}
        for i in range(num_fields):
            field_name = f"field{i}"
            schema["fields"][field_name] = {
                "type": random.choice(
                    ["string", "int", "float", "boolean", f"Type{random.randint(1, type_id)}"]
                ),
                "nullable": random.random() > 0.5,
            }
            if random.random() > 0.7:
                schema["fields"][field_name]["default"] = "default_value"
            if random.random() > 0.8:
                schema["fields"][field_name]["description"] = f"Description for {field_name}"
    elif schema["kind"] == "enum":
        schema["values"] = [f"VALUE_{i}" for i in range(random.randint(2, 8))]
    elif schema["kind"] == "union":
        schema["types"] = [f"Type{random.randint(1, type_id)}" for _ in range(random.randint(2, 5))]
    elif schema["kind"] == "interface":
        schema["implements"] = [
            f"Interface{random.randint(1, 10)}" for _ in range(random.randint(0, 3))
        ]
        schema["methods"] = {
            f"method{i}": {
                "args": [
                    {"name": f"arg{j}", "type": "string"} for j in range(random.randint(0, 3))
                ],
                "returnType": random.choice(["void", "string", "int"]),
            }
            for i in range(random.randint(1, 5))
        }

    return schema


def generate_irregular_config(depth: int = 0, max_depth: int = 8) -> dict:
    """Generate deeply nested irregular config (D1)."""
    config = {}
    num_keys = random.randint(2, 6)

    for i in range(num_keys):
        key = random.choice(
            [
                f"setting{i}",
                f"config_{i}",
                f"option{i}",
                f"param_{i}",
                f"value{i}",
            ]
        )

        # Random value types, irregular structure
        if depth < max_depth and random.random() > 0.4:
            config[key] = generate_irregular_config(depth + 1, max_depth)
        else:
            value_type = random.choice(["string", "int", "float", "bool", "list", "null"])
            if value_type == "string":
                config[key] = f"value_{random.randint(1, 1000)}"
            elif value_type == "int":
                config[key] = random.randint(-1000, 1000)
            elif value_type == "float":
                config[key] = round(random.uniform(-100, 100), 4)
            elif value_type == "bool":
                config[key] = random.random() > 0.5
            elif value_type == "list":
                config[key] = [random.randint(1, 100) for _ in range(random.randint(1, 5))]
            else:
                config[key] = None

    return config


def generate_heterogeneous_response(resp_id: int) -> dict:
    """Generate completely different structure each time (D2)."""
    structures = [
        lambda: {"id": resp_id, "name": f"Name {resp_id}"},
        lambda: {"code": resp_id, "message": "Error", "details": {"line": 1}},
        lambda: {"items": [1, 2, 3], "count": 3},
        lambda: {"user": {"id": resp_id, "active": True}},
        lambda: {"timestamp": generate_datetime(), "value": random.random()},
        lambda: {"results": [], "query": "test", "filters": {}},
        lambda: {"status": "ok", "data": None},
        lambda: {"a": 1, "b": {"c": 2, "d": {"e": 3}}},
        lambda: {"list": [{"x": 1}, {"y": 2}, {"z": 3}]},
        lambda: {"meta": {"version": "1.0"}, "payload": f"data_{resp_id}"},
    ]

    return random.choice(structures)()


def generate_dynamic_form(form_id: int) -> dict:
    """Generate dynamic form with varied fields (D2)."""
    field_types = ["text", "number", "select", "checkbox", "radio", "textarea", "date", "file"]
    num_fields = random.randint(3, 15)

    form = {
        "formId": form_id,
        "title": f"Form {form_id}",
        "fields": [],
    }

    for i in range(num_fields):
        field_type = random.choice(field_types)
        field = {
            "id": f"field_{i}",
            "type": field_type,
            "label": f"Field {i}",
            "required": random.random() > 0.5,
        }

        # Each field type has different attributes
        if field_type == "text":
            field["maxLength"] = random.randint(10, 500)
            if random.random() > 0.5:
                field["pattern"] = ".*"
        elif field_type == "number":
            field["min"] = 0
            field["max"] = random.randint(10, 1000)
        elif field_type in ["select", "radio"]:
            field["options"] = [f"Option {j}" for j in range(random.randint(2, 10))]
        elif field_type == "textarea":
            field["rows"] = random.randint(3, 10)
        elif field_type == "date":
            field["format"] = random.choice(["YYYY-MM-DD", "MM/DD/YYYY", "DD-MM-YYYY"])
        elif field_type == "file":
            field["accept"] = random.choice([".pdf", ".jpg,.png", ".doc,.docx"])
            field["maxSize"] = random.randint(1, 10) * 1024 * 1024

        form["fields"].append(field)

    return form


def generate_coordinates(num: int) -> list:
    """Generate coordinate pairs - already compact (D3)."""
    return [
        [round(random.uniform(-180, 180), 6), round(random.uniform(-90, 90), 6)] for _ in range(num)
    ]


def generate_id_list(num: int) -> list:
    """Generate simple ID list - already compact (D3)."""
    return [f"id_{i:08d}" for i in range(num)]


# ============================================================================
# File Generation Functions
# ============================================================================


def save_json(data: list | dict, filename: str) -> None:
    """Save data to JSON file with consistent formatting."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    size = filepath.stat().st_size
    print(f"  Generated: {filename} ({size:,} bytes)")


def generate_all_files() -> None:
    """Generate all benchmark files."""
    print("Generating PyToon Benchmark Files...")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Reset seed for consistency
    random.seed(SEED)

    # ========================================================================
    # TIER A: TOON Optimal
    # ========================================================================
    print("=== TIER A: TOON Optimal (40-60%+ savings) ===")

    # A1: Uniform Tabular Arrays
    print("A1: Uniform Tabular Arrays")
    save_json([generate_uniform_user(i) for i in range(1, 101)], "A1_uniform_users_S.json")
    save_json([generate_uniform_user(i) for i in range(1, 1001)], "A1_uniform_users_L.json")
    save_json([generate_uniform_product(i) for i in range(1, 501)], "A1_uniform_products_M.json")

    # A2: Sparse Tabular Arrays
    print("A2: Sparse Tabular Arrays")
    save_json([generate_sparse_profile(i) for i in range(1, 101)], "A2_sparse_profiles_S.json")
    save_json([generate_sparse_profile(i) for i in range(1, 1001)], "A2_sparse_profiles_L.json")
    save_json([generate_sparse_inventory(i) for i in range(1, 501)], "A2_sparse_inventory_M.json")

    # A3: Polymorphic Event Collections
    print("A3: Polymorphic Event Collections")
    save_json([generate_polymorphic_event(i) for i in range(1, 101)], "A3_poly_events_S.json")
    save_json([generate_polymorphic_event(i) for i in range(1, 1001)], "A3_poly_events_L.json")
    save_json(
        [generate_polymorphic_notification(i) for i in range(1, 501)],
        "A3_poly_notifications_M.json",
    )

    print()

    # ========================================================================
    # TIER B: TOON Strong
    # ========================================================================
    print("=== TIER B: TOON Strong (25-40% savings) ===")

    # B1: Rich Type Data
    print("B1: Rich Type Data")
    save_json([generate_audit_log_entry(i) for i in range(1, 501)], "B1_richtypes_audit_M.json")
    save_json(
        [generate_financial_transaction(i) for i in range(1, 1001)],
        "B1_richtypes_transactions_L.json",
    )

    # B2: Relational/Reference Data
    print("B2: Relational/Reference Data")
    products_for_orders = [generate_uniform_product(i) for i in range(1, 101)]
    save_json(
        {
            "products": products_for_orders,
            "orders": [generate_order_with_refs(i, products_for_orders) for i in range(1, 501)],
        },
        "B2_relational_orders_M.json",
    )
    save_json(
        [generate_org_chart_employee(i, 100) for i in range(1, 101)],
        "B2_relational_orgchart_S.json",
    )

    # B3: Nested Uniform Structures
    print("B3: Nested Uniform Structures")
    # Generate category tree
    categories = []
    cat_id = 1
    for i in range(10):  # 10 root categories
        cat = generate_nested_category(cat_id, None, 0, 4)
        categories.append(cat)
        cat_id += 100  # Space for children
    save_json(categories, "B3_nested_categories_M.json")

    # Generate menu hierarchy
    menus = []
    menu_id = 1
    for i in range(20):  # 20 top-level menus
        menu = generate_menu_item(menu_id, None, 0, 5)
        menus.append(menu)
        menu_id += 100
    save_json(menus, "B3_nested_menu_L.json")

    print()

    # ========================================================================
    # TIER C: TOON Moderate
    # ========================================================================
    print("=== TIER C: TOON Moderate (10-25% savings) ===")

    # C1: Semi-Structured Documents
    print("C1: Semi-Structured Documents")
    save_json([generate_blog_post(i) for i in range(1, 501)], "C1_semistructured_posts_M.json")
    save_json([generate_api_response(i) for i in range(1, 1001)], "C1_semistructured_api_L.json")

    # C2: Partially Uniform Collections
    print("C2: Partially Uniform Collections")
    save_json([generate_search_result(i) for i in range(1, 501)], "C2_partial_search_M.json")
    save_json(
        [generate_threaded_comment(i, None, 0) for i in range(1, 201)], "C2_partial_comments_L.json"
    )

    # C3: Configuration with Patterns
    print("C3: Configuration with Patterns")
    save_json([generate_feature_flag(i) for i in range(1, 101)], "C3_config_flags_S.json")

    print()

    # ========================================================================
    # TIER D: Minimal/Negative
    # ========================================================================
    print("=== TIER D: TOON Minimal/Negative (0-15% or worse) ===")

    # D1: Deeply Nested Irregular
    print("D1: Deeply Nested Irregular")
    save_json(
        [generate_irregular_schema_type(i) for i in range(1, 501)], "D1_irregular_schema_M.json"
    )
    save_json(generate_irregular_config(0, 10), "D1_irregular_config_L.json")

    # D2: Highly Heterogeneous
    print("D2: Highly Heterogeneous")
    save_json(
        [generate_heterogeneous_response(i) for i in range(1, 501)], "D2_hetero_responses_M.json"
    )
    save_json([generate_dynamic_form(i) for i in range(1, 201)], "D2_hetero_forms_L.json")

    # D3: Already Compact Primitives
    print("D3: Already Compact Primitives")
    save_json(generate_coordinates(1000), "D3_compact_coordinates_L.json")
    save_json(generate_id_list(5000), "D3_compact_ids_XL.json")

    print()
    print("=" * 50)
    print(f"Generated {len(list(OUTPUT_DIR.glob('*.json')))} benchmark files")
    print(f"Location: {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_all_files()
