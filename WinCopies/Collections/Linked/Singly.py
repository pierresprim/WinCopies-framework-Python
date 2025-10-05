from __future__ import annotations

from collections.abc import Iterable

from abc import abstractmethod
from typing import final, Callable, Self

from WinCopies import Collections, Abstract
from WinCopies.Collections import Enumeration, Generator, ICountable, IReadOnlyCollection
from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, ICountableEnumerable
from WinCopies.Collections.Linked.Enumeration import NodeEnumeratorBase, GetValueEnumeratorFromNode
from WinCopies.Collections.Linked.Node import LinkedNode

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class SinglyLinkedNode[T](LinkedNode['SinglyLinkedNode', T]):
    def __init__(self, value: T, nextNode: Self|None):
        super().__init__(value, nextNode)

class IReadOnlyList[T](IReadOnlyCollection):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def TryPeek(self) -> INullable[T]:
        pass
class IList[T](IReadOnlyList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyList[T]:
        pass
    
    @abstractmethod
    def Push(self, value: T) -> None:
        pass
    
    @abstractmethod
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        pass
    @abstractmethod
    def PushItems(self, items: Iterable[T]) -> None:
        pass
    
    @final
    def PushValues(self, *values: T) -> None:
        self.PushItems(values)
    
    @abstractmethod
    def TryPop(self) -> INullable[T]:
        pass
    
    @abstractmethod
    def Clear(self) -> None:
        pass
    
    @final
    def AsGenerator(self) -> Generator[T]:
        result: INullable[T] = self.TryPop()

        while result.HasValue():
            yield result.GetValue()
            
            result = self.TryPop()

class IReadOnlyEnumerableList[T](IReadOnlyList[T], IEnumerable[T]):
    def __init__(self):
        super().__init__()
class IEnumerableList[T](IReadOnlyEnumerableList[T], IList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        pass

class IReadOnlyCountableList[T](IReadOnlyList[T], ICountable):
    def __init__(self):
        super().__init__()
class ICountableList[T](IReadOnlyCountableList[T], IList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableList[T]:
        pass

class IReadOnlyCountableEnumerableList[T](ICountableEnumerable[T], IReadOnlyEnumerableList[T], IReadOnlyCountableList[T]):
    def __init__(self):
        super().__init__()
class ICountableEnumerableList[T](IReadOnlyCountableEnumerableList[T], IEnumerableList[T], ICountableList[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        pass

class _ReadOnlyList[TItem, TList](Abstract, IReadOnlyList[TItem], GenericConstraint[TList, IReadOnlyList[TItem]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @final
    def TryPeek(self) -> INullable[TItem]:
        return self._GetInnerContainer().TryPeek()

class ListBase[T](Abstract, IList[T]):
    def __init__(self):
        super().__init__()
        
        self.__first: SinglyLinkedNode[T]|None = None

    @final
    def IsEmpty(self) -> bool:
        return self.__first is None
    @final
    def HasItems(self) -> bool:
        return super().HasItems()
    
    @final
    def _GetFirst(self) -> SinglyLinkedNode[T]|None:
        return self.__first
    @final
    def _SetFirst(self, node: SinglyLinkedNode[T]) -> None:
        self.__first = node
    
    @abstractmethod
    def _OnRemoved(self) -> None:
        pass
    
    @abstractmethod
    def _Push(self, value: T, first: SinglyLinkedNode[T]) -> None:
        pass
    @final
    def Push(self, value: T) -> None:
        if self.IsEmpty():
            self.__first = SinglyLinkedNode[T](value, None)
        
        else:
            self._Push(value, self.__first) # type: ignore
    
    @final
    def PushItems(self, items: Iterable[T]) -> None:
        for value in items:
            self.Push(value)
    @final
    def TryPushItems(self, items: Iterable[T]|None) -> bool:
        if items is None:
            return False
        
        self.PushItems(items)

        return True
    
    @final
    def TryPeek(self) -> INullable[T]:
        return GetNullValue() if self.IsEmpty() else (GetNullValue() if self.__first is None else GetNullable(self.__first.GetValue())) # self.__first should never be None if self.IsEmpty().
    
    @final
    def TryPop(self) -> INullable[T]:
        result: INullable[T] = self.TryPeek()

        if result.HasValue():
            first: SinglyLinkedNode[T]|None = self.__first

            if first is None: # Should never be None here.
                return result

            self.__first = first.GetNext()

            first._SetNext(None) # type: ignore # Needed in case of a running enumeration.

            self._OnRemoved()

        return result
    
    @final
    def Clear(self) -> None:
        result: INullable[T] = self.TryPop()

        while result.HasValue(): # Needed in case of a running enumeration.
            result = self.TryPop()

        self.__first = None

        self._OnRemoved()

class List[T](ListBase[T]):
    class _ReadOnlyList(_ReadOnlyList[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
        def __init__(self, items: IList[T]):
            super().__init__(items)
    
    @final
    class __Updater(ValueFunctionUpdater[IReadOnlyList[T]]):
        def __init__(self, items: List[T], updater: Method[IFunction[IReadOnlyList[T]]]):
            super().__init__(updater)

            self.__items: List[T] = items
        
        def _GetValue(self) -> IReadOnlyList[T]:
            return self.__items._AsReadOnly()
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyList[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyList[T]] = List[T].__Updater(self, update)
    
    def _AsReadOnly(self) -> IReadOnlyList[T]:
        return List[T]._ReadOnlyList(self)
    @final
    def AsReadOnly(self) -> IReadOnlyList[T]:
        return self.__readOnly.GetValue()

class Enumerable[T](ListBase[T], Enumeration.Enumerable[T], IEnumerableList[T]):
    class _ReadOnlyList(_ReadOnlyList[T, IReadOnlyEnumerableList[T]], Enumeration.Enumerable[T], IReadOnlyEnumerableList[T], IGenericConstraintImplementation[IReadOnlyEnumerableList[T]]):
        def __init__(self, items: IReadOnlyEnumerableList[T]):
            super().__init__(items)
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    class __Updater(ValueFunctionUpdater[IReadOnlyEnumerableList[T]]):
        def __init__(self, items: Enumerable[T], updater: Method[IFunction[IReadOnlyEnumerableList[T]]]):
            super().__init__(updater)

            self.__items: Enumerable[T] = items
        
        def _GetValue(self) -> IReadOnlyEnumerableList[T]:
            return self.__items._AsReadOnly()
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyEnumerableList[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyEnumerableList[T]] = Enumerable[T].__Updater(self, update)
    
    def _AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        return Enumerable[T]._ReadOnlyList(self)
    @final
    def AsReadOnly(self) -> IReadOnlyEnumerableList[T]:
        return self.__readOnly.GetValue()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        if self.IsEmpty():
            return None
        
        first: SinglyLinkedNode[T]|None = self._GetFirst() # Should never be None here.
        
        return None if first is None else GetValueEnumeratorFromNode(first)

class QueueBase[T](ListBase[T]):
    def __init__(self, *values: T):
        super().__init__()
        
        self.__last: SinglyLinkedNode[T]|None = None
        self.__updater: Callable[[SinglyLinkedNode[T], SinglyLinkedNode[T]], None] = self.__GetUpdater()

        self.PushItems(values)
    
    @final
    def __Push(self, first: SinglyLinkedNode[T], newNode: SinglyLinkedNode[T]) -> None:
        def push(previousNode: SinglyLinkedNode[T], newNode: SinglyLinkedNode[T]) -> None:
            previousNode._SetNext(newNode) # type: ignore

            self.__last = newNode
        
        push(first, newNode)

        self.__updater = lambda first, newNode: push(self.__last, newNode) # type: ignore
    
    @final
    def __GetUpdater(self) -> Callable[[SinglyLinkedNode[T], SinglyLinkedNode[T]], None]:
        return lambda first, newNode: self.__Push(first, newNode)
    
    @final
    def _Push(self, value: T, first: SinglyLinkedNode[T]):
        self.__updater(first, SinglyLinkedNode[T](value, None))
    
    @final
    def _OnRemoved(self) -> None:
        if self.IsEmpty():
            self.__last = None
            self.__updater = self.__GetUpdater()
class StackBase[T](ListBase[T]):
    def __init__(self, *values: T):
        super().__init__()

        self.PushItems(values)
    
    @final
    def _Push(self, value: T, first: SinglyLinkedNode[T]) -> None:
        self._SetFirst(SinglyLinkedNode[T](value, first))
    
    @final
    def _OnRemoved(self) -> None:
        pass

class Queue[T](QueueBase[T], List[T]):
    def __init__(self, *values: T):
        super().__init__(*values)
class Stack[T](StackBase[T], List[T]):
    def __init__(self, *values: T):
        super().__init__(*values)

class SinglyLinkedNodeEnumeratorBase[TItems, TNode](NodeEnumeratorBase[TItems, TNode]):
    def __init__(self, node: TNode):
        super().__init__(node)
class SinglyLinkedNodeEnumerator[T](SinglyLinkedNodeEnumeratorBase[T, SinglyLinkedNode[T]]):
    def __init__(self, node: SinglyLinkedNode[T]):
        super().__init__(node)

class EnumerableQueue[T](QueueBase[T], Enumerable[T]):
    def __init__(self, *values: T):
        super().__init__(*values)
class EnumerableStack[T](StackBase[T], Enumerable[T]):
    def __init__(self, *values: T):
        super().__init__(*values)

class CollectionBase[TItems, TList](Abstract, GenericConstraint[TList, IList[TItems]], IList[TItems]):
    def __init__(self, l: TList):
        super().__init__()
        
        self.__list: TList = l
    
    def _GetContainer(self) -> TList:
        return self.__list
    def _GetCollection(self) -> TList:
        return self._GetContainer()

    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    @final
    def HasItems(self) -> bool:
        return self._GetInnerContainer().HasItems()

class Collection[T](CollectionBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, l: IList[T]):
        super().__init__(l)

class CountableBase[TItems, TList](CollectionBase[TItems, TList], Collections.Countable, ICountableList[TItems]):
    def __init__(self, l: TList):
        EnsureDirectModuleCall()

        super().__init__(l)

        self.__count: int = 0
    
    @final
    def GetCount(self) -> int:
        return self.__count
    
    @final
    def __Increment(self) -> None:
        self.__count += 1
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetInnerContainer().Push(value)

        self.__Increment()
    
    @final
    def __PushItems(self, items: Iterable[TItems]) -> None:
        def loop() -> Generator[TItems]:
            for item in items:
                yield item
                
                self.__Increment()
        
        self._GetInnerContainer().PushItems(loop())
    
    @final
    def TryPushItems(self, items: Iterable[TItems]|None) -> bool:
        if items is None:
            return False
        
        self.__PushItems(items)

        return True
    @final
    def PushItems(self, items: Iterable[TItems]) -> None:
        if items is None: # type: ignore
            raise ValueError("No value provided.")
        
        self.__PushItems(items)
    
    @final
    def TryPeek(self) -> INullable[TItems]:
        return self._GetInnerContainer().TryPeek()
    
    @final
    def TryPop(self) ->  INullable[TItems]:
        result: INullable[TItems] = self._GetInnerContainer().TryPop()

        if result.HasValue():
            self.__count -= 1
        
        return result
    
    @final
    def Clear(self) -> None:
        self._GetInnerContainer().Clear()

        self.__count = 0

class Countable[T](CountableBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    class _ReadOnlyList(_ReadOnlyList[T, IReadOnlyCountableList[T]], Collections.Countable, IReadOnlyCountableList[T], IGenericConstraintImplementation[IReadOnlyCountableList[T]]):
        def __init__(self, items: IReadOnlyCountableList[T]):
            super().__init__(items)
        
        @final
        def GetCount(self) -> int:
            return self._GetContainer().GetCount()
    
    @final
    class __Updater(ValueFunctionUpdater[IReadOnlyCountableList[T]]):
        def __init__(self, items: Countable[T], updater: Method[IFunction[IReadOnlyCountableList[T]]]):
            super().__init__(updater)

            self.__items: Countable[T] = items
        
        def _GetValue(self) -> IReadOnlyCountableList[T]:
            return self.__items._AsReadOnly()
    
    def __init__(self, l: IList[T]):
        def update(func: IFunction[IReadOnlyCountableList[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(l)

        self.__readOnly: IFunction[IReadOnlyCountableList[T]] = Countable[T].__Updater(self, update)
    
    def _AsReadOnly(self) -> IReadOnlyCountableList[T]:
        return Countable[T]._ReadOnlyList(self)
    @final
    def AsReadOnly(self) -> IReadOnlyCountableList[T]:
        return self.__readOnly.GetValue()

class CountableQueue[T](Countable[T]):
    def __init__(self, *values: T):
        super().__init__(Queue[T]())

        self.PushItems(values)
class CountableStack[T](Countable[T]):
    def __init__(self, *values: T):
        super().__init__(Stack[T]())

        self.PushItems(values)

class CountableEnumerableBase[TItems, TList](CountableBase[TItems, TList], Enumeration.Enumerable[TItems], ICountableEnumerableList[TItems], GenericConstraint[TList, Enumerable[TItems]]):
    def __init__(self, l: TList):
        super().__init__(l)
class CountableEnumerable[T](CountableEnumerableBase[T, Enumerable[T]], IGenericConstraintImplementation[Enumerable[T]]):
    class _ReadOnlyList(_ReadOnlyList[T, IReadOnlyCountableEnumerableList[T]], Enumeration.CountableEnumerable[T], IReadOnlyCountableEnumerableList[T], IGenericConstraintImplementation[IReadOnlyCountableEnumerableList[T]]):
        def __init__(self, items: IReadOnlyCountableEnumerableList[T]):
            super().__init__(items)
        
        @final
        def GetCount(self) -> int:
            return self._GetContainer().GetCount()
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[T]|None:
            return Enumerator[T].TryCreate(self._GetContainer().TryGetEnumerator())
    
    @final
    class __Updater(ValueFunctionUpdater[IReadOnlyCountableEnumerableList[T]]):
        def __init__(self, items: CountableEnumerable[T], updater: Method[IFunction[IReadOnlyCountableEnumerableList[T]]]):
            super().__init__(updater)

            self.__items: CountableEnumerable[T] = items
        
        def _GetValue(self) -> IReadOnlyCountableEnumerableList[T]:
            return self.__items._AsReadOnly()
    
    def __init__(self, l: Enumerable[T]):
        def update(func: IFunction[IReadOnlyCountableEnumerableList[T]]) -> None:
            self.__readOnly = func
        
        super().__init__(l)

        self.__readOnly: IFunction[IReadOnlyCountableEnumerableList[T]] = CountableEnumerable[T].__Updater(self, update)
    
    def _AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        return CountableEnumerable[T]._ReadOnlyList(self)
    @final
    def AsReadOnly(self) -> IReadOnlyCountableEnumerableList[T]:
        return self.__readOnly.GetValue()

class CountableEnumerableQueue[T](CountableEnumerable[T]):
    def __init__(self, *values: T):
        super().__init__(EnumerableQueue[T]())

        self.PushItems(values)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetCollection().TryGetEnumerator()
class CountableEnumerableStack[T](CountableEnumerable[T]):
    def __init__(self, *values: T):
        super().__init__(EnumerableStack[T]())

        self.PushItems(values)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return self._GetCollection().TryGetEnumerator()