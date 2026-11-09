"""
Unit tests for the invalidation of the enumerators of the linked lists. For now they cover the
eight enumerable types of WinCopies.Collections.Linked.Singly: the four lists and the four
buffers. The doubly linked lists will join them when the invalidation is ported to them.

A write that changes a collection invalidates the enumerators running over it, those delivered by
its read-only view included, and does so before it writes; a write that writes nothing invalidates
nothing. The lists invalidate since 27603402, before writing since 084798ce; the buffers
register their enumerators since 280c1d1b, and their Move(), which rotates them, is a write since
0fcb3eef. An enumerator registers when it starts: one not yet started reads what the collection
holds at its start, and one that has ended is no longer registered (Enumeration 6.4 §2, 6.5 §2.5).
Neither can be invalidated, so the benches start every enumerator they invalidate.
"""

import unittest

from collections.abc import Callable, Iterable
from typing import Any
from unittest import mock

import WinCopies.Collections.Linked.Singly as Singly
import WinCopies.Collections.Linked.Singly.Buffer as Buffer

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Core import ICountable
from WinCopies.Collections.Enumeration.Core import IEnumerator
from WinCopies.Collections.Linked.Enumeration import GetValueEnumeratorFromNode
from WinCopies.Typing.Delegate import Converter
from WinCopies.Typing.Discard import InvalidatedError

type _List = Singly.IEnumerableList[int]
type _Buffer = Buffer.IEnumerableBuffer[int]
type _Path = Converter[_List, IEnumerator[int]|None]

_HELD: ReadOnlyArray[int] = (1, 2, 3)

_LISTS: ReadOnlyArray[tuple[str, Converter[Iterable[int], _List]]] = (
    ("EnumerableQueue", Singly.EnumerableQueue[int]),
    ("EnumerableStack", Singly.EnumerableStack[int]),
    ("CountableEnumerableQueue", Singly.CountableEnumerableQueue[int]),
    ("CountableEnumerableStack", Singly.CountableEnumerableStack[int]))
_BUFFERS: ReadOnlyArray[tuple[str, Converter[Iterable[int], _Buffer]]] = (
    ("EnumerableBufferedQueue", Buffer.EnumerableBufferedQueue[int]),
    ("EnumerableBufferedStack", Buffer.EnumerableBufferedStack[int]),
    ("CountableEnumerableBufferedQueue", Buffer.CountableEnumerableBufferedQueue[int]),
    ("CountableEnumerableBufferedStack", Buffer.CountableEnumerableBufferedStack[int]))
_ENUMERABLES: ReadOnlyArray[tuple[str, Converter[Iterable[int], _List]]] = _LISTS + _BUFFERS

_PATHS: ReadOnlyArray[tuple[str, _Path]] = (
    ("the collection", lambda items: items.TryGetEnumerator()),
    ("its read-only view", lambda items: items.AsReadOnly().TryGetEnumerator()))
"""The two ways of obtaining an enumerator: from the collection, and from its read-only view, which
delegates to the collection."""

_WRITES: ReadOnlyArray[tuple[str, Callable[[_List], object]]] = (
    ("Push", lambda items: items.Push(7)),
    ("PushItems", lambda items: items.PushItems((7, 8))),
    ("PushRange", lambda items: items.PushRange((7, 8))),
    ("TryPop", lambda items: items.TryPop()),
    ("Clear", lambda items: items.Clear()))
_MOVES: ReadOnlyArray[tuple[str, Callable[[_Buffer], object]]] = (
    ("Move", lambda items: items.Move()),
    ("Move through the read-only view", lambda items: items.AsReadOnly().Move()))

_SELF_READINGS: ReadOnlyArray[tuple[str, Callable[[_List], object]]] = (
    ("PushItems", lambda items: items.PushItems(items.AsIterable())),
    ("PushRange", lambda items: items.PushRange(items.AsIterable())))

def _read(enumerator: IEnumerator[int]) -> ReadOnlyArray[int]:
    read: list[int] = []

    while enumerator.TryMoveNext(): read.append(enumerator.GetCurrent())

    return tuple(read)

class TestAWriteInvalidatesTheRunningEnumerators(unittest.TestCase):
    def __started(self, path: _Path, items: _List, steps: int) -> IEnumerator[int]:
        enumerator: IEnumerator[int]|None = path(items)

        if enumerator is None: self.fail("the collection gave no enumerator")

        for _ in range(steps): self.assertTrue(enumerator.TryMoveNext(), f"the enumerator ended before step {steps}")

        return enumerator

    def __assertInvalidates[T: _List](self, rows: ReadOnlyArray[tuple[str, Converter[Iterable[int], T]]], writes: ReadOnlyArray[tuple[str, Callable[[T], object]]]) -> None:
        for name, create in rows:
            for path, obtain in _PATHS:
                for label, write in writes:
                    for steps in range(1, len(_HELD) + 1):
                        with self.subTest(collection = name, enumerator = path, write = label, steps = steps):
                            items: T = create(_HELD)
                            enumerator: IEnumerator[int] = self.__started(obtain, items, steps)

                            write(items)

                            with self.assertRaises(InvalidatedError, msg = f"{label} on the {name} left an enumerator from {path} running after {steps} step(s)"): enumerator.TryMoveNext()

    def __assertLeavesRunning[T: _List](self, rows: ReadOnlyArray[tuple[str, Converter[Iterable[int], T]]], writes: ReadOnlyArray[tuple[str, ReadOnlyArray[int], Callable[[T], object]]]) -> None:
        for name, create in rows:
            for path, obtain in _PATHS:
                for label, held, write in writes:
                    with self.subTest(collection = name, enumerator = path, write = label):
                        items: T = create(held)
                        expected: ReadOnlyArray[int] = tuple(items.AsIterable())
                        enumerator: IEnumerator[int] = self.__started(obtain, items, 1)
                        first: int = enumerator.GetCurrent()

                        write(items)

                        try: read: ReadOnlyArray[int] = (first,) + _read(enumerator)
                        except InvalidatedError: self.fail(f"{label} on the {name} invalidated an enumerator from {path}")

                        self.assertEqual(read, expected, f"after {label} on the {name}, an enumerator from {path} reads another sequence")

    def test_every_write_raises_at_the_next_step(self) -> None:
        """At every position of a running enumerator: on the first item, inside, on the last."""

        self.__assertInvalidates(_ENUMERABLES, _WRITES)

    def test_move_raises_at_the_next_step(self) -> None:
        """Until 0fcb3eef, Move() rotated a buffer under a running enumerator without invalidating it.
        Since D-119 closed, the rotation rewrites two links, which the enumerator follows: over
        A → B → C, one on the first item stopped there, without raising, and one further on read A,
        B, C, A (Enumeration 6.4 §6.2). Move() through the read-only view rotates the buffer just as
        well."""

        self.__assertInvalidates(_BUFFERS, _MOVES)

    def test_a_write_that_writes_nothing_leaves_them_running(self) -> None:
        """PushItems and PushRange of an empty source on a collection that holds items, and Move() on a
        buffer of a single item, which answers False: nothing is written, so an enumerator started
        on the first item reads on to the end. A write that writes nothing on an empty collection
        cannot be observed so: no enumerator runs over an empty collection."""

        nothing: ReadOnlyArray[tuple[str, ReadOnlyArray[int], Callable[[_List], object]]] = (
            ("PushItems of an empty source", _HELD, lambda items: items.PushItems(())),
            ("PushRange of an empty source", _HELD, lambda items: items.PushRange(())))
        moves: ReadOnlyArray[tuple[str, ReadOnlyArray[int], Callable[[_Buffer], object]]] = tuple((f"{label} on a single item", (1,), move) for label, move in _MOVES)

        self.__assertLeavesRunning(_ENUMERABLES, nothing)
        self.__assertLeavesRunning(_BUFFERS, moves)

class TestASourceThatReadsTheCollectionItselfFails(unittest.TestCase):
    """PushItems or PushRange given the collection's own content: the first item read is about to be
    written, which invalidates the enumerator reading the source, so the source raises at its next
    step, and the write, which welds the items as a block once the source is spent, never happens.
    The lists doubled before 27603402, and the buffers before 280c1d1b. The indexable lists raise as
    well, but keep the items they had added (Enumeration 6.5 §2.5)."""

    def test_it_raises_and_leaves_the_collection_as_it_was(self) -> None:
        for name, create in _ENUMERABLES:
            for label, write in _SELF_READINGS:
                with self.subTest(collection = name, write = label):
                    items: _List = create((1, 2))
                    held: ReadOnlyArray[int] = tuple(items.AsIterable())

                    with self.assertRaises(InvalidatedError, msg = f"{label} of its own content on the {name} did not raise"): write(items)

                    self.assertEqual(tuple(items.AsIterable()), held, f"{label} of its own content changed the {name}")

                    if isinstance(items, ICountable): self.assertEqual(items.GetCount(), len(held), f"{label} of its own content changed the count of the {name}")

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

def _nothing(self: Any) -> None: pass
def _unregistered(self: Any) -> IEnumerator[Any]: return GetValueEnumeratorFromNode(self._GetLinkedListCookie())

class TestTheInvalidationBenchesCanFail(unittest.TestCase):
    """The benches above, run against the defects they are meant to catch: green on the intact tree,
    red on the rebuilt one. A class is reached through its public name, or by name when private,
    and is the one that carries the attribute rebuilt."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any], create: bool = False) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with mock.patch.multiple(target, create = create, **rebuilt): broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")

    def test_the_move_bench_falls_when_move_does_not_invalidate(self) -> None:
        """As until 0fcb3eef: BufferBase.Move() rotated the buffer without invalidating anything."""

        def silent(self: Any) -> bool|None:
            result: Any = self._IsFirstAlsoLast()

            if result is None: return None
            if result[1] is None: return False

            self._OnSetFirst(result[1], result[0])

            return True

        self.__assertFalls(TestAWriteInvalidatesTheRunningEnumerators, "test_move_raises_at_the_next_step", Buffer.BufferBase, {"Move": silent})

    def test_the_benches_fall_when_a_class_ahead_of_the_managed_interface_shadows_it(self) -> None:
        """The condition of Enumeration 6.6 §2.3, held on behaviour rather than on the order of
        resolution: _InvalidateViews() and TryGetEnumerator() are provided by the managed interfaces,
        which come last among the bases of the concrete types, so a class ahead of them that
        defines either shadows them (the trap of _CanInvalidate, Enumeration 5). ListBase comes
        ahead in all eight types, BufferBase and EnumerableBufferAbstract in the four buffers.
        EnumerableBufferAbstract built its enumerators without registering them from 27603402
        until 280c1d1b. Each class is given each rebuilt member alone."""

        rebuilt: ReadOnlyArray[tuple[str, type, str, Any]] = (
            ("ListBase", Singly.ListBase, "_InvalidateViews", _nothing),
            ("BufferBase", Buffer.BufferBase, "_InvalidateViews", _nothing),
            ("ListBase", Singly.ListBase, "TryGetEnumerator", _unregistered),
            ("EnumerableBufferAbstract", Buffer.EnumerableBufferAbstract, "TryGetEnumerator", _unregistered))
        benches: ReadOnlyArray[tuple[type[unittest.TestCase], str]] = (
            (TestAWriteInvalidatesTheRunningEnumerators, "test_every_write_raises_at_the_next_step"),
            (TestAWriteInvalidatesTheRunningEnumerators, "test_move_raises_at_the_next_step"),
            (TestASourceThatReadsTheCollectionItselfFails, "test_it_raises_and_leaves_the_collection_as_it_was"))

        for base, target, member, substitute in rebuilt:
            for bench, name in benches:
                with self.subTest(base = base, member = member, bench = name): self.__assertFalls(bench, name, target, {member: substitute}, create = not hasattr(target, member))

    def test_the_no_write_bench_falls_when_a_write_invalidates_before_knowing(self) -> None:
        """A write that invalidates before it knows whether it will write: _IAdder._PushRange(), which
        carries PushItems and PushRange in all eight types, invalidating before it reads its
        source, and BufferBase.Move() before it checks that the buffer holds two items."""

        adder: type = getattr(Singly, "_IAdder")
        pushRange: Callable[[Any, Iterable[Any], Any, bool], bool] = getattr(adder, "_PushRange")
        move: Callable[[Any], bool|None] = getattr(Buffer.BufferBase, "Move")

        def eagerPushRange(self: Any, items: Iterable[Any], weld: Any, range: bool) -> bool:
            self._InvalidateViews()

            return pushRange(self, items, weld, range)

        def eagerMove(self: Any) -> bool|None:
            self._InvalidateViews()

            return move(self)

        for name, target, member, substitute in (("_IAdder", adder, "_PushRange", eagerPushRange), ("BufferBase", Buffer.BufferBase, "Move", eagerMove)):
            with self.subTest(base = name, member = member): self.__assertFalls(TestAWriteInvalidatesTheRunningEnumerators, "test_a_write_that_writes_nothing_leaves_them_running", target, {member: substitute})

if __name__ == '__main__': unittest.main()
