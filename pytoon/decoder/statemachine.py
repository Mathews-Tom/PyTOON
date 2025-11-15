"""State machine for TOON parser.

This module provides the StateMachine class that manages parser state
transitions and indentation stack tracking during TOON parsing.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Literal

from pytoon.utils.errors import TOONDecodeError


class ParserState(Enum):
    """Parser state enumeration.

    Defines all possible states the parser can be in during TOON parsing.

    States:
        INITIAL: Starting state, expecting first token
        EXPECT_KEY: Expecting an identifier (key)
        EXPECT_COLON: Expecting ':' after key
        EXPECT_VALUE: Expecting value after ':'
        IN_ARRAY_TABULAR: Parsing tabular array rows
        IN_ARRAY_INLINE: Parsing inline array values
        IN_ARRAY_LIST: Parsing list-style array items
        IN_NESTED_OBJECT: Parsing nested object structure
        COMPLETE: Parsing finished successfully
        ERROR: Parsing encountered error

    Examples:
        >>> state = ParserState.INITIAL
        >>> state.name
        'INITIAL'
        >>> state == ParserState.EXPECT_KEY
        False
    """

    INITIAL = auto()
    EXPECT_KEY = auto()
    EXPECT_COLON = auto()
    EXPECT_VALUE = auto()
    IN_ARRAY_TABULAR = auto()
    IN_ARRAY_INLINE = auto()
    IN_ARRAY_LIST = auto()
    IN_NESTED_OBJECT = auto()
    COMPLETE = auto()
    ERROR = auto()


class StateMachine:
    """Manages parser state transitions and indentation tracking.

    The StateMachine is responsible for:
    - Tracking the current parser state
    - Managing the indentation stack for nested structures
    - Validating state transitions
    - Detecting dedentation to close nested structures

    Args:
        indent_size: Expected indentation size (default: 2)

    Attributes:
        state: Current parser state
        indent_stack: Stack of indentation levels (list of int)
        current_indent: Current indentation level

    Examples:
        >>> sm = StateMachine()
        >>> sm.state
        <ParserState.INITIAL: 1>
        >>> sm.push_indent(2)
        >>> sm.current_indent
        2
        >>> sm.pop_indent()
        2
        >>> sm.current_indent
        0

    Raises:
        TOONDecodeError: On invalid state transitions or indentation errors
    """

    def __init__(self, *, indent_size: int = 2) -> None:
        """Initialize StateMachine with configuration.

        Args:
            indent_size: Expected indentation size (default: 2)

        Raises:
            ValueError: If indent_size is not positive
        """
        if indent_size <= 0:
            raise ValueError(f"indent_size must be positive, got: {indent_size}")

        self._state = ParserState.INITIAL
        self._indent_stack: list[int] = [0]
        self._indent_size = indent_size
        self._context_stack: list[Literal["object", "array"]] = []

    @property
    def state(self) -> ParserState:
        """Get the current parser state."""
        return self._state

    @property
    def indent_stack(self) -> list[int]:
        """Get the current indentation stack.

        Returns a copy to prevent external modification.
        """
        return self._indent_stack.copy()

    @property
    def current_indent(self) -> int:
        """Get the current indentation level."""
        return self._indent_stack[-1]

    @property
    def indent_size(self) -> int:
        """Get the expected indentation size."""
        return self._indent_size

    @property
    def nesting_depth(self) -> int:
        """Get the current nesting depth.

        Returns:
            Number of nested structures (objects/arrays) currently open
        """
        return len(self._indent_stack) - 1

    @property
    def context_stack(self) -> list[Literal["object", "array"]]:
        """Get the current context stack.

        Returns a copy to prevent external modification.
        """
        return self._context_stack.copy()

    def transition_to(self, new_state: ParserState) -> None:
        """Transition to a new parser state.

        Validates that the transition is allowed based on current state.

        Args:
            new_state: The state to transition to

        Raises:
            TOONDecodeError: If transition is not valid

        Examples:
            >>> sm = StateMachine()
            >>> sm.transition_to(ParserState.EXPECT_KEY)
            >>> sm.state
            <ParserState.EXPECT_KEY: 2>
        """
        if not self._is_valid_transition(self._state, new_state):
            raise TOONDecodeError(
                f"Invalid state transition: {self._state.name} -> {new_state.name}"
            )

        self._state = new_state

    def _is_valid_transition(
        self, from_state: ParserState, to_state: ParserState
    ) -> bool:
        """Check if a state transition is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid, False otherwise
        """
        # Define valid transitions
        valid_transitions: dict[ParserState, set[ParserState]] = {
            ParserState.INITIAL: {
                ParserState.EXPECT_KEY,
                ParserState.EXPECT_VALUE,
                ParserState.IN_ARRAY_INLINE,
                ParserState.IN_ARRAY_TABULAR,
                ParserState.IN_ARRAY_LIST,
                ParserState.COMPLETE,
                ParserState.ERROR,
            },
            ParserState.EXPECT_KEY: {
                ParserState.EXPECT_COLON,
                ParserState.COMPLETE,
                ParserState.ERROR,
            },
            ParserState.EXPECT_COLON: {
                ParserState.EXPECT_VALUE,
                ParserState.ERROR,
            },
            ParserState.EXPECT_VALUE: {
                ParserState.EXPECT_KEY,
                ParserState.IN_NESTED_OBJECT,
                ParserState.IN_ARRAY_TABULAR,
                ParserState.IN_ARRAY_INLINE,
                ParserState.IN_ARRAY_LIST,
                ParserState.COMPLETE,
                ParserState.ERROR,
            },
            ParserState.IN_ARRAY_TABULAR: {
                ParserState.EXPECT_KEY,
                ParserState.COMPLETE,
                ParserState.ERROR,
            },
            ParserState.IN_ARRAY_INLINE: {
                ParserState.EXPECT_KEY,
                ParserState.COMPLETE,
                ParserState.ERROR,
            },
            ParserState.IN_ARRAY_LIST: {
                ParserState.EXPECT_KEY,
                ParserState.IN_NESTED_OBJECT,
                ParserState.COMPLETE,
                ParserState.ERROR,
            },
            ParserState.IN_NESTED_OBJECT: {
                ParserState.EXPECT_KEY,
                ParserState.IN_NESTED_OBJECT,
                ParserState.IN_ARRAY_TABULAR,
                ParserState.IN_ARRAY_INLINE,
                ParserState.IN_ARRAY_LIST,
                ParserState.COMPLETE,
                ParserState.ERROR,
            },
            ParserState.COMPLETE: set(),  # No transitions from COMPLETE
            ParserState.ERROR: set(),  # No transitions from ERROR
        }

        allowed = valid_transitions.get(from_state, set())
        return to_state in allowed

    def push_indent(self, indent_level: int) -> None:
        """Push a new indentation level onto the stack.

        Args:
            indent_level: The indentation level to push

        Raises:
            TOONDecodeError: If indent level is not greater than current

        Examples:
            >>> sm = StateMachine()
            >>> sm.push_indent(2)
            >>> sm.current_indent
            2
            >>> sm.push_indent(4)
            >>> sm.current_indent
            4
        """
        if indent_level <= self.current_indent:
            raise TOONDecodeError(
                f"New indent {indent_level} must be greater than "
                f"current indent {self.current_indent}"
            )

        self._indent_stack.append(indent_level)

    def pop_indent(self) -> int:
        """Pop the current indentation level from the stack.

        Returns:
            The popped indentation level

        Raises:
            TOONDecodeError: If stack would become empty

        Examples:
            >>> sm = StateMachine()
            >>> sm.push_indent(2)
            >>> sm.pop_indent()
            2
            >>> sm.current_indent
            0
        """
        if len(self._indent_stack) <= 1:
            raise TOONDecodeError("Cannot pop base indentation level")

        return self._indent_stack.pop()

    def check_dedent(self, indent_level: int) -> int:
        """Check if given indent level indicates dedentation.

        Determines how many levels to close based on the indent level.

        Args:
            indent_level: The indentation level to check

        Returns:
            Number of levels to close (0 if no dedent)

        Raises:
            TOONDecodeError: If indent level is invalid

        Examples:
            >>> sm = StateMachine()
            >>> sm.push_indent(2)
            >>> sm.push_indent(4)
            >>> sm.check_dedent(2)  # Going back to indent 2
            1
            >>> sm.check_dedent(4)  # Still at current level
            0
            >>> sm.check_dedent(0)  # Going back to base
            2
        """
        if indent_level < 0:
            raise TOONDecodeError(f"Invalid negative indentation: {indent_level}")

        # If indent is greater than or equal to current, no dedent
        if indent_level >= self.current_indent:
            return 0

        # Dedenting - indent must exactly match a level in the stack
        if indent_level not in self._indent_stack:
            raise TOONDecodeError(
                f"Invalid indentation: {indent_level}, "
                f"must match a level in stack {self._indent_stack}"
            )

        # Count how many levels we need to close
        levels_to_close = 0
        for i in range(len(self._indent_stack) - 1, -1, -1):
            if self._indent_stack[i] == indent_level:
                break
            levels_to_close += 1

        return levels_to_close

    def validate_indent_consistency(self, indent_level: int) -> None:
        """Validate that indent level is consistent with indent_size.

        Args:
            indent_level: The indentation level to validate

        Raises:
            TOONDecodeError: If indent is not a multiple of indent_size

        Examples:
            >>> sm = StateMachine(indent_size=2)
            >>> sm.validate_indent_consistency(4)  # OK: 4 is multiple of 2
            >>> sm.validate_indent_consistency(3)  # Error: 3 is not multiple of 2
            Traceback (most recent call last):
                ...
            pytoon.utils.errors.TOONDecodeError: Indentation 3 is not a multiple of 2
        """
        if indent_level % self._indent_size != 0:
            raise TOONDecodeError(
                f"Indentation {indent_level} is not a multiple of {self._indent_size}"
            )

    def push_context(self, context_type: Literal["object", "array"]) -> None:
        """Push a new parsing context onto the context stack.

        Args:
            context_type: Type of context ('object' or 'array')

        Examples:
            >>> sm = StateMachine()
            >>> sm.push_context("object")
            >>> sm.context_stack
            ['object']
            >>> sm.push_context("array")
            >>> sm.context_stack
            ['object', 'array']
        """
        self._context_stack.append(context_type)

    def pop_context(self) -> Literal["object", "array"]:
        """Pop the current parsing context from the stack.

        Returns:
            The popped context type

        Raises:
            TOONDecodeError: If context stack is empty

        Examples:
            >>> sm = StateMachine()
            >>> sm.push_context("object")
            >>> sm.pop_context()
            'object'
        """
        if not self._context_stack:
            raise TOONDecodeError("Cannot pop from empty context stack")

        return self._context_stack.pop()

    def current_context(self) -> Literal["object", "array"] | None:
        """Get the current parsing context.

        Returns:
            Current context type, or None if context stack is empty

        Examples:
            >>> sm = StateMachine()
            >>> sm.current_context() is None
            True
            >>> sm.push_context("array")
            >>> sm.current_context()
            'array'
        """
        if not self._context_stack:
            return None
        return self._context_stack[-1]

    def reset(self) -> None:
        """Reset the state machine to initial state.

        Clears all stacks and resets state to INITIAL.

        Examples:
            >>> sm = StateMachine()
            >>> sm.transition_to(ParserState.EXPECT_KEY)
            >>> sm.push_indent(2)
            >>> sm.push_context("object")
            >>> sm.reset()
            >>> sm.state
            <ParserState.INITIAL: 1>
            >>> sm.current_indent
            0
            >>> sm.context_stack
            []
        """
        self._state = ParserState.INITIAL
        self._indent_stack = [0]
        self._context_stack = []

    def __repr__(self) -> str:
        """Return string representation of state machine.

        Returns:
            String describing current state and configuration
        """
        return (
            f"StateMachine(state={self._state.name}, "
            f"indent={self.current_indent}, "
            f"depth={self.nesting_depth}, "
            f"context={self.current_context()})"
        )
