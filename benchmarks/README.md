# PyToon Benchmark Suite

Comprehensive benchmark files for evaluating TOON (Token-Oriented Object Notation) performance against JSON. These files are designed to systematically test TOON's optimization strategies across different data patterns.

## Key Insight

**TOON efficiency is determined by DATA UNIFORMITY and PATTERN EXPLOITATION, not nesting depth.**

A deeply nested but uniform structure can yield excellent savings, while a flat but heterogeneous structure may show minimal benefit.

---

## Important: Current Implementation Status

**PyToon v1.0-1.2 Basic Encoder** supports:

- ✅ **Uniform tabular arrays** (identical fields, primitive values only) → 30-60% savings
- ✅ **Nested structures with uniform sub-arrays** → 10-25% savings
- ✅ **Flat objects** → 10-20% savings
- ⚠️ **Heterogeneous arrays** (list format) → **DECODER BUG** - roundtrip fails
- ❌ Sparse array encoding (v1.2 feature not auto-integrated)
- ❌ Polymorphic sub-tables (v1.2 feature not auto-integrated)
- ❌ Reference deduplication (v1.1 feature requires `encode_refs()`)

**Actual Performance** (from benchmark run):

- Tier A1 (Uniform): **+31-60% savings**, 100% roundtrip pass
- Tier A2 (Sparse): **+48-58% savings** (treated as tabular with null values)
- Tier A3 (Polymorphic): **Roundtrip FAIL** (decoder bug with list format)
- Tier B/C/D: Mixed results, many failures due to nested/heterogeneous data

**Use `smart_encode()` for automatic format recommendation** - it will suggest JSON for heterogeneous data.

---

## Benchmark Categories

### Tier A: TOON OPTIMAL (Expected 40-60%+ savings)

*Showcases TOON's maximum strengths*

| ID | Category | Description | Optimization Strategy |
|----|----------|-------------|----------------------|
| **A1** | Uniform Tabular Arrays | Identical fields across all objects | Tabular format with field header |
| **A2** | Sparse Tabular Arrays | Many optional/null fields (30%+) | Sparse encoding with `field?` markers |
| **A3** | Polymorphic Collections | Mixed types with discriminator | Sub-tables by type (`@type:`) |

### Tier B: TOON STRONG (Expected 25-40% savings)

*Significant advantages from specific optimizations*

| ID | Category | Description | Optimization Strategy |
|----|----------|-------------|----------------------|
| **B1** | Rich Type Data | UUIDs, timestamps, dates, Decimals | Type handlers compress representations |
| **B2** | Relational/Reference Data | Foreign key relationships | Reference deduplication (`$1`, `$2`) |
| **B3** | Nested Uniform Structures | Trees with consistent shape | Pattern exploitation in nesting |

### Tier C: TOON MODERATE (Expected 10-25% savings)

*Mixed results, generally positive*

| ID | Category | Description | Optimization Strategy |
|----|----------|-------------|----------------------|
| **C1** | Semi-Structured Documents | Content + metadata | Partial uniformity benefits |
| **C2** | Partially Uniform Collections | Some patterns, some irregularity | Limited pattern exploitation |
| **C3** | Configuration with Patterns | Settings with repeating structures | Key folding opportunities |

### Tier D: TOON MINIMAL/NEGATIVE (Expected 0-15% or worse)

*Demonstrates honest limitations*

| ID | Category | Description | Why Limited |
|----|----------|-------------|-------------|
| **D1** | Deeply Nested Irregular | Complex configs, schemas | No exploitable patterns |
| **D2** | Highly Heterogeneous | Every object different | No structural consistency |
| **D3** | Already Compact Primitives | Number lists, ID arrays | JSON already efficient |

---

## Size Tiers

| Size | Code | Record Count | Approx. File Size | Token Range |
|------|------|-------------|-------------------|-------------|
| Extra Small | XS | 10 | ~1-2 KB | ~200-500 |
| Small | S | 100 | ~10-20 KB | ~2K-5K |
| Medium | M | 500 | ~50-100 KB | ~10K-25K |
| Large | L | 1,000 | ~200-500 KB | ~50K-125K |
| Extra Large | XL | 5,000 | ~1-2 MB | ~250K-500K |

---

## File Inventory

### Tier A: TOON Optimal (12 files)

#### A1 - Uniform Tabular Arrays

- `A1_uniform_users_S.json` - 100 user records with identical fields
- `A1_uniform_users_L.json` - 1,000 user records
- `A1_uniform_products_M.json` - 500 product catalog entries

#### A2 - Sparse Tabular Arrays

- `A2_sparse_profiles_S.json` - 100 user profiles, ~40% optional fields null
- `A2_sparse_profiles_L.json` - 1,000 user profiles
- `A2_sparse_inventory_M.json` - 500 inventory items with partial metadata

#### A3 - Polymorphic Event Collections

- `A3_poly_events_S.json` - 100 mixed event types (click, view, purchase, etc.)
- `A3_poly_events_L.json` - 1,000 events
- `A3_poly_notifications_M.json` - 500 notifications of different types

### Tier B: TOON Strong (9 files)

#### B1 - Rich Type Data

- `B1_richtypes_audit_M.json` - 500 audit log entries with UUIDs, timestamps
- `B1_richtypes_transactions_L.json` - 1,000 financial transactions with Decimals

#### B2 - Relational/Reference Data

- `B2_relational_orders_M.json` - 500 orders with product references
- `B2_relational_orgchart_S.json` - 100 employees with manager references

#### B3 - Nested Uniform Structures

- `B3_nested_categories_M.json` - Category tree (500 nodes)
- `B3_nested_menu_L.json` - Menu hierarchy (1,000 items)

### Tier C: TOON Moderate (9 files)

#### C1 - Semi-Structured Documents

- `C1_semistructured_posts_M.json` - 500 blog posts with metadata
- `C1_semistructured_api_L.json` - 1,000 varied API responses

#### C2 - Partially Uniform Collections

- `C2_partial_search_M.json` - 500 search results with varied metadata
- `C2_partial_comments_L.json` - 1,000 threaded comments

#### C3 - Configuration with Patterns

- `C3_config_flags_S.json` - 100 feature flags

### Tier D: TOON Minimal/Negative (6 files)

#### D1 - Deeply Nested Irregular

- `D1_irregular_schema_M.json` - Complex schema definition (500 types)
- `D1_irregular_config_L.json` - Deep nested app configuration

#### D2 - Highly Heterogeneous

- `D2_hetero_responses_M.json` - 500 completely different response structures
- `D2_hetero_forms_L.json` - 1,000 dynamic form definitions

#### D3 - Already Compact Primitives

- `D3_compact_coordinates_L.json` - 1,000 coordinate pairs (just numbers)
- `D3_compact_ids_XL.json` - 5,000 ID strings

---

## File Naming Convention

```
{Tier}{Subcategory}_{optimization}_{domain}_{size}.json
```

Examples:

- `A1_uniform_users_L.json` - Tier A, Subcategory 1, uniform optimization, users domain, Large size
- `B2_relational_orders_M.json` - Tier B, Subcategory 2, relational optimization, orders domain, Medium size
- `D1_irregular_config_L.json` - Tier D, Subcategory 1, irregular pattern, config domain, Large size

---

## Data Generation

All files are generated using **deterministic seeding** for reproducibility:

```python
import random
random.seed(42)  # Consistent across runs
```

### Data Characteristics

1. **Realistic Distributions**
   - Names: Common first/last name combinations
   - Emails: Properly formatted with realistic domains
   - Dates: Recent past (last 2 years)
   - Prices: Log-normal distribution (realistic pricing)
   - IDs: UUIDs v4 format

2. **Domain-Specific Patterns**
   - User data: Age 18-80, status distribution (active heavy)
   - Products: Categories, prices, stock levels
   - Events: Timestamp sequences, action distributions
   - Financial: Proper decimal precision

3. **Sparse Data Patterns**
   - Optional fields: 30-50% null rate
   - Realistic patterns (bio often null, phone sometimes null)
   - Not random - follows real-world patterns

4. **Polymorphic Distributions**
   - Event types: Zipf distribution (common events frequent)
   - Each type has specific fields
   - Discriminator field consistent

---

## Running Benchmarks

### Basic Token Comparison

```bash
# Single file
pytoon encode samples/A1_uniform_users_L.json --stats

# Compare all files
python benchmark_runner.py --all
```

### Expected Output

```
File: A1_uniform_users_L.json
JSON Tokens: 125,432
TOON Tokens: 52,181
Savings: 58.4%
Encoding Time: 45.2ms
Decoding Time: 38.7ms
Roundtrip: PASS
```

### Comprehensive Benchmark Script

```python
import pytoon
from pytoon.utils import TokenCounter
import json
import time
from pathlib import Path

def benchmark_file(filepath: Path) -> dict:
    """Benchmark a single JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    counter = TokenCounter()

    # Measure encoding
    start = time.perf_counter()
    toon_str = pytoon.encode(data)
    encode_time = (time.perf_counter() - start) * 1000

    # Measure decoding
    start = time.perf_counter()
    decoded = pytoon.decode(toon_str)
    decode_time = (time.perf_counter() - start) * 1000

    # Token counts
    json_str = json.dumps(data, separators=(',', ':'))
    json_tokens = counter.count_tokens(json_str)
    toon_tokens = counter.count_tokens(toon_str)

    # Roundtrip check
    roundtrip_ok = decoded == data

    return {
        'file': filepath.name,
        'json_bytes': len(json_str),
        'toon_bytes': len(toon_str),
        'json_tokens': json_tokens,
        'toon_tokens': toon_tokens,
        'savings_pct': (1 - toon_tokens / json_tokens) * 100,
        'encode_ms': encode_time,
        'decode_ms': decode_time,
        'roundtrip': 'PASS' if roundtrip_ok else 'FAIL'
    }
```

---

## Expected Results by Tier

**NOTE: These are THEORETICAL expectations based on full v1.2 features. Actual results with basic encoder differ significantly.**

### Tier A: TOON Optimal (Actual v1.2 Performance)

```
A1_uniform_users_S.json       → +44.0% savings ✅ PASS
A1_uniform_users_L.json       → +44.1% savings ✅ PASS
A1_uniform_products_M.json    → +59.3% savings ✅ PASS
A2_sparse_profiles_S.json     → +41.4% savings ✅ PASS
A2_sparse_profiles_L.json     → +41.2% savings ✅ PASS
A2_sparse_inventory_M.json    → +55.8% savings ✅ PASS
A3_poly_events_S.json         → -3.9% ✅ PASS (polymorphic, no tabular benefit)
A3_poly_events_L.json         → -4.1% ✅ PASS (polymorphic, no tabular benefit)
A3_poly_notifications_M.json  → -3.1% ❌ FAIL (nested objects lose indentation)
```

### Tier B: TOON Strong (Actual v1.2 Performance)

```
B1_richtypes_audit_M.json        → -5.0% ❌ FAIL (nested payload loses structure)
B1_richtypes_transactions_L.json → +46.9% ✅ PASS (uniform line items)
B2_relational_orders_M.json      → +9.3% 🔴 DECODE_FAIL (nested arrays in objects)
B2_relational_orgchart_S.json    → +56.4% ✅ PASS (flat tabular structure)
B3_nested_categories_M.json      → -257.1% 🔴 DECODE_FAIL (deep recursive nesting)
B3_nested_menu_L.json            → -348.2% 🔴 DECODE_FAIL (deep recursive nesting)
```

### Tier C: TOON Moderate (Actual v1.2 Performance)

```
C1_semistructured_posts_M.json → -1.1% ❌ FAIL (nested objects lose structure)
C1_semistructured_api_L.json   → -14.3% ❌ FAIL (nested data flattening)
C2_partial_search_M.json       → -1.9% ✅ PASS (flat structure with metadata)
C2_partial_comments_L.json     → -21.3% 🔴 DECODE_FAIL (nested thread structure)
C3_config_flags_S.json         → -5.8% ❌ FAIL (nested feature objects)
```

### Tier D: Minimal/Negative (Actual v1.2 Performance)

```
D1_irregular_schema_M.json    → -42.6% ❌ FAIL (schema complexity)
D1_irregular_config_L.json    → -691.0% ❌ FAIL (massive token inflation)
D2_hetero_responses_M.json    → -23.5% 🔴 DECODE_FAIL (no common structure)
D2_hetero_forms_L.json        → -38.8% 🔴 DECODE_FAIL (dynamic form fields)
D3_compact_coordinates_L.json → -30.4% ❌ FAIL (overhead on simple data)
D3_compact_ids_XL.json        → +14.3% ✅ PASS (uniform string array)
```

### Summary of Actual Results

**Overall: 12/26 PASS (46.2%), Average Savings: -41.5%**

**What works well:**

- Uniform tabular arrays (A1): +44-59% savings - excellent compression
- Sparse arrays with nulls (A2): +41-56% savings - nulls compress well
- Flat relational data (B2_orgchart): +56% savings - no nesting complexity
- Uniform line items (B1_transactions): +47% savings - tabular format
- String arrays (D3_ids): +14% savings - no overhead

**What fails:**

- **Nested objects in arrays**: Decoder doesn't track indentation properly
- **Deeply nested structures**: Indentation overhead explodes token count
- **Polymorphic data without tabular format**: No structural optimization possible
- **Complex configs**: Indentation-based nesting loses hierarchical context

**Key Limitation**: The core decoder (`pytoon/core/decoder.py`) doesn't properly track indentation levels for nested objects within list-format arrays. When an array item contains nested objects, the decoder loses the hierarchical structure.

---

## Critical Findings

### Remaining Decoder Limitation: Indentation Tracking

**Issue**: The TOON core decoder doesn't properly track indentation levels for nested objects in list-format arrays. When a list item contains nested objects (e.g., `payload: { event: notification }`), the nested fields get hoisted up as siblings instead of remaining nested.

**Root Cause**: The `_parse_object()` method in `pytoon/core/decoder.py` strips all indentation before parsing, losing the hierarchical structure information.

**Previously Fixed**: List-format array parsing now correctly groups lines by `- ` markers.

**Still Broken**: Nested objects within list items don't preserve their structure.

**Reproduction**:

```python
import pytoon

# Data with nested object inside list item
data = [
    {
        'id': 1,
        'type': 'webhook',
        'payload': {'event': 'notification', 'id': 1}  # Nested object
    }
]

toon = pytoon.encode(data)
# Output:
# [1]:
#   -   id: 1
#   type: webhook
#   payload:
#         event: notification
#         id: 1

decoded = pytoon.decode(toon)
# Returns: [{'id': 1, 'type': 'webhook', 'payload': '', 'event': 'notification'}]
# WRONG! 'event' and inner 'id' hoisted up, 'payload' becomes empty string
# Expected: [{'id': 1, 'type': 'webhook', 'payload': {'event': 'notification', 'id': 1}}]
```

**Note**: Simple flat list arrays now work correctly:

```python
# This works!
data = [
    {'id': 1, 'type': 'a', 'value': 10},
    {'id': 2, 'type': 'b', 'extra': 'data'}
]
decoded = pytoon.decode(pytoon.encode(data))
# Returns: [{'id': 1, 'type': 'a', 'value': 10}, {'id': 2, 'type': 'b', 'extra': 'data'}]
# ✅ Correct!
```

**Impact**: Files with nested objects in list-format arrays fail roundtrip (14/26 files affected).

**Workaround**: Use TOON for:
- Uniform tabular arrays (all objects have identical fields) - best compression
- Flat list arrays (objects with no nested structures) - works correctly
- Avoid deeply nested structures with indentation

---

## Validation Checklist

For each generated file:

- [ ] Valid JSON syntax (passes `json.loads()`)
- [ ] Correct record count matches size tier
- [ ] File size within expected range
- [ ] Data patterns match category description
- [ ] No PII or sensitive information
- [ ] Deterministically reproducible (same seed = same output)
- [ ] Realistic distributions (not random noise)

---

## Use Cases

1. **Performance Marketing**
   - Show 30-60% savings on real-world patterns
   - Demonstrate specific optimization strategies
   - Honest limitations (Tier D)

2. **Regression Testing**
   - Consistent files for CI/CD
   - Detect performance degradation
   - Verify roundtrip fidelity

3. **Algorithm Tuning**
   - Identify optimization opportunities
   - Test threshold adjustments
   - Profile hot paths

4. **Documentation**
   - Concrete examples for API docs
   - Tutorial material
   - Best practices guide

---

## Contributing

To add new benchmark files:

1. Follow naming convention: `{Tier}{Sub}_{optimization}_{domain}_{size}.json`
2. Update this README with file description
3. Use deterministic seeding
4. Document expected savings range
5. Ensure no PII or copyrighted content

---

## License

Benchmark data is synthetic and freely usable under the same license as PyToon.

---

## Questions?

If you need additional benchmark patterns or have questions about the test suite, please open an issue on the PyToon repository.
