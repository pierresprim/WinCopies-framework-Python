"""
The Python path against Python.

A framework collection is reached by two paths, each with a contract of its own (3.7 §1, Pierre).
The framework's methods are strict: GetAt, SetAt, RemoveAt and Insert take a position as it is,
refuse a negative one, and count from the end only when asked to, through ReverseIndex. The
Python protocol -- l[i], l[i] = x, del l[i], insert, pop, in -- follows Python instead: a negative
index counts from the end, one outside the sequence raises IndexError, and insert brings its index
back inside the sequence as list.insert does.

So the benches here compare the Python path of every carrier against a Python list holding what
the carrier reads, and the reference is computed, never written by hand. D-53 was the Python path
refusing a negative index; D-79, a converting list writing its own values into its source without
converting them back; D-80, a converting collection answering `in` by asking itself again.
"""

import contextlib
import sys
import unittest
from collections.abc import Iterator
from typing import Any, Callable
from unittest import mock

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstract.Collection import TupleCollectionAbstractBase, Tuple as ConvertingTuple, List as ConvertingList
from WinCopies.Collections.Abstraction.Collection import CreateArray, CreateList, CreateSortedList, CreateTuple, TryCreateSizedList
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Abstraction.Selection import Converters
from WinCopies.Collections.Abstraction.Selection.Collection import List as SelectionList
import WinCopies.Collections.Range as RangeModule
from WinCopies.Collections.Circular import CircularList, CircularTuple
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Extensions import IDefaultMutableSequence
from WinCopies.Collections.ObjectModel.Collection import ObservableCollection

type _Factory = Callable[[], Any]
type _Act = Callable[[Any], Any]

class _ConvertingTuple(ConvertingTuple[int, str]):
    """Read-only converter over an inner tuple of ints, as in Registry.py."""

    def _Clone(self, items: Any) -> "_ConvertingTuple": return _ConvertingTuple(items)

    def _Convert(self, item: int) -> str: return str(item)

    def GetMutability(self) -> Mutability: return Mutability.ReadOnly

class _ConvertingList(ConvertingList[int, str], IDefaultMutableSequence[str]):
    """Two-way converter over an inner list of ints, as in Registry.py."""

    def _Clone(self, items: Any) -> "_ConvertingList": return _ConvertingList(items)

    def _Convert(self, item: int) -> str: return str(item)
    def _ConvertBack(self, item: str) -> int: return int(item)

    def GetMutability(self) -> Mutability: return Mutability.Mutable

def _sizedList(capacity: int, content: list[int]|None = None) -> Any:
    items: Any = TryCreateSizedList(capacity, [0, 1, 2] if content is None else content)

    assert items is not None

    return items

_CARRIERS: ReadOnlyArray[tuple[str, _Factory, tuple[Any, Any], tuple[bool, bool, bool]]] = (
    ("List",                               lambda: CreateList([0, 1, 2]),                                                      (7, 9),     (True,  True,  True)),
    ("List, empty",                        lambda: CreateList(list[int]()),                                                    (7, 9),     (True,  True,  True)),
    ("SizedList, spare capacity",          lambda: _sizedList(5),                                                              (7, 9),     (True,  True,  True)),
    ("SizedList, full",                    lambda: _sizedList(3),                                                              (7, 9),     (True,  True,  False)),
    ("ObservableCollection",               lambda: ObservableCollection[int](CreateList([0, 1, 2])),                          (7, 9),     (True,  True,  True)),
    ("List.AsReversed()",                  lambda: CreateList([2, 1, 0]).AsReversed(),                                         (7, 9),     (True,  True,  True)),
    ("OrderedSet.AsList()",                lambda: CreateOrderedSet([0, 1, 2]).AsList(),                                       (7, 9),     (True,  True,  True)),
    ("OrderedSet.AsList().AsReversed()",   lambda: CreateOrderedSet([2, 1, 0]).AsList().AsReversed(),                          (7, 9),     (True,  True,  True)),
    ("Selection.List",                     lambda: SelectionList[int, int](CreateList([0, 1, 2]), Converters[int, int](int, int)), (7, 9), (True,  True,  True)),
    ("converting list, int to str",        lambda: _ConvertingList(CreateList([0, 1, 2])),                                     ("7", "9"), (True,  True,  True)),
    ("CircularList, start 1",              lambda: CircularList[int](CreateList([2, 0, 1]), 1),                                (7, 9),     (True,  True,  True)),
    ("CircularList over a full SizedList", lambda: CircularList[int](_sizedList(3, [2, 0, 1]), 1),                             (7, 9),     (True,  True,  False)),
    ("CircularList over OrderedSet.AsList()", lambda: CircularList[int](CreateOrderedSet([2, 0, 1]).AsList(), 1),              (7, 9),     (True,  True,  True)),
    ("CircularList.AsReversed()",          lambda: CircularList[int](CreateList([1, 0, 2]), 2).AsReversed(),                   (7, 9),     (True,  True,  True)),
    ("CreateArray",                        lambda: CreateArray([0, 1, 2]),                                                     (7, 9),     (False, False, False)),
    ("List.AsReadOnly()",                  lambda: CreateList([0, 1, 2]).AsReadOnly(),                                         (7, 9),     (False, False, False)),
    ("List.AsImmutable()",                 lambda: CreateList([0, 1, 2]).AsImmutable(),                                        (7, 9),     (False, False, False)),
    ("CircularTuple, start 1",             lambda: CircularTuple[int](CreateList([2, 0, 1]).AsImmutable(), 1),                (7, 9),     (False, False, False)),
    ("CircularList.AsReadOnly()",          lambda: CircularList[int](CreateList([2, 0, 1]), 1).AsReadOnly(),                   (7, 9),     (False, False, False)),
    ("converting tuple, int to str",       lambda: _ConvertingTuple(CreateTuple([0, 1, 2])),                                   ("7", "9"), (False, False, False)),
    ("CreateTuple",                        lambda: CreateTuple([0, 1, 2]),                                                     (7, 9),     (False, False, False)),
    ("CreateSortedList",                   lambda: CreateSortedList([0, 1, 2]),                                                (7, 9),     (False, False, False)),
    ("SizedList.SliceAt(0:3)",             lambda: _sizedList(5).SliceAt(slice(0, 3)),                                         (7, 9),     (False, False, False)))
"""Every carrier of the Python path at hand, reading (0, 1, 2) unless empty, with the value it writes
and the one it inserts, and what its Python path offers: item assignment, removal (del and pop),
insertion. A full SizedList removes but cannot insert; an array, read-only views and tuples offer
reading only, an array having no item assignment on its Python path. The eleven lists of
Contract.py are here, with a circular list's reversed view, converting collections, and the
tuples that delegate to a Python sequence."""

def _sequence(carrier: Any) -> Any:
    """The carrier's Python face: its mutable sequence where it has one, its sequence otherwise."""

    return carrier.AsMutableSequence() if hasattr(carrier, "AsMutableSequence") else carrier.AsSequence()

def _at(act: Callable[[Any, int], Any], index: int) -> _Act:
    return lambda sequence: act(sequence, index)

def _scalarChanges(count: int, values: tuple[Any, Any], offers: tuple[bool, bool, bool]) -> Iterator[tuple[str, _Act]]:
    """Every scalar use of the Python path on a carrier of `count` items: indices from two before
    the start to one past the end, so that a negative one falls inside, at the edge and outside;
    insert from three before to two past, since insert brings an index back inside the sequence."""

    value, inserted = values
    writes, removes, inserts = offers

    for index in range(-count - 2, count + 2):
        yield (f"l[{index}]", _at(lambda l, i: l[i], index))

        if writes: yield (f"l[{index}] = {value!r}", _at(lambda l, i: l.__setitem__(i, value), index))

        if removes:
            yield (f"del l[{index}]", _at(lambda l, i: l.__delitem__(i), index))
            yield (f"l.pop({index})", _at(lambda l, i: l.pop(i), index))

    if removes: yield ("l.pop()", lambda l: l.pop())

    if inserts:
        for index in range(-count - 3, count + 3): yield (f"l.insert({index}, {inserted!r})", _at(lambda l, i: l.insert(i, inserted), index))

def _outcome(sequence: Any, act: _Act, read: Callable[[], list[Any]]) -> str:
    """What a use answers and leaves: the type of what it raises, or its result and the content."""

    try: answer: Any = act(sequence)
    except Exception as exception: return type(exception).__name__

    return f"{answer!r} {read()}"

def _scalarCases() -> Iterator[tuple[str, str, _Factory, _Act]]:
    for name, factory, values, offers in _CARRIERS:
        for label, act in _scalarChanges(factory().GetCount(), values, offers): yield (name, label, factory, act)

def _divergeScalar(factory: _Factory, act: _Act) -> str|None:
    model: list[Any] = list(factory().AsIterable())
    expected: str = _outcome(model, act, lambda: model)
    carrier: Any = factory()
    actual: str = _outcome(_sequence(carrier), act, lambda: list(carrier.AsIterable()))

    return None if actual == expected else f"gives {actual}; Python gives {expected}"

class TestAScalarIndexIsResolvedAsPythonDoes(unittest.TestCase):
    """D-53, closed: the Python path refused a negative scalar index, raised KeyError for one out of
    range, and insert refused an index that list.insert brings back inside the sequence."""

    def test_every_scalar_use_matches_python(self) -> None:
        for name, label, factory, act in _scalarCases():
            with self.subTest(carrier = name, use = label):
                divergence: str|None = _divergeScalar(factory, act)

                self.assertIsNone(divergence, f"{name}, {label}: {divergence}")

    def test_the_framework_path_stays_strict(self) -> None:
        """The other path is unchanged: a negative position is refused, by raising or by answering."""

        def refuses(act: _Act) -> bool:
            try: return act(CreateList([0, 1, 2])) in (False, None)
            except (IndexError, KeyError): return True

        uses: ReadOnlyArray[tuple[str, _Act]] = (
            ("GetAt(-1)",        lambda l: l.GetAt(-1)),
            ("SetAt(-1, 7)",     lambda l: l.SetAt(-1, 7)),
            ("RemoveAt(-1)",     lambda l: l.RemoveAt(-1)),
            ("TryRemoveAt(-1)",  lambda l: l.TryRemoveAt(-1)),
            ("Insert(-1, 9)",    lambda l: l.Insert(-1, 9)),
            ("TryInsert(-1, 9)", lambda l: l.TryInsert(-1, 9)))

        for label, act in uses:
            with self.subTest(use = label): self.assertTrue(refuses(act), f"{label} took a negative position")

_KEYS: ReadOnlyArray[int|slice] = (*range(-4, 4), *(slice(first, last, step) for first in (None, 0, 1, -1) for last in (None, 2, -1) for step in (None, 1, 2, -1)))
"""Every scalar index of a three-item list and one past either end, and slices with every kind of
bound and step."""

def _divergeConverted(key: int|slice) -> str|None:
    source: Any = CreateList([0, 1, 2])
    view: Any = _ConvertingList(source)
    value: Any = "7" if isinstance(key, int) else [str(70 + offset) for offset in range(len(range(*key.indices(3))))]
    model: list[Any] = list(view.AsIterable())
    expected: list[Any]|str

    try:
        model[key] = value
        expected = model
    except Exception as exception: expected = type(exception).__name__

    try: view.AsMutableSequence()[key] = value
    except Exception as exception: return None if type(exception).__name__ == expected else f"raised {exception!r}; Python gives {expected}"

    content: list[Any] = list(view.AsIterable())
    inner: list[Any] = list(source.AsIterable())

    if content != expected: return f"reads {content}; Python gives {expected}"

    return None if all(type(item) is int for item in inner) else f"left {inner} in its source"

class TestAConvertingListWritesConvertedValues(unittest.TestCase):
    """D-79, closed: item and slice assignment on a converting list wrote the view's own values into
    its source, without converting them back. The view could not show it, reading str('7') back as
    '7': over a source of ints, c[0] = '7' left ['7', 1, 2] there."""

    def test_every_assignment_matches_python_and_converts_back(self) -> None:
        for key in _KEYS:
            with self.subTest(key = key):
                divergence: str|None = _divergeConverted(key)

                self.assertIsNone(divergence, f"c[{key}] = ...: {divergence}")

_MEMBERS: ReadOnlyArray[tuple[str, _Factory, ReadOnlyArray[Any]]] = (
    ("converting list, int to str",  lambda: _ConvertingList(CreateList([0, 1, 2])),   ("1", "9", 1)),
    ("converting tuple, int to str", lambda: _ConvertingTuple(CreateTuple([0, 1, 2])), ("1", "9", 1)),
    ("Selection.List",               lambda: SelectionList[int, int](CreateList([0, 1, 2]), Converters[int, int](int, int)), (1, 9, "1")))
"""Converting collections, each asked for an item it holds, one it does not, and one of the source's
type or the view's that it does not hold either."""

class TestAConvertingCollectionAnswersMembership(unittest.TestCase):
    """D-80, closed: Contains asked `value in self.AsSequence()`, and the sequence is the collection
    itself, whose __contains__ asks Contains again. Contains and `in` raised RecursionError on every
    converting collection, Selection.List among them."""

    def test_contains_and_in_match_python(self) -> None:
        for name, factory, values in _MEMBERS:
            for value in values:
                with self.subTest(carrier = name, value = value):
                    collection: Any = factory()
                    expected: bool = value in list(collection.AsIterable())

                    self.assertIs(collection.Contains(value), expected, f"{name}.Contains({value!r})")
                    self.assertIs(value in collection.AsSequence(), expected, f"{value!r} in {name}")

def _run(bench: unittest.TestCase|unittest.TestSuite, failfast: bool = False) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    result.failfast = failfast

    unittest.TestSuite((bench,)).run(result)

    return result

def _fell(result: unittest.TestResult) -> int:
    return len(result.failures) + len(result.errors)

def _everywhere(name: str, replacement: Any) -> contextlib.ExitStack:
    """Replaces a function in every framework module that imported it, since each holds its own
    reference."""

    stack: contextlib.ExitStack = contextlib.ExitStack()

    for module in list(sys.modules.values()):
        if getattr(module, "__name__", "").startswith("WinCopies.") and name in vars(module): stack.enter_context(mock.patch.object(module, name, replacement))

    return stack

def _refusal(act: _Act, target: Any) -> str:
    try: act(target)
    except Exception as exception: return f"{type(exception).__name__}: {exception}"

    return "no refusal"

def _zeroStepCalls(offers: tuple[bool, bool, bool]) -> Iterator[tuple[str, _Act]]:
    yield ("l[::0]", lambda s: s[::0])

    if offers[0]: yield ("l[::0] = []", lambda s: s.__setitem__(slice(None, None, 0), []))
    if offers[1]: yield ("del l[::0]", lambda s: s.__delitem__(slice(None, None, 0)))

class TestAZeroStepIsRefusedAsPythonDoes(unittest.TestCase):
    """D-86, closed: a zero step was refused with a bare IndexError by the assignment and the deletion
    of a slice, under a docstring that said it was refused as CPython refuses it; CPython raises
    ValueError("slice step cannot be zero"). Reading such a slice already raised ValueError, from
    slice.indices, so only the writes diverged."""

    def test_every_carrier_refuses_a_zero_step_as_python_does(self) -> None:
        for carrier, factory, _, offers in _CARRIERS:
            for label, act in _zeroStepCalls(offers):
                with self.subTest(carrier = carrier, call = label):
                    items: Any = factory()
                    before: list[Any] = list(items.AsIterable())

                    self.assertEqual(_refusal(act, _sequence(items)), _refusal(act, list(before)), f"{carrier}, {label}")
                    self.assertEqual(list(items.AsIterable()), before, f"{carrier}, {label} changed the content while refusing")

class TestTheProtocolBenchesCanFail(unittest.TestCase):
    """Each bench is run against the framework rebuilt with the defect it guards: green on the
    intact tree, red on the rebuilt one. A run that only has to show a bench falls stops at its
    first failure."""

    def _assertFalls(self, bench: Callable[[], unittest.TestCase], rebuild: Callable[[], contextlib.AbstractContextManager[Any]], what: str) -> None:
        self.assertEqual(_fell(_run(bench())), 0, f"the {what} bench is expected to pass on the intact tree")

        with rebuild(): broken: unittest.TestResult = _run(bench(), True)

        self.assertGreater(_fell(broken), 0, f"the {what} bench did not fall on the rebuilt tree")

    def test_the_scalar_bench_falls_when_the_index_is_taken_as_it_is(self) -> None:
        """Taking the index as it is, as both resolutions did before, rebuilds D-53."""

        def asItIs(index: Any, length: int) -> int: return int(index)

        def rebuild() -> contextlib.ExitStack:
            stack: contextlib.ExitStack = _everywhere("GetSequenceIndex", asItIs)

            stack.enter_context(_everywhere("GetSequenceInsertionIndex", asItIs))

            return stack

        self._assertFalls(lambda: TestAScalarIndexIsResolvedAsPythonDoes("test_every_scalar_use_matches_python"), rebuild, "scalar")

    def test_the_conversion_bench_falls_when_the_value_is_written_as_it_is(self) -> None:
        """Writing the view's value into the source as it is rebuilds D-79."""

        def asItIs(self: Any, index: Any, value: Any) -> None: self._GetContainer().AsMutableSequence()[index] = value

        target: Any = ConvertingList

        self._assertFalls(lambda: TestAConvertingListWritesConvertedValues("test_every_assignment_matches_python_and_converts_back"),
                          lambda: mock.patch.object(target, "__setitem__", asItIs), "conversion")

    def test_the_membership_bench_falls_when_contains_asks_itself(self) -> None:
        """Asking `in` of the collection itself rebuilds D-80."""

        def asksItself(self: Any, value: Any) -> bool: return value in self.AsSequence()

        target: Any = TupleCollectionAbstractBase

        self._assertFalls(lambda: TestAConvertingCollectionAnswersMembership("test_contains_and_in_match_python"),
                          lambda: mock.patch.object(target, "Contains", asksItself), "membership")

    def test_the_zero_step_bench_falls_when_a_zero_step_raises_a_bare_index_error(self) -> None:
        """The refusal of a zero step as it stood until D-86."""

        def bare() -> Any: raise IndexError()

        self._assertFalls(lambda: TestAZeroStepIsRefusedAsPythonDoes("test_every_carrier_refuses_a_zero_step_as_python_does"),
                          lambda: mock.patch.object(RangeModule, "ThrowZeroStepError", bare), "zero step")
