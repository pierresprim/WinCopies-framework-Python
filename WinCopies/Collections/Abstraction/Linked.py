from abc import abstractmethod
from collections.abc import Iterable
from typing import final

from WinCopies import Abstract
from WinCopies.Collections import Countable
from WinCopies.Collections.Abstraction.Enumeration import Enumerable, Enumerator
from WinCopies.Collections.Enumeration import IEnumerator, Enumerable as EnumerableBase, CountableEnumerable
from WinCopies.Collections.Linked.Singly import IReadOnlyList, IReadOnlyCountableList, IReadOnlyEnumerableList, IReadOnlyCountableEnumerableList, IList as ISinglyLinkedList, ICountableList as ICountableSinglyLinkedList, ICountableEnumerableList, IEnumerableList, ReadOnlyList
from WinCopies.Collections.Linked.Doubly import IReadWriteList, IList as IDoublyLinkedList, ICountableList as ICountableDoublyLinkedList, List, CountableList

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable
from WinCopies.Typing.Delegate import IFunction, Method, ValueFunctionUpdater

class _IReadOnlyListUpdater[TIn, TOut](ValueFunctionUpdater[TOut]):
    def __init__(self, items: TIn, updater: Method[IFunction[TOut]]):
        super().__init__(updater)

        self.__items: TIn = items
    
    @abstractmethod
    def _GetList(self, items: TIn) -> TOut:
        pass
    
    @final
    def _GetValue(self) -> TOut:
        return self._GetList(self.__items)

class _ReadOnlyList[T](ISinglyLinkedList[T]):
    @final
    class __Updater(_IReadOnlyListUpdater[ISinglyLinkedList[T], IReadOnlyList[T]]):
        @final
        class _ReadOnlyList(ReadOnlyList[T, ISinglyLinkedList[T]], IGenericConstraintImplementation[ISinglyLinkedList[T]]):
            def __init__(self, items: ISinglyLinkedList[T]):
                super().__init__(items)
        
        def __init__(self, items: ISinglyLinkedList[T], updater: Method[IFunction[IReadOnlyList[T]]]):
            super().__init__(items, updater)
        
        def _GetList(self, items: ISinglyLinkedList[T]) -> IReadOnlyList[T]:
            return _ReadOnlyList[T].__Updater._ReadOnlyList(items)
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyList[T]]) -> None:
            self.__updater = func
        
        super().__init__()
    
        self.__updater: IFunction[IReadOnlyList[T]] = _ReadOnlyList[T].__Updater(self, update)
    
    @final
    def AsReadOnly(self) -> IReadOnlyList[T]:
        return self.__updater.GetValue()
class _ReadOnlyCountableList[T](ICountableSinglyLinkedList[T]):
    @final
    class __Updater(_IReadOnlyListUpdater[ICountableSinglyLinkedList[T], IReadOnlyCountableList[T]]):
        @final
        class _ReadOnlyList(ReadOnlyList[T, ICountableSinglyLinkedList[T]], Countable, IReadOnlyCountableList[T], IGenericConstraintImplementation[ICountableSinglyLinkedList[T]]):
            def __init__(self, items: ICountableSinglyLinkedList[T]):
                super().__init__(items)
            
            def GetCount(self) -> int:
                return self._GetContainer().GetCount()
        
        def __init__(self, items: ICountableSinglyLinkedList[T], updater: Method[IFunction[IReadOnlyCountableList[T]]]):
            super().__init__(items, updater)
        
        def _GetList(self, items: ICountableSinglyLinkedList[T]) -> IReadOnlyCountableList[T]:
            return _ReadOnlyCountableList[T].__Updater._ReadOnlyList(items)
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyCountableList[T]]) -> None:
            self.__updater = func
        
        super().__init__()
    
        self.__updater: IFunction[IReadOnlyCountableList[T]] = _ReadOnlyCountableList[T].__Updater(self, update)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableList[T]:
        return self.__updater.GetValue()

class _ReadOnlyEnumerableList[T](IEnumerableList[T]):
    @final
    class __Updater(_IReadOnlyListUpdater[IEnumerableList[T], IReadOnlyEnumerableList[T]]):
        @final
        class _ReadOnlyList(ReadOnlyList[T, IEnumerableList[T]], EnumerableBase[T], IReadOnlyEnumerableList[T], IGenericConstraintImplementation[IEnumerableList[T]]):
            def __init__(self, items: IEnumerableList[T]):
                super().__init__(items)
            
            def TryGetEnumerator(self) -> IEnumerator[T]|None:
                return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
        
        def __init__(self, items: IEnumerableList[T], updater: Method[IFunction[IReadOnlyEnumerableList[T]]]):
            super().__init__(items, updater)
        
        def _GetList(self, items: IEnumerableList[T]) -> IReadOnlyEnumerableList[T]:
            return _ReadOnlyEnumerableList[T].__Updater._ReadOnlyList(items)
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyEnumerableList[T]]) -> None:
            self.__updater = func
        
        super().__init__()
    
        self.__updater: IFunction[IReadOnlyEnumerableList[T]] = _ReadOnlyEnumerableList[T].__Updater(self, update)
    
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        return self.__updater.GetValue()
class _ReadOnlyCountableEnumerableList[T](ICountableEnumerableList[T]):
    @final
    class __Updater(_IReadOnlyListUpdater[ICountableEnumerableList[T], IReadOnlyCountableEnumerableList[T]]):
        @final
        class _ReadOnlyList(ReadOnlyList[T, ICountableEnumerableList[T]], CountableEnumerable[T], IReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[ICountableEnumerableList[T]]):
            def __init__(self, items: ICountableEnumerableList[T]):
                super().__init__(items)
            
            def GetCount(self) -> int:
                return self._GetContainer().GetCount()
            
            def TryGetEnumerator(self) -> IEnumerator[T]|None:
                return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
        
        def __init__(self, items: ICountableEnumerableList[T], updater: Method[IFunction[IReadOnlyCountableEnumerableList[T]]]):
            super().__init__(items, updater)
        
        def _GetList(self, items: ICountableEnumerableList[T]) -> IReadOnlyCountableEnumerableList[T]:
            return _ReadOnlyCountableEnumerableList[T].__Updater._ReadOnlyList(items)
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyCountableEnumerableList[T]]) -> None:
            self.__updater = func
        
        super().__init__()
    
        self.__updater: IFunction[IReadOnlyCountableEnumerableList[T]] = _ReadOnlyCountableEnumerableList[T].__Updater(self, update)
    
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        return self.__updater.GetValue()

class ListBase[T](Abstract, ISinglyLinkedList[T]):
    @final
    def PushItems(self, items: Iterable[T]) -> None:
        if not self.TryPushItems(items):
            raise ValueError("items can not be None.")

class LinkedListBase[TItem, TList](ListBase[TItem], GenericConstraint[TList, IReadWriteList[TItem]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def TryPeek(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetFirst()
    
    @final
    def TryPop(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryRemoveFirst()
    
    @final
    def Clear(self) -> None:
        self._GetInnerContainer().Clear()

class QueueBase[TItems, TList](LinkedListBase[TItems, TList]):
    def __init__(self, l: TList):
        super().__init__(l)
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetInnerContainer().AddLastNode(value)
    @final
    def TryPushItems(self, items: Iterable[TItems]|None) -> bool:
        return self._GetInnerContainer().AddLastItems(items)
class StackBase[TItems, TList](LinkedListBase[TItems, TList]):
    def __init__(self, l: TList):
        super().__init__(l)
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetInnerContainer().AddFirstNode(value)
    @final
    def TryPushItems(self, items: Iterable[TItems]|None) -> bool:
        return self._GetInnerContainer().AddFirstItems(items)

@staticmethod
def _GetList[T](l: IDoublyLinkedList[T]|None) -> IDoublyLinkedList[T]:
    return List[T]() if l is None else l
@staticmethod
def _GetCountableList[T](l: ICountableDoublyLinkedList[T]|None) -> ICountableDoublyLinkedList[T]:
    return CountableList[T]() if l is None else l

class LinkedList[T](LinkedListBase[T, IReadWriteList[T]], _ReadOnlyList[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: IReadWriteList[T]|None = None):
        super().__init__(_GetList(l))
class CountableLinkedList[T](LinkedListBase[T, ICountableDoublyLinkedList[T]], _ReadOnlyCountableList[T], IGenericConstraintImplementation[ICountableDoublyLinkedList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None):
        super().__init__(_GetCountableList(l))

class EnumerableLinkedList[T](LinkedListBase[T, IDoublyLinkedList[T]], _ReadOnlyEnumerableList[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: IDoublyLinkedList[T]|None = None):
        super().__init__(_GetList(l))
class CountableEnumerableLinkedList[T](LinkedListBase[T, ICountableDoublyLinkedList[T]], _ReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[ICountableDoublyLinkedList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None):
        super().__init__(_GetCountableList(l))

class Queue[T](QueueBase[T, IReadWriteList[T]], _ReadOnlyList[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: IReadWriteList[T]|None = None):
        super().__init__(_GetList(l))
class Stack[T](StackBase[T, IReadWriteList[T]], _ReadOnlyList[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: IReadWriteList[T]|None = None):
        super().__init__(_GetList(l))

class CountableQueue[T](QueueBase[T, ICountableDoublyLinkedList[T]], _ReadOnlyCountableList[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None):
        super().__init__(_GetCountableList(l))
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
class CountableStack[T](StackBase[T, ICountableDoublyLinkedList[T]], _ReadOnlyCountableList[T], IGenericConstraintImplementation[IReadWriteList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None):
        super().__init__(_GetCountableList(l))
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()

class EnumerableQueue[T](QueueBase[T, IDoublyLinkedList[T]], _ReadOnlyEnumerableList[T], IGenericConstraintImplementation[IDoublyLinkedList[T]]):
    def __init__(self, l: IDoublyLinkedList[T]|None = None):
        super().__init__(_GetList(l))

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsIterable(self) -> Iterable[T]:
        return Enumerable[T](self._GetContainer()).AsIterable()
class EnumerableStack[T](StackBase[T, IDoublyLinkedList[T]], _ReadOnlyEnumerableList[T], IGenericConstraintImplementation[IDoublyLinkedList[T]]):
    def __init__(self, l: IDoublyLinkedList[T]|None = None):
        super().__init__(_GetList(l))

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsIterable(self) -> Iterable[T]:
        return Enumerable[T](self._GetContainer()).AsIterable()

class CountableEnumerableQueue[T](QueueBase[T, ICountableDoublyLinkedList[T]], _ReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[ICountableDoublyLinkedList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None):
        super().__init__(_GetCountableList(l))

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsIterable(self) -> Iterable[T]:
        return Enumerable[T](self._GetContainer()).AsIterable()
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()
class CountableEnumerableStack[T](StackBase[T, ICountableDoublyLinkedList[T]], _ReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[ICountableDoublyLinkedList[T]]):
    def __init__(self, l: ICountableDoublyLinkedList[T]|None = None):
        super().__init__(_GetCountableList(l))

    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    def AsIterable(self) -> Iterable[T]:
        return Enumerable[T](self._GetContainer()).AsIterable()
    
    @final
    def GetCount(self) -> int:
        return self._GetContainer().GetCount()