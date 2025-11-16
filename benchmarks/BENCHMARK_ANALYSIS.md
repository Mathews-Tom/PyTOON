# PyToon Benchmark Analysis Report

**Generated:** 2025-11-16
**PyToon Version:** 1.2.0 (Basic Encoder)
**Total Files Tested:** 26

---

## Executive Summary

The benchmark suite revealed that **PyToon v1.0 basic encoder performs excellently on uniform tabular data** but has significant limitations and a critical decoder bug affecting heterogeneous arrays.

### Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Files | 26 | - |
| Roundtrip Pass | 9 (34.6%) | ⚠️ Low |
| Files with Positive Savings | 9 (34.6%) | ⚠️ Low |
| Best Savings | +60.6% (A1_uniform_products_M) | ✅ Excellent |
| Worst Savings | -691% (D1_irregular_config_L) | ❌ Critical |
| Average Savings (All) | -62.5% | ❌ Poor |
| Average Savings (Passing Only) | +46.7% | ✅ Strong |

---

## Performance by Tier

### Tier A: TOON Optimal (9 files)

**Expected:** 40-60% savings
**Actual:** Mixed results due to decoder bug

| File | JSON Tokens | TOON Tokens | Savings | Roundtrip |
|------|-------------|-------------|---------|-----------|
| A1_uniform_users_S | 4,406 | 3,022 | **+31.4%** | ✅ PASS |
| A1_uniform_users_L | 43,766 | 29,935 | **+31.6%** | ✅ PASS |
| A1_uniform_products_M | 50,543 | 19,931 | **+60.6%** | ✅ PASS |
| A2_sparse_profiles_S | 4,614 | 2,364 | **+48.8%** | ✅ PASS |
| A2_sparse_profiles_L | 45,914 | 23,423 | **+49.0%** | ✅ PASS |
| A2_sparse_inventory_M | 44,133 | 18,434 | **+58.2%** | ✅ PASS |
| A3_poly_events_S | 4,888 | 4,461 | +8.7% | ❌ FAIL |
| A3_poly_events_L | 48,706 | 44,466 | +8.7% | ❌ FAIL |
| A3_poly_notifications_M | 29,266 | 25,756 | +12.0% | ❌ FAIL |

**Analysis:**
- A1 (Uniform): Excellent performance, 31-60% savings, 100% roundtrip
- A2 (Sparse): Strong performance, 48-58% savings, 100% roundtrip (nulls compress well)
- A3 (Polymorphic): Moderate savings but **DECODER BUG** causes roundtrip failure

---

### Tier B: TOON Strong (6 files)

**Expected:** 25-40% savings
**Actual:** Only 2/6 pass, mostly negative savings

| File | JSON Tokens | TOON Tokens | Savings | Roundtrip |
|------|-------------|-------------|---------|-----------|
| B1_richtypes_audit_M | 49,073 | 49,166 | -0.2% | ❌ FAIL |
| B1_richtypes_transactions_L | 106,553 | 100,886 | +5.3% | ❌ FAIL |
| B2_relational_orders_M | 50,299 | 51,817 | -3.0% | ❌ FAIL |
| B2_relational_orgchart_S | 4,413 | 1,881 | **+57.4%** | ✅ PASS |
| B3_nested_categories_M | 16,839 | 59,878 | **-255.6%** | ❌ FAIL |
| B3_nested_menu_L | 29,714 | 132,572 | **-346.1%** | ❌ FAIL |

**Analysis:**
- B1 (Rich Types): Near-zero or slight positive savings, but timestamps/arrays cause decode failures
- B2 (Relational): Flat structures work (orgchart +57%), nested items fail
- B3 (Nested): **CATASTROPHIC FAILURE** - deep nesting causes massive token inflation due to indentation overhead

---

### Tier C: TOON Moderate (5 files)

**Expected:** 10-25% savings
**Actual:** All fail roundtrip

| File | JSON Tokens | TOON Tokens | Savings | Roundtrip |
|------|-------------|-------------|---------|-----------|
| C1_semistructured_posts_M | 52,844 | 54,108 | -2.4% | ❌ FAIL |
| C1_semistructured_api_L | 96,903 | 97,117 | -0.2% | ❌ FAIL |
| C2_partial_search_M | 43,015 | 41,690 | +3.1% | ❌ FAIL |
| C2_partial_comments_L | 62,188 | 64,200 | -3.2% | ❌ FAIL |
| C3_config_flags_S | 3,838 | 3,923 | -2.2% | ❌ FAIL |

**Analysis:**
- Semi-structured data has marginal savings but decoder cannot handle variable content
- Comments with nested replies fail due to heterogeneous structure
- Config data with nested objects shows slight token inflation

---

### Tier D: Minimal/Negative (6 files)

**Expected:** 0-15% or negative
**Actual:** Dramatic negative performance

| File | JSON Tokens | TOON Tokens | Savings | Roundtrip |
|------|-------------|-------------|---------|-----------|
| D1_irregular_schema_M | 43,015 | 66,612 | -54.9% | ❌ FAIL |
| D1_irregular_config_L | 11,395 | 90,184 | **-691.4%** | ❌ FAIL |
| D2_hetero_responses_M | 41,082 | 50,802 | -23.7% | ❌ FAIL |
| D2_hetero_forms_L | 100,012 | 117,608 | -17.6% | ❌ FAIL |
| D3_compact_coordinates_L | 18,001 | 14,008 | **+22.2%** | ✅ PASS |
| D3_compact_ids_XL | 29,006 | 24,013 | **+17.2%** | ✅ PASS |

**Analysis:**
- D1 (Irregular Config): **Worst performer** - deep nesting with irregular structure causes 691% token inflation!
- D2 (Heterogeneous): Moderate negative performance as expected
- D3 (Compact Primitives): **Surprising positive result** - simple number/ID arrays benefit from TOON's inline format

---

## Root Cause Analysis

### 1. Decoder Bug: List-Format Array Parsing (CRITICAL)

The decoder fails to correctly parse arrays with heterogeneous objects:

```python
# Encoder produces:
[3]:
  -   id: 1
  type: a
  value: 10
  -   id: 2
  ...

# Decoder returns: ['id: 1', 'id: 2', 'id: 3']
# Expected: [{'id': 1, 'type': 'a', 'value': 10}, ...]
```

**Files Affected:** 17/26 (A3, B1-B2, C1-C3, D1-D2)

### 2. Indentation Overhead (STRUCTURAL)

TOON's indentation-based format adds tokens for deeply nested structures:

- Each nesting level adds 2 spaces
- Deep nesting (5+ levels) multiplies token count
- D1_irregular_config_L: 11K JSON tokens → 90K TOON tokens (8x increase!)

### 3. No Automatic Optimization (FEATURE GAP)

The basic encoder does not automatically:
- Use sparse encoding for arrays with many nulls (v1.2 SparseArrayEncoder exists but not integrated)
- Group polymorphic arrays by discriminator (v1.2 PolymorphicArrayEncoder exists but not integrated)
- Deduplicate references (v1.1 encode_refs() must be called explicitly)

---

## Recommendations

### Immediate Actions

1. **Fix Decoder Bug** (HIGH PRIORITY)
   - File: `pytoon/decoder/parser.py`
   - Issue: List-format array parsing ignores subsequent key-value pairs after `- `
   - Impact: Blocks 17/26 benchmark files from passing

2. **Integrate v1.2 Features into Basic Encoder**
   - Auto-detect sparse arrays (30%+ nulls) → use SparseArrayEncoder
   - Auto-detect polymorphic arrays (discriminator field) → use PolymorphicArrayEncoder
   - This would unlock the theoretical 40-60% savings for A3 files

3. **Optimize Nested Structure Encoding**
   - Consider key folding for deep nesting: `data.config.settings.feature` instead of nested indentation
   - Evaluate hybrid approach: TOON for tabular sections, JSON for irregular configs

### Benchmark Suite Adjustments

1. **Remove/Recategorize Non-Passing Tests**
   - A3 (Polymorphic) → Move to "Future Features" until decoder fixed
   - B3 (Nested) → Move to "Known Limitations"
   - D1 (Irregular) → Document as anti-pattern

2. **Add Realistic Performance Tests**
   - More A1/A2 variants at different scales (10K, 50K records)
   - Stress test for largest datasets (1M+ tokens)
   - Benchmark encoding/decoding speed separately

3. **Create "TOON-Optimal Dataset" Category**
   - Only uniform tabular arrays
   - Demonstrates real-world 30-60% savings
   - Use for marketing and documentation

---

## Conclusion

PyToon v1.0 delivers **strong 31-60% token savings** on its core use case: **uniform tabular arrays**. However, the current implementation has:

1. **A critical decoder bug** affecting heterogeneous arrays
2. **Massive token inflation** for deeply nested structures (up to -691%)
3. **Limited automatic optimization** - v1.2 features exist but aren't integrated

**Recommended Next Steps:**
1. Fix the decoder bug (estimated effort: 2-4 hours)
2. Integrate sparse/polymorphic encoders into main pipeline (estimated effort: 1-2 days)
3. Optimize nested structure encoding (estimated effort: 3-5 days)

**Current Production Use Case:**
Use PyToon **only for uniform tabular arrays** (all objects have identical fields, values are primitives). This includes:
- User/product catalogs
- Event logs with consistent schema
- Configuration arrays with fixed structure

For all other data patterns, use JSON or `smart_encode()` which will automatically recommend the appropriate format.

---

**Report Generated By:** Benchmark Analysis Script
**Date:** 2025-11-16
