"""
Conformance of the circular list to a model of what it means.

A circular list reads its container from a start and wraps around: over (2, 0, 1) with start 1
it reads (0, 1, 2). Every structural change therefore has two parts, the change to the container
and the change to the start, and the second is the one that went wrong. D-71 left the start where
it was after an insertion before the physical head, D-72 left it past the count after a first
insertion into an empty source, and D-73 left it in place after a removal before the head. Each
was invisible to any bench that read one carrier at one start, because the content comes out
right whenever the position lands after the head.

So the benches here compare every insertion and every removal, at every logical index and every
start, against a Python list holding the logical content. The reference is computed, never
written by hand.

The start is a physical position in the source (3.6 §5, Pierre: "Je confirme (A), sans
réécriture"). A source changed by another path can leave it past the count; the list then reads,
and must write, from that position reduced modulo the count, and a read never stores the reduced
value back. D-76 was the writes disagreeing with the reads there. So the second grid changes the
source directly before every change of the list, and the model is what the list reads at that
point. An insertion or a removal through the list, unlike a read, writes a start inside the
container: a source then growing past its end leaves the start where it was, which both grids
assert.

A third grid goes through the Python protocol instead of the framework's methods: item and slice
assignment and deletion, against a Python list. The Python path is a path of its own, with its own
contract (3.7 §1), and D-78 lived there unseen by the two grids above: the list converted the
logical index twice.

The last benches cover D-75: a circular type's immutable view is revoked by whatever changes what
the list reads, and by nothing else.
"""

import gc
import unittest
import weakref
from collections.abc import Iterator
from typing import Any, Callable
from unittest import mock

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import CreateList, TryCreateSizedList
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Circular import CircularAbstract, CircularList, CircularTuple
from WinCopies.Collections.Range import RemoveItems, SetItems
from WinCopies.Typing.Discard import InvalidatedError

type _Act = Callable[[Any], Any]
type _Model = Callable[[list[int]], Any]
type _Foreign = Callable[[Any], Any]

_SIZES: range = range(0, 5)
"""Sources of zero to four items: the empty one, one where every position is the head, and enough
others that a position falls before, at and after the head for some start."""

def _logical(start: int, items: ReadOnlyArray[int]) -> list[int]:
    count: int = len(items)

    return [items[(start + offset) % count] for offset in range(count)]

def _at(act: Callable[[Any, Any], Any], model: Callable[[list[int], Any], Any], argument: Any) -> tuple[_Act, _Model]:
    """One change and its model, closed over one argument: an index, a value or a count."""

    return (lambda circular: act(circular, argument), lambda items: model(items, argument))

def _bind(act: Callable[[Any, Any], Any], argument: Any) -> _Foreign:
    """One change closed over one argument: a position, a position and a count, or a slice."""

    return lambda source: act(source, argument)

def _chain(*steps: Callable[[Any], Any]) -> Callable[[Any], None]:
    """Several changes applied in order to one carrier, the circular list or the model."""

    def run(target: Any) -> None:
        for step in steps: step(target)

    return run

def _emptiedThenAdded(count: int) -> tuple[_Act, _Model]:
    """Every item removed, then one added: the start must come back inside a count of one."""

    return (_chain(lambda c: c.RemoveRange(0, count), lambda c: c.Add(9)), _chain(lambda l: l.clear(), lambda l: l.append(9)))

def _changes(view: list[int]) -> Iterator[tuple[str, _Act, _Model]]:
    """Every structural change the circular list exposes, with the same change on the model, for a
    list that reads `view`: insertions at every logical index including the append position, and
    removals at every logical index, by position and by value."""

    for index in range(len(view) + 1):
        yield (f"Insert({index}, 9)", *_at(lambda c, i: c.Insert(i, 9), lambda l, i: l.insert(i, 9), index))
        yield (f"TryInsert({index}, 9)", *_at(lambda c, i: c.TryInsert(i, 9), lambda l, i: l.insert(i, 9), index))
        yield (f"InsertRange({index}, [8, 9])", *_at(lambda c, i: c.InsertRange(i, [8, 9]), lambda l, i: l.__setitem__(slice(i, i), [8, 9]), index))
        yield (f"TryInsertRange({index}, [8, 9])", *_at(lambda c, i: c.TryInsertRange(i, [8, 9]), lambda l, i: l.__setitem__(slice(i, i), [8, 9]), index))

    yield ("Add(9)", lambda c: c.Add(9), lambda l: l.append(9))
    yield ("TryAdd(9)", lambda c: c.TryAdd(9), lambda l: l.append(9))
    yield ("AddRange([8, 9])", lambda c: c.AddRange([8, 9]), lambda l: l.extend([8, 9]))

    for index in range(len(view)):
        yield (f"RemoveAt({index})", *_at(lambda c, i: c.RemoveAt(i), lambda l, i: l.pop(i), index))
        yield (f"TryRemoveAt({index})", *_at(lambda c, i: c.TryRemoveAt(i), lambda l, i: l.pop(i), index))
        yield (f"RemoveRange({index}, 1)", *_at(lambda c, i: c.RemoveRange(i, 1), lambda l, i: l.pop(i), index))
        yield (f"Remove(value at {index})", *_at(lambda c, v: c.Remove(v), lambda l, v: l.remove(v), view[index]))

def _cases() -> Iterator[tuple[str, ReadOnlyArray[int], int, _Act, _Model]]:
    """Every change of `_changes`, at every start of every size, and three sequences that start from
    or return to an empty source, which is where the start has nowhere valid to point."""

    for size in _SIZES:
        items: ReadOnlyArray[int] = tuple(range(size))

        for start in range(max(size, 1)):
            for label, act, model in _changes(_logical(start, items)): yield (label, items, start, act, model)

            yield ("Add(9), then Insert(0, 7)", items, start,
                   _chain(lambda c: c.Add(9), lambda c: c.Insert(0, 7)), _chain(lambda l: l.append(9), lambda l: l.insert(0, 7)))
            yield ("Add(8), Add(9), then RemoveAt(0)", items, start,
                   _chain(lambda c: c.Add(8), lambda c: c.Add(9), lambda c: c.RemoveAt(0)), _chain(lambda l: l.extend([8, 9]), lambda l: l.pop(0)))

            if size > 0: yield ("RemoveRange(0, all), then Add(9)", items, start, *_emptiedThenAdded(size))

def _foreignChanges(size: int) -> Iterator[tuple[str, _Foreign]]:
    """Changes of a source of `size` items by another path than the circular list: removals that
    shrink it, down to empty, which is what leaves the start past the count; and insertions at every
    position and an append, which move what the list reads without leaving it out of bounds."""

    for position in range(size):
        yield (f"src.RemoveAt({position})", _bind(lambda s, p: s.RemoveAt(p), position))

        for count in range(2, size - position + 1): yield (f"src.RemoveRange({position}, {count})", _bind(lambda s, r: s.RemoveRange(*r), (position, count)))

    for position in range(size + 1): yield (f"src.Insert({position}, 7)", _bind(lambda s, p: s.Insert(p, 7), position))

    yield ("src.Add(7)", lambda s: s.Add(7))

def _overChangedSource(size: int, start: int, foreign: _Foreign) -> Any:
    source: Any = CreateList(list(range(size)))
    circular: Any = CircularList[int](source, start)

    foreign(source)

    return circular

def _foreignCases() -> Iterator[tuple[str, int, int, _Foreign, _Act, _Model]]:
    """Every change of the source by another path, then every change of `_changes` on the list."""

    for size in _SIZES:
        for start in range(max(size, 1)):
            for foreignLabel, foreign in _foreignChanges(size):
                for label, act, model in _changes(list(_overChangedSource(size, start, foreign).AsIterable())):
                    yield (f"{foreignLabel}, then {label}", size, start, foreign, act, model)

def _compare(circular: Any, act: _Act, expected: list[int]) -> str|None:
    """Applies a change to the list and compares what it then reads with the model. The start it
    reports must then survive its source growing past the end: a change of the list writes back a
    start inside the container, which an append does not move."""

    try: act(circular)
    except Exception as exception: return f"raised {exception!r}; the model reads {expected}"

    content: list[int] = list(circular.AsIterable())

    if content != expected: return f"reads {content}; the model reads {expected}"

    start: int = circular.GetStart()

    circular._GetContainer().Add(7)

    return None if circular.GetStart() == start else f"start {start} moved to {circular.GetStart()} when its source grew"

def _diverge(items: ReadOnlyArray[int], start: int, act: _Act, model: _Model) -> str|None:
    expected: list[int] = _logical(start, items)

    model(expected)

    return _compare(CircularList[int](CreateList(list(items)), start), act, expected)

def _divergeAfter(size: int, start: int, foreign: _Foreign, act: _Act, model: _Model) -> str|None:
    circular: Any = _overChangedSource(size, start, foreign)
    expected: list[int] = list(circular.AsIterable())

    model(expected)

    return _compare(circular, act, expected)

class TestTheCircularListMatchesItsModel(unittest.TestCase):
    """Every structural change, at every start and every logical index, against the model."""

    def test_every_change_matches_the_model(self) -> None:
        for label, items, start, act, model in _cases():
            with self.subTest(size = len(items), start = start, change = label):
                divergence: str|None = _diverge(items, start, act, model)

                self.assertIsNone(divergence, f"{len(items)} items, start {start}, {label}: {divergence}")

class TestTheCircularListWritesWhereItReads(unittest.TestCase):
    """D-76, closed: after its source was changed by another path, the list wrote from the start
    it had stored, past the count, while it read from that start reduced modulo the count. Add
    raised IndexError, TryAdd answered False, and a range inserted into a source emptied that way
    read reversed."""

    def test_every_change_after_a_change_of_the_source_matches_the_model(self) -> None:
        for label, size, start, foreign, act, model in _foreignCases():
            with self.subTest(size = size, start = start, change = label):
                divergence: str|None = _divergeAfter(size, start, foreign, act, model)

                self.assertIsNone(divergence, f"{size} items, start {start}, {label}: {divergence}")

def _overEmptySizedList() -> Any:
    items: Any = TryCreateSizedList(0, list[int]())

    assert items is not None

    return CircularList[int](items, 0)

def _overEmptyOrderedSet() -> Any:
    return CircularList[int](CreateOrderedSet(list[int]()).AsList(), 0)

_EMPTY_REFUSALS: ReadOnlyArray[tuple[str, Callable[[], Any], _Act, bool|None]] = (
    ("capacity 0, TryAdd(9)",                  _overEmptySizedList,  lambda c: c.TryAdd(9),                 False),
    ("capacity 0, TryInsertRange(0, [9])",     _overEmptySizedList,  lambda c: c.TryInsertRange(0, [9]),     None),
    ("ordered set, TryAddRange([7, 7])",       _overEmptyOrderedSet, lambda c: c.TryAddRange([7, 7]),        None),
    ("ordered set, TryInsertRange(0, [7, 7])", _overEmptyOrderedSet, lambda c: c.TryInsertRange(0, [7, 7]),  None))
"""Insertions into an empty circular list over a container that refuses them. Contract.py covers
refusals on a non-empty circular list; the empty source takes a branch of its own."""

class TestAnEmptySourceAnswersAsItsContainer(unittest.TestCase):
    """D-74 on the empty branch, closed: the helper discarded the container's answer there and
    returned True, so a refused insertion into an empty circular list reported itself done."""

    def test_a_refused_insertion_answers_as_a_refusal(self) -> None:

        for label, factory, act, expected in _EMPTY_REFUSALS:
            with self.subTest(change = label):
                circular: Any = factory()

                self.assertIs(act(circular), expected, label)
                self.assertEqual(circular.GetCount(), 0, f"{label} wrote while refusing")

def _run(*tests: unittest.TestCase|unittest.TestSuite, failfast: bool = False) -> unittest.TestResult:
    """Runs benches into a result of their own. A run that only has to show a bench falls stops at
    its first failure."""

    result: unittest.TestResult = unittest.TestResult()

    result.failfast = failfast

    unittest.TestSuite(tests).run(result)

    return result

def _fell(result: unittest.TestResult) -> int:
    return len(result.failures) + len(result.errors)

class TestTheModelBenchCanFail(unittest.TestCase):
    """The model bench is run against a circular list that never moves its start, which rebuilds
    D-71, D-72 and D-73 at once: green on the intact tree, red on the rebuilt one."""

    def test_it_falls_when_the_start_never_moves(self) -> None:
        def frozen(self: Any, start: int = 0) -> None: pass

        bench: unittest.TestCase = TestTheCircularListMatchesItsModel("test_every_change_matches_the_model")

        self.assertEqual(_fell(_run(bench)), 0, "the model bench is expected to pass on the intact tree")

        target: Any = CircularList

        with mock.patch.object(target, "SetStart", frozen): broken: unittest.TestResult = _run(bench, failfast = True)

        self.assertGreater(_fell(broken), 0, "the model bench did not fall with the start frozen")

class TestTheSecondGridCanFail(unittest.TestCase):
    """The second grid is run against a circular list that reports its start as stored, without the
    reduction modulo the count, which rebuilds D-76: green on the intact tree, red on the rebuilt
    one."""

    def test_it_falls_when_the_start_is_used_unreduced(self) -> None:
        def unreduced(self: Any) -> Any: return self._CircularAbstract__start

        bench: unittest.TestCase = TestTheCircularListWritesWhereItReads("test_every_change_after_a_change_of_the_source_matches_the_model")

        self.assertEqual(_fell(_run(bench)), 0, "the second grid is expected to pass on the intact tree")

        target: Any = CircularAbstract

        with mock.patch.object(target, "GetStart", unreduced): broken: unittest.TestResult = _run(bench, failfast = True)

        self.assertGreater(_fell(broken), 0, "the second grid did not fall with the start unreduced")

_KEYS: ReadOnlyArray[slice] = tuple(slice(first, last, step) for first in (None, 0, 1, -1, -3) for last in (None, 1, 3, -1) for step in (None, 1, 2, -1))
"""Slices with every kind of bound and step, negative ones included: a slice already counted from
the end on the Python path."""

def _pythonChanges(size: int) -> Iterator[tuple[str, _Act]]:
    """Item and slice assignment and deletion by the Python protocol, each applied alike to the
    mutable sequence of the list and to a Python list: at every index, and over every slice of
    `_KEYS` with a shorter value and with a value of the slice's own length."""

    for index in range(size):
        yield (f"l[{index}] = 7", _bind(lambda l, i: l.__setitem__(i, 7), index))
        yield (f"del l[{index}]", _bind(lambda l, i: l.__delitem__(i), index))

    for key in _KEYS:
        yield (f"del l[{key}]", _bind(lambda l, k: l.__delitem__(k), key))
        yield (f"l[{key}] = [7, 8]", _bind(lambda l, k: l.__setitem__(k, [7, 8]), key))
        yield (f"l[{key}] = as many items", _bind(lambda l, k: l.__setitem__(k, list(range(70, 70 + len(range(*k.indices(len(l))))))), key))

def _divergePython(size: int, start: int, act: _Act) -> str|None:
    circular: Any = CircularList[int](CreateList(list(range(size))), start)
    expected: list[int]|str = list(circular.AsIterable())

    try: act(expected)
    except Exception as exception: expected = type(exception).__name__

    try: act(circular.AsMutableSequence())
    except Exception as exception: return None if type(exception).__name__ == expected else f"raised {exception!r}; Python gives {expected}"

    content: list[int] = list(circular.AsIterable())

    return None if content == expected else f"reads {content}; Python gives {expected}"

class TestThePythonPathWritesWhereItReads(unittest.TestCase):
    """D-78, closed: item and slice assignment and deletion converted the logical index to a position
    in the container, then handed it to SetItems and RemoveItems, which convert it again through the
    list's own methods. Whenever the start was not 0 they wrote and removed at the wrong place: over
    a list reading [2, 3, 0, 1], c[0] = 7 read [2, 3, 7, 1] and del c[0:2] removed nothing."""

    def test_every_assignment_and_deletion_matches_python(self) -> None:
        for size in _SIZES[1:]:
            for start in range(size):
                for label, act in _pythonChanges(size):
                    with self.subTest(size = size, start = start, change = label):
                        divergence: str|None = _divergePython(size, start, act)

                        self.assertIsNone(divergence, f"{size} items, start {start}, {label}: {divergence}")

class TestThePythonPathGridCanFail(unittest.TestCase):
    """The third grid is run against a circular list that converts the index twice again, through
    _GetIndexOrKey, which rebuilds D-78: green on the intact tree, red on the rebuilt one."""

    def test_it_falls_when_the_index_is_converted_twice(self) -> None:
        def assignTwice(self: Any, index: Any, value: Any) -> None: SetItems(self, self._GetIndexOrKey(index), value)
        def deleteTwice(self: Any, index: Any) -> None: RemoveItems(self, self._GetIndexOrKey(index))

        bench: unittest.TestCase = TestThePythonPathWritesWhereItReads("test_every_assignment_and_deletion_matches_python")

        self.assertEqual(_fell(_run(bench)), 0, "the third grid is expected to pass on the intact tree")

        target: Any = CircularList

        with mock.patch.object(target, "__setitem__", assignTwice), mock.patch.object(target, "__delitem__", deleteTwice):
            broken: unittest.TestResult = _run(bench, failfast = True)

        self.assertGreater(_fell(broken), 0, "the third grid did not fall with the index converted twice")

_REVOKING: ReadOnlyArray[tuple[str, Callable[[Any, Any], Any]]] = (
    ("c.SetStart(1)",           lambda c, s: c.SetStart(1)),
    ("c.Add(9)",                lambda c, s: c.Add(9)),
    ("c.RemoveAt(0)",           lambda c, s: c.RemoveAt(0)),
    ("c[0] = 7",                lambda c, s: c.__setitem__(0, 7)),
    ("src.Add(9)",              lambda c, s: s.Add(9)),
    ("src.RemoveAt(0)",         lambda c, s: s.RemoveAt(0)),
    ("src.SetAt(0, 7)",         lambda c, s: s.SetAt(0, 7)),
    ("src.AsReversed().Add(9)", lambda c, s: s.AsReversed().Add(9)))
"""Every path by which what a circular list reads can change: its own start, its own changes, and
its source changed directly or through another of its views."""

def _overSource() -> tuple[Any, Any]:
    source: Any = CreateList([0, 1, 2, 3])

    return (source, CircularList[int](source, 2))

def _revoked(view: Any) -> bool:
    try: list(view.AsIterable())
    except InvalidatedError: return True

    return False

class TestTheImmutableViewOfACircularTypeIsRevoked(unittest.TestCase):
    """D-75, closed: no change revoked the immutable view of a circular type, so a view said to be
    immutable changed its content. The list now subscribes its registries to its source's and
    invalidates them in SetStart, in every case, by contract (3.6 §5, Pierre: "si on s'attend à une
    invalidation, on s'attend à ce qu'elle ait lieu en toutes circonstances")."""

    def test_every_change_revokes_it(self) -> None:
        for label, change in _REVOKING:
            with self.subTest(change = label):
                source, circular = _overSource()
                view: Any = circular.AsImmutable()

                change(circular, source)

                self.assertTrue(_revoked(view), f"{label} left the immutable view live")

    def test_the_read_only_view_stays_live(self) -> None:
        for label, change in _REVOKING:
            with self.subTest(change = label):
                source, circular = _overSource()
                view: Any = circular.AsReadOnly()

                change(circular, source)

                self.assertEqual(list(view.AsIterable()), list(circular.AsIterable()), label)

    def test_a_new_immutable_view_reads_the_change(self) -> None:
        for label, change in _REVOKING:
            with self.subTest(change = label):
                source, circular = _overSource()

                circular.AsImmutable()
                change(circular, source)

                self.assertEqual(list(circular.AsImmutable().AsIterable()), list(circular.AsIterable()), label)

    def test_its_start_revokes_nothing_else(self) -> None:
        source: Any = CreateList([0, 1, 2, 3])
        sourceView: Any = source.AsImmutable()
        circular: Any = CircularList[int](source, 1)
        sibling: Any = CircularList[int](source, 2)
        siblingView: Any = sibling.AsImmutable()

        circular.SetStart(3)

        self.assertFalse(_revoked(sourceView), "SetStart revoked the immutable view of the source")
        self.assertFalse(_revoked(siblingView), "SetStart revoked the immutable view of another circular list over the same source")

    def test_a_circular_list_over_it_follows_its_start(self) -> None:
        inner: Any = CircularList[int](CreateList([0, 1, 2, 3]), 1)
        view: Any = CircularList[int](inner, 1).AsImmutable()

        inner.SetStart(3)

        self.assertTrue(_revoked(view))

    def test_a_circular_tuple_revokes_it_on_its_start(self) -> None:
        circular: Any = CircularTuple[int](CreateList([0, 1, 2, 3]).AsImmutable(), 1)
        view: Any = circular.AsImmutable()

        circular.SetStart(2)

        self.assertTrue(_revoked(view))

class TestADroppedCircularListLeavesItsSource(unittest.TestCase):
    """The subscription goes through the collection registry of the source, which holds what it
    registers strongly: it was built for collections that own their source (3.6 §5, Pierre). A
    circular list is one view among many over a source that may outlive them all, so it unsubscribes
    when it dies; without that, each one dropped left its registries in the source."""

    def test_its_registries_do_not_outlive_it(self) -> None:
        source: Any = CreateList([0, 1, 2, 3])
        circular: Any = CircularList[int](source, 1)
        registries: weakref.ReferenceType[Any] = weakref.ref(circular._GetCollectionRegistries())

        circular.AsImmutable()

        del circular

        # The list sits in a cycle, so the collector frees it, and its finalizer unsubscribes it
        # during that collection, which has already found the registries reachable from the source.
        # The next collection frees them.
        gc.collect()
        gc.collect()

        self.assertIsNone(registries(), "the source kept the registries of a dropped circular list")

class TestTheRevocationBenchesCanFail(unittest.TestCase):
    """The D-75 benches are run against a circular list rebuilt without its subscription: green on
    the intact tree, red on the rebuilt one."""

    def test_the_revocation_bench_falls_without_the_subscription(self) -> None:
        """Unsubscribing at once and invalidating nothing in SetStart rebuilds D-75."""

        def unsubscribed(obj: object, unsubscribe: Callable[[], None]) -> None: unsubscribe()
        def nothing(self: Any) -> None: pass

        # A suite drops its tests once run, so each run loads its own.
        def bench() -> unittest.TestSuite: return unittest.defaultTestLoader.loadTestsFromTestCase(TestTheImmutableViewOfACircularTypeIsRevoked)

        self.assertEqual(_fell(_run(bench())), 0, "the revocation bench is expected to pass on the intact tree")

        target: Any = CircularAbstract

        with mock.patch("WinCopies.Collections.Circular.Finalizer", unsubscribed), mock.patch.object(target, "_InvalidateViews", nothing):
            broken: unittest.TestResult = _run(bench(), failfast = True)

        self.assertGreater(_fell(broken), 0, "the revocation bench did not fall without the subscription")

    def test_the_lifetime_bench_falls_when_the_list_never_unsubscribes(self) -> None:
        def kept(obj: object, unsubscribe: Callable[[], None]) -> None: pass

        bench: unittest.TestCase = TestADroppedCircularListLeavesItsSource("test_its_registries_do_not_outlive_it")

        self.assertEqual(_fell(_run(bench)), 0, "the lifetime bench is expected to pass on the intact tree")

        with mock.patch("WinCopies.Collections.Circular.Finalizer", kept): broken: unittest.TestResult = _run(bench, failfast = True)

        self.assertGreater(_fell(broken), 0, "the lifetime bench did not fall with the list never unsubscribing")
