"""
Unit tests for WinCopies.Assertion module.
"""

import unittest
from enum import Enum, Flag

from WinCopies.Assertion import (
    GetAssertionError,
    Throw,
    EnsureFalse, EnsureTrue, TryEnsureFalse, TryEnsureTrue,
    EnsureNone, EnsureValue,
    EnsureSubclass,
    EnsureEnum, EnsureFlagEnum
)

class _SampleEnum(Enum):
    A = 1
    B = 2

class _SampleFlag(Flag):
    Read = 1
    Write = 2

class TestGetAssertionError(unittest.TestCase):
    """Tests for GetAssertionError."""

    def test_default_message(self) -> None:
        """GetAssertionError with no argument uses the default message."""

        error = GetAssertionError()

        self.assertIsInstance(error, AssertionError)
        self.assertEqual(str(error), "Invalid operation.")

    def test_custom_message(self) -> None:
        """GetAssertionError with a custom message stores that message."""

        error = GetAssertionError("custom error")

        self.assertIsInstance(error, AssertionError)
        self.assertEqual(str(error), "custom error")

    def test_none_message(self) -> None:
        """GetAssertionError with None as message stores None."""

        error = GetAssertionError(None)

        self.assertIsInstance(error, AssertionError)

class TestThrow(unittest.TestCase):
    """Tests for Throw."""

    def test_always_raises(self) -> None:
        """Throw always raises AssertionError."""
        with self.assertRaises(AssertionError): Throw()

    def test_raises_with_custom_message(self) -> None:
        """Throw raises AssertionError with the provided message."""

        with self.assertRaises(AssertionError) as ctx: Throw("something went wrong")

        self.assertEqual(str(ctx.exception), "something went wrong")

    def test_raises_with_none_message(self) -> None:
        """Throw raises AssertionError even with None as message."""

        with self.assertRaises(AssertionError): Throw(None)

class TestEnsureFalse(unittest.TestCase):
    """Tests for EnsureFalse and TryEnsureFalse."""

    # EnsureFalse

    def test_ensure_false_with_false_does_not_raise(self) -> None:
        """EnsureFalse does not raise when condition is False."""

        EnsureFalse(False)

    def test_ensure_false_with_true_raises_assertion(self) -> None:
        """EnsureFalse raises AssertionError when condition is True."""
        
        with self.assertRaises(AssertionError): EnsureFalse(True)

    def test_ensure_false_with_true_uses_custom_message(self) -> None:
        """EnsureFalse uses the provided message in the AssertionError."""

        with self.assertRaises(AssertionError) as ctx: EnsureFalse(True, "must be false")

        self.assertEqual(str(ctx.exception), "must be false")

    def test_ensure_false_with_non_bool_raises_value_error(self) -> None:
        """EnsureFalse raises ValueError when condition is not a boolean."""

        with self.assertRaises(ValueError): EnsureFalse("not a bool") # type: ignore

    # TryEnsureFalse

    def test_try_ensure_false_with_false_returns_true(self) -> None:
        """TryEnsureFalse returns True when condition is a valid False boolean."""

        self.assertTrue(TryEnsureFalse(False))

    def test_try_ensure_false_with_true_raises_assertion(self) -> None:
        """TryEnsureFalse raises AssertionError when condition is True."""

        with self.assertRaises(AssertionError): TryEnsureFalse(True)

    def test_try_ensure_false_with_non_bool_returns_false(self) -> None:
        """TryEnsureFalse returns False (skips validation) when condition is not a boolean."""

        self.assertFalse(TryEnsureFalse("not a bool")) # type: ignore

class TestEnsureTrue(unittest.TestCase):
    """Tests for EnsureTrue and TryEnsureTrue."""

    # EnsureTrue

    def test_ensure_true_with_true_does_not_raise(self) -> None:
        """EnsureTrue does not raise when condition is True."""

        EnsureTrue(True)

    def test_ensure_true_with_false_raises_assertion(self) -> None:
        """EnsureTrue raises AssertionError when condition is False."""

        with self.assertRaises(AssertionError): EnsureTrue(False)

    def test_ensure_true_with_false_uses_custom_message(self) -> None:
        """EnsureTrue uses the provided message in the AssertionError."""

        with self.assertRaises(AssertionError) as ctx: EnsureTrue(False, "must be true")

        self.assertEqual(str(ctx.exception), "must be true")

    def test_ensure_true_with_non_bool_raises_value_error(self) -> None:
        """EnsureTrue raises ValueError when condition is not a boolean."""

        with self.assertRaises(ValueError): EnsureTrue(42) # type: ignore[arg-type]

    # TryEnsureTrue

    def test_try_ensure_true_with_true_returns_true(self) -> None:
        """TryEnsureTrue returns True when condition is a valid True boolean."""

        self.assertTrue(TryEnsureTrue(True))

    def test_try_ensure_true_with_false_raises_assertion(self) -> None:
        """TryEnsureTrue raises AssertionError when condition is False."""

        with self.assertRaises(AssertionError): TryEnsureTrue(False)

    def test_try_ensure_true_with_non_bool_returns_false(self) -> None:
        """TryEnsureTrue returns False (skips validation) when condition is not a boolean."""

        self.assertFalse(TryEnsureTrue(0)) # type: ignore[arg-type]

class TestEnsureNone(unittest.TestCase):
    """Tests for EnsureNone."""

    def test_none_does_not_raise(self) -> None:
        """EnsureNone does not raise when value is None."""
        
        EnsureNone(None)

    def test_non_none_raises_assertion(self) -> None:
        """EnsureNone raises AssertionError when value is not None."""
        
        with self.assertRaises(AssertionError): EnsureNone("something")

    def test_zero_raises_assertion(self) -> None:
        """EnsureNone raises AssertionError for falsy non-None values like 0."""
        
        with self.assertRaises(AssertionError): EnsureNone(0)

    def test_custom_message(self) -> None:
        """EnsureNone includes the custom message in the AssertionError."""

        with self.assertRaises(AssertionError) as ctx: EnsureNone("x", "value must be None here")

        self.assertEqual(str(ctx.exception), "value must be None here")

class TestEnsureValue(unittest.TestCase):
    """Tests for EnsureValue."""

    def test_non_none_does_not_raise(self) -> None:
        """EnsureValue does not raise when value is not None."""

        EnsureValue("something")
        EnsureValue(0)
        EnsureValue(False)

    def test_none_raises_assertion(self) -> None:
        """EnsureValue raises AssertionError when value is None."""
        
        with self.assertRaises(AssertionError): EnsureValue(None)

    def test_custom_message(self) -> None:
        """EnsureValue includes the custom message in the AssertionError."""

        with self.assertRaises(AssertionError) as ctx: EnsureValue(None, "value must not be None here")

        self.assertEqual(str(ctx.exception), "value must not be None here")

class TestEnsureSubclass(unittest.TestCase):
    """Tests for EnsureSubclass."""

    def test_valid_subclass_does_not_raise(self) -> None:
        """EnsureSubclass does not raise when c is a subclass of t."""

        EnsureSubclass(bool, int)    # bool is a subclass of int
        EnsureSubclass(int, object)  # int is a subclass of object
        EnsureSubclass(int, int)     # A class is a subclass of itself

    def test_invalid_subclass_raises_assertion(self) -> None:
        """EnsureSubclass raises AssertionError when c is not a subclass of t."""
        
        with self.assertRaises(AssertionError): EnsureSubclass(str, int)

    def test_unrelated_classes_raise_assertion(self) -> None:
        """EnsureSubclass raises AssertionError for completely unrelated classes."""

        with self.assertRaises(AssertionError): EnsureSubclass(list, dict)

    def test_custom_message(self) -> None:
        """EnsureSubclass includes the custom message in the AssertionError."""

        with self.assertRaises(AssertionError) as ctx: EnsureSubclass(str, int, "str is not a subclass of int")

        self.assertEqual(str(ctx.exception), "str is not a subclass of int")

class TestEnsureEnum(unittest.TestCase):
    """Tests for EnsureEnum and EnsureFlagEnum."""

    # EnsureEnum

    def test_enum_subclass_does_not_raise(self) -> None:
        """EnsureEnum does not raise for a regular Enum subclass."""

        EnsureEnum(_SampleEnum)

    def test_flag_subclass_does_not_raise(self) -> None:
        """EnsureEnum does not raise for a Flag subclass (Flag inherits from Enum)."""
        
        EnsureEnum(_SampleFlag)

    def test_non_enum_raises_assertion(self) -> None:
        """EnsureEnum raises AssertionError for a plain class."""
        
        with self.assertRaises(AssertionError): EnsureEnum(int)

    def test_enum_base_class_itself_does_not_raise(self) -> None:
        """EnsureEnum does not raise for Enum itself (it is a subclass of Enum)."""

        EnsureEnum(Enum)

    # EnsureFlagEnum

    def test_flag_subclass_does_not_raise_flag(self) -> None:
        """EnsureFlagEnum does not raise for a Flag subclass."""
        
        EnsureFlagEnum(_SampleFlag)

    def test_regular_enum_raises_assertion(self) -> None:
        """EnsureFlagEnum raises AssertionError for a regular Enum (not a Flag)."""
        
        with self.assertRaises(AssertionError): EnsureFlagEnum(_SampleEnum)

    def test_non_enum_raises_assertion_flag(self) -> None:
        """EnsureFlagEnum raises AssertionError for a plain class."""

        with self.assertRaises(AssertionError): EnsureFlagEnum(str)

    def test_flag_base_class_itself_does_not_raise(self) -> None:
        """EnsureFlagEnum does not raise for Flag itself."""
        
        EnsureFlagEnum(Flag)

if __name__ == '__main__':
    unittest.main()