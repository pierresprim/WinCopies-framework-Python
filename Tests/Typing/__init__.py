"""
Unit tests for WinCopies.Typing module.
"""

import unittest

from WinCopies.Typing import (
    ErrorBase, Error, InvalidOperationError,
    DiscardReason, IDisposable, IDisposableInfo, DisposableProvider,
    Monitor,
    INullable, GetNullable, GetNullValue, GetNullableValue,
    GetGenericError, GetDiscardedError,
    TryGetValue, HasValue,
    TryGetValueAs, TryGetAs)

# ---------------------------------------------------------------------------
# Concrete helpers
# ---------------------------------------------------------------------------

class _ConcreteDisposable(IDisposable):
    def __init__(self) -> None: super().__init__()

    def Dispose(self) -> None: pass

class _ConcreteDisposableInfo(IDisposableInfo):
    def __init__(self) -> None:
        super().__init__()

        self.__disposed = False

    def GetDiscardReason(self) -> DiscardReason: return DiscardReason.Disposed if self.__disposed else DiscardReason.Null
    def Dispose(self) -> None: self.__disposed = True

def _Throw() -> None: _ConcreteDisposable()._Throw() # pyright: ignore[reportPrivateUsage]


# ---------------------------------------------------------------------------
# ErrorBase / Error / InvalidOperationError
# ---------------------------------------------------------------------------

class TestError(unittest.TestCase):
    """Tests for Error and InvalidOperationError."""

    def test_get_message_returns_message(self) -> None:
        """GetMessage returns the message passed to the constructor."""

        self.assertEqual(Error("something failed").GetMessage(), "something failed")

    def test_str_delegates_to_get_message(self) -> None:
        """str() delegates to GetMessage()."""

        self.assertEqual(str(Error("test message")), "test message")

    def test_invalid_operation_error_is_error(self) -> None:
        """InvalidOperationError is an instance of Error and ErrorBase."""

        error = InvalidOperationError("cannot do this")

        self.assertIsInstance(error, Error)
        self.assertIsInstance(error, ErrorBase)

    def test_invalid_operation_error_get_message(self) -> None:
        """InvalidOperationError.GetMessage() returns the constructor message."""

        self.assertEqual(InvalidOperationError("cannot do this").GetMessage(), "cannot do this")

    def test_error_can_be_raised_and_caught(self) -> None:
        """Error can be raised and caught as an Exception."""

        with self.assertRaises(Error): raise Error("boom")

    def test_invalid_operation_error_can_be_raised_and_caught(self) -> None:
        """InvalidOperationError can be raised and caught as an Exception."""

        with self.assertRaises(InvalidOperationError): raise InvalidOperationError("boom")


# ---------------------------------------------------------------------------
# GetGenericError / GetDiscardedError
# ---------------------------------------------------------------------------

class TestErrorFactories(unittest.TestCase):
    """Tests for GetGenericError and GetDiscardedError."""

    def test_get_generic_error_returns_invalid_operation_error(self) -> None:
        """GetGenericError returns an InvalidOperationError."""

        self.assertIsInstance(GetGenericError(), InvalidOperationError)

    def test_get_generic_error_has_non_empty_message(self) -> None:
        """GetGenericError returns an error with a non-empty message."""

        self.assertGreater(len(GetGenericError().GetMessage()), 0)

    def test_get_disposed_error_returns_invalid_operation_error(self) -> None:
        """GetDiscardedError returns an InvalidOperationError."""

        self.assertIsInstance(GetDiscardedError(), InvalidOperationError)

    def test_get_disposed_error_has_non_empty_message(self) -> None:
        """GetDiscardedError returns an error with a non-empty message."""

        self.assertGreater(len(GetDiscardedError().GetMessage()), 0)


# ---------------------------------------------------------------------------
# IDisposable._Throw
# ---------------------------------------------------------------------------

class TestIDisposableThrow(unittest.TestCase):
    """Tests for IDisposable._Throw()."""

    def test_throw_raises_invalid_operation_error(self) -> None:
        """_Throw raises an InvalidOperationError."""

        with self.assertRaises(InvalidOperationError): _Throw()

    def test_throw_message_mentions_disposed(self) -> None:
        """_Throw raises an error whose message references disposal."""

        try:
            _Throw()
        except InvalidOperationError as e:
            self.assertIn("disposed", e.GetMessage().lower())


# ---------------------------------------------------------------------------
# INullable — via GetNullable
# ---------------------------------------------------------------------------

class TestGetNullable(unittest.TestCase):
    """Tests for GetNullable — wrapping a concrete value."""

    def test_has_value_returns_true(self) -> None:
        """A nullable created with GetNullable reports HasValue as True."""

        self.assertTrue(GetNullable(42).HasValue())

    def test_get_value_returns_wrapped_value(self) -> None:
        """GetValue returns the value passed to GetNullable."""

        self.assertEqual(GetNullable("hello").GetValue(), "hello")

    def test_wrapping_none_is_valid(self) -> None:
        """GetNullable can wrap None as a legitimate value."""

        n = GetNullable(None)

        self.assertTrue(n.HasValue())
        self.assertIsNone(n.GetValue())

    def test_try_get_value_returns_value(self) -> None:
        """TryGetValue returns the wrapped value when HasValue is True."""

        self.assertEqual(GetNullable(7).TryGetValue(), 7)

    def test_try_get_value_or_default_returns_value_not_default(self) -> None:
        """TryGetValueOrDefault returns the value, not the default, when HasValue is True."""

        self.assertEqual(GetNullable(3).TryGetValueOrDefault(99), 3)

    def test_convert_applies_converter(self) -> None:
        """Convert applies the converter function to the wrapped value."""

        self.assertEqual(GetNullable(5).Convert(lambda x: x * 2), 10)

    def test_try_convert_applies_converter_when_has_value(self) -> None:
        """TryConvert applies the converter when HasValue is True."""

        self.assertEqual(GetNullable(4).TryConvert(lambda x: x + 1, default=0), 5)

    def test_convert_to_nullable_wraps_result(self) -> None:
        """ConvertToNullable wraps the converted result in an INullable."""

        result = GetNullable(3).ConvertToNullable(lambda x: x * 10)

        self.assertIsInstance(result, INullable)
        self.assertTrue(result.HasValue())
        self.assertEqual(result.GetValue(), 30)

    def test_try_convert_to_nullable_returns_nullable_with_value(self) -> None:
        """TryConvertToNullable returns a value-bearing INullable when HasValue is True."""

        result = GetNullable(2).TryConvertToNullable(lambda x: str(x))

        self.assertTrue(result.HasValue())
        self.assertEqual(result.GetValue(), "2")


# ---------------------------------------------------------------------------
# INullable — via GetNullValue
# ---------------------------------------------------------------------------

def _GetNullValue() -> INullable[None]: return GetNullValue()

class TestGetNullValue(unittest.TestCase):
    """Tests for GetNullValue — the absent/null nullable."""

    def test_has_value_returns_false(self) -> None:
        """A null value reports HasValue as False."""

        self.assertFalse(GetNullValue().HasValue())

    def test_get_value_raises(self) -> None:
        """GetValue on a null value raises InvalidOperationError."""

        with self.assertRaises(InvalidOperationError): GetNullValue().GetValue()

    def test_try_get_value_returns_none(self) -> None:
        """TryGetValue returns None when HasValue is False."""

        self.assertIsNone(_GetNullValue().TryGetValue())

    def test_try_get_value_or_default_returns_default(self) -> None:
        """TryGetValueOrDefault returns the default when HasValue is False."""

        self.assertEqual(GetNullValue().TryGetValueOrDefault(42), 42)

    def test_try_convert_returns_default(self) -> None:
        """TryConvert returns the provided default when HasValue is False."""

        self.assertEqual(_GetNullValue().TryConvert(lambda x: x, default="fallback"), "fallback")

    def test_try_convert_without_default_returns_none(self) -> None:
        """TryConvert without an explicit default returns None when HasValue is False."""

        self.assertIsNone(_GetNullValue().TryConvert(lambda x: x))

    def test_try_convert_to_nullable_returns_null(self) -> None:
        """TryConvertToNullable returns a null INullable when HasValue is False."""

        self.assertFalse(_GetNullValue().TryConvertToNullable(lambda x: x).HasValue())

    def test_null_value_is_singleton(self) -> None:
        """GetNullValue returns the same singleton instance on every call."""

        self.assertIs(_GetNullValue(), _GetNullValue())


# ---------------------------------------------------------------------------
# Free functions: TryGetValue, GetNullableValue, HasValue
# ---------------------------------------------------------------------------

class TestFreeNullableFunctions(unittest.TestCase):
    """Tests for TryGetValue, GetNullableValue, and HasValue free functions."""

    # TryGetValue

    def test_try_get_value_with_none_argument_returns_none(self) -> None:
        """TryGetValue returns None when passed None (not an INullable)."""

        self.assertIsNone(TryGetValue(None))

    def test_try_get_value_with_nullable_returns_wrapped_value(self) -> None:
        """TryGetValue returns the wrapped value for a non-null INullable."""

        self.assertEqual(TryGetValue(GetNullable("x")), "x")

    def test_try_get_value_with_null_nullable_returns_none(self) -> None:
        """TryGetValue returns None for a null INullable."""

        self.assertIsNone(TryGetValue(GetNullValue()))

    # GetNullableValue

    def test_get_nullable_value_wraps_non_none(self) -> None:
        """GetNullableValue wraps a non-None value in an INullable."""

        result = GetNullableValue(10)

        self.assertTrue(result.HasValue())
        self.assertEqual(result.GetValue(), 10)

    def test_get_nullable_value_with_none_returns_null(self) -> None:
        """GetNullableValue returns a null INullable when passed None."""

        self.assertFalse(GetNullableValue(None).HasValue())

    # HasValue

    def test_has_value_with_none_returns_false(self) -> None:
        """HasValue returns False when passed None."""

        self.assertFalse(HasValue(None))

    def test_has_value_with_nullable_returns_true(self) -> None:
        """HasValue returns True for a non-null INullable."""

        self.assertTrue(HasValue(GetNullable(1)))

    def test_has_value_with_null_value_returns_false(self) -> None:
        """HasValue returns False for a null INullable."""

        self.assertFalse(HasValue(_GetNullValue()))


# ---------------------------------------------------------------------------
# DisposableProvider
# ---------------------------------------------------------------------------

class TestDisposableProvider(unittest.TestCase):
    """Tests for DisposableProvider lifecycle."""

    def test_get_item_returns_wrapped_item(self) -> None:
        """GetItem returns the item passed to the constructor."""

        item = _ConcreteDisposableInfo()
        provider = DisposableProvider(item)

        self.assertIs(provider.GetItem(), item)

    def test_is_not_disposed_initially(self) -> None:
        """IsDisposed returns False before Dispose is called."""

        self.assertFalse(DisposableProvider(_ConcreteDisposableInfo()).IsDisposed())

    def test_dispose_marks_as_disposed(self) -> None:
        """IsDisposed returns True after Dispose is called."""

        provider = DisposableProvider(_ConcreteDisposableInfo())
        provider.Dispose()

        self.assertTrue(provider.IsDisposed())

    def test_get_item_after_dispose_raises(self) -> None:
        """GetItem raises InvalidOperationError after disposal."""

        provider = DisposableProvider(_ConcreteDisposableInfo())
        provider.Dispose()

        with self.assertRaises(InvalidOperationError): provider.GetItem()

    def test_try_get_item_before_dispose_has_value(self) -> None:
        """TryGetItem returns an INullable with HasValue=True before disposal."""

        item = _ConcreteDisposableInfo()
        provider = DisposableProvider(item)
        result = provider.TryGetItem()

        self.assertTrue(result.HasValue())
        self.assertIs(result.GetValue(), item)

    def test_try_get_item_after_dispose_is_null(self) -> None:
        """TryGetItem returns a null INullable after disposal."""

        provider = DisposableProvider(_ConcreteDisposableInfo())
        provider.Dispose()

        self.assertFalse(provider.TryGetItem().HasValue())


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------

class TestMonitor(unittest.TestCase):
    """Tests for Monitor IsBusy state tracking."""

    def test_not_busy_initially(self) -> None:
        """A new Monitor is not busy."""

        self.assertFalse(Monitor().IsBusy())

    def test_busy_after_initialize(self) -> None:
        """IsBusy returns True after Initialize is called."""

        m = Monitor()
        m.Initialize()

        self.assertTrue(m.IsBusy())

    def test_not_busy_after_dispose(self) -> None:
        """IsBusy returns False after Dispose is called."""

        m = Monitor()
        m.Initialize()
        m.Dispose()

        self.assertFalse(m.IsBusy())

    def test_context_manager_sets_and_clears_busy(self) -> None:
        """Using Monitor as a context manager sets IsBusy during the block and clears it on exit."""

        m = Monitor()

        with m:
            self.assertTrue(m.IsBusy())

        self.assertFalse(m.IsBusy())


# ---------------------------------------------------------------------------
# TryGetValueAs / TryGetAs
# ---------------------------------------------------------------------------

class TestTryGetAs(unittest.TestCase):
    """Tests for TryGetValueAs and TryGetAs."""

    def test_try_get_value_as_matching_type_returns_value(self) -> None:
        """TryGetValueAs returns the value when it matches the requested type."""

        self.assertEqual(TryGetValueAs(int, 42, "default"), 42)

    def test_try_get_value_as_non_matching_type_returns_default(self) -> None:
        """TryGetValueAs returns the default when the value is not of the requested type."""

        self.assertEqual(TryGetValueAs(int, "hello", -1), -1)

    def test_try_get_value_as_subclass_succeeds(self) -> None:
        """TryGetValueAs succeeds for subclasses (bool is a subclass of int)."""

        self.assertIs(TryGetValueAs(int, True, None), True)

    def test_try_get_as_matching_type_returns_value(self) -> None:
        """TryGetAs returns the value when it matches the requested type."""

        self.assertEqual(TryGetAs(str, "hello"), "hello")

    def test_try_get_as_non_matching_type_returns_none(self) -> None:
        """TryGetAs returns None when the value does not match the requested type."""

        self.assertIsNone(TryGetAs(int, "not an int"))


if __name__ == '__main__':
    unittest.main()
