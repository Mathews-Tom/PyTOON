"""Unit tests for reference detection system.

Tests the ReferenceEncoder's ability to detect shared object references,
identify reference fields by naming patterns, and generate schema metadata.
"""

import pytest

from pytoon.references import ReferenceEncoder, ReferenceInfo
from pytoon.utils.errors import TOONEncodeError


class TestReferenceInfo:
    """Tests for ReferenceInfo dataclass."""

    def test_default_initialization(self) -> None:
        """ReferenceInfo initializes with empty collections."""
        info = ReferenceInfo()
        assert info.shared_objects == {}
        assert info.reference_fields == set()
        assert info.schema == {}
        assert info.object_count == 0

    def test_shared_objects_storage(self) -> None:
        """ReferenceInfo stores shared object mappings."""
        info = ReferenceInfo()
        obj = {"id": 1, "name": "Alice"}
        info.shared_objects[id(obj)] = (obj, 2, "$1")
        assert id(obj) in info.shared_objects
        stored_obj, count, assigned_id = info.shared_objects[id(obj)]
        assert stored_obj is obj
        assert count == 2
        assert assigned_id == "$1"

    def test_reference_fields_storage(self) -> None:
        """ReferenceInfo stores reference field names."""
        info = ReferenceInfo()
        info.reference_fields.add("userId")
        info.reference_fields.add("authorRef")
        assert "userId" in info.reference_fields
        assert "authorRef" in info.reference_fields
        assert len(info.reference_fields) == 2

    def test_schema_storage(self) -> None:
        """ReferenceInfo stores schema type definitions."""
        info = ReferenceInfo()
        info.schema["User"] = {"id": "int", "name": "str"}
        assert "User" in info.schema
        assert info.schema["User"] == {"id": "int", "name": "str"}


class TestReferenceEncoder:
    """Tests for ReferenceEncoder class."""

    def test_detect_references_empty_data(self) -> None:
        """detect_references handles empty dict."""
        encoder = ReferenceEncoder()
        info = encoder.detect_references({})
        assert info.object_count == 1
        assert len(info.shared_objects) == 0

    def test_detect_references_empty_list(self) -> None:
        """detect_references handles empty list."""
        encoder = ReferenceEncoder()
        info = encoder.detect_references([])
        assert info.object_count == 1
        assert len(info.shared_objects) == 0

    def test_detect_references_primitives(self) -> None:
        """detect_references handles primitives without tracking them."""
        encoder = ReferenceEncoder()

        # Primitives are not tracked by id()
        info = encoder.detect_references(42)
        assert info.object_count == 0
        assert len(info.shared_objects) == 0

        info = encoder.detect_references("string")
        assert info.object_count == 0

        info = encoder.detect_references(None)
        assert info.object_count == 0

        info = encoder.detect_references(True)
        assert info.object_count == 0

    def test_detect_shared_dict_reference(self) -> None:
        """detect_references finds shared dict objects."""
        encoder = ReferenceEncoder()
        user = {"id": 1, "name": "Alice"}
        data = {"users": [user], "admins": [user]}

        info = encoder.detect_references(data)

        # User object is shared (appears twice)
        assert len(info.shared_objects) == 1
        obj_id = id(user)
        assert obj_id in info.shared_objects
        stored_obj, count, assigned_id = info.shared_objects[obj_id]
        assert stored_obj is user
        assert count == 2
        assert assigned_id == "$1"

    def test_detect_multiple_shared_objects(self) -> None:
        """detect_references handles multiple shared objects."""
        encoder = ReferenceEncoder()
        user1 = {"id": 1, "name": "Alice"}
        user2 = {"id": 2, "name": "Bob"}
        role = {"name": "admin", "level": 1}

        data = {
            "users": [user1, user2],
            "admins": [user1],
            "moderators": [user2],
            "roles": {"admin": role, "primary": role},
        }

        info = encoder.detect_references(data)

        # Both user1 and user2 are shared (appear twice each)
        # role is shared (appears twice)
        assert len(info.shared_objects) == 3
        assert id(user1) in info.shared_objects
        assert id(user2) in info.shared_objects
        assert id(role) in info.shared_objects

    def test_no_shared_references_no_schema(self) -> None:
        """detect_references with no shared objects produces empty schema."""
        encoder = ReferenceEncoder()
        data = {"users": [{"id": 1}, {"id": 2}]}

        info = encoder.detect_references(data)

        assert len(info.shared_objects) == 0
        assert info.schema == {}

    def test_shared_object_generates_schema(self) -> None:
        """detect_references generates schema for shared objects."""
        encoder = ReferenceEncoder()
        user = {"id": 1, "name": "Alice", "active": True}
        data = {"a": user, "b": user}

        info = encoder.detect_references(data)

        assert len(info.schema) == 1
        assert "Object1" in info.schema
        assert info.schema["Object1"] == {
            "id": "int",
            "name": "str",
            "active": "bool",
        }

    def test_object_count_tracking(self) -> None:
        """detect_references correctly counts unique objects."""
        encoder = ReferenceEncoder()
        user = {"id": 1}
        data = {
            "root": "value",
            "users": [user, {"id": 2}],
            "admin": user,  # shared reference
        }

        info = encoder.detect_references(data)

        # Counts: root dict(1), users list(1), user dict(1), id:2 dict(1)
        # user is seen twice but counted once
        assert info.object_count == 4

    def test_assigns_sequential_ids(self) -> None:
        """detect_references assigns sequential IDs to shared objects."""
        encoder = ReferenceEncoder()
        obj1 = {"type": "A"}
        obj2 = {"type": "B"}
        obj3 = {"type": "C"}

        data = {
            "a1": obj1,
            "a2": obj1,  # shared
            "b1": obj2,
            "b2": obj2,  # shared
            "c1": obj3,
            "c2": obj3,  # shared
        }

        info = encoder.detect_references(data)

        # Should have 3 shared objects with sequential IDs
        ids = [v[2] for v in info.shared_objects.values()]
        assert set(ids) == {"$1", "$2", "$3"}

    def test_handles_nested_structures(self) -> None:
        """detect_references traverses nested structures."""
        encoder = ReferenceEncoder()
        inner = {"value": 42}
        data = {
            "level1": {
                "level2": {
                    "level3": [inner, inner],
                },
            },
        }

        info = encoder.detect_references(data)

        # inner is shared
        assert len(info.shared_objects) == 1
        assert id(inner) in info.shared_objects

    def test_handles_list_of_lists(self) -> None:
        """detect_references handles nested lists."""
        encoder = ReferenceEncoder()
        inner_list = [1, 2, 3]
        data = [inner_list, inner_list, [4, 5, 6]]

        info = encoder.detect_references(data)

        # Lists are tracked for cycle detection but not assigned IDs
        # Only dicts are assigned IDs for schema generation
        # inner_list is counted once, but referenced twice
        assert info.object_count == 3  # outer list + inner_list + [4,5,6]
        # No shared dicts, so no assigned IDs
        assert len(info.shared_objects) == 0


class TestReferenceFieldIdentification:
    """Tests for reference field identification."""

    def test_identify_userId_field(self) -> None:
        """Fields ending in Id are identified as references."""
        encoder = ReferenceEncoder()
        result = encoder._identify_reference_fields("userId")
        assert result == {"userId"}

    def test_identify_authorRef_field(self) -> None:
        """Fields ending in Ref are identified as references."""
        encoder = ReferenceEncoder()
        result = encoder._identify_reference_fields("authorRef")
        assert result == {"authorRef"}

    def test_identify_multiple_patterns(self) -> None:
        """Various *Id and *Ref patterns are recognized."""
        encoder = ReferenceEncoder()
        assert encoder._identify_reference_fields("customerId") == {"customerId"}
        assert encoder._identify_reference_fields("parentId") == {"parentId"}
        assert encoder._identify_reference_fields("objectRef") == {"objectRef"}
        assert encoder._identify_reference_fields("documentRef") == {"documentRef"}

    def test_non_reference_fields(self) -> None:
        """Regular fields are not identified as references."""
        encoder = ReferenceEncoder()
        assert encoder._identify_reference_fields("name") == set()
        assert encoder._identify_reference_fields("id") == set()  # Just "id"
        assert encoder._identify_reference_fields("valid") == set()
        assert encoder._identify_reference_fields("Referred") == set()

    def test_case_sensitive_matching(self) -> None:
        """Reference pattern matching is case-sensitive."""
        encoder = ReferenceEncoder()
        assert encoder._identify_reference_fields("userId") == {"userId"}
        assert encoder._identify_reference_fields("userid") == set()  # lowercase
        assert encoder._identify_reference_fields("USERID") == set()  # uppercase
        assert encoder._identify_reference_fields("userID") == set()  # wrong case

    def test_detect_references_collects_reference_fields(self) -> None:
        """detect_references collects all reference field names."""
        encoder = ReferenceEncoder()
        data = {
            "userId": 1,
            "authorRef": "Alice",
            "name": "Test",
            "metadata": {
                "parentId": 0,
                "categoryRef": "main",
            },
        }

        info = encoder.detect_references(data)

        assert info.reference_fields == {
            "userId",
            "authorRef",
            "parentId",
            "categoryRef",
        }

    def test_non_string_keys_ignored(self) -> None:
        """Non-string keys are ignored in reference field detection."""
        encoder = ReferenceEncoder()
        # This is technically valid in Python dicts
        result = encoder._identify_reference_fields(123)  # type: ignore[arg-type]
        assert result == set()


class TestSchemaGeneration:
    """Tests for schema generation."""

    def test_generate_schema_int_field(self) -> None:
        """Schema correctly infers int type."""
        encoder = ReferenceEncoder()
        obj = {"value": 42}
        shared = {id(obj): (obj, 2, "$1")}
        schema = encoder._generate_schema(shared)

        assert schema["Object1"]["value"] == "int"

    def test_generate_schema_str_field(self) -> None:
        """Schema correctly infers str type."""
        encoder = ReferenceEncoder()
        obj = {"value": "hello"}
        shared = {id(obj): (obj, 2, "$1")}
        schema = encoder._generate_schema(shared)

        assert schema["Object1"]["value"] == "str"

    def test_generate_schema_float_field(self) -> None:
        """Schema correctly infers float type."""
        encoder = ReferenceEncoder()
        obj = {"value": 3.14}
        shared = {id(obj): (obj, 2, "$1")}
        schema = encoder._generate_schema(shared)

        assert schema["Object1"]["value"] == "float"

    def test_generate_schema_bool_field(self) -> None:
        """Schema correctly infers bool type (not int)."""
        encoder = ReferenceEncoder()
        obj = {"active": True, "disabled": False}
        shared = {id(obj): (obj, 2, "$1")}
        schema = encoder._generate_schema(shared)

        assert schema["Object1"]["active"] == "bool"
        assert schema["Object1"]["disabled"] == "bool"

    def test_generate_schema_null_field(self) -> None:
        """Schema correctly infers null type."""
        encoder = ReferenceEncoder()
        obj = {"value": None}
        shared = {id(obj): (obj, 2, "$1")}
        schema = encoder._generate_schema(shared)

        assert schema["Object1"]["value"] == "null"

    def test_generate_schema_list_field(self) -> None:
        """Schema correctly infers list type."""
        encoder = ReferenceEncoder()
        obj = {"items": [1, 2, 3]}
        shared = {id(obj): (obj, 2, "$1")}
        schema = encoder._generate_schema(shared)

        assert schema["Object1"]["items"] == "list"

    def test_generate_schema_dict_field(self) -> None:
        """Schema correctly infers dict type."""
        encoder = ReferenceEncoder()
        obj = {"nested": {"a": 1}}
        shared = {id(obj): (obj, 2, "$1")}
        schema = encoder._generate_schema(shared)

        assert schema["Object1"]["nested"] == "dict"

    def test_generate_schema_multiple_fields(self) -> None:
        """Schema handles objects with multiple fields."""
        encoder = ReferenceEncoder()
        obj = {
            "id": 1,
            "name": "Alice",
            "score": 95.5,
            "active": True,
            "metadata": None,
        }
        shared = {id(obj): (obj, 2, "$1")}
        schema = encoder._generate_schema(shared)

        assert schema["Object1"] == {
            "id": "int",
            "name": "str",
            "score": "float",
            "active": "bool",
            "metadata": "null",
        }

    def test_generate_schema_multiple_objects(self) -> None:
        """Schema generates entries for multiple shared objects."""
        encoder = ReferenceEncoder()
        obj1 = {"id": 1}
        obj2 = {"name": "Alice"}
        shared = {
            id(obj1): (obj1, 2, "$1"),
            id(obj2): (obj2, 2, "$2"),
        }
        schema = encoder._generate_schema(shared)

        assert len(schema) == 2
        assert "Object1" in schema
        assert "Object2" in schema

    def test_generate_schema_empty_shared_objects(self) -> None:
        """Schema is empty when no shared objects exist."""
        encoder = ReferenceEncoder()
        schema = encoder._generate_schema({})
        assert schema == {}


class TestTypeInference:
    """Tests for type inference helper."""

    def test_infer_type_int(self) -> None:
        """_infer_type correctly identifies int."""
        encoder = ReferenceEncoder()
        assert encoder._infer_type(0) == "int"
        assert encoder._infer_type(42) == "int"
        assert encoder._infer_type(-100) == "int"

    def test_infer_type_float(self) -> None:
        """_infer_type correctly identifies float."""
        encoder = ReferenceEncoder()
        assert encoder._infer_type(0.0) == "float"
        assert encoder._infer_type(3.14) == "float"
        assert encoder._infer_type(-2.5) == "float"

    def test_infer_type_bool(self) -> None:
        """_infer_type correctly identifies bool (before int check)."""
        encoder = ReferenceEncoder()
        assert encoder._infer_type(True) == "bool"
        assert encoder._infer_type(False) == "bool"

    def test_infer_type_str(self) -> None:
        """_infer_type correctly identifies str."""
        encoder = ReferenceEncoder()
        assert encoder._infer_type("") == "str"
        assert encoder._infer_type("hello") == "str"

    def test_infer_type_null(self) -> None:
        """_infer_type correctly identifies null."""
        encoder = ReferenceEncoder()
        assert encoder._infer_type(None) == "null"

    def test_infer_type_list(self) -> None:
        """_infer_type correctly identifies list."""
        encoder = ReferenceEncoder()
        assert encoder._infer_type([]) == "list"
        assert encoder._infer_type([1, 2, 3]) == "list"

    def test_infer_type_dict(self) -> None:
        """_infer_type correctly identifies dict."""
        encoder = ReferenceEncoder()
        assert encoder._infer_type({}) == "dict"
        assert encoder._infer_type({"a": 1}) == "dict"

    def test_infer_type_fallback(self) -> None:
        """_infer_type uses type name for unknown types."""
        encoder = ReferenceEncoder()
        assert encoder._infer_type(set()) == "set"
        assert encoder._infer_type((1, 2)) == "tuple"


class TestErrorHandling:
    """Tests for error handling in reference detection."""

    def test_detect_references_handles_deeply_nested(self) -> None:
        """detect_references handles deeply nested structures."""
        encoder = ReferenceEncoder()

        # Create deeply nested structure (not enough to cause recursion error)
        data: dict[str, Any] = {}
        current = data
        for i in range(50):
            current["nested"] = {}
            current = current["nested"]
        current["value"] = 42

        info = encoder.detect_references(data)
        assert info.object_count == 51  # 51 nested dicts

    def test_detect_references_large_array(self) -> None:
        """detect_references handles large arrays efficiently."""
        encoder = ReferenceEncoder()

        # Large array of unique objects
        data = [{"id": i} for i in range(1000)]

        info = encoder.detect_references(data)
        assert info.object_count == 1001  # 1 list + 1000 dicts
        assert len(info.shared_objects) == 0  # No shared objects


class TestONComplexity:
    """Tests to verify O(n) traversal complexity."""

    def test_shared_object_not_revisited(self) -> None:
        """Shared objects are not recursively traversed again."""
        encoder = ReferenceEncoder()

        # Create shared object with nested content
        shared = {"id": 1, "nested": {"deep": {"value": 42}}}
        data = {"a": shared, "b": shared, "c": shared}

        info = encoder.detect_references(data)

        # Despite being referenced 3 times, nested structure counted once
        # root(1) + shared(1) + nested(1) + deep(1) = 4
        assert info.object_count == 4

        # shared is the only shared object
        assert len(info.shared_objects) == 1
        assert info.shared_objects[id(shared)][1] == 3  # count is 3

    def test_performance_linear_with_data_size(self) -> None:
        """Object count scales linearly with data size."""
        encoder = ReferenceEncoder()

        # Small data
        small_data = [{"id": i} for i in range(10)]
        small_info = encoder.detect_references(small_data)

        # Larger data (10x)
        large_data = [{"id": i} for i in range(100)]
        large_info = encoder.detect_references(large_data)

        # Object count should scale linearly
        # small: 1 list + 10 dicts = 11
        # large: 1 list + 100 dicts = 101
        assert small_info.object_count == 11
        assert large_info.object_count == 101

        # Ratio should be approximately 10x
        ratio = large_info.object_count / small_info.object_count
        assert 9.0 <= ratio <= 10.0
