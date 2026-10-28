"""
Unit tests for the singly linked lists (WinCopies.Collections.Linked.Singly), and for the stacks
and queues of every other family, which all implement the interfaces of this module.

IListBase gives a stack two ways of taking several items at once: PushItems pushes them one by
one, so that they pop in reverse, and PushRange lays them as a block, in the order received. A
queue tells the two apart in nothing. Until D-109 closed, the families did not agree on either
-- the list cursors, the singly linked lists and the doubly linked ones each kept their own
order under the one interface -- and no bench pushed anything onto a stack. So the order is
asserted here on every family at once, in one table, where a family that drifts stands out
against the others.
"""

import unittest

from collections.abc import Callable, Iterable, Iterator
from typing import Any, cast
from unittest import mock

import WinCopies.Collections.Linked.Singly as Singly
import WinCopies.Collections.Linked.Singly.Buffer as Buffer

from WinCopies.Collections import ReadOnlyArray, EnumerationOrder
from WinCopies.Collections.Abstract.Linked import SinglyLinkedList, SinglyLinkedListBase
from WinCopies.Collections.Abstraction.Collection import CreateList
from WinCopies.Collections.Abstraction.Selection import Converters
from WinCopies.Collections.Abstraction.Selection.Collection import List as SelectionList
from WinCopies.Collections.Core import ICountable
from WinCopies.Collections.Enumeration.Core import IEnumerable
from WinCopies.Collections.Extensions.Collection import BufferedStackBase
from WinCopies.Collections.Linked.Doubly.Welded import CreateList as CreateDoublyList
from WinCopies.Collections.Linked.Singly import IListBase, IList, IReadOnlyList
from WinCopies.Collections.Linked.Singly.Priority import PriorityLevel, PriorityItemList, IPriorityList, PriorityQueue, PriorityStack
from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import Function, Converter

type _Factory = Function[IListBase[int]]
type _Creator = Converter[Iterable[int], IListBase[int]]
type _Push = Callable[[IListBase[int], Iterable[int]], None]
type _Observation = tuple[int|None, int|None, ReadOnlyArray[int]|None]

_PUSHED: ReadOnlyArray[int] = (1, 2, 3)

_OPERATIONS: ReadOnlyArray[tuple[str, _Push]] = (
    ("PushItems", lambda items, pushed: items.PushItems(pushed)),
    ("PushRange", lambda items, pushed: items.PushRange(pushed)))

_ORDERS: dict[tuple[str, str], ReadOnlyArray[int]] = {
    ("stack", "PushItems"): (3, 2, 1, 9), ("stack", "PushRange"): (1, 2, 3, 9),
    ("queue", "PushItems"): (9, 1, 2, 3), ("queue", "PushRange"): (9, 1, 2, 3)}
"""What a collection holding 9 pops once [1, 2, 3] is pushed onto it: on a stack, the items
pushed one by one come off in reverse and the block in the order it was given; on a queue, both
come off after the 9, in the order given."""

def _drain(items: IListBase[int]) -> ReadOnlyArray[int]:
    """Everything the collection pops, from the first item out to the last, emptying it."""

    popped: list[int] = []

    while True:
        item: INullable[int] = items.TryPop()

        if not item.HasValue(): return tuple(popped)

        popped.append(item.GetValue())

def _head(items: IListBase[int]) -> int|None:
    head: INullable[int] = items.TryPeek()

    return head.GetValue() if head.HasValue() else None

def _selection(items: list[int]) -> SelectionList[int, int]:
    """A converting list over items, which reads each of them plus 10."""

    return SelectionList[int, int](CreateList(items), Converters[int, int](lambda item: item + 10, lambda item: item - 10))

def _prioritised[T: IPriorityList[int, PriorityLevel]](items: T, values: Iterable[int] = (9,)) -> T:
    """A priority list, which takes no items when it is created, given values at its normal level."""

    for value in values: items.Push(value)

    return items

class _ShiftedSinglyLinkedList(SinglyLinkedList[int, int]):
    """Abstract/Linked has no concrete wrapper of its own: this one reads each item of the list it
    wraps plus 10, as the probes of D-109 did. It writes IsEmpty, GetOrder and AsReadOnly, which the
    base leaves to its subclasses; AsReadOnly, which nothing here asks, only raises."""

    def __init__(self, items: IList[int]) -> None: super().__init__(items)

    def _Convert(self, item: int) -> int: return item + 10
    def _ConvertBack(self, item: int) -> int: return item - 10

    def IsEmpty(self) -> bool: return self._GetInnerContainer().IsEmpty()

    def GetOrder(self) -> EnumerationOrder: return self._GetInnerContainer().GetOrder()

    def AsReadOnly(self) -> IReadOnlyList[int]: raise NotImplementedError()

_FAMILIES: ReadOnlyArray[tuple[str, _Factory, _Factory]] = (
    ("list cursor",                        lambda: CreateList([9]).AsStackedCursor(),                   lambda: CreateList([9]).AsQueuedCursor()),
    ("SelectionList cursor",               lambda: _selection([-1]).AsStackedCursor(),                  lambda: _selection([-1]).AsQueuedCursor()),
    ("Linked.Singly",                      lambda: Singly.CreateStack([9]),                             lambda: Singly.CreateQueue([9])),
    ("Linked.Singly, countable",           lambda: Singly.CreateCountableEnumerableStack([9]),          lambda: Singly.CreateCountableEnumerableQueue([9])),
    ("Linked.Singly.Buffer",               lambda: Buffer.CreateBufferedStack([9]),                     lambda: Buffer.CreateBufferedQueue([9])),
    ("Linked.Singly.Buffer, countable",    lambda: Buffer.CreateCountableEnumerableBufferedStack([9]),  lambda: Buffer.CreateCountableEnumerableBufferedQueue([9])),
    ("Linked.Singly.Priority",             lambda: _prioritised(PriorityStack[int]()),                  lambda: _prioritised(PriorityQueue[int]())),
    ("Linked.Doubly cursor",               lambda: CreateDoublyList([9]).AsStackedCursor(),             lambda: CreateDoublyList([9]).AsQueuedCursor()),
    ("Abstract.Linked over Linked.Singly", lambda: _ShiftedSinglyLinkedList(Singly.CreateStack([-1])), lambda: _ShiftedSinglyLinkedList(Singly.CreateQueue([-1]))))
"""Every family of stacks and queues at hand, each holding 9 alone: its stack, then its queue. The
converting families hold -1 and read it as 9."""

class TestEveryStackAndQueuePushesInOneOrder(unittest.TestCase):
    """D-91 and D-109. The list cursor's stack inserted each item at the index of the one before
    it, so that [1, 2, 3] pushed onto [9] read [2, 3, 1, 9] (D-91). Once that was fixed, the cursors
    and Abstraction.Linked laid the items as a block while Linked.Singly pushed them one by one,
    under the one IStack (D-109). Its correction parted PushItems from PushRange, and on the way
    left a stack created from items popping them in the order given, PushRange doing nothing on
    Abstraction.Linked and Abstract.Linked, and PriorityStack's PushRange pushing one by one. No
    bench pushed anything onto a stack, so each was seen with a probe."""

    def test_every_family_pushes_items_one_by_one_and_a_range_as_a_block(self) -> None:
        for family, stack, queue in _FAMILIES:
            for kind, create in (("stack", stack), ("queue", queue)):
                for operation, push in _OPERATIONS:
                    with self.subTest(family = family, kind = kind, operation = operation):
                        items: IListBase[int] = create()

                        push(items, _PUSHED)

                        self.assertEqual(_drain(items), _ORDERS[kind, operation], f"{operation} on the {kind} of {family} pops another order")

    def test_a_stack_created_from_items_pops_them_in_reverse(self) -> None:
        """Creation pushes the items one by one. When 4f86c23 made it lay them as a block, the
        three callers that reverse a sequence through a stack stopped reversing, and 561 benches
        fell elsewhere in the suite (4.29 §3); this one names the cause."""

        stacks: ReadOnlyArray[tuple[str, _Creator]] = (
            ("Linked.Singly.CreateStack",                                   Singly.CreateStack),
            ("Linked.Singly.CreateCountableEnumerableStack",                Singly.CreateCountableEnumerableStack),
            ("Linked.Singly.Buffer.CreateBufferedStack",                    Buffer.CreateBufferedStack),
            ("Linked.Singly.Buffer.CreateCountableEnumerableBufferedStack", Buffer.CreateCountableEnumerableBufferedStack))

        for family, create in stacks:
            with self.subTest(family = family): self.assertEqual(_drain(create(_PUSHED)), (3, 2, 1), f"{family}({list(_PUSHED)}) pops another order")

class _SourceError(Exception):
    """What a failing source raises, so that a bench tells it from any error of the collection."""

def _failing() -> Iterator[int]:
    yield 1
    yield 2

    raise _SourceError()

_SINGLY_LINKED: ReadOnlyArray[tuple[str, str, _Creator, bool]] = (
    ("Linked.Singly.CreateQueue",                                   "queue", Singly.CreateQueue,                            False),
    ("Linked.Singly.CreateCountableQueue",                          "queue", Singly.CreateCountableQueue,                   True),
    ("Linked.Singly.CreateEnumerableQueue",                         "queue", Singly.CreateEnumerableQueue,                  False),
    ("Linked.Singly.CreateCountableEnumerableQueue",                "queue", Singly.CreateCountableEnumerableQueue,         True),
    ("Linked.Singly.CreateStack",                                   "stack", Singly.CreateStack,                            False),
    ("Linked.Singly.CreateCountableStack",                          "stack", Singly.CreateCountableStack,                   True),
    ("Linked.Singly.CreateEnumerableStack",                         "stack", Singly.CreateEnumerableStack,                  False),
    ("Linked.Singly.CreateCountableEnumerableStack",                "stack", Singly.CreateCountableEnumerableStack,         True),
    ("Linked.Singly.Buffer.CreateBufferedQueue",                    "queue", Buffer.CreateBufferedQueue,                    False),
    ("Linked.Singly.Buffer.CreateCountableEnumerableBufferedQueue", "queue", Buffer.CreateCountableEnumerableBufferedQueue, False),
    ("Linked.Singly.Buffer.CreateBufferedStack",                    "stack", Buffer.CreateBufferedStack,                    False),
    ("Linked.Singly.Buffer.CreateCountableEnumerableBufferedStack", "stack", Buffer.CreateCountableEnumerableBufferedStack, False),
    ("Linked.Singly.Priority.PriorityQueue",                        "queue", lambda items: _prioritised(PriorityQueue[int](), items), False),
    ("Linked.Singly.Priority.PriorityStack",                        "stack", lambda items: _prioritised(PriorityStack[int](), items), False))
"""The stacks and queues of Linked/Singly, each with whether its count is asserted. A countable
buffer does not count the items it is created with (D-110, out of these benches), so its count is
not."""

def _enumerate(items: IListBase[int]) -> ReadOnlyArray[int]|None:
    """The items of a collection that enumerates them, read without popping any."""

    return tuple(cast(IEnumerable[int], items).AsIterable()) if isinstance(items, IEnumerable) else None

def _observe(items: IListBase[int], counted: bool) -> _Observation:
    """What a reader sees of a collection: its head, its count when it is asserted, and its items
    when it enumerates them."""

    return (_head(items), items.GetCount() if counted and isinstance(items, ICountable) else None, _enumerate(items))

class TestASinglyLinkedPushIsAtomic(unittest.TestCase):
    """D-109, its point (3). From 4f86c23, Linked.Singly's StackBase laid a block from the top down,
    holding the former content aside in a local and hanging it back under the block only once the
    source was spent: a source that failed left the block without the content, [1, 2] where [9]
    was, and a source that read the stack saw it so (4.29 §5). A queue, which pushed one by one,
    kept the start of the block, and a countable list counted it. e81d816 builds the block apart
    and welds it on at once, for the queues as for the stacks, and counts what it pushed only after
    the weld: the collection changes whole or not at all. No bench gave a push a source that
    fails."""

    def test_a_source_that_fails_leaves_the_collection_as_it_was(self) -> None:
        for family, _, create, counted in _SINGLY_LINKED:
            for operation, push in _OPERATIONS:
                with self.subTest(family = family, operation = operation):
                    items: IListBase[int] = create([9])
                    before: _Observation = _observe(items, counted)

                    with self.assertRaises(_SourceError, msg = f"{operation} on {family} did not let the source's error through"): push(items, _failing())

                    self.assertEqual(_observe(items, counted), before, f"{operation} on {family} kept part of a block whose source failed")
                    self.assertEqual(_drain(items), (9,), f"{operation} on {family} lost or kept items when its source failed")

    def test_a_source_that_reads_the_collection_sees_it_as_it_was(self) -> None:
        for family, kind, create, counted in _SINGLY_LINKED:
            for operation, push in _OPERATIONS:
                with self.subTest(family = family, operation = operation):
                    items: IListBase[int] = create([9])
                    before: _Observation = _observe(items, counted)
                    seen: list[_Observation] = []

                    def reading() -> Iterator[int]:
                        yield 1
                        yield 2

                        seen.append(_observe(items, counted))

                        yield 3

                    push(items, reading())

                    self.assertEqual(seen, [before], f"the source of {operation} on {family} saw the collection while it was pushed onto")
                    self.assertEqual(_drain(items), _ORDERS[kind, operation], f"{operation} on {family} pops another order once its source is spent")

_QUEUES: ReadOnlyArray[tuple[str, _Creator]] = tuple((family, create) for family, kind, create, _ in _SINGLY_LINKED if kind == "queue")

class TestAQueueKeepsWhatItHeldWhenABlockFollows(unittest.TestCase):
    """D-109, the regressions of its point (3). The weld of e81d816 hangs a block under the last
    node of a queue, and takes a queue without one for an empty queue; but Push, on an empty queue,
    recorded the first node alone, so that a block pushed after it took the place of its item
    (4.37 §3). 5f36430 has that Push record the last node too. A buffered queue still lost its
    content, whether it was created with it or given it by Push: e81d816 renamed _SetLast to
    _SetLastCookie everywhere but in Buffer.py, so that BufferedQueue defined the setter under the
    old name, the one the weld calls did nothing, and its last node was never recorded (4.38 §3),
    until d4c9197. No bench pushed a block onto a queue that held anything."""

    def test_a_block_follows_a_single_push(self) -> None:
        for family, create in _QUEUES:
            for operation, push in _OPERATIONS:
                with self.subTest(family = family, operation = operation):
                    items: IListBase[int] = create(())

                    items.Push(9)
                    push(items, _PUSHED)

                    self.assertEqual(_drain(items), (9, 1, 2, 3), f"{operation} on {family} after a single Push pops another order")

    def test_a_block_follows_what_the_queue_was_created_with(self) -> None:
        for family, create in _QUEUES:
            for operation, push in _OPERATIONS:
                with self.subTest(family = family, operation = operation):
                    items: IListBase[int] = create([9])

                    push(items, _PUSHED)

                    self.assertEqual(_drain(items), (9, 1, 2, 3), f"{operation} on {family} created with [9] pops another order")

                    items = create([8, 9])

                    items.TryPop()
                    push(items, (1, 2))

                    self.assertEqual(_drain(items), (9, 1, 2), f"{operation} on {family} created with [8, 9] and popped once pops another order")

class TestThePriorityListsPopTheHighestLevelFirst(unittest.TestCase):
    """Found while measuring D-109 (4.33 §3) and closed by 66cde57. A priority list keeps one list
    per level, at the index of the level less the lowest one; _Convert turned that difference back
    into a PriorityLevel, so that every level above Normal, whose difference names no level,
    raised ValueError. No bench pushed at a level."""

    def test_one_item_at_every_level_pops_from_the_highest_down(self) -> None:
        lists: ReadOnlyArray[tuple[str, Function[IPriorityList[int, PriorityLevel]]]] = (("PriorityQueue", PriorityQueue[int]), ("PriorityStack", PriorityStack[int]))

        for family, create in lists:
            with self.subTest(family = family):
                items: IPriorityList[int, PriorityLevel] = create()

                for level in PriorityLevel: items.PushAt(level, level.value)

                self.assertEqual(_drain(items), tuple(range(PriorityLevel.Highest.value, PriorityLevel.Lowest.value - 1, -1)), f"{family} pops its levels in another order")

class TestAConvertingListStacksOnTop(unittest.TestCase):
    """D-92. A converting list's cursors write through a cursor of its source, and both went through
    the source's queued one: Push on the stacked cursor of a SelectionList appended at the end, as a
    queue does. TryPeek and TryPop read the front of both, which is why only Push showed it. No
    bench asked a converting list for a cursor."""

    def test_each_cursor_pushes_at_its_own_end(self) -> None:
        """The list reads [11, 12, 13]."""

        cursors: ReadOnlyArray[tuple[str, Converter[SelectionList[int, int], IListBase[int]], ReadOnlyArray[int]]] = (
            ("stacked", lambda items: items.AsStackedCursor(), (10, 11, 12, 13)),
            ("queued",  lambda items: items.AsQueuedCursor(),  (11, 12, 13, 10)))

        for kind, cursorOf, pushed in cursors:
            with self.subTest(cursor = kind):
                items: SelectionList[int, int] = _selection([1, 2, 3])
                cursor: IListBase[int] = cursorOf(items)

                cursor.Push(10)

                self.assertEqual(tuple(items.AsIterable()), pushed, f"Push(10) on the {kind} cursor wrote elsewhere")
                self.assertEqual(_head(cursor), pushed[0], f"the {kind} cursor peeks another item")

                popped: INullable[int] = cursor.TryPop()

                self.assertEqual(popped.GetValue() if popped.HasValue() else None, pushed[0], f"the {kind} cursor pops another item")
                self.assertEqual(tuple(items.AsIterable()), pushed[1:], f"TryPop on the {kind} cursor removed another item")

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

def _detachedBlock(self: Any, items: Iterable[Any]) -> None:
    """Linked.Singly's StackBase.PushItems as it stood at 4f86c23, which 70e4d1e renamed PushRange
    and e81d816 replaced: the first item becomes the top with nothing under it, the others are
    chained below it, and the former content is hung back under the last of them once the source
    is spent."""

    push: Callable[[Any], Any]|None = None

    def pushFirst(item: Any) -> Any:
        cookie: Any

        def pushNext(item: Any) -> Any:
            nonlocal cookie

            return (cookie := self._SetNext(item, cookie))

        nonlocal push

        cookie = self._SetFirstCookie(item)

        push = pushNext

        return cookie

    first: Any = self._GetFirst()
    cookie: Any = None

    push = pushFirst

    for value in items: cookie = push(value)

    if not (first is None or cookie is None): cookie.SetNext(first)

class TestTheStackAndQueueBenchesCanFail(unittest.TestCase):
    """The benches above, run against the code as it stood before each fix: green on the intact
    tree, red on the rebuilt one. A class is reached through its public name or through the
    object, and is the one that carries the attribute rebuilt, or carried it then."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any]) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with mock.patch.multiple(target, **rebuilt): broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")

    def test_the_order_bench_falls_when_the_list_cursor_misplaces_its_items(self) -> None:
        """As before fea5bdb (D-91): BufferedStackBase.PushItems, which carries the push of the list
        cursors' stack and of the converting list's, which hands it on, inserted each item at the
        index of the one before it. As at fea5bdb, before edf8dbe: it laid the items as a block,
        added onto an empty stack and inserted from the top down otherwise, one TryInsert each,
        which swallowed a refusal (4.1 §7, 4.28 §2)."""

        def misplaced(self: Any, items: Iterable[Any]) -> None:
            adder: Callable[[int, Any], None]|None = None
            i: int = 0

            def insert(index: int, item: Any) -> None: self._GetSpecializedContainer().TryInsert(index, item)
            def add(index: int, item: Any) -> None:
                nonlocal adder

                if self.IsEmpty(): self._GetSpecializedContainer().Add(item)
                else: insert(index, item)

                adder = insertItem

            def insertItem(index: int, item: Any) -> None:
                nonlocal i

                i += 1

                insert(index, item)

            adder = add

            for item in items: adder(i, item)

        def inserted(self: Any, items: Iterable[Any]) -> None:
            adder: Callable[[Any], None]|None = None

            def add(item: Any) -> None:
                def add(item: Any) -> None: self._GetSpecializedContainer().Add(item)
                def insert(item: Any) -> None:
                    nonlocal adder

                    i: int = 0

                    def insert(index: int, item: Any) -> None: self._GetSpecializedContainer().TryInsert(index, item)
                    def insertItem(item: Any) -> None:
                        nonlocal i

                        i += 1

                        insert(i, item)

                    insert(i, item)

                    adder = insertItem

                nonlocal adder

                if self.IsEmpty():
                    add(item)

                    adder = add

                else: insert(item)

            adder = add

            for item in items: adder(item)

        for state, rebuilt in (("before fea5bdb", misplaced), ("before edf8dbe", inserted)):
            with self.subTest(state = state):
                self.__assertFalls(TestEveryStackAndQueuePushesInOneOrder, "test_every_family_pushes_items_one_by_one_and_a_range_as_a_block", BufferedStackBase, {"PushItems": rebuilt})

    def test_the_order_bench_falls_when_a_doubly_linked_stack_pushes_no_range(self) -> None:
        """As before 210a2b4. PushRange was abstract in IListBase since 70e4d1e, and an abstract
        method does nothing when it is called: Abstraction.Linked.StackBase did not define it, and
        its PushItems laid the items as a block, through AddFirstItems; nor did
        Abstract.Linked.SinglyLinkedListBase, which carries the wrappers' pushes. Each is rebuilt
        alone. Abstraction.Linked is gone since 2131975: the doubly linked stack is now the stacked
        cursor of the doubly linked list, and the class that carries its pushes is reached through
        that cursor."""

        def block(self: Any, items: Iterable[Any]) -> None: self._GetSpecializedContainer().AddFirstItems(items)
        def nothing(self: Any, items: Iterable[Any]) -> None: return None

        doubly: type = next(cls for cls in type(CreateDoublyList([9]).AsStackedCursor()).__mro__ if "PushRange" in vars(cls))

        for base, target, rebuilt in (("the doubly linked stacked cursor", doubly, {"PushItems": block, "PushRange": nothing}),
                                      ("Abstract.Linked.SinglyLinkedListBase", SinglyLinkedListBase, {"PushRange": nothing})):
            with self.subTest(base = base):
                self.__assertFalls(TestEveryStackAndQueuePushesInOneOrder, "test_every_family_pushes_items_one_by_one_and_a_range_as_a_block", target, rebuilt)

    def test_the_creation_bench_falls_when_a_stack_lays_its_items_as_a_block(self) -> None:
        """As at 4f86c23, until 70e4d1e: Linked.Singly's StackBase carried a PushItems that laid the
        items as a block. That PushItems is _IStackAdder's since e81d816; the substitution gives it
        back to StackBase, which every singly linked stack derives from."""

        self.__assertFalls(TestEveryStackAndQueuePushesInOneOrder, "test_a_stack_created_from_items_pops_them_in_reverse", Singly.StackBase, {"PushItems": _detachedBlock})

    def test_the_atomicity_benches_fall_when_a_stack_detaches_its_content(self) -> None:
        """As before e81d816: Linked.Singly's StackBase carried a PushRange, the PushItems of 4f86c23
        renamed, that detached the former content until the source was spent. That PushRange is
        _IAdder's since e81d816; the substitution gives it back to StackBase."""

        for name in ("test_a_source_that_fails_leaves_the_collection_as_it_was", "test_a_source_that_reads_the_collection_sees_it_as_it_was"):
            with self.subTest(bench = name): self.__assertFalls(TestASinglyLinkedPushIsAtomic, name, Singly.StackBase, {"PushRange": _detachedBlock})

    def test_the_queue_bench_falls_when_a_single_push_records_no_last_node(self) -> None:
        """As before 5f36430: ListBase.Push, on an empty collection, recorded the first node alone,
        whether the collection was a stack or a queue."""

        def firstOnly(self: Any, value: Any) -> None:
            first: Any = self._GetFirstCookie()

            if first is None: self._SetFirstCookie(value)
            else: self._Push(value, first)

        self.__assertFalls(TestAQueueKeepsWhatItHeldWhenABlockFollows, "test_a_block_follows_a_single_push", Singly.ListBase, {"Push": firstOnly})

    def test_the_queue_bench_falls_when_a_buffered_queue_records_no_last_node(self) -> None:
        """As before d4c9197: BufferedQueue defined _SetLast, so that its _SetLastCookie was the
        abstract method of _IQueueAdderBase, which does nothing."""

        def unrecorded(self: Any, node: Any) -> None: return None

        self.__assertFalls(TestAQueueKeepsWhatItHeldWhenABlockFollows, "test_a_block_follows_what_the_queue_was_created_with", Buffer.BufferedQueue, {"_SetLastCookie": unrecorded})

    def test_the_priority_bench_falls_when_a_level_index_is_made_a_level(self) -> None:
        """As before 66cde57: PriorityItemList._Convert made the index of a level a PriorityLevel."""

        def converted(self: Any, level: PriorityLevel) -> int: return (level - PriorityLevel.Lowest).value

        self.__assertFalls(TestThePriorityListsPopTheHighestLevelFirst, "test_one_item_at_every_level_pops_from_the_highest_down", PriorityItemList, {"_Convert": converted})

    def test_the_converting_cursor_bench_falls_when_the_stack_writes_through_the_queue(self) -> None:
        """As before c196445: _Buffer sent every write through the queued cursor of its source, the
        stacked buffer's too. c196445 gave each buffer the hook _AsCursor, which the stacked one,
        reached through the object, carries: the substitution has it ask for the queued cursor
        again."""

        def queued(self: Any, source: Any) -> Any: return source.AsQueuedCursor()

        self.__assertFalls(TestAConvertingListStacksOnTop, "test_each_cursor_pushes_at_its_own_end", type(_selection([0]).AsStackedCursor()), {"_AsCursor": queued})
