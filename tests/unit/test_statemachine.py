"""Unit tests for StateMachine class.

Tests cover:
- State transitions
- Indentation stack management
- Context stack management
- Validation and error handling
"""

import pytest

from pytoon.decoder.statemachine import ParserState, StateMachine
from pytoon.utils.errors import TOONDecodeError


class TestStateMachineInit:
    """Test StateMachine initialization."""

    def test_default_init(self) -> None:
        """Test default initialization."""
        sm = StateMachine()
        assert sm.state == ParserState.INITIAL
        assert sm.current_indent == 0
        assert sm.indent_stack == [0]
        assert sm.indent_size == 2
        assert sm.nesting_depth == 0
        assert sm.context_stack == []

    def test_custom_indent_size(self) -> None:
        """Test initialization with custom indent size."""
        sm = StateMachine(indent_size=4)
        assert sm.indent_size == 4

    def test_invalid_indent_size_zero(self) -> None:
        """Test that zero indent size raises error."""
        with pytest.raises(ValueError, match="indent_size must be positive"):
            StateMachine(indent_size=0)

    def test_invalid_indent_size_negative(self) -> None:
        """Test that negative indent size raises error."""
        with pytest.raises(ValueError, match="indent_size must be positive"):
            StateMachine(indent_size=-1)


class TestStateTransitions:
    """Test state transition logic."""

    def test_initial_to_expect_key(self) -> None:
        """Test transition from INITIAL to EXPECT_KEY."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        assert sm.state == ParserState.EXPECT_KEY

    def test_initial_to_complete(self) -> None:
        """Test transition from INITIAL to COMPLETE (empty input)."""
        sm = StateMachine()
        sm.transition_to(ParserState.COMPLETE)
        assert sm.state == ParserState.COMPLETE

    def test_expect_key_to_expect_colon(self) -> None:
        """Test transition from EXPECT_KEY to EXPECT_COLON."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.transition_to(ParserState.EXPECT_COLON)
        assert sm.state == ParserState.EXPECT_COLON

    def test_expect_colon_to_expect_value(self) -> None:
        """Test transition from EXPECT_COLON to EXPECT_VALUE."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.transition_to(ParserState.EXPECT_COLON)
        sm.transition_to(ParserState.EXPECT_VALUE)
        assert sm.state == ParserState.EXPECT_VALUE

    def test_expect_value_to_nested_object(self) -> None:
        """Test transition to nested object state."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.transition_to(ParserState.EXPECT_COLON)
        sm.transition_to(ParserState.EXPECT_VALUE)
        sm.transition_to(ParserState.IN_NESTED_OBJECT)
        assert sm.state == ParserState.IN_NESTED_OBJECT

    def test_expect_value_to_array_tabular(self) -> None:
        """Test transition to tabular array state."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.transition_to(ParserState.EXPECT_COLON)
        sm.transition_to(ParserState.EXPECT_VALUE)
        sm.transition_to(ParserState.IN_ARRAY_TABULAR)
        assert sm.state == ParserState.IN_ARRAY_TABULAR

    def test_expect_value_to_array_inline(self) -> None:
        """Test transition to inline array state."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.transition_to(ParserState.EXPECT_COLON)
        sm.transition_to(ParserState.EXPECT_VALUE)
        sm.transition_to(ParserState.IN_ARRAY_INLINE)
        assert sm.state == ParserState.IN_ARRAY_INLINE

    def test_expect_value_to_array_list(self) -> None:
        """Test transition to list array state."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.transition_to(ParserState.EXPECT_COLON)
        sm.transition_to(ParserState.EXPECT_VALUE)
        sm.transition_to(ParserState.IN_ARRAY_LIST)
        assert sm.state == ParserState.IN_ARRAY_LIST

    def test_array_tabular_to_expect_key(self) -> None:
        """Test transition from tabular array back to expect key."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.transition_to(ParserState.EXPECT_COLON)
        sm.transition_to(ParserState.EXPECT_VALUE)
        sm.transition_to(ParserState.IN_ARRAY_TABULAR)
        sm.transition_to(ParserState.EXPECT_KEY)
        assert sm.state == ParserState.EXPECT_KEY

    def test_invalid_transition_from_complete(self) -> None:
        """Test that transitions from COMPLETE are invalid."""
        sm = StateMachine()
        sm.transition_to(ParserState.COMPLETE)
        with pytest.raises(TOONDecodeError, match="Invalid state transition"):
            sm.transition_to(ParserState.EXPECT_KEY)

    def test_invalid_transition_from_error(self) -> None:
        """Test that transitions from ERROR are invalid."""
        sm = StateMachine()
        sm.transition_to(ParserState.ERROR)
        with pytest.raises(TOONDecodeError, match="Invalid state transition"):
            sm.transition_to(ParserState.INITIAL)

    def test_invalid_transition_initial_to_colon(self) -> None:
        """Test invalid transition from INITIAL to EXPECT_COLON."""
        sm = StateMachine()
        with pytest.raises(TOONDecodeError, match="Invalid state transition"):
            sm.transition_to(ParserState.EXPECT_COLON)


class TestIndentationStack:
    """Test indentation stack management."""

    def test_push_indent(self) -> None:
        """Test pushing indent level."""
        sm = StateMachine()
        sm.push_indent(2)
        assert sm.current_indent == 2
        assert sm.indent_stack == [0, 2]

    def test_push_multiple_indents(self) -> None:
        """Test pushing multiple indent levels."""
        sm = StateMachine()
        sm.push_indent(2)
        sm.push_indent(4)
        assert sm.current_indent == 4
        assert sm.indent_stack == [0, 2, 4]
        assert sm.nesting_depth == 2

    def test_push_invalid_indent_same_level(self) -> None:
        """Test pushing same indent level raises error."""
        sm = StateMachine()
        sm.push_indent(2)
        with pytest.raises(TOONDecodeError, match="must be greater than"):
            sm.push_indent(2)

    def test_push_invalid_indent_less_than_current(self) -> None:
        """Test pushing smaller indent level raises error."""
        sm = StateMachine()
        sm.push_indent(4)
        with pytest.raises(TOONDecodeError, match="must be greater than"):
            sm.push_indent(2)

    def test_pop_indent(self) -> None:
        """Test popping indent level."""
        sm = StateMachine()
        sm.push_indent(2)
        popped = sm.pop_indent()
        assert popped == 2
        assert sm.current_indent == 0
        assert sm.indent_stack == [0]

    def test_pop_multiple_indents(self) -> None:
        """Test popping multiple indent levels."""
        sm = StateMachine()
        sm.push_indent(2)
        sm.push_indent(4)
        sm.push_indent(6)
        sm.pop_indent()
        assert sm.current_indent == 4
        sm.pop_indent()
        assert sm.current_indent == 2
        sm.pop_indent()
        assert sm.current_indent == 0

    def test_pop_base_indent_raises_error(self) -> None:
        """Test popping base indent level raises error."""
        sm = StateMachine()
        with pytest.raises(TOONDecodeError, match="Cannot pop base indentation"):
            sm.pop_indent()

    def test_nesting_depth(self) -> None:
        """Test nesting depth calculation."""
        sm = StateMachine()
        assert sm.nesting_depth == 0
        sm.push_indent(2)
        assert sm.nesting_depth == 1
        sm.push_indent(4)
        assert sm.nesting_depth == 2
        sm.pop_indent()
        assert sm.nesting_depth == 1


class TestDedentDetection:
    """Test dedentation detection logic."""

    def test_no_dedent_at_current_level(self) -> None:
        """Test no dedent when at current level."""
        sm = StateMachine()
        sm.push_indent(2)
        levels = sm.check_dedent(2)
        assert levels == 0

    def test_dedent_one_level(self) -> None:
        """Test dedenting one level."""
        sm = StateMachine()
        sm.push_indent(2)
        sm.push_indent(4)
        levels = sm.check_dedent(2)
        assert levels == 1

    def test_dedent_multiple_levels(self) -> None:
        """Test dedenting multiple levels."""
        sm = StateMachine()
        sm.push_indent(2)
        sm.push_indent(4)
        sm.push_indent(6)
        levels = sm.check_dedent(2)
        assert levels == 2

    def test_dedent_to_base(self) -> None:
        """Test dedenting to base level."""
        sm = StateMachine()
        sm.push_indent(2)
        sm.push_indent(4)
        levels = sm.check_dedent(0)
        assert levels == 2

    def test_invalid_negative_indent(self) -> None:
        """Test negative indentation raises error."""
        sm = StateMachine()
        with pytest.raises(TOONDecodeError, match="Invalid negative indentation"):
            sm.check_dedent(-1)

    def test_invalid_indent_not_in_stack(self) -> None:
        """Test indent not in stack raises error when dedenting."""
        sm = StateMachine()
        sm.push_indent(2)
        sm.push_indent(4)
        # Indent 3 is between 2 and 4, should raise error when dedenting
        with pytest.raises(TOONDecodeError, match="Invalid indentation"):
            sm.check_dedent(1)  # 1 is not 0 or 2, so invalid

    def test_valid_new_indent_not_dedent(self) -> None:
        """Test that higher indent is treated as potential new nesting."""
        sm = StateMachine()
        sm.push_indent(2)
        # 6 is greater than 2, so it's a valid new nesting level, not dedent
        levels = sm.check_dedent(6)
        assert levels == 0


class TestIndentConsistency:
    """Test indentation consistency validation."""

    def test_valid_indent_multiple_of_size(self) -> None:
        """Test valid indent that's multiple of indent_size."""
        sm = StateMachine(indent_size=2)
        sm.validate_indent_consistency(0)  # OK
        sm.validate_indent_consistency(2)  # OK
        sm.validate_indent_consistency(4)  # OK
        sm.validate_indent_consistency(100)  # OK

    def test_invalid_indent_not_multiple(self) -> None:
        """Test invalid indent that's not multiple of indent_size."""
        sm = StateMachine(indent_size=2)
        with pytest.raises(TOONDecodeError, match="not a multiple of 2"):
            sm.validate_indent_consistency(3)

    def test_indent_consistency_size_4(self) -> None:
        """Test indent consistency with size 4."""
        sm = StateMachine(indent_size=4)
        sm.validate_indent_consistency(0)
        sm.validate_indent_consistency(4)
        sm.validate_indent_consistency(8)
        with pytest.raises(TOONDecodeError, match="not a multiple of 4"):
            sm.validate_indent_consistency(6)


class TestContextStack:
    """Test context stack management."""

    def test_push_object_context(self) -> None:
        """Test pushing object context."""
        sm = StateMachine()
        sm.push_context("object")
        assert sm.context_stack == ["object"]
        assert sm.current_context() == "object"

    def test_push_array_context(self) -> None:
        """Test pushing array context."""
        sm = StateMachine()
        sm.push_context("array")
        assert sm.context_stack == ["array"]
        assert sm.current_context() == "array"

    def test_push_multiple_contexts(self) -> None:
        """Test pushing multiple contexts."""
        sm = StateMachine()
        sm.push_context("object")
        sm.push_context("array")
        sm.push_context("object")
        assert sm.context_stack == ["object", "array", "object"]

    def test_pop_context(self) -> None:
        """Test popping context."""
        sm = StateMachine()
        sm.push_context("object")
        sm.push_context("array")
        ctx = sm.pop_context()
        assert ctx == "array"
        assert sm.current_context() == "object"

    def test_pop_empty_context_stack(self) -> None:
        """Test popping from empty context stack raises error."""
        sm = StateMachine()
        with pytest.raises(TOONDecodeError, match="Cannot pop from empty context"):
            sm.pop_context()

    def test_current_context_empty(self) -> None:
        """Test current context when stack is empty."""
        sm = StateMachine()
        assert sm.current_context() is None

    def test_context_stack_copy(self) -> None:
        """Test that context_stack returns a copy."""
        sm = StateMachine()
        sm.push_context("object")
        stack = sm.context_stack
        stack.append("array")  # Modify the copy
        # Original should be unchanged
        assert sm.context_stack == ["object"]


class TestReset:
    """Test state machine reset functionality."""

    def test_reset_state(self) -> None:
        """Test that reset restores initial state."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.reset()
        assert sm.state == ParserState.INITIAL

    def test_reset_indent_stack(self) -> None:
        """Test that reset clears indent stack."""
        sm = StateMachine()
        sm.push_indent(2)
        sm.push_indent(4)
        sm.reset()
        assert sm.indent_stack == [0]
        assert sm.current_indent == 0

    def test_reset_context_stack(self) -> None:
        """Test that reset clears context stack."""
        sm = StateMachine()
        sm.push_context("object")
        sm.push_context("array")
        sm.reset()
        assert sm.context_stack == []

    def test_reset_full(self) -> None:
        """Test full reset of all state."""
        sm = StateMachine()
        sm.transition_to(ParserState.EXPECT_KEY)
        sm.push_indent(2)
        sm.push_context("object")
        sm.reset()
        assert sm.state == ParserState.INITIAL
        assert sm.indent_stack == [0]
        assert sm.context_stack == []
        assert sm.nesting_depth == 0


class TestRepr:
    """Test string representation."""

    def test_repr_initial_state(self) -> None:
        """Test repr for initial state."""
        sm = StateMachine()
        r = repr(sm)
        assert "state=INITIAL" in r
        assert "indent=0" in r
        assert "depth=0" in r

    def test_repr_with_context(self) -> None:
        """Test repr with context information."""
        sm = StateMachine()
        sm.push_context("object")
        sm.push_indent(2)
        sm.transition_to(ParserState.EXPECT_KEY)
        r = repr(sm)
        assert "state=EXPECT_KEY" in r
        assert "indent=2" in r
        assert "depth=1" in r
        assert "object" in r


class TestParserStateEnum:
    """Test ParserState enum."""

    def test_all_states_defined(self) -> None:
        """Test that all expected states are defined."""
        expected_states = {
            "INITIAL",
            "EXPECT_KEY",
            "EXPECT_COLON",
            "EXPECT_VALUE",
            "IN_ARRAY_TABULAR",
            "IN_ARRAY_INLINE",
            "IN_ARRAY_LIST",
            "IN_NESTED_OBJECT",
            "COMPLETE",
            "ERROR",
        }
        actual_states = {s.name for s in ParserState}
        assert actual_states == expected_states

    def test_state_comparison(self) -> None:
        """Test state comparison."""
        assert ParserState.INITIAL != ParserState.EXPECT_KEY
        assert ParserState.INITIAL == ParserState.INITIAL

    def test_state_name(self) -> None:
        """Test state name attribute."""
        assert ParserState.INITIAL.name == "INITIAL"
        assert ParserState.EXPECT_KEY.name == "EXPECT_KEY"
