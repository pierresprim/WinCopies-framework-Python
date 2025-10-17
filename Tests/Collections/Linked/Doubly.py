"""
Tests unitaires pour les listes doublement chaînées (WinCopies.Collections.Linked.Doubly)
"""

import unittest
from typing import Callable, List as PyList

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
from WinCopies.Typing.Delegate import Converter

def __populateList(l: IReadWriteList[int], action: Callable[[IReadWriteList[int], int], INode[int]], value: int = 3) -> None:
    for i in range(1, value):
        action(l, i)

def populateList(l: IReadWriteList[int], value: int = 3) -> None:
    __populateList(l, lambda l, value: l.AddLastNode(value), value)
def populateListR(l: IReadWriteList[int], value: int = 3) -> None:
    __populateList(l, lambda l, value: l.AddFirstNode(value), value)

def assertEmpty[T](test: unittest.TestCase, l: IReadOnlyList[T]) -> None:
    test.assertTrue(l.IsEmpty())
    test.assertFalse(l.HasItems())
def assertNotEmpty[T](test: unittest.TestCase, l: IReadOnlyList[T]) -> None:
    test.assertTrue(l.IsEmpty())
    test.assertFalse(l.HasItems())

def assertNotNone[T](test: unittest.TestCase, value: T|None) -> T:
    if value is None:
        test.assertIsNotNone(value)

        raise SystemError()
    
    return value

def assertNodeValue[T](test: unittest.TestCase, l: IList[T], node: IDoublyLinkedNode[T]|None, value: T) -> None:
    assertNotEmpty(test, l)

    test.assertIsNotNone(node)
    test.assertEqual(assertNotNone(test, node).GetValue(), value)

def assertNullValue[T](test: unittest.TestCase, l: IList[T], value: INullable[T]) -> None:
    assertEmpty(test, l)

    test.assertFalse(value.HasValue())

def assertNullableValue[T](test: unittest.TestCase, l: IList[T], expected: T, actual: INullable[T]) -> None:
    assertNotEmpty(test, l)

    test.assertTrue(actual.HasValue())

    test.assertEqual(actual.GetValue(), expected)
def assertValue[T](test: unittest.TestCase, l: IList[T], expected: T, actual: T|None) -> None:
    assertNotEmpty(test, l)

    test.assertEqual(actual, expected)

def assertValueAndEmpty[T](test: unittest.TestCase, l: IList[T], expected: T, actual: INullable[T]) -> None:
    assertNullableValue(test, l, expected, actual)
    assertEmpty(test, l)

def assertEnumeration[T](test: unittest.TestCase, l: IList[int], enumeratorConverter: Converter[IList[int], IEnumerator[T]|None], valueConverter: Converter[T, int]) -> None:
    l.AddLast(1)
    l.AddLast(2)
    l.AddLast(3)

    enumerator: IEnumerator[T] = assertNotNone(test, enumeratorConverter(l))

    values: PyList[int] = []
    
    for value in enumerator.AsIterator():
        values.append(valueConverter(value))

    test.assertEqual(values, [1, 2, 3])

def assertNext(test: unittest.TestCase, l: IList[int], value: int, action: Callable[[IDoublyLinkedNode[int], int], IDoublyLinkedNode[int]], values: tuple[int, int]) -> None:
    def assertNext(expected: int) -> None:
        nonlocal node

        test.assertEqual((node := assertNotNone(test, node.GetNext())).GetValue(), expected)
    
    test.assertIsNotNone(action(assertNotNone(test, assertNotNone(test, l.GetFirst()).GetNext()), value))

    node: IDoublyLinkedNode[int] = assertNotNone(test, l.GetFirst())

    test.assertEqual(node.GetValue(), 1)
    assertNext(values[0])
    assertNext(values[1])
    assertNext(3)

def assertRemoveNode(test: unittest.TestCase, l: IList[int], value: int, converter: Converter[IList[int], IDoublyLinkedNode[int]|None]) -> None:
    node: IDoublyLinkedNode[int] = assertNotNone(test, converter(l))

    removedValue = node.Remove()

    test.assertEqual(removedValue, value)
    # The new node must be 2
    test.assertEqual(assertNotNone(test, converter(l)).GetValue(), 2)

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

class TestList(unittest.TestCase):
    """Tests for the List[T] class - common doubly linked list."""

    def setUp(self):
        """Initializes an empty list before each test"""
        self.__list: IList[int] = List[int]()

    # Basic tests - Add and retrieve

    def test_empty_list_is_empty(self):
        """A new list should be empty"""
        assertEmpty(self, self.__list)

    def test_add_first_single_item(self):
        """Add new item at the beginning of an empty list"""
        def addNode(value: int) -> None:
            assertNodeValue(self, self.__list, self.__list.AddFirst(value), value)
        
        addNode(42)

    def test_add_last_single_item(self):
        """Add new item at the end of an empty list"""
        def addNode(value: int) -> None:
            assertNodeValue(self, self.__list, self.__list.AddLast(value), value)
        
        addNode(42)

    def test_add_first_multiple_items(self):
        """Add multiple items at the beginning (reversed order)"""
        populateListR(self.__list)

        # Item order should be: 3, 2, 1
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 3)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 1)

    def test_add_last_multiple_items(self):
        """Add multiple items at the end (preserved order)"""
        populateList(self.__list)

        # Item order should be: 1, 2, 3
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 1)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 3)

    def test_add_mixed_first_and_last(self):
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

    def test_try_get_first_empty_list(self):
        """TryGetFirst on empty list should return a null (empty) value"""
        assertNullValue(self, self.__list, self.__list.TryGetFirst())

    def test_try_get_last_empty_list(self):
        """TryGetLast on empty list should return a null (empty) value"""
        assertNullValue(self, self.__list, self.__list.TryGetLast())

    def test_try_get_first_with_items(self):
        """TryGetFirst with items must return the first one"""
        populateList(self.__list, 2)

        assertNullableValue(self, self.__list, 1, self.__list.TryGetFirst())

    def test_try_get_last_with_items(self):
        """TryGetFirst with items must return the last one"""
        populateList(self.__list, 2)

        assertNullableValue(self, self.__list, 2, self.__list.TryGetLast())

    def test_try_get_first_value_or_none(self):
        """TryGetFirstValueOrNone must return None when the list is empty"""
        self.assertIsNone(self.__list.TryGetFirstValueOrNone())

        self.__list.AddLast(42)
        assertValue(self, self.__list, 42, self.__list.TryGetFirstValueOrNone())

    def test_try_get_last_value_or_none(self):
        """TryGetLastValueOrNone must return None when the list is empty"""
        self.assertIsNone(self.__list.TryGetLastValueOrNone())

        self.__list.AddLast(42)
        assertValue(self, self.__list, 42, self.__list.TryGetLastValueOrNone())

    def test_try_get_first_value_with_default(self):
        """TryGetFirstValue with default value"""
        self.assertEqual(self.__list.TryGetFirstValue(-1), -1)

        self.__list.AddLast(42)
        assertValue(self, self.__list, 42, self.__list.TryGetFirstValue(-1))

    def test_try_get_last_value_with_default(self):
        """TryGetLastValue with default value"""
        self.assertEqual(self.__list.TryGetLastValue(-1), -1)

        self.__list.AddLast(42)
        assertValue(self, self.__list, 42, self.__list.TryGetLastValue(-1))

    # Remove tests

    def test_remove_first_empty_list(self):
        """RemoveFirst on an empty list must return a null (empty) value"""
        self.assertFalse(self.__list.RemoveFirst().HasValue())

    def test_remove_last_empty_list(self):
        """RemoveLast on an empty list must return a null (empty) value"""
        self.assertFalse(self.__list.RemoveLast().HasValue())

    def test_remove_first_single_item(self):
        """Remove first item on a list with only one item"""
        self.__list.AddLast(42)

        assertValueAndEmpty(self, self.__list, 42, self.__list.RemoveFirst())

    def test_remove_last_single_item(self):
        """Remove last item on a list with only one item"""
        self.__list.AddLast(42)

        assertValueAndEmpty(self, self.__list, 42, self.__list.RemoveLast())

    def test_remove_first_multiple_items(self):
        """Remove first item when multiple items"""
        populateList(self.__list)

        assertNullableValue(self, self.__list, 1, self.__list.RemoveFirst())

        # Check that the new first is 2
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 2)

    def test_remove_last_multiple_items(self):
        """Remove last item when multiple items"""
        populateList(self.__list)

        assertNullableValue(self, self.__list, 3, self.__list.RemoveLast())

        # Check that the new last is 2
        assertNodeValue(self, self.__list, self.__list.GetLast(), 2)

    def test_remove_all_items_from_start(self):
        """Remove all items from the beginning"""
        assertRemoveAll(self, self.__list, lambda l: l.RemoveFirst())

    def test_remove_all_items_from_end(self):
        """Remove all items from the end"""
        assertRemoveAll(self, self.__list, lambda l: l.RemoveLast())

    # Clear tests

    def test_clear_empty_list(self):
        """Clear on an empty list should not raise any error"""
        self.__list.Clear()

        assertEmpty(self, self.__list)

    def test_clear_list_with_items(self):
        """Clear must remove all items from the list"""
        populateList(self.__list)

        self.__list.Clear()

        assertEmpty(self, self.__list)

        self.assertIsNone(self.__list.GetFirst())
        self.assertIsNone(self.__list.GetLast())

    # Tests AddFirstItems / AddLastItems

    def test_add_first_items_from_list(self):
        """Add multiple items at the beginning from an iterable"""
        self.assertTrue(self.__list.AddFirstItems((1, 2, 3)))

        # Reversed order because we add at the beginning: 3, 2, 1
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 3)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 1)

    def test_add_last_items_from_list(self):
        """Add multiple items at the end from an iterable"""
        self.assertTrue(self.__list.AddLastItems((1, 2, 3)))
        
        # Preserved order: 1, 2, 3
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 1)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 3)

    def test_add_first_items_none(self):
        """AddFirstItems with None must return False"""
        self.assertFalse(self.__list.AddFirstItems(None))

    def test_add_last_items_none(self):
        """AddLastItems with None must return False"""
        self.assertFalse(self.__list.AddLastItems(None))

    def test_add_first_values_varargs(self):
        """Add values via *args at the beginning"""
        self.assertTrue(self.__list.AddFirstValues(1, 2, 3))
        
        # Reversed order: 3, 2, 1
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 3)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 1)

    def test_add_last_values_varargs(self):
        """Ajout de valeurs via *args à la fin"""
        self.assertTrue(self.__list.AddLastValues(1, 2, 3))

        # Preserved order: 1, 2, 3
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 1)
        assertNodeValue(self, self.__list, self.__list.GetLast(), 3)

    # Tests des énumérateurs

    def test_enumerate_empty_list(self):
        """Enumerate from an empty list"""
        self.assertIsNone(self.__list.TryGetEnumerator())

    def test_enumerate_list_with_items(self):
        """Enumerate from a list with items"""
        assertEnumeration(self, self.__list, lambda l: l.TryGetEnumerator(), Self)

    def test_enumerate_nodes(self):
        """Enumerate nodes"""
        populateList(self.__list)

        assertEnumeration(self, self.__list, lambda l: l.TryGetNodeEnumerator(), lambda node: node.GetValue())

    def test_as_queued_enumerator(self):
        """FIFO enumerator - remove items"""
        populateList(self.__list)

        enumerator: IEnumerator[int] = self.__list.AsQueuedEnumerator()
        values: PyList[int] = []

        for value in enumerator.AsIterator():
            values.append(value)

        # Values should be: 1, 2, 3
        self.assertEqual(values, [1, 2, 3])

        # The list should be empty after enumeration
        assertEmpty(self, self.__list)

    def test_as_stacked_enumerator(self):
        """LIFO enumerator - remove items"""
        populateList(self.__list)

        enumerator: IEnumerator[int] = self.__list.AsStackedEnumerator()
        values: PyList[int] = []

        for value in enumerator.AsIterator():
            values.append(value)

        # Values should be: 3, 2, 1 (reversed order)
        self.assertEqual(values, [3, 2, 1])
        # The list should be empty after enumeration
        assertEmpty(self, self.__list)

    # Tests AsReadOnly

    def test_as_read_only(self):
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

    def setUp(self):
        """Initialize a list with some items"""
        self.__list: IList[int] = List[int]()
        
        populateList(self.__list)

    def test_node_get_value(self):
        """Retrieve value from a node"""
        assertNodeValue(self, self.__list, self.__list.GetFirst(), 1)

    def test_node_get_next(self):
        """Navigate to the next node"""
        first: IDoublyLinkedNode[int] = assertNotNone(self, self.__list.GetFirst())

        assertNodeValue(self, self.__list, first.GetNext(), 2)

    def test_node_get_previous(self):
        """Navigate to the previous node"""
        last: IDoublyLinkedNode[int] = assertNotNone(self, self.__list.GetLast())

        assertNodeValue(self, self.__list, last.GetPrevious(), 2)

    def test_node_get_list(self):
        """Retrieve the list from a node"""
        node: IDoublyLinkedNode[int] = assertNotNone(self, self.__list.GetFirst())

        l: IList[int] = assertNotNone(self, node.GetList())
        
        self.assertIs(l, self.__list)

    def test_node_set_previous(self):
        """Insert a value before an existing node"""
        assertNext(self, self.__list, 15, lambda node, value: node.SetPrevious(value), (15, 2))

    def test_node_set_next(self):
        """Insert a value after an existing node"""
        assertNext(self, self.__list, 25, lambda node, value: node.SetNext(value), (2, 25))

    def test_node_set_previous_at_first(self):
        """Inserting before the first node must create a new first"""
        assertNotNone(self, assertNotNone(self, self.__list.GetFirst()).SetPrevious(0))

        node: IDoublyLinkedNode[int] = assertNotNone(self, self.__list.GetFirst())

        # Check that 0 has become the first value
        self.assertEqual(node.GetValue(), 0)
        self.assertEqual(assertNotNone(self, node.GetNext()).GetValue(), 1)

    def test_node_set_next_at_last(self):
        """Inserting after the last node must create a new last"""
        assertNotNone(self, assertNotNone(self, self.__list.GetLast()).SetNext(4))

        node: IDoublyLinkedNode[int] = assertNotNone(self, self.__list.GetLast())

        # Check that 0 has become the last value
        self.assertEqual(node.GetValue(), 4)
        self.assertEqual(assertNotNone(self, node.GetPrevious()).GetValue(), 3)

    def test_node_remove_first(self):
        """Remove the first node via Remove()"""
        assertRemoveNode(self, self.__list, 1, lambda l: l.GetFirst())

    def test_node_remove_last(self):
        """Remove the last node via Remove()"""
        assertRemoveNode(self, self.__list, 3, lambda l: l.GetLast())

    def test_node_remove_middle(self):
        """Remove a node at middle"""
        middle: IDoublyLinkedNode[int] = assertNotNone(self, assertNotNone(self, self.__list.GetFirst()).GetNext())

        self.assertEqual(middle.Remove(), 2)

        # Structure should be: 1 -> 3
        first: IDoublyLinkedNode[int] = assertNotNone(self, self.__list.GetFirst())

        self.assertEqual(first.GetValue(), 1)
        self.assertEqual(assertNotNone(self, first.GetNext()).GetValue(), 3)

    def test_node_remove_only_item(self):
        """Remove the only node"""
        l: IList[int] = List[int]()

        node: IDoublyLinkedNode[int] = l.AddLast(42)

        self.assertEqual(node.Remove(), 42)
        assertEmpty(self, self.__list)

class TestCountableList(unittest.TestCase):
    """Tests for the CountableList[T] class - list with counter"""

    def setUp(self):
        """Initialize an empty list before each test"""
        self.__list: ICountableList[int] = CountableList[int]()

    def test_empty_list_count_is_zero(self):
        """An empty list must have a counter set to 0"""
        assertCount(self, self.__list, 0)
        assertEmpty(self, self.__list)

    def test_count_after_add_first(self):
        """The counter must increment after a call to AddFirst"""
        def add(value: int) -> None:
            self.__list.AddFirst(value)

            assertCount(self, self.__list, value)
        
        add(1)
        add(2)
        add(3)

    def test_count_after_add_last(self):
        """The counter must increment after a call to AddLast"""
        def add(value: int) -> None:
            self.__list.AddLast(value)

            assertCount(self, self.__list, value)
        
        add(1)
        add(2)
        add(3)

    def test_count_after_remove_first(self):
        """The counter must decrement after a call to RemoveFirst"""
        assertRemove(self, self.__list, lambda l: l.RemoveFirst())

    def test_count_after_remove_last(self):
        """The counter must decrement after a call to RemoveLast"""
        assertRemove(self, self.__list, lambda l: l.RemoveLast())

    def test_count_after_clear(self):
        """The counter must be 0 after a call to Clear"""
        populateList(self.__list)

        assertCount(self, self.__list, 3)

        self.__list.Clear()

        assertCount(self, self.__list, 0)
        assertEmpty(self, self.__list)

    def test_count_with_node_operations(self):
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

    def test_enumerate_countable_list(self):
        """Enumerate a CountableList"""
        populateList(self.__list)

        enumerator: IEnumerator[int] = assertNotNone(self, self.__list.TryGetEnumerator())

        values: tuple[int, ...] = tuple(enumerator.AsIterator())
        self.assertEqual(values, (1, 2, 3))

    def test_countable_node_get_list(self):
        """The node must be able to retrieve the countable list"""
        l: ICountableList[int] = assertNotNone(self, self.__list.AddLast(42).GetList())

        self.assertIs(l, self.__list)

    def test_as_sized(self):
        """The list must be compatible with the Sized class"""
        populateList(self.__list, 2)

        self.assertEqual(len(self.__list.AsSized()), 2)

class TestListWithStrings(unittest.TestCase):
    """Tests with other data types than int"""

    def test_string_list(self):
        """Test with strings"""
        l: IList[str] = List[str]()

        l.AddLast("hello")
        l.AddLast("world")

        assertNodeValue(self, l, l.GetFirst(), "hello")
        assertNodeValue(self, l, l.GetLast(), "world")

    def test_float_list(self):
        """Test with floating point numbers"""
        l: IList[float] = List[float]()

        l.AddLast(3.14)
        l.AddLast(2.71)
        
        self.assertEqual(tuple(assertNotNone(self, l.TryGetEnumerator()).AsIterator()), (3.14, 2.71))

class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases"""

    def test_add_and_remove_alternating(self):
        """Alternate addition and deletion"""
        l: IList[int] = List[int]()

        l.AddLast(1)
        l.RemoveFirst()
        assertEmpty(self, l)

        l.AddFirst(2)
        l.RemoveLast()
        assertEmpty(self, l)

    def test_large_list(self):
        """Test with a large list"""
        l: IList[int] = List[int]()

        # Add 1000 items
        for i in range(1000):
            l.AddLast(i)

        # Check the first and last
        assertNodeValue(self, l, l.GetFirst(), 0)
        assertNodeValue(self, l, l.GetLast(), 999)

        # Enumerate all items
        enumerator: IEnumerator[int] = assertNotNone(self, l.TryGetEnumerator())

        values: PyList[int] = list(enumerator.AsIterator())
        
        self.assertEqual(len(values), 1000)
        self.assertEqual(values[0], 0)
        self.assertEqual(values[999], 999)

    def test_multiple_clears(self):
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

    def test_node_chain_navigation(self):
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