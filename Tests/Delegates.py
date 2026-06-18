"""
Unit tests for WinCopies.Delegates module.
"""

import unittest

from WinCopies.Delegates import (
    Self,
    BoolTrue, BoolFalse, FuncNone, DoNothing,
    CompareEquality,
    PredicateAction, GetPredicateAction,
    BoolFuncAction, GetBoolFuncAction,
    ExecuteActions, ConcatenateActions,
    ExecuteMethods, ConcatenateMethods, JoinMethods,
    RepeatAndAlso, GetRepeatAndAlso,
    RepeatAnd, GetRepeatAnd,
    RepeatOrElse, GetRepeatOrElse,
    RepeatOr, GetRepeatOr,
    PredicateAndAlso, GetAndAlsoPredicate,
    PredicateAnd, GetAndPredicate,
    PredicateOrElse, GetOrElsePredicate,
    PredicateOr, GetOrPredicate,
    PredicateNotAndAlso, GetNotAndAlsoPredicate,
    PredicateNotAnd, GetNotAndPredicate,
    PredicateNot, GetNotPredicate,
    FuncAndAlso, GetAndAlsoFunc,
    FuncAnd, GetAndFunc,
    FuncOrElse, GetOrElseFunc,
    FuncOr, GetOrFunc,
    FuncNotAndAlso, GetNotAndAlsoFunc,
    FuncNotAnd, GetNotAndFunc,
    FuncNot, GetNotFunc,
    GetEqualityComparison,
    GetIndexedValueIndexComparison,
    GetIndexedValueValueComparison,
    GetIndexedValueComparison,
    GetSelectedEqualityComparison,
    TryGetSelectedEqualityComparison
)
from WinCopies.Typing.Delegate import EqualityComparison, Function, IndexedValueComparison, Method, Predicate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _counter(return_value: bool = True) -> tuple[Function[bool], Function[int]]:
    """Returns a (func, calls) pair where calls counts invocations."""

    calls: int = 0

    def func() -> bool:
        nonlocal calls

        calls += 1

        return return_value

    return func, lambda: calls

def _predicate_counter(return_value: bool = True) -> tuple[Predicate[object], Function[int]]:
    """Returns a (predicate, calls) pair where calls[0] counts invocations."""

    calls = 0

    def pred(_: object) -> bool:
        nonlocal calls

        calls += 1

        return return_value

    return pred, lambda: calls

# ---------------------------------------------------------------------------
# Basic delegates
# ---------------------------------------------------------------------------

class TestBasicDelegates(unittest.TestCase):
    """Tests for Self, BoolTrue, BoolFalse, FuncNone, DoNothing, CompareEquality."""

    def test_self_returns_the_value(self) -> None:
        """Self returns the value it receives unchanged."""

        self.assertEqual(Self(42), 42)
        self.assertEqual(Self("hello"), "hello")
        self.assertIsNone(Self(None))

    def test_bool_true(self) -> None:
        """BoolTrue always returns True."""
        
        self.assertTrue(BoolTrue())

    def test_bool_false(self) -> None:
        """BoolFalse always returns False."""
        
        self.assertFalse(BoolFalse())

    def test_func_none(self) -> None:
        """FuncNone always returns None."""
        
        self.assertIsNone(FuncNone()) # type: ignore[func-returns-value]

    def test_do_nothing_returns_none(self) -> None:
        """DoNothing accepts any argument and returns None implicitly."""
        
        self.assertIsNone(DoNothing(42)) # type: ignore[func-returns-value]
        self.assertIsNone(DoNothing(None)) # type: ignore[func-returns-value]

    def test_compare_equality_equal_values(self) -> None:
        """CompareEquality returns True for equal values."""
        
        self.assertTrue(CompareEquality(1, 1))
        self.assertTrue(CompareEquality("x", "x"))

    def test_compare_equality_unequal_values(self) -> None:
        """CompareEquality returns False for different values."""
        
        self.assertFalse(CompareEquality(1, 2))
        self.assertFalse(CompareEquality("a", "b"))

# ---------------------------------------------------------------------------
# PredicateAction and BoolFuncAction
# ---------------------------------------------------------------------------

class TestPredicateAction(unittest.TestCase):
    """Tests for PredicateAction, GetPredicateAction, BoolFuncAction, GetBoolFuncAction."""

    def test_predicate_action_true_calls_action(self) -> None:
        """PredicateAction calls action and returns True when predicate is satisfied."""
        
        called = False

        def update(_: int) -> None:
            nonlocal called

            called = True

        result = PredicateAction(10, lambda x: x > 5, update)

        self.assertTrue(result)
        self.assertTrue(called)

    def test_predicate_action_false_skips_action(self) -> None:
        """PredicateAction does not call action and returns False when predicate fails."""
        
        called = False

        def update(_: int) -> None:
            nonlocal called

            called = True

        result = PredicateAction(3, lambda x: x > 5, update)

        self.assertFalse(result)
        self.assertFalse(called)

    def test_get_predicate_action_returns_callable(self) -> None:
        """GetPredicateAction returns a predicate that behaves like PredicateAction."""
        
        called = False

        def update(_: int) -> None:
            nonlocal called

            called = True
        
        pred: Predicate[int] = GetPredicateAction(lambda x: x > 5, update)

        self.assertTrue(pred(10))
        self.assertTrue(called)

        called = False
        
        self.assertFalse(pred(3))
        self.assertFalse(called)

    def test_bool_func_action_true_calls_action(self) -> None:
        """BoolFuncAction calls action and returns True when func returns True."""
        
        called = False

        def update() -> None:
            nonlocal called

            called = True

        result = BoolFuncAction(lambda: True, update)

        self.assertTrue(result)
        self.assertTrue(called)

    def test_bool_func_action_false_skips_action(self) -> None:
        """BoolFuncAction does not call action and returns False when func returns False."""
        
        called = False

        def update() -> None:
            nonlocal called

            called = True

        result = BoolFuncAction(lambda: False, update)

        self.assertFalse(result)
        self.assertFalse(called)

    def test_get_bool_func_action_returns_callable(self) -> None:
        """GetBoolFuncAction returns a function that behaves like BoolFuncAction."""
        
        called = False

        def update() -> None:
            nonlocal called

            called = True
        
        func = GetBoolFuncAction(lambda: True, update)

        self.assertTrue(func())
        self.assertTrue(called)

# ---------------------------------------------------------------------------
# Execute / Concatenate
# ---------------------------------------------------------------------------

class TestExecute(unittest.TestCase):
    """Tests for ExecuteActions, ConcatenateActions, ExecuteMethods, ConcatenateMethods, JoinMethods."""

    def test_execute_actions_calls_all(self) -> None:
        """ExecuteActions calls every action in order."""

        log: list[int] = []

        ExecuteActions(lambda: log.append(1), lambda: log.append(2), lambda: log.append(3))

        self.assertEqual(log, [1, 2, 3])

    def test_execute_actions_empty(self) -> None:
        """ExecuteActions with no arguments does nothing."""

        ExecuteActions()  # Should not raise

    def test_concatenate_actions_returns_callable(self) -> None:
        """ConcatenateActions returns an action that calls all sub-actions."""

        log: list[int] = []

        action = ConcatenateActions(lambda: log.append(1), lambda: log.append(2))
        action()

        self.assertEqual(log, [1, 2])

    def test_execute_methods_calls_all_with_arg(self) -> None:
        """ExecuteMethods calls every method with the same argument."""

        results: list[int] = []

        ExecuteMethods(5, lambda x: results.append(x * 1), lambda x: results.append(x * 2))

        self.assertEqual(results, [5, 10])

    def test_concatenate_methods_returns_callable(self) -> None:
        """ConcatenateMethods returns a method that passes arg to all sub-methods."""

        results: list[int] = []

        method: Method[int] = ConcatenateMethods(lambda x: results.append(x), lambda x: results.append(x * 2))
        method(3)

        self.assertEqual(results, [3, 6])

    def test_join_methods_returns_action(self) -> None:
        """JoinMethods returns an argument-free action that binds the arg at creation."""

        results: list[int] = []

        action = JoinMethods(7, lambda x: results.append(x), lambda x: results.append(x + 1))
        action()

        self.assertEqual(results, [7, 8])

# ---------------------------------------------------------------------------
# Repeat functions
# ---------------------------------------------------------------------------

class TestRepeatAndAlso(unittest.TestCase):
    """Tests for RepeatAndAlso and GetRepeatAndAlso (short-circuit AND)."""

    def test_n_less_than_one_raises(self) -> None:
        """RepeatAndAlso raises ValueError for n < 1."""

        with self.assertRaises(ValueError): RepeatAndAlso(0, lambda: True)

    def test_n_one_true(self) -> None:
        """RepeatAndAlso(1, func) returns the result of a single call."""

        self.assertTrue(RepeatAndAlso(1, lambda: True))
        self.assertFalse(RepeatAndAlso(1, lambda: False))

    def test_n_two_both_true(self) -> None:
        """RepeatAndAlso(2, ...) returns True when both calls return True."""
        
        self.assertTrue(RepeatAndAlso(2, lambda: True))

    def test_n_two_first_false_short_circuits(self) -> None:
        """RepeatAndAlso(2, ...) returns False and skips second call when first is False."""
        
        func, calls = _counter(False)

        self.assertFalse(RepeatAndAlso(2, func))
        self.assertEqual(calls(), 1) # Only one call due to short-circuit

    def test_n_two_second_false(self) -> None:
        """RepeatAndAlso(2, ...) returns False when second call is False."""
        
        results = (True, False)
        i: int = 0

        def func() -> bool:
            nonlocal i

            val: bool = results[i]
            i += 1

            return val

        self.assertFalse(RepeatAndAlso(2, func))
        self.assertEqual(i, 2)

    def test_n_three_all_true(self) -> None:
        """RepeatAndAlso(3, ...) returns True when all three calls return True."""

        self.assertTrue(RepeatAndAlso(3, lambda: True))

    def test_n_three_first_false_short_circuits(self) -> None:
        """RepeatAndAlso(3, ...) returns False and does not call beyond the first False."""
        
        func, calls = _counter(False)

        self.assertFalse(RepeatAndAlso(3, func))
        self.assertLess(calls(), 3) # Short-circuit must have occurred

    def test_get_repeat_and_also_matches_direct(self) -> None:
        """GetRepeatAndAlso returns a function producing the same result as RepeatAndAlso."""

        self.assertEqual(GetRepeatAndAlso(2, lambda: True)(), RepeatAndAlso(2, lambda: True))

class TestRepeatAnd(unittest.TestCase):
    """Tests for RepeatAnd and GetRepeatAnd (non-short-circuit AND)."""

    def test_n_less_than_one_raises(self) -> None:
        """RepeatAnd raises ValueError for n < 1."""

        with self.assertRaises(ValueError): RepeatAnd(0, lambda: True)

    def test_n_one(self) -> None:
        """RepeatAnd(1, func) returns the result of a single call."""

        self.assertTrue(RepeatAnd(1, lambda: True))
        self.assertFalse(RepeatAnd(1, lambda: False))

    def test_n_two_all_true(self) -> None:
        """RepeatAnd(2, ...) returns True when both calls return True."""
        
        self.assertTrue(RepeatAnd(2, lambda: True))

    def test_n_two_any_false(self) -> None:
        """RepeatAnd(2, ...) returns False when any call returns False."""
        
        self.assertFalse(RepeatAnd(2, lambda: False))

    def test_n_two_no_short_circuit(self) -> None:
        """RepeatAnd(2, ...) calls func twice even when first returns False."""
        
        func, calls = _counter(False)

        RepeatAnd(2, func)

        self.assertEqual(calls(), 2)  # Both calls must happen

    def test_n_three_all_true(self) -> None:
        """RepeatAnd(3, ...) returns True when all calls return True."""
        
        self.assertTrue(RepeatAnd(3, lambda: True))

    def test_n_three_all_called_even_on_false(self) -> None:
        """RepeatAnd(3, ...) calls func 3 times even if first is False."""
        
        func, calls = _counter(False)

        RepeatAnd(3, func)

        self.assertEqual(calls(), 3)

    def test_get_repeat_and_matches_direct(self) -> None:
        """GetRepeatAnd returns a function producing the same result as RepeatAnd."""

        self.assertEqual(GetRepeatAnd(2, lambda: False)(), RepeatAnd(2, lambda: False))

class TestRepeatOrElse(unittest.TestCase):
    """Tests for RepeatOrElse and GetRepeatOrElse (short-circuit OR)."""

    def test_n_less_than_one_raises(self) -> None:
        """RepeatOrElse raises ValueError for n < 1."""

        with self.assertRaises(ValueError): RepeatOrElse(0, lambda: True)

    def test_n_one(self) -> None:
        """RepeatOrElse(1, func) returns the result of a single call."""

        self.assertTrue(RepeatOrElse(1, lambda: True))
        self.assertFalse(RepeatOrElse(1, lambda: False))

    def test_n_two_any_true(self) -> None:
        """RepeatOrElse(2, ...) returns True when any call returns True."""

        self.assertTrue(RepeatOrElse(2, lambda: True))

    def test_n_two_all_false(self) -> None:
        """RepeatOrElse(2, ...) returns False when both calls return False."""
        
        self.assertFalse(RepeatOrElse(2, lambda: False))

    def test_n_two_first_true_short_circuits(self) -> None:
        """RepeatOrElse(2, ...) does not call func a second time when first is True."""
        
        func, calls = _counter(True)

        self.assertTrue(RepeatOrElse(2, func))
        self.assertEqual(calls(), 1)  # Short-circuit

    def test_n_three_all_false(self) -> None:
        """RepeatOrElse(3, ...) returns False when all calls return False."""
        
        self.assertFalse(RepeatOrElse(3, lambda: False))

    def test_n_three_short_circuits_on_true(self) -> None:
        """RepeatOrElse(3, ...) stops calling as soon as a True is found."""
        
        func, calls = _counter(True)

        self.assertTrue(RepeatOrElse(3, func))
        self.assertLess(calls(), 3)

    def test_get_repeat_or_else_matches_direct(self) -> None:
        """GetRepeatOrElse returns a function producing the same result as RepeatOrElse."""
        
        self.assertEqual(GetRepeatOrElse(2, lambda: False)(), RepeatOrElse(2, lambda: False))

class TestRepeatOr(unittest.TestCase):
    """Tests for RepeatOr and GetRepeatOr (non-short-circuit OR)."""

    def test_n_less_than_one_raises(self) -> None:
        """RepeatOr raises ValueError for n < 1."""

        with self.assertRaises(ValueError): RepeatOr(0, lambda: True)

    def test_n_one(self) -> None:
        """RepeatOr(1, func) returns the result of a single call."""

        self.assertTrue(RepeatOr(1, lambda: True))
        self.assertFalse(RepeatOr(1, lambda: False))

    def test_n_two_any_true(self) -> None:
        """RepeatOr(2, ...) returns True when any call returns True."""
        
        self.assertTrue(RepeatOr(2, lambda: True))

    def test_n_two_all_false(self) -> None:
        """RepeatOr(2, ...) returns False when all calls return False."""
        
        self.assertFalse(RepeatOr(2, lambda: False))

    def test_n_two_no_short_circuit(self) -> None:
        """RepeatOr(2, ...) calls func twice even when first returns True."""
        
        func, calls = _counter(True)

        RepeatOr(2, func)

        self.assertEqual(calls(), 2)

    def test_n_three_all_called_on_true(self) -> None:
        """RepeatOr(3, ...) calls func 3 times even if first is True."""
        
        func, calls = _counter(True)

        RepeatOr(3, func)

        self.assertEqual(calls(), 3)

    def test_get_repeat_or_matches_direct(self) -> None:
        """GetRepeatOr returns a function producing the same result as RepeatOr."""
        
        self.assertEqual(GetRepeatOr(2, lambda: True)(), RepeatOr(2, lambda: True))

# ---------------------------------------------------------------------------
# Predicate combination
# ---------------------------------------------------------------------------

class TestPredicateCombination(unittest.TestCase):
    """Tests for all predicate combination functions and their Get* factories."""

    def test_predicate_and_also_both_true(self) -> None:
        """PredicateAndAlso returns True when both predicates are satisfied."""

        self.assertTrue(PredicateAndAlso(5, lambda x: x > 0, lambda x: x < 10))

    def test_predicate_and_also_first_false_short_circuits(self) -> None:
        """PredicateAndAlso short-circuits: second predicate not called when first is False."""
        
        pred2, calls = _predicate_counter(True)

        self.assertFalse(PredicateAndAlso(5, lambda _: False, pred2))
        self.assertEqual(calls(), 0)

    def test_get_and_also_predicate(self) -> None:
        """GetAndAlsoPredicate returns a predicate equivalent to PredicateAndAlso."""

        pred: Predicate[int] = GetAndAlsoPredicate(lambda x: x > 0, lambda x: x < 10)

        self.assertTrue(pred(5))
        self.assertFalse(pred(-1))

    def test_predicate_and_both_true(self) -> None:
        """PredicateAnd returns True when both predicates are satisfied."""
        
        self.assertTrue(PredicateAnd(5, lambda x: x > 0, lambda x: x < 10))

    def test_predicate_and_no_short_circuit(self) -> None:
        """PredicateAnd evaluates both predicates even when first is False."""
        
        pred2, calls = _predicate_counter(True)

        PredicateAnd(5, lambda _: False, pred2)

        self.assertEqual(calls(), 1) # Both evaluated

    def test_get_and_predicate(self) -> None:
        """GetAndPredicate returns a predicate equivalent to PredicateAnd."""

        pred: Predicate[int] = GetAndPredicate(lambda x: x > 0, lambda x: x < 10)

        self.assertTrue(pred(5))
        self.assertFalse(pred(-1))

    def test_predicate_or_else_any_true(self) -> None:
        """PredicateOrElse returns True when at least one predicate is satisfied."""
        
        self.assertTrue(PredicateOrElse(5, lambda x: x > 0, lambda _: False))

    def test_predicate_or_else_short_circuits(self) -> None:
        """PredicateOrElse does not call second predicate when first is True."""
        
        pred2, calls = _predicate_counter(False)

        result = PredicateOrElse(5, lambda _: True, pred2)

        self.assertTrue(result)
        self.assertEqual(calls(), 0)

    def test_get_or_else_predicate(self) -> None:
        """GetOrElsePredicate returns a predicate equivalent to PredicateOrElse."""
        
        pred: Predicate[int] = GetOrElsePredicate(lambda x: x > 0, lambda x: x > 10)

        self.assertTrue(pred(5))
        self.assertFalse(pred(-1))

    def test_predicate_or_no_short_circuit(self) -> None:
        """PredicateOr evaluates both predicates even when first is True."""
        
        pred2, calls = _predicate_counter(False)

        PredicateOr(5, lambda _: True, pred2)

        self.assertEqual(calls(), 1)

    def test_get_or_predicate(self) -> None:
        """GetOrPredicate returns a predicate equivalent to PredicateOr."""
        
        pred: Predicate[int] = GetOrPredicate(lambda x: x > 0, lambda x: x > 10)

        self.assertTrue(pred(5))
        self.assertFalse(pred(-1))

    def test_predicate_not_and_also(self) -> None:
        """PredicateNotAndAlso returns True when first is False and second is True."""
        
        self.assertTrue(PredicateNotAndAlso(5, lambda x: x > 10, lambda x: x > 0))
        self.assertFalse(PredicateNotAndAlso(5, lambda x: x > 0, lambda x: x > 10))

    def test_predicate_not_and_also_short_circuits(self) -> None:
        """PredicateNotAndAlso does not call second predicate when first is True."""
        
        pred2, calls = _predicate_counter(True)

        result = PredicateNotAndAlso(5, lambda _: True, pred2)

        self.assertFalse(result)
        self.assertEqual(calls(), 0)

    def test_get_not_and_also_predicate(self) -> None:
        """GetNotAndAlsoPredicate returns a predicate equivalent to PredicateNotAndAlso."""
        
        pred: Predicate[int] = GetNotAndAlsoPredicate(lambda x: x > 10, lambda x: x > 0)

        self.assertTrue(pred(5))
        self.assertFalse(pred(15))

    def test_predicate_not_and(self) -> None:
        """PredicateNotAnd returns True when first is False and second is True."""
        
        self.assertTrue(PredicateNotAnd(5, lambda x: x > 10, lambda x: x > 0))
        self.assertFalse(PredicateNotAnd(5, lambda x: x > 0, lambda x: x > 10))

    def test_predicate_not_and_no_short_circuit(self) -> None:
        """PredicateNotAnd evaluates both predicates even when first is True."""
        
        pred2, calls = _predicate_counter(True)

        PredicateNotAnd(5, lambda _: True, pred2)

        self.assertEqual(calls(), 1)

    def test_get_not_and_predicate(self) -> None:
        """GetNotAndPredicate returns a predicate equivalent to PredicateNotAnd."""
        
        pred: Predicate[int] = GetNotAndPredicate(lambda x: x > 10, lambda x: x > 0)

        self.assertTrue(pred(5))

    def test_predicate_not(self) -> None:
        """PredicateNot returns the negation of the predicate result."""
        
        self.assertTrue(PredicateNot(5, lambda x: x > 10))
        self.assertFalse(PredicateNot(5, lambda x: x > 0))

    def test_get_not_predicate(self) -> None:
        """GetNotPredicate returns a predicate that negates the original."""
        
        pred: Predicate[int] = GetNotPredicate(lambda x: x > 0)

        self.assertTrue(pred(-1))
        self.assertFalse(pred(5))

# ---------------------------------------------------------------------------
# Function combination
# ---------------------------------------------------------------------------

class TestFuncCombination(unittest.TestCase):
    """Tests for all function combination functions and their Get* factories."""

    def test_func_and_also_both_true(self) -> None:
        """FuncAndAlso returns True when both functions return True."""
        
        self.assertTrue(FuncAndAlso(lambda: True, lambda: True))

    def test_func_and_also_short_circuits(self) -> None:
        """FuncAndAlso does not call f2 when f1 returns False."""
        
        f2, calls = _counter(True)

        self.assertFalse(FuncAndAlso(lambda: False, f2))
        self.assertEqual(calls(), 0)

    def test_get_and_also_func(self) -> None:
        """GetAndAlsoFunc returns a function equivalent to FuncAndAlso."""

        self.assertTrue(GetAndAlsoFunc(lambda: True, lambda: True)())

    def test_func_and_no_short_circuit(self) -> None:
        """FuncAnd evaluates both functions even when f1 returns False."""

        f2, calls = _counter(True)

        FuncAnd(lambda: False, f2)

        self.assertEqual(calls(), 1)

    def test_func_and_both_false(self) -> None:
        """FuncAnd returns False when any function returns False."""

        self.assertFalse(FuncAnd(lambda: False, lambda: True))

    def test_get_and_func(self) -> None:
        """GetAndFunc returns a function equivalent to FuncAnd."""
        
        self.assertFalse(GetAndFunc(lambda: False, lambda: True)())

    def test_func_or_else_short_circuits(self) -> None:
        """FuncOrElse does not call f2 when f1 returns True."""

        f2, calls = _counter(False)

        self.assertTrue(FuncOrElse(lambda: True, f2))
        self.assertEqual(calls(), 0)

    def test_func_or_else_both_false(self) -> None:
        """FuncOrElse returns False when both functions return False."""

        self.assertFalse(FuncOrElse(lambda: False, lambda: False))

    def test_get_or_else_func(self) -> None:
        """GetOrElseFunc returns a function equivalent to FuncOrElse."""
        
        self.assertTrue(GetOrElseFunc(lambda: False, lambda: True)())

    def test_func_or_no_short_circuit(self) -> None:
        """FuncOr evaluates both functions even when f1 returns True."""

        f2, calls = _counter(False)

        FuncOr(lambda: True, f2)

        self.assertEqual(calls(), 1)

    def test_get_or_func(self) -> None:
        """GetOrFunc returns a function equivalent to FuncOr."""
        
        self.assertTrue(GetOrFunc(lambda: True, lambda: False)())

    def test_func_not_and_also(self) -> None:
        """FuncNotAndAlso returns True when f1 is False and f2 is True."""

        self.assertTrue(FuncNotAndAlso(lambda: False, lambda: True))
        self.assertFalse(FuncNotAndAlso(lambda: True, lambda: True))

    def test_func_not_and_also_short_circuits(self) -> None:
        """FuncNotAndAlso does not call f2 when f1 is True."""

        f2, calls = _counter(True)

        FuncNotAndAlso(lambda: True, f2)

        self.assertEqual(calls(), 0)

    def test_get_not_and_also_func(self) -> None:
        """GetNotAndAlsoFunc returns a function equivalent to FuncNotAndAlso."""
        
        self.assertTrue(GetNotAndAlsoFunc(lambda: False, lambda: True)())

    def test_func_not_and_no_short_circuit(self) -> None:
        """FuncNotAnd evaluates both functions even when f1 is True."""

        f2, calls = _counter(True)

        FuncNotAnd(lambda: True, f2)

        self.assertEqual(calls(), 1)

    def test_get_not_and_func(self) -> None:
        """GetNotAndFunc returns a function equivalent to FuncNotAnd."""

        self.assertTrue(GetNotAndFunc(lambda: False, lambda: True)())

    def test_func_not(self) -> None:
        """FuncNot returns the negation of the function result."""

        self.assertTrue(FuncNot(lambda: False))
        self.assertFalse(FuncNot(lambda: True))

    def test_get_not_func(self) -> None:
        """GetNotFunc returns a function that negates the original."""
        self.assertFalse(GetNotFunc(lambda: True)())

# ---------------------------------------------------------------------------
# Comparison factories
# ---------------------------------------------------------------------------

class TestComparisonFactories(unittest.TestCase):
    """Tests for GetEqualityComparison, GetIndexedValue*, GetSelectedEqualityComparison."""

    def test_get_equality_comparison(self) -> None:
        """GetEqualityComparison returns a predicate that checks equality against a fixed value."""

        is_five = GetEqualityComparison(5)

        self.assertTrue(is_five(5))
        self.assertFalse(is_five(4))
        self.assertFalse(is_five(6))

    def test_get_indexed_value_index_comparison(self) -> None:
        """GetIndexedValueIndexComparison returns a comparison that checks the index only."""
        
        comp: IndexedValueComparison[str] = GetIndexedValueIndexComparison(2)

        self.assertTrue(comp(2, "any"))
        self.assertFalse(comp(1, "any"))
        self.assertFalse(comp(3, "any"))

    def test_get_indexed_value_value_comparison(self) -> None:
        """GetIndexedValueValueComparison returns a comparison that checks the value only."""
        
        comp = GetIndexedValueValueComparison("hello")

        self.assertTrue(comp(0, "hello"))
        self.assertTrue(comp(99, "hello"))
        self.assertFalse(comp(0, "world"))

    def test_get_indexed_value_comparison(self) -> None:
        """GetIndexedValueComparison returns a comparison that checks both index and value."""
        
        comp = GetIndexedValueComparison(1, "x")

        self.assertTrue(comp(1, "x"))
        self.assertFalse(comp(0, "x")) # Wrong index
        self.assertFalse(comp(1, "y")) # Wrong value
        self.assertFalse(comp(0, "y")) # Both wrong

    def test_get_selected_equality_comparison(self) -> None:
        """GetSelectedEqualityComparison applies a converter before comparing."""
        
        comp: EqualityComparison[str] = GetSelectedEqualityComparison(lambda x, y: x == y, lambda s: s.lower())

        self.assertTrue(comp("Hello", "hello"))
        self.assertTrue(comp("ABC", "abc"))
        self.assertFalse(comp("Hello", "world"))

    def test_try_get_selected_equality_comparison_with_predicate(self) -> None:
        """TryGetSelectedEqualityComparison returns a comparison when predicate is provided."""
        
        comp: EqualityComparison[str]|None = TryGetSelectedEqualityComparison(lambda x, y: x == y, lambda s: s.lower())

        self.assertIsNotNone(comp)
        self.assertTrue(comp("Hello", "hello"))  # type: ignore[misc]

    def test_try_get_selected_equality_comparison_with_none(self) -> None:
        """TryGetSelectedEqualityComparison returns None when predicate is None."""

        comp: EqualityComparison[str]|None = TryGetSelectedEqualityComparison(None, lambda s: s)
        
        self.assertIsNone(comp)

if __name__ == '__main__':
    unittest.main()