"""
Unit tests for doubly linked lists (WinCopies.Collections.Linked.Doubly)
"""

import unittest
from typing import Callable, List as PyList

from WinCopies.Collections import Generator
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Linked.Doubly import (
    IReadOnlyList,
    IReadWriteList,
    IList,
    ICountableList,
    INode,
    IDoublyLinkedNode,
    ICountableLinkedListNode,
    List,
    CountableList
)
from WinCopies.Delegates import Self
from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import Method, Converter

def __populateList(l: IReadWriteList[int], action: Callable[[IReadWriteList[int], int], INode[int]], value: int = 3) -> None:
    for i in range(0, value):
        action(l, i + 1)

def populateList(l: IReadWriteList[int], value: int = 3) -> None:
    __populateList(l, lambda l, value: l.AddLastNode(value), value)
def populateListR(l: IReadWriteList[int], value: int = 3) -> None:
    __populateList(l, lambda l, value: l.AddFirstNode(value), value)

def assertEmpty[T](test: unittest.TestCase, l: IReadOnlyList[T]) -> None:
    test.assertTrue(l.IsEmpty())
    test.assertFalse(l.HasItems())
def assertNotEmpty[T](test: unittest.TestCase, l: IReadOnlyList[T]) -> None:
    test.assertFalse(l.IsEmpty())
    test.assertTrue(l.HasItems())

def assertNotNone[T](test: unittest.TestCase, value: T|None, action: Method[T]) -> None:
    if value is None:
        test.assertIsNotNone(value)

        raise SystemError()
    
    action(value)

def assertNodeValue[T](test: unittest.TestCase, l: IList[T], node: IDoublyLinkedNode[T]|None, value: T) -> None:
    assertNotEmpty(test, l)

    assertNotNone(test, node, lambda node: test.assertEqual(node.GetValue(), value))

def assertNullValue[T](test: unittest.TestCase, l: IList[T], value: INullable[T]) -> None:
    assertEmpty(test, l)

    test.assertFalse(value.HasValue())

def _assertNullableValue[T](test: unittest.TestCase, l: IList[T], expected: T, actual: INullable[T]) -> None:
    test.assertTrue(actual.HasValue())

    test.assertEqual(actual.GetValue(), expected)
def assertNullableValue[T](test: unittest.TestCase, l: IList[T], expected: T, actual: INullable[T]) -> None:
    assertNotEmpty(test, l)

    _assertNullableValue(test, l, expected, actual)

def assertValue[T](test: unittest.TestCase, l: IList[T], expected: T, actual: T|None) -> None:
    assertNotEmpty(test, l)

    test.assertEqual(actual, expected)

def assertValueAndEmpty[T](test: unittest.TestCase, l: IList[T], expected: T, actual: INullable[T]) -> None:
    _assertNullableValue(test, l, expected, actual)
    assertEmpty(test, l)

def assertEnumeration[T](test: unittest.TestCase, l: IList[int], enumeratorConverter: Converter[IList[int], IEnumerator[T]|None], valueConverter: Converter[T, int]) -> None:
    def enumerate(enumerator: IEnumerator[T]) -> None:
        values: PyList[int] = []
        
        for value in enumerator.AsIterator():
            values.append(valueConverter(value))

        test.assertEqual(values, [1, 2, 3])

    populateList(l)
    assertNotNone(test, enumeratorConverter(l), enumerate)

def assertNext(test: unittest.TestCase, l: IList[int], value: int, action: Callable[[IDoublyLinkedNode[int], int], IDoublyLinkedNode[int]], values: tuple[int, int]) -> None:
    def _assertNotNone[T](value: T|None, action: Method[T]) -> None:
        assertNotNone(test, value, action)
    
    def assertNext(node: IDoublyLinkedNode[int]) -> None:
        def assertNext(expected: int) -> None:
            def assertNext(_node: IDoublyLinkedNode[int]) -> None:
                nonlocal node

                test.assertEqual((node := _node).GetValue(), expected)

            _assertNotNone(node.GetNext(), assertNext)
        
        _assertNotNone(l.GetFirst(), lambda _node: _assertNotNone(_node.GetNext(), lambda __node: test.assertIsNotNone(action(__node, value))))

        test.assertEqual(node.GetValue(), 1)
        assertNext(values[0])
        assertNext(values[1])
        assertNext(3)

    _assertNotNone(l.GetFirst(), assertNext)

def assertRemoveNode(test: unittest.TestCase, l: IList[int], value: int, converter: Converter[IList[int], IDoublyLinkedNode[int]|None]) -> None:
    def remove(node: IDoublyLinkedNode[int]) -> None:
        removedValue = node.Remove()

        test.assertEqual(removedValue, value)
        # The new node must be 2
        assertNotNone(test, converter(l), lambda _node: test.assertEqual(_node.GetValue(), 2))

    assertNotNone(test, converter(l), remove)

def assertCount[T](test: unittest.TestCase, l: ICountableList[T], value: int) -> None:
    test.assertEqual(l.GetCount(), value)

def assertRemove(test: unittest.TestCase, l: ICountableList[int], method: Converter[IReadWriteList[int], INullable[int]]) -> None:
    def remove(value: int) -> None:
        method(l)

        assertCount(test, l, value)
    
    l.AddLast(1)
    l.AddLast(2)
    l.AddLast(3)

    assertCount(test, l, 3)

    remove(2)
    remove(1)
    remove(0)

def assertRemoveAll(test: unittest.TestCase, l: IList[int], method: Converter[IReadWriteList[int], INullable[int]]) -> None:
    populateList(l)

    for _ in range(3):
        method(l)
    
    assertEmpty(test, l)

def assertAddMultipleTimes(test: unittest.TestCase, l: IList[int], first: int, last: int) -> None:
    def _assertNotNone[T](value: T|None, action: Converter[T, T|None]) -> None:
        assertNotNone(test, value, lambda _value: test.assertIsNone(action(_value)))
    def _assertNodeValue(node: IDoublyLinkedNode[int]|None, value: int) -> None:
        assertNodeValue(test, l, node, value)
    
    def getFirst() -> IDoublyLinkedNode[int]|None:
        return l.GetFirst()
    def getLast() -> IDoublyLinkedNode[int]|None:
        return l.GetLast()

    populateListR(l)

    _assertNodeValue(getFirst(), first)
    _assertNodeValue(getLast(), last)

    _assertNotNone(getFirst(), lambda node: node.GetPrevious())
    _assertNotNone(getLast(), lambda node: node.GetNext())

class TestList(unittest.TestCase):
    """Tests for the List[T] class - common doubly linked list."""

    def setUp(self) -> None:
        """Initializes an empty list before each test"""
        self.__list: IList[int] = List[int]()

    # Basic tests - Add and retrieve

    def test_empty_list_is_empty(self) -> None:
        """A new list should be empty"""
        assertEmpty(self, self.__list)

    def test_add_first_single_item(self) -> None:
        """Add new item at the beginning of an empty list"""
        def addNode(value: int) -> None:
            assertNodeValue(self, self.__list, self.__list.AddFirst(value), value)
        
        addNode(42)

    def test_add_last_single_item(self) -> None:
        """Add new item at the end of an empty list"""
        def addNode(value: int) -> None:
            assertNodeValue(self, self.__list, self.__list.AddLast(value), value)
        
        addNode(42)

    def test_add_first_multiple_items(self) -> None:
        """Add multiple items at the beginning (reversed order)"""
        assertAddMultipleTimes(self, self.__list, 3, 1)

    def test_add_last_multiple_items(self) -> None:
        """Add multiple items at the end (preserved order)"""
        assertAddMultipleTimes(self, self.__list, 1, 3)

    def test_add_mixed_first_and_last(self) -> None:
        """Add to both beginning and end"""
        def addFirst(value: int) -> None:
            self.__list.AddFirst(value)
        def addLast(value: int) -> None:
            self.__list.AddLast(value)
        
        addLast(2)      # [2]
        addFirst(1)     # [1, 2]
        addLast(3)      # [1, 2, 3]
        addFirst(0)     # [0, 1, 2, 3]

        assertNodeValue(self, self.__list, self.__list.GetFirst(), 0)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 3)

    # TryGetFirst and TryGetLast tests

    def test_try_get_first_empty_list(self) -> None:
        """TryGetFirst on empty list should return a null (empty) value"""
        assertNullValue(self, self.__list, self.__list.TryGetFirst())

    def test_try_get_last_empty_list(self) -> None:
        """TryGetLast on empty list should return a null (empty) value"""
        assertNullValue(self, self.__list, self.__list.TryGetLast())

    def test_try_get_first_with_items(self) -> None:
        """TryGetFirst with items must return the first one"""
        populateList(self.__list, 2)

        assertNullableValue(self, self.__list, 1, self.__list.TryGetFirst())

    def test_try_get_last_with_items(self) -> None:
        """TryGetFirst with items must return the last one"""
        populateList(self.__list, 2)

        assertNullableValue(self, self.__list, 2, self.__list.TryGetLast())

    def test_try_get_first_value_or_none(self) -> None:
        """TryGetFirstValueOrNone must return None when the list is empty"""
        self.assertIsNone(self.__list.TryGetFirstValueOrNone())

        self.__list.AddLast(42)
        assertValue(self, self.__list, 42, self.__list.TryGetFirstValueOrNone())

    def test_try_get_last_value_or_none(self) -> None:
        """TryGetLastValueOrNone must return None when the list is empty"""
        self.assertIsNone(self.__list.TryGetLastValueOrNone())

        self.__list.AddLast(42)
        assertValue(self, self.__list, 42, self.__list.TryGetLastValueOrNone())

    def test_try_get_first_value_with_default(self) -> None:
        """TryGetFirstValue with default value"""
        self.assertEqual(self.__list.TryGetFirstValue(-1), -1)

        self.__list.AddLast(42)
        assertValue(self, self.__list, 42, self.__list.TryGetFirstValue(-1))

    def test_try_get_last_value_with_default(self) -> None:
        """TryGetLastValue with default value"""
        self.assertEqual(self.__list.TryGetLastValue(-1), -1)

        self.__list.AddLast(42)
        assertValue(self, self.__list, 42, self.__list.TryGetLastValue(-1))

    # Remove tests

    def test_remove_first_empty_list(self) -> None:
        """RemoveFirst on an empty list must return a null (empty) value"""
        self.assertFalse(self.__list.TryRemoveFirst().HasValue())

    def test_remove_last_empty_list(self) -> None:
        """RemoveLast on an empty list must return a null (empty) value"""
        self.assertFalse(self.__list.TryRemoveLast().HasValue())

    def test_remove_first_single_item(self) -> None:
        """Remove first item on a list with only one item"""
        self.__list.AddLast(42)

        assertValueAndEmpty(self, self.__list, 42, self.__list.TryRemoveFirst())

    def test_remove_last_single_item(self) -> None:
        """Remove last item on a list with only one item"""
        self.__list.AddLast(42)

        assertValueAndEmpty(self, self.__list, 42, self.__list.TryRemoveLast())

    def test_remove_first_multiple_items(self) -> None:
        """Remove first item when multiple items"""
        populateList(self.__list)

        assertNullableValue(self, self.__list, 1, self.__list.TryRemoveFirst())

        # Check that the new first is 2
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 2)

    def test_remove_last_multiple_items(self) -> None:
        """Remove last item when multiple items"""
        populateList(self.__list)

        assertNullableValue(self, self.__list, 3, self.__list.TryRemoveLast())

        # Check that the new last is 2
        assertNodeValue(self, self.__list, self.__list.GetLast(), 2)

    def test_remove_all_items_from_start(self) -> None:
        """Remove all items from the beginning"""
        assertRemoveAll(self, self.__list, lambda l: l.TryRemoveFirst())

    def test_remove_all_items_from_end(self) -> None:
        """Remove all items from the end"""
        assertRemoveAll(self, self.__list, lambda l: l.TryRemoveLast())

    # Clear tests

    def test_clear_empty_list(self) -> None:
        """Clear on an empty list should not raise any error"""
        self.__list.Clear()

        assertEmpty(self, self.__list)

    def test_clear_list_with_items(self) -> None:
        """Clear must remove all items from the list"""
        populateList(self.__list)

        self.__list.Clear()

        assertEmpty(self, self.__list)

        self.assertIsNone(self.__list.GetFirst())
        self.assertIsNone(self.__list.GetLast())

    # Tests AddFirstItems / AddLastItems

    def test_add_first_items_from_list(self) -> None:
        """Add multiple items at the beginning from an iterable"""
        populateList(self.__list)

        self.assertTrue(self.__list.AddFirstItems((4, 5, 6)))

        assertNodeValue(self, self.__list, self.__list.GetFirst(), 4)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 3)

    def test_add_last_items_from_list(self) -> None:
        """Add multiple items at the end from an iterable"""
        populateList(self.__list)

        self.assertTrue(self.__list.AddLastItems((4, 5, 6)))
        
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 1)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 6)

    def test_add_first_items_none(self) -> None:
        """AddFirstItems with None must return False"""
        self.assertFalse(self.__list.AddFirstItems(None))

    def test_add_last_items_none(self) -> None:
        """AddLastItems with None must return False"""
        self.assertFalse(self.__list.AddLastItems(None))

    def test_add_first_values_varargs(self) -> None:
        """Add values via *args at the beginning"""
        populateList(self.__list)

        self.assertTrue(self.__list.AddFirstValues(4, 5, 6))
        
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 4)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 3)

    def test_add_last_values_varargs(self) -> None:
        """Add values via *args at the end"""
        populateList(self.__list)

        self.assertTrue(self.__list.AddLastValues(4, 5, 6))

        assertNodeValue(self, self.__list, self.__list.GetFirst(), 1)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 6)

    # Tests des énumérateurs

    def test_enumerate_empty_list(self) -> None:
        """Enumerate from an empty list"""
        self.assertIsNone(self.__list.TryGetEnumerator())

    def test_enumerate_list_with_items(self) -> None:
        """Enumerate from a list with items"""
        assertEnumeration(self, self.__list, lambda l: l.TryGetEnumerator(), Self)

    def test_enumerate_nodes(self) -> None:
        """Enumerate nodes"""
        assertEnumeration(self, self.__list, lambda l: l.TryGetNodeEnumerator(), lambda node: node.GetValue())

    def test_as_queued_enumerator(self) -> None:
        """FIFO enumerator - remove items"""
        populateList(self.__list)

        iterator: Generator[int] = self.__list.AsQueuedGenerator()
        values: PyList[int] = []

        for value in iterator:
            values.append(value)

        # Values should be: 1, 2, 3
        self.assertEqual(values, [1, 2, 3])

        # The list should be empty after enumeration
        assertEmpty(self, self.__list)

    def test_as_stacked_enumerator(self) -> None:
        """LIFO enumerator - remove items"""
        populateList(self.__list)

        iterator: Generator[int] = self.__list.AsStackedGenerator()
        values: PyList[int] = []

        for value in iterator:
            values.append(value)

        # Values should be: 3, 2, 1 (reversed order)
        self.assertEqual(values, [3, 2, 1])
        # The list should be empty after enumeration
        assertEmpty(self, self.__list)

    # Tests AsReadOnly

    def test_as_read_only(self) -> None:
        """Create a read-only view of the list"""
        populateList(self.__list, 2)

        readOnly: IReadOnlyList[int] = self.__list.AsReadOnly()

        self.assertIsNotNone(readOnly)
        
        assertNotEmpty(self, readOnly)

        # Vérifier que les valeurs sont accessibles
        self.assertEqual(readOnly.TryGetFirstValueOrNone(), 1)
        self.assertEqual(readOnly.TryGetLastValueOrNone(), 2)

class TestListNode(unittest.TestCase):
    """Tests for node operations on List[T]"""

    def setUp(self) -> None:
        """Initialize a list with some items"""
        self.__list: IList[int] = List[int]()
        
        populateList(self.__list)

    def test_node_get_value(self) -> None:
        """Retrieve value from a node"""
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 1)

    def test_node_get_next(self) -> None:
        """Navigate to the next node"""
        assertNotNone(self, self.__list.GetFirst(), lambda first: assertNodeValue(self, self.__list, first.GetNext(), 2))

    def test_node_get_previous(self) -> None:
        """Navigate to the previous node"""
        assertNotNone(self, self.__list.GetLast(), lambda last: assertNodeValue(self, self.__list, last.GetPrevious(), 2))

    def test_node_get_list(self) -> None:
        """Retrieve the list from a node"""
        def assertGetList(node: IDoublyLinkedNode[int]) -> None:
            assertNotNone(self, node.GetList(), lambda l: self.assertIs(l, self.__list))
        
        assertNotNone(self, self.__list.GetFirst(), assertGetList)

    def test_node_set_previous(self) -> None:
        """Insert a value before an existing node"""
        assertNext(self, self.__list, 15, lambda node, value: node.SetPrevious(value), (15, 2))

    def test_node_set_next(self) -> None:
        """Insert a value after an existing node"""
        assertNext(self, self.__list, 25, lambda node, value: node.SetNext(value), (2, 25))

    def test_node_set_previous_at_first(self) -> None:
        """Inserting before the first node must create a new first"""
        def assertEqual(node: IDoublyLinkedNode[int]) -> None:
            # Check that 0 has become the first value
            self.assertEqual(node.GetValue(), 0)
            assertNotNone(self, node.GetNext(), lambda node: self.assertEqual(node.GetValue(), 1))
        
        assertNotNone(self, self.__list.GetFirst(), lambda first: self.assertIsNotNone(self, first.SetPrevious(0)))
        assertNotNone(self, self.__list.GetFirst(), assertEqual)

    def test_node_set_next_at_last(self) -> None:
        """Inserting after the last node must create a new last"""
        def assertEqual(node: IDoublyLinkedNode[int]) -> None:
            # Check that 0 has become the last value
            self.assertEqual(node.GetValue(), 4)
            assertNotNone(self, node.GetPrevious(), lambda node: self.assertEqual(node.GetValue(), 3))
        
        assertNotNone(self, self.__list.GetLast(), lambda last: self.assertIsNotNone(self, last.SetNext(4)))
        assertNotNone(self, self.__list.GetLast(), assertEqual)

    def test_node_remove_first(self) -> None:
        """Remove the first node via Remove()"""
        assertRemoveNode(self, self.__list, 1, lambda l: l.GetFirst())

    def test_node_remove_last(self) -> None:
        """Remove the last node via Remove()"""
        assertRemoveNode(self, self.__list, 3, lambda l: l.GetLast())

    def test_node_remove_middle(self) -> None:
        """Remove a node at middle"""
        def assertEqual(first: IDoublyLinkedNode[int]) -> None:
            self.assertEqual(first.GetValue(), 1)
            assertNotNone(self, first.GetNext(), lambda node: self.assertEqual(node.GetValue(), 3))

        assertNotNone(self, self.__list.GetFirst(), lambda first: assertNotNone(self, first.GetNext(), lambda middle: self.assertEqual(middle.Remove(), 2)))

        # Structure should be: 1 -> 3
        assertNotNone(self, self.__list.GetFirst(), assertEqual)

    def test_node_remove_only_item(self) -> None:
        """Remove the only node"""
        l: IList[int] = List[int]()

        node: IDoublyLinkedNode[int] = l.AddLast(42)

        self.assertEqual(node.Remove(), 42)
        assertEmpty(self, l)

class TestCountableList(unittest.TestCase):
    """Tests for the CountableList[T] class - list with counter"""

    def setUp(self) -> None:
        """Initialize an empty list before each test"""
        self.__list: ICountableList[int] = CountableList[int]()

    def test_empty_list_count_is_zero(self) -> None:
        """An empty list must have a counter set to 0"""
        assertCount(self, self.__list, 0)
        assertEmpty(self, self.__list)

    def test_count_after_add_first(self) -> None:
        """The counter must increment after a call to AddFirst"""
        def add(value: int) -> None:
            self.__list.AddFirst(value)

            assertCount(self, self.__list, value)
        
        add(1)
        add(2)
        add(3)

    def test_count_after_add_last(self) -> None:
        """The counter must increment after a call to AddLast"""
        def add(value: int) -> None:
            self.__list.AddLast(value)

            assertCount(self, self.__list, value)
        
        add(1)
        add(2)
        add(3)

    def test_count_after_remove_first(self) -> None:
        """The counter must decrement after a call to RemoveFirst"""
        assertRemove(self, self.__list, lambda l: l.TryRemoveFirst())

    def test_count_after_remove_last(self) -> None:
        """The counter must decrement after a call to RemoveLast"""
        assertRemove(self, self.__list, lambda l: l.TryRemoveLast())

    def test_count_after_clear(self) -> None:
        """The counter must be 0 after a call to Clear"""
        populateList(self.__list)

        assertCount(self, self.__list, 3)

        self.__list.Clear()

        assertCount(self, self.__list, 0)
        assertEmpty(self, self.__list)

    def test_count_with_node_operations(self) -> None:
        """The counter must correspond to the operations on the nodes"""
        nodeOne: ICountableLinkedListNode[int] = self.__list.AddLast(1)
        assertCount(self, self.__list, 1)

        # Add via SetNext on the node
        nodeOne.SetNext(2)
        assertCount(self, self.__list, 2)

        # Add via SetPrevious on the node
        nodeOne.SetPrevious(0)
        assertCount(self, self.__list, 3)

        # Remove a node
        nodeOne.Remove()
        assertCount(self, self.__list, 2)

    def test_enumerate_countable_list(self) -> None:
        """Enumerate a CountableList"""
        populateList(self.__list)

        assertNotNone(self, self.__list.TryGetEnumerator(), lambda enumerator: self.assertEqual(tuple(enumerator.AsIterator()), (1, 2, 3)))

    def test_countable_node_get_list(self) -> None:
        """The node must be able to retrieve the countable list"""
        assertNotNone(self, self.__list.AddLast(42).GetList(), lambda l: self.assertIs(l, self.__list))

    def test_as_sized(self) -> None:
        """The list must be compatible with the Sized class"""
        populateList(self.__list, 2)

        self.assertEqual(len(self.__list.AsSized()), 2)

class TestListWithStrings(unittest.TestCase):
    """Tests with other data types than int"""

    def test_string_list(self) -> None:
        """Test with strings"""
        l: IList[str] = List[str]()

        l.AddLast("hello")
        l.AddLast("world")

        assertNodeValue(self, l, l.GetFirst(), "hello")
        assertNodeValue(self, l, l.GetLast(), "world")

    def test_float_list(self) -> None:
        """Test with floating point numbers"""
        l: IList[float] = List[float]()

        l.AddLast(3.14)
        l.AddLast(2.71)
        
        assertNotNone(self, l.TryGetEnumerator(), lambda enumerator: self.assertEqual(tuple(enumerator.AsIterator()), (3.14, 2.71)))

class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases"""

    def test_add_and_remove_alternating(self) -> None:
        """Alternate addition and deletion"""
        l: IList[int] = List[int]()

        l.AddLast(1)
        l.TryRemoveFirst()
        assertEmpty(self, l)

        l.AddFirst(2)
        l.TryRemoveLast()
        assertEmpty(self, l)

    def test_large_list(self) -> None:
        """Test with a large list"""
        def assertEqual(enumerator: IEnumerator[int]) -> None:
            values: PyList[int] = list(enumerator.AsIterator())
            
            self.assertEqual(len(values), 1000)
            self.assertEqual(values[0], 0)
            self.assertEqual(values[999], 999)

        l: IList[int] = List[int]()

        # Add 1000 items
        for i in range(1000):
            l.AddLast(i)

        # Check the first and last
        assertNodeValue(self, l, l.GetFirst(), 0)
        assertNodeValue(self, l, l.GetLast(), 999)

        # Enumerate all items
        assertNotNone(self, l.TryGetEnumerator(), assertEqual)

    def test_multiple_clears(self) -> None:
        """Multiple successive Clear()"""
        def addAndClear(l: IList[int], value: int) -> None:
            l.AddLast(value)
            l.Clear()
            assertEmpty(self, l)

            l.Clear()  # Clear on already empty list
            assertEmpty(self, l)

        l: IList[int] = List[int]()

        addAndClear(l, 1)
        addAndClear(l, 2)

    def test_node_chain_navigation(self) -> None:
        """Full navigation through nodes"""
        def navigate(converter: Converter[IList[int], IDoublyLinkedNode[int]|None], selector: Converter[IDoublyLinkedNode[int], IDoublyLinkedNode[int]|None], values: list[int]) -> None:
            current: IDoublyLinkedNode[int]|None = converter(l)
            _values: PyList[int] = []

            while current is not None:
                _values.append(current.GetValue())
                current = selector(current)

            self.assertEqual(_values, values)

        l: IList[int] = List[int]()
        
        populateList(l, 5)

        # Forward navigation
        navigate(lambda l: l.GetFirst(), lambda node: node.GetNext(), [1, 2, 3, 4, 5])

        # Backward navigation
        navigate(lambda l: l.GetLast(), lambda node: node.GetPrevious(), [5, 4, 3, 2, 1])

if __name__ == '__main__':
    unittest.main()