"""
Unit tests for the mapping family (WinCopies.Collections.Abstraction.Mapping).

The ordered set is the subject these benches were written for. Five defects were found on
that one type in a single session -- D-41 to D-45 -- of which three let the collection reach
a state no ordered set may be in, and not one of them was caught by a bench, because the
harness held none. All five were found by hand, with a probe.

So these benches assert the invariant itself rather than the outcome of any one call. A
bench per defect catches that defect; a bench on the invariant catches the class. Whatever a
mutator returns, and whether it writes, refuses by return value or refuses by raising, the
collection it leaves behind must still be an ordered set.
"""

import unittest
from collections.abc import Iterator, MutableSequence
from typing import Any, Callable

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Extensions import IList, IOrderedSet
from WinCopies.Typing.Delegate import Converter

type _Carrier = tuple[IOrderedSet[int], IList[int]]
type _Call = Callable[[IOrderedSet[int], IList[int]], Any]

_CONTENT: ReadOnlyArray[int] = (0, 1, 2)

_DOMAIN: ReadOnlyArray[int] = (-1, 0, 1, 2, 7, 8, 9, 99)
"""Every value these benches hand to a mutator, plus values none of them inserts.

The clause that catches a phantom -- something the set admits that the order does not carry
-- has to be a biconditional over a finite declared domain rather than a comparison of two
enumerations, because the set is reachable only as a membership oracle: no member of either
type returns an element taken from it. Verified by enumerating every use of the set in
Abstraction/Mapping/Extensions.py.
"""

_REFUSABLE: frozenset[str] = frozenset((
    "Add(0)", "AddRange([0])", "TryAddRange([0])", "TryAdd(0)", "TryAddRange([7, 0])",
    "AddRange([7, 7])", "TryAddRange([7, 7])", "AddValues(7, 7)", "TryAddValues(7, 7)", "extend([7, 7])",
    "Insert(4, 7)", "TryInsert(4, 7)", "Insert(1, 0)", "TryInsert(1, 0)",
    "InsertRange(1, [0])", "InsertRange(1, [7, 0])", "InsertRange(4, [7])", "TryInsertRange(1, [0])",
    "InsertRange(1, [7, 7])", "TryInsertRange(1, [7, 7])", "TryInsertRange(1, dup)",
    "InsertValues(1, 0)", "InsertValues(1, 7, 7)",
    "SetAt(1, 0)", "SetAt(9, 7)", "TrySetAt(1, 0)", "TrySetAt(9, 7)",
    "l[1] = 0", "l[9] = 7", "l[1:2] = [0]", "l[0:2] = [7, 7]",
    "RemoveAt(9)", "TryRemoveAt(-1)", "TryRemoveAt(9)", "TryRemoveRange(9, 1)",
    "Remove(7)", "TryRemove(7)", "TryMove(0, 9)", "TrySwap(0, 9)", "del l[9]",
    "rev.SetAt(1, 0)", "rev[1] = 0", "rev.Insert(1, 0)", "rev.InsertRange(1, [7, 7])"))
"""The calls these benches build that the subject may legitimately refuse: an index outside
its range, a value the set already holds elsewhere, or -- D-60 -- a range that carries the
same value twice, which no ordered set can take whole whatever its indices.

Everything else is legitimate on a (0, 1, 2) ordered set and must therefore succeed. That
line is what the invariant alone cannot draw: a call that refuses leaves a correct state
behind, so asserting the invariant passes over a member that does not work at all. D-52
lived there for a session, and D-51 still does.
"""

_BLOCKED: ReadOnlyArray[tuple[str, ReadOnlyArray[tuple[str, str]]]] = (
    ("D-53 and D-54, the protocol mixins reach for index -1",
     (("list", "pop()"), ("list", "clear()"))),
    ("D-24 on the set family, an empty range is a failure",
     (("set", "AddRange([])"), ("set", "AddValues()"))))
"""Legitimate calls that an open defect still refuses, each named with its carrier and
grouped by the defect that refuses it, so every group signals on its own when its defect
closes. The carrier is part of the name because the list view and the collection share
labels: AddRange([]) succeeds on the first and fails on the second."""

def _carriers() -> ReadOnlyArray[tuple[str, dict[str, _Call]]]:
    return (("list", _listCalls()), ("set", _setCalls()), ("reversed", _reversedCalls()))

def _blocked() -> frozenset[tuple[str, str]]:
    return frozenset(call for _, calls in _BLOCKED for call in calls)

def _create() -> _Carrier:
    items: IOrderedSet[int] = CreateOrderedSet(_CONTENT)

    return (items, items.AsList())

def _snapshot(items: IOrderedSet[int]) -> ReadOnlyArray[int]:
    return tuple(items.AsIterable())

def _mutable[T](view: IList[T]) -> MutableSequence[T]:
    """The declared door to the Python protocol.

    IList is an interface and carries no dunder; the framework's way to the subscript is
    AsMutableSequence(), which is measured to be the view itself. So routing through it
    exercises the very object a consumer writes to, and keeps the sweep type-clean -- the
    lesson the read-path sweep of Registry.py already paid for.
    """

    return view.AsMutableSequence()

def _assertInvariant(test: unittest.TestCase, items: IOrderedSet[int], view: IList[int], label: str) -> None:
    """The four clauses that make a collection an ordered set.

    Order carries no duplicate; the count agrees with the order; the set admits exactly what
    the order carries, over the declared domain; and the list view reads the same order as
    the collection itself.
    """

    carried: ReadOnlyArray[int] = tuple(_snapshot(items))

    test.assertEqual(len(set(carried)), len(carried), f"{label}: duplicate in {carried}")
    test.assertEqual(items.GetCount(), len(carried), f"{label}: count {items.GetCount()} against {carried}")

    for value in _DOMAIN:
        test.assertEqual(items.Contains(value), value in carried,
                         f"{label}: Contains({value}) is {items.Contains(value)} while the order carries {carried}")

    test.assertEqual(tuple(view.AsSequence()), carried, f"{label}: the list view reads {tuple(view.AsSequence())}")

def _setElements(candidate: object) -> ReadOnlyArray[Any]:
    """The elements of `candidate` when it is a non-empty set, otherwise nothing.

    One signature holds the whole reflective step, so the single thing a strict checker
    cannot resolve -- the element type of a set reached by walking an object graph -- stays
    on one line instead of spreading through the walk that needs it.
    """

    return tuple[Any](candidate) if isinstance(candidate, set) and len(candidate) > 0 else () # pyright: ignore[reportUnknownArgumentType]

def _attempt(call: _Call, items: IOrderedSet[int], view: IList[int]) -> Any:
    """Runs a mutator and swallows whatever it answers, including an exception.

    The invariant is not conditional on success: a refusal must leave an ordered set behind
    just as a write must, and a refusal that raises is still a refusal.
    """

    try: return call(items, view)
    except Exception as exception: return exception

def _listCalls() -> dict[str, _Call]:
    """Every public mutator of the ordered set's list view, in every argument shape that
    the type distinguishes: a value it holds, one it does not, an index inside, the append
    position, an index outside, an empty range, and a one-pass iterable."""

    return {
        "Add(7)":                   lambda o, l: l.Add(7),
        "Add(0)":                   lambda o, l: l.Add(0),
        "AddRange([7, 8])":         lambda o, l: l.AddRange([7, 8]),
        "AddRange([])":             lambda o, l: l.AddRange([]),
        "AddRange([0])":            lambda o, l: l.AddRange([0]),
        "AddRange([7, 7])":         lambda o, l: l.AddRange([7, 7]),
        "AddRange(iter([7, 8]))":   lambda o, l: l.AddRange(iter([7, 8])),
        "TryAddRange([7, 8])":      lambda o, l: l.TryAddRange([7, 8]),
        "TryAddRange([])":          lambda o, l: l.TryAddRange([]),
        "TryAddRange([0])":         lambda o, l: l.TryAddRange([0]),

        "Insert(1, 7)":             lambda o, l: l.Insert(1, 7),
        "Insert(3, 7)":             lambda o, l: l.Insert(3, 7),
        "Insert(4, 7)":             lambda o, l: l.Insert(4, 7),
        "Insert(1, 0)":             lambda o, l: l.Insert(1, 0),
        "TryInsert(1, 7)":          lambda o, l: l.TryInsert(1, 7),
        "TryInsert(3, 7)":          lambda o, l: l.TryInsert(3, 7),
        "TryInsert(4, 7)":          lambda o, l: l.TryInsert(4, 7),
        "TryInsert(1, 0)":          lambda o, l: l.TryInsert(1, 0),

        "InsertRange(1, [7, 8])":   lambda o, l: l.InsertRange(1, [7, 8]),
        "InsertRange(1, [])":       lambda o, l: l.InsertRange(1, []),
        "InsertRange(1, [0])":      lambda o, l: l.InsertRange(1, [0]),
        "InsertRange(1, [7, 0])":   lambda o, l: l.InsertRange(1, [7, 0]),
        "InsertRange(1, [7, 7])":   lambda o, l: l.InsertRange(1, [7, 7]),
        "InsertRange(4, [7])":      lambda o, l: l.InsertRange(4, [7]),
        "InsertRange(1, iter)":     lambda o, l: l.InsertRange(1, iter([7, 8])),
        "TryInsertRange(1, [7])":   lambda o, l: l.TryInsertRange(1, [7]),
        "TryInsertRange(1, [])":    lambda o, l: l.TryInsertRange(1, []),
        "TryInsertRange(1, [0])":   lambda o, l: l.TryInsertRange(1, [0]),
        "TryInsertRange(1, [7, 7])":lambda o, l: l.TryInsertRange(1, [7, 7]),
        "TryInsertRange(1, iter)":  lambda o, l: l.TryInsertRange(1, iter([7, 8])),
        # The duplicate reaches the unicity pass through the buffer rather than from a
        # sequence it can re-read, which is the seam D-42's residual still sits on.
        "TryInsertRange(1, dup)":   lambda o, l: l.TryInsertRange(1, iter([7, 7])),

        "InsertValues(1, 7, 8)":    lambda o, l: l.InsertValues(1, 7, 8),
        "InsertValues(1)":          lambda o, l: l.InsertValues(1),
        "InsertValues(1, 0)":       lambda o, l: l.InsertValues(1, 0),
        "InsertValues(1, 7, 7)":    lambda o, l: l.InsertValues(1, 7, 7),
        "TryInsertValues(1, 7)":    lambda o, l: l.TryInsertValues(1, 7),
        "TryInsertValues(1)":       lambda o, l: l.TryInsertValues(1),

        "SetAt(1, 7)":              lambda o, l: l.SetAt(1, 7),
        "SetAt(1, 1)":              lambda o, l: l.SetAt(1, 1),
        "SetAt(1, 0)":              lambda o, l: l.SetAt(1, 0),
        "SetAt(9, 7)":              lambda o, l: l.SetAt(9, 7),
        "TrySetAt(1, 7)":           lambda o, l: l.TrySetAt(1, 7),
        "TrySetAt(1, 1)":           lambda o, l: l.TrySetAt(1, 1),
        "TrySetAt(1, 0)":           lambda o, l: l.TrySetAt(1, 0),
        "TrySetAt(9, 7)":           lambda o, l: l.TrySetAt(9, 7),

        "l[1] = 7":                 lambda o, l: _mutable(l).__setitem__(1, 7),
        "l[1] = 1":                 lambda o, l: _mutable(l).__setitem__(1, 1),
        "l[1] = 0":                 lambda o, l: _mutable(l).__setitem__(1, 0),
        "l[9] = 7":                 lambda o, l: _mutable(l).__setitem__(9, 7),
        "l[0:2] = [7, 8]":          lambda o, l: _mutable(l).__setitem__(slice(0, 2), [7, 8]),
        "l[1:2] = [0]":             lambda o, l: _mutable(l).__setitem__(slice(1, 2), [0]),
        "l[0:2] = [1, 0]":          lambda o, l: _mutable(l).__setitem__(slice(0, 2), [1, 0]),
        "l[1:1] = [7]":             lambda o, l: _mutable(l).__setitem__(slice(1, 1), [7]),
        "l[1:1] = []":              lambda o, l: _mutable(l).__setitem__(slice(1, 1), []),
        "l[0:2] = [7, 7]":          lambda o, l: _mutable(l).__setitem__(slice(0, 2), [7, 7]),

        "RemoveAt(1)":              lambda o, l: l.RemoveAt(1),
        "RemoveAt(9)":              lambda o, l: l.RemoveAt(9),
        "TryRemoveAt(1)":           lambda o, l: l.TryRemoveAt(1),
        "TryRemoveAt(-1)":          lambda o, l: l.TryRemoveAt(-1),
        "TryRemoveAt(9)":           lambda o, l: l.TryRemoveAt(9),
        "RemoveRange(0, 2)":        lambda o, l: l.RemoveRange(0, 2),
        "TryRemoveRange(0, 2)":     lambda o, l: l.TryRemoveRange(0, 2),
        "TryRemoveRange(0, 99)":    lambda o, l: l.TryRemoveRange(0, 99),
        "TryRemoveRange(9, 1)":     lambda o, l: l.TryRemoveRange(9, 1),
        "Remove(0)":                lambda o, l: l.Remove(0),
        "Remove(7)":                lambda o, l: l.Remove(7),
        "TryRemove(0)":             lambda o, l: l.TryRemove(0),
        "TryRemove(7)":             lambda o, l: l.TryRemove(7),

        "Move(0, 2)":               lambda o, l: l.Move(0, 2),
        "TryMove(0, 2)":            lambda o, l: l.TryMove(0, 2),
        "TryMove(0, 9)":            lambda o, l: l.TryMove(0, 9),
        "Swap(0, 2)":               lambda o, l: l.Swap(0, 2),
        "TrySwap(0, 2)":            lambda o, l: l.TrySwap(0, 2),
        "TrySwap(0, 9)":            lambda o, l: l.TrySwap(0, 9),
        "Clear()":                  lambda o, l: l.Clear(),

        "insert(1, 7)":             lambda o, l: _mutable(l).insert(1, 7),
        "append(7)":                lambda o, l: _mutable(l).append(7),
        "extend([7, 8])":           lambda o, l: _mutable(l).extend([7, 8]),
        "extend([7, 7])":           lambda o, l: _mutable(l).extend([7, 7]),
        "pop()":                    lambda o, l: _mutable(l).pop(),
        "pop(0)":                   lambda o, l: _mutable(l).pop(0),
        "remove(0)":                lambda o, l: _mutable(l).remove(0),
        "reverse()":                lambda o, l: _mutable(l).reverse(),
        "clear()":                  lambda o, l: _mutable(l).clear(),
        "del l[1]":                 lambda o, l: _mutable(l).__delitem__(1),
        "del l[9]":                 lambda o, l: _mutable(l).__delitem__(9),
        "del l[0:2]":               lambda o, l: _mutable(l).__delitem__(slice(0, 2))}

def _setCalls() -> dict[str, _Call]:
    """Every public mutator of the ordered set itself."""

    return {
        "Add(7)":                   lambda o, l: o.Add(7),
        "Add(0)":                   lambda o, l: o.Add(0),
        "TryAdd(7)":                lambda o, l: o.TryAdd(7),
        "TryAdd(0)":                lambda o, l: o.TryAdd(0),
        "AddRange([7, 8])":         lambda o, l: o.AddRange([7, 8]),
        "AddRange([])":             lambda o, l: o.AddRange([]),
        "AddRange([0])":            lambda o, l: o.AddRange([0]),
        "TryAddRange([7, 8])":      lambda o, l: o.TryAddRange([7, 8]),
        "TryAddRange([])":          lambda o, l: o.TryAddRange([]),
        "TryAddRange([7, 0])":      lambda o, l: o.TryAddRange([7, 0]),
        "AddRange([7, 7])":         lambda o, l: o.AddRange([7, 7]),
        "TryAddRange([7, 7])":      lambda o, l: o.TryAddRange([7, 7]),
        "AddValues(7, 8)":          lambda o, l: o.AddValues(7, 8),
        "AddValues()":              lambda o, l: o.AddValues(),
        "TryAddValues(7, 8)":       lambda o, l: o.TryAddValues(7, 8),
        "TryAddValues()":           lambda o, l: o.TryAddValues(),
        "AddValues(7, 7)":          lambda o, l: o.AddValues(7, 7),
        "TryAddValues(7, 7)":       lambda o, l: o.TryAddValues(7, 7),
        "Remove(0)":                lambda o, l: o.Remove(0),
        "Remove(7)":                lambda o, l: o.Remove(7),
        "TryRemove(0)":             lambda o, l: o.TryRemove(0),
        "TryRemove(7)":             lambda o, l: o.TryRemove(7),
        "Clear()":                  lambda o, l: o.Clear()}

def _reversedCalls() -> dict[str, _Call]:
    """The same list surface, reached through the reversed view: it maps every index, so a
    mapping that forgets the set is a distinct way to break the same invariant."""

    def reversedView(l: IList[int]) -> IList[int]: return l.AsReversed()

    return {
        "rev.SetAt(1, 7)":          lambda o, l: reversedView(l).SetAt(1, 7),
        "rev.SetAt(1, 1)":          lambda o, l: reversedView(l).SetAt(1, 1),
        "rev.SetAt(1, 0)":          lambda o, l: reversedView(l).SetAt(1, 0),
        "rev.TrySetAt(1, 7)":       lambda o, l: reversedView(l).TrySetAt(1, 7),
        "rev[1] = 7":               lambda o, l: _mutable(reversedView(l)).__setitem__(1, 7),
        "rev[1] = 0":               lambda o, l: _mutable(reversedView(l)).__setitem__(1, 0),
        "rev[0:2] = [7, 8]":        lambda o, l: _mutable(reversedView(l)).__setitem__(slice(0, 2), [7, 8]),
        "rev.Insert(1, 7)":         lambda o, l: reversedView(l).Insert(1, 7),
        "rev.Insert(3, 7)":         lambda o, l: reversedView(l).Insert(3, 7),
        "rev.Insert(1, 0)":         lambda o, l: reversedView(l).Insert(1, 0),
        "rev.InsertRange(1, [7])":  lambda o, l: reversedView(l).InsertRange(1, [7]),
        "rev.InsertRange(1, [7, 7])": lambda o, l: reversedView(l).InsertRange(1, [7, 7]),
        "rev.Add(7)":               lambda o, l: reversedView(l).Add(7),
        "rev.AddRange([7, 8])":     lambda o, l: reversedView(l).AddRange([7, 8]),
        "rev.RemoveAt(1)":          lambda o, l: reversedView(l).RemoveAt(1),
        "rev.Remove(0)":            lambda o, l: reversedView(l).Remove(0),
        "rev.Move(0, 2)":           lambda o, l: reversedView(l).Move(0, 2),
        "rev.Swap(0, 2)":           lambda o, l: reversedView(l).Swap(0, 2),
        "rev.reverse()":            lambda o, l: _mutable(reversedView(l)).reverse(),
        "del rev[1]":               lambda o, l: _mutable(reversedView(l)).__delitem__(1),
        "del rev[0:2]":             lambda o, l: _mutable(reversedView(l)).__delitem__(slice(0, 2))}

class TestOrderedSetInvariant(unittest.TestCase):
    """What defines the type, asserted after every mutator of every carrier.

    D-41 and D-45 both reached a state where the set and the order disagreed, and D-42 left
    values the set admitted and the order did not carry. The three are distinct bugs with one
    shape, which is why the assertion is on the shape and not on the three.
    """

    def __run(self, calls: dict[str, _Call], carrier: str) -> None:
        for label, call in calls.items():
            with self.subTest(carrier = carrier, call = label):
                items, view = _create()

                _attempt(call, items, view)
                _assertInvariant(self, items, view, f"{carrier}.{label}")

    def test_the_list_view_leaves_an_ordered_set(self) -> None:
        self.__run(_listCalls(), "list")

    def test_the_ordered_set_leaves_an_ordered_set(self) -> None:
        self.__run(_setCalls(), "set")

    def test_the_reversed_view_leaves_an_ordered_set(self) -> None:
        self.__run(_reversedCalls(), "reversed")

class TestLegitimateCallsSucceed(unittest.TestCase):
    """The half the invariant cannot assert: a call that should work does work.

    A member that refuses leaves a correct state behind, so TestOrderedSetInvariant passes
    over it -- it asserts that the state stays correct whatever the answer, and a refusal
    that mutates nothing satisfies that. This asserts the other half, and it is the bench
    that would have caught D-52 the day it was introduced.
    """

    def test_every_legitimate_call_succeeds(self) -> None:
        blocked: frozenset[tuple[str, str]] = _blocked()

        for carrier, calls in _carriers():
            for label, call in calls.items():
                if label in _REFUSABLE or (carrier, label) in blocked: continue

                with self.subTest(carrier = carrier, call = label):
                    items, view = _create()
                    outcome: Any = _attempt(call, items, view)

                    self.assertNotIsInstance(outcome, Exception, f"{carrier}.{label} refused: {outcome!r}")
                    _assertInvariant(self, items, view, f"{carrier}.{label}")

class TestCallsBlockedByOpenDefects(unittest.TestCase):
    """Legitimate calls that an open defect still refuses, one bench per defect.

    expectedFailure rather than an exclusion, for the reason 4.1 §2.6 established: an
    exclusion that stays says nothing, while an expectedFailure becomes an unexpected
    success -- and so a red run -- the day its defect closes. One bench per defect, so that
    closing one of the three signals without waiting for the others.
    """

    def _assertGroupSucceeds(self, defect: str) -> None:
        calls: ReadOnlyArray[tuple[str, str]] = next(group for name, group in _BLOCKED if name.startswith(defect))
        tables: dict[str, dict[str, _Call]] = dict(_carriers())

        for carrier, label in calls:
            with self.subTest(defect = defect, carrier = carrier, call = label):
                items, view = _create()
                outcome: Any = _attempt(tables[carrier][label], items, view)

                self.assertNotIsInstance(outcome, Exception, f"{carrier}.{label} refused: {outcome!r}")

    @unittest.expectedFailure
    def test_the_protocol_pop_and_clear_work(self) -> None:
        self._assertGroupSucceeds("D-53")

    @unittest.expectedFailure
    def test_an_empty_range_is_not_a_failure(self) -> None:
        self._assertGroupSucceeds("D-24")

class TestRefusalLeavesNoTrace(unittest.TestCase):
    """A call that refuses must change nothing at all.

    Half of what the five defects did was to refuse and mutate anyway, or to report success
    and mutate half. Asserting the invariant catches an incoherent state; this catches a
    coherent state that is not the one the caller was promised.
    """

    def test_a_refused_call_changes_nothing(self) -> None:
        for label, call in ((name, call) for name, call in _listCalls().items() if name in _REFUSABLE):
            with self.subTest(call = label):
                items, view = _create()
                before: ReadOnlyArray[int] = _snapshot(items)

                _attempt(call, items, view)

                self.assertEqual(_snapshot(items), before, f"{label} changed the content")
                _assertInvariant(self, items, view, label)

class TestWriteRoutesAgree(unittest.TestCase):
    """D-45. One request, three routes, one outcome.

    A positional write is reachable by name, by subscript and by slice. The three went
    through three different implementations, two of which did not maintain the set, so the
    same request landed three different contents. The bench states the equality rather than
    the three behaviours, because that is the property that was missing.
    """

    def __write(self, route: str, key: int, value: int) -> tuple[Any, ReadOnlyArray[int]]:
        items, view = _create()

        match route:
            case "named": outcome: Any = _attempt(lambda o, l: l.SetAt(key, value), items, view)
            case "scalar": outcome = _attempt(lambda o, l: _mutable(l).__setitem__(key, value), items, view)

            case _: outcome = _attempt(lambda o, l: _mutable(l).__setitem__(slice(key, key + 1), [value]), items, view)

        return (outcome, _snapshot(items))

    def test_the_three_routes_land_the_same_content(self) -> None:
        def write(route: str, key: int, value: int) -> ReadOnlyArray[int]:
            return self.__write(route, key, value)[1]

        def assertEqual(route: str, key: int, value: int, named: ReadOnlyArray[int]) -> None:
            self.assertEqual(write(route, key, value), named)

        for key in range(0, len(_CONTENT)):
            for value in _DOMAIN:
                with self.subTest(key = key, value = value):
                    named: ReadOnlyArray[int] = write("named", key, value)

                    assertEqual("scalar", key, value, named)
                    assertEqual("slice", key, value, named)

    def test_every_route_refuses_a_value_the_set_keeps(self) -> None:
        """The refusal is what D-45 lost: the scalar route wrote the duplicate instead."""

        for route in ("named", "scalar", "slice"):
            with self.subTest(route = route):
                outcome, content = self.__write(route, 1, 0)

                self.assertIsInstance(outcome, Exception, f"{route} did not refuse")
                self.assertEqual(content, _CONTENT, f"{route} mutated while refusing")

class TestUnicityCriterion(unittest.TestCase):
    """D-44. The value a position gives up is out of the unicity test.

    It is leaving, so it cannot conflict with the value replacing it. The slice write already
    applied that criterion through the values of the range it overwrites; the scalar write
    refused instead, so setting a position to the value it already held failed.
    """

    def test_a_position_accepts_the_value_it_already_holds(self) -> None:
        for key in range(0, len(_CONTENT)):
            with self.subTest(key = key):
                items, view = _create()

                self.assertTrue(view.TrySetAt(key, view.GetAt(key)))
                _assertInvariant(self, items, view, f"TrySetAt({key}, GetAt({key}))")

    def test_a_position_refuses_a_value_another_position_holds(self) -> None:
        """The other half: the criterion excludes the value that leaves, not every value the
        set already admits. A bench on the first half alone would pass on a write that had no
        unicity test at all."""

        for key in range(0, len(_CONTENT)):
            for other in range(0, len(_CONTENT)):
                if other == key: continue

                with self.subTest(key = key, other = other):
                    items, view = _create()

                    self.assertFalse(view.TrySetAt(key, view.GetAt(other)))
                    self.assertEqual(_snapshot(items), _CONTENT)

    def test_the_criterion_excludes_by_identity_and_not_only_by_equality(self) -> None:
        """A value never equal to itself -- float('nan') is one, and it is hashable, so an
        ordered set may legitimately hold it -- is still the value the position gives up.
        An inequality test refuses it; a membership test, which carries an identity shortcut,
        does not."""

        nan: float = float("nan")
        items: IOrderedSet[float] = CreateOrderedSet((nan,))
        view: IList[float] = items.AsList()

        self.assertFalse(nan == nan)
        self.assertTrue(items.Contains(nan))
        self.assertTrue(view.TrySetAt(0, nan), "a position refused the very object it holds")
        self.assertEqual(items.GetCount(), 1)

class TestRangeUnicityCriterion(unittest.TestCase):
    """D-60. A range that carries the same value twice is refused, not deduplicated.

    The set the view maintains answers only that none of the values was already held, and a
    set given a duplicated range keeps one of the two -- measured: TryAddRange((7, 7)) on the
    inner set answers True and grows it by one. The view read that boolean as permission to
    insert every value, so the order took two 7s where the set took one and the unicity clause
    fell on a True answer: TryInsertRange(1, (7, 7)) on CreateOrderedSet((1, 2, 3, 4)).AsList()
    answered True and left the order (1, 7, 7, 2, 3, 4) against a count of 6.

    The slice route already refused the same range, through SetOrderedValues. So the two
    routes are asserted together rather than each on its own: what one type refuses by one
    door it cannot accept by another, and it was the disagreement between the doors that
    made the defect visible.
    """

    __DUPLICATED: ReadOnlyArray[int] = (7, 7)

    def test_the_range_route_refuses_a_duplicated_range(self) -> None:
        """None rather than False: the house mapping makes False an empty range, which is the
        one answer the non-Try form is bound to let pass, so answering it would put a refused
        range back in silently -- the shape D-57 closed on."""

        items, view = _create()

        self.assertIsNone(view.TryInsertRange(1, list(self.__DUPLICATED)))
        self.assertEqual(_snapshot(items), _CONTENT, "the refusal mutated the order")
        _assertInvariant(self, items, view, "TryInsertRange(1, [7, 7])")

    def test_the_throwing_range_route_raises(self) -> None:
        """InsertRange is final on IList and raises on None alone, so the trivalent answer is
        what makes the non-Try route refuse at all."""

        items, view = _create()

        with self.assertRaises(IndexError): view.InsertRange(1, list(self.__DUPLICATED))

        self.assertEqual(_snapshot(items), _CONTENT)

    def test_the_slice_route_refuses_the_same_range(self) -> None:
        """The precedent the range route was made to match, asserted here so that the two
        cannot drift apart unnoticed."""

        items, view = _create()

        with self.assertRaises(ValueError): _mutable(view).__setitem__(slice(0, 2), list(self.__DUPLICATED))

        self.assertEqual(_snapshot(items), _CONTENT)

    def test_a_one_pass_range_carrying_a_duplicate_is_refused(self) -> None:
        """The unicity pass reads the buffer, not the caller's iterable. A pass that consumed
        the iterable instead would leave the set's own pass nothing to read, and the range
        would go in empty -- which is D-42's shape, not a refusal."""

        items, view = _create()

        self.assertIsNone(view.TryInsertRange(1, iter(self.__DUPLICATED)))
        self.assertEqual(_snapshot(items), _CONTENT)
        _assertInvariant(self, items, view, "TryInsertRange(1, iter([7, 7]))")

    def test_a_range_with_no_internal_duplicate_still_inserts(self) -> None:
        """The counter-example. A unicity pass that refused any range of more than one item
        would satisfy every clause above."""

        items, view = _create()

        self.assertTrue(view.TryInsertRange(1, [7, 8]))
        self.assertEqual(_snapshot(items), (0, 7, 8, 1, 2))
        _assertInvariant(self, items, view, "TryInsertRange(1, [7, 8])")

    def test_an_empty_range_is_not_a_refusal(self) -> None:
        """The other counter-example, and the reason the answer is trivalent: an empty range
        is nothing to do, which False says and None would not."""

        items, view = _create()

        self.assertIs(view.TryInsertRange(1, []), False)
        self.assertEqual(_snapshot(items), _CONTENT)

class TestOrderedSetRangeUnicityCriterion(unittest.TestCase):
    """D-60's second site: the same defect on the ordered set's own range add.

    TryAddRange read the set's boolean exactly as the list view did, 250 lines above in the
    same file: it hands `items` to the set, which keeps one of the two 7s and reports that it
    grew, and then to the order, which takes both. Measured before the fix on
    CreateOrderedSet((1, 2, 3, 4)): TryAddRange((7, 7)) answered True and left
    (1, 2, 3, 4, 7, 7) against a count of 6. AddRange, AddValues and TryAddValues reach it
    too, being final wrappers over it, so all four are asserted rather than the one.

    The question is asked by the same helper the view uses, so the two sites cannot answer it
    differently. What they may differ on is how they say no: ISetBase.TryAddRange is bivalent
    by contract and AddRange raises on the False alone, so this family cannot tell a refused
    range from an empty one. That conflation is D-24's open complaint against the set family,
    not something this closes, which is why no clause here reads the empty range's answer.
    """

    def test_every_range_route_refuses_a_duplicated_range(self) -> None:
        calls: ReadOnlyArray[tuple[str, _Call, bool]] = (
            ("TryAddRange([7, 7])", lambda o, l: o.TryAddRange([7, 7]), False),
            ("AddRange([7, 7])", lambda o, l: o.AddRange([7, 7]), True),
            ("TryAddValues(7, 7)", lambda o, l: o.TryAddValues(7, 7), False),
            ("AddValues(7, 7)", lambda o, l: o.AddValues(7, 7), True))

        for label, call, raises in calls:
            with self.subTest(call = label):
                items, view = _create()
                outcome: Any = _attempt(call, items, view)

                # KeyError is what ISetBase.AddRange raises on a False, so the throwing forms
                # are held to that one and not merely to "something was raised".
                if raises: self.assertIsInstance(outcome, KeyError, f"{label} did not refuse: {outcome!r}")
                else: self.assertIs(outcome, False, f"{label} answered {outcome!r}")

                self.assertEqual(_snapshot(items), _CONTENT, f"{label} mutated while refusing")
                _assertInvariant(self, items, view, f"set.{label}")

    def test_a_range_with_no_internal_duplicate_still_goes_in(self) -> None:
        """The counter-example. A pass that refused every range of more than one value, or
        every range at all, would satisfy the clause above."""

        items, view = _create()

        self.assertTrue(items.TryAddRange([7, 8]))
        self.assertEqual(_snapshot(items), (0, 1, 2, 7, 8))
        _assertInvariant(self, items, view, "set.TryAddRange([7, 8])")

    def test_the_two_sites_agree(self) -> None:
        """The disagreement between the doors is what made D-60 visible in the first place, so
        it is the agreement that is asserted, not the two behaviours. Neither route may take a
        range the other refuses."""

        for label, carry in (("[7, 7]", (7, 7)), ("[7, 8]", (7, 8)), ("[7, 0]", (7, 0))):
            with self.subTest(range = label):
                setItems, _ = _create()
                viewItems, view = _create()

                refusedBySet: bool = _attempt(lambda o, l: o.TryAddRange(list(carry)), setItems, _) is not True
                refusedByView: bool = _attempt(lambda o, l: l.TryInsertRange(1, list(carry)), viewItems, view) is not True

                self.assertEqual(refusedBySet, refusedByView,
                                 f"{label}: the set route refused {refusedBySet} where the view route refused {refusedByView}")

class TestWriteReplacesInBothContainers(unittest.TestCase):
    """The design decision D-44 and D-45 were closed on, which nothing else would catch.

    A positional write replaces the object in the order AND in the set, so the two hold the
    same object rather than two that merely compare equal. Every positional write in the
    framework writes, and the slice write of this very type replaces in both -- so the scalar
    write conforms. Replacing in the order alone passes every other bench in this module,
    which is why this one exists.

    The set is private and holds no public accessor to its elements, so it is reached by type
    rather than by name, the way the revocable-view benches count cookies.
    """

    class _Value:
        """Equal and hashable on `id`; `tag` is payload the equality ignores."""

        def __init__(self, id: int, tag: str) -> None:
            self.id: int = id
            self.tag: str = tag

        def __eq__(self, other: object) -> bool: return isinstance(other, TestWriteReplacesInBothContainers._Value) and other.id == self.id
        def __hash__(self) -> int: return hash(self.id)
        def __repr__(self) -> str: return f"{self.id}{self.tag}"

    def __heldBy(self, items: object, value: Any) -> Any:
        """The object the inner set holds for `value`, or None if it holds no such object.

        The set is private and no member of either type returns an element taken from it, so
        it is reached by type, the way the revocable-view benches reach cookies by name. The
        walk is reflective by necessity, so pyright cannot type what it traverses; only one
        element leaves this method, which keeps the unknown confined to the walk.
        """

        seen: set[int] = set[int]()
        stack: list[object] = [items]

        while len(stack) > 0:
            current: object = stack.pop()

            if id(current) in seen: continue

            seen.add(id(current))

            elements: ReadOnlyArray[Any] = _setElements(current)

            if len(elements) > 0:
                for element in elements:
                    if element == value: return element

                return None
            
            if hasattr(current, "__dict__"): stack.extend(vars(current).values())

        self.fail("the inner set was not reachable: this bench needs rewriting, not disabling")

    def test_a_write_replaces_the_object_in_the_set_too(self) -> None:
        routes: ReadOnlyArray[tuple[str, Callable[[IList[Any], Any], Any]]] = (
            ("named", lambda v, x: v.SetAt(1, x)),
            ("scalar", lambda v, x: _mutable(v).__setitem__(1, x)),
            ("slice", lambda v, x: _mutable(v).__setitem__(slice(1, 2), [x])))

        for route, write in routes:
            with self.subTest(route = route):
                values: ReadOnlyArray[Any] = tuple(TestWriteReplacesInBothContainers._Value(i, "a") for i in range(3))
                replacement: Any = TestWriteReplacesInBothContainers._Value(1, "b")

                items: IOrderedSet[Any] = CreateOrderedSet(values)
                view: IList[Any] = items.AsList()

                # The write goes through _attempt: a route that refuses must read as this
                # bench failing with its reason, not as it erroring out on the exception.
                outcome: Any = _attempt(lambda o, l: write(view, replacement), items, view)

                self.assertNotIsInstance(outcome, Exception, f"{route}: the write was refused ({outcome!r})")
                self.assertIs(view.GetAt(1), replacement, f"{route}: the order kept the old object")

                held: Any = self.__heldBy(items, replacement)

                self.assertIsNotNone(held, f"{route}: the set no longer admits the value at all")
                self.assertIs(held, replacement, f"{route}: the set kept the old object")

class TestOrderedSetAddRangeIsSinglePass(unittest.TestCase):
    """Open defect: the residual of D-42, on the ordered set's own TryAddRange.

    TryAddRange never buffers, so the first pass over a one-pass iterable consumes it and the
    order never receives the values. The list view was corrected by buffering; the set itself
    was not, 250 lines above in the same file.

    D-60 moved where that consumption happens without closing this, so the symptom this
    bench reads is not the one it was written against. Measured after D-60:
    TryAddRange(iter([7, 8])) answers False and leaves (0, 1, 2) with Contains(7) false,
    where before it answered True and left the set admitting values the order did not carry.
    The phantom is gone and the refusal is now clean, but the range still does not go in,
    which is the clause below and why this stays open. Buffering here would close it, and
    would also turn this bench into an unexpected success, so it is a decision to take on its
    own rather than a side effect of D-60.

    This is expectedFailure rather than an exclusion because it must signal when the defect
    is closed, which an exclusion would not: an exclusion that stays says nothing.
    """

    @unittest.expectedFailure
    def test_a_one_pass_iterable_reaches_the_order(self) -> None:
        def getCall(methodName: str, actionProvider: Converter[Iterator[int], Converter[IOrderedSet[int], Any]]) -> tuple[str, Converter[IOrderedSet[int], Any]]:
            return (methodName, actionProvider(iter([7, 8])))

        calls: ReadOnlyArray[tuple[str, Converter[IOrderedSet[int], Any]]] = (
            getCall("TryAddRange", lambda values: lambda o: o.TryAddRange(values)),
            getCall("AddRange", lambda values: lambda o: o.AddRange(values)))

        for label, call in calls:
            with self.subTest(call = label):
                items: IOrderedSet[int] = CreateOrderedSet(_CONTENT)

                call(items)

                self.assertEqual(_snapshot(items), (0, 1, 2, 7, 8), f"{label} lost the values")
                self.assertTrue(items.Contains(7))
