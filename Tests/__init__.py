"""
Unit tests for WinCopies root package (WinCopies/__init__.py).
"""

import unittest

from WinCopies import (
    BooleanableEnum, NullableBoolean,
    IDisposable,
    IStringable,
    Endianness, Sign, BitDepthLevel,
    ToNullableBool, ToNullableBoolean,
    Not,
    TryConvertToInt
)

# ---------------------------------------------------------------------------
# Concrete helpers for abstract classes
# ---------------------------------------------------------------------------

class _BooleanableValue(BooleanableEnum):
    Negative = -1
    Zero = 0
    Positive = 1

class _ConcreteDisposable(IDisposable):
    def __init__(self) -> None:
        super().__init__()

        self.__initialized = False
        self.__disposed = False
    
    def IsInitialized(self) -> bool: return self.__initialized
    def IsDisposed(self) -> bool: return self.__disposed

    def Initialize(self) -> None: self.__initialized = True
    def Dispose(self) -> None: self.__disposed = True

class _ConcreteStringable(IStringable):
    def __init__(self, value: str) -> None:
        super().__init__()

        self.__value = value

    def ToString(self) -> str: return self.__value

# ---------------------------------------------------------------------------
# BooleanableEnum
# ---------------------------------------------------------------------------

class TestBooleanableEnum(unittest.TestCase):
    """Tests for BooleanableEnum.__bool__."""

    def test_negative_value_is_falsy(self) -> None:
        """A BooleanableEnum member with a negative value is falsy."""
        
        self.assertFalse(bool(_BooleanableValue.Negative))

    def test_zero_value_is_truthy(self) -> None:
        """A BooleanableEnum member with value 0 is truthy (0 >= 0)."""

        self.assertTrue(bool(_BooleanableValue.Zero))

    def test_positive_value_is_truthy(self) -> None:
        """A BooleanableEnum member with a positive value is truthy."""

        self.assertTrue(bool(_BooleanableValue.Positive))

# ---------------------------------------------------------------------------
# NullableBoolean
# ---------------------------------------------------------------------------

class TestNullableBoolean(unittest.TestCase):
    """Tests for NullableBoolean values, truthiness, Not(), and NullableNot()."""

    def test_values(self) -> None:
        """NullableBoolean members have the expected integer values."""

        self.assertEqual(NullableBoolean.BoolFalse.value, -1)
        self.assertEqual(NullableBoolean.Null.value, 0)
        self.assertEqual(NullableBoolean.BoolTrue.value, 1)

    def test_bool_false_is_falsy(self) -> None:
        """NullableBoolean.BoolFalse is falsy (value -1 < 0)."""

        self.assertFalse(bool(NullableBoolean.BoolFalse))

    def test_null_is_truthy(self) -> None:
        """NullableBoolean.Null is truthy (value 0 >= 0)."""

        self.assertTrue(bool(NullableBoolean.Null))

    def test_bool_true_is_truthy(self) -> None:
        """NullableBoolean.BoolTrue is truthy (value 1 >= 0)."""

        self.assertTrue(bool(NullableBoolean.BoolTrue))

    # Not()

    def test_not_bool_false_returns_bool_true(self) -> None:
        """Not() on BoolFalse (falsy) returns BoolTrue."""

        self.assertIs(NullableBoolean.BoolFalse.Not(), NullableBoolean.BoolTrue)

    def test_not_bool_true_returns_bool_false(self) -> None:
        """Not() on BoolTrue (truthy) returns BoolFalse."""

        self.assertIs(NullableBoolean.BoolTrue.Not(), NullableBoolean.BoolFalse)

    def test_not_null_returns_bool_false(self) -> None:
        """Not() on Null (truthy) returns BoolFalse."""

        self.assertIs(NullableBoolean.Null.Not(), NullableBoolean.BoolFalse)

    # NullableNot()

    def test_nullable_not_null_returns_null(self) -> None:
        """NullableNot() on Null returns Null (preserves the null state)."""

        self.assertIs(NullableBoolean.Null.NullableNot(), NullableBoolean.Null)

    def test_nullable_not_bool_false_returns_bool_true(self) -> None:
        """NullableNot() on BoolFalse returns BoolTrue."""

        self.assertIs(NullableBoolean.BoolFalse.NullableNot(), NullableBoolean.BoolTrue)

    def test_nullable_not_bool_true_returns_bool_false(self) -> None:
        """NullableNot() on BoolTrue returns BoolFalse."""

        self.assertIs(NullableBoolean.BoolTrue.NullableNot(), NullableBoolean.BoolFalse)

# ---------------------------------------------------------------------------
# ToNullableBool / ToNullableBoolean
# ---------------------------------------------------------------------------

class TestToNullableBool(unittest.TestCase):
    """Tests for ToNullableBool."""

    def test_null_returns_none(self) -> None:
        """ToNullableBool converts NullableBoolean.Null to None."""

        self.assertIsNone(ToNullableBool(NullableBoolean.Null))

    def test_bool_false_returns_false(self) -> None:
        """ToNullableBool converts NullableBoolean.BoolFalse to False."""

        self.assertIs(ToNullableBool(NullableBoolean.BoolFalse), False)

    def test_bool_true_returns_true(self) -> None:
        """ToNullableBool converts NullableBoolean.BoolTrue to True."""

        self.assertIs(ToNullableBool(NullableBoolean.BoolTrue), True)

class TestToNullableBoolean(unittest.TestCase):
    """Tests for ToNullableBoolean."""

    def test_true_returns_bool_true(self) -> None:
        """ToNullableBoolean converts True to NullableBoolean.BoolTrue."""

        self.assertIs(ToNullableBoolean(True), NullableBoolean.BoolTrue)

    def test_false_returns_bool_false(self) -> None:
        """ToNullableBoolean converts False to NullableBoolean.BoolFalse."""

        self.assertIs(ToNullableBoolean(False), NullableBoolean.BoolFalse)

    def test_none_returns_null(self) -> None:
        """ToNullableBoolean converts None to NullableBoolean.Null."""

        self.assertIs(ToNullableBoolean(None), NullableBoolean.Null)

class TestRoundTrip(unittest.TestCase):
    """Tests for the round-trip consistency between ToNullableBool and ToNullableBoolean."""

    def test_round_trip_from_nullable_boolean(self) -> None:
        """ToNullableBoolean(ToNullableBool(x)) == x for all NullableBoolean members."""

        for member in NullableBoolean:
            self.assertIs(ToNullableBoolean(ToNullableBool(member)), member)

    def test_round_trip_from_nullable_bool(self) -> None:
        """ToNullableBool(ToNullableBoolean(x)) == x for True, False, and None."""

        for value in (True, False, None):
            self.assertEqual(ToNullableBool(ToNullableBoolean(value)), value)

# ---------------------------------------------------------------------------
# Not
# ---------------------------------------------------------------------------

class TestNot(unittest.TestCase):
    """Tests for the Not(value: bool|None) -> bool|None function."""

    def test_not_true_returns_false(self) -> None:
        """Not(True) returns False."""

        self.assertIs(Not(True), False)

    def test_not_false_returns_true(self) -> None:
        """Not(False) returns True."""

        self.assertIs(Not(False), True)

    def test_not_none_returns_none(self) -> None:
        """Not(None) returns None."""

        self.assertIsNone(Not(None))

# ---------------------------------------------------------------------------
# TryConvertToInt
# ---------------------------------------------------------------------------

class TestTryConvertToInt(unittest.TestCase):
    """Tests for TryConvertToInt."""

    def test_int_returns_self(self) -> None:
        """TryConvertToInt passes an int through unchanged."""

        self.assertEqual(TryConvertToInt(42), 42)
        self.assertEqual(TryConvertToInt(0), 0)
        self.assertEqual(TryConvertToInt(-7), -7)

    def test_numeric_string_returns_int(self) -> None:
        """TryConvertToInt converts a numeric string to int."""

        self.assertEqual(TryConvertToInt("123"), 123)
        self.assertEqual(TryConvertToInt("-5"), -5)

    def test_float_returns_truncated_int(self) -> None:
        """TryConvertToInt truncates a float to int."""

        self.assertEqual(TryConvertToInt(3.9), 3)
        self.assertEqual(TryConvertToInt(-2.7), -2)

    def test_non_numeric_string_returns_none(self) -> None:
        """TryConvertToInt returns None for a non-numeric string."""

        self.assertIsNone(TryConvertToInt("abc"))
        self.assertIsNone(TryConvertToInt(""))

    def test_float_string_returns_none(self) -> None:
        """TryConvertToInt returns None for a float string (int() rejects '3.7')."""

        self.assertIsNone(TryConvertToInt("3.7"))

# ---------------------------------------------------------------------------
# IDisposable
# ---------------------------------------------------------------------------

class TestIDisposable(unittest.TestCase):
    """Tests for IDisposable.__enter__ and __exit__ (context manager protocol)."""

    def test_enter_calls_initialize_and_returns_self(self) -> None:
        """__enter__ calls Initialize() and returns the disposable object itself."""

        obj = _ConcreteDisposable()

        result = obj.__enter__()

        self.assertIs(result, obj)
        self.assertTrue(obj.IsInitialized())

    def test_exit_calls_dispose(self) -> None:
        """__exit__ calls Dispose() and returns False."""

        obj = _ConcreteDisposable()

        result = obj.__exit__(None, None, None)

        self.assertTrue(obj.IsDisposed())
        self.assertIs(result, False)

    def test_context_manager_protocol(self) -> None:
        """The with statement calls Initialize() on entry and Dispose() on exit."""

        obj = _ConcreteDisposable()

        with obj:
            self.assertTrue(obj.IsInitialized())
            self.assertFalse(obj.IsDisposed())

        self.assertTrue(obj.IsDisposed())

    def test_exit_called_on_exception(self) -> None:
        """Dispose() is called even when an exception is raised inside the with block."""

        obj = _ConcreteDisposable()

        try:
            with obj: raise RuntimeError("test error")
        except RuntimeError: pass

        self.assertTrue(obj.IsDisposed())

# ---------------------------------------------------------------------------
# IStringable
# ---------------------------------------------------------------------------

class TestIStringable(unittest.TestCase):
    """Tests for IStringable.__str__ delegating to ToString()."""

    def test_str_returns_to_string_result(self) -> None:
        """str() on an IStringable returns whatever ToString() returns."""

        obj = _ConcreteStringable("hello world")

        self.assertEqual(str(obj), "hello world")

    def test_str_with_empty_string(self) -> None:
        """str() returns an empty string when ToString() returns one."""

        self.assertEqual(str(_ConcreteStringable("")), "")

# ---------------------------------------------------------------------------
# Simple enums
# ---------------------------------------------------------------------------

class TestEndianness(unittest.TestCase):
    """Tests for the Endianness enum values."""

    def test_values(self) -> None:
        """Endianness members have the expected integer values."""

        self.assertEqual(Endianness.Null.value, 0)
        self.assertEqual(Endianness.Little.value, 1)
        self.assertEqual(Endianness.Big.value, 2)

    def test_member_count(self) -> None:
        """Endianness has exactly three members."""

        self.assertEqual(len(list(Endianness)), 3)

class TestSign(unittest.TestCase):
    """Tests for the Sign enum values."""

    def test_values(self) -> None:
        """Sign members have the expected integer values."""

        self.assertEqual(Sign.Signed.value, 1)
        self.assertEqual(Sign.Unsigned.value, 2)
        self.assertEqual(Sign.Float.value, 3)

    def test_member_count(self) -> None:
        """Sign has exactly three members."""

        self.assertEqual(len(list(Sign)), 3)

class TestBitDepthLevel(unittest.TestCase):
    """Tests for the BitDepthLevel enum values."""

    def test_values(self) -> None:
        """BitDepthLevel members represent bit widths as multiples of 8."""

        self.assertEqual(BitDepthLevel.One.value, 8)
        self.assertEqual(BitDepthLevel.Two.value, 16)
        self.assertEqual(BitDepthLevel.Three.value, 32)
        self.assertEqual(BitDepthLevel.Four.value, 64)

    def test_member_count(self) -> None:
        """BitDepthLevel has exactly four members."""

        self.assertEqual(len(list(BitDepthLevel)), 4)

if __name__ == '__main__':
    unittest.main()