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
from typing import Any, Callable

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import List
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Extensions import IList, IOrderedSet
from WinCopies.Collections.ObjectModel.Collection import (CollectionChangedAction, CollectionChangedEventArgs,
                                                          IObservableCollection, ObservableCollection)

type _Call = Callable[[Any], Any]
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

def _listen(call: _Call, source: Callable[[ObservableCollection[int]], Any]|None = None) -> tuple[ReadOnlyArray[_Record], Any]:
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
_PROJECTED: ReadOnlyArray[tuple[str, _Call, Callable[[ObservableCollection[int]], Any], str]] = (
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
            with self.subTest(channel = channel):
                self.assertIn(channel, reached, f"{channel} is declared and nothing reaches it")

    def test_nothing_reaches_a_channel_the_surface_does_not_declare(self) -> None:
        declared: set[str] = {channel for channel, _ in _CHANNELS}

        for name, call, _ in _ELEMENTARY:
            records, _ = _listen(call)

            for channel, _ in records:
                with self.subTest(call = name, channel = channel):
                    self.assertIn(channel, declared)

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

def _constrained() -> tuple[IOrderedSet[int], IList[int], ObservableCollection[int]]:
    """An observable collection over a container that refuses some writes.

    An ordered set's list view is the one container in the tree whose positional write can
    be refused for a reason the wrapper's own index validation cannot see: the index is
    valid and the value is not. Every other refusal is filtered upstream, before any hook
    is reached, which is why the table above cannot exercise this clause -- a hook that
    announced unconditionally would still pass it.
    """

    items: IOrderedSet[int] = CreateOrderedSet(_CONTENT)
    view: IList[int] = items.AsList()

    return items, view, ObservableCollection[int](view)

class TestARefusalThatReachesTheHookIsSilent(unittest.TestCase):
    """A hook that did not write does not announce.

    The guard is real -- each override reads what super() answered -- and this is what
    holds it in place. Writing a value the ordered set already holds elsewhere passes the
    index validation and is refused by the container, so the hook runs and returns False.
    """

    def test_a_write_the_container_refuses_announces_nothing(self) -> None:
        _, _, items = _constrained()
        listener: _Listener = _Listener(items)

        items.TrySetAt(1, 3)

        self.assertEqual(tuple(items.AsIterable()), _CONTENT, "the refused write went through; the bench is not measuring a refusal")
        self.assertEqual(listener.GetRecords(), (), f"a refused write announced {listener.GetRecords()}")

    def test_an_accepted_write_on_the_same_container_announces_once(self) -> None:
        """The counter-example, so the clause above cannot pass by the container refusing
        everything."""

        _, _, items = _constrained()
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
        _, bare, _ = _constrained()
        _, _, wrapped = _constrained()

        self.assertEqual(wrapped.TrySetAt(1, 3), bare.TrySetAt(1, 3),
                         "the wrapper reports a write its container refused")

    def test_the_wrapper_raises_where_its_container_raises(self) -> None:
        """SetAt is final on ISetter and raises when TrySetAt answers False, so a wrapper
        whose hook stayed silent broke the one member whose contract is to write or raise."""

        _, _, wrapped = _constrained()

        with self.assertRaises(KeyError): wrapped.SetAt(1, 3)

        self.assertEqual(tuple(wrapped.AsIterable()), _CONTENT, "the refused write went through")

    def test_the_wrapper_refuses_the_scalar_subscript(self) -> None:
        """The protocol face reaches the same seam, and silence there is a write that reads
        as having happened."""

        _, _, wrapped = _constrained()

        with self.assertRaises(Exception): wrapped.AsMutableSequence()[1] = 3

        self.assertEqual(tuple(wrapped.AsIterable()), _CONTENT, "the refused write went through")

    def test_an_accepted_write_still_answers_true(self) -> None:
        """The counter-example: the clause above must not pass by refusing everything."""

        _, _, wrapped = _constrained()

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

# A bulk insertion announces once or once per item depending on how it is spelled:
# InsertRange reaches the _InsertItems hook and announces the range, while AddRange has no
# hook and is written as repeated Add on ICollection, so it announces each item. The
# protocol's extend() is the same case as AddRange, being written as repeated append.
# This is the shape D-55 had -- a bulk act with no hook of its own, seen by the observable
# layer as its elements -- and it is D-57, presented and not arbitrated: either spelling may
# be the one to change. The bench asserts the agreement rather than a side, so whichever way
# it is settled closes it.
_BULK: ReadOnlyArray[tuple[str, _Call]] = (
    ("InsertRange", lambda o: o.InsertRange(1, (7, 8))),
    ("AddRange",    lambda o: o.AddRange((7, 8))),
    ("extend()",    lambda o: o.AsMutableSequence().extend((7, 8))))

class TestBulkInsertionAnnouncesCoherently(unittest.TestCase):
    """D-57: the same bulk act announces a different number of times per spelling."""

    @unittest.expectedFailure
    def test_every_bulk_insertion_announces_the_same_count(self) -> None:
        counts: dict[str, int] = {name: len(_listen(call)[0]) for name, call in _BULK}

        self.assertEqual(len(set(counts.values())), 1,
                         f"two items inserted announce a different number of events per spelling: {counts}")

if __name__ == "__main__": unittest.main()
