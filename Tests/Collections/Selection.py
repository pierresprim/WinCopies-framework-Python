"""
Unit tests for the predicate enumerators of WinCopies.Collections.Enumeration.Selection, and for the
two functions of WinCopies.Collections.Iteration.Enumeration that exclude a prefix, ExcludeWhile() and
ExcludeUntil().

Each enumerator reads its source in order, and asks its predicate about the current item, None
included: the predicate decides. With a predicate p:
- SelectorEnumerator keeps the items that satisfy p;
- IncluerEnumerator includes the items while p holds, and IncluerUntilEnumerator until it holds,
  without the item that stops them;
- PredicateDoWhileEnumerator includes them while p holds, and DoUntilEnumerator and
  PredicateDoUntilEnumerator until it holds, with the item that stops them;
- ExcluerEnumerator excludes them while p holds, and ExcluerUntilEnumerator until it holds, then
  includes the rest; ExcludeWhile() and ExcludeUntil() do the same over any iterable.

Until a3ff1202, ExcluerEnumerator behaved as ExcluerUntilEnumerator; IncluerEnumerator filtered out
the items that satisfy p, and IncluerUntilEnumerator included the items while p held; and an item
None never satisfied p, which was not asked. ExcludeWhile() was built on ExcluerEnumerator, and
behaved as ExcludeUntil() until 61fe9e9f (Enumeration 6.14).
"""

import unittest

from collections.abc import Callable
from contextlib import ExitStack
from typing import Any
from unittest import mock

import WinCopies.Collections.Enumeration.Selection as Selection
import WinCopies.Collections.Iteration.Enumeration as Iteration

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import CreateList
from WinCopies.Collections.Enumeration.Core import IEnumerator
from WinCopies.Typing.Delegate import Predicate

type _Factory[T] = Callable[[IEnumerator[T], Predicate[T]], IEnumerator[T]]

def _below2(value: int) -> bool: return value < 2
def _none(value: int|None) -> bool: return value is None

_SEQUENCES: ReadOnlyArray[ReadOnlyArray[int]] = ((1, 1, 4, 1, 5), (3, 1, 4, 1, 5), ())
"""Two sequences that start on either side of the predicate `value < 2`, and an empty one."""

_ENUMERATORS: ReadOnlyArray[tuple[str, _Factory[int], ReadOnlyArray[ReadOnlyArray[int]]]] = (
    ("SelectorEnumerator", Selection.SelectorEnumerator[int], ((1, 1, 1), (1, 1), ())),
    ("IncluerEnumerator", Selection.IncluerEnumerator[int], ((1, 1), (), ())),
    ("IncluerUntilEnumerator", Selection.IncluerUntilEnumerator[int], ((), (3,), ())),
    ("PredicateDoWhileEnumerator", Selection.PredicateDoWhileEnumerator[int], ((1, 1, 4), (3,), ())),
    ("DoUntilEnumerator", Selection.DoUntilEnumerator[int], ((1,), (3, 1), ())),
    ("PredicateDoUntilEnumerator", Selection.PredicateDoUntilEnumerator[int], ((1,), (3, 1), ())),
    ("ExcluerEnumerator", Selection.ExcluerEnumerator[int], ((4, 1, 5), (3, 1, 4, 1, 5), ())),
    ("ExcluerUntilEnumerator", Selection.ExcluerUntilEnumerator[int], ((1, 1, 4, 1, 5), (1, 4, 1, 5), ())))
"""Each enumerator, and what it reads of each sequence with the predicate `value < 2`."""

_WITH_NONE: ReadOnlyArray[int|None] = (1, None, 2)

_ENUMERATORS_WITH_NONE: ReadOnlyArray[tuple[str, _Factory[int|None], ReadOnlyArray[int|None]]] = (
    ("SelectorEnumerator", Selection.SelectorEnumerator[int|None], (None,)),
    ("IncluerEnumerator", Selection.IncluerEnumerator[int|None], ()),
    ("IncluerUntilEnumerator", Selection.IncluerUntilEnumerator[int|None], (1,)),
    ("PredicateDoWhileEnumerator", Selection.PredicateDoWhileEnumerator[int|None], (1,)),
    ("DoUntilEnumerator", Selection.DoUntilEnumerator[int|None], (1, None)),
    ("PredicateDoUntilEnumerator", Selection.PredicateDoUntilEnumerator[int|None], (1, None)),
    ("ExcluerEnumerator", Selection.ExcluerEnumerator[int|None], (1, None, 2)),
    ("ExcluerUntilEnumerator", Selection.ExcluerUntilEnumerator[int|None], (None, 2)))
"""Each enumerator, and what it reads of (1, None, 2) with the predicate `value is None`."""

def _read[T](create: _Factory[T], items: ReadOnlyArray[T], predicate: Predicate[T]) -> tuple[ReadOnlyArray[T], str]:
    """What an enumerator over `items` reads, and its status once it has ended."""

    source: IEnumerator[T]|None = CreateList(list(items)).TryGetEnumerator()

    assert source is not None

    enumerator: IEnumerator[T] = create(source, predicate)
    read: list[T] = []

    while enumerator.TryMoveNext(): read.append(enumerator.GetCurrent())

    return (tuple(read), f"{enumerator.GetStatus().GetState().name}/{enumerator.GetStatus().GetResult().name}")

class TestEachEnumeratorReadsWhatItsPredicateSelects(unittest.TestCase):
    def test_each_enumerator_reads_what_its_predicate_selects(self) -> None:
        """Each ends Completed, the empty sequence included."""

        for name, create, expected in _ENUMERATORS:
            for items, reads in zip(_SEQUENCES, expected):
                with self.subTest(enumerator = name, items = items): self.assertEqual(_read(create, items, _below2), (reads, "Ended/Completed"))

    def test_the_predicate_decides_for_an_item_none(self) -> None:
        """None is an item like any other: the predicate is asked about it, and here it is the one item
        that satisfies it."""

        for name, create, expected in _ENUMERATORS_WITH_NONE:
            with self.subTest(enumerator = name): self.assertEqual(_read(create, _WITH_NONE, _none), (expected, "Ended/Completed"))

class TestExcludeWhileAndExcludeUntil(unittest.TestCase):
    def test_they_exclude_a_prefix(self) -> None:
        """They read as ExcluerEnumerator and ExcluerUntilEnumerator do, over a tuple, None included;
        given no items, they yield none."""

        cases: ReadOnlyArray[tuple[str, Callable[[ReadOnlyArray[int]|None, Predicate[int]], Any], ReadOnlyArray[ReadOnlyArray[int]]]] = (
            ("ExcludeWhile", Iteration.ExcludeWhile, ((4, 1, 5), (3, 1, 4, 1, 5), ())),
            ("ExcludeUntil", Iteration.ExcludeUntil, ((1, 1, 4, 1, 5), (1, 4, 1, 5), ())))

        for name, exclude, expected in cases:
            for items, reads in zip(_SEQUENCES, expected):
                with self.subTest(function = name, items = items): self.assertEqual(tuple(exclude(items, _below2)), reads)

            with self.subTest(function = name, items = None): self.assertEqual(tuple(exclude(None, _below2)), ())

        withNone: ReadOnlyArray[tuple[str, Callable[[ReadOnlyArray[int|None], Predicate[int|None]], Any], ReadOnlyArray[int|None]]] = (
            ("ExcludeWhile", Iteration.ExcludeWhile, (1, None, 2)),
            ("ExcludeUntil", Iteration.ExcludeUntil, (None, 2)))

        for name, excludeWithNone, readsWithNone in withNone:
            with self.subTest(function = name, items = _WITH_NONE): self.assertEqual(tuple(excludeWithNone(_WITH_NONE, _none)), readsWithNone)

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

class TestTheSelectionBenchesCanFail(unittest.TestCase):
    """The benches above, run against the defects that a3ff1202 and 61fe9e9f corrected: green on the
    intact tree, red on the rebuilt one, and red on their assertions rather than on an error. The
    private members are reached by their mangled names."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, rebuilt: ReadOnlyArray[tuple[Any, dict[str, Any]]]) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with ExitStack() as patches:
            for target, members in rebuilt: patches.enter_context(mock.patch.multiple(target, **members))

            broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")
        self.assertEqual(broken.errors, [], f"{name} fell on an error rather than on its assertions")

    def test_the_bench_falls_when_excluding_while_behaves_as_excluding_until(self) -> None:
        """ExclusionEnumerator derived from ExclusionUntilEnumerator, and took its rule."""

        self.__assertFalls(TestEachEnumeratorReadsWhatItsPredicateSelects, "test_each_enumerator_reads_what_its_predicate_selects", ((Selection.ExclusionEnumerator, {"_OnMoveNext": getattr(Selection.ExclusionUntilEnumerator, "_OnMoveNext")}),))

    def test_the_bench_falls_on_the_inclusion_enumerators_as_they_were(self) -> None:
        """IncluerUntilEnumerator derived from InclusionEnumerator, and so included the items while its
        predicate held. IncluerEnumerator derived from InclusionUntilEnumerator, which had no rule of
        its own to stop, and so kept the filter of ConditionalEnumerator over the negated predicate."""

        def negated(predicate: str) -> Callable[[Any], bool]:
            def validate(self: Any) -> bool: return not getattr(self, predicate).GetValue()

            return validate

        rebuilt: ReadOnlyArray[tuple[Any, dict[str, Any]]] = (
            (Selection.IncluerUntilEnumerator, {"_ValidateValue": negated("_IncluerUntilEnumerator__predicate")}),
            (Selection.IncluerEnumerator, {"_MoveNextOverride": getattr(Selection.ConditionalEnumerator, "_MoveNextOverride"), "_Validate": negated("_IncluerEnumerator__predicate")}))

        for target, members in rebuilt:
            with self.subTest(enumerator = target.__name__): self.__assertFalls(TestEachEnumeratorReadsWhatItsPredicateSelects, "test_each_enumerator_reads_what_its_predicate_selects", ((target, members),))

    def test_the_bench_falls_when_an_item_none_is_never_selected(self) -> None:
        """The predicate was not asked about None, which never satisfied it."""

        predicate: type = getattr(Selection, "_PredicateEnumerator")

        def unasked(self: Any) -> bool:
            current: Any = getattr(self, "_PredicateEnumerator__enumerator").GetCurrent()

            return False if current is None else bool(getattr(self, "_PredicateEnumerator__predicate")(current))

        self.__assertFalls(TestEachEnumeratorReadsWhatItsPredicateSelects, "test_the_predicate_decides_for_an_item_none", ((predicate, {"GetValue": unasked}),))

    def test_the_function_bench_falls_when_excluding_while_behaves_as_excluding_until(self) -> None:
        """ExcludeWhile() behaved as ExcludeUntil(): rebuilt as excluding until its predicate itself
        holds, rather than until its negation does."""

        def unchanged(predicate: Predicate[Any]) -> Predicate[Any]: return predicate

        self.__assertFalls(TestExcludeWhileAndExcludeUntil, "test_they_exclude_a_prefix", ((Iteration, {"GetNotPredicate": unchanged}),))

if __name__ == '__main__': unittest.main()
