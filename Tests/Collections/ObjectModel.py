"""
Unit tests for the observable collection's event surface (WinCopies.Collections.ObjectModel).

The surface had no bench at all: five events across five parallel layers, and not one
reference to GetEventManager or OnItem* anywhere in this tree. That is how D-55 lived. The
reversal did not merely fail to announce itself -- it announced n item replacements,
because it arrived from the collections.abc mixin and reached _SetItem once per positional
write instead of reaching a hook of its own. A bench on the content alone would not have
seen it; the content was right until the hook was declared.

So these benches assert what an event surface is for: that an operation announces itself
once, on the channel that names it, with an action that agrees with the channel. Unicity is
the load-bearing clause. A bench that only checked "something fired" would have passed
throughout.
"""

import unittest
from typing import Any
from unittest import mock

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import List
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Extensions import ITuple, IList, ILinkedCursorProvider
from WinCopies.Collections.Extensions.Collection import BufferedStackBase
from WinCopies.Collections.Linked.Singly import IReadOnlyCountableEnumerableList, ICountableEnumerableList, ICountableEnumerableQueue, ICountableEnumerableStack
from WinCopies.Collections.ObjectModel.Collection import (CollectionChangedAction, CollectionChangedEventArgs,
                                                          IObservableCollection, ObservableCollection)

from WinCopies.Typing import INullable, InvalidOperationError
from WinCopies.Typing.Delegate import Function, Converter, NullablePredicate
from WinCopies.Typing.Delegate.Event import EventMonitor

type _Call = NullablePredicate[ObservableCollection[int]]
type _Record = tuple[str, CollectionChangedAction]

_CONTENT: ReadOnlyArray[int] = (1, 2, 3, 4)

# The surface, named once. Every bench below reads it rather than its own list, so a
# seventh event cannot be added without a bench either covering it or saying it does not.
_CHANNELS: ReadOnlyArray[tuple[str, CollectionChangedAction]] = (
    ("OnItemAdded",     CollectionChangedAction.Add),
    ("OnItemUpdated",   CollectionChangedAction.Update),
    ("OnItemsSwapped",  CollectionChangedAction.Swap),
    ("OnItemMoved",     CollectionChangedAction.Move),
    ("OnItemsReversed", CollectionChangedAction.Reverse),
    ("OnItemRemoved",   CollectionChangedAction.Remove))

class _Listener:
    """Subscribes to every channel at once and records what arrives, in order.

    One handler per channel, each closing over its own channel name: the record therefore
    says which channel carried the event, not only what the args claimed. The two can
    disagree -- that is one of the things worth measuring -- so neither is read from the
    other.
    """

    def __init__(self, items: IObservableCollection[int]) -> None:
        self.__records: list[_Record] = []

        for channel, _ in _CHANNELS:
            def handle(sender: IObservableCollection[int], args: CollectionChangedEventArgs, channel: str = channel) -> None:
                self.__records.append((channel, args.GetAction()))

            getattr(items.GetEventManager(), channel)(handle)

    def GetRecords(self) -> ReadOnlyArray[_Record]: return tuple(self.__records)

def _create() -> ObservableCollection[int]:
    return ObservableCollection[int](List[int](list(_CONTENT)))

def _attempt(items: ObservableCollection[int], call: _Call) -> Any:
    """Runs a mutator on a collection the caller built and swallows whatever it answers, an
    exception included: these benches ask what the collection holds afterwards, not how the
    call ended, and a raise is one legitimate way to refuse."""

    try: return call(items)
    except Exception as exception: return exception

def _listen(call: _Call, source: Converter[ObservableCollection[int], Any]|None = None) -> tuple[ReadOnlyArray[_Record], Any]:
    """Runs one call on a fresh collection and returns what the surface announced.

    Whatever the call answers is returned with the records, an exception included: a
    mutation that raises is still a mutation that must not announce what it did not do.
    """

    items: ObservableCollection[int] = _create()
    listener: _Listener = _Listener(items)

    try: answer: Any = call(items if source is None else source(items))
    except Exception as exception: answer = exception

    return listener.GetRecords(), answer

# One elementary operation each, with the channel it must reach. 'Elementary' is the whole
# claim: each of these is one act, so it announces once. The bulk forms are measured apart,
# below, because they do not agree with each other.
_ELEMENTARY: ReadOnlyArray[tuple[str, _Call, str]] = (
    ("Add",            lambda o: o.Add(9),                           "OnItemAdded"),
    ("Insert",         lambda o: o.Insert(1, 9),                     "OnItemAdded"),
    ("InsertRange",    lambda o: o.InsertRange(1, (7, 8)),           "OnItemAdded"),
    ("InsertValues",   lambda o: o.InsertValues(1, 7, 8),            "OnItemAdded"),
    ("SetAt",          lambda o: o.SetAt(0, 9),                      "OnItemUpdated"),
    ("TrySetAt",       lambda o: o.TrySetAt(0, 9),                   "OnItemUpdated"),
    ("Move",           lambda o: o.Move(0, 2),                       "OnItemMoved"),
    ("Swap",           lambda o: o.Swap(0, 2),                       "OnItemsSwapped"),
    ("RemoveAt",       lambda o: o.RemoveAt(0),                      "OnItemRemoved"),
    ("Remove",         lambda o: o.Remove(1),                        "OnItemRemoved"),
    ("RemoveRange",    lambda o: o.RemoveRange(0, 2),                "OnItemRemoved"),
    ("Clear",          lambda o: o.Clear(),                          "OnItemRemoved"),
    # The protocol face reaches the same hooks. reverse() is here because it is what D-55
    # was: before the hook existed it reached OnItemUpdated four times on four elements.
    ("reverse()",      lambda o: o.AsMutableSequence().reverse(),     "OnItemsReversed"),
    ("append()",       lambda o: o.AsMutableSequence().append(9),     "OnItemAdded"),
    ("insert()",       lambda o: o.AsMutableSequence().insert(1, 9),  "OnItemAdded"),
    ("l[0] = 9",       lambda o: o.AsMutableSequence().__setitem__(0, 9), "OnItemUpdated"),
    ("del l[0]",       lambda o: o.AsMutableSequence().__delitem__(0),    "OnItemRemoved"))

# Refused outright, by return value. The surface announces what happened, so it says
# nothing here.
_REFUSED: ReadOnlyArray[tuple[str, _Call]] = (
    ("TrySetAt out of range",    lambda o: o.TrySetAt(99, 9)),
    ("TryRemoveAt out of range", lambda o: o.TryRemoveAt(99)),
    ("TryInsert out of range",   lambda o: o.TryInsert(99, 9)),
    ("TryMove out of range",     lambda o: o.TryMove(0, 99)),
    ("TrySwap out of range",     lambda o: o.TrySwap(0, 99)),
    ("TryRemove absent value",   lambda o: o.TryRemove(42)))

# The projections do not own a manager: GetEventManager is final on the read-only base and
# routes to the source's. A mutation through one of them must therefore reach a subscriber
# of the source, with no channel of its own.
_PROJECTED: ReadOnlyArray[tuple[str, _Call, Converter[ObservableCollection[int], ITuple[int]], str]] = (
    ("fixed size, SetAt", lambda v: v.SetAt(0, 9),  lambda o: o.AsFixedSize(), "OnItemUpdated"),
    ("fixed size, Swap",  lambda v: v.Swap(0, 2),   lambda o: o.AsFixedSize(), "OnItemsSwapped"),
    ("reversed, SetAt",   lambda v: v.SetAt(0, 9),  lambda o: o.AsReversed(),  "OnItemUpdated"),
    ("reversed, reverse", lambda v: v.AsMutableSequence().reverse(), lambda o: o.AsReversed(), "OnItemsReversed"))

class TestEveryOperationAnnouncesItselfOnce(unittest.TestCase):
    """One act, one event, on the channel that names it, with the agreeing action.

    Three assertions per call, and the first is the one that matters: a count. D-55's
    reversal announced four times on four elements, each announcement individually
    well-formed. Only the count said anything was wrong.
    """

    def test_every_elementary_operation_announces_once(self) -> None:
        self.assertGreaterEqual(len(_ELEMENTARY), 17, "the table has shrunk; the perimeter is no longer the surface")

        for name, call, channel in _ELEMENTARY:
            with self.subTest(call = name):
                records, answer = _listen(call)

                self.assertNotIsInstance(answer, Exception, f"{name} raised: {answer}")
                self.assertEqual(len(records), 1, f"{name} announced {len(records)} events, not one: {records}")
                self.assertEqual(records[0][0], channel, f"{name} announced on {records[0][0]} rather than {channel}")

    def test_the_action_agrees_with_the_channel(self) -> None:
        actions: dict[str, CollectionChangedAction] = dict(_CHANNELS)

        for name, call, channel in _ELEMENTARY:
            with self.subTest(call = name):
                records, _ = _listen(call)

                self.assertEqual(len(records), 1, f"{name} announced {len(records)} events")
                self.assertIs(records[0][1], actions[channel],
                              f"{name} reached {channel} carrying {records[0][1].name} rather than {actions[channel].name}")

class TestTheSurfaceHasNoDeadChannel(unittest.TestCase):
    """Every channel the surface declares is reached by something.

    A channel nothing reaches is a promise with no keeper, and it is also how a hook comes
    to be declared and never wired: _ReverseItems existed for the length of one measurement
    before this bench was written, and this is the clause that would have said so.
    """

    def test_every_declared_channel_is_reached(self) -> None:
        reached: set[str] = set()

        for _, call, _ in _ELEMENTARY:
            records, _ = _listen(call)

            reached.update(channel for channel, _ in records)

        for channel, _ in _CHANNELS:
            with self.subTest(channel = channel): self.assertIn(channel, reached, f"{channel} is declared and nothing reaches it")

    def test_nothing_reaches_a_channel_the_surface_does_not_declare(self) -> None:
        declared: set[str] = {channel for channel, _ in _CHANNELS}

        for name, call, _ in _ELEMENTARY:
            records, _ = _listen(call)

            for channel, _ in records:
                with self.subTest(call = name, channel = channel): self.assertIn(channel, declared)

class TestARefusalAnnouncesNothing(unittest.TestCase):
    """The surface reports what the collection did, not what was asked of it."""

    def test_a_refused_mutation_is_silent(self) -> None:
        for name, call in _REFUSED:
            with self.subTest(call = name):
                records, answer = _listen(call)

                self.assertNotIsInstance(answer, Exception, f"{name} raised rather than refusing: {answer}")
                self.assertEqual(records, (), f"{name} was refused yet announced {records}")

    def test_a_refused_mutation_leaves_the_content_alone(self) -> None:
        for name, call in _REFUSED:
            with self.subTest(call = name):
                items: ObservableCollection[int] = _create()

                call(items)

                self.assertEqual(tuple(items.AsIterable()), _CONTENT, f"{name} was refused yet changed the content")

def _constrained() -> tuple[IList[int], ObservableCollection[int]]:
    """An observable collection over a container that refuses some writes.

    An ordered set's list view is the one container in the tree whose positional write can
    be refused for a reason the wrapper's own index validation cannot see: the index is
    valid and the value is not. Every other refusal is filtered upstream, before any hook
    is reached, which is why the table above cannot exercise this clause -- a hook that
    announced unconditionally would still pass it.
    """

    view: IList[int] = CreateOrderedSet(_CONTENT).AsList()

    return view, ObservableCollection[int](view)

class TestARefusalThatReachesTheHookIsSilent(unittest.TestCase):
    """A hook that did not write does not announce.

    The guard is real -- each override reads what super() answered -- and this is what
    holds it in place. Writing a value the ordered set already holds elsewhere passes the
    index validation and is refused by the container, so the hook runs and returns False.
    """

    def test_a_write_the_container_refuses_announces_nothing(self) -> None:
        items: ObservableCollection[int] = _constrained()[1]
        listener: _Listener = _Listener(items)

        items.TrySetAt(1, 3)

        self.assertEqual(tuple(items.AsIterable()), _CONTENT, "the refused write went through; the bench is not measuring a refusal")
        self.assertEqual(listener.GetRecords(), (), f"a refused write announced {listener.GetRecords()}")

    def test_an_accepted_write_on_the_same_container_announces_once(self) -> None:
        """The counter-example, so the clause above cannot pass by the container refusing
        everything."""

        items: ObservableCollection[int] = _constrained()[1]
        listener: _Listener = _Listener(items)

        items.TrySetAt(1, 9)

        self.assertEqual(tuple(items.AsIterable()), (1, 9, 3, 4))
        self.assertEqual(listener.GetRecords(), (("OnItemUpdated", CollectionChangedAction.Update),))

class TestAWrapperReportsTheRefusalItReceived(unittest.TestCase):
    """A wrapper answers what its container answered.

    This was D-56, and the marker that held it reported its closure: _SetAt was declared
    -> None, so the hook could not report a refusal and TrySetAt answered that the key
    existed. The three scalar routes are measured together because they are three faces of
    one write, and the defect showed on all three while the content stayed right -- D-58,
    on the slice route, is the one that does not, and has no bench here.
    """

    def test_the_wrapper_answers_what_its_container_answered(self) -> None:
        bare: IList[int] = _constrained()[0]
        wrapped: ObservableCollection[int] = _constrained()[1]

        self.assertEqual(wrapped.TrySetAt(1, 3), bare.TrySetAt(1, 3),
                         "the wrapper reports a write its container refused")

    def test_the_wrapper_raises_where_its_container_raises(self) -> None:
        """SetAt is final on ISetter and raises when TrySetAt answers False, so a wrapper
        whose hook stayed silent broke the one member whose contract is to write or raise."""

        wrapped: ObservableCollection[int] = _constrained()[1]

        with self.assertRaises(KeyError): wrapped.SetAt(1, 3)

        self.assertEqual(tuple(wrapped.AsIterable()), _CONTENT, "the refused write went through")

    def test_the_wrapper_refuses_the_scalar_subscript(self) -> None:
        """The protocol face reaches the same seam, and silence there is a write that reads
        as having happened."""

        wrapped: ObservableCollection[int] = _constrained()[1]

        with self.assertRaises(Exception): wrapped.AsMutableSequence()[1] = 3

        self.assertEqual(tuple(wrapped.AsIterable()), _CONTENT, "the refused write went through")

    def test_an_accepted_write_still_answers_true(self) -> None:
        """The counter-example: the clause above must not pass by refusing everything."""

        wrapped: ObservableCollection[int] = _constrained()[1]

        self.assertTrue(wrapped.TrySetAt(1, 9))
        self.assertEqual(tuple(wrapped.AsIterable()), (1, 9, 3, 4))

class TestAProjectionAnnouncesOnTheSource(unittest.TestCase):
    """A view has no manager of its own, so what it changes the source announces."""

    def test_a_mutation_through_a_projection_reaches_the_source(self) -> None:
        for name, call, source, channel in _PROJECTED:
            with self.subTest(view = name):
                records, answer = _listen(call, source)

                self.assertNotIsInstance(answer, Exception, f"{name} raised: {answer}")
                self.assertEqual(len(records), 1, f"{name} announced {len(records)} events on the source, not one: {records}")
                self.assertEqual(records[0][0], channel, f"{name} announced on {records[0][0]} rather than {channel}")

    def test_a_projection_shares_the_source_manager(self) -> None:
        items: ObservableCollection[int] = _create()

        self.assertIs(items.AsFixedSize().GetEventManager(), items.GetEventManager())
        self.assertIs(items.AsReadOnly().GetEventManager(), items.GetEventManager())

# The three spellings of one bulk insertion. This was D-57: AddRange had no hook of its own
# and was written as repeated Add on ICollection, extend() as repeated append on the
# collections.abc mixin, so both were seen by the observable layer as their elements and both
# left the collection half written when an item was refused partway. They now route through
# the range primitive, and these are what keeps them there.
_BULK: ReadOnlyArray[tuple[str, _Call]] = (
    ("InsertRange", lambda o: o.InsertRange(1, (7, 8))),
    ("AddRange",    lambda o: o.AddRange((7, 8))),
    ("extend()",    lambda o: o.AsMutableSequence().extend((7, 8))))

# The same three, over a container that refuses the second item: 3 is already in the ordered
# set, so each call asks for one acceptable item and one refused one.
_BULK_REFUSED: ReadOnlyArray[tuple[str, _Call]] = (
    ("InsertRange", lambda o: o.InsertRange(1, (9, 3))),
    ("AddRange",    lambda o: o.AddRange((9, 3))),
    ("TryAddRange", lambda o: o.TryAddRange((9, 3))),
    ("extend()",    lambda o: o.AsMutableSequence().extend((9, 3))))

# And the same three asking for nothing. Kept beside the other two tables rather than inline,
# so the three lambdas carry the declared signature the others do.
_BULK_EMPTY: ReadOnlyArray[tuple[str, _Call]] = (
    ("InsertRange", lambda o: o.InsertRange(1, ())),
    ("AddRange",    lambda o: o.AddRange(())),
    ("extend()",    lambda o: o.AsMutableSequence().extend(())))

class TestBulkInsertionIsOneAct(unittest.TestCase):
    """A bulk insertion is one act: it announces once, and it goes in whole or not at all.

    The count clause is what marked D-57, and it was too weak on its own -- it says the
    spellings agree, not that any of them is right. The two clauses below are the ones that
    bite: nothing is inserted when an item is refused, and no spelling reports a success it
    did not perform.
    """

    def test_every_bulk_insertion_announces_once(self) -> None:
        counts: dict[str, int] = {name: len(_listen(call)[0]) for name, call in _BULK}

        self.assertEqual(set(counts.values()), {1}, f"a bulk insertion of two items announced {counts}")

    def test_a_refused_bulk_insertion_inserts_nothing(self) -> None:
        """Atomicity. Before the fix, the item before the refused one stayed in and the
        collection was left one element longer than it started, with an exception raised on
        top -- the worst outcome for a caller trying to recover."""

        for name, call in _BULK_REFUSED:
            with self.subTest(call = name):
                items: ObservableCollection[int] = _constrained()[1]

                _attempt(items, call)

                self.assertEqual(tuple(items.AsIterable()), _CONTENT, f"{name} inserted part of a refused range")

    def test_a_refused_bulk_insertion_reports_no_success(self) -> None:
        """A refusal answers anything but success. Raising is one way and is what the named
        forms do; what none of them may do is answer True, which is what AddRange did while
        routing through a primitive whose False it swallowed."""

        for name, call in _BULK_REFUSED:
            with self.subTest(call = name): self.assertIsNot(_attempt(_constrained()[1], call), True, f"{name} reported success for a refused range")

    def test_an_empty_bulk_insertion_is_nothing_to_do(self) -> None:
        """The counter-example that keeps the two clauses above from passing by refusing
        everything: an empty range is not a refusal, and must neither raise nor announce."""

        for name, call in _BULK_EMPTY:
            with self.subTest(call = name):
                items: ObservableCollection[int] = _constrained()[1]
                listener: _Listener = _Listener(items)

                answer: Any = _attempt(items, call)

                self.assertNotIsInstance(answer, Exception, f"{name} raised on an empty range: {answer}")
                self.assertEqual(listener.GetRecords(), (), f"{name} announced {listener.GetRecords()} for an empty range")
                self.assertEqual(tuple(items.AsIterable()), _CONTENT)

class TestASliceAssignmentIsOneAct(unittest.TestCase):
    """It is, now: the span is validated before the first write.

    D-58, closed. SetValues removed the old span before knowing whether the new one was
    accepted, and InsertRange had no refusal left to report by then, so a refused slice
    assignment destroyed what it removed -- measured here at l[1:2] = (3,), which left three
    elements where it found four. The order is no longer the fix: Extensions.IList.CanSetRange
    asks the container while the content is intact, and the refusal arrives before anything
    moves.

    This class is what keeps it closed, and it asks two things the registry's own span bench
    cannot. The content clause is the defect itself. The silence clause is the reason the
    rollback route was refused instead: restoring the span would have announced Removed and
    then Added for an assignment that never happened, leaving a consumer to recognise the
    pairs that net out -- a refusal must announce nothing at all.
    """

    def test_a_refused_slice_assignment_leaves_the_content_alone(self) -> None:
        items: ObservableCollection[int] = _constrained()[1]

        _attempt(items, lambda o: o.AsMutableSequence().__setitem__(slice(1, 2), (3,)))

        self.assertEqual(tuple(items.AsIterable()), _CONTENT, "a refused slice assignment destroyed an element")

    def test_a_refused_slice_assignment_announces_nothing(self) -> None:
        records: ReadOnlyArray[_Record] = _listen(lambda o: o.AsMutableSequence().__setitem__(slice(1, 2), (3,)), lambda _: _constrained()[1])[0]

        self.assertEqual(records, (), f"a refused slice assignment announced {tuple(record[0] for record in records)}")

    def test_a_refused_stepped_span_leaves_the_content_alone(self) -> None:
        """The stepped branch, which writes n times through SetAt and so had its own way to
        stop halfway. It reaches the hook only through the wrapper: the container's own
        __setitem__ routes to SetOrderedValues, which validates on its own behalf, whereas
        the wrapper's goes to the generic primitive. The order of the two values is what
        makes this clause measure anything: the 9 at position 0 is accepted, so the branch
        writes it and only then meets the 2, which position 1 still holds outside the span.
        Reversed, the first write would be the one refused and the content would survive
        without the hook ever being consulted -- measured, and the reason this key is this
        way round.
        """

        items: ObservableCollection[int] = _constrained()[1]

        _attempt(items, lambda o: o.AsMutableSequence().__setitem__(slice(0, 4, 2), (9, 2)))

        self.assertEqual(tuple(items.AsIterable()), _CONTENT, "a refused stepped span changed the content")

    def test_a_legitimate_span_still_goes_through(self) -> None:
        """Without this one the two clauses above are vacuous: a hook that refused every span
        would satisfy both, and the wrapper would have lost slice assignment altogether. The
        key is the one measured legitimate on this very container -- the 3 that arrives at
        position 1 is the 3 that leaves position 2, which is why unicity does not forbid it.
        """

        view, items = _constrained()

        items.AsMutableSequence()[1:3] = (3, 9)

        self.assertEqual(tuple(items.AsIterable()), (1, 3, 9, 4), "a legitimate span was refused or misplaced")
        self.assertEqual(tuple(view.AsIterable()), (1, 3, 9, 4), "the container and its wrapper disagree on the result")

def _listenFrom(start: ReadOnlyArray[int], call: Converter[ObservableCollection[int], Any]) -> tuple[ReadOnlyArray[_Record], Any, ReadOnlyArray[int]]:
    """As _listen, on a collection holding start, and with what the collection holds afterwards."""

    items: ObservableCollection[int] = ObservableCollection[int](List[int](list(start)))
    listener: _Listener = _Listener(items)
    answer: Any = _attempt(items, call)

    return listener.GetRecords(), answer, tuple(items.AsIterable())

def _cursorHead(cursor: IReadOnlyCountableEnumerableList[int]) -> int|None:
    head: INullable[int] = cursor.TryPeek()

    return head.GetValue() if head.HasValue() else None

def _askCursor[T](ask: Function[T]) -> T|RecursionError:
    """Asks for a cursor, and hands back the RecursionError of a view that asks itself, so that a bench
    reports it as a failure of its own rather than under a traceback a thousand frames deep."""

    try: return ask()
    except RecursionError as error: return error

# The two faces of D-106: the views of the collection, each read-only as far as its cursors go.
_OBSERVABLE_VIEWS: ReadOnlyArray[tuple[str, Converter[ObservableCollection[int], ITuple[int]]]] = (
    ("AsReadOnly()",  lambda o: o.AsReadOnly()),
    ("AsFixedSize()", lambda o: o.AsFixedSize()))

_VIEW_CURSORS: ReadOnlyArray[tuple[str, Converter[ITuple[int], IReadOnlyCountableEnumerableList[int]]]] = (
    ("queued",  lambda items: items.AsQueuedCursor()),
    ("stacked", lambda items: items.AsStackedCursor()))

# Each write a cursor of the collection can make, with the channel it must reach and what it leaves.
# The stacked Push is asked twice because it has two branches: Add on an empty stack, Insert at 0
# otherwise.
_CURSOR_WRITES: ReadOnlyArray[tuple[str, ReadOnlyArray[int], Converter[ObservableCollection[int], Any], str, ReadOnlyArray[int]]] = (
    ("queued TryPop",       _CONTENT, lambda o: o.AsQueuedCursor().TryPop(),  "OnItemRemoved", (2, 3, 4)),
    ("stacked TryPop",      _CONTENT, lambda o: o.AsStackedCursor().TryPop(), "OnItemRemoved", (2, 3, 4)),
    ("queued Push",         _CONTENT, lambda o: o.AsQueuedCursor().Push(9),   "OnItemAdded",   (1, 2, 3, 4, 9)),
    ("stacked Push",        _CONTENT, lambda o: o.AsStackedCursor().Push(9),  "OnItemAdded",   (9, 1, 2, 3, 4)),
    ("stacked Push, empty", (),       lambda o: o.AsStackedCursor().Push(9),  "OnItemAdded",   (9,)),
    ("queued Clear",        _CONTENT, lambda o: o.AsQueuedCursor().Clear(),   "OnItemRemoved", ()),
    ("stacked Clear",       _CONTENT, lambda o: o.AsStackedCursor().Clear(),  "OnItemRemoved", ()))

# PushItems through each cursor, on a collection with and without content. The order is that of
# successive pushes, the meaning PushItems has had since 70e4d1e; the stacked cursor gets it from one
# AddRange on its reversed view.
_CURSOR_PUSHES: ReadOnlyArray[tuple[str, ReadOnlyArray[int], Converter[ObservableCollection[int], Any], ReadOnlyArray[int]]] = (
    ("queued cursor",                    _CONTENT, lambda o: o.AsQueuedCursor().PushItems((7, 8, 9)),  (1, 2, 3, 4, 7, 8, 9)),
    ("stacked cursor",                   _CONTENT, lambda o: o.AsStackedCursor().PushItems((7, 8, 9)), (9, 8, 7, 1, 2, 3, 4)),
    ("queued cursor, empty collection",  (),       lambda o: o.AsQueuedCursor().PushItems((7, 8, 9)),  (7, 8, 9)),
    ("stacked cursor, empty collection", (),       lambda o: o.AsStackedCursor().PushItems((7, 8, 9)), (9, 8, 7)))

class TestEachObservableFaceDeclaresItsMutability(unittest.TestCase):
    """D-101. GetMutability sat under @final on the base the read-only and the fixed-size views share,
    and answered ReadOnly for both: the fixed-size view, which writes, declared that it did not, and
    rendered as a read-only tuple, (1, 2, 3, 4) rather than [1, 2, 3, 4]. No bench asked a view of the
    collection for its mutability or its rendering. The collection is the third row, so that the three
    answers are read side by side."""

    def test_each_face_declares_its_mutability_and_renders_by_it(self) -> None:
        items: ObservableCollection[int] = _create()
        faces: ReadOnlyArray[tuple[str, ITuple[int], Mutability, str]] = (
            ("the collection", items,               Mutability.Mutable,   "[1, 2, 3, 4]"),
            ("AsFixedSize()",  items.AsFixedSize(), Mutability.FixedSize, "[1, 2, 3, 4]"),
            ("AsReadOnly()",   items.AsReadOnly(),  Mutability.ReadOnly,  "(1, 2, 3, 4)"))

        for face, view, mutability, rendering in faces:
            with self.subTest(face = face):
                self.assertIs(view.GetMutability(), mutability, f"{face} declares {view.GetMutability().name} rather than {mutability.name}")
                self.assertEqual(view.ToString(), rendering, f"{face} renders as another mutability")

class TestTheObservableCollectionProvidesCursors(unittest.TestCase):
    """D-105. The collection is an IList, so since d6c7a8f it owes mutable cursors, and it derived from
    no cursor provider: its two cursors were the abstract members of ILinkedCursorProvider, which the
    runtime let it be instantiated without, and they answered None. pyright and mypy said so on
    Contract.py, which instantiates the collection; no bench asked for a cursor.

    The cursors walk the collection itself, so their writes reach its hooks: each announces once, on the
    channel that names it, as the elementary operations above do."""

    def test_the_collection_provides_mutable_cursors(self) -> None:
        items: ObservableCollection[int] = _create()
        cursors: ReadOnlyArray[tuple[str, Function[ICountableEnumerableList[int]], type]] = (
            ("queued",  lambda: items.AsQueuedCursor(),  ICountableEnumerableQueue),
            ("stacked", lambda: items.AsStackedCursor(), ICountableEnumerableStack))

        for kind, ask, mutable in cursors:
            with self.subTest(cursor = kind):
                cursor: ICountableEnumerableList[int] = ask()

                self.assertIsInstance(cursor, mutable, f"the {kind} cursor of the collection is {cursor!r}, not a mutable one")
                self.assertIs(ask(), cursor, f"the {kind} cursor is built again on each request")
                self.assertEqual(_cursorHead(cursor), _CONTENT[0], f"the {kind} cursor has another head")
                self.assertEqual(cursor.GetCount(), len(_CONTENT), f"the {kind} cursor counts otherwise")
                self.assertEqual(tuple(cursor.AsIterable()), _CONTENT, f"the {kind} cursor reads another order")

    def test_a_cursor_write_announces_once(self) -> None:
        for name, start, call, channel, expected in _CURSOR_WRITES:
            with self.subTest(call = name):
                records, answer, content = _listenFrom(start, call)

                self.assertNotIsInstance(answer, Exception, f"{name} raised: {answer}")
                self.assertEqual(len(records), 1, f"{name} announced {len(records)} events, not one: {records}")
                self.assertEqual(records[0][0], channel, f"{name} announced on {records[0][0]} rather than {channel}")
                self.assertEqual(content, expected, f"{name} left another content")

    def test_pushing_several_items_announces_once(self) -> None:
        """PushItems is one call, and the collection announces one ItemAdded for it, whatever the number
        of items. The queued cursor has always pushed them in one AddRange; the stacked one has pushed
        them in one range call since edf8dbe, and before it added them one by one, so that the collection
        announced each."""

        for name, start, call, expected in _CURSOR_PUSHES:
            with self.subTest(push = name):
                records, answer, content = _listenFrom(start, call)

                self.assertNotIsInstance(answer, Exception, f"PushItems through the {name} raised: {answer}")
                self.assertEqual(records, (("OnItemAdded", CollectionChangedAction.Add),), f"PushItems of three items through the {name} announced {records}")
                self.assertEqual(content, expected, f"PushItems through the {name} left another content")

class TestTheObservableViewsProvideCursors(unittest.TestCase):
    """D-106. The read-only and the fixed-size views owe read-only cursors, and they asked the read-only
    side of their container for them, which is the read-only view itself: each request recursed, the
    shape of D-87. The fixed-size view gets read-only cursors too, as IArray promises no other. No bench
    asked a view for a cursor."""

    def test_a_view_provides_read_only_cursors(self) -> None:
        items: ObservableCollection[int] = _create()

        for view, provide in _OBSERVABLE_VIEWS:
            for kind, ask in _VIEW_CURSORS:
                with self.subTest(view = view, cursor = kind):
                    subject: ITuple[int] = provide(items)
                    cursor: IReadOnlyCountableEnumerableList[int]|RecursionError = _askCursor(lambda: ask(subject))

                    if isinstance(cursor, RecursionError): self.fail(f"the {kind} cursor of {view} recursed")

                    self.assertIs(ask(subject), cursor, f"the {kind} cursor of {view} is built again on each request")
                    self.assertFalse(hasattr(cursor, "TryPop") or hasattr(cursor, "Push"), f"the {kind} cursor of {view} writes")
                    self.assertEqual(_cursorHead(cursor), _CONTENT[0], f"the {kind} cursor of {view} has another head")
                    self.assertEqual(cursor.GetCount(), len(_CONTENT), f"the {kind} cursor of {view} counts otherwise")
                    self.assertEqual(tuple(cursor.AsIterable()), _CONTENT, f"the {kind} cursor of {view} reads another order")

    def test_a_view_cursor_follows_the_collection(self) -> None:
        """A cursor reads its view when it is read, not when it is asked for."""

        items: ObservableCollection[int] = _create()
        taken: ReadOnlyArray[tuple[str, str, IReadOnlyCountableEnumerableList[int]]] = tuple(
            (view, kind, ask(provide(items))) for view, provide in _OBSERVABLE_VIEWS for kind, ask in _VIEW_CURSORS)

        items.Insert(0, 9)

        for view, kind, cursor in taken:
            with self.subTest(view = view, cursor = kind):
                self.assertEqual(_cursorHead(cursor), 9, f"the {kind} cursor of {view} did not follow the collection")
                self.assertEqual(tuple(cursor.AsIterable()), (9,) + _CONTENT, f"the {kind} cursor of {view} did not follow the collection")

def _contentAfter(call: _Call) -> ReadOnlyArray[int]:
    """What a fresh collection holds after one call, with nothing listening."""

    items: ObservableCollection[int] = _create()

    call(items)

    return tuple(items.AsIterable())

def _writeFromHandler(channel: str, trigger: _Call, write: Converter[ObservableCollection[int], Any]) -> tuple[bool, Any, ReadOnlyArray[int]]:
    """Subscribes to one channel of a fresh collection a handler that attempts one write, fires the
    channel by trigger, and returns whether the handler ran, what its write answered and what the
    collection holds afterwards.

    The handler writes on its first call only. On a rebuilt defect the write goes through and may fire
    the same channel again, and a handler that wrote each time would chain to the empty collection or to
    RecursionError rather than answer. It catches what its write raises, so the trigger ends normally:
    what reaches an outer call when a handler does not catch is R, which is not a defect and is not
    asserted here."""

    items: ObservableCollection[int] = _create()
    called: bool = False
    answer: Any = None

    def handle(sender: IObservableCollection[int], args: CollectionChangedEventArgs) -> None:
        nonlocal called, answer

        if called: return

        called = True
        answer = _attempt(items, write)

    getattr(items.GetEventManager(), channel)(handle)

    _attempt(items, trigger)

    return called, answer, tuple(items.AsIterable())

# The fourteen write paths of D-107, each attempted from a handler: the six single-item writes, the four
# that reach several items, the two cursors and the two projections that write.
_REENTRANT_WRITES: ReadOnlyArray[tuple[str, Converter[ObservableCollection[int], Any]]] = (
    ("TryRemoveAt",         lambda o: o.TryRemoveAt(0)),
    ("Add",                 lambda o: o.Add(9)),
    ("Insert",              lambda o: o.Insert(0, 9)),
    ("SetAt",               lambda o: o.SetAt(0, 9)),
    ("Move",                lambda o: o.Move(0, 1)),
    ("Swap",                lambda o: o.Swap(0, 1)),
    ("reverse()",           lambda o: o.AsMutableSequence().reverse()),
    ("Clear",               lambda o: o.Clear()),
    ("AddRange",            lambda o: o.AddRange((8, 9))),
    ("RemoveRange",         lambda o: o.RemoveRange(0, 1)),
    ("queued TryPop",       lambda o: o.AsQueuedCursor().TryPop()),
    ("stacked Push",        lambda o: o.AsStackedCursor().Push(9)),
    ("AsReversed().Add",    lambda o: o.AsReversed().Add(9)),
    ("AsFixedSize().SetAt", lambda o: o.AsFixedSize().SetAt(0, 9)))

# What a handler may still do with the collection it listens to.
_HANDLER_READS: ReadOnlyArray[tuple[str, Converter[ObservableCollection[int], Any]]] = (
    ("GetCount",                lambda o: o.GetCount()),
    ("ToString",                lambda o: o.ToString()),
    ("Contains",                lambda o: o.Contains(2)),
    ("GetAt",                   lambda o: o.GetAt(0)),
    ("a read-only cursor head", lambda o: _cursorHead(o.AsReadOnly().AsQueuedCursor())))

class TestAHandlerCannotChangeTheCollectionItListensTo(unittest.TestCase):
    """D-107. The collection refuses to be changed while it invokes its handlers: each write hook asserts
    reentrancy first. The assertion asked a monitor that was busy only while a handler was being added,
    never while handlers ran, so a handler's write went through: a removal from an OnItemRemoved handler
    chained until the collection was empty, an addition from an OnItemAdded one until RecursionError.
    The handlers now run inside the monitor (b1adfcb, 870a5d1), and a subscription asserts the monitor
    free before entering it (dc3d94e), since entering it from a handler and leaving it freed it while the
    invocation still ran. No bench wrote from a handler.

    Neither R nor R' is contradicted: each handler catches what it is refused, so that nothing is
    asserted of what reaches an outer call when a handler does not (R); and each is alone on its channel
    and refused all the same (R')."""

    def test_a_write_from_a_handler_is_refused_on_every_path(self) -> None:
        trigger: _Call = lambda o: o.TryRemoveAt(0)
        expected: ReadOnlyArray[int] = _contentAfter(trigger)

        for name, write in _REENTRANT_WRITES:
            with self.subTest(write = name):
                called, answer, content = _writeFromHandler("OnItemRemoved", trigger, write)

                self.assertTrue(called, "the removal did not reach the handler; the bench measures nothing")
                self.assertIsInstance(answer, InvalidOperationError, f"{name} from a handler went through, answering {answer!r}, rather than being refused")
                self.assertEqual(content, expected, f"{name} from a handler changed the collection; only the removal that fired it may stand")

    def test_a_write_from_a_handler_is_refused_on_every_channel(self) -> None:
        """Add, from a handler of each channel the surface declares, the channel fired by the first
        elementary operation that reaches it."""

        triggers: dict[str, tuple[str, _Call]] = {}

        for name, call, channel in _ELEMENTARY: triggers.setdefault(channel, (name, call))

        for channel, _ in _CHANNELS:
            with self.subTest(channel = channel):
                self.assertIn(channel, triggers, f"no elementary operation reaches {channel}")

                name, trigger = triggers[channel]
                called, answer, content = _writeFromHandler(channel, trigger, lambda o: o.Add(9))

                self.assertTrue(called, f"{name} did not reach {channel}; the bench measures nothing")
                self.assertIsInstance(answer, InvalidOperationError, f"Add from a handler of {channel} went through, answering {answer!r}, rather than being refused")
                self.assertEqual(content, _contentAfter(trigger), f"Add from a handler of {channel} changed the collection")

    def test_a_handler_still_reads(self) -> None:
        """The counter-example: the guard refuses writes, not access. A handler reads what any caller
        reads once the removal is made."""

        items: ObservableCollection[int] = _create()
        answers: dict[str, Any] = {}

        def handle(sender: IObservableCollection[int], args: CollectionChangedEventArgs) -> None:
            for name, read in _HANDLER_READS: answers[name] = _attempt(items, read)

        items.GetEventManager().OnItemRemoved(handle)
        items.TryRemoveAt(0)

        reference: ObservableCollection[int] = _create()

        reference.TryRemoveAt(0)

        for name, read in _HANDLER_READS:
            with self.subTest(read = name): self.assertEqual(answers.get(name), read(reference), f"{name} from a handler answered otherwise than outside one")

    def test_a_handler_that_raises_leaves_the_collection_usable(self) -> None:
        """An error leaves the invocation, and the monitor with it: the next subscription and the next
        write pass, and the new handler hears the write."""

        items: ObservableCollection[int] = _create()
        raised: list[bool] = []
        added: list[CollectionChangedAction] = []

        def handle(sender: IObservableCollection[int], args: CollectionChangedEventArgs) -> None:
            raised.append(True)

            raise ValueError("raised by the handler")

        items.GetEventManager().OnItemRemoved(handle)

        _attempt(items, lambda o: o.TryRemoveAt(0))

        self.assertEqual(raised, [True], "the removal did not reach the handler; the bench measures nothing")

        items.GetEventManager().OnItemAdded(lambda sender, args: added.append(args.GetAction()))
        items.Add(9)

        self.assertEqual(tuple(items.AsIterable()), _CONTENT[1:] + (9,), "the write after a handler that raised did not go through")
        self.assertEqual(added, [CollectionChangedAction.Add], "the subscription after a handler that raised was not heard")

    def test_subscribing_from_a_handler_is_refused(self) -> None:
        """Subscribing from a handler entered the busy monitor and, leaving it, freed it while the
        invocation still ran, so the handler's next write went through. It is refused now, as a write
        is, and the write that follows it is refused too."""

        items: ObservableCollection[int] = _create()
        answers: dict[str, Any] = {}

        def subscribe(o: ObservableCollection[int]) -> Any: return o.GetEventManager().OnItemAdded(lambda sender, args: None)

        def handle(sender: IObservableCollection[int], args: CollectionChangedEventArgs) -> None:
            answers["subscription"] = _attempt(items, subscribe)
            answers["write"] = _attempt(items, lambda o: o.Add(9))

        items.GetEventManager().OnItemRemoved(handle)

        _attempt(items, lambda o: o.TryRemoveAt(0))

        self.assertIsInstance(answers.get("subscription"), InvalidOperationError, f"a subscription from a handler went through, answering {answers.get('subscription')!r}, rather than being refused")
        self.assertIsInstance(answers.get("write"), InvalidOperationError, f"the write after it answered {answers.get('write')!r}: the subscription freed the monitor")
        self.assertEqual(tuple(items.AsIterable()), _CONTENT[1:], "the handler changed the collection")

    def test_a_handler_changes_another_collection(self) -> None:
        """The counter-example: each collection has its own monitor. A handler of one subscribes to
        another and writes to it, and the new handler hears the write."""

        items: ObservableCollection[int] = _create()
        other: ObservableCollection[int] = _create()
        added: list[CollectionChangedAction] = []
        answers: dict[str, Any] = {}

        def subscribe(o: ObservableCollection[int]) -> Any: return o.GetEventManager().OnItemAdded(lambda sender, args: added.append(args.GetAction()))

        def handle(sender: IObservableCollection[int], args: CollectionChangedEventArgs) -> None:
            answers["subscription"] = _attempt(other, subscribe)
            answers["write"] = _attempt(other, lambda o: o.Add(9))

        items.GetEventManager().OnItemRemoved(handle)
        items.TryRemoveAt(0)

        for step in ("subscription", "write"):
            with self.subTest(step = step): self.assertNotIsInstance(answers.get(step), Exception, f"the {step} on another collection was refused: {answers.get(step)}")

        self.assertEqual(tuple(other.AsIterable()), _CONTENT + (9,), "the write to another collection did not go through")
        self.assertEqual(added, [CollectionChangedAction.Add], "the handler subscribed to another collection did not hear its write")

def _runBench(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

class TestTheObservableCollectionBenchesCanFail(unittest.TestCase):
    """The benches of D-101, D-105, D-106 and D-107, and of the one announcement of PushItems, run
    against the code as it stood before each was closed: green on the intact tree, red on the rebuilt
    one, and red on their assertions rather than on an error. The views are reached through the objects;
    EventMonitor and BufferedStackBase by their public names."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any]) -> None:
        self.assertTrue(_runBench(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with mock.patch.multiple(target, **rebuilt): broken: unittest.TestResult = _runBench(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")
        self.assertEqual(broken.errors, [], f"{name} fell on an error rather than on its assertions")

    def test_the_mutability_bench_falls_when_the_fixed_size_view_answers_read_only(self) -> None:
        """As before ba61adc: GetMutability sat under @final on the base both views share, and answered
        ReadOnly. Each view carries its own since; the fixed-size one is given that answer back."""

        def readOnly(self: Any) -> Mutability: return Mutability.ReadOnly

        self.__assertFalls(TestEachObservableFaceDeclaresItsMutability, "test_each_face_declares_its_mutability_and_renders_by_it",
                           type(_create().AsFixedSize()), {"GetMutability": readOnly})

    def test_the_cursor_bench_falls_when_the_collection_has_no_cursors(self) -> None:
        """As before bd908d4: the collection derived from no cursor provider, and its cursors resolved to
        the abstract members of ILinkedCursorProvider, which answer None. ICursorProvider carries them
        today and List derives from it too, so the absence is not rebuilt by removing them there: the
        abstract members are put back on ObservableCollection, ahead of ICursorProvider, which gives the
        collection exactly the resolution it had and leaves every other provider alone."""

        abstract: dict[str, Any] = {name: vars(ILinkedCursorProvider)[name] for name in ("AsQueuedCursor", "AsStackedCursor")}

        self.__assertFalls(TestTheObservableCollectionProvidesCursors, "test_the_collection_provides_mutable_cursors", ObservableCollection, abstract)

    def test_the_view_cursor_bench_falls_when_a_view_asks_itself(self) -> None:
        """As before bd908d4: the base both views share asked the read-only side of their container for
        its cursors, and that side is the read-only view. The two members are put back on that base,
        reached as the first class the two views' MROs share; IReadOnlyCursorProvider, after it in both,
        carries the cursors today."""

        def queued(self: Any) -> Any: return self._GetInnerContainer().AsReadOnly().AsQueuedCursor()
        def stacked(self: Any) -> Any: return self._GetInnerContainer().AsReadOnly().AsStackedCursor()

        items: ObservableCollection[int] = _create()
        shared: type = next(cls for cls in type(items.AsReadOnly()).__mro__ if cls in type(items.AsFixedSize()).__mro__)

        self.__assertFalls(TestTheObservableViewsProvideCursors, "test_a_view_provides_read_only_cursors", shared, {"AsQueuedCursor": queued, "AsStackedCursor": stacked})

    def test_the_push_items_bench_falls_when_the_stack_pushes_item_by_item(self) -> None:
        """As before edf8dbe: the stacked cursor added its items one at a time, by Add on an empty stack
        and by TryInsert at 0, 1, 2 otherwise. BufferedStackBase carries PushItems; the closures of that
        version are rebuilt as the loop they amounted to."""

        def itemByItem(self: Any, items: Any) -> None:
            container: Any = self._GetSpecializedContainer()

            if self.IsEmpty():
                for item in items: container.Add(item)

            else:
                for index, item in enumerate(items): container.TryInsert(index, item)

        self.__assertFalls(TestTheObservableCollectionProvidesCursors, "test_pushing_several_items_announces_once", BufferedStackBase, {"PushItems": itemByItem})

    def test_the_write_benches_fall_when_handlers_run_outside_the_monitor(self) -> None:
        """As at 8d136f3: the collection invoked its handlers directly, and the monitor was busy only
        while a handler was being added. EventMonitor carries _Invoke, through which the collection
        invokes them now; it is rebuilt as that direct call."""

        def direct(self: Any, eventManager: Any, sender: Any, args: Any) -> None: eventManager.Invoke(sender, args)

        for test in ("test_a_write_from_a_handler_is_refused_on_every_path", "test_a_write_from_a_handler_is_refused_on_every_channel"):
            with self.subTest(bench = test): self.__assertFalls(TestAHandlerCannotChangeTheCollectionItListensTo, test, EventMonitor, {"_Invoke": direct})

    def test_the_subscription_bench_falls_when_subscribing_enters_the_busy_monitor(self) -> None:
        """As at 870a5d1: _AddHandler entered the monitor without asserting it free, and leaving it freed
        it. EventMonitor carries _AddHandler; its monitor is read under the name Python gives
        EventMonitor.__monitor, the attribute that version used."""

        def entering(self: Any, eventManager: Any, handler: Any) -> Any:
            with self._EventMonitor__monitor: return eventManager.Add(handler)

        self.__assertFalls(TestAHandlerCannotChangeTheCollectionItListensTo, "test_subscribing_from_a_handler_is_refused", EventMonitor, {"_AddHandler": entering})

if __name__ == "__main__": unittest.main()
